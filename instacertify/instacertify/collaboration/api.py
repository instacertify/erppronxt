# Copyright (c) Instacertify
"""Internal project chat / collaboration."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, strip_html


@frappe.whitelist()
def list_chat_rooms(search: str | None = None, limit: int = 40):
	"""Projects the user can discuss, with last message preview."""
	limit = min(cint(limit) or 40, 100)
	search = (search or "").strip()

	filters: dict = {"status": ["not in", ["Cancelled"]]}
	or_filters = None
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
		fields=["name", "project_name", "status", "customer", "percent_complete", "modified"],
		order_by="modified desc",
		limit_page_length=limit,
		ignore_permissions=False,
	)

	rooms = []
	for p in projects:
		last = _last_message(p.name)
		msg_count = (
			frappe.db.count("Project Chat Message", {"project": p.name})
			if frappe.db.exists("DocType", "Project Chat Message")
			else 0
		)
		rooms.append(
			{
				"project": p.name,
				"project_name": p.project_name or p.name,
				"status": p.status,
				"customer": p.customer,
				"percent_complete": p.percent_complete,
				"message_count": msg_count,
				"last_message": (last or {}).get("plain") or "",
				"last_sender": (last or {}).get("sender_name") or (last or {}).get("sender") or "",
				"last_at": (last or {}).get("creation"),
				"last_at_label": (last or {}).get("time_label") or "",
				"has_activity": 1 if last else 0,
			}
		)

	# Active chats first, then by last activity / project modified
	rooms.sort(
		key=lambda r: (
			0 if r["has_activity"] else 1,
			r["last_at"] or "",
			r.get("project_name") or "",
		),
		reverse=True,
	)
	return {"rooms": rooms, "me": frappe.session.user}


@frappe.whitelist()
def get_recent_chat_activity(limit: int = 8):
	"""Recent project chats for home dashboard."""
	limit = min(cint(limit) or 8, 30)
	if not frappe.db.exists("DocType", "Project Chat Message"):
		return {"items": []}

	rows = frappe.get_all(
		"Project Chat Message",
		fields=[
			"name",
			"project",
			"sender",
			"sender_name",
			"message",
			"creation",
		],
		order_by="creation desc",
		limit_page_length=limit * 3,
	)

	# Keep one preview per project, only for projects user can read
	seen = set()
	items = []
	for r in rows:
		if r.project in seen:
			continue
		if not frappe.has_permission("Project", doc=r.project):
			continue
		seen.add(r.project)
		project_name = frappe.db.get_value("Project", r.project, "project_name") or r.project
		items.append(
			{
				"project": r.project,
				"project_name": project_name,
				"sender_name": r.sender_name or r.sender,
				"plain": strip_html(r.message or "")[:160],
				"time_label": frappe.utils.format_datetime(r.creation, "dd MMM HH:mm") if r.creation else "",
				"is_mine": 1 if r.sender == frappe.session.user else 0,
			}
		)
		if len(items) >= limit:
			break
	return {"items": items}


@frappe.whitelist()
def get_project_messages(project: str, limit: int = 80, after: str | None = None):
	"""Return chat messages for a project (oldest first)."""
	if not project:
		frappe.throw(_("Project is required"))
	frappe.has_permission("Project", doc=project, throw=True)
	if not frappe.db.exists("DocType", "Project Chat Message"):
		return {"messages": [], "project": _project_meta(project), "me": frappe.session.user}

	filters = {"project": project}
	if after:
		filters["creation"] = [">", after]

	rows = frappe.get_all(
		"Project Chat Message",
		filters=filters,
		fields=[
			"name",
			"project",
			"sender",
			"sender_name",
			"message",
			"message_type",
			"attachment",
			"creation",
			"modified",
		],
		order_by="creation asc",
		limit_page_length=int(limit or 80),
	)
	for r in rows:
		r["plain"] = strip_html(r.message or "")[:500]
		r["is_mine"] = 1 if r.sender == frappe.session.user else 0
		r["time_label"] = frappe.utils.format_datetime(r.creation, "dd MMM HH:mm") if r.creation else ""
	return {
		"messages": rows,
		"project": _project_meta(project),
		"me": frappe.session.user,
	}


@frappe.whitelist()
def post_project_message(project: str, message: str, attachment: str | None = None, message_type: str = "Chat"):
	"""Post a chat message on a project and notify teammates."""
	if not project:
		frappe.throw(_("Project is required"))
	if not (message or "").strip() and not attachment:
		frappe.throw(_("Message cannot be empty"))
	# Allow users who can read the project to chat
	frappe.has_permission("Project", doc=project, throw=True)

	doc = frappe.get_doc(
		{
			"doctype": "Project Chat Message",
			"project": project,
			"sender": frappe.session.user,
			"message": message,
			"attachment": attachment,
			"message_type": message_type or "Chat",
		}
	)
	doc.insert(ignore_permissions=True)
	_notify_project_team(project, doc)
	return {
		"name": doc.name,
		"sender": doc.sender,
		"sender_name": doc.sender_name,
		"message": doc.message,
		"attachment": doc.attachment,
		"creation": str(doc.creation),
		"is_mine": 1,
		"time_label": frappe.utils.format_datetime(doc.creation, "dd MMM HH:mm"),
		"plain": strip_html(doc.message or "")[:500],
	}


def _project_meta(project: str) -> dict:
	row = frappe.db.get_value(
		"Project",
		project,
		["name", "project_name", "status", "customer", "percent_complete"],
		as_dict=True,
	)
	return row or {"name": project, "project_name": project}


def _last_message(project: str) -> dict | None:
	if not frappe.db.exists("DocType", "Project Chat Message"):
		return None
	rows = frappe.get_all(
		"Project Chat Message",
		filters={"project": project},
		fields=["sender", "sender_name", "message", "creation"],
		order_by="creation desc",
		limit_page_length=1,
	)
	if not rows:
		return None
	r = rows[0]
	r["plain"] = strip_html(r.message or "")[:140]
	r["time_label"] = frappe.utils.format_datetime(r.creation, "dd MMM HH:mm") if r.creation else ""
	return r


def _notify_project_team(project: str, msg_doc):
	proj = frappe.get_doc("Project", project)
	recipients = [proj.owner, "Administrator"]
	if proj.get("ic_assigned_employee"):
		assigned = proj.ic_assigned_employee
		if frappe.db.exists("User", assigned):
			recipients.append(assigned)
		else:
			uid = frappe.db.get_value("Employee", assigned, "user_id")
			if uid:
				recipients.append(uid)

	# Standard Project User child table (multiple assignees)
	if proj.meta.has_field("users"):
		for row in proj.get("users") or []:
			if row.get("user"):
				recipients.append(row.user)

	# Also users who already chatted
	prior = frappe.get_all(
		"Project Chat Message",
		filters={"project": project, "sender": ["!=", frappe.session.user]},
		fields=["sender"],
		distinct=True,
		limit_page_length=40,
	)
	for p in prior:
		recipients.append(p.sender)

	snippet = strip_html(msg_doc.message or "")[:120]
	for user in set(filter(None, recipients)):
		if user == frappe.session.user or not frappe.db.exists("User", user):
			continue
		try:
			frappe.get_doc(
				{
					"doctype": "Notification Log",
					"subject": f"Project chat: {proj.project_name or project}",
					"email_content": f"{msg_doc.sender_name or msg_doc.sender}: {snippet}",
					"document_type": "Project",
					"document_name": project,
					"for_user": user,
					"type": "Alert",
					"from_user": frappe.session.user,
				}
			).insert(ignore_permissions=True)
		except Exception:
			pass
