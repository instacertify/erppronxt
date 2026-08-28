# Copyright (c) Instacertify
"""Customer form Connections dashboard — ERPNext links + Instacertify DocTypes."""

from __future__ import annotations

from frappe import _


def get_dashboard_data(data):
	"""Extend Customer Connections with certification / consulting records."""
	data.setdefault("fieldname", "customer")
	data.setdefault("non_standard_fieldnames", {})
	data.setdefault("dynamic_links", {})
	data.setdefault("transactions", [])

	# Ensure core selling / project groups remain visible (ERPNext already adds these;
	# re-assert labels users expect when browsing a customer).
	existing_items = set()
	for group in data["transactions"]:
		for item in group.get("items") or []:
			existing_items.add(item)

	ic_items = [
		"Helpdesk Ticket",
		"IC Testing Request",
		"IC Document Request",
		"IC Sample Tracking",
		"IC Project Record",
	]
	missing_ic = [dt for dt in ic_items if dt not in existing_items]
	if missing_ic:
		data["transactions"].append({"label": _("Instacertify"), "items": missing_ic})

	_ensure_group(data, _("Helpdesk"), ["Helpdesk Ticket", "Issue"], existing_items)

	# Guarantee Projects / Invoices / Quotations / Payments appear even if a prior
	# override stripped them.
	_ensure_group(data, _("Pre Sales"), ["Opportunity", "Quotation"], existing_items)
	_ensure_group(
		data,
		_("Orders"),
		["Sales Order", "Delivery Note", "Sales Invoice"],
		existing_items,
	)
	_ensure_group(
		data,
		_("Payments"),
		["Payment Entry", "Bank Account", "Dunning"],
		existing_items,
	)
	_ensure_group(data, _("Projects"), ["Project"], existing_items)

	return data


def _ensure_group(data, label, items, existing_items):
	needed = [dt for dt in items if dt not in existing_items]
	if not needed:
		return
	for group in data["transactions"]:
		if group.get("label") == label:
			for dt in needed:
				if dt not in group["items"]:
					group["items"].append(dt)
					existing_items.add(dt)
			return
	data["transactions"].append({"label": label, "items": needed})
	existing_items.update(needed)
