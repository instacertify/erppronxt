# Copyright (c) Instacertify
"""Document request portal APIs."""

from __future__ import annotations

import secrets

import frappe
from frappe import _
from frappe.utils import now_datetime


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
		"name": doc.name,
		"title": doc.title,
		"customer": doc.customer,
		"status": doc.status,
		"items": [
			{
				"idx": row.idx,
				"name": row.name,
				"document_name": row.document_name,
				"category": row.category,
				"is_mandatory": row.is_mandatory,
				"status": row.status,
				"uploaded_file": row.uploaded_file,
				"review_remarks": row.review_remarks,
			}
			for row in doc.items
		],
	}


@frappe.whitelist(allow_guest=True)
def upload_document_item(token: str, item_name: str, file_url: str):
	parent = frappe.db.get_value("IC Document Request", {"share_token": token}, "name")
	if not parent:
		frappe.throw(_("Invalid document link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Document Request", parent)
	updated = False
	for row in doc.items:
		if row.name == item_name:
			row.uploaded_file = file_url
			row.status = "Uploaded"
			row.uploaded_on = now_datetime()
			updated = True
			break
	if not updated:
		frappe.throw(_("Document item not found"))
	pending = any(r.status == "Pending" for r in doc.items)
	doc.status = "Partially Uploaded" if pending else "Under Review"
	doc.save(ignore_permissions=True)

	# Notify assigned
	for user in set(filter(None, [doc.assigned_to, doc.owner, "Administrator"])):
		if frappe.db.exists("User", user):
			frappe.get_doc(
				{
					"doctype": "Notification Log",
					"subject": f"Customer document uploaded: {doc.name}",
					"email_content": f"A document was uploaded for {doc.name}",
					"document_type": "IC Document Request",
					"document_name": doc.name,
					"for_user": user,
					"type": "Alert",
					"from_user": "Guest",
				}
			).insert(ignore_permissions=True)
	return {"status": doc.status}


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
