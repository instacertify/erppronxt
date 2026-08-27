# Copyright (c) Instacertify
"""Lead / CRM events."""

from __future__ import annotations

import frappe


def validate_lead(doc, method=None):
	# Keep UTM source aligned for analytics when available
	if doc.ic_lead_source_detail and hasattr(doc, "utm_source") and not doc.utm_source:
		if frappe.db.exists("DocType", "UTM Source") and frappe.db.exists(
			"UTM Source", doc.ic_lead_source_detail
		):
			doc.utm_source = doc.ic_lead_source_detail

	if doc.country == "India" and doc.ic_gst_number:
		doc.ic_gst_number = (doc.ic_gst_number or "").strip().upper()


@frappe.whitelist()
def get_customer_history(customer: str):
	"""Complete customer relationship overview for Customer Profile."""
	if not customer:
		return {}

	def list_docs(doctype, filters, fields=None, limit=50):
		try:
			return frappe.get_list(
				doctype,
				filters=filters,
				fields=fields or ["name", "modified"],
				order_by="modified desc",
				limit_page_length=limit,
			)
		except Exception:
			return []

	leads = list_docs(
		"Lead",
		{"company_name": frappe.db.get_value("Customer", customer, "customer_name")},
		["name", "status", "source", "ic_request_category", "modified"],
	)
	# Also match by lead_name / email later; keep simple
	quotations = list_docs(
		"Quotation",
		{"party_name": customer, "quotation_to": "Customer"},
		["name", "status", "ic_workflow_status", "grand_total", "currency", "transaction_date"],
	)
	projects = list_docs(
		"Project",
		{"customer": customer},
		["name", "project_name", "status", "ic_project_stage", "ic_progress_percentage", "ic_deadline"],
	)
	testing = list_docs(
		"IC Testing Request",
		{"customer": customer},
		["name", "title", "status", "product", "test_name"],
	)
	samples = list_docs(
		"IC Sample Tracking",
		{"customer": customer},
		["name", "tracking_number", "status", "sample_description"],
	)
	invoices = list_docs(
		"Sales Invoice",
		{"customer": customer, "docstatus": 1},
		["name", "grand_total", "outstanding_amount", "status", "currency", "posting_date"],
	)
	documents = list_docs(
		"IC Document Request",
		{"customer": customer},
		["name", "title", "status"],
	)
	records = list_docs(
		"IC Project Record",
		{"customer": customer},
		["name", "subject", "record_type", "category"],
	)
	contacts = frappe.get_list(
		"Dynamic Link",
		filters={"link_doctype": "Customer", "link_name": customer, "parenttype": "Contact"},
		fields=["parent"],
	)
	contact_details = []
	for c in contacts:
		contact = frappe.db.get_value(
			"Contact",
			c.parent,
			["name", "first_name", "last_name", "email_id", "mobile_no", "is_primary_contact", "designation"],
			as_dict=True,
		)
		if contact:
			contact_details.append(contact)

	accepted = [q for q in quotations if q.get("ic_workflow_status") == "Accepted"]
	active_quotes = [
		q
		for q in quotations
		if q.get("ic_workflow_status") in ("Shared with Customer", "Customer Review", "Ready to Share")
	]
	active_projects = [p for p in projects if p.get("status") not in ("Completed", "Cancelled")]
	completed_projects = [p for p in projects if p.get("status") == "Completed"]

	billed = sum(float(i.get("grand_total") or 0) for i in invoices)
	outstanding = sum(float(i.get("outstanding_amount") or 0) for i in invoices)

	return {
		"leads": leads,
		"quotations": quotations,
		"accepted_quotations": accepted,
		"active_quotations": active_quotes,
		"projects": projects,
		"active_projects": active_projects,
		"completed_projects": completed_projects,
		"testing_requests": testing,
		"samples": samples,
		"invoices": invoices,
		"documents": documents,
		"records": records,
		"contacts": contact_details,
		"amount_billed": billed,
		"outstanding_amount": outstanding,
	}
