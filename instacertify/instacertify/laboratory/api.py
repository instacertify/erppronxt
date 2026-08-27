# Copyright (c) Instacertify
"""Laboratory library APIs — accreditation scope & testing pricing."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, fmt_money


def _scope_label(row) -> str:
	currency = row.currency or "INR"
	try:
		price = fmt_money(flt(row.selling_price), currency=currency)
	except Exception:
		price = str(flt(row.selling_price))
	standard = row.applicable_standard or "—"
	return f"{row.test_name} | {standard} | {price}"


def _active_scopes(laboratory: str):
	if not laboratory or not frappe.db.exists("IC Laboratory", laboratory):
		return []
	lab = frappe.get_doc("IC Laboratory", laboratory)
	return [row for row in (lab.test_scopes or []) if cint_active(row)]


def cint_active(row) -> bool:
	return int(getattr(row, "is_active", 1) or 0) == 1


@frappe.whitelist()
def get_lab_test_scope_options(laboratory: str):
	"""Autocomplete options for lab accreditation scope / test pricing."""
	options = []
	for row in _active_scopes(laboratory):
		label = _scope_label(row)
		options.append(
			{
				"value": label,
				"label": label,
				"name": row.name,
				"test_name": row.test_name,
				"applicable_standard": row.applicable_standard,
				"selling_price": flt(row.selling_price),
				"purchase_price": flt(row.purchase_price),
				"currency": row.currency or "INR",
				"category": row.category,
			}
		)
	return options


@frappe.whitelist()
def get_lab_test_scope_details(laboratory: str, scope_key: str = None, scope_row: str = None):
	"""Resolve a selected scope option into test + suggested selling price."""
	if not laboratory:
		return None

	scopes = _active_scopes(laboratory)
	match = None
	if scope_row:
		match = next((r for r in scopes if r.name == scope_row), None)
	if not match and scope_key:
		for row in scopes:
			if _scope_label(row) == scope_key or row.test_name == scope_key:
				match = row
				break
	if not match:
		return None

	return {
		"name": match.name,
		"test_name": match.test_name,
		"applicable_standard": match.applicable_standard,
		"category": match.category,
		"selling_price": flt(match.selling_price),
		"purchase_price": flt(match.purchase_price),
		"currency": match.currency or "INR",
		"label": _scope_label(match),
	}


@frappe.whitelist()
def get_laboratory_summary(laboratory: str):
	"""Location + short accreditation blurb for quotation / testing rows."""
	if not laboratory or not frappe.db.exists("IC Laboratory", laboratory):
		return {}
	lab = frappe.get_doc("IC Laboratory", laboratory)
	details = frappe.utils.strip_html(lab.accreditation_details or "")[:400]
	scope = frappe.utils.strip_html(lab.accreditation_scope or "")[:400]
	return {
		"name": lab.name,
		"laboratory_name": lab.laboratory_name,
		"location": lab.location,
		"status": lab.status,
		"accreditation_summary": details or scope,
		"active_scope_count": len(_active_scopes(laboratory)),
	}
