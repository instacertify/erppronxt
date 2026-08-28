# Copyright (c) Instacertify
"""QC: Quotation series by type — Service / Testing / Others."""

from __future__ import annotations

import json
import re

import frappe


def run_quote_series_qc() -> dict:
	report = {"ok": [], "warn": [], "fail": []}

	def ok(m):
		report["ok"].append(m)

	def fail(m):
		report["fail"].append(m)

	def warn(m):
		report["warn"].append(m)

	frappe.set_user("Administrator")
	from instacertify.setup.naming_series import (
		QUOTE_SERIES_OTHERS,
		QUOTE_SERIES_SERVICE,
		QUOTE_SERIES_TESTING,
		apply_quotation_series,
		ensure_quotation_naming_series,
		quotation_series_for_type,
	)

	ensure_quotation_naming_series()

	opts = frappe.db.get_value(
		"Property Setter",
		{"doc_type": "Quotation", "field_name": "naming_series", "property": "options"},
		"value",
	) or ""
	for s in (QUOTE_SERIES_SERVICE, QUOTE_SERIES_TESTING, QUOTE_SERIES_OTHERS):
		(ok if s in opts else fail)(f"options contain {s}")
	if "SAL-QTN" in opts:
		fail(f"legacy SAL-QTN still in options: {opts!r}")
	else:
		ok("legacy SAL-QTN removed")

	cases = [
		("Service", QUOTE_SERIES_SERVICE),
		("Consulting", QUOTE_SERIES_SERVICE),
		("Testing", QUOTE_SERIES_TESTING),
		("Other", QUOTE_SERIES_OTHERS),
		("Renewal", QUOTE_SERIES_OTHERS),
		("Multiple Products / Multiple Services", QUOTE_SERIES_OTHERS),
		("", QUOTE_SERIES_OTHERS),
	]
	for t, expected in cases:
		got = quotation_series_for_type(t)
		(ok if got == expected else fail)(f"type {t!r} → {got} (want {expected})")

	# Dummy apply
	dummy = frappe._dict(
		naming_series="SAL-QTN-.YYYY.-",
		ic_quotation_type="Testing",
		flags=frappe._dict(),
	)
	# is_new()
	dummy.is_new = lambda: True  # type: ignore
	apply_quotation_series(dummy)
	(ok if dummy.naming_series == QUOTE_SERIES_TESTING else fail)(
		f"apply Testing → {dummy.naming_series}"
	)

	# Create one draft per bucket
	company = frappe.db.get_value("Company", {}, "name")
	party = frappe.db.get_value("Customer", {}, "name") or frappe.db.get_value("Lead", {}, "name")
	if not (company and party):
		warn("Skip create — no company/party")
	else:
		created = []
		for qtype, prefix in (
			("Service", "QTN-SRV-"),
			("Testing", "QTN-TST-"),
			("Other", "QTN-OTH-"),
		):
			try:
				q = frappe.new_doc("Quotation")
				q.quotation_to = "Customer" if frappe.db.exists("Customer", party) else "Lead"
				q.party_name = party
				q.company = company
				q.transaction_date = frappe.utils.today()
				q.ic_quotation_type = qtype
				q.order_type = "Sales"
				apply_quotation_series(q)
				# Minimal item if required
				item = frappe.db.get_value("Item", {"is_sales_item": 1}, "name")
				if item and not q.items:
					q.append("items", {"item_code": item, "qty": 1, "rate": 1})
				q.insert(ignore_permissions=True)
				name = q.name
				if re.match(rf"^{re.escape(prefix)}\d{{5}}$", name):
					ok(f"created {name} ({qtype})")
				else:
					fail(f"created unexpected {name} for {qtype}")
				created.append(q)
			except Exception as e:
				warn(f"create {qtype}: {e}")
				from frappe.model.naming import make_autoname

				series = quotation_series_for_type(qtype)
				trial = make_autoname(series)
				(ok if trial.startswith(prefix) else fail)(f"make_autoname {qtype} → {trial}")
		for q in created:
			try:
				q.delete(ignore_permissions=True)
			except Exception as e:
				warn(f"cleanup {q.name}: {e}")
		if created:
			ok(f"cleaned {len(created)} drafts")

	report["summary"] = {
		"ok": len(report["ok"]),
		"warn": len(report["warn"]),
		"fail": len(report["fail"]),
		"passed": len(report["fail"]) == 0,
	}
	print(json.dumps(report, indent=2, default=str))
	return report
