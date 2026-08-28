# Copyright (c) Instacertify
"""Test report customer portal."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import strip_html

no_cache = 1


def get_context(context):
	context.token = frappe.form_dict.get("name") or frappe.form_dict.get("token")
	context.no_cache = 1
	context.no_header = 1
	context.no_footer = 1


@frappe.whitelist(allow_guest=True)
def get_report(token: str):
	name = frappe.db.get_value("IC Testing Request", {"share_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid report link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Testing Request", name)
	status = doc.status or ""
	if status != "Report Shared with Customer":
		frappe.throw(_("This report is not shared with the customer yet"), frappe.PermissionError)
	return {
		"title": strip_html(doc.title or "") or "Test Report",
		"product": strip_html(doc.product or ""),
		"test_name": strip_html(doc.test_name or ""),
		"status": status,
		"test_report": doc.test_report,
		"report_shared_on": str(doc.report_shared_on or ""),
		"portal_notice": _(
			"Download your report here. This link does not provide access to Instacertify ERP."
		),
	}
