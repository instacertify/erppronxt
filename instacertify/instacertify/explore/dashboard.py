# Copyright (c) Instacertify
"""Role-aware home sections shown on Instacertify Home after login."""

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


def _doctype_exists(name: str) -> bool:
	return bool(frappe.db.exists("DocType", name))


def get_user_authority(roles: set[str] | None = None) -> dict:
	"""Map session roles to major home-section authority flags."""
	roles = set(roles or frappe.get_roles())
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
	is_accounts = bool(roles & {"Accounts Manager", "Accounts User", "Auditor"}) or is_admin
	is_hr = bool(roles & {"HR Manager", "HR User", "Employee"}) or _can_read("Employee") or is_admin
	# Settings / master data uploads — ops leads + admin
	is_settings = is_admin or bool(roles & {"IC Senior Operations", "IC Operations Manager"})
	can_expense = _can_create("IC Expense Claim") or _can_read("IC Expense Claim")

	return {
		"is_admin": is_admin,
		"is_sales": is_sales,
		"is_ops": is_ops,
		"is_accounts": is_accounts,
		"is_hr": is_hr,
		"is_settings": is_settings,
		"show_crm": is_sales or is_ops,
		"show_projects": is_ops or is_sales,
		"show_billing": is_accounts or is_sales or is_ops or is_admin,
		"show_hrms": is_hr or can_expense,
		"show_settings": is_settings,
		"show_helpdesk": True,
		"show_collab": is_ops or is_sales or is_admin,
	}


@frappe.whitelist()
def get_explore_prompts() -> dict:
	"""
	Return major home sections + explore cards filtered by the user's authority.
	Sections: CRM & Leads, Projects & Labs, Billing/Finance/GST, HRMS, Settings.
	"""
	roles = set(frappe.get_roles())
	auth = get_user_authority(roles)

	sections_meta = [
		{
			"id": "crm",
			"title": _("CRM & Lead Management"),
			"subtitle": _("Leads, customers, quotes and follow-ups"),
			"show": auth["show_crm"],
			"accent": "coral",
		},
		{
			"id": "projects",
			"title": _("Projects & Labs"),
			"subtitle": _("Delivery, testing, samples and laboratories"),
			"show": auth["show_projects"],
			"accent": "teal",
		},
		{
			"id": "billing",
			"title": _("Billing, Finance & GST"),
			"subtitle": _("Invoices, payments, accounts and GST returns"),
			"show": auth["show_billing"],
			"accent": "citrus",
		},
		{
			"id": "hrms",
			"title": _("HRMS"),
			"subtitle": _("Hiring → payroll → exit · expenses"),
			"show": auth["show_hrms"],
			"accent": "teal",
		},
		{
			"id": "settings",
			"title": _("Settings & Uploads"),
			"subtitle": _("Upload masters, quote formats, labs and config"),
			"show": auth["show_settings"],
			"accent": "citrus",
		},
		{
			"id": "everyday",
			"title": _("Everyday"),
			"subtitle": _("Calendar, helpdesk and collaboration"),
			"show": True,
			"accent": "teal",
		},
	]

	cards: list[dict] = []

	def add(
		section: str,
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
		if doctype and not _doctype_exists(doctype):
			return
		if doctype and not _can_read(doctype) and not action:
			return
		from instacertify.setup.navigation_icons import EXPLORE_ICONS

		cards.append(
			{
				"id": card_id,
				"section": section,
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

	# ——— CRM & Lead Management ———
	add(
		"crm",
		"leads",
		_("Leads"),
		_("Capture & follow up prospects"),
		["List", "Lead"],
		doctype="Lead",
		count=_count("Lead", {"status": ["not in", ["Converted", "Do Not Contact"]]}),
		accent="coral",
		priority=10,
		show=auth["show_crm"],
	)
	add(
		"crm",
		"quotations",
		_("Quotations"),
		_("Create & share customer quotes"),
		["List", "Quotation"],
		doctype="Quotation",
		count=_count("Quotation"),
		accent="teal",
		priority=20,
		show=auth["is_sales"] or auth["is_admin"],
	)
	add(
		"crm",
		"customers",
		_("Customers"),
		_("Accounts & contacts"),
		["List", "Customer"],
		doctype="Customer",
		count=_count("Customer"),
		accent="teal",
		priority=30,
		show=auth["show_crm"],
	)
	add(
		"crm",
		"opportunities",
		_("Opportunities"),
		_("Pipeline deals"),
		["List", "Opportunity"],
		doctype="Opportunity",
		count=_count("Opportunity", {"status": ["not in", ["Lost", "Closed"]]}),
		accent="coral",
		priority=35,
		show=auth["is_sales"] or auth["is_admin"],
	)
	add(
		"crm",
		"documents",
		_("Documents Collection"),
		_("Customer upload checklists & share links"),
		["List", "IC Document Request"],
		doctype="IC Document Request",
		count=_count(
			"IC Document Request",
			{"status": ["in", ["Sent to Customer", "Partially Uploaded"]]},
		),
		accent="coral",
		priority=40,
		show=auth["show_crm"],
	)
	add(
		"crm",
		"quote_library",
		_("Quote Format Library"),
		_("Upload & manage quote templates"),
		["List", "IC Quotation Template"],
		doctype="IC Quotation Template",
		count=_count("IC Quotation Template", {"is_active": 1}),
		accent="citrus",
		action="upload_quote_format",
		priority=45,
		show=auth["is_sales"] or auth["is_admin"],
	)

	# ——— Projects & Labs ———
	add(
		"projects",
		"projects",
		_("Projects"),
		_("Delivery board & timelines"),
		["List", "Project"],
		doctype="Project",
		count=_count("Project", {"status": ["not in", ["Completed", "Cancelled"]]}),
		accent="teal",
		priority=10,
		show=auth["show_projects"],
	)
	add(
		"projects",
		"project_board",
		_("Project Board"),
		_("Tile view of ongoing work"),
		["project-board"],
		accent="teal",
		priority=15,
		show=auth["show_projects"],
	)
	add(
		"projects",
		"labs",
		_("Laboratories"),
		_("Lab names, scope & prices"),
		["List", "IC Laboratory"],
		doctype="IC Laboratory",
		count=_count("IC Laboratory", {"status": "Active"}),
		accent="citrus",
		priority=20,
		show=auth["is_ops"] or auth["is_admin"],
	)
	add(
		"projects",
		"testing",
		_("Testing Requests"),
		_("Lab testing workflow"),
		["List", "IC Testing Request"],
		doctype="IC Testing Request",
		count=_count(
			"IC Testing Request",
			{"status": ["not in", ["Report Shared with Customer"]]},
		),
		accent="teal",
		priority=25,
		show=auth["is_ops"] or auth["is_admin"],
	)
	add(
		"projects",
		"samples",
		_("Samples"),
		_("Custody & dispatch tracking"),
		["List", "IC Sample Tracking"],
		doctype="IC Sample Tracking",
		count=_count("IC Sample Tracking"),
		accent="teal",
		priority=30,
		show=auth["is_ops"] or auth["is_admin"],
	)
	add(
		"projects",
		"sample_dispatch",
		_("Sample Dispatch Sheets"),
		_("Customer sample dispatch data collection"),
		["List", "IC Sample Dispatch Collection"],
		doctype="IC Sample Dispatch Collection",
		count=_count("IC Sample Dispatch Collection"),
		accent="teal",
		priority=35,
		show=auth["is_ops"] or auth["is_admin"],
	)

	# ——— Billing, Finance & GST ———
	add(
		"billing",
		"invoices",
		_("Sales Invoice"),
		_("Bill consulting & services"),
		["List", "Sales Invoice"],
		doctype="Sales Invoice",
		count=_count("Sales Invoice", {"docstatus": 0}),
		accent="citrus",
		priority=10,
		show=auth["show_billing"] and (auth["is_sales"] or auth["is_accounts"] or auth["is_admin"]),
	)
	add(
		"billing",
		"payments",
		_("Payment Entry"),
		_("Receive & make payments"),
		["List", "Payment Entry"],
		doctype="Payment Entry",
		accent="citrus",
		priority=20,
		show=auth["is_accounts"] or auth["is_admin"],
	)
	add(
		"billing",
		"purchase",
		_("Purchase Invoice"),
		_("Buy lab / vendor services"),
		["List", "Purchase Invoice"],
		doctype="Purchase Invoice",
		accent="citrus",
		priority=30,
		show=(auth["is_ops"] or auth["is_accounts"] or auth["is_admin"]) and auth["show_billing"],
	)
	add(
		"billing",
		"journal",
		_("Journal Entry"),
		_("Accounting adjustments"),
		["List", "Journal Entry"],
		doctype="Journal Entry",
		accent="teal",
		priority=40,
		show=auth["is_accounts"] or auth["is_admin"],
	)
	add(
		"billing",
		"gstr1",
		_("GSTR-1"),
		_("File outward supplies"),
		["List", "GSTR-1"],
		doctype="GSTR-1",
		accent="coral",
		priority=50,
		show=auth["is_accounts"] or auth["is_admin"],
	)
	add(
		"billing",
		"gstr3b",
		_("GSTR-3B"),
		_("Monthly GST return"),
		["List", "GSTR 3B Report"],
		doctype="GSTR 3B Report",
		accent="coral",
		priority=55,
		show=auth["is_accounts"] or auth["is_admin"],
	)
	add(
		"billing",
		"gst_india",
		_("GST India"),
		_("GST workspace & settings"),
		["Workspaces", "GST India"],
		accent="coral",
		priority=60,
		show=auth["is_accounts"] or auth["is_admin"],
	)
	add(
		"billing",
		"chart_of_accounts",
		_("Chart of Accounts"),
		_("Company account tree"),
		["Tree", "Account"],
		doctype="Account",
		accent="teal",
		priority=70,
		show=auth["is_accounts"] or auth["is_admin"],
	)

	# ——— HRMS ———
	add(
		"hrms",
		"hr_lifecycle",
		_("HRMS (Hiring → FnF)"),
		_("Applicant · onboarding · payroll · exit"),
		["List", "Employee"],
		doctype="Employee",
		accent="teal",
		priority=10,
		show=auth["show_hrms"] and (_can_read("Employee") or auth["is_admin"]),
	)
	add(
		"hrms",
		"expenses",
		_("File an Expense"),
		_("Travel · petty · office expenses"),
		["List", "IC Expense Claim"],
		doctype="IC Expense Claim",
		count=_count(
			"IC Expense Claim",
			{"owner": frappe.session.user, "status": ["in", ["Draft", "Submitted"]]},
		),
		accent="citrus",
		action="new_expense",
		priority=20,
		show=_can_create("IC Expense Claim") or _can_read("IC Expense Claim") or auth["show_hrms"],
	)
	add(
		"hrms",
		"hrms_workspace",
		_("HRMS & Expenses"),
		_("Open HR workspace"),
		["Workspaces", "HRMS & Expenses"],
		accent="teal",
		priority=30,
		show=auth["show_hrms"],
	)
	add(
		"hrms",
		"attendance",
		_("Attendance"),
		_("Mark & review attendance"),
		["List", "Attendance"],
		doctype="Attendance",
		accent="teal",
		priority=40,
		show=auth["show_hrms"] and _can_read("Attendance"),
	)
	add(
		"hrms",
		"leave",
		_("Leave Application"),
		_("Apply and approve leave"),
		["List", "Leave Application"],
		doctype="Leave Application",
		accent="teal",
		priority=50,
		show=auth["show_hrms"] and _can_read("Leave Application"),
	)

	# ——— Settings & Uploads ———
	add(
		"settings",
		"lab_upload",
		_("Upload Laboratories"),
		_("Import lab masters & pricing"),
		["List", "IC Laboratory"],
		doctype="IC Laboratory",
		accent="citrus",
		action="upload_laboratory",
		priority=20,
		show=auth["show_settings"],
	)
	add(
		"settings",
		"lead_sources",
		_("Lead Sources"),
		_("Editable lead source master"),
		["List", "IC Lead Source"],
		doctype="IC Lead Source",
		accent="teal",
		priority=30,
		show=auth["show_settings"],
	)
	add(
		"settings",
		"project_types",
		_("Project Types"),
		_("Service / project type master"),
		["List", "IC Project Type"],
		doctype="IC Project Type",
		accent="teal",
		priority=40,
		show=auth["show_settings"],
	)
	add(
		"settings",
		"ic_settings",
		_("Instacertify Settings"),
		_("Quote accept rules · defaults"),
		["Form", "IC Settings"],
		doctype="IC Settings",
		accent="coral",
		priority=50,
		show=auth["is_admin"],
	)
	add(
		"settings",
		"gst_settings",
		_("GST Settings"),
		_("India compliance configuration"),
		["Form", "GST Settings"],
		doctype="GST Settings",
		accent="coral",
		priority=60,
		show=auth["is_admin"] or auth["is_accounts"],
	)

	# ——— Everyday ———
	add(
		"everyday",
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
		priority=10,
		show=auth["show_helpdesk"],
	)
	add(
		"everyday",
		"calendar",
		_("Team Calendar"),
		_("Sessions & reminders"),
		["List", "Event", "Calendar"],
		doctype="Event",
		accent="teal",
		priority=20,
	)
	add(
		"everyday",
		"collab",
		_("Team Collaboration"),
		_("Project chats with teammates"),
		["team-collaboration"],
		accent="teal",
		priority=30,
		show=auth["show_collab"],
	)

	cards.sort(key=lambda c: (c.get("priority", 99), c.get("title") or ""))

	# Build section payloads (only sections the user may see, with at least one card)
	by_section: dict[str, list] = {}
	for c in cards:
		by_section.setdefault(c["section"], []).append(c)

	sections = []
	for meta in sections_meta:
		if not meta["show"]:
			continue
		sec_cards = by_section.get(meta["id"]) or []
		if not sec_cards:
			continue
		sections.append(
			{
				**meta,
				"cards": sec_cards,
				"count": len(sec_cards),
			}
		)

	# Flat cards kept for backward compatibility (QC / older clients)
	flat = [c for s in sections for c in s["cards"]]

	if not flat:
		flat = [
			{
				"id": "helpdesk",
				"section": "everyday",
				"title": _("Helpdesk"),
				"subtitle": _("Raise a complaint or query"),
				"route": ["List", "Helpdesk Ticket"],
				"doctype": "Helpdesk Ticket",
				"accent": "coral",
				"priority": 1,
			}
		]
		sections = [
			{
				"id": "everyday",
				"title": _("Everyday"),
				"subtitle": _("Getting started"),
				"accent": "teal",
				"show": True,
				"cards": flat,
				"count": len(flat),
			}
		]

	return {
		"user": frappe.session.user,
		"full_name": frappe.utils.get_fullname(frappe.session.user),
		"roles": sorted(roles),
		"authority": auth,
		"sections": sections,
		"cards": flat,
		"hint": _("Sections match your role — tap a tile to open."),
		"visibility": {
			"explore": True,
			"crm_panels": auth["show_crm"],
			"lead_hub": auth["show_crm"],
			"my_leads": auth["show_crm"],
			"projects": auth["show_projects"],
			"helpdesk": auth["show_helpdesk"],
			"collab": auth["show_collab"],
			"hrms": auth["show_hrms"],
			"billing": auth["show_billing"],
			"settings": auth["show_settings"],
		},
	}
