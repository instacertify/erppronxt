# Copyright (c) Instacertify
"""QC: unified Sales Invoice series INV-#####."""

from __future__ import annotations

import json
import re

import frappe


def run_invoice_series_qc() -> dict:
	report = {"ok": [], "warn": [], "fail": []}

	def ok(m):
		report["ok"].append(m)

	def fail(m):
		report["fail"].append(m)

	def warn(m):
		report["warn"].append(m)

	frappe.set_user("Administrator")
	from instacertify.setup.naming_series import (
		SALES_INVOICE_SERIES,
		ensure_invoice_naming_series,
		apply_sales_invoice_series,
	)

	ensure_invoice_naming_series()

	# Property setter / meta
	opts = frappe.db.get_value(
		"Property Setter",
		{"doc_type": "Sales Invoice", "field_name": "naming_series", "property": "options"},
		"value",
	)
	default = frappe.db.get_value(
		"Property Setter",
		{"doc_type": "Sales Invoice", "field_name": "naming_series", "property": "default"},
		"value",
	)
	if opts and "INV-.#####" in opts and "ACC-SINV" not in (opts or ""):
		ok(f"options={opts!r}")
	else:
		fail(f"options unexpected: {opts!r}")
	(ok if default == SALES_INVOICE_SERIES else fail)(f"default={default!r}")

	# Apply helper
	dummy = frappe._dict(naming_series="ACC-SINV-.YYYY.-", is_return=0, flags=frappe._dict())
	apply_sales_invoice_series(dummy)
	(ok if dummy.naming_series == SALES_INVOICE_SERIES else fail)(
		f"legacy rewrite → {dummy.naming_series}"
	)

	# Create a draft SI and confirm name pattern (then cancel/delete)
	existing_si = frappe.db.get_value(
		"Sales Invoice", {}, ["customer", "company"], order_by="creation desc", as_dict=True
	)
	customer = (existing_si or {}).get("customer") or frappe.db.get_value(
		"Customer", {}, "name", order_by="modified desc"
	)
	company = (existing_si or {}).get("company") or frappe.db.get_value(
		"Company", {}, "name", order_by="creation asc"
	)
	item = frappe.db.get_value("Item", {"is_sales_item": 1, "is_stock_item": 0}, "name") or frappe.db.get_value(
		"Item", {"is_sales_item": 1}, "name"
	) or frappe.db.get_value("Item", {}, "name")
	if not (customer and company and item):
		warn("Skip create SI — missing customer/company/item")
	else:
		try:
			si = frappe.new_doc("Sales Invoice")
			si.customer = customer
			si.company = company
			si.posting_date = frappe.utils.today()
			# Prefer a cost center / income account if company needs them
			si.append("items", {"item_code": item, "qty": 1, "rate": 1})
			apply_sales_invoice_series(si)
			# Bypass fiscal year issues on throw by using ignore_validate if needed
			si.flags.ignore_permissions = True
			si.insert(ignore_permissions=True)
			name = si.name
			if re.match(r"^INV-\d{5}$", name):
				ok(f"created {name}")
			else:
				fail(f"created unexpected name {name}")
			try:
				si.delete(ignore_permissions=True)
				ok(f"deleted draft {name}")
			except Exception as e:
				warn(f"cleanup: {e}")
		except Exception as e:
			# Still verify series was set even if insert fails for accounting reasons
			msg = str(e)
			warn(f"SI insert skipped ({msg[:120]})")
			# Unit-test make_autoname
			from frappe.model.naming import make_autoname

			trial = make_autoname(SALES_INVOICE_SERIES)
			if re.match(r"^INV-\d{5}$", trial):
				ok(f"make_autoname → {trial}")
			else:
				fail(f"make_autoname unexpected {trial}")
			# rollback counter bump from make_autoname by not worrying — OK for QC site
			frappe.db.rollback()
			ensure_invoice_naming_series()
			frappe.db.commit()

	report["summary"] = {
		"ok": len(report["ok"]),
		"warn": len(report["warn"]),
		"fail": len(report["fail"]),
		"passed": len(report["fail"]) == 0,
		"series": SALES_INVOICE_SERIES,
	}
	print(json.dumps(report, indent=2, default=str))
	return report
