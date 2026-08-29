# Copyright (c) Instacertify
"""Customer contract portal."""

from __future__ import annotations

import frappe

no_cache = 1


def get_context(context):
	token = frappe.form_dict.get("name") or frappe.form_dict.get("token")
	context.token = token
	context.csrf_token = frappe.sessions.get_csrf_token()
	frappe.db.commit()
	context.no_cache = 1
	context.show_sidebar = False
	context.no_header = 1
	context.no_footer = 1
