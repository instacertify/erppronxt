# Copyright (c) Instacertify
"""Test report customer portal — link + 8-digit access code."""

from __future__ import annotations

import frappe
from frappe import _

no_cache = 1


def get_context(context):
	context.token = frappe.form_dict.get("name") or frappe.form_dict.get("token")
	context.no_cache = 1
	context.no_header = 1
	context.no_footer = 1


# Re-export guest APIs so /api/method/instacertify.www.ic_report.* keeps working
from instacertify.crm.report_share import get_report_gate, unlock_report  # noqa: E402,F401

# Back-compat for older clients that called get_report(token) without a code
@frappe.whitelist(allow_guest=True)
def get_report(token: str, access_code: str | None = None):
	"""Legacy endpoint: requires access_code to return the file."""
	from instacertify.crm.report_share import get_report_gate, unlock_report

	if not access_code:
		gate = get_report_gate(token)
		gate["unlocked"] = False
		return gate
	payload = unlock_report(token, access_code)
	payload["unlocked"] = True
	# shape expected by older HTML
	payload["test_report"] = payload.get("file_url")
	payload["name"] = ""
	payload["product"] = ""
	payload["test_name"] = ""
	payload["status"] = "Shared"
	return payload
