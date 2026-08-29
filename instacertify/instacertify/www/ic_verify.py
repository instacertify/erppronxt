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
	"sample": "Sample",
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

	# Compact sample sticker QR: /ic-verify/sample/<tracking_number>
	path = (frappe.request.path if getattr(frappe, "request", None) else "") or ""
	if "/ic-verify/sample/" in path and not doctype:
		doctype = "sample"
		if not name:
			name = path.rstrip("/").rsplit("/", 1)[-1]

	# Route may pass tracking as `name` with doctype missing, or doctype=sample
	if (not doctype or str(doctype).lower() == "sample") and name:
		resolved = _resolve_sample(name)
		if resolved:
			doctype = "IC Sample Tracking"
			name = resolved
		elif str(doctype).lower() == "sample":
			context.error = _("Sample not found for tracking number {0}").format(name)
			context.no_cache = 1
			return

	if not doctype or not name:
		context.error = _("Missing document reference")
		context.no_cache = 1
		return

	if doctype not in ALLOWED_VERIFY_DOCTYPES:
		context.error = _("This document type cannot be verified publicly")
		context.no_cache = 1
		return

	# Allow lookup by sample tracking number as well as document name
	if doctype == "IC Sample Tracking" and not frappe.db.exists(doctype, name):
		resolved = _resolve_sample(name)
		if resolved:
			name = resolved

	if not frappe.db.exists(doctype, name):
		context.error = _("Document not found")
		context.no_cache = 1
		return

	doc = frappe.get_doc(doctype, name)
	context.valid = True
	context.docname = doc.name
	title = (
		doc.get("tracking_number")
		or doc.get("title")
		or doc.get("customer_name")
		or doc.get("subject")
		or doc.name
	)
	context.details = {
		"title": strip_html(str(title or "")),
		"status": strip_html(
			str(doc.get("status") or doc.get("ic_workflow_status") or doc.get("ic_project_stage") or "")
		),
		"tracking_number": strip_html(str(doc.get("tracking_number") or "")),
		"customer": strip_html(str(doc.get("customer") or doc.get("customer_name") or "")),
		"modified": str(doc.modified),
	}
	context.doctype = FRIENDLY_TYPE.get(doctype, doctype)
	context.no_cache = 1


def _resolve_sample(token: str) -> str | None:
	"""Resolve sample docname from tracking number or doc name."""
	token = (token or "").strip()
	if not token:
		return None
	if frappe.db.exists("IC Sample Tracking", token):
		return token
	return frappe.db.get_value("IC Sample Tracking", {"tracking_number": token}, "name")
