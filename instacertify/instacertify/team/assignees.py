# Copyright (c) Instacertify
"""Multi-person assignment helpers for Quotation, Testing, Task, and Project."""

from __future__ import annotations

import frappe


def sync_assignees(
	doc,
	*,
	table_field: str = "ic_assignees",
	primary_field: str | None = None,
	legacy_seed_field: str | None = None,
	default_user: str | None = None,
):
	"""Normalize assignee rows: unique users, one Primary, optional primary Link mirror.

	Also seeds the table from a legacy single Link field (or default_user) when empty.
	"""
	meta = doc.meta
	if not meta.has_field(table_field):
		return

	members = []
	seen = set()
	for row in doc.get(table_field) or []:
		user = row.get("user")
		if not user or user in seen:
			continue
		seen.add(user)
		full_name = row.get("full_name") or frappe.db.get_value("User", user, "full_name") or user
		role = row.get("role") or "Member"
		members.append({"user": user, "full_name": full_name, "role": role})

	seed_user = None
	if not members:
		seed = legacy_seed_field or primary_field
		if seed and doc.get(seed):
			seed_user = doc.get(seed)
		elif default_user and default_user not in (None, "", "Guest"):
			seed_user = default_user
		if seed_user and frappe.db.exists("User", seed_user):
			full_name = frappe.db.get_value("User", seed_user, "full_name") or seed_user
			members = [{"user": seed_user, "full_name": full_name, "role": "Primary"}]

	if not members:
		if primary_field and meta.has_field(primary_field):
			doc.set(primary_field, None)
		return

	primaries = [m for m in members if m["role"] == "Primary"]
	if not primaries:
		members[0]["role"] = "Primary"
	elif len(primaries) > 1:
		seen_primary = False
		for m in members:
			if m["role"] == "Primary":
				if seen_primary:
					m["role"] = "Member"
				else:
					seen_primary = True

	doc.set(table_field, [])
	for m in members:
		doc.append(table_field, m)

	primary = next((m for m in members if m["role"] == "Primary"), members[0])
	if primary_field and meta.has_field(primary_field):
		doc.set(primary_field, primary["user"])


def append_assignees_from_users(doc, users: list[str], *, table_field: str = "ic_assignees"):
	"""Append users onto an assignee child table (skipping duplicates). First becomes Primary if empty."""
	if not doc.meta.has_field(table_field):
		return
	existing = {row.get("user") for row in (doc.get(table_field) or []) if row.get("user")}
	for user in users or []:
		if not user or user in existing or not frappe.db.exists("User", user):
			continue
		role = "Primary" if not existing else "Member"
		doc.append(
			table_field,
			{
				"user": user,
				"full_name": frappe.db.get_value("User", user, "full_name") or user,
				"role": role,
			},
		)
		existing.add(user)


def get_assignee_users(doc, table_field: str = "ic_assignees", primary_field: str | None = None) -> list[str]:
	"""Return unique User names assigned on a document."""
	users = []
	seen = set()
	if doc.meta.has_field(table_field):
		for row in doc.get(table_field) or []:
			user = row.get("user")
			if user and user not in seen:
				seen.add(user)
				users.append(user)
	if primary_field and doc.get(primary_field) and doc.get(primary_field) not in seen:
		users.append(doc.get(primary_field))
	# Project team table uses role_on_project
	if not users and doc.meta.has_field("ic_team_members"):
		for row in doc.get("ic_team_members") or []:
			user = row.get("user")
			if user and user not in seen:
				seen.add(user)
				users.append(user)
	if not users and doc.get("owner") and doc.owner not in ("Guest", "Administrator"):
		users.append(doc.owner)
	return users


def sync_frappe_assignments(doc, users: list[str] | None = None):
	"""Mirror assignees onto Frappe Assign To (ToDo / _assign) for Task workdesk."""
	users = users if users is not None else get_assignee_users(doc)
	if doc.is_new() or not users:
		return
	try:
		from frappe.desk.form import assign_to
	except Exception:
		return

	existing = set()
	try:
		import json

		raw = doc.get("_assign") or frappe.db.get_value(doc.doctype, doc.name, "_assign")
		if raw:
			existing = set(json.loads(raw) if isinstance(raw, str) else raw)
	except Exception:
		existing = set()

	for user in users:
		if user in existing:
			continue
		if not frappe.db.exists("User", user):
			continue
		try:
			assign_to.add(
				{
					"assign_to": [user],
					"doctype": doc.doctype,
					"name": doc.name,
					"description": f"Assigned on {doc.doctype}",
					"notify": 0,
				}
			)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "sync_frappe_assignments")
