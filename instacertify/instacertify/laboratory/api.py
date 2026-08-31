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
	"""User-facing option: Lab · location · buy · sell · test · standard (unique)."""
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
	std = (row.applicable_standard or "").strip() or "—"
	# Include standard so two scopes with same prices stay distinguishable
	return f"{title} · {loc} · Buy {buy} · Sell {sell} · {test} · {std}"


OTHER_OPTION = "Other"


def _normalize_standard(value: str | None) -> str:
	return " ".join((value or "").strip().split()).casefold()


def _is_other(value: str | None) -> bool:
	return _normalize_standard(value) == _normalize_standard(OTHER_OPTION)


def _append_other(options: list[dict]) -> list[dict]:
	"""Ensure a selectable Other option for free / unlisted values."""
	if not any(_is_other(o.get("value")) for o in options):
		options.append(
			{
				"value": OTHER_OPTION,
				"label": OTHER_OPTION,
				"lab_count": 0,
				"labs": [],
				"lab_names": "",
				"is_other": 1,
			}
		)
	return options


def _match_test(row_test: str, test_key: str) -> bool:
	if not test_key:
		return True
	if _is_other(test_key):
		return True
	return test_key in row_test or row_test in test_key


def _match_standard(row_std: str, standard_key: str, *, exact: bool = False) -> bool:
	if not standard_key:
		return True
	if _is_other(standard_key):
		return True
	if row_std == standard_key:
		return True
	if exact:
		return False
	return standard_key in row_std or row_std in standard_key


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
def get_standard_options(txt: str | None = None, test_name: str | None = None):
	"""Distinct applicable standards from Active lab libraries (for autocomplete).

	When test_name is set, delegates to get_standards_for_test so Test and
	Standard stay interrelated. Always includes Other.
	"""
	if (test_name or "").strip():
		return get_standards_for_test(test_name=test_name, txt=txt)
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
	return _append_other([{"value": v, "label": v} for v in values])


@frappe.whitelist()
def get_test_name_options(txt: str | None = None, applicable_standard: str | None = None):
	"""Distinct test names from Active lab libraries (for autocomplete).

	When applicable_standard is set (and not Other), only tests that offer that
	standard are returned. Always includes Other for unlisted / custom tests.
	"""
	needle = _normalize_standard(txt)
	standard_key = _normalize_standard(applicable_standard) if applicable_standard else ""
	if _is_other(applicable_standard):
		standard_key = ""
	seen = {}
	for _lab, row in _iter_active_lab_scopes():
		name = (row.test_name or "").strip()
		if not name:
			continue
		if standard_key:
			row_std = _normalize_standard(row.applicable_standard)
			if not _match_standard(row_std, standard_key, exact=True):
				continue
		key = _normalize_standard(name)
		if needle and needle not in key:
			continue
		seen.setdefault(key, name)
	values = sorted(seen.values(), key=lambda s: s.casefold())
	return _append_other([{"value": v, "label": v} for v in values])


@frappe.whitelist()
def get_standards_for_test(test_name: str | None = None, txt: str | None = None):
	"""Applicable standards related to a selected test name (from Active labs).

	One test can map to multiple standards across multiple labs. Each option
	includes the lab names that carry that standard for the test. Always ends
	with Other for unlisted / custom standards.
	"""
	test_key = _normalize_standard(test_name)
	# No test yet → all standards (+ Other) so fields stay interrelated either way
	needle = _normalize_standard(txt)
	seen = {}
	labs_by_std: dict[str, dict[str, str]] = {}
	for lab, row in _iter_active_lab_scopes():
		row_test = _normalize_standard(row.test_name)
		if test_key and not _is_other(test_name):
			# Exact test name — dropdown selection is a concrete library value
			if row_test != test_key:
				continue
		std = (row.applicable_standard or "").strip()
		if not std:
			continue
		key = _normalize_standard(std)
		if needle and needle not in key:
			continue
		seen.setdefault(key, std)
		labs_by_std.setdefault(key, {})
		lab_id = lab.name
		labs_by_std[key][lab_id] = lab.get("laboratory_name") or lab.name

	values = sorted(seen.values(), key=lambda s: s.casefold())
	out = []
	for v in values:
		key = _normalize_standard(v)
		lab_map = labs_by_std.get(key) or {}
		lab_list = [{"name": n, "laboratory_name": title} for n, title in sorted(lab_map.items(), key=lambda x: x[1].casefold())]
		out.append(
			{
				"value": v,
				"label": v,
				"lab_count": len(lab_list),
				"labs": lab_list,
				"lab_names": ", ".join(x["laboratory_name"] for x in lab_list),
				"is_other": 0,
			}
		)
	return _append_other(out)


@frappe.whitelist()
def get_test_names_for_standard(applicable_standard: str | None = None, txt: str | None = None):
	"""Test names related to a selected applicable standard (mirror of standards-for-test)."""
	return get_test_name_options(txt=txt, applicable_standard=applicable_standard)


@frappe.whitelist()
def get_labs_for_standard(applicable_standard: str | None = None, test_name: str | None = None):
	"""Labs that offer the standard and/or test, with buying & selling rates.

	Either filter may be provided. When both are set (and neither is Other),
	results must match both. Other means “no filter on that side”.
	Same standard/test can appear under multiple labs at different prices.
	Includes phone and address for lab selection UIs.
	"""
	standard_raw = (applicable_standard or "").strip()
	test_raw = (test_name or "").strip()
	standard_key = "" if _is_other(standard_raw) else _normalize_standard(standard_raw)
	test_key = "" if _is_other(test_raw) else _normalize_standard(test_raw)
	if not standard_key and not test_key and not (standard_raw or test_raw):
		return []
	# Selecting Other alone with no counterpart → show nothing useful; require at least one real filter
	# or Other+Other still empty. If only Other on one side with empty other, return [].
	if not standard_key and not test_key:
		return []

	offers = []
	for lab, row in _iter_active_lab_scopes():
		if standard_key:
			row_std = _normalize_standard(row.applicable_standard)
			# Exact standard match — user picked a specific library standard
			if not _match_standard(row_std, standard_key, exact=True):
				continue
		if test_key:
			row_test = _normalize_standard(row.test_name)
			# Exact test when a concrete standard is selected (avoid Safety Test ≈ Safety Testing)
			if standard_key:
				if row_test != test_key:
					continue
			elif not _match_test(row_test, test_key):
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
