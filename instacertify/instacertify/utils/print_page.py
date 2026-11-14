# Copyright (c) Instacertify
"""Keep the quotation print page from dying on a draft or a bad template.

The list “view / download quote” link opens /printview. Frappe then refuses a
draft when “Allow Print for Draft” is off, and a broken letter-head value of
the text “None” makes Get PDF fail. Quotations are printed before they are
submitted, so this page allows that and falls back to the plain format.
"""

from __future__ import annotations

import frappe

_BLANK = {"", "none", "null", "undefined"}


def clean_param(value):
	"""Turn missing and the literal text None/null into a real empty value."""
	if value is None:
		return None
	text = str(value).strip()
	if text.lower() in _BLANK:
		return None
	return value


def install_printview_guard():
	"""Wrap Frappe's print page once per process."""
	import frappe.www.printview as printview

	if getattr(printview.get_context, "_ic_guard", False):
		return

	original = printview.get_context

	def get_context(context):
		_select_quotation_format()
		try:
			result = original(context)
		except Exception as exc:
			if (frappe.form_dict.get("doctype") or "") != "Quotation":
				raise
			frappe.log_error(frappe.get_traceback(), "Quotation print view")
			try:
				result = _render_quotation(printview)
			except Exception:
				raise exc
		return _clean_context(result)

	get_context._ic_guard = True
	printview.get_context = get_context


def _select_quotation_format():
	"""Use the Instacertify format for this quote when the link did not name one."""
	if (frappe.form_dict.get("doctype") or "") != "Quotation":
		return
	if clean_param(frappe.form_dict.get("format")):
		frappe.form_dict.format = clean_param(frappe.form_dict.get("format"))
		return
	name = frappe.form_dict.get("name")
	if not name or not frappe.db.exists("Quotation", name):
		return
	from instacertify.utils.pdf import quotation_print_format

	fmt = quotation_print_format(frappe.get_doc("Quotation", name))
	if fmt:
		frappe.form_dict.format = fmt


def _render_quotation(printview):
	"""Print a quotation even when it is still a draft, then fall back to Standard."""
	name = frappe.form_dict.get("name")
	doc = frappe.get_doc("Quotation", name)
	meta = frappe.get_meta("Quotation")
	from instacertify.utils.pdf import quotation_print_format

	fmt_name = clean_param(frappe.form_dict.get("format")) or quotation_print_format(doc)
	settings = {"allow_print_for_draft": 1, "allow_print_for_cancelled": 1}
	last = None
	for fmt in (fmt_name, "Standard"):
		try:
			print_format = printview.get_print_format_doc(fmt, meta) if fmt else None
			body = printview.get_rendered_template(
				doc,
				print_format=print_format,
				meta=meta,
				trigger_print=frappe.form_dict.get("trigger_print"),
				no_letterhead=clean_param(frappe.form_dict.get("no_letterhead")),
				letterhead=clean_param(frappe.form_dict.get("letterhead")),
				settings=settings,
			)
			return _context(printview, doc, body, print_format)
		except Exception as exc:
			last = exc
	raise last


def _context(printview, doc, body, print_format):
	from frappe.utils.jinja_globals import is_rtl

	print_format_name = getattr(print_format, "name", "Standard")
	pdf_generator = getattr(print_format, "pdf_generator", "wkhtmltopdf")
	return {
		"body": body,
		"print_style": printview.get_print_style(frappe.form_dict.get("style"), print_format),
		"comment": frappe.session.user,
		"title": frappe.utils.strip_html(frappe.utils.cstr(doc.get_title() or doc.name)),
		"lang": frappe.local.lang,
		"layout_direction": "rtl" if is_rtl() else "ltr",
		"doctype": "Quotation",
		"name": doc.name,
		"key": clean_param(frappe.form_dict.get("key")) or "",
		"print_format": print_format_name,
		"letterhead": doc.get("letter_head") or "",
		"no_letterhead": clean_param(frappe.form_dict.get("no_letterhead")) or 0,
		"pdf_generator": frappe.form_dict.get("pdf_generator") or pdf_generator,
	}


def _clean_context(result):
	if not isinstance(result, dict):
		return result
	for key in ("letterhead", "key", "print_format"):
		if result.get(key) is None or str(result.get(key)).strip().lower() in _BLANK:
			result[key] = ""
	if result.get("no_letterhead") is None or str(result.get("no_letterhead")).strip().lower() in _BLANK:
		result["no_letterhead"] = 0
	return result
