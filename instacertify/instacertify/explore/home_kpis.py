# Copyright (c) Instacertify
"""Headline figures for the Home page.

Read-only. Every figure is counted from existing records, is left out when the
signed-in user cannot read that kind of record, and comes with the list filters
that open exactly the records it counts.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate, nowdate

QUOTES_WAITING = ["Shared with Customer", "Customer Review"]
LEADS_CLOSED = ["Converted", "Do Not Contact"]
PROJECTS_CLOSED = ["Completed", "Cancelled"]
TASKS_CLOSED = ["Completed", "Cancelled", "Template"]


def _can_read(doctype: str) -> bool:
	try:
		return bool(frappe.db.exists("DocType", doctype) and frappe.has_permission(doctype, "read"))
	except Exception:
		return False


def _count(doctype: str, filters=None) -> int:
	try:
		return int(frappe.db.count(doctype, filters or {}) or 0)
	except Exception:
		return 0


def _change(current, previous):
	"""Percent change against the earlier period; None when there is nothing to compare with."""
	if not previous:
		return None
	return round(((flt(current) - flt(previous)) / flt(previous)) * 100.0, 1)


def _invoiced(from_date, to_date) -> float:
	"""Net amount (before tax) of submitted sales invoices posted in the period."""
	try:
		rows = frappe.db.sql(
			"""
			select coalesce(sum(base_net_total), 0)
			from `tabSales Invoice`
			where docstatus = 1 and posting_date between %s and %s
			""",
			(str(from_date), str(to_date)),
		)
		return flt(rows[0][0]) if rows else 0.0
	except Exception:
		return 0.0


@frappe.whitelist()
def get_home_kpis() -> dict:
	today = getdate(nowdate())
	d30 = add_days(today, -29)
	prev_from = add_days(today, -59)
	prev_to = add_days(today, -30)
	period = _("last 30 days")
	versus = _("vs previous 30 days")

	cards: list[dict] = []

	if _can_read("Lead"):
		total = _count("Lead")
		new_now = _count("Lead", [["creation", ">=", str(d30)]])
		new_prev = _count(
			"Lead", [["creation", ">=", str(prev_from)], ["creation", "<", str(d30)]]
		)
		converted = _count("Lead", {"status": "Converted"})
		due = _count(
			"Lead",
			[
				["status", "not in", LEADS_CLOSED],
				["ic_next_contact_date", "is", "set"],
				["ic_next_contact_date", "<=", str(today)],
			],
		) if frappe.get_meta("Lead").has_field("ic_next_contact_date") else None
		overdue = _count(
			"Lead",
			[
				["status", "not in", LEADS_CLOSED],
				["ic_next_contact_date", "is", "set"],
				["ic_next_contact_date", "<", str(today)],
			],
		) if due is not None else 0

		cards.append(
			{
				"id": "total_leads",
				"label": _("Total leads"),
				"icon": "users",
				"value": total,
				"sub": _("{0} added in the {1}").format(new_now, period),
				"doctype": "Lead",
				"filters": [],
			}
		)
		cards.append(
			{
				"id": "new_leads",
				"label": _("New leads (30 days)"),
				"icon": "user-plus",
				"value": new_now,
				"sub": "",
				"change": _change(new_now, new_prev),
				"change_label": versus,
				"doctype": "Lead",
				"filters": [["Lead", "creation", ">=", str(d30)]],
			}
		)
		cards.append(
			{
				"id": "converted_leads",
				"label": _("Converted leads"),
				"icon": "badge-check",
				"value": converted,
				"sub": _("{0}% of all leads").format(f"{(converted * 100.0 / total) if total else 0:.1f}".rstrip("0").rstrip(".")),
				"doctype": "Lead",
				"filters": [["Lead", "status", "=", "Converted"]],
				"tone": "ok",
			}
		)
		if due is not None:
			cards.append(
				{
					"id": "pending_followups",
					"label": _("Pending follow-ups"),
					"icon": "phone",
					"value": due,
					"sub": _("{0} overdue").format(overdue) if overdue else _("due today or earlier"),
					"doctype": "Lead",
					"filters": [
						["Lead", "status", "not in", LEADS_CLOSED],
						["Lead", "ic_next_contact_date", "between", ["2000-01-01", str(today)]],
					],
					"tone": "warn" if due else "",
				}
			)

	if _can_read("Project"):
		active = _count("Project", {"status": ["not in", PROJECTS_CLOSED]})
		sub = ""
		if frappe.get_meta("Project").has_field("ic_deadline"):
			soon = _count(
				"Project",
				{
					"status": ["not in", PROJECTS_CLOSED],
					"ic_deadline": ["<=", str(add_days(today, 14))],
				},
			)
			sub = _("{0} due within 14 days").format(soon)
		cards.append(
			{
				"id": "active_projects",
				"label": _("Active projects"),
				"icon": "briefcase",
				"value": active,
				"sub": sub,
				"doctype": "Project",
				"filters": [["Project", "status", "not in", PROJECTS_CLOSED]],
			}
		)

	if _can_read("Quotation") and frappe.get_meta("Quotation").has_field("ic_workflow_status"):
		waiting = _count("Quotation", {"ic_workflow_status": ["in", QUOTES_WAITING]})
		cards.append(
			{
				"id": "quotations_pending",
				"label": _("Quotations pending"),
				"icon": "file-text",
				"value": waiting,
				"sub": _("waiting for the customer's reply"),
				"doctype": "Quotation",
				"filters": [["Quotation", "ic_workflow_status", "in", QUOTES_WAITING]],
			}
		)

	if _can_read("Sales Invoice"):
		now_amount = _invoiced(d30, today)
		prev_amount = _invoiced(prev_from, prev_to)
		currency = None
		try:
			company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value(
				"Global Defaults", "default_company"
			)
			currency = frappe.get_cached_value("Company", company, "default_currency") if company else None
		except Exception:
			currency = None
		cards.append(
			{
				"id": "revenue",
				"label": _("Revenue (30 days)"),
				"icon": "indian-rupee",
				"value": now_amount,
				"currency": currency or frappe.db.get_default("currency"),
				"sub": _("invoiced, before tax"),
				"change": _change(now_amount, prev_amount),
				"change_label": versus,
				"doctype": "Sales Invoice",
				"filters": [
					["Sales Invoice", "docstatus", "=", 1],
					["Sales Invoice", "posting_date", "between", [str(d30), str(today)]],
				],
			}
		)

	if _can_read("Task"):
		late = _count(
			"Task",
			[
				["status", "not in", TASKS_CLOSED],
				["exp_end_date", "is", "set"],
				["exp_end_date", "<", str(today)],
			],
		)
		cards.append(
			{
				"id": "overdue_tasks",
				"label": _("Overdue tasks"),
				"icon": "alarm-clock",
				"value": late,
				"sub": _("past their end date"),
				"doctype": "Task",
				"filters": [
					["Task", "status", "not in", TASKS_CLOSED],
					["Task", "exp_end_date", "<", str(today)],
				],
				"tone": "danger" if late else "",
			}
		)

	order = [
		"total_leads",
		"new_leads",
		"converted_leads",
		"active_projects",
		"quotations_pending",
		"revenue",
		"pending_followups",
		"overdue_tasks",
	]
	cards.sort(key=lambda c: order.index(c["id"]))
	return {"cards": cards, "as_of": str(today)}
