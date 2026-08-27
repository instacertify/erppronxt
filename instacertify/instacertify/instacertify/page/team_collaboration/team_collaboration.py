# Copyright (c) Instacertify
"""Team Collaboration desk page."""

import frappe


@frappe.whitelist()
def get_bootstrap(project: str | None = None):
	from instacertify.collaboration.api import get_project_messages, list_chat_rooms

	rooms = list_chat_rooms(limit=40)
	messages = None
	if project:
		messages = get_project_messages(project=project, limit=100)
	return {"rooms": rooms.get("rooms") or [], "messages": messages, "me": frappe.session.user}
