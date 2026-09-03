# Copyright (c) Instacertify
"""Quotation print-section visibility, order, and form hide helpers."""

from __future__ import annotations

import json
from typing import Any

# Template fieldname → (Quotation custom field, short key, label)
# Default is ON (1). Uncheck to hide on Print/PDF and (optionally) form.
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

# Short keys used in ic_section_order JSON / print loop
SECTION_KEYS: list[str] = [
	"about",
	"applicable_standards",
	"process",
	"validity",
	"sample_required",
	"documents_required",
	"timelines",
	"deliverables",
	"commercials",
	"payment_terms",
	"banking",
	"cancellation",
	"force_majeure",
	"confidentiality",
	"terms",
	"sample_handling",
]

SECTION_META: dict[str, dict[str, Any]] = {
	"about": {
		"show_field": "ic_show_about",
		"label": "About / Narrative",
		"form_fields": ["ic_section_about", "ic_about_service", "ic_about_testing", "ic_scope_of_work"],
	},
	"applicable_standards": {
		"show_field": "ic_show_applicable_standards",
		"label": "Applicable Standards",
		"form_fields": ["ic_applicable_standard", "ic_standard_narrative", "ic_applicable_standards_text"],
	},
	"process": {
		"show_field": "ic_show_process",
		"label": "Process Steps",
		"form_fields": ["ic_process_steps"],
	},
	"validity": {
		"show_field": "ic_show_validity",
		"label": "Validity",
		"form_fields": ["ic_validity_text", "ic_validity_days"],
	},
	"sample_required": {
		"show_field": "ic_show_sample_required",
		"label": "Sample Required",
		"form_fields": ["ic_sample_required", "ic_samples_note"],
	},
	"documents_required": {
		"show_field": "ic_show_documents_required",
		"label": "Documents Required",
		"form_fields": ["ic_documents_required"],
	},
	"timelines": {
		"show_field": "ic_show_timelines",
		"label": "Timelines",
		"form_fields": ["ic_estimated_timeline", "ic_timeline_details", "ic_section_docs_timeline"],
	},
	"deliverables": {
		"show_field": "ic_show_deliverables",
		"label": "Deliverables",
		"form_fields": ["ic_deliverables", "ic_section_scope"],
	},
	"commercials": {
		"show_field": "ic_show_commercials",
		"label": "Commercials / Test Lines",
		"form_fields": [
			"ic_section_test_lines",
			"ic_test_items",
			"ic_section_costing",
			"ic_cost_items",
			"ic_section_cost_totals",
			"ic_commercial_value",
			"ic_passthrough_value",
			"ic_total_quoted_value",
			"ic_commercials_notes",
		],
	},
	"payment_terms": {
		"show_field": "ic_show_payment_terms",
		"label": "Payment Terms",
		"form_fields": ["ic_payment_terms", "ic_section_policies", "ic_bank_account"],
	},
	"banking": {
		"show_field": "ic_show_banking",
		"label": "Banking Details",
		"form_fields": ["ic_bank_account"],
	},
	"cancellation": {
		"show_field": "ic_show_cancellation",
		"label": "Cancellation & Refund",
		"form_fields": ["ic_cancellation_policy"],
	},
	"force_majeure": {
		"show_field": "ic_show_force_majeure",
		"label": "Force Majeure",
		"form_fields": ["ic_force_majeure", "ic_section_terms"],
	},
	"confidentiality": {
		"show_field": "ic_show_confidentiality",
		"label": "Confidentiality",
		"form_fields": ["ic_confidentiality"],
	},
	"terms": {
		"show_field": "ic_show_terms",
		"label": "Terms and Conditions",
		"form_fields": ["ic_terms_and_conditions"],
	},
	"sample_handling": {
		"show_field": "ic_show_sample_handling",
		"label": "Sample Handling Policy",
		"form_fields": ["ic_sample_handling_policy"],
	},
}

CONSULTING_DEFAULT_ORDER = [
	"about",
	"applicable_standards",
	"process",
	"validity",
	"commercials",
	"payment_terms",
	"timelines",
	"sample_required",
	"documents_required",
	"banking",
	"cancellation",
	"force_majeure",
	"confidentiality",
	"terms",
	"sample_handling",
	"deliverables",
]

TESTING_DEFAULT_ORDER = [
	"about",
	"applicable_standards",
	"sample_required",
	"commercials",
	"deliverables",
	"timelines",
	"payment_terms",
	"sample_handling",
	"banking",
	"cancellation",
	"force_majeure",
	"confidentiality",
	"terms",
	"process",
	"validity",
	"documents_required",
]


def section_key_from_show_field(show_field: str) -> str | None:
	for key, meta in SECTION_META.items():
		if meta["show_field"] == show_field:
			return key
	return None


def default_section_order(quotation_type: str | None = None) -> list[str]:
	t = (quotation_type or "").strip()
	if t in ("Testing", "Multiple Products / Multiple Services"):
		return list(TESTING_DEFAULT_ORDER)
	return list(CONSULTING_DEFAULT_ORDER)


def parse_section_order(raw: Any, quotation_type: str | None = None) -> list[str]:
	"""Parse stored order (JSON list or comma-separated) and merge missing keys."""
	base = default_section_order(quotation_type)
	parsed: list[str] = []
	if raw:
		try:
			if isinstance(raw, (list, tuple)):
				parsed = [str(x).strip() for x in raw if str(x).strip()]
			else:
				text = str(raw).strip()
				if text.startswith("["):
					parsed = [str(x).strip() for x in json.loads(text) if str(x).strip()]
				else:
					parsed = [p.strip() for p in text.split(",") if p.strip()]
		except Exception:
			parsed = []
	# Keep only known keys, preserve order, append any missing from default
	seen = set()
	out: list[str] = []
	for k in parsed:
		if k in SECTION_META and k not in seen:
			out.append(k)
			seen.add(k)
	for k in base:
		if k not in seen:
			out.append(k)
			seen.add(k)
	return out


def quote_section_order(doc=None) -> list[str]:
	"""Ordered section keys for Print/PDF Jinja loops.

	Usage: {% for _sk in quote_section_order(doc) %}
	"""
	qtype = None
	raw = None
	if doc is not None:
		try:
			qtype = doc.get("ic_quotation_type")
			raw = doc.get("ic_section_order")
		except Exception:
			qtype = getattr(doc, "ic_quotation_type", None)
			raw = getattr(doc, "ic_section_order", None)
	return parse_section_order(raw, qtype)


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


def section_catalog_for_client(quotation_type: str | None = None) -> list[dict[str, Any]]:
	"""Payload for Arrange Sections dialog."""
	order = default_section_order(quotation_type)
	rows = []
	for key in order:
		meta = SECTION_META[key]
		rows.append(
			{
				"key": key,
				"label": meta["label"],
				"show_field": meta["show_field"],
				"form_fields": list(meta.get("form_fields") or []),
			}
		)
	return rows


def quote_line_currency(row=None, doc=None) -> str:
	"""Currency for a quote line — row override, else quotation primary, else INR."""
	cur = None
	if row is not None:
		try:
			cur = row.get("currency") if hasattr(row, "get") else getattr(row, "currency", None)
		except Exception:
			cur = getattr(row, "currency", None)
	if not cur and doc is not None:
		try:
			cur = doc.get("currency") if hasattr(doc, "get") else getattr(doc, "currency", None)
		except Exception:
			cur = getattr(doc, "currency", None)
	cur = (str(cur).strip() if cur else "") or "INR"
	return cur


def quote_money(amount, currency=None, doc=None) -> str:
	"""Format an amount in the given (or document) currency for Print/PDF."""
	from frappe.utils import fmt_money

	cur = (currency or "").strip() if currency else ""
	if not cur:
		cur = quote_line_currency(None, doc)
	try:
		amt = float(amount or 0)
	except Exception:
		amt = 0.0
	if cur == "INR":
		try:
			return f"₹{amt:,.0f}/-"
		except Exception:
			pass
	try:
		return fmt_money(amt, currency=cur)
	except Exception:
		return f"{cur} {amt:,.2f}"


def quote_totals_by_currency(doc) -> list[dict[str, Any]]:
	"""Per-currency testing / commercials / combined totals for multi-currency quotes."""
	from collections import OrderedDict

	buckets: OrderedDict[str, dict[str, Any]] = OrderedDict()

	def bump(cur: str, *, testing: float = 0.0, cost: float = 0.0) -> None:
		cur = (cur or "INR").strip() or "INR"
		if cur not in buckets:
			buckets[cur] = {"currency": cur, "testing": 0.0, "cost": 0.0, "total": 0.0}
		buckets[cur]["testing"] += float(testing or 0)
		buckets[cur]["cost"] += float(cost or 0)
		buckets[cur]["total"] = buckets[cur]["testing"] + buckets[cur]["cost"]

	for row in (doc.get("ic_test_items") if doc else None) or []:
		units = float(row.get("number_of_samples") or 1) or 1.0
		per = row.get("suggested_selling_price")
		if per in (None, ""):
			per = row.get("per_unit_charges")
		total = row.get("testing_charges")
		if total in (None, ""):
			try:
				total = float(per or 0) * units
			except Exception:
				total = 0.0
		bump(quote_line_currency(row, doc), testing=float(total or 0))

	for row in (doc.get("ic_cost_items") if doc else None) or []:
		units = float(row.get("qty") or 1) or 1.0
		per = float(row.get("amount") or 0)
		total = row.get("total_amount")
		if total in (None, ""):
			total = per * units
		bump(quote_line_currency(row, doc), cost=float(total or 0))

	return list(buckets.values())
