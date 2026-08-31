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
	"""Keep Website Link / Login ID / Password in sync with the first portal row."""
	if not doc.meta.has_field("ic_portal_credentials"):
		return

	website = (doc.get("ic_website_link") or "").strip() if doc.meta.has_field("ic_website_link") else ""
	login_id = (doc.get("ic_customer_user_id") or "").strip() if doc.meta.has_field("ic_customer_user_id") else ""
	password = doc.get("ic_customer_password") if doc.meta.has_field("ic_customer_password") else None
	notes = (doc.get("ic_login_notes") or "").strip() if doc.meta.has_field("ic_login_notes") else ""

	rows = doc.get("ic_portal_credentials") or []

	# Seed first portal row from the simple fields when table is empty
	if not rows and (website or login_id or password or notes):
		portal_link = website
		if not portal_link and notes and (
			notes.startswith("http://") or notes.startswith("https://") or "." in notes.split()[0]
		):
			portal_link = notes.split()[0]
		doc.append(
			"ic_portal_credentials",
			{
				"portal_name": "Primary Portal",
				"portal_link": portal_link,
				"user_id": login_id,
				"password": password,
			},
		)
		rows = doc.get("ic_portal_credentials") or []

	# Push simple-field edits into the first row when present
	elif rows and (website or login_id or password):
		row = rows[0]
		if website:
			row.portal_link = website
		if login_id:
			row.user_id = login_id
		if password:
			row.password = password
		if not (row.get("portal_name") or "").strip():
			row.portal_name = "Primary Portal"

	# Pull first row into empty simple fields (so old table-only data shows up)
	if rows:
		row0 = rows[0]
		if doc.meta.has_field("ic_website_link") and not website and row0.get("portal_link"):
			doc.ic_website_link = row0.get("portal_link")
		if doc.meta.has_field("ic_customer_user_id") and not login_id and row0.get("user_id"):
			doc.ic_customer_user_id = row0.get("user_id")

	for i, row in enumerate(doc.get("ic_portal_credentials") or [], start=1):
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
