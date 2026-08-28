# Copyright (c) Instacertify
"""Sample Dispatch Data Collection Sheet — shareable customer portal APIs."""

from __future__ import annotations

import secrets

import frappe
from frappe import _
from frappe.utils import now_datetime

from instacertify.documents.api import _assert_allowed_upload


OPEN_STATUSES = {"Draft", "Sent to Customer", "Submitted by Customer", "Under Review"}


def _portal_url(token: str) -> str:
	base = None
	try:
		base = frappe.db.get_single_value("IC Settings", "portal_base_url")
	except Exception:
		base = None
	path = f"/ic-dispatch/{token}"
	if base:
		return str(base).rstrip("/") + path
	return frappe.utils.get_url(path)


@frappe.whitelist()
def share_sample_dispatch_collection(name: str):
	"""Generate / refresh customer share link for a Sample Dispatch Collection sheet."""
	doc = frappe.get_doc("IC Sample Dispatch Collection", name)
	if not doc.share_token:
		doc.share_token = secrets.token_urlsafe(24)
	if doc.status in (None, "", "Draft"):
		doc.status = "Sent to Customer"
	doc.sent_on = now_datetime()
	doc.save(ignore_permissions=True)
	url = _portal_url(doc.share_token)
	return {"url": url, "token": doc.share_token, "name": doc.name}


@frappe.whitelist()
def create_sample_dispatch_for_project(project: str, title: str | None = None):
	"""Create (or reuse open) Sample Dispatch Data Collection sheet and return share link.

	Callable by project handlers / admins from the Project form.
	"""
	proj = frappe.get_doc("Project", project)
	if not proj.customer:
		frappe.throw(_("Project must have a Customer before sharing a sample dispatch sheet"))

	existing = frappe.db.get_value(
		"IC Sample Dispatch Collection",
		{
			"project": project,
			"status": ["in", ["Draft", "Sent to Customer", "Submitted by Customer", "Under Review"]],
		},
		"name",
		order_by="modified desc",
	)
	if existing:
		doc = frappe.get_doc("IC Sample Dispatch Collection", existing)
	else:
		instructions = (
			"<p>Please complete this <b>Sample Dispatch Data Collection Sheet</b> when you "
			"ship the sample(s) for this project.</p>"
			"<ul>"
			"<li>Enter courier name, AWB / tracking number, and dispatch date</li>"
			"<li>Upload POD / dispatch proof (PDF or image)</li>"
			"<li>Describe the sample quantity, condition, and packaging</li>"
			"</ul>"
		)
		doc = frappe.get_doc(
			{
				"doctype": "IC Sample Dispatch Collection",
				"title": title
				or f"Sample Dispatch — {proj.project_name or proj.name}",
				"customer": proj.customer,
				"project": proj.name,
				"quotation": proj.get("ic_quotation"),
				"assigned_to": frappe.session.user,
				"status": "Draft",
				"customer_instructions": instructions,
			}
		)
		doc.insert(ignore_permissions=True)

	return share_sample_dispatch_collection(doc.name)


@frappe.whitelist(allow_guest=True)
def get_sample_dispatch_by_token(token: str):
	name = frappe.db.get_value("IC Sample Dispatch Collection", {"share_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid sample dispatch link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Sample Dispatch Collection", name)
	lab_name = None
	if doc.laboratory:
		lab_name = frappe.db.get_value("IC Laboratory", doc.laboratory, "laboratory_name") or doc.laboratory
	return {
		"title": doc.title,
		"status": doc.status,
		"customer_instructions": doc.customer_instructions,
		"contact_person": doc.contact_person,
		"contact_phone": doc.contact_phone,
		"contact_email": doc.contact_email,
		"dispatch_from_address": doc.dispatch_from_address,
		"sample_description": doc.sample_description,
		"sample_quantity": doc.sample_quantity,
		"sample_condition": doc.sample_condition,
		"packaging_details": doc.packaging_details,
		"courier_name": doc.courier_name,
		"tracking_number": doc.tracking_number,
		"dispatch_date": str(doc.dispatch_date or ""),
		"expected_delivery": str(doc.expected_delivery or ""),
		"pod_attachment": doc.pod_attachment,
		"customer_remarks": doc.customer_remarks,
		"laboratory_name": lab_name,
		"read_only": doc.status in ("Completed", "Cancelled"),
		"portal_notice": _(
			"This is the Sample Dispatch Data Collection Sheet. Submit courier and sample details here. "
			"This link does not provide access to Instacertify ERP."
		),
		"allowed_types": "PDF, images (PNG/JPG/WEBP/GIF/TIFF), Excel/CSV, Word",
	}


@frappe.whitelist(allow_guest=True)
def save_sample_dispatch_collection(
	token: str,
	contact_person: str | None = None,
	contact_phone: str | None = None,
	contact_email: str | None = None,
	dispatch_from_address: str | None = None,
	sample_description: str | None = None,
	sample_quantity: str | None = None,
	sample_condition: str | None = None,
	packaging_details: str | None = None,
	courier_name: str | None = None,
	tracking_number: str | None = None,
	dispatch_date: str | None = None,
	expected_delivery: str | None = None,
	pod_attachment: str | None = None,
	customer_remarks: str | None = None,
):
	name = frappe.db.get_value("IC Sample Dispatch Collection", {"share_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid sample dispatch link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Sample Dispatch Collection", name)
	if doc.status not in OPEN_STATUSES:
		frappe.throw(_("This sample dispatch sheet is closed"), frappe.PermissionError)

	if pod_attachment:
		_assert_allowed_upload(pod_attachment)
		doc.pod_attachment = pod_attachment

	doc.contact_person = contact_person or doc.contact_person
	doc.contact_phone = contact_phone or doc.contact_phone
	doc.contact_email = contact_email or doc.contact_email
	doc.dispatch_from_address = dispatch_from_address or doc.dispatch_from_address
	doc.sample_description = sample_description or doc.sample_description
	doc.sample_quantity = sample_quantity or doc.sample_quantity
	doc.sample_condition = sample_condition or doc.sample_condition
	doc.packaging_details = packaging_details or doc.packaging_details
	doc.courier_name = courier_name or doc.courier_name
	doc.tracking_number = tracking_number or doc.tracking_number
	if dispatch_date:
		doc.dispatch_date = dispatch_date
	if expected_delivery:
		doc.expected_delivery = expected_delivery
	doc.customer_remarks = customer_remarks if customer_remarks is not None else doc.customer_remarks
	doc.status = "Submitted by Customer"
	doc.submitted_on = now_datetime()
	doc.save(ignore_permissions=True)

	_sync_to_sample_tracking(doc)
	_notify_handlers(doc)
	return {"ok": 1, "status": doc.status, "name": doc.name}


def _sync_to_sample_tracking(doc):
	"""Push courier/AWB onto linked Sample Tracking or project samples."""
	targets = []
	if doc.sample_tracking:
		targets.append(doc.sample_tracking)
	elif doc.project:
		targets = frappe.get_all(
			"IC Sample Tracking",
			filters={"project": doc.project},
			pluck="name",
			limit_page_length=20,
		)
	for name in targets:
		try:
			sample = frappe.get_doc("IC Sample Tracking", name)
			if doc.courier_name:
				sample.courier_name = doc.courier_name
			if doc.tracking_number:
				sample.courier_awb = doc.tracking_number
			if doc.dispatch_date:
				sample.dispatch_date = doc.dispatch_date
			if doc.expected_delivery:
				sample.expected_arrival = doc.expected_delivery
			if doc.sample_description and not sample.sample_description:
				sample.sample_description = doc.sample_description
			if doc.sample_quantity and not sample.quantity:
				sample.quantity = doc.sample_quantity
			if sample.status in (None, "", "Sample Awaited"):
				sample.status = "Sample Dispatched to Laboratory"
			sample.save(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Sync Sample Dispatch → Tracking")


def _notify_handlers(doc):
	recipients = set()
	if doc.assigned_to:
		recipients.add(doc.assigned_to)
	if doc.project:
		try:
			proj = frappe.get_doc("Project", doc.project)
			for row in proj.get("ic_team_members") or []:
				if row.user:
					recipients.add(row.user)
		except Exception:
			pass
	recipients.discard("Guest")
	recipients.discard("Administrator")
	if not recipients:
		return
	try:
		frappe.sendmail(
			recipients=list(recipients),
			subject=_("Sample dispatch submitted: {0}").format(doc.title or doc.name),
			message=_(
				"Customer submitted Sample Dispatch Data Collection Sheet <b>{0}</b>. "
				"Courier: {1}, AWB: {2}."
			).format(doc.name, doc.courier_name or "—", doc.tracking_number or "—"),
			delayed=True,
			reference_doctype=doc.doctype,
			reference_name=doc.name,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Sample Dispatch notify")
