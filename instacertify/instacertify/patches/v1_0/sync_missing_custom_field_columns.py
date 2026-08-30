"""Ensure Custom Field meta columns exist on parent DocType tables.

Some sites had Custom Field rows (e.g. Quotation.ic_primary_assignee) without the
matching MariaDB column, which breaks save/submit with:
OperationalError: Unknown column 'ic_primary_assignee' in 'SET'
"""

from __future__ import annotations

import frappe
from frappe.model import no_value_fields, table_fields


def execute():
	doctypes = sorted(
		{
			r.dt
			for r in frappe.get_all(
				"Custom Field",
				filters={"dt": ["like", "%"]},
				fields=["dt"],
				distinct=True,
			)
			if r.dt
		}
	)
	# Prefer Instacertify-touched doctypes first
	priority = [
		"Quotation",
		"Project",
		"Task",
		"Lead",
		"Customer",
		"Sales Invoice",
		"Purchase Invoice",
		"Event",
		"Asset",
	]
	ordered = [d for d in priority if d in doctypes] + [d for d in doctypes if d not in priority]

	for doctype in ordered:
		if not frappe.db.exists("DocType", doctype):
			continue
		try:
			_sync_doctype_columns(doctype)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"sync custom columns: {doctype}")


def _sync_doctype_columns(doctype: str) -> None:
	from frappe.database.schema import add_column

	meta = frappe.get_meta(doctype)
	missing = []
	for cf in frappe.get_all(
		"Custom Field",
		filters={"dt": doctype},
		fields=["fieldname", "fieldtype", "is_virtual"],
	):
		if not cf.fieldname:
			continue
		if cf.fieldtype in no_value_fields or cf.fieldtype in table_fields:
			continue
		if cf.is_virtual:
			continue
		df = meta.get_field(cf.fieldname)
		if df and getattr(df, "is_virtual", 0):
			continue
		if not frappe.db.has_column(doctype, cf.fieldname):
			missing.append(cf)

	if not missing:
		return

	# updatedb rebuilds columns from DocType + Custom Field meta
	frappe.db.updatedb(doctype)

	still = [cf for cf in missing if not frappe.db.has_column(doctype, cf.fieldname)]
	for cf in still:
		try:
			add_column(doctype, cf.fieldname, cf.fieldtype)
		except Exception:
			frappe.log_error(
				frappe.get_traceback(),
				f"add_column {doctype}.{cf.fieldname}",
			)

	frappe.clear_cache(doctype=doctype)
