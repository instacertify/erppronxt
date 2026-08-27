# Copyright (c) Instacertify
"""Lead / CRM events."""

from __future__ import annotations

import frappe


def before_validate_lead(doc, method=None):
	"""Run before ERPNext Lead.validate so party name satisfies core checks."""
	_sync_party_name(doc)


def validate_lead(doc, method=None):
	_sync_party_name(doc)
	_ensure_mandatory_name(doc)

	# Keep UTM source aligned for analytics when available
	if doc.get("ic_lead_source_detail") and hasattr(doc, "utm_source") and not doc.utm_source:
		source = doc.ic_lead_source_detail
		if frappe.db.exists("DocType", "UTM Source") and frappe.db.exists("UTM Source", source):
			doc.utm_source = source

	if doc.country == "India" and doc.get("ic_gst_number"):
		doc.ic_gst_number = (doc.ic_gst_number or "").strip().upper()


def _sync_party_name(doc):
	"""Keep ERPNext company_name / first_name in sync with mandatory party name."""
	party = (doc.get("ic_party_name") or "").strip()
	if not party:
		party = (doc.get("company_name") or doc.get("lead_name") or doc.get("first_name") or "").strip()
		if party:
			doc.ic_party_name = party
	if not party:
		return

	if not doc.company_name:
		doc.company_name = party
	if not (doc.first_name or doc.last_name or doc.middle_name):
		doc.first_name = party.split()[0][:140]


def _ensure_mandatory_name(doc):
	from frappe import _

	if not (doc.get("ic_party_name") or "").strip():
		frappe.throw(_("Name of Person / Firm is mandatory"))


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
