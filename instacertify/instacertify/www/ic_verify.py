# Copyright (c) Instacertify
"""Public verification page for QR codes — allowlisted DocTypes only."""

from __future__ import annotations

import frappe
from frappe import _

no_cache = 1

ALLOWED_VERIFY_DOCTYPES = {
	"Quotation",
	"Sales Invoice",
	"IC Sample Tracking",
	"IC Testing Request",
	"IC Joining Letter",
	"IC Document Request",
	"Project",
}


def get_context(context):
	doctype = frappe.form_dict.get("doctype")
	name = frappe.form_dict.get("name")
	context.doctype = doctype
	context.docname = name
	context.valid = False
	context.details = {}
	context.error = None

	if not doctype or not name:
		context.error = _("Missing document reference")
		context.no_cache = 1
		return

	if doctype not in ALLOWED_VERIFY_DOCTYPES:
		context.error = _("This document type cannot be verified publicly")
		context.no_cache = 1
		return

	if not frappe.db.exists(doctype, name):
		context.error = _("Document not found")
		context.no_cache = 1
		return

	doc = frappe.get_doc(doctype, name)
	context.valid = True
	context.details = {
		"name": doc.name,
		"title": doc.get("title")
		or doc.get("project_name")
		or doc.get("customer_name")
		or doc.get("employee_name")
		or doc.get("tracking_number")
		or doc.get("subject")
		or doc.name,
		"status": doc.get("status") or doc.get("ic_workflow_status") or doc.get("ic_project_stage") or "",
		"modified": str(doc.modified),
	}
	context.no_cache = 1
