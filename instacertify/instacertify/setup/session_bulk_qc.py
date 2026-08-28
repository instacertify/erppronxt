# Copyright (c) Instacertify
"""Bulk session QC: create ~50 linked records and validate interoperability."""

from __future__ import annotations

import frappe
from frappe.utils import add_days, nowdate, random_string


CATEGORIES = [
	"Travel",
	"Petty Cash",
	"Office",
	"Conveyance",
	"Lodging",
	"Meals",
	"Communication",
	"Other",
]


@frappe.whitelist()
def run_session_bulk_qc(target: int = 50) -> dict:
	"""
	Create a linked batch of demo records across the Instacertify session
	(leads → quotations → projects → expenses → labs → tickets → samples)
	and validate counts / links. Idempotent marker: title prefix QC50-.
	"""
	target = max(10, min(int(target or 50), 80))
	report = {"created": {}, "validated": [], "warnings": [], "errors": [], "total_created": 0}
	marker = f"QC50-{nowdate().replace('-', '')}"

	frappe.set_user("Administrator")

	try:
		company = frappe.db.get_single_value("Global Defaults", "default_company") or frappe.db.get_value(
			"Company", {}, "name"
		)
		if not company:
			report["errors"].append("No Company found")
			return report

		# --- Leads (10) ---
		# Note: Lead.lead_name can truncate long titles — key uniqueness by email.
		leads = []
		for i in range(10):
			email = f"qc50.lead{i+1}@example.com"
			name = frappe.db.get_value("Lead", {"email_id": email}, "name")
			if name:
				leads.append(name)
				continue
			doc = frappe.get_doc(
				{
					"doctype": "Lead",
					"lead_name": f"{marker} L{i+1}",
					"company_name": f"{marker} Co {i+1}",
					"status": "Lead",
					"email_id": email,
					"mobile_no": f"90000000{i:02d}",
					"ic_next_contact_date": add_days(nowdate(), i % 5),
					"ic_call_remarks": f"QC bulk contact note {i+1}",
					"ic_pipeline_stage": "Lead",
				}
			)
			doc.insert(ignore_permissions=True)
			leads.append(doc.name)
			report["total_created"] += 1
		report["created"]["leads"] = len(leads)

		# --- Customers from first 5 leads (5) ---
		customers = []
		for i, lead in enumerate(leads[:5]):
			cname = f"{marker} Customer {i+1}"
			existing = frappe.db.get_value("Customer", {"customer_name": cname}, "name")
			if existing:
				customers.append(existing)
				continue
			cust = frappe.get_doc(
				{
					"doctype": "Customer",
					"customer_name": cname,
					"customer_type": "Company",
					"territory": frappe.db.get_value("Territory", {}, "name") or "All Territories",
					"customer_group": frappe.db.get_value("Customer Group", {}, "name") or "All Customer Groups",
				}
			)
			cust.insert(ignore_permissions=True)
			customers.append(cust.name)
			report["total_created"] += 1
		report["created"]["customers"] = len(customers)

		# --- Quote templates (3) if missing ---
		templates = []
		for i, qtype in enumerate(["Consulting", "Testing", "Renewal"]):
			tname = f"{marker} Template {qtype}"
			if not frappe.db.exists("IC Quotation Template", tname):
				frappe.get_doc(
					{
						"doctype": "IC Quotation Template",
						"template_name": tname,
						"quotation_type": qtype,
						"service_family": "QC Bulk",
						"is_active": 1,
						"template_notes": "Session QC template",
					}
				).insert(ignore_permissions=True)
				report["total_created"] += 1
			templates.append(tname)
		report["created"]["templates"] = len(templates)

		# --- Quotations (8) ---
		quotations = []
		qmeta = frappe.get_meta("Quotation")
		for i in range(8):
			party = customers[i % len(customers)] if customers else None
			title = f"{marker} Quote {i+1}"
			existing = None
			if qmeta.has_field("ic_internal_title"):
				existing = frappe.db.get_value("Quotation", {"ic_internal_title": title}, "name")
			if existing:
				quotations.append(existing)
				continue
			qtype = ["Consulting", "Testing", "Renewal", "Consulting"][i % 4]
			doc = frappe.get_doc(
				{
					"doctype": "Quotation",
					"quotation_to": "Customer" if party else "Lead",
					"party_name": party or leads[i % len(leads)],
					"company": company,
					"transaction_date": nowdate(),
					"valid_till": add_days(nowdate(), 30),
					"order_type": "Sales",
					"ic_quotation_type": qtype,
					"ic_quotation_template": templates[0]
					if qtype == "Consulting"
					else templates[min(1, len(templates) - 1)],
				}
			)
			if qmeta.has_field("ic_internal_title"):
				doc.ic_internal_title = title
			if qmeta.has_field("ic_service_family"):
				doc.ic_service_family = "QC Bulk"
			item = frappe.db.get_value("Item", {"is_stock_item": 0, "disabled": 0}, "name")
			if item:
				doc.append(
					"items",
					{
						"item_code": item,
						"qty": 1,
						"rate": 1000 + i * 100,
					},
				)
			doc.insert(ignore_permissions=True)
			quotations.append(doc.name)
			report["total_created"] += 1
		report["created"]["quotations"] = len(quotations)

		# --- Projects linked to quotations (8) ---
		projects = []
		for i, qtn in enumerate(quotations):
			pname = f"{marker} Project {i+1}"
			existing = frappe.db.get_value("Project", {"project_name": pname}, "name")
			if existing:
				projects.append(existing)
				continue
			cust = frappe.db.get_value("Quotation", qtn, "party_name") if frappe.db.get_value("Quotation", qtn, "quotation_to") == "Customer" else (customers[0] if customers else None)
			doc = frappe.get_doc(
				{
					"doctype": "Project",
					"project_name": pname,
					"status": "Open",
					"company": company,
					"customer": cust,
					"expected_end_date": add_days(nowdate(), 30 + i),
				}
			)
			if frappe.get_meta("Project").has_field("ic_quotation"):
				doc.ic_quotation = qtn
			if frappe.get_meta("Project").has_field("custom_source_quotation"):
				doc.custom_source_quotation = qtn
			if frappe.get_meta("Project").has_field("ic_deadline"):
				doc.ic_deadline = add_days(nowdate(), 21 + i)
			doc.insert(ignore_permissions=True)
			projects.append(doc.name)
			report["total_created"] += 1
		report["created"]["projects"] = len(projects)

		# --- Laboratories (3) ---
		labs = []
		for i in range(3):
			lname = f"{marker} Lab {i+1}"
			existing = frappe.db.get_value("IC Laboratory", {"laboratory_name": lname}, "name")
			if existing:
				labs.append(existing)
				continue
			doc = frappe.get_doc(
				{
					"doctype": "IC Laboratory",
					"laboratory_name": lname,
					"location": "QC City",
					"status": "Active",
					"accreditation_scope": f"EMI/EMC scope batch {i+1}",
				}
			)
			doc.append(
				"test_scopes",
				{
					"test_name": f"QC Test {i+1}",
					"applicable_standard": "IEC 62368-1",
					"category": "Safety",
					"selling_price": 5000,
					"purchase_price": 3500,
					"is_active": 1,
				},
			)
			doc.insert(ignore_permissions=True)
			labs.append(doc.name)
			report["total_created"] += 1
		report["created"]["laboratories"] = len(labs)

		# --- Expenses (8) ---
		expenses = []
		for i in range(8):
			title = f"{marker} Expense {i+1}"
			existing = frappe.db.get_value("IC Expense Claim", {"title": title}, "name")
			if existing:
				expenses.append(existing)
				continue
			doc = frappe.get_doc(
				{
					"doctype": "IC Expense Claim",
					"title": title,
					"category": CATEGORIES[i % len(CATEGORIES)],
					"expense_date": add_days(nowdate(), -(i % 7)),
					"amount": 500 + i * 75,
					"currency": "INR",
					"description": f"QC session expense {i+1}",
					"payment_mode": "Self",
					"project": projects[i % len(projects)] if projects else None,
				}
			)
			doc.insert(ignore_permissions=True)
			expenses.append(doc.name)
			report["total_created"] += 1
		report["created"]["expenses"] = len(expenses)

		# --- Helpdesk tickets (5) ---
		tickets = []
		for i in range(5):
			subj = f"{marker} Ticket {i+1}"
			existing = frappe.db.get_value("Helpdesk Ticket", {"subject": subj}, "name")
			if existing:
				tickets.append(existing)
				continue
			doc = frappe.get_doc(
				{
					"doctype": "Helpdesk Ticket",
					"subject": subj,
					"ticket_type": "Query" if i % 2 == 0 else "Complaint",
					"priority": "Medium",
					"status": "Open",
					"description": f"QC helpdesk {i+1}",
					"customer": customers[i % len(customers)] if customers else None,
				}
			)
			doc.insert(ignore_permissions=True)
			tickets.append(doc.name)
			report["total_created"] += 1
		report["created"]["tickets"] = len(tickets)

		# --- Document requests (3) ---
		docs = []
		for i in range(3):
			title = f"{marker} DocReq {i+1}"
			# Try common title fields
			existing = None
			meta = frappe.get_meta("IC Document Request")
			title_field = "title" if meta.has_field("title") else ("subject" if meta.has_field("subject") else None)
			if title_field:
				existing = frappe.db.get_value("IC Document Request", {title_field: title}, "name")
			if existing:
				docs.append(existing)
				continue
			payload = {"doctype": "IC Document Request"}
			if title_field:
				payload[title_field] = title
			if meta.has_field("customer"):
				payload["customer"] = customers[i % len(customers)] if customers else None
			if meta.has_field("project"):
				payload["project"] = projects[i % len(projects)] if projects else None
			if meta.has_field("status"):
				payload["status"] = "Draft"
			doc = frappe.get_doc(payload)
			doc.insert(ignore_permissions=True)
			docs.append(doc.name)
			report["total_created"] += 1
		report["created"]["document_requests"] = len(docs)

		# --- Samples (3) ---
		samples = []
		if frappe.db.exists("DocType", "IC Sample Tracking"):
			meta = frappe.get_meta("IC Sample Tracking")
			for i in range(3):
				label = f"{marker} Sample {i+1}"
				existing = frappe.db.get_value(
					"IC Sample Tracking", {"sample_description": label}, "name"
				) if meta.has_field("sample_description") else None
				if existing:
					samples.append(existing)
					continue
				payload = {
					"doctype": "IC Sample Tracking",
					"sample_description": label,
					"status": "Sample Received" if meta.has_field("status") else None,
				}
				if meta.has_field("project") and projects:
					payload["project"] = projects[i % len(projects)]
				if meta.has_field("customer") and customers:
					payload["customer"] = customers[i % len(customers)]
				# drop Nones
				payload = {k: v for k, v in payload.items() if v is not None}
				try:
					doc = frappe.get_doc(payload)
					doc.insert(ignore_permissions=True)
					samples.append(doc.name)
					report["total_created"] += 1
				except Exception as e:
					report["warnings"].append(f"Sample {i+1}: {e}")
			report["created"]["samples"] = len(samples)

		# --- Tasks (5) ---
		tasks = []
		for i in range(5):
			subj = f"{marker} Task {i+1}"
			existing = frappe.db.get_value("Task", {"subject": subj}, "name")
			if existing:
				tasks.append(existing)
				continue
			doc = frappe.get_doc(
				{
					"doctype": "Task",
					"subject": subj,
					"status": "Open",
					"project": projects[i % len(projects)] if projects else None,
					"exp_end_date": add_days(nowdate(), 7 + i),
				}
			)
			doc.insert(ignore_permissions=True)
			tasks.append(doc.name)
			report["total_created"] += 1
		report["created"]["tasks"] = len(tasks)

		frappe.db.commit()

		# ---- validations ----
		total = sum(report["created"].values())
		if total >= target:
			report["validated"].append(f"Created/found {total} session records (target {target})")
		else:
			report["warnings"].append(f"Only {total} records vs target {target}")

		# Live DB counts for this session marker
		db_counts = {
			"leads": frappe.db.count("Lead", {"email_id": ["like", "qc50.lead%@example.com"]}),
			"customers": frappe.db.count("Customer", {"customer_name": ["like", f"{marker}%"]}),
			"projects": frappe.db.count("Project", {"project_name": ["like", f"{marker}%"]}),
			"expenses": frappe.db.count("IC Expense Claim", {"title": ["like", f"{marker}%"]}),
			"laboratories": frappe.db.count("IC Laboratory", {"laboratory_name": ["like", f"{marker}%"]}),
			"tickets": frappe.db.count("Helpdesk Ticket", {"subject": ["like", f"{marker}%"]}),
			"tasks": frappe.db.count("Task", {"subject": ["like", f"{marker}%"]}),
			"templates": frappe.db.count("IC Quotation Template", {"name": ["like", f"{marker}%"]}),
		}
		report["db_counts"] = db_counts
		report["validated"].append(f"DB counts={db_counts}")
		report["validated"].append(f"DB total marked≈{sum(db_counts.values())} (+quotations/docs/samples)")

		# Link checks
		linked = 0
		if frappe.get_meta("Project").has_field("ic_quotation"):
			linked = frappe.db.count("Project", {"project_name": ["like", f"{marker}%"], "ic_quotation": ["is", "set"]})
		elif frappe.get_meta("Project").has_field("custom_source_quotation"):
			linked = frappe.db.count(
				"Project", {"project_name": ["like", f"{marker}%"], "custom_source_quotation": ["is", "set"]}
			)
		report["validated"].append(f"Projects linked to quotations: {linked}")
		if linked < len(projects):
			report["warnings"].append(f"Expected {len(projects)} project↔quote links, found {linked}")

		expense_linked = frappe.db.count(
			"IC Expense Claim", {"title": ["like", f"{marker}%"], "project": ["is", "set"]}
		)
		report["validated"].append(f"Expenses linked to projects: {expense_linked}")

		# APIs still healthy
		from instacertify.setup.interop_qc import run as interop_run

		qc = interop_run()
		report["interop"] = {"ok": qc.get("ok"), "warn": qc.get("warn"), "fail": qc.get("fail")}
		if qc.get("fail"):
			report["errors"].extend(qc["report"]["fail"][:10])
		else:
			report["validated"].append(f"Interop QC ok={qc.get('ok')} warn={qc.get('warn')}")

		# Explore + library
		explore = frappe.call("instacertify.explore.dashboard.get_explore_prompts") or {}
		report["validated"].append(f"Explore cards={len(explore.get('cards') or [])}")
		lib = frappe.call("instacertify.setup.library_upload.get_library_summary") or {}
		report["validated"].append(f"Library summary={lib}")

		# Cross-session smoke: share a QC quotation + expense create API
		if quotations:
			from instacertify.quotation.events import share_with_customer

			share = share_with_customer(quotations[0])
			report["validated"].append(f"Share portal token ok for {quotations[0]} url={bool(share.get('url'))}")
		from instacertify.expenses.api import create_expense_claim

		exp = create_expense_claim(
			title=f"{marker} Interop Expense",
			category="Travel",
			amount=999,
			description="Session interop QC travel expense",
		)
		report["validated"].append(f"Expense API create={exp.get('name')}")
		report["total_created"] += 1

	except Exception:
		frappe.db.rollback()
		report["errors"].append(frappe.get_traceback())

	report["marker"] = marker
	report["ok"] = not report["errors"] and sum(report["created"].values()) >= min(target, 40)
	return report
