# Copyright (c) Instacertify
"""Helpdesk helpers for CRM ticket raising and dashboard counts."""

from __future__ import annotations

import frappe
from frappe import _


@frappe.whitelist()
def get_open_ticket_summary(limit: int = 8):
	"""Open / in-progress tickets for Home dashboard."""
	limit = int(limit or 8)
	if not frappe.db.exists("DocType", "Helpdesk Ticket"):
		return {"open_count": 0, "tickets": []}

	filters = {"status": ["in", ["Open", "In Progress", "Waiting on Customer"]]}
	tickets = frappe.get_list(
		"Helpdesk Ticket",
		filters=filters,
		fields=[
			"name",
			"subject",
			"ticket_type",
			"status",
			"priority",
			"customer",
			"lead",
			"project",
			"opened_on",
			"assigned_to",
			"modified",
		],
		order_by="priority desc, modified desc",
		limit_page_length=limit,
	)
	for t in tickets:
		t["party"] = t.get("customer") or t.get("lead") or t.get("project") or "—"
	return {
		"open_count": frappe.db.count("Helpdesk Ticket", filters),
		"urgent_count": frappe.db.count(
			"Helpdesk Ticket",
			{
				"status": ["in", ["Open", "In Progress", "Waiting on Customer"]],
				"priority": "Urgent",
			},
		),
		"complaint_count": frappe.db.count(
			"Helpdesk Ticket",
			{
				"status": ["in", ["Open", "In Progress", "Waiting on Customer"]],
				"ticket_type": "Complaint",
			},
		),
		"tickets": tickets,
	}


@frappe.whitelist()
def raise_ticket(
	subject: str,
	ticket_type: str = "Complaint",
	priority: str = "Medium",
	description: str | None = None,
	customer: str | None = None,
	lead: str | None = None,
	opportunity: str | None = None,
	project: str | None = None,
	quotation: str | None = None,
	sales_invoice: str | None = None,
	channel: str = "Internal",
	assigned_to: str | None = None,
):
	"""Create a helpdesk ticket from CRM contexts (Customer, Lead, Project, …)."""
	if not subject:
		frappe.throw(_("Subject is required"))
	if not frappe.db.exists("DocType", "Helpdesk Ticket"):
		frappe.throw(_("Helpdesk Ticket is not installed"))

	doc = frappe.get_doc(
		{
			"doctype": "Helpdesk Ticket",
			"subject": subject,
			"ticket_type": ticket_type or "Complaint",
			"priority": priority or "Medium",
			"description": description or "",
			"customer": customer,
			"lead": lead,
			"opportunity": opportunity,
			"project": project,
			"quotation": quotation,
			"sales_invoice": sales_invoice,
			"channel": channel or "Internal",
			"assigned_to": assigned_to,
			"status": "Open",
		}
	)
	doc.insert(ignore_permissions=False)
	return {"name": doc.name, "route": f"/app/helpdesk-ticket/{doc.name}"}
