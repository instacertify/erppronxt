# Copyright (c) Instacertify
"""Accounting / billing document events."""

from __future__ import annotations

import frappe

from instacertify.accounting.billing import (
	apply_customer_billing_defaults,
	apply_transaction_billing_defaults,
)
from instacertify.accounting.consulting_billing import strip_warehouse_from_service_items


def validate_customer(doc, method=None):
	apply_customer_billing_defaults(doc)
	_sync_customer_portal_credentials(doc)


def _sync_customer_portal_credentials(doc):
	"""Number portal rows and migrate legacy single user/password into the table once."""
	if not doc.meta.has_field("ic_portal_credentials"):
		return

	rows = doc.get("ic_portal_credentials") or []
	if not rows:
		legacy_user = (doc.get("ic_customer_user_id") or "").strip()
		legacy_pass = doc.get("ic_customer_password")
		legacy_notes = (doc.get("ic_login_notes") or "").strip()
		if legacy_user or legacy_pass or legacy_notes:
			portal_link = ""
			if legacy_notes and (
				legacy_notes.startswith("http://")
				or legacy_notes.startswith("https://")
				or "." in legacy_notes.split()[0]
			):
				portal_link = legacy_notes.split()[0]
			doc.append(
				"ic_portal_credentials",
				{
					"portal_name": "Primary Portal",
					"portal_link": portal_link,
					"user_id": legacy_user,
					"password": legacy_pass,
				},
			)
			rows = doc.get("ic_portal_credentials") or []

	for i, row in enumerate(rows, start=1):
		row.sno = i
		if not (row.get("portal_name") or "").strip():
			row.portal_name = f"Portal {i}"


def validate_quotation(doc, method=None):
	if doc.quotation_to == "Customer" and doc.party_name:
		apply_transaction_billing_defaults(doc, customer_field="party_name")
	strip_warehouse_from_service_items(doc)


def validate_sales_invoice(doc, method=None):
	# Instacertify does not use POS billing
	if getattr(doc, "is_pos", 0):
		doc.is_pos = 0
		doc.pos_profile = None
	from instacertify.setup.naming_series import apply_sales_invoice_series

	apply_sales_invoice_series(doc)
	apply_transaction_billing_defaults(doc, customer_field="customer")
	# Consulting: sell services without warehouse / stock update
	strip_warehouse_from_service_items(doc)


def before_insert_sales_invoice(doc, method=None):
	from instacertify.setup.naming_series import apply_sales_invoice_series

	apply_sales_invoice_series(doc)


def validate_purchase_invoice(doc, method=None):
	# Consulting: buy lab services / expenses without warehouse
	strip_warehouse_from_service_items(doc)
	if doc.meta.has_field("ic_consulting_note") and not doc.get("ic_consulting_note"):
		doc.ic_consulting_note = (
			"Consulting purchase — lab/vendor service (non-stock). Warehouse not required."
		)
