# Copyright (c) Instacertify
"""Unified document naming series — one Sales Invoice series: INV-00001, INV-00002, …"""

from __future__ import annotations

import re

import frappe

# Single series across all Sales Invoices (consulting, testing, others)
SALES_INVOICE_SERIES = "INV-.#####"
SALES_INVOICE_SERIES_OPTIONS = "INV-.#####"
# Credit / debit notes keep a clear sibling prefix but stay INV-family
SALES_INVOICE_RETURN_SERIES = "INV-RET-.#####"
SALES_INVOICE_RETURN_OPTIONS = "INV-.#####\nINV-RET-.#####"


def ensure_invoice_naming_series():
	"""Force one shared Sales Invoice naming series: INV-00001 … INV-99999."""
	_set_naming_series_options(
		"Sales Invoice",
		options=SALES_INVOICE_RETURN_OPTIONS,
		default=SALES_INVOICE_SERIES,
	)
	_seed_series_counter("INV-", digits=5)
	_seed_series_counter("INV-RET-", digits=5)
	frappe.clear_cache(doctype="Sales Invoice")
	return {
		"sales_invoice_series": SALES_INVOICE_SERIES,
		"example": "INV-00001",
	}


def apply_sales_invoice_series(doc):
	"""Ensure a Sales Invoice (or return) uses the unified INV series before insert/save."""
	if getattr(doc, "flags", None) and doc.flags.get("ignore_ic_naming_series"):
		return
	is_return = int(getattr(doc, "is_return", 0) or 0)
	wanted = SALES_INVOICE_RETURN_SERIES if is_return else SALES_INVOICE_SERIES
	# Only override when blank or still on legacy ACC-SINV / SINV patterns
	current = (doc.get("naming_series") or "").strip()
	if not current or _is_legacy_sales_invoice_series(current):
		doc.naming_series = wanted


def _is_legacy_sales_invoice_series(series: str) -> bool:
	s = (series or "").strip()
	if s in (SALES_INVOICE_SERIES, SALES_INVOICE_RETURN_SERIES):
		return False
	return bool(
		re.match(r"^(ACC-)?SINV", s, flags=re.I)
		or re.match(r"^SRET", s, flags=re.I)
		or re.match(r"^ACC-SINV", s, flags=re.I)
	)


def _set_naming_series_options(doctype: str, options: str, default: str):
	"""Property setters for naming_series options + default."""
	_upsert_property_setter(
		doctype=doctype,
		field_name="naming_series",
		property="options",
		value=options,
		property_type="Text",
	)
	_upsert_property_setter(
		doctype=doctype,
		field_name="naming_series",
		property="default",
		value=default,
		property_type="Text",
	)
	# Also patch DocField so forms without property-setter merge still see it
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


def _seed_series_counter(prefix: str, digits: int = 5):
	"""Ensure tabSeries row exists; bump current to max(existing INV-##### names)."""
	like = f"{prefix}%"
	max_n = 0
	try:
		names = frappe.db.sql(
			"""
			select name from `tabSales Invoice`
			where name like %s
			""",
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
