# Copyright (c) Instacertify
"""Shared team calendar — Event participants, sharing, and session booking."""

from __future__ import annotations

import frappe
import frappe.share
from frappe import _
from frappe.utils import get_datetime, now_datetime


def validate_event(doc, method=None):
	"""Keep participant emails in sync and reset reminder flag when time changes."""
	_sync_participant_emails(doc)
	_ensure_defaults(doc)
	if doc.has_value_changed("starts_on"):
		if doc.meta.has_field("ic_prestart_notified"):
			doc.ic_prestart_notified = 0


def on_update_event(doc, method=None):
	"""Share Event with all User participants so teammates see private sessions."""
	_share_with_participants(doc)
	_notify_new_participants(doc)


def after_insert_event(doc, method=None):
	_share_with_participants(doc)
	_notify_new_participants(doc, force=True)


def _ensure_defaults(doc):
	if not doc.event_category:
		doc.event_category = "Meeting"
	if doc.send_reminder is None:
		doc.send_reminder = 1
	if doc.meta.has_field("ic_notify_minutes") and not doc.get("ic_notify_minutes"):
		doc.ic_notify_minutes = 30
	if doc.meta.has_field("ic_booked_by") and not doc.get("ic_booked_by"):
		doc.ic_booked_by = frappe.session.user


def _sync_participant_emails(doc):
	"""Frappe permission checks use participant.email — must match User name."""
	for row in doc.get("event_participants") or []:
		if not row.reference_doctype or not row.reference_docname:
			continue
		email = None
		if row.reference_doctype == "User":
			email = row.reference_docname
		elif row.reference_doctype == "Employee":
			email = frappe.db.get_value("Employee", row.reference_docname, "user_id")
		elif row.reference_doctype == "Contact":
			email = frappe.db.get_value("Contact", row.reference_docname, "email_id")
		if email and row.email != email:
			row.email = email


def _participant_users(doc) -> set[str]:
	users = set()
	for row in doc.get("event_participants") or []:
		user = None
		if row.reference_doctype == "User" and row.reference_docname:
			user = row.reference_docname
		elif row.email and frappe.db.exists("User", row.email):
			user = row.email
		elif row.reference_doctype == "Employee" and row.reference_docname:
			user = frappe.db.get_value("Employee", row.reference_docname, "user_id")
		if user and user not in ("Guest", "Administrator") and frappe.db.exists("User", user):
			users.add(user)
	if doc.owner and doc.owner not in ("Guest",):
		users.add(doc.owner)
	return users


def _share_with_participants(doc):
	for user in _participant_users(doc):
		if user == doc.owner:
			continue
		try:
			frappe.share.add_docshare(
				"Event",
				doc.name,
				user,
				read=1,
				write=0,
				share=0,
				notify=0,
				flags={"ignore_share_permission": True},
			)
		except Exception:
			try:
				frappe.share.add("Event", doc.name, user, read=1, write=0, share=0, notify=0)
			except Exception:
				frappe.log_error(frappe.get_traceback(), f"Event share {doc.name} → {user}")


def _notify_new_participants(doc, force: bool = False):
	"""Alert users when they are booked onto a session."""
	users = _participant_users(doc)
	actor = frappe.session.user
	for user in users:
		if user == actor and not force:
			continue
		# Avoid spamming on every save — only when newly added or forced insert
		if not force:
			prev = doc.get_doc_before_save()
			if prev:
				prev_users = _participant_users(prev)
				if user in prev_users:
					continue
		try:
			frappe.get_doc(
				{
					"doctype": "Notification Log",
					"subject": _("Calendar session: {0}").format(doc.subject),
					"email_content": _(
						"{0} booked you for “{1}” starting {2}. Open your calendar to review."
					).format(
						frappe.db.get_value("User", actor, "full_name") or actor,
						doc.subject,
						frappe.format(doc.starts_on, {"fieldtype": "Datetime"}),
					),
					"document_type": "Event",
					"document_name": doc.name,
					"for_user": user,
					"type": "Alert",
					"from_user": actor if frappe.db.exists("User", actor) else "Administrator",
				}
			).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Event invite notify {doc.name}")


@frappe.whitelist()
def create_team_session(
	subject: str,
	starts_on: str,
	ends_on: str | None = None,
	participants: str | list | None = None,
	description: str | None = None,
	location: str | None = None,
	event_type: str = "Public",
	all_day: int = 0,
):
	"""Book a calendar session and invite teammates (any Desk User can call)."""
	if not subject or not starts_on:
		frappe.throw(_("Subject and start time are required"))

	if isinstance(participants, str):
		try:
			participants = frappe.parse_json(participants)
		except Exception:
			participants = [p.strip() for p in participants.split(",") if p.strip()]

	participants = participants or []
	starts = get_datetime(starts_on)
	ends = get_datetime(ends_on) if ends_on else frappe.utils.add_to_date(starts, hours=1)

	doc = frappe.get_doc(
		{
			"doctype": "Event",
			"subject": subject,
			"starts_on": starts,
			"ends_on": ends,
			"all_day": int(all_day or 0),
			"event_type": event_type if event_type in ("Public", "Private") else "Public",
			"event_category": "Meeting",
			"send_reminder": 1,
			"status": "Open",
			"description": description,
			"location": location,
		}
	)
	if doc.meta.has_field("ic_notify_minutes"):
		doc.ic_notify_minutes = 30
	if doc.meta.has_field("ic_booked_by"):
		doc.ic_booked_by = frappe.session.user

	# Always include the booker
	seen = set()
	for user in [frappe.session.user, *participants]:
		if not user or user in seen or not frappe.db.exists("User", user):
			continue
		if frappe.db.get_value("User", user, "enabled") == 0:
			continue
		seen.add(user)
		doc.append(
			"event_participants",
			{"reference_doctype": "User", "reference_docname": user, "email": user},
		)

	doc.insert(ignore_permissions=True)
	return {"name": doc.name, "subject": doc.subject, "starts_on": str(doc.starts_on)}


@frappe.whitelist()
def get_team_users():
	"""Active system users for the Schedule Session dialog."""
	return frappe.get_all(
		"User",
		filters={"enabled": 1, "user_type": "System User", "name": ["not in", ["Guest", "Administrator"]]},
		fields=["name", "full_name", "user_image"],
		order_by="full_name asc",
		limit_page_length=200,
	)


def repair_participant_emails():
	"""One-shot fix for existing Events with blank participant emails."""
	events = frappe.get_all("Event", pluck="name")
	fixed = 0
	for name in events:
		doc = frappe.get_doc("Event", name)
		before = [(r.idx, r.email) for r in doc.event_participants]
		_sync_participant_emails(doc)
		after = [(r.idx, r.email) for r in doc.event_participants]
		if before != after:
			doc.flags.ignore_permissions = True
			doc.save()
			fixed += 1
		else:
			_share_with_participants(doc)
	return fixed
