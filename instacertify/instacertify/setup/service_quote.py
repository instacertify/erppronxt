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
	# Shipping / GST / contact / payment — not required to create a service quote
	for field in (
		"shipping_rule",
		"taxes_and_charges",
		"tax_category",
		"payment_terms_template",
		"payment_schedule",
		"customer_address",
		"shipping_address_name",
		"company_address",
		"company_gstin",
		"place_of_supply",
		"gst_category",
		"billing_address_gstin",
		"contact_person",
		"contact_display",
		"contact_email",
		"contact_mobile",
		"customer_name",
		"address_display",
		"shipping_address",
		"company_contact_person",
		"tc_name",
		"terms",
	):
		try:
			_upsert_property_setter("Quotation", field, "reqd", "0", "Check")
		except Exception:
			pass

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

	# Assignees optional + collapsed (not on first-page mandatory path)
	try:
		sec = frappe.db.exists(
			"Custom Field", {"dt": "Quotation", "fieldname": "ic_section_assignees"}
		)
		if sec:
			frappe.db.set_value(
				"Custom Field",
				sec,
				{
					"label": "Additional Information — Assigned Team (optional)",
					"collapsible": 1,
					"description": "Optional. Assignees are not required to create a quotation.",
				},
				update_modified=False,
			)
		# collapsed may be stored as property on Section Break
		_upsert_property_setter("Quotation", "ic_section_assignees", "collapsible", "1", "Check")
		_upsert_property_setter("Quotation", "ic_section_assignees", "collapsed", "1", "Check")
		asn = frappe.db.exists("Custom Field", {"dt": "Quotation", "fieldname": "ic_assignees"})
		if asn:
			frappe.db.set_value(
				"Custom Field",
				asn,
				{
					"reqd": 0,
					"description": "Optional — add people later. Not required to save or share a quote.",
				},
				update_modified=False,
			)
	except Exception:
		pass

	# Quote No comes from naming series (document name) — never required on create
	try:
		qn = frappe.db.exists(
			"Custom Field", {"dt": "Quotation", "fieldname": "ic_quote_number"}
		)
		if qn:
			frappe.db.set_value(
				"Custom Field",
				qn,
				{
					"reqd": 0,
					"read_only": 1,
					"label": "Quote No (from series)",
					"description": "Auto-set from naming series after save (e.g. QTN-SRV-00001).",
				},
				update_modified=False,
			)
		_upsert_property_setter("Quotation", "ic_quote_number", "reqd", "0", "Check")
		_upsert_property_setter("Quotation", "naming_series", "reqd", "0", "Check")
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
		qty = cint(row.get("qty") or 0) or 1
		row.qty = qty
		try:
			row.total_amount = float(row.get("amount") or 0) * qty
		except Exception:
			pass

	# Free-text service lines on Items table: create non-stock Item from name/description
	for row in doc.get("items") or []:
		code = (row.get("item_code") or "").strip()
		label = (row.get("item_name") or row.get("description") or "").strip()
		if not code and label:
			row.item_code = ensure_nonstock_item_for_label(label)
			if not row.get("item_name"):
				row.item_name = label[:140]
			if not row.get("uom"):
				row.uom = "Nos"
			if not row.get("qty"):
				row.qty = 1

	# Draft with Customer only / Instacertify tables: ERPNext may still expect Items —
	# map free-text lines to non-stock Items, or add a zero placeholder (no inventory).
	has_items = any((row.get("item_code") or "").strip() for row in (doc.get("items") or []))
	if not has_items:
		mapped = False
		for row in doc.get("ic_cost_items") or []:
			qty = cint(row.get("qty") or 0) or 1
			unit = float(row.get("amount") or 0)
			amount = float(row.get("total_amount") or (unit * qty))
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
					"qty": qty,
					"rate": unit,
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


@frappe.whitelist()
def suggest_service_price(label: str | None = None, test_name: str | None = None, applicable_standard: str | None = None):
	"""Suggest a selling price for a free-text service from the lab purchase/scope library.

	Returns best (lowest purchase) matching offer, or empty when nothing matches.
	Also ensures a non-stock Item exists for the label so the quote line can use it.
	"""
	from instacertify.laboratory.api import get_labs_for_standard

	text = (label or test_name or "").strip()
	std = (applicable_standard or "").strip()
	offers = get_labs_for_standard(
		applicable_standard=std or None,
		test_name=text or None,
	)
	# Broaden: if no match on test_name alone, try using label as standard
	if not offers and text and not std:
		offers = get_labs_for_standard(applicable_standard=text)

	item_code = ensure_nonstock_item_for_label(text or "Customer Product / Service")
	if not offers:
		return {
			"item_code": item_code,
			"item_name": text or "Customer Product / Service",
			"suggested_selling_price": 0,
			"purchase_price": 0,
			"offers": [],
		}

	best = offers[0]
	return {
		"item_code": item_code,
		"item_name": text or best.get("test_name") or "Service",
		"suggested_selling_price": best.get("selling_price") or 0,
		"purchase_price": best.get("purchase_price") or 0,
		"currency": best.get("currency") or "INR",
		"laboratory": best.get("laboratory"),
		"laboratory_name": best.get("laboratory_name"),
		"lab_offer": best.get("value"),
		"offers": offers[:25],
	}
