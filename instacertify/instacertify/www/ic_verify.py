# Copyright (c) Instacertify
"""Public verification page for QR codes."""

from __future__ import annotations

import frappe
from frappe import _

no_cache = 1


def get_context(context):
	doctype = frappe.form_dict.get("doctype")
	name = frappe.form_dict.get("name")
	context.doctype = doctype
	context.docname = name
	context.valid = False
	context.details = {}
	if doctype and name and frappe.db.exists(doctype, name):
		context.valid = True
		meta_fields = ["name"]
		doc = frappe.get_doc(doctype, name)
		context.details = {
			"name": doc.name,
			"title": doc.get("title")
			or doc.get("project_name")
			or doc.get("customer_name")
			or doc.get("employee_name")
			or doc.get("tracking_number")
			or doc.name,
			"status": doc.get("status") or doc.get("ic_workflow_status") or doc.get("ic_project_stage") or "",
			"modified": str(doc.modified),
		}
	context.no_cache = 1
