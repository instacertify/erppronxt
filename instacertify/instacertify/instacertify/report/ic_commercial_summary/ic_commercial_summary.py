# Copyright (c) Instacertify
"""Script report: Commercial revenue vs pass-through."""

from __future__ import annotations

import frappe


def execute(filters=None):
	filters = filters or {}
	columns = [
		{"label": "Quotation", "fieldname": "name", "fieldtype": "Link", "options": "Quotation", "width": 140},
		{"label": "Customer", "fieldname": "party_name", "fieldtype": "Data", "width": 180},
		{"label": "Currency", "fieldname": "currency", "fieldtype": "Link", "options": "Currency", "width": 80},
		{"label": "Status", "fieldname": "ic_workflow_status", "fieldtype": "Data", "width": 120},
		{"label": "Consulting / Commercial", "fieldname": "ic_commercial_value", "fieldtype": "Currency", "width": 150},
		{"label": "Pass-Through", "fieldname": "ic_passthrough_value", "fieldtype": "Currency", "width": 130},
		{"label": "Total Quoted", "fieldname": "ic_total_quoted_value", "fieldtype": "Currency", "width": 130},
		{"label": "Date", "fieldname": "transaction_date", "fieldtype": "Date", "width": 100},
	]
	conditions = "1=1"
	values = {}
	if filters.get("from_date"):
		conditions += " AND transaction_date >= %(from_date)s"
		values["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions += " AND transaction_date <= %(to_date)s"
		values["to_date"] = filters["to_date"]
	data = frappe.db.sql(
		f"""
		SELECT name, party_name, currency, ic_workflow_status,
		       ic_commercial_value, ic_passthrough_value, ic_total_quoted_value, transaction_date
		FROM `tabQuotation`
		WHERE docstatus < 2 AND {conditions}
		ORDER BY transaction_date DESC
		""",
		values,
		as_dict=True,
	)
	return columns, data
