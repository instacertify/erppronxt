# Copyright (c) Instacertify
"""Testing & sample events."""

from __future__ import annotations

import secrets

import frappe
from frappe import _
from frappe.model.naming import make_autoname
from frappe.utils import now_datetime


def before_insert_sample(doc, method=None):
	if not doc.tracking_number:
		doc.tracking_number = make_autoname("SMP-TRK-.YYYY.-.#####")


def validate_sample(doc, method=None):
	"""Hook backup — DocType.validate also syncs custody."""
	from instacertify.instacertify.doctype.ic_sample_tracking.ic_sample_tracking import (
		PRESERVE_LOCATIONS_ON_REPORT,
		STATUS_TO_LOCATION,
	)

	if doc.status == "Sample Received" and not doc.sample_received_date:
		doc.sample_received_date = frappe.utils.today()
	# Normalize legacy storage label
	if doc.sample_location == "At Instacertify Storage":
		doc.sample_location = "At Instacertify Warehouse"
	# Only derive location from status when location is empty or status is a custody move
	if doc.status in STATUS_TO_LOCATION:
		if not doc.sample_location or (
			doc.sample_location not in PRESERVE_LOCATIONS_ON_REPORT
			and doc.status
			not in (
				"Report Available",
				"Report Uploaded",
				"Report Shared with Customer",
			)
		):
			doc.sample_location = STATUS_TO_LOCATION[doc.status]
	if not doc.qr_code and doc.tracking_number:
		_attach_sample_qr(doc)


def _attach_sample_qr(doc):
	from instacertify.utils.qr import generate_and_attach_qr, sample_qr_payload

	try:
		# Save first if new
		if doc.is_new() or not doc.tracking_number:
			return
		generate_and_attach_qr(
			"IC Sample Tracking",
			doc.name,
			"qr_code",
			sample_qr_payload(doc.tracking_number, doc.name),
			box_size=6,
			border=1,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Sample QR")


def validate_testing_request(doc, method=None):
	from instacertify.team.assignees import sync_assignees

	sync_assignees(
		doc,
		table_field="ic_assignees",
		primary_field="assigned_person",
		legacy_seed_field="assigned_person",
		default_user=doc.owner,
	)
	_sync_testing_request_reports(doc)


def _sync_testing_request_reports(doc):
	"""Keep multi-PDF table and primary test_report in sync."""
	if not doc.meta.has_field("test_reports"):
		return

	rows = doc.get("test_reports") or []
	# Migrate legacy single Attach into the table once
	legacy = (doc.get("test_report") or "").strip()
	if legacy and not rows:
		doc.append(
			"test_reports",
			{
				"report_title": "Primary Report",
				"report_file": legacy,
				"uploaded_on": frappe.utils.now_datetime(),
			},
		)
		rows = doc.get("test_reports") or []

	# Drop empty rows; stamp uploaded_on; enforce PDF-ish attach
	cleaned = []
	for row in rows:
		file_url = (row.get("report_file") or "").strip()
		if not file_url:
			continue
		if not row.get("uploaded_on"):
			row.uploaded_on = frappe.utils.now_datetime()
		if not (row.get("report_title") or "").strip():
			row.report_title = f"Report {len(cleaned) + 1}"
		cleaned.append(row)

	# Primary share field = first attached file
	primary = cleaned[0].report_file if cleaned else ""
	if doc.meta.has_field("test_report"):
		doc.test_report = primary or None


@frappe.whitelist()
def regenerate_sample_qr(sample: str):
	"""Force-regenerate QR so it encodes the unique sample tracking number."""
	doc = frappe.get_doc("IC Sample Tracking", sample)
	if not doc.tracking_number:
		frappe.throw(_("Sample has no tracking number yet — save the sample first"))
	_attach_sample_qr(doc)
	doc.reload()
	return {"qr_code": doc.qr_code, "tracking_number": doc.tracking_number}


@frappe.whitelist()
def download_sample_sticker_50x25(sample: str):
	"""Download a 50×25 mm PNG sticker: QR + tracking number + www.instacertify.com."""
	doc = frappe.get_doc("IC Sample Tracking", sample)
	if not doc.tracking_number:
		frappe.throw(_("Sample has no tracking number yet — save the sample first"))
	from instacertify.utils.qr import render_sample_sticker_50x25_png, sample_qr_payload

	payload = sample_qr_payload(doc.tracking_number, doc.name)
	png = render_sample_sticker_50x25_png(doc.tracking_number, payload)
	fname = f"sample-sticker-50x25-{doc.tracking_number}.png".replace("/", "-")
	existing = frappe.db.get_value(
		"File",
		{
			"file_name": fname,
			"attached_to_doctype": "IC Sample Tracking",
			"attached_to_name": doc.name,
		},
		"name",
	)
	if existing:
		frappe.delete_doc("File", existing, ignore_permissions=True, force=True)
	file_doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": fname,
			"content": png,
			"is_private": 0,
			"attached_to_doctype": "IC Sample Tracking",
			"attached_to_name": doc.name,
		}
	)
	file_doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {
		"file_url": file_doc.file_url,
		"tracking_number": doc.tracking_number,
		"file_name": fname,
		"size_mm": "50x25",
	}


@frappe.whitelist()
def download_sample_sticker_8mm(sample: str):
	"""Back-compat alias — stickers are now 50×25 mm."""
	return download_sample_sticker_50x25(sample)


@frappe.whitelist()
def get_testing_request_sample_labels(testing_request: str):
	"""Unique printable QR labels for every sample on a Testing Request.

	Each label includes:
	- QR (unique sample tracking code + verify URL) as an embedded data URI
	- Sample tracking number
	- “For more information visit www.instacertify.com”
	"""
	from instacertify.utils.qr import (
		get_qr_code_data_uri,
		render_sample_sticker_50x25_png,
		sample_qr_payload,
	)
	import base64

	if not testing_request or not frappe.db.exists("IC Testing Request", testing_request):
		frappe.throw(_("Testing Request not found"))

	# Ensure samples exist so QR always has something to show
	try:
		ensure_samples_for_testing_request(testing_request)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ensure samples before QR labels")

	samples = get_samples_for_testing_request(testing_request)
	labels = []
	for row in samples:
		doc = frappe.get_doc("IC Sample Tracking", row.name)
		if not doc.tracking_number:
			continue
		if not doc.qr_code:
			_attach_sample_qr(doc)
			doc.reload()
		payload = sample_qr_payload(doc.tracking_number, doc.name)
		qr_uri = get_qr_code_data_uri(payload, box_size=8, border=1) or ""
		# Prefer embedded sticker PNG so the dialog never depends on /files URL loading
		sticker_uri = ""
		sticker_url = doc.get("qr_code") or ""
		try:
			png = render_sample_sticker_50x25_png(doc.tracking_number, payload)
			sticker_uri = "data:image/png;base64," + base64.b64encode(png).decode()
			sticker = download_sample_sticker_50x25(doc.name)
			sticker_url = (sticker or {}).get("file_url") or sticker_url
		except Exception:
			frappe.log_error(frappe.get_traceback(), "sample sticker for TR labels")
		if not qr_uri and doc.qr_code:
			# Absolute URL fallback for attached file
			qr_uri = doc.qr_code
		labels.append(
			{
				"name": doc.name,
				"tracking_number": doc.tracking_number,
				"sample_description": doc.sample_description,
				"qr_code": doc.qr_code,
				"qr_data_uri": qr_uri,
				"sticker_data_uri": sticker_uri,
				"sticker_url": sticker_url,
				"website": "www.instacertify.com",
				"info_line": "For more information visit",
				"print_format": "Instacertify Sample Sticker 50x25mm",
			}
		)

	tr = frappe.db.get_value(
		"IC Testing Request",
		testing_request,
		["name", "title", "customer", "test_name", "applicable_standard", "laboratory"],
		as_dict=True,
	) or {}
	return {
		"testing_request": testing_request,
		"title": tr.get("title") or testing_request,
		"customer": tr.get("customer"),
		"test_name": tr.get("test_name"),
		"applicable_standard": tr.get("applicable_standard"),
		"laboratory": tr.get("laboratory"),
		"labels": labels,
		"count": len(labels),
	}


def on_update_testing_request(doc, method=None):
	# Keep Sample Tracking rows in lockstep with this Testing Request
	try:
		ensure_samples_for_testing_request(doc.name)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ensure samples for testing request")

	if doc.has_value_changed("status"):
		_sync_sample_status(doc)
		_notify_status_change(doc)
	if doc.has_value_changed("laboratory") or doc.has_value_changed("customer") or doc.has_value_changed(
		"project"
	) or doc.has_value_changed("quotation"):
		_sync_sample_links_from_tr(doc)
	if doc.test_report and doc.status == "Report Available":
		doc.db_set("status", "Report Uploaded", update_modified=False)
	# When TR report is newly attached, push to linked samples + customer records
	if doc.test_report and doc.has_value_changed("test_report"):
		_propagate_report_to_samples(doc)
		try:
			from instacertify.crm.customer_data import ingest_sample_report

			# Reuse ingest with a lightweight shim (TR shares test_report field)
			ingest_sample_report(doc)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "ingest testing request report")


def after_insert_testing_request(doc, method=None):
	"""Create Sample Tracking rows as soon as a Testing Request exists."""
	if getattr(doc.flags, "ic_skip_auto_samples", False):
		if doc.status in (None, "", "Testing Request Created"):
			doc.status = "Sample Awaited"
			doc.db_set("status", "Sample Awaited", update_modified=False)
		return
	try:
		ensure_samples_for_testing_request(doc.name)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "after_insert ensure samples")
	# Move TR out of "Created" once samples are awaited from customer
	if doc.status in (None, "", "Testing Request Created"):
		doc.status = "Sample Awaited"
		doc.db_set("status", "Sample Awaited", update_modified=False)
		_sync_sample_status(doc)


def _sample_names_linked_to_tr(testing_request: str) -> list[str]:
	"""Primary testing_request link + multi-test child table links."""
	names = set(
		frappe.get_all(
			"IC Sample Tracking",
			filters={"testing_request": testing_request},
			pluck="name",
		)
	)
	if frappe.db.exists("DocType", "IC Sample Testing Link"):
		via = frappe.get_all(
			"IC Sample Testing Link",
			filters={"testing_request": testing_request, "parenttype": "IC Sample Tracking"},
			pluck="parent",
		)
		names.update(via)
	return sorted(names)

def _propagate_report_to_samples(doc):
	"""Copy test report onto linked Sample Tracking rows and stamp upload time."""
	meta = frappe.get_meta("IC Sample Tracking")
	if not meta.has_field("test_report"):
		return
	samples = _sample_names_linked_to_tr(doc.name)
	stamp = now_datetime()
	for name in samples:
		values = {
			"test_report": doc.test_report,
			"status": "Report Uploaded",
		}
		if meta.has_field("report_uploaded_on"):
			values["report_uploaded_on"] = stamp
		if meta.has_field("report_uploaded_by"):
			values["report_uploaded_by"] = frappe.session.user
		frappe.db.set_value("IC Sample Tracking", name, values, update_modified=True)


def _sync_sample_status(doc):
	"""Mirror testing-request workflow onto linked samples without wiping custody."""
	from instacertify.instacertify.doctype.ic_sample_tracking.ic_sample_tracking import (
		PRESERVE_LOCATIONS_ON_REPORT,
		STATUS_TO_LOCATION,
	)

	workflow_statuses = {
		"Testing in Progress",
		"Report Available",
		"Report Uploaded",
		"Report Shared with Customer",
		"Sample Dispatched to Laboratory",
		"Sample Received",
		"Sample Awaited",
	}
	if doc.status not in workflow_statuses and doc.status not in STATUS_TO_LOCATION:
		return

	report_statuses = {
		"Report Available",
		"Report Uploaded",
		"Report Shared with Customer",
	}

	names = _sample_names_linked_to_tr(doc.name)
	if not names:
		return
	samples = frappe.get_all(
		"IC Sample Tracking",
		filters={"name": ["in", names]},
		fields=["name", "status", "sample_location"],
	)
	for row in samples:
		if row.status == "Discarded" or row.sample_location == "Discarded":
			continue
		values = {"status": doc.status}
		# After testing completes, keep physical location (lab / warehouse / client)
		if doc.status in report_statuses:
			if row.sample_location in PRESERVE_LOCATIONS_ON_REPORT or row.sample_location:
				pass  # status only
			elif doc.status in STATUS_TO_LOCATION:
				values["sample_location"] = STATUS_TO_LOCATION[doc.status]
		elif doc.status == "Testing in Progress":
			values["sample_location"] = "At Laboratory"
		elif doc.status in STATUS_TO_LOCATION:
			# Don't yank a sample already returned / in warehouse back to transit
			if row.sample_location not in (
				"Returned to Client",
				"In Transit to Client",
				"At Instacertify Warehouse",
				"At Instacertify Storage",
			):
				values["sample_location"] = STATUS_TO_LOCATION[doc.status]
		frappe.db.set_value("IC Sample Tracking", row.name, values)


def _sync_sample_links_from_tr(doc):
	"""Push laboratory / customer / project / quotation from Testing Request onto linked samples.

	Never reassign a sample to a different laboratory (same-lab multi-test rule).
	"""
	names = _sample_names_linked_to_tr(doc.name)
	meta = frappe.get_meta("IC Sample Tracking")
	for name in names:
		sample = frappe.get_doc("IC Sample Tracking", name)
		values = {}
		if doc.laboratory:
			if sample.laboratory and sample.laboratory != doc.laboratory:
				frappe.throw(
					_(
						"Cannot change Testing Request {0} laboratory to {1}: sample {2} is already "
						"assigned to {3}. One sample cannot serve tests at different labs."
					).format(doc.name, doc.laboratory, sample.tracking_number or name, sample.laboratory),
					title=_("Same-lab only"),
				)
			if not sample.laboratory:
				values["laboratory"] = doc.laboratory
		if doc.customer:
			values["customer"] = doc.customer
		if doc.project:
			values["project"] = doc.project
		if meta.has_field("quotation") and doc.quotation:
			values["quotation"] = doc.quotation
		if values:
			for k, v in values.items():
				sample.set(k, v)
			sample.flags.ignore_permissions = True
			sample.save()


def _sample_description_from_tr(tr, index: int, total: int) -> str:
	bits = [b for b in [(tr.product or "").strip(), (tr.test_name or "").strip()] if b]
	base = " / ".join(bits) if bits else f"Sample for {tr.name}"
	if (tr.applicable_standard or "").strip():
		base = f"{base} ({tr.applicable_standard.strip()})"
	if total > 1:
		base = f"{base} — {index}/{total}"
	return base[:140]


@frappe.whitelist()
def create_testing_and_samples(
	customer: str,
	product: str | None = None,
	test_name: str | None = None,
	applicable_standard: str | None = None,
	laboratory: str | None = None,
	lab_scope_row: str | None = None,
	lab_offer: str | None = None,
	number_of_samples: int | None = 1,
	project: str | None = None,
	quotation: str | None = None,
	title: str | None = None,
	reuse_samples: str | list | None = None,
	library_buying_price: float | None = None,
	suggested_selling_price: float | None = None,
	price_currency: str | None = None,
):
	"""One-shot: create Testing Request from lab library pricing + linked samples.

	reuse_samples: optional list (or JSON) of existing IC Sample Tracking names to
	link to this TR. Allowed only when those samples already belong to the same
	laboratory (one sample → multiple tests at same lab only).

	library_buying_price / suggested_selling_price / price_currency: optional overrides
	from the Generate page so case handlers can set the buy/sell record used for
	lab purchase invoices and customer billing.
	"""
	from frappe.utils import cint, flt
	import json

	if not customer:
		frappe.throw(_("Customer is required"))
	if not frappe.db.exists("Customer", customer):
		frappe.throw(_("Customer {0} not found").format(customer))

	if isinstance(reuse_samples, str):
		reuse_samples = json.loads(reuse_samples) if reuse_samples.strip() else []
	reuse_samples = [s for s in (reuse_samples or []) if s]

	needed = max(cint(number_of_samples) or 1, 1)
	buying = 0
	selling = 0
	currency = (price_currency or "").strip() or "INR"
	scope_label = ""
	lab_loc = ""

	# Resolve lab scope / prices from laboratory library
	if laboratory and (lab_scope_row or test_name or applicable_standard):
		try:
			from instacertify.laboratory.api import get_lab_offer_details, get_lab_test_scope_details

			if lab_scope_row:
				detail = get_lab_test_scope_details(
					laboratory=laboratory,
					scope_key="",
					scope_row=lab_scope_row,
				)
			else:
				detail = get_lab_offer_details(
					lab_offer=lab_offer,
					applicable_standard=applicable_standard,
					test_name=test_name,
					laboratory=laboratory,
					scope_row=lab_scope_row,
				)
			if detail:
				buying = flt(detail.get("purchase_price") or detail.get("buying_price"))
				selling = flt(detail.get("selling_price"))
				if detail.get("currency"):
					currency = detail.get("currency") or currency
				scope_label = detail.get("label") or detail.get("scope_label") or ""
				lab_scope_row = detail.get("name") or detail.get("scope_row") or lab_scope_row
				if not test_name:
					test_name = detail.get("test_name") or test_name
				if not applicable_standard:
					applicable_standard = detail.get("applicable_standard") or applicable_standard
				if not laboratory:
					laboratory = detail.get("laboratory") or laboratory
		except Exception:
			frappe.log_error(frappe.get_traceback(), "create_testing_and_samples lab resolve")

	# Case-handler overrides from Generate page
	if library_buying_price is not None and str(library_buying_price) != "":
		buying = flt(library_buying_price)
	if suggested_selling_price is not None and str(suggested_selling_price) != "":
		selling = flt(suggested_selling_price)
	if price_currency:
		currency = str(price_currency).strip() or currency
	if currency and not frappe.db.exists("Currency", currency):
		frappe.throw(_("Currency {0} not found").format(currency))

	if laboratory and frappe.db.exists("IC Laboratory", laboratory):
		lab_loc = frappe.db.get_value("IC Laboratory", laboratory, "location") or ""

	tr_title = (title or "").strip() or " / ".join(
		[b for b in [(test_name or "").strip(), (product or "").strip()] if b]
	) or _("Testing Request")

	payload = {
		"doctype": "IC Testing Request",
		"title": tr_title[:140],
		"customer": customer,
		"number_of_samples": needed,
		"suggested_selling_price": selling,
		"library_buying_price": buying,
		"status": "Sample Awaited",
	}
	if frappe.get_meta("IC Testing Request").has_field("price_currency"):
		payload["price_currency"] = currency
	for key, val in {
		"project": project,
		"quotation": quotation,
		"product": product,
		"test_name": test_name,
		"applicable_standard": applicable_standard,
		"laboratory": laboratory,
		"lab_scope_row": lab_scope_row,
		"lab_test_scope": scope_label,
		"lab_offer": lab_offer,
	}.items():
		if val:
			payload[key] = val

	# Skip auto sample creation when reusing — we link after insert
	tr = frappe.get_doc(payload)
	if reuse_samples:
		tr.flags.ic_skip_auto_samples = True
	tr.insert(ignore_permissions=True)

	linked = []
	if reuse_samples:
		linked = link_samples_to_testing_request(tr.name, reuse_samples)
		# If fewer reused than needed, create the remainder as new samples
		have = len(linked.get("linked") or [])
		if have < needed:
			tr.db_set("number_of_samples", needed, update_modified=False)
			bundle = ensure_samples_for_testing_request(tr.name, force_sync=1)
		else:
			# number_of_samples reflects linked count for display
			tr.db_set("number_of_samples", max(needed, have), update_modified=False)
			bundle = {
				"created": [],
				"samples": get_samples_for_testing_request(tr.name),
				"count": have,
			}
	else:
		bundle = ensure_samples_for_testing_request(tr.name, force_sync=1)

	return {
		"testing_request": tr.name,
		"title": tr.title,
		"status": tr.status,
		"laboratory": laboratory,
		"laboratory_location": lab_loc,
		"library_buying_price": buying,
		"suggested_selling_price": selling,
		"samples": bundle.get("samples") or [],
		"created_samples": bundle.get("created") or [],
		"reused_samples": (linked.get("linked") if linked else []) or [],
		"sample_labels": get_testing_request_sample_labels(tr.name),
	}


@frappe.whitelist()
def list_testing_samples_board(
	customer: str | None = None,
	project: str | None = None,
	status: str | None = None,
	limit: int | None = 40,
):
	"""Board rows for the Testing & Samples page — TR + nested sample custody."""
	from frappe.utils import cint

	filters = {}
	if customer:
		filters["customer"] = customer
	if project:
		filters["project"] = project
	if status:
		filters["status"] = status

	tr_fields = [
		"name",
		"title",
		"status",
		"customer",
		"project",
		"quotation",
		"product",
		"test_name",
		"applicable_standard",
		"laboratory",
		"number_of_samples",
		"library_buying_price",
		"suggested_selling_price",
		"modified",
	]
	if frappe.get_meta("IC Testing Request").has_field("price_currency"):
		tr_fields.append("price_currency")

	trs = frappe.get_all(
		"IC Testing Request",
		filters=filters,
		fields=tr_fields,
		order_by="modified desc",
		limit_page_length=cint(limit) or 40,
	)
	lab_ids = {t.laboratory for t in trs if t.laboratory}
	lab_map = {}
	if lab_ids:
		for lab in frappe.get_all(
			"IC Laboratory",
			filters={"name": ["in", list(lab_ids)]},
			fields=["name", "laboratory_name", "location"],
		):
			lab_map[lab.name] = lab

	customers = {t.customer for t in trs if t.customer}
	customer_map = {}
	if customers:
		for c in frappe.get_all(
			"Customer",
			filters={"name": ["in", list(customers)]},
			fields=["name", "customer_name"],
		):
			customer_map[c.name] = c.customer_name or c.name

	# Latest TRF per Testing Request (for Manage TR Actions: link + PDF)
	trf_map = {}
	tr_names = [t.name for t in trs]
	if tr_names and frappe.db.exists("DocType", "IC Test Request Form"):
		for row in frappe.get_all(
			"IC Test Request Form",
			filters={"testing_request": ["in", tr_names]},
			fields=["name", "testing_request", "share_url", "pdf_file", "status", "modified"],
			order_by="modified desc",
			limit_page_length=len(tr_names) * 5,
		):
			if row.testing_request not in trf_map:
				trf_map[row.testing_request] = row

	out = []
	for tr in trs:
		lab = lab_map.get(tr.laboratory) or {}
		samples = get_samples_for_testing_request(tr.name)
		trf = trf_map.get(tr.name) or {}
		out.append(
			{
				**tr,
				"customer_name": customer_map.get(tr.customer) or tr.customer,
				"laboratory_name": lab.get("laboratory_name") or tr.laboratory,
				"laboratory_city": lab.get("location") or "",
				"samples": samples,
				"trf_name": trf.get("name") or "",
				"trf_share_url": trf.get("share_url") or "",
				"trf_pdf_file": trf.get("pdf_file") or "",
				"trf_status": trf.get("status") or "",
				"price_currency": tr.get("price_currency") or "INR",
			}
		)
	return out


@frappe.whitelist()
def update_testing_request_prices(
	testing_request: str,
	library_buying_price: float | None = None,
	suggested_selling_price: float | None = None,
	price_currency: str | None = None,
):
	"""Case handler: edit buying/selling library prices and currency on a Testing Request."""
	from frappe.utils import flt

	if not testing_request or not frappe.db.exists("IC Testing Request", testing_request):
		frappe.throw(_("Testing Request not found"))
	doc = frappe.get_doc("IC Testing Request", testing_request)
	if library_buying_price is not None:
		doc.library_buying_price = flt(library_buying_price)
	if suggested_selling_price is not None:
		doc.suggested_selling_price = flt(suggested_selling_price)
	if price_currency:
		if not frappe.db.exists("Currency", price_currency):
			frappe.throw(_("Currency {0} not found").format(price_currency))
		doc.price_currency = price_currency
	elif not doc.price_currency:
		doc.price_currency = "INR"
	doc.flags.ignore_permissions = True
	# Allow updating read-only currency fields via API for case handlers
	doc.save(ignore_permissions=True)
	return {
		"ok": 1,
		"name": doc.name,
		"library_buying_price": doc.library_buying_price,
		"suggested_selling_price": doc.suggested_selling_price,
		"price_currency": doc.price_currency or "INR",
	}


@frappe.whitelist()
def ensure_samples_for_testing_request(testing_request: str, force_sync: int | None = 0):
	"""Create missing Sample Tracking rows for a Testing Request and sync lab links.

	Uses Number of Samples. Each sample inherits customer, project, laboratory,
	and a description built from Product / Test / Standard (lab library data).

	Samples already linked via linked_tests (multi-test same lab) count toward needed.
	"""
	from frappe.utils import cint

	tr = frappe.get_doc("IC Testing Request", testing_request)
	if not tr.customer:
		frappe.throw(_("Set Customer on the Testing Request before creating samples"))

	needed = max(cint(tr.number_of_samples) or 1, 1)
	linked_names = _sample_names_linked_to_tr(tr.name)
	existing = []
	if linked_names:
		existing_fields = ["name", "laboratory", "customer", "project", "sample_description"]
		if frappe.get_meta("IC Sample Tracking").has_field("quotation"):
			existing_fields.append("quotation")
		existing = frappe.get_all(
			"IC Sample Tracking",
			filters={"name": ["in", linked_names]},
			fields=existing_fields,
			order_by="creation asc",
		)

	created = []
	for i in range(len(existing), needed):
		payload = {
			"doctype": "IC Sample Tracking",
			"customer": tr.customer,
			"project": tr.project,
			"testing_request": tr.name,
			"laboratory": tr.laboratory,
			"sample_description": _sample_description_from_tr(tr, i + 1, needed),
			"quantity": 1,
			"status": "Sample Awaited",
			"sample_location": "With Customer",
		}
		if frappe.get_meta("IC Sample Tracking").has_field("quotation") and tr.quotation:
			payload["quotation"] = tr.quotation
		doc = frappe.get_doc(payload)
		doc.insert(ignore_permissions=True)
		created.append(doc.name)

	# Sync lab / links onto existing rows — never move a sample to a different lab
	meta = frappe.get_meta("IC Sample Tracking")
	for row in existing:
		values = {}
		if tr.laboratory:
			if not row.laboratory:
				values["laboratory"] = tr.laboratory
			elif row.laboratory != tr.laboratory:
				frappe.throw(
					_(
						"Sample {0} is at laboratory {1} and cannot be synced to Testing Request {2} "
						"which uses {3}. One sample cannot serve tests at different labs."
					).format(row.name, row.laboratory, tr.name, tr.laboratory),
					title=_("Same-lab only"),
				)
		if tr.customer and row.customer != tr.customer:
			values["customer"] = tr.customer
		if tr.project and (force_sync or not row.project):
			values["project"] = tr.project
		if meta.has_field("quotation") and tr.quotation and (force_sync or not row.get("quotation")):
			values["quotation"] = tr.quotation
		if values:
			# Use document save so same-lab validation runs when linking fields change
			sample = frappe.get_doc("IC Sample Tracking", row.name)
			for k, v in values.items():
				sample.set(k, v)
			_ensure_sample_tr_link(sample, tr)
			sample.flags.ignore_permissions = True
			sample.save()

	# Ensure every linked sample has this TR in linked_tests
	for name in [r.name for r in existing] + created:
		sample = frappe.get_doc("IC Sample Tracking", name)
		if _ensure_sample_tr_link(sample, tr):
			sample.flags.ignore_permissions = True
			sample.save()

	return {
		"created": created,
		"samples": get_samples_for_testing_request(tr.name),
		"count": len(_sample_names_linked_to_tr(tr.name)),
	}


def _ensure_sample_tr_link(sample, tr) -> bool:
	"""Append TR to sample.linked_tests if missing. Returns True if sample changed."""
	changed = False
	if not sample.testing_request:
		sample.testing_request = tr.name
		changed = True
	if not sample.meta.has_field("linked_tests"):
		return changed
	existing = {row.testing_request for row in (sample.get("linked_tests") or []) if row.testing_request}
	if tr.name in existing:
		return changed
	sample.append(
		"linked_tests",
		{
			"testing_request": tr.name,
			"test_name": tr.test_name,
			"applicable_standard": tr.applicable_standard,
			"laboratory": tr.laboratory,
		},
	)
	return True


@frappe.whitelist()
def get_reusable_samples(
	customer: str,
	laboratory: str,
	project: str | None = None,
	limit: int | None = 40,
):
	"""Samples for this customer already assigned to the same laboratory.

	These can be reused for additional Testing Requests at that lab only.
	"""
	from frappe.utils import cint

	if not customer or not laboratory:
		return []
	filters = {
		"customer": customer,
		"laboratory": laboratory,
		"status": ["!=", "Discarded"],
	}
	if project:
		filters["project"] = project
	rows = frappe.get_all(
		"IC Sample Tracking",
		filters=filters,
		fields=[
			"name",
			"tracking_number",
			"status",
			"sample_location",
			"sample_description",
			"testing_request",
			"laboratory",
			"project",
			"modified",
		],
		order_by="modified desc",
		limit_page_length=cint(limit) or 40,
	)
	out = []
	for r in rows:
		linked = []
		if r.testing_request:
			linked.append(r.testing_request)
		if frappe.db.exists("DocType", "IC Sample Testing Link"):
			extra = frappe.get_all(
				"IC Sample Testing Link",
				filters={"parent": r.name, "parenttype": "IC Sample Tracking"},
				fields=["testing_request", "test_name", "applicable_standard"],
			)
			for e in extra:
				if e.testing_request and e.testing_request not in linked:
					linked.append(e.testing_request)
		lab_title = frappe.db.get_value("IC Laboratory", laboratory, "laboratory_name") or laboratory
		out.append(
			{
				**r,
				"laboratory_name": lab_title,
				"linked_testing_requests": linked,
				"linked_count": len(linked),
			}
		)
	return out


@frappe.whitelist()
def link_samples_to_testing_request(testing_request: str, samples: str | list | None = None):
	"""Link existing samples to a Testing Request (same laboratory only)."""
	import json

	if not testing_request or not frappe.db.exists("IC Testing Request", testing_request):
		frappe.throw(_("Testing Request not found"))
	tr = frappe.get_doc("IC Testing Request", testing_request)
	if not tr.laboratory:
		frappe.throw(_("Set Laboratory on the Testing Request before linking samples"))

	if isinstance(samples, str):
		samples = json.loads(samples) if samples.strip() else []
	samples = [s for s in (samples or []) if s]
	if not samples:
		frappe.throw(_("Select at least one sample to link"))

	linked = []
	for name in samples:
		if not frappe.db.exists("IC Sample Tracking", name):
			frappe.throw(_("Sample {0} not found").format(name))
		sample = frappe.get_doc("IC Sample Tracking", name)
		if sample.customer and tr.customer and sample.customer != tr.customer:
			frappe.throw(
				_("Sample {0} belongs to a different customer and cannot be linked.").format(
					sample.tracking_number or name
				)
			)
		if sample.laboratory and sample.laboratory != tr.laboratory:
			lab_a = frappe.db.get_value("IC Laboratory", sample.laboratory, "laboratory_name") or sample.laboratory
			lab_b = frappe.db.get_value("IC Laboratory", tr.laboratory, "laboratory_name") or tr.laboratory
			frappe.throw(
				_(
					"Sample {0} is for {1} and cannot be used for Testing Request {2} at {3}. "
					"One sample can cover multiple tests only at the same laboratory."
				).format(sample.tracking_number or name, lab_a, tr.name, lab_b),
				title=_("Same-lab only"),
			)
		if not sample.laboratory:
			sample.laboratory = tr.laboratory
		_ensure_sample_tr_link(sample, tr)
		sample.flags.ignore_permissions = True
		sample.save()
		linked.append(sample.name)

	frappe.db.commit()
	return {"linked": linked, "samples": get_samples_for_testing_request(testing_request)}


@frappe.whitelist()
def get_samples_for_testing_request(testing_request: str):
	"""List Sample Tracking rows linked to a Testing Request (primary or multi-test table)."""
	names = _sample_names_linked_to_tr(testing_request)
	if not names:
		return []
	rows = frappe.get_all(
		"IC Sample Tracking",
		filters={"name": ["in", names]},
		fields=[
			"name",
			"tracking_number",
			"status",
			"sample_location",
			"laboratory",
			"sample_description",
			"location_updated_on",
			"dispatch_date",
			"sample_received_date",
			"test_report",
			"testing_request",
		],
		order_by="creation asc",
	)
	# Resolve lab titles + linked TR count
	lab_names = {r.laboratory for r in rows if r.laboratory}
	lab_map = {}
	if lab_names:
		for lab in frappe.get_all(
			"IC Laboratory",
			filters={"name": ["in", list(lab_names)]},
			fields=["name", "laboratory_name", "location"],
		):
			lab_map[lab.name] = lab
	for r in rows:
		lab = lab_map.get(r.laboratory) or {}
		r["laboratory_name"] = lab.get("laboratory_name") or r.laboratory
		r["laboratory_city"] = lab.get("location") or ""
		r["custody_label"] = r.sample_location or r.status or "—"
		link_count = 0
		if frappe.db.exists("DocType", "IC Sample Testing Link"):
			link_count = frappe.db.count(
				"IC Sample Testing Link",
				{"parent": r.name, "parenttype": "IC Sample Tracking"},
			)
		r["linked_test_count"] = max(link_count, 1 if r.testing_request else 0)
	return rows


@frappe.whitelist()
def get_linked_testing_overview(project: str | None = None, customer: str | None = None):
	"""Testing Requests + Samples for a Project or Customer (desk panels)."""
	filters = {}
	if project:
		filters["project"] = project
	elif customer:
		filters["customer"] = customer
	else:
		frappe.throw(_("Pass project or customer"))

	testing = frappe.get_all(
		"IC Testing Request",
		filters=filters,
		fields=[
			"name",
			"title",
			"status",
			"product",
			"test_name",
			"applicable_standard",
			"laboratory",
			"number_of_samples",
			"quotation",
			"project",
			"customer",
			"modified",
		],
		order_by="modified desc",
		limit_page_length=50,
	)
	sample_filters = dict(filters)
	samples = frappe.get_all(
		"IC Sample Tracking",
		filters=sample_filters,
		fields=[
			"name",
			"tracking_number",
			"status",
			"sample_location",
			"laboratory",
			"testing_request",
			"sample_description",
			"project",
			"customer",
			"modified",
		],
		order_by="modified desc",
		limit_page_length=80,
	)
	lab_ids = {r.laboratory for r in testing + samples if r.laboratory}
	lab_map = {}
	if lab_ids:
		for lab in frappe.get_all(
			"IC Laboratory",
			filters={"name": ["in", list(lab_ids)]},
			fields=["name", "laboratory_name", "location"],
		):
			lab_map[lab.name] = lab
	for row in testing + samples:
		lab = lab_map.get(row.laboratory) or {}
		row["laboratory_name"] = lab.get("laboratory_name") or row.laboratory
		row["laboratory_city"] = lab.get("location") or ""
	for s in samples:
		s["custody_label"] = s.sample_location or s.status or "—"

	custody_counts = {}
	for s in samples:
		key = s.sample_location or "Unset"
		custody_counts[key] = custody_counts.get(key, 0) + 1

	return {
		"testing_requests": testing,
		"samples": samples,
		"custody_counts": custody_counts,
	}


@frappe.whitelist()
def set_sample_location(sample: str, location: str, discard_reason: str | None = None):
	"""Set physical custody location on a sample record."""
	from instacertify.instacertify.doctype.ic_sample_tracking.ic_sample_tracking import (
		LOCATION_TO_STATUS,
		SAMPLE_LOCATIONS,
	)

	# Accept legacy storage label
	if location == "At Instacertify Storage":
		location = "At Instacertify Warehouse"
	if location not in SAMPLE_LOCATIONS:
		frappe.throw(_("Invalid sample location: {0}").format(location))
	doc = frappe.get_doc("IC Sample Tracking", sample)
	doc.sample_location = location
	doc.status = LOCATION_TO_STATUS.get(location, doc.status)
	if location == "Discarded" and discard_reason:
		doc.discard_reason = discard_reason
	doc.save(ignore_permissions=True)

	# Nudge parent Testing Request status when sample reaches the lab / office
	if doc.testing_request and location in (
		"At Instacertify Office",
		"In Transit to Lab",
		"At Laboratory",
		"At Instacertify Warehouse",
		"Returned to Client",
	):
		_maybe_advance_testing_request_from_sample(doc)

	return doc.as_dict()


def _maybe_advance_testing_request_from_sample(sample):
	"""Advance TR status from sample custody moves (does not move backward)."""
	tr_name = sample.testing_request
	if not tr_name or not frappe.db.exists("IC Testing Request", tr_name):
		return
	tr_status = frappe.db.get_value("IC Testing Request", tr_name, "status")
	loc = sample.sample_location
	order = [
		"Testing Request Created",
		"Sample Awaited",
		"Sample Received",
		"Sample Dispatched to Laboratory",
		"Testing in Progress",
		"Report Available",
		"Report Uploaded",
		"Report Shared with Customer",
	]
	target = None
	if loc == "At Instacertify Office":
		target = "Sample Received"
	elif loc in ("In Transit to Lab",):
		target = "Sample Dispatched to Laboratory"
	elif loc == "At Laboratory":
		target = "Testing in Progress"
	# Warehouse / returned to client after testing — leave TR on report workflow
	if not target:
		return
	try:
		cur_i = order.index(tr_status) if tr_status in order else -1
		tgt_i = order.index(target)
	except ValueError:
		return
	if tgt_i > cur_i:
		frappe.db.set_value("IC Testing Request", tr_name, "status", target, update_modified=True)


@frappe.whitelist()
def get_sample_custody_summary():
	"""Counts of samples by physical location for management views."""
	from instacertify.instacertify.doctype.ic_sample_tracking.ic_sample_tracking import (
		SAMPLE_LOCATIONS,
	)

	rows = frappe.db.sql(
		"""
		select ifnull(sample_location, '') as sample_location, count(*) as count
		from `tabIC Sample Tracking`
		group by ifnull(sample_location, '')
		""",
		as_dict=True,
	)
	counts = {loc: 0 for loc in SAMPLE_LOCATIONS}
	counts["Unset"] = 0
	for r in rows:
		loc = r.sample_location or "Unset"
		if loc in counts:
			counts[loc] = int(r.count or 0)
		else:
			counts["Unset"] = counts.get("Unset", 0) + int(r.count or 0)
	return counts


def _notify_status_change(doc):
	from instacertify.team.assignees import get_assignee_users

	users = get_assignee_users(doc, primary_field="assigned_person") + [
		doc.owner,
		"Administrator",
	]
	for user in set(filter(None, users)):
		if not frappe.db.exists("User", user):
			continue
		try:
			frappe.get_doc(
				{
					"doctype": "Notification Log",
					"subject": f"Testing Request {doc.name}: {doc.status}",
					"email_content": f"Status changed to {doc.status}",
					"document_type": "IC Testing Request",
					"document_name": doc.name,
					"for_user": user,
					"type": "Alert",
					"from_user": frappe.session.user,
				}
			).insert(ignore_permissions=True)
		except Exception:
			pass


@frappe.whitelist()
def share_report_with_customer(testing_request: str):
	from instacertify.crm.report_share import share_from_testing_request

	payload = share_from_testing_request(testing_request)
	return {
		"url": payload.get("share_url"),
		"access_code": payload.get("access_code"),
		"share_token": payload.get("share_token"),
		"name": payload.get("name"),
	}


@frappe.whitelist()
def upload_sample_report(sample: str, file_url: str):
	"""Upload / replace test report PDF on Sample Tracking when status is Report Available.

	Stamps date/time, sets status to Report Uploaded, syncs linked Testing Request,
	and writes the file into Customer records for download.
	"""
	from instacertify.utils.files import assert_internal_file

	if not sample:
		frappe.throw(_("Sample is required"))
	file_url = assert_internal_file(file_url, _("Test Report PDF"))
	_assert_pdf_report(file_url)

	doc = frappe.get_doc("IC Sample Tracking", sample)
	if doc.status not in (
		"Report Available",
		"Report Uploaded",
		"Report Shared with Customer",
		"Testing in Progress",
		"At Laboratory",
	):
		frappe.throw(
			_("Set status to Report Available before uploading the test report (current: {0})").format(
				doc.status
			)
		)

	doc.test_report = file_url
	doc.report_uploaded_on = now_datetime()
	doc.report_uploaded_by = frappe.session.user
	doc.status = "Report Uploaded"
	doc.save(ignore_permissions=True)

	# Mirror onto linked Testing Request so Share Report still works there
	if doc.testing_request and frappe.db.exists("IC Testing Request", doc.testing_request):
		tr = frappe.get_doc("IC Testing Request", doc.testing_request)
		tr.test_report = file_url
		if tr.status in (
			"Report Available",
			"Testing in Progress",
			"At Laboratory",
			"Sample Dispatched to Laboratory",
		):
			tr.status = "Report Uploaded"
		tr.save(ignore_permissions=True)

	# Customer records ingest runs from IC Sample Tracking.on_update
	doc.reload()
	return {
		"name": doc.name,
		"status": doc.status,
		"test_report": doc.test_report,
		"report_uploaded_on": str(doc.report_uploaded_on),
		"report_uploaded_by": doc.report_uploaded_by,
		"customer": doc.customer,
	}


@frappe.whitelist()
def delete_sample_report(sample: str):
	"""Remove the uploaded test report so a new PDF can be uploaded (status → Report Available)."""
	doc = frappe.get_doc("IC Sample Tracking", sample)
	if not doc.test_report:
		frappe.throw(_("No test report to delete"))

	old_url = doc.test_report
	doc.test_report = None
	doc.report_uploaded_on = None
	doc.report_uploaded_by = None
	if doc.status in ("Report Uploaded", "Report Shared with Customer"):
		doc.status = "Report Available"
	doc.save(ignore_permissions=True)

	if doc.testing_request and frappe.db.exists("IC Testing Request", doc.testing_request):
		tr = frappe.get_doc("IC Testing Request", doc.testing_request)
		if (tr.test_report or "") == old_url:
			tr.test_report = None
			if tr.status in ("Report Uploaded", "Report Shared with Customer"):
				tr.status = "Report Available"
			tr.save(ignore_permissions=True)

	doc.reload()
	return {
		"name": doc.name,
		"status": doc.status,
		"test_report": doc.test_report,
		"cleared": old_url,
	}


def _assert_pdf_report(file_url: str):
	"""Only accept PDF test reports."""
	name = (file_url or "").split("?")[0].rsplit("/", 1)[-1].lower()
	if name.endswith(".pdf"):
		return
	ftype = frappe.db.get_value("File", {"file_url": file_url}, "file_type") or ""
	if str(ftype).strip().upper() == "PDF":
		return
	frappe.throw(_("Test report must be a PDF file (.pdf)"))


@frappe.whitelist()
def mark_sample_report_available(sample: str):
	"""Mark sample as Report Available so ops can upload the lab report PDF."""
	doc = frappe.get_doc("IC Sample Tracking", sample)
	if doc.status == "Discarded":
		frappe.throw(_("Cannot mark a discarded sample as Report Available"))
	doc.status = "Report Available"
	doc.save(ignore_permissions=True)
	return doc.as_dict()


@frappe.whitelist()
def mark_sample_received(sample: str, quantity=None, condition=None, description=None):
	doc = frappe.get_doc("IC Sample Tracking", sample)
	doc.status = "Sample Received"
	doc.sample_location = "At Instacertify Office"
	doc.sample_received_date = frappe.utils.today()
	doc.received_by = frappe.session.user
	if quantity:
		doc.quantity = quantity
	if condition:
		doc.sample_condition = condition
	if description:
		doc.sample_description = description
	doc.save(ignore_permissions=True)
	if not doc.qr_code:
		_attach_sample_qr(doc)
	for user in set(filter(None, [doc.owner, "Administrator"])):
		try:
			frappe.get_doc(
				{
					"doctype": "Notification Log",
					"subject": f"Sample Received: {doc.tracking_number}",
					"email_content": f"Sample {doc.tracking_number} received at Instacertify office",
					"document_type": "IC Sample Tracking",
					"document_name": doc.name,
					"for_user": user,
					"type": "Alert",
					"from_user": frappe.session.user,
				}
			).insert(ignore_permissions=True)
		except Exception:
			pass
	return doc.as_dict()


@frappe.whitelist()
def create_testing_requests_from_quotation(quotation: str, project: str | None = None):
	"""Create IC Testing Request rows from Testing Quotation lab/test lines.

	Uses Laboratory Library assignments so ops can execute per lab scope.
	"""
	qt = frappe.get_doc("Quotation", quotation)
	if qt.quotation_to != "Customer" or not qt.party_name:
		frappe.throw(_("Quotation must be for a Customer"))

	if not project:
		project = frappe.db.get_value("Project", {"ic_quotation": qt.name}, "name")

	created = []
	existing = []
	for row in qt.get("ic_test_items") or []:
		if not row.test_name:
			continue
		filters = {
			"quotation": qt.name,
			"test_name": row.test_name,
			"customer": qt.party_name,
		}
		if row.laboratory:
			filters["laboratory"] = row.laboratory
		found = frappe.db.exists("IC Testing Request", filters)
		if found:
			existing.append(found)
			continue

		from instacertify.team.assignees import append_assignees_from_users, get_assignee_users

		title = f"{row.test_name} – {row.product_name or qt.party_name}"
		assignees = get_assignee_users(qt, primary_field="ic_primary_assignee")
		if not assignees:
			seed = qt.get("ic_assigned_salesperson") or qt.owner
			if seed:
				assignees = [seed]
		doc = frappe.get_doc(
			{
				"doctype": "IC Testing Request",
				"title": title[:140],
				"customer": qt.party_name,
				"project": project,
				"quotation": qt.name,
				"product": row.product_name or qt.ic_service_name or "Product",
				"test_name": row.test_name,
				"applicable_standard": row.applicable_standard,
				"number_of_samples": row.number_of_samples or 1,
				"laboratory": row.laboratory,
				"lab_test_scope": row.get("lab_test_scope"),
				"lab_scope_row": row.get("lab_scope_row"),
				"suggested_selling_price": row.get("suggested_selling_price")
				or row.get("per_unit_charges"),
				"testing_timeline": row.testing_timeline,
				"assigned_person": (assignees[0] if assignees else None),
				"status": "Testing Request Created",
				"priority": "Medium",
			}
		)
		append_assignees_from_users(doc, assignees)
		doc.insert(ignore_permissions=True)
		created.append(doc.name)

	return {"created": created, "existing": existing, "project": project}
