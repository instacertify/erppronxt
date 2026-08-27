# Copyright (c) Instacertify
"""Notification documents."""

from __future__ import annotations

import frappe


def ensure_notifications():
	# Most notifications are created via Notification Log in event handlers.
	# Also create a few Email Alert style Notification docs where useful.
	defs = [
		{
			"name": "IC Quotation Accepted",
			"subject": "Quotation {{ doc.name }} Accepted",
			"document_type": "Quotation",
			"event": "Value Change",
			"value_changed": "ic_workflow_status",
			"condition": "doc.ic_workflow_status=='Accepted'",
			"message": "Quotation <b>{{ doc.name }}</b> was accepted by the customer.",
			"channel": "System Notification",
			"recipients": [{"receiver_by_document_field": "owner"}],
		},
		{
			"name": "IC Quotation Changes Requested",
			"subject": "Changes requested on {{ doc.name }}",
			"document_type": "Quotation",
			"event": "Value Change",
			"value_changed": "ic_workflow_status",
			"condition": "doc.ic_workflow_status=='Changes Requested'",
			"message": "Customer requested changes on quotation <b>{{ doc.name }}</b>.<br>{{ doc.ic_customer_remarks or '' }}",
			"channel": "System Notification",
			"recipients": [{"receiver_by_document_field": "owner"}],
		},
	]
	for d in defs:
		if frappe.db.exists("Notification", d["name"]):
			continue
		try:
			doc = frappe.get_doc({"doctype": "Notification", "module": "Instacertify", "enabled": 1, **d})
			doc.insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Notification {d['name']}")
