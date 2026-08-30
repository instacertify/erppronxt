# Copyright (c) Instacertify
"""Customer Test Request Form (TRF) portal."""

from __future__ import annotations

import frappe

no_cache = 1


def get_context(context):
	context.token = frappe.form_dict.get("name") or frappe.form_dict.get("token")
	context.csrf_token = frappe.sessions.get_csrf_token()
	frappe.db.commit()
	context.no_cache = 1
