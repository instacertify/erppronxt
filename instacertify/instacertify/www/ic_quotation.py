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

	cost_items = []
	for row in doc.get("ic_cost_items") or []:
		cost_items.append(
			{
				"particulars": row.particulars or row.cost_component or row.description,
				"amount": row.amount,
				"payment_destination": row.payment_destination,
			}
		)

	test_items = []
	for row in doc.get("ic_test_items") or []:
		test_items.append(
			{
				"product_name": row.product_name,
				"test_name": row.test_name,
				"applicable_standard": row.applicable_standard,
				"testing_charges": row.testing_charges,
			}
		)

	status = doc.ic_workflow_status or "Draft"
	can_decide = status in (
		"Shared with Customer",
		"Customer Review",
		"Ready to Share",
		"Changes Requested",
	)

	return {
		"name": doc.name,
		"party_name": doc.party_name,
		"customer_name": doc.customer_name,
		"ic_revision_number": doc.ic_revision_number,
		"ic_quotation_type": doc.ic_quotation_type,
		"ic_workflow_status": status,
		"ic_service_name": doc.ic_service_name,
		"ic_estimated_timeline": doc.ic_estimated_timeline,
		"ic_scope_of_work": doc.ic_scope_of_work,
		"ic_deliverables": doc.ic_deliverables,
		"ic_payment_terms": doc.ic_payment_terms,
		"ic_commercial_value": doc.ic_commercial_value,
		"ic_passthrough_value": doc.ic_passthrough_value,
		"ic_total_quoted_value": doc.ic_total_quoted_value,
		"ic_customer_remarks": doc.ic_customer_remarks,
		"grand_total": doc.grand_total,
		"currency": doc.currency,
		"transaction_date": str(doc.transaction_date or ""),
		"valid_till": str(doc.valid_till or ""),
		"cost_items": cost_items,
		"test_items": test_items,
		"can_decide": 1 if can_decide and status not in ("Accepted", "Rejected / Lost") else 0,
		"is_final": 1 if status in ("Accepted", "Rejected / Lost") else 0,
		"pdf_url": f"/api/method/instacertify.quotation.events.download_quotation_pdf?token={token}",
	}
