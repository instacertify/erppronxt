# Copyright (c) Instacertify
"""Internal project chat / collaboration."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import strip_html


@frappe.whitelist()
def get_project_messages(project: str, limit: int = 80, after: str | None = None):
	"""Return chat messages for a project (oldest first)."""
	if not project:
		frappe.throw(_("Project is required"))
	frappe.has_permission("Project", doc=project, throw=True)
	if not frappe.db.exists("DocType", "Project Chat Message"):
		return {"messages": []}

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
	return {"messages": rows, "me": frappe.session.user}


@frappe.whitelist()
def post_project_message(project: str, message: str, attachment: str | None = None, message_type: str = "Chat"):
	"""Post a chat message on a project and notify teammates."""
	if not project:
		frappe.throw(_("Project is required"))
	if not (message or "").strip() and not attachment:
		frappe.throw(_("Message cannot be empty"))
	frappe.has_permission("Project", doc=project, ptype="write", throw=False)
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
	# Also users who already chatted
	prior = frappe.get_all(
		"Project Chat Message",
		filters={"project": project, "sender": ["!=", frappe.session.user]},
		fields=["sender"],
		distinct=True,
		limit_page_length=20,
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
