# Copyright (c) Instacertify
"""Document naming series — Quotation by type (Service / Testing / Others)."""

from __future__ import annotations

import re

import frappe

# Quotation series by business type (user-facing: Service, Testing, Others)
QUOTE_SERIES_SERVICE = "QTN-SRV-.#####"
QUOTE_SERIES_TESTING = "QTN-TST-.#####"
QUOTE_SERIES_OTHERS = "QTN-OTH-.#####"

QUOTE_SERIES_OPTIONS = "\n".join(
	[
		QUOTE_SERIES_SERVICE,
		QUOTE_SERIES_TESTING,
		QUOTE_SERIES_OTHERS,
	]
)

# ic_quotation_type values that map to Service series
_SERVICE_TYPES = {"Service", "Consulting"}
_TESTING_TYPES = {"Testing"}


def ensure_quotation_naming_series():
	"""Install distinct Quotation series for Service, Testing, and Others."""
	_set_naming_series_options(
		"Quotation",
		options=QUOTE_SERIES_OPTIONS,
		default=QUOTE_SERIES_SERVICE,
	)
	for prefix in ("QTN-SRV-", "QTN-TST-", "QTN-OTH-"):
		_seed_series_counter("Quotation", prefix, digits=5)
	frappe.clear_cache(doctype="Quotation")
	return {
		"service": QUOTE_SERIES_SERVICE,
		"testing": QUOTE_SERIES_TESTING,
		"others": QUOTE_SERIES_OTHERS,
		"examples": ["QTN-SRV-00001", "QTN-TST-00001", "QTN-OTH-00001"],
	}


def quotation_series_for_type(quotation_type: str | None) -> str:
	"""Map ic_quotation_type → naming series."""
	t = (quotation_type or "").strip()
	if t in _TESTING_TYPES:
		return QUOTE_SERIES_TESTING
	if t in _SERVICE_TYPES:
		return QUOTE_SERIES_SERVICE
	# Renewal, Other, Multiple Products / Multiple Services, blank → Others
	return QUOTE_SERIES_OTHERS


def apply_quotation_series(doc):
	"""Set Quotation naming_series from type before insert / on validate (new docs)."""
	if getattr(doc, "flags", None) and doc.flags.get("ignore_ic_naming_series"):
		return
	# Never rename an already-saved document
	if not doc.is_new():
		return
	wanted = quotation_series_for_type(doc.get("ic_quotation_type"))
	current = (doc.get("naming_series") or "").strip()
	if not current or _is_legacy_quotation_series(current) or current != wanted:
		doc.naming_series = wanted


def _is_legacy_quotation_series(series: str) -> bool:
	s = (series or "").strip()
	if s in (QUOTE_SERIES_SERVICE, QUOTE_SERIES_TESTING, QUOTE_SERIES_OTHERS):
		return False
	return bool(re.match(r"^(SAL-)?QTN", s, flags=re.I) or re.match(r"^QTN-\.YYYY", s, flags=re.I))


def _set_naming_series_options(doctype: str, options: str, default: str):
	_upsert_property_setter(doctype, "naming_series", "options", options, "Text")
	_upsert_property_setter(doctype, "naming_series", "default", default, "Text")
	try:
		frappe.db.sql(
			"""
			update `tabDocField`
			set options=%s, `default`=%s
			where parent=%s and fieldname='naming_series'
			""",
			(options, default, doctype),
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"DocField naming_series {doctype}")


def _upsert_property_setter(
	doctype: str, field_name: str, property: str, value: str, property_type: str
):
	existing = frappe.db.exists(
		"Property Setter",
		{"doc_type": doctype, "field_name": field_name, "property": property},
	)
	if existing:
		frappe.db.set_value(
			"Property Setter",
			existing,
			{"value": value, "module": "Instacertify"},
			update_modified=False,
		)
		return
	frappe.get_doc(
		{
			"doctype": "Property Setter",
			"doctype_or_field": "DocField",
			"doc_type": doctype,
			"field_name": field_name,
			"property": property,
			"property_type": property_type,
			"value": value,
			"module": "Instacertify",
		}
	).insert(ignore_permissions=True)


def _seed_series_counter(doctype: str, prefix: str, digits: int = 5):
	like = f"{prefix}%"
	max_n = 0
	try:
		names = frappe.db.sql(
			f"select name from `tab{doctype}` where name like %s",
			(like,),
			as_dict=True,
		)
		rx = re.compile(rf"^{re.escape(prefix)}(\d{{{digits}}})$")
		for row in names:
			m = rx.match(row.name or "")
			if m:
				max_n = max(max_n, int(m.group(1)))
	except Exception:
		pass

	series_name = prefix
	row = frappe.db.sql(
		"select name, current from tabSeries where name=%s",
		(series_name,),
		as_dict=True,
	)
	if row:
		current = int(row[0].get("current") or 0)
		if max_n > current:
			frappe.db.sql(
				"update tabSeries set current=%s where name=%s",
				(max_n, series_name),
			)
	else:
		frappe.db.sql(
			"insert into tabSeries (name, current) values (%s, %s)",
			(series_name, max_n),
		)
