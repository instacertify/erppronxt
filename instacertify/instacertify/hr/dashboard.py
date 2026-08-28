# Copyright (c) Instacertify
"""Employee workdesk + HR self-service for Instacertify Home."""

from __future__ import annotations

import frappe
from frappe.utils import add_days, getdate, nowdate


def _current_employee():
	"""Resolve Employee linked to the logged-in user."""
	user = frappe.session.user
	if not user or user == "Guest":
		return None
	name = frappe.db.get_value("Employee", {"user_id": user, "status": "Active"}, "name")
	if name:
		return frappe.get_doc("Employee", name)
	# Administrators: prefer any active employee for desk preview
	if "System Manager" in frappe.get_roles(user):
		name = frappe.db.get_value("Employee", {"status": "Active"}, "name", order_by="creation asc")
		if name:
			return frappe.get_doc("Employee", name)
	return None


@frappe.whitelist()
def get_workdesk_insights(limit: int = 8):
	"""My tasks, upcoming calendar events, and owned leads for the home dashboard."""
	limit = int(limit or 8)
	today = getdate(nowdate())
	user = frappe.session.user

	tasks = []
	try:
		filters = [
			["status", "in", ["Open", "Working", "Pending Review"]],
		]
		# Prefer tasks assigned to me
		or_filters = [
			["owner", "=", user],
			["_assign", "like", f"%{user}%"],
		]
		rows = frappe.get_list(
			"Task",
			filters=filters,
			or_filters=or_filters,
			fields=["name", "subject", "status", "priority", "exp_end_date", "project", "modified"],
			order_by="exp_end_date asc, modified desc",
			limit_page_length=limit,
		)
		for t in rows:
			due = getdate(t.exp_end_date) if t.exp_end_date else None
			if due and due < today:
				due_label, urgency = "Overdue", "overdue"
			elif due == today:
				due_label, urgency = "Due today", "today"
			elif due:
				due_label, urgency = f"Due {due.strftime('%d %b')}", "upcoming"
			else:
				due_label, urgency = "No due date", "upcoming"
			tasks.append(
				{
					**t,
					"due_label": due_label,
					"urgency": urgency,
				}
			)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "workdesk tasks")

	events = []
	try:
		horizon = add_days(today, 14)
		rows = frappe.get_list(
			"Event",
			filters=[
				["starts_on", ">=", str(today)],
				["starts_on", "<=", f"{horizon} 23:59:59"],
				["status", "!=", "Cancelled"],
			],
			fields=["name", "subject", "starts_on", "ends_on", "event_type", "status", "description"],
			order_by="starts_on asc",
			limit_page_length=limit,
		)
		# Also include events where user is a participant when possible
		for e in rows:
			start = e.starts_on
			day = getdate(start) if start else None
			if day == today:
				when_label = "Today"
			elif day == add_days(today, 1):
				when_label = "Tomorrow"
			else:
				when_label = day.strftime("%d %b") if day else "—"
			time_label = ""
			try:
				time_label = frappe.utils.format_datetime(start, "HH:mm") if start else ""
			except Exception:
				time_label = str(start)[11:16] if start else ""
			events.append(
				{
					**e,
					"when_label": when_label,
					"time_label": time_label,
				}
			)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "workdesk events")

	my_leads = []
	try:
		my_leads = frappe.get_list(
			"Lead",
			filters={
				"status": ["not in", ["Converted", "Do Not Contact"]],
				"lead_owner": user,
			},
			fields=[
				"name",
				"lead_name",
				"company_name",
				"ic_party_name",
				"status",
				"ic_next_contact_date",
				"ic_call_remarks",
				"ic_lead_connected",
			],
			order_by="ic_next_contact_date asc, modified desc",
			limit_page_length=limit,
		)
		if not my_leads and "System Manager" in frappe.get_roles(user):
			my_leads = frappe.get_list(
				"Lead",
				filters={"status": ["not in", ["Converted", "Do Not Contact"]]},
				fields=[
					"name",
					"lead_name",
					"company_name",
					"ic_party_name",
					"status",
					"ic_next_contact_date",
					"ic_call_remarks",
					"ic_lead_connected",
				],
				order_by="modified desc",
				limit_page_length=limit,
			)
		for lead in my_leads:
			lead["title"] = lead.get("ic_party_name") or lead.get("company_name") or lead.get("lead_name") or lead.name
	except Exception:
		frappe.log_error(frappe.get_traceback(), "workdesk leads")

	return {
		"today": str(today),
		"tasks": tasks,
		"events": events,
		"my_leads": my_leads,
		"task_count": len(tasks),
		"event_count": len(events),
		"lead_count": len(my_leads),
	}


@frappe.whitelist()
def get_my_hr_panel(limit: int = 12):
	"""HR self-service: profile, joining letters, salary slips & employment documents."""
	limit = int(limit or 12)
	emp = _current_employee()
	if not emp:
		return {
			"employee": None,
			"message": "No Employee linked to your login. Ask HR to set User ID on your Employee record.",
			"joining_letters": [],
			"salary_slips": [],
			"documents": [],
			"links": _hr_links(),
		}

	profile = {
		"name": emp.name,
		"employee_name": emp.employee_name,
		"designation": emp.get("designation"),
		"department": emp.get("department"),
		"date_of_joining": str(emp.get("date_of_joining") or ""),
		"status": emp.status,
		"company_email": emp.get("company_email") or emp.get("prefered_email"),
		"cell_number": emp.get("cell_number"),
	}

	joining_letters = []
	if frappe.db.exists("DocType", "IC Joining Letter"):
		joining_letters = frappe.get_all(
			"IC Joining Letter",
			filters={"employee": emp.name},
			fields=["name", "employee_name", "joining_date", "designation", "department", "modified"],
			order_by="joining_date desc",
			limit_page_length=limit,
		)

	salary_slips = []
	documents = []
	if frappe.db.exists("DocType", "IC Employee Document"):
		docs = frappe.get_all(
			"IC Employee Document",
			filters={"employee": emp.name},
			fields=[
				"name",
				"document_title",
				"document_type",
				"attachment",
				"issue_date",
				"modified",
			],
			order_by="issue_date desc, modified desc",
			limit_page_length=limit,
		)
		for d in docs:
			if d.document_type == "Salary Slip":
				salary_slips.append(d)
			else:
				documents.append(d)

	return {
		"employee": profile,
		"joining_letters": joining_letters,
		"salary_slips": salary_slips,
		"documents": documents,
		"links": _hr_links(emp.name),
	}


def _hr_links(employee: str | None = None):
	links = [
		{"label": "My Employee Profile", "route": f"/app/employee/{employee}" if employee else "/app/employee"},
		{"label": "Joining Letters", "route": "/app/ic-joining-letter"},
		{"label": "Employment Documents", "route": "/app/ic-employee-document"},
		{"label": "Salary Slips (documents)", "route": "/app/ic-employee-document?document_type=Salary%20Slip"},
		{"label": "Holiday List", "route": "/app/holiday-list"},
	]
	if frappe.db.exists("DocType", "Attendance"):
		links.insert(3, {"label": "Attendance", "route": "/app/attendance"})
	if frappe.db.exists("DocType", "Salary Slip"):
		links.insert(3, {"label": "Salary Slips", "route": "/app/salary-slip"})
	return links
