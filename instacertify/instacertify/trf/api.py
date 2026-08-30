# Copyright (c) Instacertify
"""Test Request Form (TRF) — customer fill link + staff fill + PDF with sample QR."""

from __future__ import annotations

import secrets

import frappe
from frappe import _
from frappe.utils import now_datetime

from instacertify.documents.api import _assert_allowed_upload


OPEN_STATUSES = {"Draft", "Sent to Customer", "Submitted by Customer", "Under Review"}
FILLED_STATUSES = {"Submitted by Customer", "Under Review", "PDF Generated", "Completed"}


def _portal_url(token: str) -> str:
	base = None
	try:
		base = frappe.db.get_single_value("IC Settings", "portal_base_url")
	except Exception:
		base = None
	path = f"/ic-trf/{token}"
	if base:
		return str(base).rstrip("/") + path
	return frappe.utils.get_url(path)


def _pick_sample_for_tr(testing_request: str) -> dict | None:
	"""Prefer first linked sample so TRF QR matches product sample QR."""
	from instacertify.testing.events import get_samples_for_testing_request

	rows = get_samples_for_testing_request(testing_request) or []
	if not rows:
		return None
	row = rows[0]
	doc = frappe.get_doc("IC Sample Tracking", row.name)
	if not doc.qr_code:
		try:
			from instacertify.testing.events import _attach_sample_qr

			_attach_sample_qr(doc)
			doc.reload()
		except Exception:
			frappe.log_error(frappe.get_traceback(), "TRF attach sample QR")
	return {
		"name": doc.name,
		"tracking_number": doc.tracking_number,
		"qr_code": doc.qr_code,
		"sample_description": doc.sample_description,
	}


@frappe.whitelist()
def create_or_get_trf(testing_request: str, share: int = 0):
	"""Create (or reuse open) TRF for a Testing Request. Optionally share with customer."""
	if not testing_request or not frappe.db.exists("IC Testing Request", testing_request):
		frappe.throw(_("Testing Request not found"))

	tr = frappe.get_doc("IC Testing Request", testing_request)
	existing = frappe.db.get_value(
		"IC Test Request Form",
		{
			"testing_request": testing_request,
			"status": ["in", list(OPEN_STATUSES) + ["PDF Generated"]],
		},
		"name",
		order_by="modified desc",
	)
	sample = _pick_sample_for_tr(testing_request)
	if existing:
		doc = frappe.get_doc("IC Test Request Form", existing)
	else:
		instructions = (
			"<p>Please complete this <b>Test Request Form (TRF)</b> for your testing case.</p>"
			"<ul>"
			"<li>Sample name (description of the sample)</li>"
			"<li>Sample quantity, model no, brand name, brand logo</li>"
			"<li>Rated input / product specification</li>"
			"<li>Testing requested and applicable standard</li>"
			"<li>Description and other remarks</li>"
			"</ul>"
			"<p>The form carries the <b>same QR code as your product sample</b> for matching.</p>"
		)
		doc = frappe.get_doc(
			{
				"doctype": "IC Test Request Form",
				"title": f"TRF — {tr.name}" + (f" / {tr.title}" if tr.title else ""),
				"testing_request": tr.name,
				"customer": tr.customer,
				"project": tr.project,
				"quotation": tr.quotation,
				"assigned_to": frappe.session.user,
				"status": "Draft",
				"filled_by": "Staff",
				"customer_instructions": instructions,
				"testing_requested": tr.test_name or "",
				"applicable_standard": tr.applicable_standard or "",
				"sample_name": (sample or {}).get("sample_description") or tr.product or "",
				"sample_quantity": str(tr.number_of_samples or "") or "",
			}
		)
		if sample:
			doc.sample_tracking = sample["name"]
			doc.sample_tracking_number = sample.get("tracking_number")
			doc.sample_qr_code = sample.get("qr_code")
		doc.insert(ignore_permissions=True)

	# Refresh sample QR link if missing
	if sample and (not doc.sample_tracking or not doc.sample_qr_code):
		doc.sample_tracking = sample["name"]
		doc.sample_tracking_number = sample.get("tracking_number")
		doc.sample_qr_code = sample.get("qr_code")
		doc.save(ignore_permissions=True)

	if int(share or 0):
		return share_trf(doc.name)
	return {
		"name": doc.name,
		"status": doc.status,
		"share_url": doc.share_url,
		"testing_request": doc.testing_request,
	}


@frappe.whitelist()
def share_trf(name: str):
	"""Generate / refresh customer fill link for a TRF."""
	doc = frappe.get_doc("IC Test Request Form", name)
	if not doc.share_token:
		doc.share_token = secrets.token_urlsafe(24)
	if doc.status in (None, "", "Draft"):
		doc.status = "Sent to Customer"
	doc.sent_on = now_datetime()
	url = _portal_url(doc.share_token)
	doc.share_url = url
	doc.save(ignore_permissions=True)
	return {"url": url, "token": doc.share_token, "name": doc.name, "status": doc.status}


@frappe.whitelist(allow_guest=True)
def get_trf_by_token(token: str):
	name = frappe.db.get_value("IC Test Request Form", {"share_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid Test Request Form link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Test Request Form", name)
	qr_data_uri = ""
	try:
		from instacertify.utils.qr import get_qr_code_data_uri, sample_qr_payload

		trk = doc.sample_tracking_number or ""
		if trk:
			qr_data_uri = get_qr_code_data_uri(sample_qr_payload(trk, doc.sample_tracking), box_size=6, border=1)
	except Exception:
		pass
	can_pdf = doc.status in FILLED_STATUSES or bool(doc.pdf_file)
	return {
		"name": doc.name,
		"title": doc.title,
		"status": doc.status,
		"customer_instructions": doc.customer_instructions,
		"testing_request": doc.testing_request,
		"sample_tracking_number": doc.sample_tracking_number,
		"sample_qr_code": doc.sample_qr_code,
		"qr_data_uri": qr_data_uri,
		"sample_name": doc.sample_name,
		"sample_quantity": doc.sample_quantity,
		"rated_input": doc.rated_input,
		"model_no": doc.model_no,
		"brand_name": doc.brand_name,
		"brand_logo": doc.brand_logo,
		"testing_requested": doc.testing_requested,
		"applicable_standard": doc.applicable_standard,
		"description": doc.description,
		"other_remarks": doc.other_remarks,
		"pdf_file": doc.pdf_file if can_pdf else "",
		"can_generate_pdf": can_pdf,
		"read_only": doc.status in ("Completed", "Cancelled"),
		"portal_notice": _(
			"This is the Test Request Form (TRF). Fill sample and product details here. "
			"The QR matches your product sample. This link does not provide ERP access."
		),
	}


@frappe.whitelist(allow_guest=True)
def save_trf(
	token: str,
	sample_name: str | None = None,
	sample_quantity: str | None = None,
	rated_input: str | None = None,
	model_no: str | None = None,
	brand_name: str | None = None,
	brand_logo: str | None = None,
	testing_requested: str | None = None,
	applicable_standard: str | None = None,
	description: str | None = None,
	other_remarks: str | None = None,
	as_staff: int = 0,
):
	name = frappe.db.get_value("IC Test Request Form", {"share_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid Test Request Form link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Test Request Form", name)
	if doc.status not in OPEN_STATUSES and not (frappe.session.user != "Guest" and int(as_staff or 0)):
		frappe.throw(_("This Test Request Form is closed"), frappe.PermissionError)

	if brand_logo:
		_assert_allowed_upload(brand_logo)
		doc.brand_logo = brand_logo

	doc.sample_name = sample_name if sample_name is not None else doc.sample_name
	doc.sample_quantity = sample_quantity if sample_quantity is not None else doc.sample_quantity
	doc.rated_input = rated_input if rated_input is not None else doc.rated_input
	doc.model_no = model_no if model_no is not None else doc.model_no
	doc.brand_name = brand_name if brand_name is not None else doc.brand_name
	doc.testing_requested = testing_requested if testing_requested is not None else doc.testing_requested
	doc.applicable_standard = (
		applicable_standard if applicable_standard is not None else doc.applicable_standard
	)
	doc.description = description if description is not None else doc.description
	doc.other_remarks = other_remarks if other_remarks is not None else doc.other_remarks

	is_guest = frappe.session.user == "Guest"
	if is_guest:
		doc.status = "Submitted by Customer"
		doc.submitted_on = now_datetime()
		doc.filled_by = "Customer" if doc.filled_by in (None, "", "Customer") else "Both"
	else:
		if doc.status == "Draft":
			doc.status = "Under Review"
		doc.filled_by = "Staff" if doc.filled_by in (None, "", "Staff") else "Both"
		if not doc.submitted_on and doc.sample_name:
			doc.submitted_on = now_datetime()

	doc.save(ignore_permissions=True)
	_sync_to_sample(doc)
	return {
		"ok": 1,
		"status": doc.status,
		"name": doc.name,
		"can_generate_pdf": 1,
	}


@frappe.whitelist()
def save_trf_staff(name: str, **kwargs):
	"""Staff save from desk (case handler can fill the same fields)."""
	doc = frappe.get_doc("IC Test Request Form", name)
	for key in (
		"sample_name",
		"sample_quantity",
		"rated_input",
		"model_no",
		"brand_name",
		"brand_logo",
		"testing_requested",
		"applicable_standard",
		"description",
		"other_remarks",
	):
		if key in kwargs and kwargs[key] is not None:
			setattr(doc, key, kwargs[key])
	if doc.brand_logo:
		_assert_allowed_upload(doc.brand_logo)
	if doc.status == "Draft":
		doc.status = "Under Review"
	doc.filled_by = "Staff" if doc.filled_by in (None, "", "Staff") else "Both"
	if not doc.submitted_on and doc.sample_name:
		doc.submitted_on = now_datetime()
	doc.save(ignore_permissions=False)
	_sync_to_sample(doc)
	return {"ok": 1, "status": doc.status, "name": doc.name}


def _sync_to_sample(doc):
	"""Push sample name/qty onto linked sample tracking."""
	if not doc.sample_tracking or not frappe.db.exists("IC Sample Tracking", doc.sample_tracking):
		return
	vals = {}
	if doc.sample_name:
		vals["sample_description"] = doc.sample_name
	if doc.sample_quantity and frappe.get_meta("IC Sample Tracking").has_field("quantity"):
		try:
			vals["quantity"] = float(str(doc.sample_quantity).split()[0])
		except Exception:
			pass
	if vals:
		frappe.db.set_value("IC Sample Tracking", doc.sample_tracking, vals, update_modified=False)


@frappe.whitelist(allow_guest=True)
def generate_trf_pdf(name: str | None = None, token: str | None = None):
	"""Generate TRF PDF (staff by name, or customer by token after submit)."""
	if token:
		name = frappe.db.get_value("IC Test Request Form", {"share_token": token}, "name")
	if not name:
		frappe.throw(_("Test Request Form not found"))
	doc = frappe.get_doc("IC Test Request Form", name)

	# Guest may only generate after the form is filled/submitted
	if frappe.session.user == "Guest":
		if not token or doc.share_token != token:
			frappe.throw(_("Not permitted"), frappe.PermissionError)
		if doc.status not in FILLED_STATUSES and not (doc.sample_name and doc.brand_name):
			frappe.throw(_("Submit the form before generating the PDF"))

	# Ensure sample QR is present
	if not doc.sample_qr_code and doc.testing_request:
		sample = _pick_sample_for_tr(doc.testing_request)
		if sample:
			doc.sample_tracking = sample["name"]
			doc.sample_tracking_number = sample.get("tracking_number")
			doc.sample_qr_code = sample.get("qr_code")
			doc.save(ignore_permissions=True)

	from instacertify.utils.pdf import make_pdf

	# Elevate for print + PDF (Guest has no print permission on TRF)
	prev = frappe.session.user
	try:
		if prev == "Guest":
			frappe.set_user("Administrator")
		html = frappe.get_print(
			"IC Test Request Form",
			doc.name,
			print_format="Instacertify Test Request Form",
			no_letterhead=1,
		)
		pdf_bytes = make_pdf(html)
	finally:
		if prev == "Guest":
			frappe.set_user(prev)

	fname = f"TRF-{doc.name}.pdf".replace("/", "-")
	existing = frappe.db.get_value(
		"File",
		{
			"file_name": fname,
			"attached_to_doctype": "IC Test Request Form",
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
			"content": pdf_bytes,
			"is_private": 0,
			"attached_to_doctype": "IC Test Request Form",
			"attached_to_name": doc.name,
			"attached_to_field": "pdf_file",
		}
	)
	file_doc.insert(ignore_permissions=True)
	doc.pdf_file = file_doc.file_url
	if doc.status in ("Submitted by Customer", "Under Review", "Sent to Customer", "Draft"):
		doc.status = "PDF Generated"
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {
		"ok": 1,
		"file_url": file_doc.file_url,
		"file_name": fname,
		"name": doc.name,
		"status": doc.status,
	}
