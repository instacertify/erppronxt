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
	"""Complete customer relationship overview for Customer Related Data tab."""
	if not customer:
		return {}

	def list_docs(doctype, filters, fields=None, limit=100):
		if not frappe.db.exists("DocType", doctype):
			return []
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

	customer_name = frappe.db.get_value("Customer", customer, "customer_name") or customer

	leads = list_docs(
		"Lead",
		{"company_name": customer_name},
		["name", "status", "source", "ic_request_category", "modified"],
	)
	opportunities = list_docs(
		"Opportunity",
		{"party_name": customer, "opportunity_from": "Customer"},
		["name", "status", "opportunity_amount", "currency", "transaction_date", "title"],
	)
	quotations = list_docs(
		"Quotation",
		{"party_name": customer, "quotation_to": "Customer"},
		[
			"name",
			"status",
			"ic_workflow_status",
			"grand_total",
			"currency",
			"transaction_date",
			"valid_till",
		],
	)
	projects = list_docs(
		"Project",
		{"customer": customer},
		[
			"name",
			"project_name",
			"status",
			"ic_project_stage",
			"ic_progress_percentage",
			"ic_deadline",
			"expected_end_date",
		],
	)
	testing = list_docs(
		"IC Testing Request",
		{"customer": customer},
		["name", "title", "status", "product", "test_name", "modified"],
	)
	samples = list_docs(
		"IC Sample Tracking",
		{"customer": customer},
		["name", "tracking_number", "status", "sample_description", "modified"],
	)
	invoices = list_docs(
		"Sales Invoice",
		{"customer": customer, "docstatus": ["<", 2]},
		[
			"name",
			"grand_total",
			"outstanding_amount",
			"status",
			"currency",
			"posting_date",
			"docstatus",
			"ic_quotation",
		],
	)
	payments = list_docs(
		"Payment Entry",
		{"party_type": "Customer", "party": customer, "docstatus": ["<", 2]},
		[
			"name",
			"posting_date",
			"paid_amount",
			"received_amount",
			"currency",
			"status",
			"mode_of_payment",
			"docstatus",
			"payment_type",
		],
	)
	documents = list_docs(
		"IC Document Request",
		{"customer": customer},
		["name", "title", "status", "modified"],
	)
	records = list_docs(
		"IC Project Record",
		{"customer": customer},
		["name", "subject", "record_type", "category", "modified"],
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
			[
				"name",
				"first_name",
				"last_name",
				"email_id",
				"mobile_no",
				"is_primary_contact",
				"designation",
			],
			as_dict=True,
		)
		if contact:
			contact_details.append(contact)

	accepted = [q for q in quotations if q.get("ic_workflow_status") == "Accepted"]
	active_quotes = [
		q
		for q in quotations
		if q.get("ic_workflow_status")
		in ("Shared with Customer", "Customer Review", "Ready to Share")
	]
	shared_quotes = [
		q
		for q in quotations
		if q.get("ic_workflow_status")
		in ("Shared with Customer", "Customer Review", "Accepted", "Ready to Share")
	]
	active_projects = [p for p in projects if p.get("status") not in ("Completed", "Cancelled")]
	completed_projects = [p for p in projects if p.get("status") == "Completed"]

	billed = sum(
		float(i.get("grand_total") or 0) for i in invoices if int(i.get("docstatus") or 0) == 1
	)
	outstanding = sum(
		float(i.get("outstanding_amount") or 0)
		for i in invoices
		if int(i.get("docstatus") or 0) == 1
	)
	paid = sum(
		float(p.get("received_amount") or p.get("paid_amount") or 0)
		for p in payments
		if int(p.get("docstatus") or 0) == 1 and p.get("payment_type") == "Receive"
	)

	return {
		"customer": customer,
		"customer_name": customer_name,
		"leads": leads,
		"opportunities": opportunities,
		"quotations": quotations,
		"accepted_quotations": accepted,
		"active_quotations": active_quotes,
		"shared_quotations": shared_quotes,
		"projects": projects,
		"active_projects": active_projects,
		"completed_projects": completed_projects,
		"testing_requests": testing,
		"samples": samples,
		"invoices": invoices,
		"payments": payments,
		"documents": documents,
		"records": records,
		"contacts": contact_details,
		"amount_billed": billed,
		"outstanding_amount": outstanding,
		"amount_paid": paid,
	}
