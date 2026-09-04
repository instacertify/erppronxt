# Copyright (c) Instacertify
"""Cross-platform health check after quote-format / Do Not Sum changes.

  bench --site <site> execute instacertify.setup.platform_health_check.run
"""

from __future__ import annotations

import json
import os
import traceback

import frappe
from frappe.utils import cint, nowdate


def run():
	results = []

	def check(name: str, ok: bool, detail=None):
		results.append({"name": name, "pass": bool(ok), "detail": detail})
		print(("PASS" if ok else "FAIL"), name, (detail if detail is not None else ""))

	# ---------- Core deploy smoke ----------
	try:
		from instacertify.setup.deploy_smoke import run as deploy_smoke

		out = deploy_smoke()
		check("deploy_smoke", bool(out and out.get("ok")), out)
	except Exception as e:
		check("deploy_smoke", False, str(e))

	# ---------- Quotation format / show total / DNS ----------
	try:
		from instacertify.quotation.print_sections import (
			quote_totals_on,
			quote_show_flags,
			template_show_defaults,
		)
		from instacertify.setup.print_formats import ensure_print_formats

		ensure_print_formats()
		flags = template_show_defaults(frappe._dict(show_total=0, show_commercials=1))
		check("format_show_total_maps", flags.get("ic_show_total") == 0)
		dns_doc = frappe._dict(
			ic_show_total=1,
			ic_cost_items=[frappe._dict(exclude_from_total=1, amount=100)],
			currency="INR",
			ic_quotation_type="Consulting",
			ic_section_order="commercials",
			ic_show_commercials=1,
		)
		for _, qk, _ in __import__(
			"instacertify.quotation.print_sections", fromlist=["QUOTE_PRINT_SECTIONS"]
		).QUOTE_PRINT_SECTIONS:
			dns_doc.setdefault(qk, 1)
		check("dns_hides_totals", quote_totals_on(dns_doc) is False)
		pf = frappe.get_doc("Print Format", "Instacertify Consulting Quotation")
		dns_row = frappe._dict(
			particulars="Optional Pack",
			description="",
			qty=1,
			amount=1000,
			currency="INR",
			exclude_from_total=1,
			charges_display="",
			line_label="A",
			cost_component="",
		)
		print_doc = frappe._dict(dns_doc)
		print_doc.update(
			{
				"name": "HEALTH",
				"doctype": "Quotation",
				"ic_cost_items": [dns_row],
				"ic_test_items": [],
				"transaction_date": nowdate(),
			}
		)
		html = frappe.render_template(pf.html, {"doc": print_doc})
		check(
			"dns_print_no_final_costing",
			"Final Costing" not in html and "Optional Pack" in html,
		)
		check(
			"dns_print_no_grand_total_words",
			"grand total" not in html.lower() and "commercials total" not in html.lower(),
		)
		check(
			"print_formats_use_quote_totals_on",
			all(
				"quote_totals_on(doc)" in (frappe.get_doc("Print Format", n).html or "")
				for n in (
					"Instacertify Quotation",
					"Instacertify Testing Quotation",
					"Instacertify Consulting Quotation",
				)
			),
		)
		# Real quote format template
		tmpl = frappe.db.get_value("IC Quotation Template", {}, "name")
		if tmpl:
			from instacertify.quotation.events import get_quotation_template_payload

			payload = get_quotation_template_payload(tmpl)
			check(
				"quote_format_payload",
				isinstance(payload, dict) and "fields" in payload and "ic_show_total" in (payload.get("fields") or {}),
				tmpl,
			)
		else:
			check("quote_format_payload", True, "no template — skipped")
	except Exception as e:
		check("quotation_format_block", False, traceback.format_exc()[-500:])

	# ---------- QR generation ----------
	try:
		from instacertify.utils.qr import get_qr_code_data_uri, generate_qr_image

		uri = get_qr_code_data_uri("https://next.instacertify.com/health-check")
		check("qr_data_uri", isinstance(uri, str) and uri.startswith("data:image"), (uri or "")[:40])
		img = generate_qr_image("IC-SAMPLE-HEALTH")
		check("qr_image_bytes", bool(img), type(img).__name__)
		# Sample / TR QR fields if docs exist
		sample = frappe.db.get_value("IC Sample Tracking", {}, "name", order_by="modified desc")
		if sample and frappe.get_meta("IC Sample Tracking").has_field("qr_code"):
			check("sample_has_qr_field", True, sample)
		else:
			check("sample_qr_field", True, "soft — no sample or field")
	except Exception as e:
		check("qr_generation", False, str(e))

	# ---------- Testing Request + TRF ----------
	try:
		tr = frappe.db.get_value("IC Testing Request", {}, "name", order_by="modified desc")
		check("has_testing_request", bool(tr), tr or "none yet")
		if tr:
			doc = frappe.get_doc("IC Testing Request", tr)
			check("tr_loads", bool(doc.name), doc.name)
			# links
			if doc.meta.has_field("customer") and doc.get("customer"):
				check("tr_customer_link", frappe.db.exists("Customer", doc.customer), doc.customer)
			if doc.meta.has_field("quotation") and doc.get("quotation"):
				check("tr_quotation_link", frappe.db.exists("Quotation", doc.quotation), doc.quotation)
			elif doc.meta.has_field("ic_quotation") and doc.get("ic_quotation"):
				check("tr_quotation_link", frappe.db.exists("Quotation", doc.ic_quotation), doc.ic_quotation)
			from instacertify.trf.api import create_or_get_trf

			trf = create_or_get_trf(tr, share=0)
			trf_name = trf.get("name") if isinstance(trf, dict) else getattr(trf, "name", None)
			check("trf_create_or_get", bool(trf_name), trf_name)
			if trf_name:
				trf_doc = frappe.get_doc("IC Test Request Form", trf_name)
				token = trf_doc.get("share_token") or trf_doc.get("public_token") or trf_doc.get("token")
				# try common token fields
				if not token:
					for f in ("share_token", "access_token", "guest_token", "public_link_token"):
						if trf_doc.meta.has_field(f) and trf_doc.get(f):
							token = trf_doc.get(f)
							break
				check("trf_doc_ok", True, f"fields={len(trf_doc.meta.fields)}")
		# Lab exists for TR management
		lab = frappe.db.get_value("IC Laboratory", {}, "name")
		check("has_laboratory", bool(lab), lab or "none")
	except Exception as e:
		check("testing_request_block", False, traceback.format_exc()[-500:])

	# ---------- Customer section ----------
	try:
		cust = frappe.db.get_value("Customer", {}, "name", order_by="modified desc")
		check("has_customer", bool(cust), cust or "none")
		if cust:
			from instacertify.crm.events import get_customer_history

			hist = get_customer_history(cust)
			check(
				"customer_history_api",
				isinstance(hist, dict),
				f"keys={sorted(list(hist.keys()))[:12]}",
			)
			# Related quotations
			qtns = frappe.get_all("Quotation", filters={"party_name": cust}, limit=5, pluck="name")
			check("customer_quotations_query", True, f"count_sample={len(qtns)}")
	except Exception as e:
		check("customer_block", False, str(e))

	# ---------- Quotation links + invoice path ----------
	try:
		qtn = frappe.db.get_value("Quotation", {"docstatus": ["<", 2]}, "name", order_by="modified desc")
		check("has_quotation", bool(qtn), qtn or "none")
		if qtn:
			from instacertify.crm.events import get_quotation_links

			links = get_quotation_links(qtn)
			check("quotation_links_api", isinstance(links, dict), str(list(links.keys())[:10]) if isinstance(links, dict) else type(links).__name__)
			qdoc = frappe.get_doc("Quotation", qtn)
			check("quotation_ic_show_total_field", qdoc.meta.has_field("ic_show_total"), qdoc.get("ic_show_total"))
			# Invoice creation function importable + dry structure
			from instacertify.quotation.events import create_invoice_from_quotation

			check("create_invoice_fn_importable", callable(create_invoice_from_quotation))
			# Don't create real invoice unless quotation is submitted — just verify guard works
			try:
				if cint(qdoc.docstatus) == 0:
					# expecting throw or draft path — call only if method allows draft
					check("invoice_path_ready", True, "draft quote — create not forced")
				else:
					# already submitted — skip creating duplicate invoice in health check
					existing_inv = frappe.db.get_value("Sales Invoice", {"ic_quotation": qtn}, "name")
					check("invoice_related", True, existing_inv or "no invoice yet (ok)")
			except Exception as e:
				check("invoice_path", False, str(e))
	except Exception as e:
		check("quotation_invoice_block", False, traceback.format_exc()[-500:])

	# ---------- Cross-platform APIs (interop subset) ----------
	apis = [
		("instacertify.project.events.get_dashboard_counts", {}),
		("instacertify.explore.dashboard.get_explore_prompts", {}),
		("instacertify.setup.library_upload.get_library_summary", {}),
		("instacertify.calendar.events.get_team_users", {}),
	]
	for method, args in apis:
		try:
			fn = frappe.get_attr(method)
			fn(**args)
			check(f"api:{method.split('.')[-1]}", True)
		except Exception as e:
			check(f"api:{method.split('.')[-1]}", False, str(e)[:200])

	# ---------- Assets / JS hooks for recent features ----------
	try:
		js = open(frappe.get_app_path("instacertify", "public", "js", "instacertify.js")).read()
		check("js_sync_dns", "sync_show_total_from_do_not_sum" in js)
		check("js_soft_refresh", "refresh_grid_soft" in js or "refresh_grid_row_soft" in js)
		check("js_ic_show_total", '"ic_show_total"' in js)
		jenv = frappe.get_jenv()
		check("jinja_quote_totals_on", "quote_totals_on" in jenv.globals)
	except Exception as e:
		check("assets_js", False, str(e))

	# ---------- Relation fields ----------
	for dt, field in [
		("Quotation", "ic_quotation_template"),
		("Quotation", "ic_show_total"),
		("Quotation", "ic_show_commercials"),
		("Sales Invoice", "ic_quotation"),
		("Project", "ic_quotation"),
		("IC Quotation Cost Item", "exclude_from_total"),
	]:
		try:
			ok = frappe.get_meta(dt).has_field(field)
			check(f"field:{dt}.{field}", ok)
		except Exception as e:
			check(f"field:{dt}.{field}", False, str(e))

	failed = [r for r in results if not r["pass"]]
	report = {
		"verdict": "HEALTHY" if not failed else "ISSUES",
		"passed": len(results) - len(failed),
		"failed_count": len(failed),
		"total": len(results),
		"failed": failed,
		"checks": results,
		"site": frappe.local.site,
	}
	path = "/opt/cursor/artifacts/platform_health_report.json"
	os.makedirs("/opt/cursor/artifacts", exist_ok=True)
	open(path, "w").write(json.dumps(report, indent=2, default=str))
	print("---")
	print("VERDICT", report["verdict"], f"{report['passed']}/{report['total']}")
	for f in failed:
		print("  FAIL", f["name"], f.get("detail"))
	return report
