# Copyright (c) Instacertify
"""Latest Raven message for the desk popup. Read-only."""

from __future__ import annotations

import re

import frappe


def _plain(value) -> str:
	text = str(value or "")
	text = re.sub(r"<[^>]+>", " ", text)
	text = re.sub(r"\s+", " ", text).strip()
	return text[:180]


@frappe.whitelist()
def peek():
	"""Unread chat for the signed-in person, used by the small desk window."""
	if "raven" not in frappe.get_installed_apps():
		return {"enabled": 0}
	user = frappe.session.user
	if not user or user == "Guest":
		return {"enabled": 0}
	if not frappe.db.exists("Raven User", {"user": user, "enabled": 1}):
		return {"enabled": 0}

	rows = frappe.db.sql(
		"""
		SELECT m.name, m.text, m.content, m.message_type, m.owner, m.creation,
			m.channel_id, c.channel_name, c.is_direct_message
		FROM `tabRaven Message` m
		INNER JOIN `tabRaven Channel Member` mem
			ON mem.channel_id = m.channel_id AND mem.user_id = %(user)s
		INNER JOIN `tabRaven Channel` c ON c.name = m.channel_id
		WHERE IFNULL(c.is_archived, 0) = 0
			AND IFNULL(c.is_thread, 0) = 0
			AND m.message_type != 'System'
			AND m.owner != %(user)s
			AND m.creation > IFNULL(mem.last_visit, '2000-01-01')
		ORDER BY m.creation DESC
		LIMIT 1
		""",
		{"user": user},
		as_dict=True,
	)
	unread = frappe.db.sql(
		"""
		SELECT COUNT(*) AS n
		FROM `tabRaven Message` m
		INNER JOIN `tabRaven Channel Member` mem
			ON mem.channel_id = m.channel_id AND mem.user_id = %(user)s
		INNER JOIN `tabRaven Channel` c ON c.name = m.channel_id
		WHERE IFNULL(c.is_archived, 0) = 0
			AND IFNULL(c.is_thread, 0) = 0
			AND m.message_type != 'System'
			AND m.owner != %(user)s
			AND m.creation > IFNULL(mem.last_visit, '2000-01-01')
		""",
		{"user": user},
		as_dict=True,
	)
	count = int((unread[0] or {}).get("n") or 0) if unread else 0
	message = None
	if rows:
		row = rows[0]
		kind = row.message_type or "Text"
		if kind == "Image":
			preview = "Sent a photo"
		elif kind == "File":
			preview = "Sent a file"
		elif kind == "Poll":
			preview = "Sent a poll"
		else:
			preview = _plain(row.text) or _plain(row.content) or "New message"
		sender = frappe.db.get_value("User", row.owner, "full_name") or row.owner
		where = sender if row.is_direct_message else (row.channel_name or "Chat")
		message = {
			"id": row.name,
			"preview": preview,
			"sender": sender,
			"where": where,
			"channel_id": row.channel_id,
		}
	return {"enabled": 1, "unread": count, "message": message}
