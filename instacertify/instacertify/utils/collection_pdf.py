# Copyright (c) Instacertify
"""Guest PDF download for customer data-collection sheets."""

from __future__ import annotations

import frappe
from frappe import _


COLLECTION_PRINT_FORMATS = {
	"IC Document Request": "Instacertify Documents Collection Sheet",
	"IC Sample Dispatch Collection": "Instacertify Sample Dispatch Collection",
	"IC Test Request Form": "Instacertify Test Request Form",
}


def pdf_bytes_for_doc(doctype: str, name: str, print_format: str | None = None) -> bytes:
	"""Render Instacertify print format → PDF (elevates Guest for print perms)."""
	from instacertify.utils.pdf import make_pdf

	fmt = print_format or COLLECTION_PRINT_FORMATS.get(doctype)
	if not fmt or not frappe.db.exists("Print Format", fmt):
		frappe.throw(_("Print format not available for {0}").format(doctype))

	prev = frappe.session.user
	elevated = prev == "Guest"
	try:
		if elevated:
			frappe.set_user("Administrator")
		html = frappe.get_print(doctype, name, print_format=fmt, no_letterhead=1)
		return make_pdf(html)
	finally:
		if elevated:
			frappe.set_user(prev)


def respond_pdf(filename: str, pdf: bytes):
	safe = (filename or "collection").replace("/", "-").replace(" ", "-")
	if not safe.lower().endswith(".pdf"):
		safe = f"{safe}.pdf"
	frappe.local.response.filename = safe
	frappe.local.response.filecontent = pdf
	frappe.local.response.type = "pdf"


def download_by_share_token(
	doctype: str,
	token: str,
	*,
	token_field: str = "share_token",
	print_format: str | None = None,
	filename_prefix: str | None = None,
):
	"""Resolve share token → PDF download response."""
	if not token:
		frappe.throw(_("Invalid link"), frappe.PermissionError)
	name = frappe.db.get_value(doctype, {token_field: token}, "name")
	if not name:
		frappe.throw(_("Invalid link"), frappe.PermissionError)
	try:
		pdf = pdf_bytes_for_doc(doctype, name, print_format=print_format)
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"Portal PDF {doctype}")
		frappe.throw(
			_("PDF could not be generated right now. Please try again or contact Instacertify."),
			title=_("PDF generation failed"),
		)
	prefix = filename_prefix or doctype.replace(" ", "-")
	respond_pdf(f"{prefix}-{name}", pdf)
