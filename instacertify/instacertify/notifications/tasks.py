# Copyright (c) Instacertify
"""Scheduled notification tasks."""

from __future__ import annotations

import frappe
from frappe.utils import add_days, today


def deadline_reminders():
	"""Notify assignees of upcoming project deadlines."""
	cutoff = add_days(today(), 3)
	projects = frappe.get_all(
		"Project",
		filters={
			"status": ["not in", ["Completed", "Cancelled"]],
			"ic_deadline": ["between", [today(), cutoff]],
		},
		fields=["name", "project_name", "ic_deadline", "ic_assigned_employee", "owner"],
	)
	for p in projects:
		for user in set(filter(None, [p.ic_assigned_employee, p.owner])):
			if not frappe.db.exists("User", user):
				continue
			frappe.get_doc(
				{
					"doctype": "Notification Log",
					"subject": f"Deadline approaching: {p.project_name}",
					"email_content": f"Project {p.name} deadline is {p.ic_deadline}",
					"document_type": "Project",
					"document_name": p.name,
					"for_user": user,
					"type": "Alert",
					"from_user": "Administrator",
				}
			).insert(ignore_permissions=True)
