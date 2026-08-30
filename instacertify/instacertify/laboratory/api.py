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


def _lab_offer_label(lab_name: str, lab_title: str, location: str, row) -> str:
	"""User-facing option: Lab · location · buy · sell · test."""
	currency = row.currency or "INR"
	try:
		buy = fmt_money(flt(row.purchase_price), currency=currency)
		sell = fmt_money(flt(row.selling_price), currency=currency)
	except Exception:
		buy = str(flt(row.purchase_price))
		sell = str(flt(row.selling_price))
	loc = (location or "").strip() or "—"
	title = (lab_title or lab_name or "").strip()
	test = (row.test_name or "").strip() or "Test"
	return f"{title} · {loc} · Buy {buy} · Sell {sell} · {test}"


def _normalize_standard(value: str | None) -> str:
	return " ".join((value or "").strip().split()).casefold()


def _active_scopes(laboratory: str):
	if not laboratory or not frappe.db.exists("IC Laboratory", laboratory):
		return []
	lab = frappe.get_doc("IC Laboratory", laboratory)
	return [row for row in (lab.test_scopes or []) if cint_active(row)]


def cint_active(row) -> bool:
	return int(getattr(row, "is_active", 1) or 0) == 1


def _iter_active_lab_scopes():
	"""Yield (lab dict, scope_row) for Active labs with active scopes."""
	lab_fields = [
		"name",
		"laboratory_name",
		"location",
		"city",
		"state",
		"country",
		"address",
		"phone",
		"email",
		"contact_person",
		"accreditation_details",
		"accreditation_scope",
	]
	if frappe.db.has_column("IC Laboratory", "contact_designation"):
		lab_fields.append("contact_designation")
	labs = frappe.get_all(
		"IC Laboratory",
		filters={"status": "Active"},
		fields=lab_fields,
		order_by="laboratory_name asc",
	)
	for lab in labs:
		doc = frappe.get_doc("IC Laboratory", lab.name)
		for row in doc.test_scopes or []:
			if not cint_active(row):
				continue
			if not (row.applicable_standard or "").strip() and not (row.test_name or "").strip():
				continue
			yield lab, row


def _lab_address_line(lab) -> str:
	parts = [
		(lab.get("address") or "").strip(),
		(lab.get("city") or "").strip(),
		(lab.get("state") or "").strip(),
		(lab.get("location") or "").strip(),
		(lab.get("country") or "").strip(),
	]
	# Dedupe while preserving order
	seen = set()
	out = []
	for p in parts:
		key = p.casefold()
		if not p or key in seen:
			continue
		seen.add(key)
		out.append(p)
	return ", ".join(out)


def _offer_dict(lab, row) -> dict:
	location = lab.get("location") or lab.get("city") or ""
	label = _lab_offer_label(lab.name, lab.get("laboratory_name"), location, row)
	return {
		"value": label,
		"label": label,
		"laboratory": lab.name,
		"laboratory_name": lab.get("laboratory_name") or lab.name,
		"location": location,
		"address": _lab_address_line(lab),
		"phone": (lab.get("phone") or "").strip(),
		"email": (lab.get("email") or "").strip(),
		"contact_person": (lab.get("contact_person") or "").strip(),
		"contact_designation": (lab.get("contact_designation") or "").strip(),
		"accreditation_details": (lab.get("accreditation_details") or "").strip(),
		"accreditation_scope": (lab.get("accreditation_scope") or "").strip(),
		"scope_row": row.name,
		"test_name": row.test_name,
		"applicable_standard": row.applicable_standard,
		"category": row.category,
		"selling_price": flt(row.selling_price),
		"purchase_price": flt(row.purchase_price),
		"currency": row.currency or "INR",
		"scope_label": _scope_label(row),
	}


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
def get_standard_options(txt: str | None = None):
	"""Distinct applicable standards from Active lab libraries (for autocomplete)."""
	needle = _normalize_standard(txt)
	seen = {}
	for _lab, row in _iter_active_lab_scopes():
		std = (row.applicable_standard or "").strip()
		if not std:
			continue
		key = _normalize_standard(std)
		if needle and needle not in key:
			continue
		seen.setdefault(key, std)
	values = sorted(seen.values(), key=lambda s: s.casefold())
	return [{"value": v, "label": v} for v in values]


@frappe.whitelist()
def get_test_name_options(txt: str | None = None):
	"""Distinct test names from Active lab libraries (for autocomplete)."""
	needle = _normalize_standard(txt)
	seen = {}
	for _lab, row in _iter_active_lab_scopes():
		name = (row.test_name or "").strip()
		if not name:
			continue
		key = _normalize_standard(name)
		if needle and needle not in key:
			continue
		seen.setdefault(key, name)
	values = sorted(seen.values(), key=lambda s: s.casefold())
	return [{"value": v, "label": v} for v in values]


@frappe.whitelist()
def get_standards_for_test(test_name: str | None = None, txt: str | None = None):
	"""Applicable standards suggested for a selected test name (from Active labs)."""
	test_key = _normalize_standard(test_name)
	if not test_key:
		return []
	needle = _normalize_standard(txt)
	seen = {}
	lab_counts = {}
	for _lab, row in _iter_active_lab_scopes():
		row_test = _normalize_standard(row.test_name)
		if test_key not in row_test and row_test not in test_key:
			continue
		std = (row.applicable_standard or "").strip()
		if not std:
			continue
		key = _normalize_standard(std)
		if needle and needle not in key:
			continue
		seen.setdefault(key, std)
		lab_counts[key] = lab_counts.get(key, 0) + 1
	values = sorted(seen.values(), key=lambda s: s.casefold())
	return [
		{
			"value": v,
			"label": v,
			"lab_count": lab_counts.get(_normalize_standard(v), 0),
		}
		for v in values
	]


@frappe.whitelist()
def get_labs_for_standard(applicable_standard: str | None = None, test_name: str | None = None):
	"""Labs that offer the standard and/or test, with buying & selling rates.

	Either filter may be provided. When both are set, results must match both.
	Same standard/test can appear under multiple labs at different prices.
	Includes phone and address for lab selection UIs.
	"""
	standard_key = _normalize_standard(applicable_standard)
	test_key = _normalize_standard(test_name) if test_name else ""
	if not standard_key and not test_key:
		return []

	offers = []
	for lab, row in _iter_active_lab_scopes():
		if standard_key:
			row_std = _normalize_standard(row.applicable_standard)
			if row_std != standard_key and standard_key not in row_std and row_std not in standard_key:
				continue
		if test_key:
			row_test = _normalize_standard(row.test_name)
			if test_key not in row_test and row_test not in test_key:
				continue
		offers.append(_offer_dict(lab, row))

	offers.sort(
		key=lambda o: (
			flt(o["purchase_price"]),
			flt(o["selling_price"]),
			(o["laboratory_name"] or "").casefold(),
		)
	)
	return offers


@frappe.whitelist()
def get_labs_for_test_or_standard(
	applicable_standard: str | None = None,
	test_name: str | None = None,
):
	"""Alias used by Testing Request UI — same as get_labs_for_standard."""
	return get_labs_for_standard(applicable_standard=applicable_standard, test_name=test_name)


@frappe.whitelist()
def get_lab_offer_details(
	lab_offer: str | None = None,
	applicable_standard: str | None = None,
	test_name: str | None = None,
	laboratory: str | None = None,
	scope_row: str | None = None,
):
	"""Resolve a selected multi-lab offer label back to lab + scope + prices."""
	offers = get_labs_for_standard(
		applicable_standard=applicable_standard or None,
		test_name=test_name or None,
	)
	if not offers:
		offers = [_offer_dict(lab, row) for lab, row in _iter_active_lab_scopes()]

	match = None
	if scope_row:
		match = next((o for o in offers if o.get("scope_row") == scope_row), None)
	if not match and laboratory and lab_offer:
		match = next(
			(o for o in offers if o.get("laboratory") == laboratory and o.get("value") == lab_offer),
			None,
		)
	if not match and lab_offer:
		match = next((o for o in offers if o.get("value") == lab_offer), None)
	if not match and laboratory:
		cands = [o for o in offers if o.get("laboratory") == laboratory]
		match = cands[0] if cands else None
	return match


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
