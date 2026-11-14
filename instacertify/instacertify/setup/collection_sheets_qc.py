# Copyright (c) Instacertify
"""QC for Documents Collection Sheet + Sample Dispatch Collection share links."""

from __future__ import annotations

import json

import frappe


def run_collection_sheets_qc() -> dict:
	report = {"ok": [], "warn": [], "fail": [], "urls": {}}

	def ok(m):
		report["ok"].append(m)

	def fail(m):
		report["fail"].append(m)

	frappe.set_user("Administrator")

	# DocTypes + print formats
	for dt in ("IC Sample Dispatch Collection", "IC Data Collection Item", "IC Document Request"):
		(ok if frappe.db.exists("DocType", dt) else fail)(f"DocType {dt}")
	for fmt in (
		"Instacertify Documents Collection Sheet",
		"Instacertify Sample Dispatch Collection",
	):
		(ok if frappe.db.exists("Print Format", fmt) else fail)(f"Print Format {fmt}")

	# Meta: data collection fields on document request
	meta = frappe.get_meta("IC Document Request")
	for field in ("company_legal_name", "data_fields", "product_name"):
		(ok if meta.has_field(field) else fail)(f"IC Document Request.{field}")

	project = frappe.db.get_value("Project", {"customer": ["is", "set"]}, "name", order_by="modified desc")
	if not project:
		fail("No Project with customer for collection QC")
		report["summary"] = {
			"ok": len(report["ok"]),
			"fail": len(report["fail"]),
			"passed": False,
		}
		print(json.dumps(report, indent=2, default=str))
		return report

	# Documents collection share
	from instacertify.documents.api import (
		create_document_request_for_project,
		get_document_request_by_token,
		save_data_collection,
	)

	doc_share = create_document_request_for_project(project)
	report["urls"]["documents"] = doc_share.get("url")
	ok(f"Documents share {doc_share.get('document_request')}")

	frappe.set_user("Guest")
	try:
		payload = get_document_request_by_token(doc_share["token"])
		if "project" in payload or "customer" in payload or "name" in payload:
			fail("Documents guest payload leaked desk ids")
		else:
			ok("Documents guest payload stripped")
		if "data_fields" not in payload:
			fail("Documents payload missing data_fields")
		else:
			ok(f"Documents data_fields={len(payload.get('data_fields') or [])}")
		if not payload.get("pdf_url") or "download_collection_pdf" not in payload["pdf_url"]:
			fail("Documents payload missing pdf_url")
		else:
			ok("Documents pdf_url present")
		save_data_collection(
			token=doc_share["token"],
			company_legal_name="QC Test Pvt Ltd",
			gstin="09AAAAA0000A1Z5",
			product_name="QC Product",
			data_fields=[
				{"name": row["name"], "field_value": f"QC value {row['idx']}"}
				for row in (payload.get("data_fields") or [])
			],
		)
		ok("save_data_collection ok")
	except Exception as e:
		fail(f"Documents guest flow: {e}")
	finally:
		frappe.set_user("Administrator")

	# Sample dispatch share
	from instacertify.sample_dispatch.api import (
		create_sample_dispatch_for_project,
		get_sample_dispatch_by_token,
		save_sample_dispatch_collection,
	)

	disp = create_sample_dispatch_for_project(project)
	report["urls"]["dispatch"] = disp.get("url")
	ok(f"Dispatch share {disp.get('name')}")

	frappe.set_user("Guest")
	try:
		payload = get_sample_dispatch_by_token(disp["token"])
		if any(k in payload for k in ("project", "customer", "name", "share_token")):
			fail("Dispatch guest payload leaked desk ids")
		else:
			ok("Dispatch guest payload stripped")
		if not payload.get("pdf_url") or "download_dispatch_pdf" not in payload["pdf_url"]:
			fail("Dispatch payload missing pdf_url")
		else:
			ok("Dispatch pdf_url present")
		save_sample_dispatch_collection(
			token=disp["token"],
			contact_person="QC Contact",
			courier_name="BlueDart",
			tracking_number="QC-AWB-001",
			dispatch_date=frappe.utils.today(),
			sample_description="QC sample unit",
			sample_quantity="2",
		)
		ok("save_sample_dispatch_collection ok")
	except Exception as e:
		fail(f"Dispatch guest flow: {e}")
	finally:
		frappe.set_user("Administrator")

	try:
		doc = frappe.get_doc("IC Sample Dispatch Collection", disp["name"])
		if doc.status != "Submitted by Customer":
			fail(f"Dispatch status expected Submitted, got {doc.status}")
		else:
			ok("Dispatch status Submitted by Customer")
		if doc.tracking_number != "QC-AWB-001":
			fail("Dispatch tracking not saved")
		else:
			ok("Dispatch tracking saved")
	except Exception as e:
		fail(f"Dispatch verify: {e}")

	# Print HTML renders
	try:
		from frappe.utils.print_format import download_pdf  # noqa: F401
		from instacertify.utils.pdf import make_pdf

		dr = doc_share.get("document_request")
		html = frappe.get_print("IC Document Request", dr, print_format="Instacertify Documents Collection Sheet")
		pdf = make_pdf(html)
		(ok if pdf and pdf[:4] == b"%PDF" else fail)(f"Documents collection PDF bytes={len(pdf or b'')}")
		html2 = frappe.get_print(
			"IC Sample Dispatch Collection",
			disp["name"],
			print_format="Instacertify Sample Dispatch Collection",
		)
		pdf2 = make_pdf(html2)
		(ok if pdf2 and pdf2[:4] == b"%PDF" else fail)(f"Dispatch collection PDF bytes={len(pdf2 or b'')}")
	except Exception as e:
		fail(f"Print QC: {e}")

	report["summary"] = {
		"ok": len(report["ok"]),
		"warn": len(report["warn"]),
		"fail": len(report["fail"]),
		"passed": len(report["fail"]) == 0,
	}
	print(json.dumps(report, indent=2, default=str))
	return report
