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

	_sync_project_team(doc)
	_sync_amc_dates(doc)
	if doc.ic_project_stage == "Project Completed" and doc.status != "Completed":
		doc.status = "Completed"


def _sync_project_team(doc):
	"""Keep Assign People, Primary Assignee, and ERPNext Users table aligned."""
	members = []
	seen = set()
	for row in doc.get("ic_team_members") or []:
		user = row.get("user")
		if not user or user in seen:
			continue
		seen.add(user)
		if not row.get("full_name"):
			row.full_name = frappe.db.get_value("User", user, "full_name") or user
		role = row.get("role_on_project") or "Member"
		members.append({"user": user, "full_name": row.full_name, "role_on_project": role})

	# Seed from legacy primary if team empty
	if not members and doc.get("ic_assigned_employee"):
		user = doc.ic_assigned_employee
		members.append(
			{
				"user": user,
				"full_name": frappe.db.get_value("User", user, "full_name") or user,
				"role_on_project": "Primary",
			}
		)
		doc.set("ic_team_members", [])
		doc.append(
			"ic_team_members",
			{"user": user, "full_name": members[0]["full_name"], "role_on_project": "Primary"},
		)

	# Ensure a single Primary
	primaries = [m for m in members if m["role_on_project"] == "Primary"]
	if members and not primaries:
		members[0]["role_on_project"] = "Primary"
		if doc.get("ic_team_members"):
			doc.ic_team_members[0].role_on_project = "Primary"
	elif len(primaries) > 1:
		# Keep first Primary only
		first = True
		for row in doc.get("ic_team_members") or []:
			if row.get("role_on_project") == "Primary":
				if first:
					first = False
				else:
					row.role_on_project = "Member"
		members = []
		seen = set()
		for row in doc.get("ic_team_members") or []:
			if row.user and row.user not in seen:
				seen.add(row.user)
				members.append(
					{
						"user": row.user,
						"full_name": row.full_name or row.user,
						"role_on_project": row.role_on_project or "Member",
					}
				)

	primary = next((m for m in members if m["role_on_project"] == "Primary"), members[0] if members else None)
	doc.ic_assigned_employee = primary["user"] if primary else None

	# Sync into standard Project User child table when present
	if doc.meta.has_field("users"):
		existing = {row.user: row for row in (doc.get("users") or []) if row.get("user")}
		wanted = {m["user"] for m in members}
		# Remove users no longer assigned (only those we manage — keep unmatched? remove extras from team sync)
		doc.set(
			"users",
			[row for row in (doc.get("users") or []) if row.get("user") in wanted],
		)
		have = {row.user for row in (doc.get("users") or []) if row.get("user")}
		for m in members:
			if m["user"] not in have:
				doc.append("users", {"user": m["user"]})


def get_project_assignee_users(project) -> list[str]:
	"""Return user ids assigned to a project (team + primary + users table)."""
	if isinstance(project, str):
		if not frappe.db.exists("Project", project):
			return []
		project = frappe.get_doc("Project", project)
	users = []
	for row in project.get("ic_team_members") or []:
		if row.get("user"):
			users.append(row.user)
	if project.get("ic_assigned_employee"):
		users.append(project.ic_assigned_employee)
	if project.meta.has_field("users"):
		for row in project.get("users") or []:
			if row.get("user"):
				users.append(row.user)
	# unique preserve order
	out = []
	seen = set()
	for u in users:
		if u and u not in seen:
			seen.add(u)
			out.append(u)
	return out


def format_assignee_label(project) -> str:
	"""Human label for tiles: 'Priya Sharma +2'."""
	if isinstance(project, str):
		names = frappe.get_all(
			"Project Team Member",
			filters={"parent": project, "parenttype": "Project"},
			fields=["user", "full_name", "role_on_project"],
			order_by="idx asc",
		)
		if not names:
			primary = frappe.db.get_value("Project", project, "ic_assigned_employee")
			if primary:
				return frappe.db.get_value("User", primary, "full_name") or primary
			return "Unassigned"
		ordered = sorted(names, key=lambda r: 0 if r.role_on_project == "Primary" else 1)
		first = ordered[0].full_name or frappe.db.get_value("User", ordered[0].user, "full_name") or ordered[0].user
		extra = len(ordered) - 1
		return f"{first} +{extra}" if extra else first

	users = get_project_assignee_users(project)
	if not users:
		return "Unassigned"
	first = frappe.db.get_value("User", users[0], "full_name") or users[0]
	extra = len(users) - 1
	return f"{first} +{extra}" if extra else first



def _sync_amc_dates(doc):
	if not doc.get("ic_requires_amc"):
		if doc.get("ic_amc_status") not in (None, "", "Not Applicable"):
			doc.ic_amc_status = "Not Applicable"
		return
	if doc.ic_amc_contact_date:
		doc.ic_amc_reminder_date = frappe.utils.add_months(doc.ic_amc_contact_date, -1)
		if doc.ic_amc_status in (None, "", "Not Applicable"):
			doc.ic_amc_status = "Scheduled"


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

	if doc.get("ic_requires_amc") and doc.get("ic_amc_contact_date"):
		_ensure_amc_event(doc)


def _notify_stage_change(doc):
	users = get_project_assignee_users(doc) + [doc.owner, "Administrator"]
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


def _amc_notify_users(doc):
	users = set(filter(None, get_project_assignee_users(doc) + [doc.owner, "Administrator"]))
	try:
		from frappe.utils.user import get_users_with_role

		for role in ("IC Admin", "Sales Manager", "IC Sales Person"):
			users.update(get_users_with_role(role) or [])
	except Exception:
		pass
	return [u for u in users if frappe.db.exists("User", u) and u != "Guest"]


def _ensure_amc_event(doc):
	"""Create / refresh calendar Event for AMC contact date."""
	if not doc.ic_amc_contact_date:
		return
	subject = f"AMC Contact: {doc.project_name or doc.name}"
	starts = f"{doc.ic_amc_contact_date} 10:00:00"
	ends = f"{doc.ic_amc_contact_date} 11:00:00"
	try:
		if doc.ic_amc_event and frappe.db.exists("Event", doc.ic_amc_event):
			ev = frappe.get_doc("Event", doc.ic_amc_event)
			ev.subject = subject
			ev.starts_on = starts
			ev.ends_on = ends
			ev.save(ignore_permissions=True)
			return
		ev = frappe.get_doc(
			{
				"doctype": "Event",
				"subject": subject,
				"event_type": "Public",
				"starts_on": starts,
				"ends_on": ends,
				"all_day": 0,
				"send_reminder": 1,
				"description": (
					f"AMC / renewal contact for project <b>{doc.name}</b>"
					f"<br>Customer: {doc.customer or '-'}"
					f"<br>Reminder fires 1 month prior ({doc.ic_amc_reminder_date or '-'})"
				),
				"reference_doctype": "Project",
				"reference_docname": doc.name,
			}
		)
		for user in _amc_notify_users(doc)[:10]:
			ev.append("event_participants", {"reference_doctype": "User", "reference_docname": user})
		ev.insert(ignore_permissions=True)
		frappe.db.set_value("Project", doc.name, "ic_amc_event", ev.name, update_modified=False)
		doc.ic_amc_event = ev.name
	except Exception:
		frappe.log_error(frappe.get_traceback(), "AMC Event create")


@frappe.whitelist()
def schedule_project_amc(project: str, contact_date: str = None):
	"""Mark project as requiring AMC and schedule calendar + reminders."""
	doc = frappe.get_doc("Project", project)
	doc.ic_requires_amc = 1
	doc.ic_amc_contact_date = contact_date or frappe.utils.add_years(frappe.utils.today(), 1)
	doc.ic_amc_status = "Scheduled"
	_sync_amc_dates(doc)
	doc.save(ignore_permissions=True)
	_ensure_amc_event(doc)
	# Immediate highlight to Admin / Sales
	for user in _amc_notify_users(doc):
		try:
			frappe.get_doc(
				{
					"doctype": "Notification Log",
					"subject": f"AMC scheduled: {doc.project_name or doc.name}",
					"email_content": (
						f"Contact on {doc.ic_amc_contact_date}. "
						f"Reminder on {doc.ic_amc_reminder_date}."
					),
					"document_type": "Project",
					"document_name": doc.name,
					"for_user": user,
					"type": "Alert",
					"from_user": frappe.session.user,
				}
			).insert(ignore_permissions=True)
		except Exception:
			pass
	return {
		"project": doc.name,
		"contact_date": str(doc.ic_amc_contact_date),
		"reminder_date": str(doc.ic_amc_reminder_date),
		"event": doc.ic_amc_event,
	}


@frappe.whitelist()
def get_ongoing_project_cards(limit: int = 12):
	"""Return project tile data for dashboard / board (permission-aware)."""
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
			"modified",
		],
		order_by="ic_deadline asc, modified desc",
		limit_page_length=int(limit or 12),
	)
	today = frappe.utils.getdate(frappe.utils.today())
	for p in projects:
		_enrich_project_tile(p, today)
	return projects


def _enrich_project_tile(p, today=None):
	today = today or frappe.utils.getdate(frappe.utils.today())
	if p.get("customer"):
		p["customer_name"] = frappe.db.get_value("Customer", p.customer, "customer_name")
	p["progress"] = int(round(p.get("ic_progress_percentage") or p.get("percent_complete") or 0))
	p["deadline"] = p.get("ic_deadline") or p.get("expected_end_date")
	p["deadline_label"] = (
		frappe.utils.formatdate(p["deadline"], "dd MMM yyyy") if p.get("deadline") else ""
	)
	days_left = None
	urgency = "ok"
	if p.get("deadline"):
		try:
			days_left = (frappe.utils.getdate(p["deadline"]) - today).days
			if days_left < 0:
				urgency = "overdue"
			elif days_left <= 3:
				urgency = "soon"
			elif days_left <= 14:
				urgency = "upcoming"
		except Exception:
			days_left = None
	p["days_left"] = days_left
	p["urgency"] = urgency
	p["assigned_name"] = format_assignee_label(p.get("name"))
	# detailed list for UI tooltips
	team = frappe.get_all(
		"Project Team Member",
		filters={"parent": p.get("name"), "parenttype": "Project"},
		fields=["user", "full_name", "role_on_project"],
		order_by="idx asc",
	)
	if not team and p.get("ic_assigned_employee"):
		uid = p.ic_assigned_employee
		team = [
			{
				"user": uid,
				"full_name": frappe.db.get_value("User", uid, "full_name") or uid,
				"role_on_project": "Primary",
			}
		]
	p["assignees"] = team
	p["assignee_count"] = len(team)
	title = p.get("project_name") or p.get("name") or "?"
	parts = [x for x in title.replace("-", " ").split() if x]
	p["initials"] = ("".join(w[0] for w in parts[:2]) or "?").upper()
	p["stage"] = p.get("ic_project_stage") or p.get("status") or "Active"
	p["priority"] = p.get("ic_priority") or "Medium"


@frappe.whitelist()
def get_project_board(limit: int = 48, search: str | None = None, priority: str | None = None):
	"""Tile board for Project list / Projects page."""
	limit = min(int(limit or 48), 100)
	filters: dict = {"status": ["not in", ["Cancelled"]]}
	if priority and priority not in ("All", ""):
		filters["ic_priority"] = priority
	or_filters = None
	search = (search or "").strip()
	if search:
		or_filters = [
			["project_name", "like", f"%{search}%"],
			["name", "like", f"%{search}%"],
			["customer", "like", f"%{search}%"],
		]
	projects = frappe.get_list(
		"Project",
		filters=filters,
		or_filters=or_filters,
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
			"modified",
		],
		order_by="modified desc",
		limit_page_length=limit,
	)
	today = frappe.utils.getdate(frappe.utils.today())
	for p in projects:
		_enrich_project_tile(p, today)
	return {"projects": projects}



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
		"open_tickets": count(
			"Helpdesk Ticket",
			{"status": ["in", ["Open", "In Progress", "Waiting on Customer"]]},
		),
		"open_complaints": count(
			"Helpdesk Ticket",
			{
				"status": ["in", ["Open", "In Progress", "Waiting on Customer"]],
				"ticket_type": "Complaint",
			},
		),
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
		"amc_due_soon": count(
			"Project",
			{
				"ic_requires_amc": 1,
				"ic_amc_status": ["in", ["Scheduled", "Reminded"]],
				"ic_amc_contact_date": [
					"<=",
					frappe.utils.add_days(frappe.utils.today(), 31),
				],
			},
		),
		"leads_to_contact": count(
			"Lead",
			[
				["status", "not in", ["Converted", "Do Not Contact"]],
				["ic_next_contact_date", "is", "set"],
				["ic_next_contact_date", "<=", frappe.utils.today()],
			],
		),
	}
