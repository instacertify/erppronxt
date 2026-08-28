# Copyright (c) Instacertify
"""Document request portal APIs — customer uploads, remarks, sample POD/tracking."""

from __future__ import annotations

import secrets

import frappe
from frappe import _
from frappe.utils import now_datetime, today


ALLOWED_UPLOAD_EXTENSIONS = {
	".pdf",
	".png",
	".jpg",
	".jpeg",
	".webp",
	".gif",
	".bmp",
	".tif",
	".tiff",
	".xls",
	".xlsx",
	".csv",
	".doc",
	".docx",
}

OPEN_DOC_STATUSES = {
	"Sent to Customer",
	"Partially Uploaded",
	"Under Review",
	"Draft",
}


def _assert_allowed_upload(file_url: str | None):
	"""Accept only local File attachments with allowlisted extensions."""
	from instacertify.utils.files import assert_internal_file

	url = assert_internal_file(file_url, "File")
	fname = url.rsplit("/", 1)[-1].lower()
	ext = ""
	if "." in fname:
		ext = "." + fname.rsplit(".", 1)[-1]
	if ext not in ALLOWED_UPLOAD_EXTENSIONS:
		frappe.throw(
			_(
				"File type not allowed. Upload PDF, image (PNG/JPG/WEBP/GIF/TIFF), Excel/CSV, or Word documents."
			)
		)
	return url


def _assert_doc_request_open(doc):
	status = doc.status or "Draft"
	if status not in OPEN_DOC_STATUSES and status not in (
		"Sent to Customer",
		"Partially Uploaded",
		"Under Review",
	):
		frappe.throw(_("This document checklist is closed for uploads"), frappe.PermissionError)


def _assert_manager():
	roles = set(frappe.get_roles())
	if roles.intersection({"System Manager", "IC Admin", "IC Senior Operations", "IC Operations Manager"}):
		return
	frappe.throw(_("Only managers or admin can delete or replace customer documents"))


@frappe.whitelist()
def share_document_request(document_request: str):
	doc = frappe.get_doc("IC Document Request", document_request)
	if not doc.share_token:
		doc.share_token = secrets.token_urlsafe(24)
	doc.status = "Sent to Customer"
	doc.sent_on = now_datetime()
	doc.save(ignore_permissions=True)
	url = frappe.utils.get_url(f"/ic-documents/{doc.share_token}")
	return {"url": url, "token": doc.share_token}


@frappe.whitelist()
def create_document_request_for_project(project: str, title: str | None = None, template: str | None = None):
	"""Create (or reuse draft) document checklist for a project and return share link."""
	proj = frappe.get_doc("Project", project)
	if not proj.customer:
		frappe.throw(_("Project must have a Customer before sharing a document checklist"))

	existing = frappe.db.get_value(
		"IC Document Request",
		{"project": project, "status": ["in", ["Draft", "Sent to Customer", "Partially Uploaded"]]},
		"name",
		order_by="modified desc",
	)
	if existing:
		doc = frappe.get_doc("IC Document Request", existing)
	else:
		doc = frappe.get_doc(
			{
				"doctype": "IC Document Request",
				"title": title or f"Documents for {proj.project_name or proj.name}",
				"customer": proj.customer,
				"project": proj.name,
				"assigned_to": frappe.session.user,
				"status": "Draft",
			}
		)
		doc.insert(ignore_permissions=True)

	if template and not doc.items:
		apply_checklist_template(doc.name, template)
		doc.reload()
	elif not doc.items:
		# Sensible default checklist
		for name, cat in (
			("Company Registration / GST", "Customer Documents"),
			("Product Datasheet / Specs", "Technical Documents"),
			("Authorization Letter", "Applications"),
			("Sample Dispatch POD", "Other"),
		):
			doc.append(
				"items",
				{"document_name": name, "category": cat, "is_mandatory": 1, "status": "Pending"},
			)
		doc.save(ignore_permissions=True)

	return share_document_request(doc.name) | {"document_request": doc.name}


@frappe.whitelist()
def apply_checklist_template(document_request: str, template: str):
	doc = frappe.get_doc("IC Document Request", document_request)
	tmpl = frappe.get_doc("IC Document Checklist Template", template)
	doc.set("items", [])
	for row in tmpl.items or []:
		doc.append(
			"items",
			{
				"document_name": row.document_name,
				"category": row.category,
				"is_mandatory": row.is_mandatory,
				"status": "Pending",
			},
		)
	doc.save(ignore_permissions=True)
	return doc.as_dict()


@frappe.whitelist(allow_guest=True)
def get_document_request_by_token(token: str):
	name = frappe.db.get_value("IC Document Request", {"share_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid document link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Document Request", name)
	return {
		"title": doc.title,
		"status": doc.status,
		"courier_name": doc.get("courier_name"),
		"tracking_number": doc.get("tracking_number"),
		"dispatch_date": str(doc.get("dispatch_date") or ""),
		"pod_attachment": doc.get("pod_attachment"),
		"sample_dispatch_remarks": doc.get("sample_dispatch_remarks"),
		"portal_notice": _(
			"Upload the requested documents and sample dispatch details here. This link does not provide access to Instacertify ERP."
		),
		"allowed_types": "PDF, images (PNG/JPG/WEBP/GIF/TIFF), Excel/CSV, Word",
		"items": [
			{
				"idx": row.idx,
				"name": row.name,
				"document_name": row.document_name,
				"category": row.category,
				"is_mandatory": row.is_mandatory,
				"status": row.status,
				"uploaded_file": row.uploaded_file,
				"customer_remarks": row.get("customer_remarks"),
				"review_remarks": row.review_remarks,
			}
			for row in doc.items
		],
	}


@frappe.whitelist(allow_guest=True)
def upload_document_item(token: str, item_name: str, file_url: str, remarks: str | None = None):
	parent = frappe.db.get_value("IC Document Request", {"share_token": token}, "name")
	if not parent:
		frappe.throw(_("Invalid document link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Document Request", parent)
	_assert_doc_request_open(doc)
	file_url = _assert_allowed_upload(file_url)
	updated_row = None
	for row in doc.items:
		if row.name == item_name:
			row.uploaded_file = file_url
			row.status = "Uploaded"
			row.uploaded_on = now_datetime()
			if remarks is not None:
				row.customer_remarks = remarks
			updated_row = row
			break
	if not updated_row:
		frappe.throw(_("Document item not found"))
	pending = any(r.status == "Pending" for r in doc.items)
	doc.status = "Partially Uploaded" if pending else "Under Review"
	doc.save(ignore_permissions=True)

	_log_customer_upload(doc, updated_row)
	_notify_upload(doc)
	return {"status": doc.status, "item": updated_row.name}


@frappe.whitelist(allow_guest=True)
def save_item_remarks(token: str, item_name: str, remarks: str):
	parent = frappe.db.get_value("IC Document Request", {"share_token": token}, "name")
	if not parent:
		frappe.throw(_("Invalid document link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Document Request", parent)
	_assert_doc_request_open(doc)
	for row in doc.items:
		if row.name == item_name:
			row.customer_remarks = remarks
			doc.save(ignore_permissions=True)
			return {"ok": 1}
	frappe.throw(_("Document item not found"))


@frappe.whitelist(allow_guest=True)
def save_sample_dispatch(
	token: str,
	courier_name: str | None = None,
	tracking_number: str | None = None,
	dispatch_date: str | None = None,
	pod_attachment: str | None = None,
	sample_dispatch_remarks: str | None = None,
):
	"""Customer submits sample courier / POD / tracking for backend access."""
	parent = frappe.db.get_value("IC Document Request", {"share_token": token}, "name")
	if not parent:
		frappe.throw(_("Invalid document link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Document Request", parent)
	_assert_doc_request_open(doc)
	values = {
		"courier_name": courier_name,
		"tracking_number": tracking_number,
		"dispatch_date": dispatch_date or None,
		"sample_dispatch_remarks": sample_dispatch_remarks,
	}
	if pod_attachment:
		_assert_allowed_upload(pod_attachment)
		values["pod_attachment"] = pod_attachment
	frappe.db.set_value("IC Document Request", parent, values, update_modified=True)
	doc = frappe.get_doc("IC Document Request", parent)

	_log_sample_dispatch(doc)
	_sync_sample_tracking(doc)
	_notify_upload(doc, subject_prefix="Sample dispatch updated")
	return {
		"ok": 1,
		"courier_name": doc.courier_name,
		"tracking_number": doc.tracking_number,
		"pod_attachment": doc.pod_attachment,
	}


@frappe.whitelist()
def clear_document_item(document_request: str, item_name: str):
	"""Manager/admin delete a customer upload so a new file can be provided."""
	_assert_manager()
	doc = frappe.get_doc("IC Document Request", document_request)
	for row in doc.items:
		if row.name == item_name:
			row.uploaded_file = None
			row.status = "Pending"
			row.uploaded_on = None
			break
	else:
		frappe.throw(_("Document item not found"))
	pending = any(r.status in ("Pending", "Replacement Requested") for r in doc.items)
	uploaded = any(r.status in ("Uploaded", "Approved") for r in doc.items)
	if pending and uploaded:
		doc.status = "Partially Uploaded"
	elif pending:
		doc.status = "Sent to Customer" if doc.share_token else "Draft"
	doc.save(ignore_permissions=True)
	_log_staff_action(doc, f"Cleared upload for {item_name}")
	return doc.as_dict()


@frappe.whitelist()
def replace_document_item(document_request: str, item_name: str, file_url: str, remarks: str | None = None):
	"""Manager/admin replace customer document with a new file."""
	_assert_manager()
	file_url = _assert_allowed_upload(file_url)
	doc = frappe.get_doc("IC Document Request", document_request)
	for row in doc.items:
		if row.name == item_name:
			row.uploaded_file = file_url
			row.status = "Uploaded"
			row.uploaded_on = now_datetime()
			if remarks:
				row.review_remarks = remarks
			break
	else:
		frappe.throw(_("Document item not found"))
	doc.status = "Under Review"
	doc.save(ignore_permissions=True)
	_log_staff_action(doc, f"Replaced document {item_name}", attachment=file_url)
	return doc.as_dict()


@frappe.whitelist()
def review_document_item(document_request: str, item_name: str, action: str, remarks: str | None = None):
	doc = frappe.get_doc("IC Document Request", document_request)
	for row in doc.items:
		if row.name == item_name:
			if action == "approve":
				row.status = "Approved"
			elif action == "reject":
				row.status = "Rejected"
			elif action == "replace":
				row.status = "Replacement Requested"
			row.review_remarks = remarks
			break
	if all(r.status == "Approved" for r in doc.items):
		doc.status = "Completed"
	else:
		doc.status = "Under Review"
	doc.save(ignore_permissions=True)
	if action in ("reject", "replace"):
		for user in set(filter(None, [doc.assigned_to, doc.owner])):
			if frappe.db.exists("User", user):
				frappe.get_doc(
					{
						"doctype": "Notification Log",
						"subject": f"Document {action}: {doc.name}",
						"email_content": remarks or "",
						"document_type": "IC Document Request",
						"document_name": doc.name,
						"for_user": user,
						"type": "Alert",
						"from_user": frappe.session.user,
					}
				).insert(ignore_permissions=True)
	return doc.as_dict()


def _notify_upload(doc, subject_prefix: str = "Customer document uploaded"):
	for user in set(filter(None, [doc.assigned_to, doc.owner, "Administrator"])):
		if frappe.db.exists("User", user):
			try:
				frappe.get_doc(
					{
						"doctype": "Notification Log",
						"subject": f"{subject_prefix}: {doc.name}",
						"email_content": f"{subject_prefix} for {doc.name}",
						"document_type": "IC Document Request",
						"document_name": doc.name,
						"for_user": user,
						"type": "Alert",
						"from_user": frappe.session.user if frappe.session.user != "Guest" else "Guest",
					}
				).insert(ignore_permissions=True)
			except Exception:
				pass


def _recorder():
	user = frappe.session.user
	if user and user != "Guest" and frappe.db.exists("User", user):
		return user
	return "Administrator"


def _log_customer_upload(doc, row):
	if not frappe.db.exists("DocType", "IC Project Record"):
		return
	try:
		frappe.get_doc(
			{
				"doctype": "IC Project Record",
				"subject": f"Customer uploaded: {row.document_name}",
				"record_type": "Document",
				"customer": doc.customer,
				"project": doc.project,
				"category": row.category or "Customer Documents",
				"content": f"<p>Uploaded via document checklist {doc.name}.</p>"
				+ (f"<p>Remarks: {frappe.utils.escape_html(row.customer_remarks)}</p>" if row.get("customer_remarks") else ""),
				"attachment": row.uploaded_file,
				"recorded_by": _recorder(),
			}
		).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "document upload project record")


def _log_sample_dispatch(doc):
	if not frappe.db.exists("DocType", "IC Project Record"):
		return
	try:
		frappe.get_doc(
			{
				"doctype": "IC Project Record",
				"subject": f"Sample dispatch: {doc.tracking_number or doc.courier_name or doc.name}",
				"record_type": "Important Customer Note",
				"customer": doc.customer,
				"project": doc.project,
				"category": "Other",
				"content": (
					f"<p>Courier: {frappe.utils.escape_html(doc.courier_name or '—')}</p>"
					f"<p>Tracking: {frappe.utils.escape_html(doc.tracking_number or '—')}</p>"
					f"<p>Dispatch date: {doc.dispatch_date or '—'}</p>"
					f"<p>{frappe.utils.escape_html(doc.sample_dispatch_remarks or '')}</p>"
				),
				"attachment": doc.pod_attachment,
				"recorded_by": _recorder(),
			}
		).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "sample dispatch project record")


def _log_staff_action(doc, subject: str, attachment: str | None = None):
	if not doc.project or not frappe.db.exists("DocType", "IC Project Record"):
		return
	try:
		frappe.get_doc(
			{
				"doctype": "IC Project Record",
				"subject": subject,
				"record_type": "Document",
				"customer": doc.customer,
				"project": doc.project,
				"category": "Customer Documents",
				"content": f"<p>{frappe.utils.escape_html(subject)}</p><p>By {frappe.session.user}</p>",
				"attachment": attachment,
				"recorded_by": frappe.session.user,
			}
		).insert(ignore_permissions=True)
	except Exception:
		pass


def _sync_sample_tracking(doc):
	"""Push courier/tracking onto linked project samples when possible."""
	if not doc.project or not doc.tracking_number:
		return
	if not frappe.db.exists("DocType", "IC Sample Tracking"):
		return
	samples = frappe.get_all(
		"IC Sample Tracking",
		filters={"project": doc.project},
		fields=["name"],
		limit_page_length=5,
		order_by="modified desc",
	)
	for s in samples:
		try:
			vals = {"courier_awb": doc.tracking_number}
			if doc.courier_name:
				vals["courier_name"] = doc.courier_name
			if doc.dispatch_date:
				vals["dispatch_date"] = doc.dispatch_date
			frappe.db.set_value("IC Sample Tracking", s.name, vals, update_modified=False)
		except Exception:
			pass
