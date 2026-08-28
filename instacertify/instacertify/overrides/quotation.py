# Copyright (c) Instacertify
"""Quotation Connections — link Project, Invoice, Testing, Documents."""

from __future__ import annotations

from frappe import _


def get_dashboard_data(data):
	data = data or {}
	data.setdefault("fieldname", "prevdoc_docname")
	data.setdefault("non_standard_fieldnames", {})
	data["non_standard_fieldnames"].update(
		{
			"Auto Repeat": "reference_document",
			"Project": "ic_quotation",
			"Sales Invoice": "ic_quotation",
			"IC Testing Request": "quotation",
			"IC Document Request": "quotation",
			"IC Sample Tracking": "quotation",
		}
	)
	data["transactions"] = [
		{
			"label": _("Delivery"),
			"items": ["Project", "IC Testing Request", "IC Document Request", "IC Sample Tracking"],
		},
		{"label": _("Billing"), "items": ["Sales Invoice", "Sales Order"]},
		{"label": _("Subscription"), "items": ["Auto Repeat"]},
	]
	return data
