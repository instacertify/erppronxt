# Copyright (c) Instacertify
"""Service-business quotation rules: Customer-only mandatory, free-text products, non-stock."""

from __future__ import annotations

import re

import frappe
from frappe import _
from frappe.utils import cint


def ensure_service_quote_rules():
	"""Property setters + masters so quotes need only Customer; services are non-stock."""
	from instacertify.setup.naming_series import _upsert_property_setter

	# Only Customer / party is mandatory on Quotation
	_upsert_property_setter("Quotation", "party_name", "reqd", "1", "Check")
	_upsert_property_setter("Quotation", "quotation_to", "default", "Customer", "Text")
	_upsert_property_setter("Quotation", "quotation_to", "reqd", "0", "Check")
	_upsert_property_setter("Quotation", "order_type", "reqd", "0", "Check")
	# ERPNext Item table is optional for draft service quotes
	_upsert_property_setter("Quotation", "items", "reqd", "0", "Check")
	_upsert_property_setter("Quotation Item", "item_code", "reqd", "0", "Check")

	# Quotation Type optional (defaults when blank)
	try:
		name = frappe.db.exists(
			"Custom Field", {"dt": "Quotation", "fieldname": "ic_quotation_type"}
		)
		if name:
			frappe.db.set_value(
				"Custom Field",
				name,
				{
					"reqd": 0,
					"description": "Optional category. Only Customer is required to create a quote.",
				},
				update_modified=False,
			)
	except Exception:
		pass

	_ensure_generic_service_item()


def _ensure_generic_service_item():
	"""Catch-all non-stock Item for free-text customer products / services on quotes."""
	code = "CUSTOMER-SERVICE"
	if frappe.db.exists("Item", code):
		frappe.db.set_value("Item", code, {"is_stock_item": 0, "is_sales_item": 1}, update_modified=False)
		return code
	group = (
		"Consulting Services"
		if frappe.db.exists("Item Group", "Consulting Services")
		else ("Services" if frappe.db.exists("Item Group", "Services") else "All Item Groups")
	)
	hsn = None
	if frappe.db.exists("DocType", "GST HSN Code"):
		hsn = (
			frappe.db.get_value("GST HSN Code", {"hsn_code": "999900"}, "name")
			or frappe.db.get_value("GST HSN Code", {"hsn_code": ["like", "99%"]}, "name")
		)
	doc = frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": code,
			"item_name": "Customer Product / Service",
			"item_group": group,
			"stock_uom": "Nos",
			"is_stock_item": 0,
			"is_sales_item": 1,
			"is_purchase_item": 0,
			"include_item_in_manufacturing": 0,
			"description": "Generic non-stock line for customer products/services quoted by Instacertify (no inventory).",
		}
	)
	if hsn and doc.meta.has_field("gst_hsn_code"):
		doc.gst_hsn_code = hsn
	try:
		doc.insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ensure CUSTOMER-SERVICE item")
	return code


def ensure_nonstock_item_for_label(label: str | None = None) -> str:
	"""Return a non-stock Item code for a free-text product/service label (create if needed)."""
	_ensure_generic_service_item()
	text = (label or "").strip()
	if not text:
		return "CUSTOMER-SERVICE"

	# Prefer existing service items by name
	existing = frappe.db.get_value(
		"Item",
		{"item_name": text, "is_stock_item": 0, "disabled": 0},
		"name",
	)
	if existing:
		return existing

	slug = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").upper()[:40] or "SERVICE"
	code = f"SVC-{slug}"
	if frappe.db.exists("Item", code):
		return code

	group = (
		"Consulting Services"
		if frappe.db.exists("Item Group", "Consulting Services")
		else ("Services" if frappe.db.exists("Item Group", "Services") else "All Item Groups")
	)
	hsn = None
	if frappe.db.exists("DocType", "GST HSN Code"):
		hsn = (
			frappe.db.get_value("GST HSN Code", {"hsn_code": "999900"}, "name")
			or frappe.db.get_value("GST HSN Code", {"hsn_code": ["like", "99%"]}, "name")
		)
	doc = frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": code,
			"item_name": text[:140],
			"item_group": group,
			"stock_uom": "Nos",
			"is_stock_item": 0,
			"is_sales_item": 1,
			"is_purchase_item": 0,
			"include_item_in_manufacturing": 0,
			"description": text,
		}
	)
	if hsn and doc.meta.has_field("gst_hsn_code"):
		doc.gst_hsn_code = hsn
	try:
		doc.insert(ignore_permissions=True)
		return doc.name
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"create service item {code}")
		return "CUSTOMER-SERVICE"


def apply_quote_customer_only_rules(doc):
	"""Validate Quotation: Customer required; everything else optional for draft."""
	if not (doc.get("party_name") or "").strip():
		frappe.throw(_("Customer is mandatory to create a quotation"))
	if not doc.get("quotation_to"):
		doc.quotation_to = "Customer"
	# Prefer Customer for service quotes when blank party type
	if doc.quotation_to not in ("Customer", "Lead", "Prospect"):
		doc.quotation_to = "Customer"
	if not doc.get("ic_quotation_type"):
		doc.ic_quotation_type = "Consulting"
	if not (doc.get("order_type") or "").strip():
		doc.order_type = "Sales"
	# Soft defaults on cost lines so incomplete rows still save
	for row in doc.get("ic_cost_items") or []:
		if not (row.get("payment_destination") or "").strip():
			row.payment_destination = "Payable to Instacertify"
		if not (row.get("revenue_treatment") or "").strip():
			row.revenue_treatment = "Counted Revenue"
		if not (row.get("cost_component") or "").strip() and (row.get("particulars") or "").strip():
			row.cost_component = row.particulars

	# Draft with Customer only / Instacertify tables: ERPNext may still expect Items —
	# map free-text lines to non-stock Items, or add a zero placeholder (no inventory).
	has_items = any((row.get("item_code") or "").strip() for row in (doc.get("items") or []))
	if not has_items:
		mapped = False
		for row in doc.get("ic_cost_items") or []:
			amount = float(row.get("amount") or 0)
			label = (
				row.get("particulars")
				or row.get("description")
				or row.get("cost_component")
				or ""
			).strip()
			if not label and amount <= 0:
				continue
			label = label or "Service Charges"
			code = ensure_nonstock_item_for_label(label)
			doc.append(
				"items",
				{
					"item_code": code,
					"item_name": label[:140],
					"description": label,
					"qty": 1,
					"rate": amount,
					"uom": "Nos",
				},
			)
			mapped = True
		if not mapped:
			for row in doc.get("ic_test_items") or []:
				amount = float(row.get("testing_charges") or row.get("per_unit_charges") or 0)
				label = (
					row.get("test_name")
					or row.get("applicable_standard")
					or row.get("product_name")
					or ""
				).strip()
				if not label and amount <= 0:
					continue
				label = label or "Testing Service"
				code = ensure_nonstock_item_for_label(label)
				doc.append(
					"items",
					{
						"item_code": code,
						"item_name": label[:140],
						"description": label,
						"qty": 1,
						"rate": amount,
						"uom": "Nos",
					},
				)
				mapped = True
		if not mapped:
			for row in doc.get("ic_products") or []:
				label = (row.get("product_name") or "").strip()
				amount = float(row.get("estimated_value") or 0)
				if not label and amount <= 0:
					continue
				label = label or "Customer Product"
				code = ensure_nonstock_item_for_label(label)
				doc.append(
					"items",
					{
						"item_code": code,
						"item_name": label[:140],
						"description": label,
						"qty": 1,
						"rate": amount,
						"uom": "Nos",
					},
				)
				mapped = True
		if not mapped:
			code = _ensure_generic_service_item()
			doc.append(
				"items",
				{
					"item_code": code,
					"item_name": "Customer Product / Service",
					"description": "Service quote — add products, tests, or cost lines as needed.",
					"qty": 1,
					"rate": 0,
					"uom": "Nos",
				},
			)

	# Never require stock warehouses on service lines
	for row in doc.get("items") or []:
		if not row.get("item_code"):
			continue
		if not cint(frappe.db.get_value("Item", row.item_code, "is_stock_item")):
			for f in ("warehouse", "target_warehouse", "from_warehouse"):
				if hasattr(row, f):
					row.set(f, None)
