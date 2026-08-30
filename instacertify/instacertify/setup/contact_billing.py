# Copyright (c) Instacertify
"""Ensure ERPNext Contact.is_billing_contact column exists (quote / party lookup)."""

from __future__ import annotations

import frappe

_ENSURED = False


def ensure_contact_billing_fields():
	"""Create Address/Contact custom fields ERPNext expects for party billing lookups.

	Without `tabContact.is_billing_contact`, Quotation / Customer contact queries raise:
	MySQLdb.OperationalError: (1054, \"Unknown column 'tabContact.is_billing_contact'\")
	"""
	global _ENSURED
	if _ENSURED:
		return
	try:
		# Prefer ERPNext's canonical installer (creates Custom Field + DB column)
		from erpnext.setup.install import create_address_and_contact_custom_fields

		create_address_and_contact_custom_fields()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ensure_contact_billing_fields erpnext")
		_ensure_billing_contact_field_fallback()

	# Hard-check column in case Custom Field exists but migrate never ran ALTER
	_ensure_billing_contact_column()
	_ENSURED = True


def _ensure_billing_contact_field_fallback():
	if frappe.db.exists("Custom Field", "Contact-is_billing_contact"):
		return
	try:
		from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

		create_custom_fields(
			{
				"Contact": [
					{
						"label": "Is Billing Contact",
						"fieldname": "is_billing_contact",
						"fieldtype": "Check",
						"insert_after": "is_primary_contact",
					}
				]
			},
			update=True,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "fallback Contact-is_billing_contact")


def _ensure_billing_contact_column():
	"""Add the DB column if Custom Field meta exists but ALTER never landed."""
	try:
		cols = frappe.db.get_table_columns("Contact")
	except Exception:
		return
	if "is_billing_contact" in (cols or []):
		return
	try:
		frappe.db.sql(
			"ALTER TABLE `tabContact` ADD COLUMN `is_billing_contact` tinyint(4) NOT NULL DEFAULT 0"
		)
		frappe.clear_cache(doctype="Contact")
	except Exception:
		# Concurrent migrate / already added
		pass
