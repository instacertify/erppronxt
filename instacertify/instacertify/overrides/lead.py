# Copyright (c) Instacertify
"""Lead Connections — Quotation, Opportunity, Customer, Tickets."""

from __future__ import annotations

from frappe import _


def get_dashboard_data(data):
	data = data or {}
	data.setdefault("fieldname", "lead")
	data.setdefault("non_standard_fieldnames", {})
	data["non_standard_fieldnames"].update(
		{
			"Quotation": "party_name",
			"Opportunity": "party_name",
			"Helpdesk Ticket": "lead",
			"Customer": "lead_name",
		}
	)
	data.setdefault("dynamic_links", {})
	data["dynamic_links"].update({"party_name": ["Lead", "quotation_to"]})
	data["transactions"] = [
		{"label": _("Pre Sales"), "items": ["Opportunity", "Quotation", "Prospect", "Customer"]},
		# Only records that hold a link to the lead belong here. A document request
		# has no lead field, and listing it made the whole Connections tab fail.
		{"label": _("Support"), "items": ["Helpdesk Ticket"]},
	]
	return data
