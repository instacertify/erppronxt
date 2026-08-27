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

	amc_renewal_reminders()
	lead_contact_reminders()


def amc_renewal_reminders():
	"""1 month prior to AMC contact — highlight Admin, Sales Manager, creator."""
	if not frappe.get_meta("Project").has_field("ic_requires_amc"):
		return
	due = frappe.get_all(
		"Project",
		filters={
			"ic_requires_amc": 1,
			"ic_amc_status": ["in", ["Scheduled", "Reminded"]],
			"ic_amc_reminder_date": ["<=", today()],
			"ic_amc_contact_date": [">=", today()],
		},
		fields=[
			"name",
			"project_name",
			"customer",
			"ic_amc_contact_date",
			"ic_amc_reminder_date",
			"ic_amc_last_notified",
			"ic_assigned_employee",
			"owner",
		],
	)
	from instacertify.project.events import _amc_notify_users

	for p in due:
		if p.ic_amc_last_notified == today():
			continue
		doc = frappe.get_doc("Project", p.name)
		for user in _amc_notify_users(doc):
			try:
				frappe.get_doc(
					{
						"doctype": "Notification Log",
						"subject": f"AMC renewal contact due: {p.project_name}",
						"email_content": (
							f"Contact customer by {p.ic_amc_contact_date} for AMC / renewal. "
							f"Project {p.name}."
						),
						"document_type": "Project",
						"document_name": p.name,
						"for_user": user,
						"type": "Alert",
						"from_user": "Administrator",
					}
				).insert(ignore_permissions=True)
			except Exception:
				pass
		frappe.db.set_value(
			"Project",
			p.name,
			{"ic_amc_status": "Reminded", "ic_amc_last_notified": today()},
			update_modified=False,
		)


def lead_contact_reminders():
	"""Prompt when Lead next-contact date is due."""
	if not frappe.get_meta("Lead").has_field("ic_next_contact_date"):
		return
	leads = frappe.get_all(
		"Lead",
		filters={
			"status": ["not in", ["Converted", "Do Not Contact"]],
			"ic_next_contact_date": ["<=", today()],
		},
		fields=["name", "lead_name", "company_name", "ic_call_remarks", "lead_owner", "owner"],
		limit=50,
	)
	for lead in leads:
		for user in set(filter(None, [lead.lead_owner, lead.owner, "Administrator"])):
			if not frappe.db.exists("User", user):
				continue
			try:
				frappe.get_doc(
					{
						"doctype": "Notification Log",
						"subject": f"Contact lead: {lead.company_name or lead.lead_name or lead.name}",
						"email_content": lead.ic_call_remarks or "Follow up as scheduled",
						"document_type": "Lead",
						"document_name": lead.name,
						"for_user": user,
						"type": "Alert",
						"from_user": "Administrator",
					}
				).insert(ignore_permissions=True)
			except Exception:
				pass
