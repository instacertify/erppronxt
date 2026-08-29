# Copyright (c) Instacertify
"""Task multi-assignee sync."""

from __future__ import annotations


def validate_task(doc, method=None):
	from instacertify.team.assignees import sync_assignees

	sync_assignees(
		doc,
		table_field="ic_assignees",
		primary_field="ic_primary_assignee",
		default_user=doc.get("completed_by") or doc.owner,
	)


def on_update_task(doc, method=None):
	from instacertify.team.assignees import get_assignee_users, sync_frappe_assignments

	if doc.has_value_changed("ic_assignees") or doc.has_value_changed("ic_primary_assignee"):
		sync_frappe_assignments(doc, get_assignee_users(doc, primary_field="ic_primary_assignee"))
