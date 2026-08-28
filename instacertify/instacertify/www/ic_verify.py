# Copyright (c) Instacertify
"""Public verification page for QR codes — allowlisted DocTypes only."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import strip_html

no_cache = 1

# Customer-facing verify only — no HR / internal Project browse
ALLOWED_VERIFY_DOCTYPES = {
	"Quotation",
	"Sales Invoice",
	"IC Sample Tracking",
	"IC Testing Request",
	"IC Document Request",
	"IC Sample Dispatch Collection",
}

FRIENDLY_TYPE = {
	"Quotation": "Quotation",
	"Sales Invoice": "Tax Invoice",
	"IC Sample Tracking": "Sample",
	"IC Testing Request": "Testing Request",
	"IC Document Request": "Documents Collection Sheet",
	"IC Sample Dispatch Collection": "Sample Dispatch Collection",
}


def get_context(context):
	doctype = frappe.form_dict.get("doctype")
	name = frappe.form_dict.get("name")
	context.doctype = FRIENDLY_TYPE.get(doctype, doctype)
	context.docname = None
	context.valid = False
	context.details = {}
	context.error = None
	context.no_header = 1
	context.no_footer = 1

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
	title = (
		doc.get("title")
		or doc.get("customer_name")
		or doc.get("tracking_number")
		or doc.get("subject")
		or doc.name
	)
	context.details = {
		"title": strip_html(str(title or "")),
		"status": strip_html(
			str(doc.get("status") or doc.get("ic_workflow_status") or doc.get("ic_project_stage") or "")
		),
		"modified": str(doc.modified),
	}
	context.no_cache = 1
