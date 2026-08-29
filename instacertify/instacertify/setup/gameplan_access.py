# Copyright (c) Instacertify
"""Ensure Gameplan is reachable from Instacertify Home / sidebar / desk icons."""

from __future__ import annotations

import frappe


GAMEPLAN_URL = "/g"
GAMEPLAN_LOGO = "/assets/gameplan/manifest/favicon-196.png"


def gameplan_installed() -> bool:
	try:
		return "gameplan" in frappe.get_installed_apps()
	except Exception:
		return False


def ensure_gameplan_access():
	"""Create / refresh Gameplan desktop icon, Home shortcut, and sidebar link."""
	if not gameplan_installed():
		return
	_ensure_desktop_icon()
	_ensure_home_sidebar_link()
	# Workspace shortcuts are rebuilt in workspace_setup; keep icon visible.
	frappe.clear_cache()


def _ensure_desktop_icon():
	"""Keep a visible Desk app icon that opens /g."""
	name = "Gameplan"
	vals = {
		"label": "Gameplan",
		"link": GAMEPLAN_URL,
		"app": "gameplan",
		"logo_url": GAMEPLAN_LOGO,
		"hidden": 0,
		"standard": 0,
	}
	# Frappe 16 Desktop Icon uses icon_type / link_type on some builds
	meta = frappe.get_meta("Desktop Icon")
	if meta.has_field("icon_type"):
		vals["icon_type"] = "App"
	if meta.has_field("link_type"):
		vals["link_type"] = "External"
	if meta.has_field("icon_image"):
		vals["icon_image"] = GAMEPLAN_LOGO

	if frappe.db.exists("Desktop Icon", name):
		doc = frappe.get_doc("Desktop Icon", name)
		changed = False
		for k, v in vals.items():
			if doc.get(k) != v:
				doc.set(k, v)
				changed = True
		if changed:
			doc.flags.ignore_permissions = True
			doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc({"doctype": "Desktop Icon", "name": name, **vals})
		doc.flags.ignore_permissions = True
		doc.insert(ignore_permissions=True)


def _ensure_home_sidebar_link():
	"""Add Gameplan URL near the top of Instacertify Home workspace sidebar."""
	sidebar_name = "Instacertify Home"
	if not frappe.db.exists("Workspace Sidebar", sidebar_name):
		return
	doc = frappe.get_doc("Workspace Sidebar", sidebar_name)
	existing = None
	for row in doc.items or []:
		if (row.label or "").strip().lower() == "gameplan" or (row.url or "") == GAMEPLAN_URL:
			existing = row
			break
	if existing:
		existing.link_type = "URL"
		existing.type = "Link"
		existing.url = GAMEPLAN_URL
		existing.icon = existing.icon or "message-circle"
		existing.link_to = None
	else:
		row = doc.append(
			"items",
			{
				"label": "Gameplan",
				"link_type": "URL",
				"type": "Link",
				"url": GAMEPLAN_URL,
				"icon": "message-circle",
			},
		)
		# Place right after Home
		items = list(doc.items or [])
		home_idx = next(
			(i for i, r in enumerate(items) if (r.label or "").lower() == "home"),
			0,
		)
		# Move last appended row to home_idx + 1
		items = [r for r in items if r is not row]
		items.insert(min(home_idx + 1, len(items)), row)
		doc.set("items", [])
		for r in items:
			doc.append(
				"items",
				{
					"label": r.label,
					"link_type": r.link_type,
					"type": r.type,
					"link_to": r.link_to,
					"url": r.url,
					"icon": r.icon,
					"child": r.child,
					"indent": r.indent,
				},
			)
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
