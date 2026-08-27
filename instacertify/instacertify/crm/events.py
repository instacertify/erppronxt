# Copyright (c) Instacertify
"""Lead / CRM events."""

from __future__ import annotations

import frappe
from frappe import _


def before_validate_lead(doc, method=None):
	"""Run before ERPNext Lead.validate so party name satisfies core checks."""
	_sync_party_name(doc)


def validate_lead(doc, method=None):
	_sync_party_name(doc)
	_ensure_mandatory_name(doc)
	if not doc.get("ic_pipeline_stage"):
		doc.ic_pipeline_stage = "Lead"

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
	tickets = list_docs(
		"Helpdesk Ticket",
		{"customer": customer},
		[
			"name",
			"subject",
			"ticket_type",
			"status",
			"priority",
			"opened_on",
			"assigned_to",
			"modified",
		],
	)
	records = list_docs(
		"IC Project Record",
		{"customer": customer},
		["name", "subject", "record_type", "category", "modified"],
	)
	# Files attached to completed projects for this customer
	project_files = []
	completed_project_names = [
		p["name"]
		for p in projects
		if p.get("status") == "Completed" or p.get("ic_project_stage") == "Project Completed"
	]
	for pname in completed_project_names[:30]:
		files = frappe.get_all(
			"File",
			filters={
				"attached_to_doctype": "Project",
				"attached_to_name": pname,
				"is_folder": 0,
			},
			fields=["name", "file_name", "file_url", "creation", "attached_to_name", "content_hash"],
			order_by="creation desc",
			limit_page_length=30,
		)
		for f in files:
			f["project"] = pname
			f["source"] = "Project"
			project_files.append(f)
	# Also IC Project Record attachments for this customer
	for rec in records[:30]:
		files = frappe.get_all(
			"File",
			filters={
				"attached_to_doctype": "IC Project Record",
				"attached_to_name": rec["name"],
				"is_folder": 0,
			},
			fields=["name", "file_name", "file_url", "creation", "attached_to_name", "content_hash"],
			limit_page_length=15,
		)
		for f in files:
			f["project"] = rec["name"]
			f["record"] = rec["name"]
			f["source"] = "IC Project Record"
			project_files.append(f)

	# Files already saved on this Customer
	customer_files = frappe.get_all(
		"File",
		filters={
			"attached_to_doctype": "Customer",
			"attached_to_name": customer,
			"is_folder": 0,
		},
		fields=["name", "file_name", "file_url", "creation", "content_hash"],
		order_by="creation desc",
		limit_page_length=100,
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
	completed_projects = [
		p
		for p in projects
		if p.get("status") == "Completed" or p.get("ic_project_stage") == "Project Completed"
	]

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
		"tickets": tickets,
		"open_tickets": [
			t for t in tickets if t.get("status") in ("Open", "In Progress", "Waiting on Customer")
		],
		"records": records,
		"project_files": project_files,
		"customer_files": customer_files,
		"completed_project_names": completed_project_names,
		"contacts": contact_details,
		"amount_billed": billed,
		"outstanding_amount": outstanding,
		"amount_paid": paid,
	}


@frappe.whitelist()
def get_lead_history(lead: str):
	"""Linked quotations, opportunities, customer and support for a Lead."""
	if not lead or not frappe.db.exists("Lead", lead):
		return {}

	def list_docs(doctype, filters, fields=None, limit=80):
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

	lead_doc = frappe.db.get_value(
		"Lead",
		lead,
		[
			"name",
			"status",
			"company_name",
			"lead_name",
			"ic_party_name",
			"ic_pipeline_stage",
			"email_id",
			"mobile_no",
			"phone",
			"ic_next_contact_date",
			"ic_call_remarks",
			"ic_lead_connected",
			"ic_project_type",
			"ic_estimated_value",
		],
		as_dict=True,
	) or {}

	quotations = list_docs(
		"Quotation",
		{"party_name": lead, "quotation_to": "Lead"},
		[
			"name",
			"status",
			"ic_workflow_status",
			"grand_total",
			"currency",
			"transaction_date",
			"ic_quotation_type",
			"valid_till",
		],
	)
	# Also quotes created after conversion (party became Customer) via opportunity
	opportunities = list_docs(
		"Opportunity",
		{"party_name": lead, "opportunity_from": "Lead"},
		["name", "status", "opportunity_amount", "currency", "transaction_date", "title"],
	)
	# Quotes linked via Opportunity
	for opp in opportunities:
		extra = list_docs(
			"Quotation",
			{"opportunity": opp["name"]},
			[
				"name",
				"status",
				"ic_workflow_status",
				"grand_total",
				"currency",
				"transaction_date",
				"ic_quotation_type",
				"valid_till",
			],
		)
		seen = {q["name"] for q in quotations}
		for q in extra:
			if q["name"] not in seen:
				quotations.append(q)
				seen.add(q["name"])

	customer = None
	if frappe.db.has_column("Customer", "lead_name"):
		customer = frappe.db.get_value("Customer", {"lead_name": lead}, ["name", "customer_name"], as_dict=True)
	projects = []
	invoices = []
	if customer:
		projects = list_docs(
			"Project",
			{"customer": customer.name},
			["name", "project_name", "status", "ic_project_stage", "ic_quotation", "ic_deadline"],
		)
		invoices = list_docs(
			"Sales Invoice",
			{"customer": customer.name, "docstatus": ["<", 2]},
			["name", "grand_total", "status", "posting_date", "ic_quotation", "currency"],
		)

	tickets = list_docs(
		"Helpdesk Ticket",
		{"lead": lead} if frappe.get_meta("Helpdesk Ticket").has_field("lead") else {"name": "__none__"},
		["name", "subject", "status", "ticket_type", "priority", "modified"],
	)
	documents = list_docs(
		"IC Document Request",
		{"lead": lead} if frappe.get_meta("IC Document Request").has_field("lead") else {"name": "__none__"},
		["name", "title", "status", "modified"],
	)

	return {
		"lead": lead_doc,
		"quotations": quotations,
		"opportunities": opportunities,
		"customer": customer,
		"projects": projects,
		"invoices": invoices,
		"tickets": tickets,
		"documents": documents,
		"accepted_quotations": [q for q in quotations if q.get("ic_workflow_status") == "Accepted"],
		"open_quotations": [
			q
			for q in quotations
			if q.get("ic_workflow_status")
			in ("Draft", "Ready to Share", "Shared with Customer", "Customer Review", "Changes Requested")
		],
	}


@frappe.whitelist()
def get_quotation_links(quotation: str):
	"""Linked Lead/Customer, projects, invoices, testing and documents for a Quotation."""
	if not quotation or not frappe.db.exists("Quotation", quotation):
		return {}

	def list_docs(doctype, filters, fields=None, limit=50):
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

	q = frappe.db.get_value(
		"Quotation",
		quotation,
		[
			"name",
			"quotation_to",
			"party_name",
			"customer_name",
			"opportunity",
			"ic_workflow_status",
			"ic_quotation_type",
			"ic_parent_quotation",
			"grand_total",
			"currency",
			"status",
		],
		as_dict=True,
	) or {}

	party = {"doctype": q.get("quotation_to"), "name": q.get("party_name"), "label": q.get("customer_name")}
	lead = None
	customer = None
	if q.get("quotation_to") == "Lead" and q.get("party_name"):
		lead = frappe.db.get_value(
			"Lead",
			q.party_name,
			["name", "status", "ic_pipeline_stage", "ic_party_name", "company_name", "email_id", "mobile_no"],
			as_dict=True,
		)
	elif q.get("quotation_to") == "Customer" and q.get("party_name"):
		customer = frappe.db.get_value(
			"Customer", q.party_name, ["name", "customer_name", "lead_name"], as_dict=True
		)
		if customer and customer.get("lead_name"):
			lead = frappe.db.get_value(
				"Lead",
				customer.lead_name,
				["name", "status", "ic_pipeline_stage", "ic_party_name", "company_name"],
				as_dict=True,
			)

	projects = list_docs(
		"Project",
		{"ic_quotation": quotation},
		["name", "project_name", "status", "ic_project_stage", "customer", "ic_deadline", "percent_complete"],
	)
	invoices = list_docs(
		"Sales Invoice",
		{"ic_quotation": quotation, "docstatus": ["<", 2]},
		["name", "grand_total", "outstanding_amount", "status", "posting_date", "currency", "customer"],
	)
	testing = list_docs(
		"IC Testing Request",
		{"quotation": quotation},
		["name", "title", "status", "product", "project", "modified"],
	)
	documents = list_docs(
		"IC Document Request",
		{"quotation": quotation},
		["name", "title", "status", "project", "modified"],
	)
	samples = list_docs(
		"IC Sample Tracking",
		{"quotation": quotation} if frappe.get_meta("IC Sample Tracking").has_field("quotation") else {"name": "__none__"},
		["name", "tracking_number", "status", "sample_location", "modified"],
	)
	revisions = list_docs(
		"Quotation",
		{"ic_parent_quotation": quotation},
		["name", "ic_revision_number", "ic_workflow_status", "grand_total", "transaction_date"],
	)

	return {
		"quotation": q,
		"party": party,
		"lead": lead,
		"customer": customer,
		"opportunity": q.get("opportunity"),
		"projects": projects,
		"invoices": invoices,
		"testing_requests": testing,
		"documents": documents,
		"samples": samples,
		"revisions": revisions,
		"parent_quotation": q.get("ic_parent_quotation"),
	}


def _copy_file_to_customer(src_file_name, customer, prefix, existing_hashes, existing_names):
	"""Attach an existing File's URL onto Customer. Returns 'copied' | 'skipped'."""
	src = frappe.get_doc("File", src_file_name)
	if src.content_hash and src.content_hash in existing_hashes:
		return "skipped"
	target_name = f"{prefix}-{src.file_name}" if prefix else src.file_name
	if target_name in existing_names or src.file_name in existing_names:
		return "skipped"
	new_file = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": target_name,
			"file_url": src.file_url,
			"is_private": src.is_private,
			"attached_to_doctype": "Customer",
			"attached_to_name": customer,
			"content_hash": src.content_hash,
			"folder": "Home/Attachments",
		}
	)
	new_file.insert(ignore_permissions=True)
	if src.content_hash:
		existing_hashes.add(src.content_hash)
	existing_names.add(new_file.file_name)
	return "copied"


@frappe.whitelist()
def import_completed_project_files(customer: str):
	"""Copy attachments from completed projects onto the Customer record."""
	if not customer or not frappe.db.exists("Customer", customer):
		frappe.throw(_("Customer is required"))

	all_p = frappe.get_all(
		"Project",
		filters={"customer": customer},
		fields=["name", "status", "ic_project_stage"],
	)
	projects = [
		p.name
		for p in all_p
		if p.status == "Completed" or p.get("ic_project_stage") == "Project Completed"
	]

	existing_hashes = {
		h
		for h in frappe.get_all(
			"File",
			filters={
				"attached_to_doctype": "Customer",
				"attached_to_name": customer,
				"is_folder": 0,
			},
			pluck="content_hash",
		)
		if h
	}
	existing_names = set(
		frappe.get_all(
			"File",
			filters={
				"attached_to_doctype": "Customer",
				"attached_to_name": customer,
				"is_folder": 0,
			},
			pluck="file_name",
		)
	)

	copied = []
	skipped = 0
	for pname in projects:
		files = frappe.get_all(
			"File",
			filters={
				"attached_to_doctype": "Project",
				"attached_to_name": pname,
				"is_folder": 0,
			},
			fields=["name", "file_name", "file_url", "content_hash", "is_private"],
		)
		for f in files:
			try:
				result = _copy_file_to_customer(
					f.name, customer, pname, existing_hashes, existing_names
				)
				if result == "copied":
					copied.append(f.file_name)
				else:
					skipped += 1
			except Exception:
				frappe.log_error(frappe.get_traceback(), f"Copy file {f.name} to customer")

	# Also pull IC Project Record attachments for this customer
	records = frappe.get_all(
		"IC Project Record",
		filters={"customer": customer},
		pluck="name",
		limit=50,
	) if frappe.db.exists("DocType", "IC Project Record") else []
	for rec in records:
		files = frappe.get_all(
			"File",
			filters={
				"attached_to_doctype": "IC Project Record",
				"attached_to_name": rec,
				"is_folder": 0,
			},
			fields=["name", "file_name"],
		)
		for f in files:
			try:
				result = _copy_file_to_customer(
					f.name, customer, rec, existing_hashes, existing_names
				)
				if result == "copied":
					copied.append(f.file_name)
				else:
					skipped += 1
			except Exception:
				frappe.log_error(frappe.get_traceback(), f"Copy record file {f.name} to customer")

	return {
		"copied": len(copied),
		"skipped": skipped,
		"projects": len(projects),
		"files": copied,
	}
