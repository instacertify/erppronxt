# Copyright (c) Instacertify
"""Test report customer portal."""

from __future__ import annotations

import frappe
from frappe import _

no_cache = 1


def get_context(context):
	context.token = frappe.form_dict.get("name") or frappe.form_dict.get("token")
	context.no_cache = 1


@frappe.whitelist(allow_guest=True)
def get_report(token: str):
	name = frappe.db.get_value("IC Testing Request", {"share_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid report link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Testing Request", name)
	return {
		"name": doc.name,
		"title": doc.title,
		"customer": doc.customer,
		"product": doc.product,
		"test_name": doc.test_name,
		"status": doc.status,
		"test_report": doc.test_report,
		"report_shared_on": doc.report_shared_on,
	}
