# Copyright (c) Instacertify
"""Role-aware explore prompts shown on Instacertify Home after login."""

from __future__ import annotations

import frappe
from frappe import _


def _can_read(doctype: str) -> bool:
	try:
		return bool(frappe.has_permission(doctype, "read"))
	except Exception:
		return False


def _can_create(doctype: str) -> bool:
	try:
		return bool(frappe.has_permission(doctype, "create"))
	except Exception:
		return False


def _count(doctype: str, filters: dict | None = None) -> int | None:
	if not _can_read(doctype):
		return None
	try:
		return frappe.db.count(doctype, filters or {})
	except Exception:
		return None


@frappe.whitelist()
def get_explore_prompts() -> dict:
	"""
	Return explore cards for the Home dashboard so users can discover
	relevant Instacertify options right after login.
	"""
	roles = set(frappe.get_roles())
	is_admin = bool(roles & {"System Manager", "IC Admin", "Administrator"})
	is_sales = bool(roles & {"IC Sales Person", "Sales User", "Sales Manager"}) or is_admin
	is_ops = bool(
		roles
		& {
			"IC Operations Manager",
			"IC Senior Operations",
			"Projects User",
			"Projects Manager",
		}
	) or is_admin

	cards: list[dict] = []

	def add(
		card_id: str,
		title: str,
		subtitle: str,
		route: list,
		*,
		doctype: str | None = None,
		count: int | None = None,
		accent: str = "teal",
		action: str | None = None,
		priority: int = 50,
		show: bool = True,
		icon: str | None = None,
	):
		if not show:
			return
		if doctype and not _can_read(doctype):
			return
		from instacertify.setup.navigation_icons import EXPLORE_ICONS

		cards.append(
			{
				"id": card_id,
				"title": title,
				"subtitle": subtitle,
				"route": route,
				"doctype": doctype,
				"count": count,
				"accent": accent,
				"action": action,
				"priority": priority,
				"icon": icon or EXPLORE_ICONS.get(card_id) or "file",
			}
		)

	# Universal — everyone with desk access
	add(
		"leads",
		_("Leads"),
		_("Capture & follow up prospects"),
		["List", "Lead"],
		doctype="Lead",
		count=_count("Lead", {"status": ["not in", ["Converted", "Do Not Contact"]]}),
		accent="coral",
		priority=10,
		show=is_sales or is_ops or is_admin,
	)
	add(
		"quotations",
		_("Quotations"),
		_("Create & share customer quotes"),
		["List", "Quotation"],
		doctype="Quotation",
		count=_count("Quotation"),
		accent="teal",
		priority=20,
		show=is_sales or is_admin,
	)
	add(
		"quote_library",
		_("Quote Format Library"),
		_("Upload & manage quote templates"),
		["List", "IC Quotation Template"],
		doctype="IC Quotation Template",
		count=_count("IC Quotation Template", {"is_active": 1}),
		accent="citrus",
		action="upload_quote_format",
		priority=25,
		show=is_sales or is_admin,
	)
	add(
		"customers",
		_("Customers"),
		_("Accounts & contacts"),
		["List", "Customer"],
		doctype="Customer",
		count=_count("Customer"),
		accent="teal",
		priority=30,
		show=is_sales or is_ops or is_admin,
	)
	add(
		"projects",
		_("Projects"),
		_("Delivery board & timelines"),
		["List", "Project"],
		doctype="Project",
		count=_count("Project", {"status": ["not in", ["Completed", "Cancelled"]]}),
		accent="teal",
		priority=40,
		show=is_ops or is_sales or is_admin,
	)
	add(
		"project_board",
		_("Project Board"),
		_("Tile view of ongoing work"),
		["project-board"],
		accent="teal",
		priority=45,
		show=is_ops or is_sales or is_admin,
	)
	add(
		"labs",
		_("Laboratories"),
		_("Lab names, scope & prices"),
		["List", "IC Laboratory"],
		doctype="IC Laboratory",
		count=_count("IC Laboratory", {"status": "Active"}),
		accent="citrus",
		action="upload_laboratory",
		priority=50,
		show=is_ops or is_admin,
	)
	add(
		"testing",
		_("Testing Requests"),
		_("Lab testing workflow"),
		["List", "IC Testing Request"],
		doctype="IC Testing Request",
		count=_count("IC Testing Request", {"status": ["not in", ["Report Shared with Customer"]]}),
		accent="teal",
		priority=55,
		show=is_ops or is_admin,
	)
	add(
		"samples",
		_("Samples"),
		_("Custody & dispatch tracking"),
		["List", "IC Sample Tracking"],
		doctype="IC Sample Tracking",
		count=_count("IC Sample Tracking"),
		accent="teal",
		priority=60,
		show=is_ops or is_admin,
	)
	add(
		"documents",
		_("Documents Collection"),
		_("Customer upload checklists & share links"),
		["List", "IC Document Request"],
		doctype="IC Document Request",
		count=_count("IC Document Request", {"status": ["in", ["Sent to Customer", "Partially Uploaded"]]}),
		accent="coral",
		priority=65,
		show=is_ops or is_sales or is_admin,
	)
	add(
		"sample_dispatch",
		_("Sample Dispatch Sheets"),
		_("Customer sample dispatch data collection"),
		["List", "IC Sample Dispatch Collection"],
		doctype="IC Sample Dispatch Collection",
		count=_count("IC Sample Dispatch Collection"),
		accent="teal",
		priority=66,
		show=is_ops or is_admin,
	)
	add(
		"helpdesk",
		_("Helpdesk"),
		_("Complaints & support tickets"),
		["List", "Helpdesk Ticket"],
		doctype="Helpdesk Ticket",
		count=_count(
			"Helpdesk Ticket",
			{"status": ["in", ["Open", "In Progress", "Waiting on Customer"]]},
		),
		accent="coral",
		priority=70,
	)
	add(
		"calendar",
		_("Team Calendar"),
		_("Sessions & reminders"),
		["List", "Event", "Calendar"],
		doctype="Event",
		accent="teal",
		priority=80,
	)
	add(
		"collab",
		_("Team Collaboration"),
		_("Project chats with teammates"),
		["team-collaboration"],
		accent="teal",
		priority=85,
	)
	add(
		"invoices",
		_("Sales Invoice"),
		_("Bill consulting services"),
		["List", "Sales Invoice"],
		doctype="Sales Invoice",
		accent="citrus",
		priority=90,
		show=is_sales or is_admin,
	)
	add(
		"purchase",
		_("Purchase Invoice"),
		_("Buy lab / vendor services"),
		["List", "Purchase Invoice"],
		doctype="Purchase Invoice",
		accent="citrus",
		priority=91,
		show=is_ops or is_admin,
	)
	# Expenses & HRMS — always last in Explore
	add(
		"hr_lifecycle",
		_("HRMS (Hiring → FnF)"),
		_("Applicant · onboarding · payroll · exit"),
		["List", "Employee"],
		doctype="Employee",
		accent="teal",
		priority=98,
		show=_can_read("Employee") or is_admin,
	)
	add(
		"expenses",
		_("File an Expense"),
		_("Travel · petty · office expenses"),
		["List", "IC Expense Claim"],
		doctype="IC Expense Claim",
		count=_count("IC Expense Claim", {"owner": frappe.session.user, "status": ["in", ["Draft", "Submitted"]]}),
		accent="citrus",
		action="new_expense",
		priority=99,
		show=_can_create("IC Expense Claim") or _can_read("IC Expense Claim"),
	)

	cards.sort(key=lambda c: (c.get("priority", 99), c.get("title") or ""))

	# Always show at least a helpful subset for Desk User with sparse roles
	if not cards:
		add(
			"helpdesk",
			_("Helpdesk"),
			_("Raise a complaint or query"),
			["List", "Helpdesk Ticket"],
			doctype="Helpdesk Ticket",
			accent="coral",
			priority=1,
		)
		add(
			"expenses",
			_("File an Expense"),
			_("Travel · petty · office"),
			["List", "IC Expense Claim"],
			doctype="IC Expense Claim",
			action="new_expense",
			accent="citrus",
			priority=2,
			show=_can_read("IC Expense Claim"),
		)

	return {
		"user": frappe.session.user,
		"full_name": frappe.utils.get_fullname(frappe.session.user),
		"roles": sorted(roles),
		"cards": cards,
		"hint": _("Tap a card to explore — uploads and new forms open from the Library / File buttons."),
	}
