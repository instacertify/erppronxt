# Copyright (c) Instacertify
"""Disable POS billing — Instacertify uses Sales Invoice only."""

from __future__ import annotations

import frappe

POS_DOCTYPES = (
	"POS Invoice",
	"POS Profile",
	"POS Opening Entry",
	"POS Closing Entry",
	"POS Settings",
	"POS Invoice Merge Log",
)

POS_LABELS = {
	"pos",
	"point of sale",
	"point-of-sale",
	"pos profile",
	"pos invoice",
	"pos opening entry",
	"pos closing entry",
	"pos invoice merge log",
	"pos settings",
	"pos register",
}


def disable_pos_billing():
	"""Hide POS UI and block POS DocType usage site-wide."""
	_hide_sales_invoice_pos_fields()
	_strip_selling_workspace_pos()
	_strip_workspace_sidebar_pos("Selling")
	_strip_workspace_sidebar_pos("ERPNext Settings")
	_block_pos_permissions()
	_hide_pos_page()
	frappe.clear_cache()


def _hide_sales_invoice_pos_fields():
	for fieldname in ("is_pos", "pos_profile"):
		_make_setter(
			doctype="Sales Invoice",
			fieldname=fieldname,
			property="hidden",
			value="1",
			property_type="Check",
		)
		_make_setter(
			doctype="Sales Invoice",
			fieldname=fieldname,
			property="read_only",
			value="1",
			property_type="Check",
		)
	# Keep new invoices non-POS
	_make_setter(
		doctype="Sales Invoice",
		fieldname="is_pos",
		property="default",
		value="0",
		property_type="Text",
	)


def _make_setter(doctype: str, fieldname: str, property: str, value: str, property_type: str):
	name = f"{doctype}-{fieldname}-{property}"
	existing = frappe.db.exists("Property Setter", {"doc_type": doctype, "field_name": fieldname, "property": property})
	if existing:
		frappe.db.set_value(
			"Property Setter",
			existing,
			{"value": value, "module": "Instacertify"},
			update_modified=False,
		)
		return
	try:
		frappe.get_doc(
			{
				"doctype": "Property Setter",
				"doctype_or_field": "DocField",
				"doc_type": doctype,
				"field_name": fieldname,
				"property": property,
				"property_type": property_type,
				"value": value,
				"module": "Instacertify",
			}
		).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"POS property setter {name}")


def _strip_selling_workspace_pos():
	if not frappe.db.exists("Workspace", "Selling"):
		return
	ws = frappe.get_doc("Workspace", "Selling")
	changed = False

	# Remove POS card break + following POS links until next card
	new_links = []
	skip_card = False
	for link in ws.links or []:
		label = (link.label or "").strip().lower()
		link_to = (link.link_to or "").strip().lower()
		is_pos = label in POS_LABELS or link_to in POS_LABELS or "pos" == label or label.startswith("pos ")
		if link.type == "Card Break" and ("point of sale" in label or label == "pos"):
			skip_card = True
			changed = True
			continue
		if skip_card and link.type == "Card Break":
			skip_card = False
		if skip_card or is_pos:
			changed = True
			continue
		new_links.append(link)

	if changed:
		ws.set("links", [])
		for link in new_links:
			ws.append("links", link.as_dict())
		ws.flags.ignore_links = True
		ws.flags.ignore_validate = True
		ws.flags.ignore_permissions = True
		ws.save(ignore_permissions=True)


def _strip_workspace_sidebar_pos(sidebar_name: str):
	if not frappe.db.exists("Workspace Sidebar", sidebar_name):
		return
	# Direct SQL — sidesteps broken optional links on stock sidebars
	rows = frappe.db.sql(
		"""
		select name, label, link_to
		from `tabWorkspace Sidebar Item`
		where parent=%s
		""",
		sidebar_name,
		as_dict=True,
	)
	to_delete = []
	for row in rows:
		label = (row.label or "").strip().lower()
		link_to = (row.link_to or "").strip().lower()
		if (
			label in POS_LABELS
			or link_to in POS_LABELS
			or label == "pos"
			or link_to == "point-of-sale"
			or "pos " in label
			or label.endswith(" pos")
		):
			to_delete.append(row.name)
	if to_delete:
		frappe.db.delete("Workspace Sidebar Item", {"name": ["in", to_delete]})
		frappe.db.set_value("Workspace Sidebar", sidebar_name, "modified", frappe.utils.now(), update_modified=False)


def _block_pos_permissions():
	"""Remove create/read/write for non–System Manager roles on POS DocTypes."""
	for dt in POS_DOCTYPES:
		if not frappe.db.exists("DocType", dt):
			continue
		# Soft-hide from desk search for everyone via Custom DocPerm wipe of select for common roles
		roles = frappe.get_all(
			"Custom DocPerm",
			filters={"parent": dt},
			pluck="role",
		) or []
		# Also cover standard DocPerm by adding Custom DocPerm that deny for Sales/Accounts roles
		for role in (
			"Sales User",
			"Sales Manager",
			"Accounts User",
			"Accounts Manager",
			"All",
			"IC Admin",
			"IC Senior Operations",
			"IC Sales Person",
			"IC Operations Manager",
		):
			_set_no_perm(dt, role)

		# Ensure System Manager can still recover if needed
		if not frappe.db.exists("Custom DocPerm", {"parent": dt, "role": "System Manager"}):
			try:
				frappe.get_doc(
					{
						"doctype": "Custom DocPerm",
						"parent": dt,
						"parenttype": "DocType",
						"parentfield": "permissions",
						"role": "System Manager",
						"read": 1,
						"write": 1,
						"create": 1,
						"delete": 1,
						"report": 1,
						"export": 1,
						"share": 1,
						"print": 1,
						"email": 1,
					}
				).insert(ignore_permissions=True)
			except Exception:
				pass

		# Hide from AwesomeBar / desk by setting in_create if available via Property Setter on DocType
		_make_doctype_hidden(dt)


def _set_no_perm(dt: str, role: str):
	existing = frappe.db.exists("Custom DocPerm", {"parent": dt, "role": role, "permlevel": 0})
	values = {
		"read": 0,
		"write": 0,
		"create": 0,
		"delete": 0,
		"submit": 0,
		"cancel": 0,
		"amend": 0,
		"report": 0,
		"export": 0,
		"import": 0,
		"share": 0,
		"print": 0,
		"email": 0,
		"select": 0,
	}
	if existing:
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


def _make_doctype_hidden(dt: str):
	"""Hide DocType from AwesomeBar / module listing."""
	for prop, val, ptype in (
		("in_create", "1", "Check"),
		("restrict_to_domain", "Retail", "Data"),
	):
		existing = frappe.db.exists(
			"Property Setter", {"doc_type": dt, "property": prop, "doctype_or_field": "DocType"}
		)
		if existing:
			frappe.db.set_value(
				"Property Setter",
				existing,
				{"value": val, "module": "Instacertify"},
				update_modified=False,
			)
			continue
		try:
			frappe.get_doc(
				{
					"doctype": "Property Setter",
					"doctype_or_field": "DocType",
					"doc_type": dt,
					"property": prop,
					"property_type": ptype,
					"value": val,
					"module": "Instacertify",
				}
			).insert(ignore_permissions=True)
		except Exception:
			pass


def _hide_pos_page():
	if not frappe.db.exists("Page", "point-of-sale"):
		return
	# Remove page roles so users cannot open POS page
	frappe.db.sql("delete from `tabHas Role` where parent=%s and parenttype='Page'", "point-of-sale")
	# Restrict page to Retail domain if not already
	existing = frappe.db.exists(
		"Property Setter",
		{"doc_type": "Page", "property": "restrict_to_domain", "value": "Retail"},
	)
	# Page DocType uses field on Page document itself
	try:
		frappe.db.set_value("Page", "point-of-sale", "restrict_to_domain", "Retail", update_modified=False)
	except Exception:
		pass
