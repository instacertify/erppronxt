# Copyright (c) Instacertify
"""Ensure sidebar, desktop, and shortcut icons are set and space-aligned."""

from __future__ import annotations

import frappe

# Lucide icon names (must exist in frappe/public/icons/lucide)
SHORTCUT_ICONS = {
	"Leads": "users",
	"Customers": "building",
	"Quotations": "file-text",
	"Projects": "briefcase",
	"Project Board": "layout-grid",
	"Team Collaboration": "message-circle",
	"Team Calendar": "calendar",
	"Testing & Samples": "flask-conical",
	"Testing Requests": "flask-conical",
	"Laboratories": "microscope",
	"Quote Format Library": "book-open",
	"Samples": "package",
	"Documents Collection Sheets": "clipboard-list",
	"Document Collection Library": "folder-open",
	"Sample Dispatch Sheets": "truck",
	"Helpdesk": "headset",
	"Sales Invoice": "receipt",
	"Purchase Invoice": "shopping-cart",
	"Asset": "boxes",
	"GSTR-1": "badge-indian-rupee",
	"GSTR-3B": "calculator",
	"GST Settings": "settings",
	"HRMS Lifecycle": "id-card",
	"File Expense": "wallet",
	"Lead Reminders": "phone",
	"Job Applicant": "user-plus",
	"Job Offer": "file-check",
	"Employee": "square-user-round",
	"Employee Onboarding": "user-star",
	"Joining Letters": "mail",
	"Attendance": "calendar-check",
	"Leave Application": "plane",
	"Salary Slip": "banknote",
	"Payroll Entry": "circle-dollar-sign",
	"Expense Claim": "wallet",
	"Employee Separation": "log-out",
	"Full and Final": "scale",
}

SIDEBAR_ICONS = {
	"Home": "layout-dashboard",
	"Gameplan": "message-circle",
	"Leads": "users",
	"Customers": "building",
	"Quotations": "file-text",
	"Projects": "briefcase",
	"Testing Requests": "flask-conical",
	"Laboratories": "microscope",
	"Samples": "package",
	"Document Requests": "clipboard-list",
	"Documents Collection Sheets": "clipboard-list",
	"Sales Invoice": "receipt",
	"Payment Entry": "banknote",
	"GSTR-1": "badge-indian-rupee",
	"GSTR-3B": "calculator",
	"GST Return Log": "file-spreadsheet",
	"GST Settings": "settings",
	"Lead Reminders": "phone",
	"Team Calendar": "calendar",
	"Team Collaboration": "message-circle",
	"Helpdesk": "headset",
	"File Expense": "wallet",
	"HRMS Lifecycle": "id-card",
	"GST & Invoicing": "landmark",
}

EXPLORE_ICONS = {
	"leads": "users",
	"quotations": "file-text",
	"quote_library": "book-open",
	"customers": "building",
	"projects": "briefcase",
	"project_board": "layout-grid",
	"labs": "microscope",
	"testing": "flask-conical",
	"samples": "package",
	"documents": "clipboard-list",
	"sample_dispatch": "truck",
	"helpdesk": "headset",
	"calendar": "calendar",
	"collab": "message-circle",
	"invoices": "receipt",
	"purchase": "shopping-cart",
	"hr_lifecycle": "id-card",
	"expenses": "wallet",
	"assets": "boxes",
}

DESKTOP_ICON_MAP = {
	"Instacertify Home": {"icon": "layout-dashboard", "bg_color": "Blue"},
	"HRMS & Expenses": {"icon": "id-card", "bg_color": "Orange"},
	"Gameplan": {"icon": "message-circle", "bg_color": "Green"},
}


def apply_shortcut_icons(shortcuts: list[dict]) -> list[dict]:
	"""Return shortcut rows with lucide icons filled in."""
	out = []
	for s in shortcuts:
		row = dict(s)
		if not row.get("icon"):
			row["icon"] = SHORTCUT_ICONS.get(row.get("label") or "", "file")
		out.append(row)
	return out


def ensure_navigation_icons():
	"""Fill missing icons on Desktop Icon, Workspace, Sidebar, and Shortcuts."""
	_ensure_desktop_icons()
	_ensure_workspace_icons()
	_ensure_sidebar_icons("Instacertify Home", header="layout-dashboard")
	_ensure_sidebar_icons("HRMS & Expenses", header="id-card")
	_ensure_shortcut_icons_on_workspace("Instacertify Home")
	_ensure_shortcut_icons_on_workspace("HRMS & Expenses")


def _ensure_desktop_icons():
	for label, conf in DESKTOP_ICON_MAP.items():
		if not frappe.db.exists("Desktop Icon", label):
			continue
		vals = {}
		cur_icon = frappe.db.get_value("Desktop Icon", label, "icon")
		if not cur_icon:
			vals["icon"] = conf["icon"]
		cur_bg = frappe.db.get_value("Desktop Icon", label, "bg_color")
		if not cur_bg and conf.get("bg_color"):
			vals["bg_color"] = conf["bg_color"]
		if vals:
			frappe.db.set_value("Desktop Icon", label, vals, update_modified=False)


def _ensure_workspace_icons():
	for name, icon in (
		("Instacertify Home", "layout-dashboard"),
		("HRMS & Expenses", "id-card"),
	):
		if not frappe.db.exists("Workspace", name):
			continue
		if not frappe.db.get_value("Workspace", name, "icon"):
			frappe.db.set_value("Workspace", name, "icon", icon, update_modified=False)


def _ensure_sidebar_icons(sidebar_name: str, header: str):
	if not frappe.db.exists("Workspace Sidebar", sidebar_name):
		return
	sb = frappe.get_doc("Workspace Sidebar", sidebar_name)
	changed = False
	if not sb.header_icon:
		sb.header_icon = header
		changed = True
	for row in sb.items or []:
		label = (row.label or "").strip()
		wanted = SIDEBAR_ICONS.get(label)
		if row.type == "Section Break":
			if wanted and row.icon != wanted:
				row.icon = wanted
				changed = True
			continue
		# Always set a concrete icon so child rows don't render empty slots
		icon = wanted or SHORTCUT_ICONS.get(label) or "file"
		if row.icon != icon:
			row.icon = icon
			changed = True
	if changed:
		sb.flags.ignore_permissions = True
		sb.flags.ignore_links = True
		sb.flags.ignore_validate = True
		try:
			sb.save(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"sidebar icons {sidebar_name}")


def _ensure_shortcut_icons_on_workspace(workspace_name: str):
	if not frappe.db.exists("Workspace", workspace_name):
		return
	ws = frappe.get_doc("Workspace", workspace_name)
	changed = False
	for row in ws.shortcuts or []:
		label = (row.label or "").strip()
		wanted = SHORTCUT_ICONS.get(label) or "file"
		if row.icon != wanted:
			row.icon = wanted
			changed = True
	if changed:
		ws.flags.ignore_permissions = True
		try:
			ws.save(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"shortcut icons {workspace_name}")
