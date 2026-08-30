# Copyright (c) Instacertify
"""Ensure ERPNext Contact billing field + Quotation payment defaults."""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


PAYMENT_TEMPLATE_NAME = "100% Advance"


def ensure_contact_billing_field():
	"""ERPNext party.get_party_details orders by Contact.is_billing_contact.

	If that custom field was never created (failed migrate / partial install),
	selecting a Customer on Quotation raises:
	Unknown column 'tabContact.is_billing_contact' in 'WHERE'
	"""
	create_custom_fields(
		{
			"Contact": [
				{
					"fieldname": "is_billing_contact",
					"fieldtype": "Check",
					"label": "Is Billing Contact",
					"insert_after": "is_primary_contact",
					"default": "0",
				}
			]
		},
		update=True,
	)
	# Hard guarantee column exists even if Custom Field already present but DB lagged
	if not frappe.db.has_column("Contact", "is_billing_contact"):
		frappe.db.sql(
			"ALTER TABLE `tabContact` ADD COLUMN `is_billing_contact` INT(1) NOT NULL DEFAULT 0"
		)


def ensure_payment_terms_advance():
	"""Create editable Payment Terms Template: 100% Advance."""
	if frappe.db.exists("Payment Terms Template", PAYMENT_TEMPLATE_NAME):
		return PAYMENT_TEMPLATE_NAME

	term_name = "100% Advance"
	if frappe.db.exists("DocType", "Payment Term") and not frappe.db.exists("Payment Term", term_name):
		try:
			frappe.get_doc(
				{
					"doctype": "Payment Term",
					"payment_term_name": term_name,
					"invoice_portion": 100,
					"due_date_based_on": "Day(s) after invoice date",
					"credit_days": 0,
					"description": "100% Advance",
				}
			).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "create Payment Term 100% Advance")

	terms_row = {
		"description": "100% Advance",
		"invoice_portion": 100,
		"due_date_based_on": "Day(s) after invoice date",
		"credit_days": 0,
	}
	if frappe.db.exists("Payment Term", term_name):
		terms_row["payment_term"] = term_name

	doc = frappe.get_doc(
		{
			"doctype": "Payment Terms Template",
			"template_name": PAYMENT_TEMPLATE_NAME,
			"allocate_payment_based_on_payment_terms": 1,
			"terms": [terms_row],
		}
	)
	doc.insert(ignore_permissions=True)
	return PAYMENT_TEMPLATE_NAME


def ensure_quotation_party_required():
	"""Customer / party name is mandatory when generating a quote."""
	from instacertify.setup.naming_series import _upsert_property_setter

	_upsert_property_setter(
		doctype="Quotation",
		field_name="party_name",
		property="reqd",
		value="1",
		property_type="Check",
	)
	_upsert_property_setter(
		doctype="Quotation",
		field_name="payment_terms_template",
		property="default",
		value=PAYMENT_TEMPLATE_NAME,
		property_type="Text",
	)


def ensure_quotation_billing_defaults():
	ensure_contact_billing_field()
	ensure_payment_terms_advance()
	ensure_quotation_party_required()
