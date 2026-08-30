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
	"Laboratories": "microscope",
	"Quote Format Library": "book-open",
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
	"Testing & Samples": "flask-conical",
	"Laboratories": "microscope",
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
	"testing_samples": "flask-conical",
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
	"Instacertify Home": {
		"icon": "layout-dashboard",
		"bg_color": "blue",
		"logo_url": "/assets/instacertify/images/favicon-48.png",
		"link_type": "Workspace Sidebar",
		"icon_type": "Link",
		"link_to": "Instacertify Home",
		"idx": 0,
	},
	"Lead Reminders": {
		"icon": "phone",
		"bg_color": "blue",
		"logo_url": "/assets/instacertify/images/favicon-48.png",
		"link_type": "External",
		"icon_type": "Link",
		"link": "/app/lead-reminders",
		"idx": 1,
	},
	"HRMS & Expenses": {
		"icon": "id-card",
		"bg_color": "gray",
		"logo_url": "/assets/instacertify/images/favicon-48.png",
		"link_type": "Workspace Sidebar",
		"icon_type": "Link",
		"link_to": "HRMS & Expenses",
		"idx": 80,
	},
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
	"""Create / refresh desk icons so Instacertify Home is one click from /desk."""
	if not frappe.db.exists("DocType", "Desktop Icon"):
		return
	meta = frappe.get_meta("Desktop Icon")
	for label, conf in DESKTOP_ICON_MAP.items():
		# Skip workspace icons when the workspace is missing
		link_to = conf.get("link_to")
		if link_to and conf.get("link_type") == "Workspace Sidebar":
			if not frappe.db.exists("Workspace Sidebar", link_to) and not frappe.db.exists(
				"Workspace", link_to
			):
				continue

		vals = {
			"label": label,
			"hidden": 0,
			"standard": 0,
			"icon": conf.get("icon") or "file",
		}
		if meta.has_field("bg_color") and conf.get("bg_color"):
			vals["bg_color"] = conf["bg_color"]
		if meta.has_field("logo_url") and conf.get("logo_url"):
			vals["logo_url"] = conf["logo_url"]
		if meta.has_field("icon_image") and conf.get("logo_url"):
			vals["icon_image"] = conf["logo_url"]
		if meta.has_field("icon_type"):
			vals["icon_type"] = conf.get("icon_type") or "Link"
		if meta.has_field("link_type"):
			vals["link_type"] = conf.get("link_type") or "Workspace Sidebar"
		if meta.has_field("link_to") and conf.get("link_to"):
			vals["link_to"] = conf["link_to"]
		if meta.has_field("link") and conf.get("link"):
			vals["link"] = conf["link"]
		if meta.has_field("idx") and conf.get("idx") is not None:
			vals["idx"] = conf["idx"]
		if meta.has_field("app"):
			vals["app"] = "instacertify"

		try:
			if frappe.db.exists("Desktop Icon", label):
				doc = frappe.get_doc("Desktop Icon", label)
				changed = False
				for k, v in vals.items():
					if doc.get(k) != v:
						doc.set(k, v)
						changed = True
				# Always unhide Instacertify Home
				if doc.hidden:
					doc.hidden = 0
					changed = True
				if changed:
					doc.flags.ignore_permissions = True
					doc.save(ignore_permissions=True)
			else:
				doc = frappe.get_doc({"doctype": "Desktop Icon", "name": label, **vals})
				doc.flags.ignore_permissions = True
				doc.insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"desktop icon {label}")


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
