# Copyright (c) Instacertify
"""Accounting / billing document events."""

from __future__ import annotations

import frappe

from instacertify.accounting.billing import (
	apply_customer_billing_defaults,
	apply_transaction_billing_defaults,
)


def validate_customer(doc, method=None):
	apply_customer_billing_defaults(doc)


def validate_quotation(doc, method=None):
	if doc.quotation_to == "Customer" and doc.party_name:
		apply_transaction_billing_defaults(doc, customer_field="party_name")


def validate_sales_invoice(doc, method=None):
	apply_transaction_billing_defaults(doc, customer_field="customer")
