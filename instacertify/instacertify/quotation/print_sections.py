# Copyright (c) Instacertify
"""Quotation print-section visibility toggles."""

from __future__ import annotations

from typing import Any

# Template fieldname → (Quotation custom field, label)
# Default is ON (1). Uncheck to hide on Print/PDF.
QUOTE_PRINT_SECTIONS: list[tuple[str, str, str]] = [
	("show_about", "ic_show_about", "About / Narrative"),
	("show_applicable_standards", "ic_show_applicable_standards", "Applicable Standards"),
	("show_process", "ic_show_process", "Process Steps"),
	("show_validity", "ic_show_validity", "Validity"),
	("show_sample_required", "ic_show_sample_required", "Sample Required"),
	("show_documents_required", "ic_show_documents_required", "Documents Required"),
	("show_timelines", "ic_show_timelines", "Timelines"),
	("show_deliverables", "ic_show_deliverables", "Deliverables"),
	("show_commercials", "ic_show_commercials", "Commercials"),
	("show_payment_terms", "ic_show_payment_terms", "Payment Terms"),
	("show_banking", "ic_show_banking", "Banking Details"),
	("show_cancellation", "ic_show_cancellation", "Cancellation & Refund"),
	("show_force_majeure", "ic_show_force_majeure", "Force Majeure"),
	("show_confidentiality", "ic_show_confidentiality", "Confidentiality"),
	("show_terms", "ic_show_terms", "Terms and Conditions"),
	("show_sample_handling", "ic_show_sample_handling", "Sample Handling Policy"),
]


def quote_section_on(doc=None, fieldname: str = "") -> bool:
	"""True unless the section checkbox is explicitly unchecked (0).

	Used from print Jinja: {% if quote_section_on(doc, 'ic_show_sample_required') %}
	"""
	if not fieldname:
		return True
	if not doc:
		return True
	try:
		val = doc.get(fieldname)
	except Exception:
		val = getattr(doc, fieldname, None)
	if val in (0, "0", False):
		return False
	return True


def template_show_defaults(tmpl=None) -> dict[str, Any]:
	"""Map template show_* checks → quotation ic_show_* (default 1)."""
	out = {}
	for tmpl_key, quote_key, _label in QUOTE_PRINT_SECTIONS:
		val = 1
		if tmpl is not None:
			try:
				raw = tmpl.get(tmpl_key)
			except Exception:
				raw = getattr(tmpl, tmpl_key, None)
			if raw in (0, "0", False):
				val = 0
			elif raw in (1, "1", True):
				val = 1
			elif raw is None:
				val = 1
		out[quote_key] = val
	return out
