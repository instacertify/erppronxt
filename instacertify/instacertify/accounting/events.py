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
	if doc.meta.has_field("letter_head") and not doc.get("letter_head"):
		if frappe.db.exists("Letter Head", "Instacertify"):
			doc.letter_head = "Instacertify"
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
