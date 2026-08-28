# Copyright (c) Instacertify
"""Make Instacertify Home the default dashboard across the ERP."""

from __future__ import annotations

import frappe


HOME_WORKSPACE = "Instacertify Home"


def ensure_default_dashboard():
	"""Pin Instacertify Home as the desk landing page for all system users."""
	if not frappe.db.exists("Workspace", HOME_WORKSPACE):
		from instacertify.setup.workspace_setup import ensure_workspaces

		ensure_workspaces()

	if not frappe.db.exists("Workspace", HOME_WORKSPACE):
		return

	# Always first in the workspace sidebar
	frappe.db.set_value(
		"Workspace",
		HOME_WORKSPACE,
		{"public": 1, "is_hidden": 0, "sequence_id": 0},
		update_modified=False,
	)

	# Deprioritize generic Welcome / Home so they don't steal first slot
	for name, seq in (("Welcome Workspace", 90), ("Home", 91), ("Build", 92)):
		if frappe.db.exists("Workspace", name):
			frappe.db.set_value("Workspace", name, "sequence_id", seq, update_modified=False)

	# Expenses & HRMS workspace — after core ops, before generic Welcome clutter
	if frappe.db.exists("Workspace", "HRMS & Expenses"):
		frappe.db.set_value(
			"Workspace",
			"HRMS & Expenses",
			{"public": 1, "is_hidden": 0, "sequence_id": 80},
			update_modified=False,
		)

	# Push stock HRMS workspaces slightly after ours if present
	for name, seq in (("HR", 81), ("Payroll", 82), ("Leaves", 83), ("Shift & Attendance", 84)):
		if frappe.db.exists("Workspace", name):
			frappe.db.set_value("Workspace", name, "sequence_id", seq, update_modified=False)

	# Explicit per-user default (Frappe login redirects here)
	users = frappe.get_all(
		"User",
		filters={"enabled": 1, "user_type": "System User"},
		pluck="name",
	)
	for user in users:
		if user in ("Guest", "Administrator"):
			# Still set Administrator so desk opens on Instacertify Home
			pass
		try:
			frappe.db.set_value(
				"User",
				user,
				"default_workspace",
				HOME_WORKSPACE,
				update_modified=False,
			)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"default_workspace {user}")

	# Global desk home preference
	try:
		frappe.db.set_default("desktop:home_page", "workspace")
	except Exception:
		pass

	# Cursor / legacy bookmarks often open /desktop — that path 404s on Frappe 16.
	# Always send it (and bare /app leftovers) to Instacertify Home on Desk.
	_ensure_desk_entry_redirects()

	# Soft-hide unused ERPNext module workspaces from cluttering new users?
	# Keep visible but later in sequence — already done above for Welcome/Home.


def _ensure_desk_entry_redirects():
	"""Map common dead entry URLs to Desk Instacertify Home."""
	home = "/desk/instacertify-home"
	wanted = (
		("/desktop", home),
		("/desktop/", home),
		("/Desktop", home),
		("/app/home", home),
		("/app/instacertify-home", home),
	)

	# Prefer Website Settings child table (what PathResolver reads)
	try:
		ws = frappe.get_single("Website Settings")
		existing = {(row.source or "").rstrip("/"): row for row in (ws.route_redirects or [])}
		changed = False
		for source, target in wanted:
			key = source.rstrip("/")
			row = existing.get(key)
			if row:
				if row.target != target:
					row.target = target
					row.redirect_http_status = "302"
					changed = True
				continue
			ws.append(
				"route_redirects",
				{
					"source": source,
					"target": target,
					"redirect_http_status": "302",
				},
			)
			changed = True
		if changed:
			ws.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "desk entry redirects")

	# Bust redirect cache so /desktop resolves immediately
	try:
		for source, _target in wanted:
			frappe.cache.hdel("website_redirects", source.strip("/") or "/")
			frappe.cache.hdel("website_redirects", source.lstrip("/") or "/")
			frappe.cache.hdel("website_redirects", source)
	except Exception:
		pass
