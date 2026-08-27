# Copyright (c) Instacertify
"""Expose Sales Invoice + GSTR-1 / GSTR-3B filing tools in Instacertify navigation."""

from __future__ import annotations

import frappe

GSTR_DOCTYPES = (
	"GSTR-1",
	"GSTR 3B Report",
	"GST Return Log",
	"GST Settings",
	"Sales Invoice",
	"Payment Entry",
	"Sales Invoice Payment",
)

IC_ROLES = (
	"IC Admin",
	"IC Senior Operations",
	"IC Sales Person",
	"IC Operations Manager",
	"Accounts Manager",
	"Accounts User",
	"System Manager",
)


def ensure_gst_returns_access():
	"""Make invoicing + GSTR-1 / GSTR-3B generation & filing reachable."""
	_ensure_gst_settings_for_returns()
	_ensure_gst_india_workspace_visible()
	_grant_gstr_permissions()
	_ensure_instacertify_sidebar_gst_links()
	frappe.clear_cache()


def _ensure_gst_settings_for_returns():
	if not frappe.db.exists("DocType", "GST Settings"):
		return
	try:
		gs = frappe.get_single("GST Settings")
		# Enable local generation; API filing needs api_secret separately
		if hasattr(gs, "enable_gstr_1_api"):
			gs.enable_gstr_1_api = 1
		if hasattr(gs, "hsn_wise_tax_breakup"):
			gs.hsn_wise_tax_breakup = 1
		if hasattr(gs, "enable_overseas_transactions"):
			gs.enable_overseas_transactions = 1
		gs.flags.ignore_permissions = True
		gs.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "GST Settings returns")


def _ensure_gst_india_workspace_visible():
	if not frappe.db.exists("Workspace", "GST India"):
		return
	ws = frappe.get_doc("Workspace", "GST India")
	ws.is_hidden = 0
	ws.public = 1
	# Allow Instacertify + Accounts roles to see the workspace
	existing = {r.role for r in (ws.roles or [])}
	ws.roles = []
	for role in ("Accounts Manager", "Accounts User", "IC Admin", "IC Senior Operations", "System Manager"):
		if frappe.db.exists("Role", role):
			ws.append("roles", {"role": role})
	ws.flags.ignore_permissions = True
	ws.flags.ignore_links = True
	try:
		ws.save(ignore_permissions=True)
	except Exception:
		frappe.db.set_value("Workspace", "GST India", {"is_hidden": 0, "public": 1}, update_modified=False)


def _grant_gstr_permissions():
	"""Ensure IC roles can open GSTR-1 / GSTR 3B Report / GST Return Log."""
	for dt in ("GSTR-1", "GSTR 3B Report", "GST Return Log", "GST Settings", "Sales Invoice", "Payment Entry"):
		if not frappe.db.exists("DocType", dt):
			continue
		for role in IC_ROLES:
			if not frappe.db.exists("Role", role):
				continue
			_ensure_role_perm(
				dt,
				role,
				read=1,
				write=1 if dt != "GST Settings" or role in ("IC Admin", "System Manager", "Accounts Manager") else 0,
				create=1 if dt not in ("GST Settings",) else 0,
				report=1,
				export=1,
				print=1,
				select=1,
			)

	# Report GSTR-3B Details
	if frappe.db.exists("Report", "GSTR-3B Details"):
		for role in ("Accounts User", "Accounts Manager", "IC Admin", "IC Senior Operations", "Auditor"):
			if not frappe.db.exists("Role", role):
				continue
			if frappe.db.exists("Has Role", {"parent": "GSTR-3B Details", "parenttype": "Report", "role": role}):
				continue
			try:
				frappe.get_doc(
					{
						"doctype": "Has Role",
						"parent": "GSTR-3B Details",
						"parenttype": "Report",
						"parentfield": "roles",
						"role": role,
					}
				).insert(ignore_permissions=True)
			except Exception:
				pass


def _ensure_role_perm(dt: str, role: str, **perms):
	existing = frappe.db.exists("Custom DocPerm", {"parent": dt, "role": role, "permlevel": 0})
	values = {
		"read": perms.get("read", 0),
		"write": perms.get("write", 0),
		"create": perms.get("create", 0),
		"delete": perms.get("delete", 0),
		"submit": perms.get("submit", 0),
		"cancel": perms.get("cancel", 0),
		"amend": 0,
		"report": perms.get("report", 0),
		"export": perms.get("export", 0),
		"import": 0,
		"share": 0,
		"print": perms.get("print", 0),
		"email": 0,
		"select": perms.get("select", 0),
	}
	if existing:
		# Don't downgrade if already stronger
		cur = frappe.db.get_value(
			"Custom DocPerm",
			existing,
			["read", "write", "create", "select"],
			as_dict=True,
		)
		merged = {k: max(int(cur.get(k) or 0), int(values.get(k) or 0)) for k in ("read", "write", "create", "select")}
		values.update(merged)
		frappe.db.set_value("Custom DocPerm", existing, values, update_modified=False)
		return
	try:
		frappe.get_doc(
			{
				"doctype": "Custom DocPerm",
				"parent": dt,
				"parenttype": "DocType",
				"parentfield": "permissions",
				"role": role,
				"permlevel": 0,
				**values,
			}
		).insert(ignore_permissions=True)
	except Exception:
		pass


def _ensure_instacertify_sidebar_gst_links():
	"""Add GST & Invoicing section to Instacertify Home workspace sidebar if present."""
	sidebar_name = "Instacertify Home"
	if not frappe.db.exists("Workspace Sidebar", sidebar_name):
		# Create a minimal sidebar so GSTR is one click away
		try:
			sb = frappe.get_doc(
				{
					"doctype": "Workspace Sidebar",
					"title": sidebar_name,
					"header_icon": "file",
				}
			)
			sb.insert(ignore_permissions=True)
		except Exception:
			return

	sb = frappe.get_doc("Workspace Sidebar", sidebar_name)
	existing_links = {(i.link_to or "").strip() for i in (sb.items or [])}

	wanted = [
		("Section Break", "GST & Invoicing", None),
		("Link", "Sales Invoice", "Sales Invoice"),
		("Link", "Payment Entry", "Payment Entry"),
		("Link", "GSTR-1", "GSTR-1"),
		("Link", "GSTR-3B", "GSTR 3B Report"),
		("Link", "GST Return Log", "GST Return Log"),
		("Link", "GST Settings", "GST Settings"),
	]

	changed = False
	for typ, label, link_to in wanted:
		if link_to and link_to in existing_links:
			continue
		if typ == "Section Break" and any(
			(i.label or "") == label and i.type == "Section Break" for i in (sb.items or [])
		):
			continue
		if link_to and not frappe.db.exists("DocType", link_to):
			continue
		row = {
			"type": typ,
			"label": label,
			"link_type": "DocType" if link_to else None,
			"link_to": link_to,
			"child": 1 if typ == "Link" else 0,
			"collapsible": 1 if typ == "Section Break" else 0,
			"indent": 1 if typ == "Section Break" else 0,
			"keep_closed": 0,
		}
		sb.append("items", row)
		changed = True

	if changed:
		sb.flags.ignore_permissions = True
		sb.flags.ignore_links = True
		sb.flags.ignore_validate = True
		try:
			sb.save(ignore_permissions=True)
		except Exception:
			# Fall back to SQL insert of missing Link rows only
			for typ, label, link_to in wanted:
				if typ != "Link" or not link_to or link_to in existing_links:
					continue
				if not frappe.db.exists("DocType", link_to):
					continue
				frappe.get_doc(
					{
						"doctype": "Workspace Sidebar Item",
						"parent": sidebar_name,
						"parenttype": "Workspace Sidebar",
						"parentfield": "items",
						"type": "Link",
						"label": label,
						"link_type": "DocType",
						"link_to": link_to,
						"child": 1,
					}
				).insert(ignore_permissions=True)
