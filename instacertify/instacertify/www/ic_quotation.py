# Copyright (c) Instacertify
"""Customer quotation portal."""

from __future__ import annotations

import frappe
from frappe import _


no_cache = 1


def get_context(context):
	token = frappe.form_dict.get("name") or frappe.form_dict.get("token")
	context.token = token
	context.csrf_token = frappe.sessions.get_csrf_token()
	frappe.db.commit()
	context.no_cache = 1
	context.show_sidebar = False


@frappe.whitelist(allow_guest=True)
def get_quotation(token: str):
	name = frappe.db.get_value("Quotation", {"ic_share_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid quotation link"), frappe.PermissionError)
	doc = frappe.get_doc("Quotation", name)
	# Expose only safe fields
	return {
		"name": doc.name,
		"party_name": doc.party_name,
		"customer_name": doc.customer_name,
		"ic_revision_number": doc.ic_revision_number,
		"ic_quotation_type": doc.ic_quotation_type,
		"ic_workflow_status": doc.ic_workflow_status,
		"ic_service_name": doc.ic_service_name,
		"ic_estimated_timeline": doc.ic_estimated_timeline,
		"ic_scope_of_work": doc.ic_scope_of_work,
		"ic_deliverables": doc.ic_deliverables,
		"ic_commercial_value": doc.ic_commercial_value,
		"ic_passthrough_value": doc.ic_passthrough_value,
		"ic_total_quoted_value": doc.ic_total_quoted_value,
		"grand_total": doc.grand_total,
		"currency": doc.currency,
		"transaction_date": doc.transaction_date,
	}
