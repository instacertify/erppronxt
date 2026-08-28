# Copyright (c) Instacertify
"""Scheduled notification tasks."""

from __future__ import annotations

import frappe
from frappe import _
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
		filters=[
			["status", "not in", ["Converted", "Do Not Contact"]],
			["ic_next_contact_date", "is", "set"],
			["ic_next_contact_date", "<=", today()],
		],
		fields=[
			"name",
			"lead_name",
			"company_name",
			"ic_party_name",
			"ic_call_remarks",
			"ic_lead_connected",
			"lead_owner",
			"owner",
			"ic_next_contact_date",
		],
		limit=50,
	)
	for lead in leads:
		title = lead.ic_party_name or lead.company_name or lead.lead_name or lead.name
		connected = "Connected" if lead.ic_lead_connected else "Not connected yet"
		remarks = lead.ic_call_remarks or "No call remarks yet"
		for user in set(filter(None, [lead.lead_owner, lead.owner, "Administrator"])):
			if not frappe.db.exists("User", user):
				continue
			try:
				frappe.get_doc(
					{
						"doctype": "Notification Log",
						"subject": f"Contact lead today: {title}",
						"email_content": (
							f"Next contact: {lead.ic_next_contact_date}. "
							f"{connected}. Remarks: {remarks}"
						),
						"document_type": "Lead",
						"document_name": lead.name,
						"for_user": user,
						"type": "Alert",
						"from_user": "Administrator",
					}
				).insert(ignore_permissions=True)
			except Exception:
				pass


def event_start_reminders():
	"""Notify Event participants ~30 minutes before the session starts.

	Runs every 15 minutes. Marks ic_prestart_notified so each Event only
	fires once per start time.
	"""
	from frappe.utils import add_to_date

	from instacertify.calendar.events import _participant_users

	now = frappe.utils.now_datetime()
	window_end = add_to_date(now, minutes=30)

	filters = {
		"status": ["!=", "Cancelled"],
		"starts_on": ["between", [now, window_end]],
	}
	if frappe.get_meta("Event").has_field("ic_prestart_notified"):
		filters["ic_prestart_notified"] = 0

	events = frappe.get_all(
		"Event",
		filters=filters,
		fields=["name", "subject", "starts_on", "ends_on", "owner", "location"],
		limit_page_length=100,
	)
	for row in events:
		try:
			doc = frappe.get_doc("Event", row.name)
			minutes = 30
			if doc.meta.has_field("ic_notify_minutes") and doc.get("ic_notify_minutes"):
				minutes = int(doc.ic_notify_minutes)
			starts = frappe.utils.get_datetime(doc.starts_on)
			delta_min = (starts - now).total_seconds() / 60.0
			if delta_min < 0 or delta_min > minutes:
				continue

			users = _participant_users(doc)
			when = frappe.format(doc.starts_on, {"fieldtype": "Datetime"})
			where = f" · {doc.location}" if doc.location else ""
			for user in users:
				try:
					frappe.get_doc(
						{
							"doctype": "Notification Log",
							"subject": _("Starting in ~{0} min: {1}").format(
								max(1, int(round(delta_min))), doc.subject
							),
							"email_content": _(
								"Your calendar session “{0}” starts at {1}{2}. Open Event {3}."
							).format(doc.subject, when, where, doc.name),
							"document_type": "Event",
							"document_name": doc.name,
							"for_user": user,
							"type": "Alert",
							"from_user": "Administrator",
						}
					).insert(ignore_permissions=True)
				except Exception:
					frappe.log_error(frappe.get_traceback(), f"Event 30m notify {doc.name}→{user}")

			if doc.meta.has_field("ic_prestart_notified"):
				frappe.db.set_value(
					"Event", doc.name, "ic_prestart_notified", 1, update_modified=False
				)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Event start reminder {row.name}")
