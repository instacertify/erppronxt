# Copyright (c) Instacertify
"""Project events and helpers."""

from __future__ import annotations

import frappe

STAGE_PROGRESS = {
	"Project Initiated": 5,
	"Customer Documents Pending": 15,
	"Documents Under Review": 25,
	"Application Submitted": 35,
	"Sample Awaited": 40,
	"Sample Received": 50,
	"Sample Dispatched to Laboratory": 55,
	"Testing in Progress": 65,
	"Report Awaited": 70,
	"Report Available": 80,
	"Certification in Progress": 85,
	"Certificate Available": 92,
	"Delivered to Customer": 98,
	"Project Completed": 100,
}


def validate_project(doc, method=None):
	if doc.ic_project_stage and not doc.ic_progress_percentage:
		doc.ic_progress_percentage = STAGE_PROGRESS.get(doc.ic_project_stage, doc.ic_progress_percentage)
	elif doc.ic_project_stage and doc.has_value_changed("ic_project_stage"):
		suggested = STAGE_PROGRESS.get(doc.ic_project_stage)
		if suggested is not None:
			doc.ic_progress_percentage = suggested


def on_update_project(doc, method=None):
	if doc.has_value_changed("ic_project_stage"):
		_notify_stage_change(doc)
		# Auto create project update timeline entry
		try:
			frappe.get_doc(
				{
					"doctype": "IC Project Update",
					"project": doc.name,
					"subject": f"Stage changed to {doc.ic_project_stage}",
					"project_stage": doc.ic_project_stage,
					"progress_percentage": doc.ic_progress_percentage,
					"pending_action": doc.ic_pending_action,
					"remarks": f"Project stage updated to <b>{doc.ic_project_stage}</b>",
					"updated_by": frappe.session.user,
				}
			).insert(ignore_permissions=True)
		except Exception:
			pass


def _notify_stage_change(doc):
	users = [doc.ic_assigned_employee, doc.owner, "Administrator"]
	for user in set(filter(None, users)):
		if not frappe.db.exists("User", user):
			continue
		try:
			frappe.get_doc(
				{
					"doctype": "Notification Log",
					"subject": f"Project {doc.name}: {doc.ic_project_stage}",
					"email_content": f"Status changed to {doc.ic_project_stage}",
					"document_type": "Project",
					"document_name": doc.name,
					"for_user": user,
					"type": "Alert",
					"from_user": frappe.session.user,
				}
			).insert(ignore_permissions=True)
		except Exception:
			pass


@frappe.whitelist()
def get_ongoing_project_cards(limit: int = 8):
	"""Return project card data for dashboard (permission-aware)."""
	filters = {"status": ["not in", ["Cancelled", "Completed"]]}
	projects = frappe.get_list(
		"Project",
		filters=filters,
		fields=[
			"name",
			"project_name",
			"customer",
			"status",
			"percent_complete",
			"ic_project_stage",
			"ic_priority",
			"ic_pending_action",
			"ic_progress_percentage",
			"ic_assigned_employee",
			"ic_deadline",
			"expected_end_date",
		],
		order_by="ic_deadline asc, modified desc",
		limit_page_length=int(limit),
	)
	for p in projects:
		if p.get("customer"):
			p["customer_name"] = frappe.db.get_value("Customer", p.customer, "customer_name")
		p["progress"] = p.get("ic_progress_percentage") or p.get("percent_complete") or 0
		p["deadline"] = p.get("ic_deadline") or p.get("expected_end_date")
	return projects


@frappe.whitelist()
def get_dashboard_counts():
	"""Role-aware summary counts for Instacertify Home."""
	def count(doctype, filters=None):
		try:
			return frappe.db.count(doctype, filters or {})
		except Exception:
			return 0

	return {
		"new_leads": count("Lead", {"status": "Lead"}),
		"active_leads": count("Lead", {"status": ["in", ["Open", "Replied", "Opportunity"]]}),
		"quotations_sent": count(
			"Quotation", {"ic_workflow_status": ["in", ["Shared with Customer", "Customer Review"]]}
		),
		"quotations_awaiting": count(
			"Quotation", {"ic_workflow_status": ["in", ["Shared with Customer", "Customer Review"]]}
		),
		"quotations_accepted": count("Quotation", {"ic_workflow_status": "Accepted"}),
		"active_projects": count("Project", {"status": ["not in", ["Completed", "Cancelled"]]}),
		"pending_tasks": count("Task", {"status": ["in", ["Open", "Working"]]}),
		"pending_documents": count(
			"IC Document Request", {"status": ["in", ["Sent to Customer", "Partially Uploaded"]]}
		),
		"testing_requests": count(
			"IC Testing Request",
			{"status": ["not in", ["Report Shared with Customer"]]},
		),
		"upcoming_deadlines": count(
			"Project",
			{
				"status": ["not in", ["Completed", "Cancelled"]],
				"ic_deadline": ["<=", frappe.utils.add_days(frappe.utils.today(), 14)],
			},
		),
	}
