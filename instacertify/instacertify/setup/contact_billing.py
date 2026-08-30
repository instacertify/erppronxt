# Copyright (c) Instacertify
"""Ensure ERPNext Address/Contact columns used by get_party_details exist.

ERPNext party lookups need:
- Contact.is_billing_contact
- Address.tax_category
- Address.is_your_company_address

Missing columns raise MySQLdb.OperationalError 1054 when creating Quotation.
"""

from __future__ import annotations

import frappe

_ENSURED = False

# (doctype, fieldname, sql_type_default)
_REQUIRED_COLUMNS = (
	("Contact", "is_billing_contact", "tinyint(4) NOT NULL DEFAULT 0"),
	("Address", "tax_category", "varchar(140)"),
	("Address", "is_your_company_address", "tinyint(4) NOT NULL DEFAULT 0"),
)


def ensure_contact_billing_fields():
	"""Alias kept for existing callers."""
	ensure_party_address_contact_fields()


def ensure_party_address_contact_fields():
	"""Create Custom Fields + DB columns ERPNext expects for party/quote lookups."""
	global _ENSURED
	if _ENSURED and _all_columns_present():
		return

	try:
		from erpnext.setup.install import create_address_and_contact_custom_fields

		create_address_and_contact_custom_fields()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ensure_party_address_contact_fields erpnext")
		_ensure_custom_fields_fallback()

	_ensure_missing_columns()
	_ENSURED = _all_columns_present()


def _all_columns_present() -> bool:
	for doctype, fieldname, _sql in _REQUIRED_COLUMNS:
		try:
			cols = frappe.db.get_table_columns(doctype) or []
		except Exception:
			return False
		if fieldname not in cols:
			return False
	return True


def _ensure_custom_fields_fallback():
	try:
		from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

		create_custom_fields(
			{
				"Address": [
					{
						"label": "Tax Category",
						"fieldname": "tax_category",
						"fieldtype": "Link",
						"options": "Tax Category",
						"insert_after": "fax",
					},
					{
						"label": "Is Your Company Address",
						"fieldname": "is_your_company_address",
						"fieldtype": "Check",
						"default": "0",
						"insert_after": "linked_with",
					},
				],
				"Contact": [
					{
						"label": "Is Billing Contact",
						"fieldname": "is_billing_contact",
						"fieldtype": "Check",
						"insert_after": "is_primary_contact",
					},
				],
			},
			update=True,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "fallback Address/Contact custom fields")


def _ensure_missing_columns():
	"""ALTER TABLE when Custom Field meta exists but the column never landed."""
	for doctype, fieldname, sql_type in _REQUIRED_COLUMNS:
		try:
			cols = frappe.db.get_table_columns(doctype) or []
		except Exception:
			continue
		if fieldname in cols:
			continue
		try:
			frappe.db.sql(
				f"ALTER TABLE `tab{doctype}` ADD COLUMN `{fieldname}` {sql_type}"
			)
			frappe.clear_cache(doctype=doctype)
		except Exception:
			# Concurrent migrate / already added
			pass


@frappe.whitelist()
def ensure_party_fields():
	"""Desk can call this before get_party_details so quote create never 1054s."""
	ensure_party_address_contact_fields()
	return {"ok": 1, "ready": _all_columns_present()}


def _call_erpnext_party_fn(fn, *args, **kwargs):
	"""Forward only kwargs the ERPNext function accepts (strip cmd / form_dict junk)."""
	import inspect

	kwargs = dict(kwargs or {})
	for junk in ("cmd", "_", "csrf_token", "args"):
		kwargs.pop(junk, None)

	try:
		sig = inspect.signature(fn)
		allowed = {
			name
			for name, param in sig.parameters.items()
			if param.kind
			in (
				inspect.Parameter.POSITIONAL_OR_KEYWORD,
				inspect.Parameter.KEYWORD_ONLY,
			)
		}
		# If the function accepts **kwargs, pass everything remaining
		if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
			filtered = kwargs
		else:
			filtered = {k: v for k, v in kwargs.items() if k in allowed}
	except (TypeError, ValueError):
		filtered = {k: v for k, v in kwargs.items() if k != "cmd"}

	return fn(*args, **filtered)


@frappe.whitelist()
def get_party_details(*args, **kwargs):
	"""Wrap ERPNext get_party_details after ensuring Address/Contact columns."""
	ensure_party_address_contact_fields()
	from erpnext.accounts.party import get_party_details as _erpnext_get_party_details

	return _call_erpnext_party_fn(_erpnext_get_party_details, *args, **kwargs)


@frappe.whitelist()
def get_address_tax_category(*args, **kwargs):
	"""Wrap ERPNext get_address_tax_category after ensuring Address.tax_category."""
	ensure_party_address_contact_fields()
	from erpnext.accounts.party import get_address_tax_category as _erpnext_get_address_tax_category

	return _call_erpnext_party_fn(_erpnext_get_address_tax_category, *args, **kwargs)
