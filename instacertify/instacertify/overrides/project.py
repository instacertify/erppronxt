# Copyright (c) Instacertify
"""Project Connections — Quotation, Testing, Documents, Samples."""

from __future__ import annotations

from frappe import _


def get_dashboard_data(data):
	data = data or {}
	data.setdefault("fieldname", "project")
	data.setdefault("non_standard_fieldnames", {})
	data["non_standard_fieldnames"].update(
		{
			"IC Testing Request": "project",
			"IC Document Request": "project",
			"IC Sample Dispatch Collection": "project",
			"IC Sample Tracking": "project",
			"Helpdesk Ticket": "project",
			"IC Project Record": "project",
			"Sales Invoice": "project",
		}
	)

	# Keep ERPNext groups and append Instacertify links
	existing = set()
	for group in data.get("transactions") or []:
		for item in group.get("items") or []:
			existing.add(item)

	def ensure(label, items):
		needed = [i for i in items if i not in existing]
		if not needed:
			return
		for group in data.get("transactions") or []:
			if group.get("label") == label:
				for i in needed:
					group.setdefault("items", []).append(i)
					existing.add(i)
				return
		data.setdefault("transactions", []).append({"label": label, "items": needed})
		existing.update(needed)

	ensure(_("Project"), ["Task", "Timesheet", "Issue", "Project Update"])
	ensure(_("Sales"), ["Sales Order", "Delivery Note", "Sales Invoice"])
	ensure(_("Purchase"), ["Purchase Order", "Purchase Receipt", "Purchase Invoice"])
	ensure(
		_("Instacertify"),
		[
			"IC Testing Request",
			"IC Document Request",
			"IC Sample Dispatch Collection",
			"IC Sample Tracking",
			"IC Project Record",
			"Helpdesk Ticket",
		],
	)
	return data
