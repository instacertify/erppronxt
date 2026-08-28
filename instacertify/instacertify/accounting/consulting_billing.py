# Copyright (c) Instacertify
"""Consulting billing: buy lab services, sell to customers, buy assets — no warehouse."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, today


SERVICE_ITEM_DEFAULTS = {
	"is_stock_item": 0,
	"include_item_in_manufacturing": 0,
	"is_fixed_asset": 0,
}


def _default_service_hsn() -> str | None:
	if not frappe.db.exists("DocType", "GST HSN Code"):
		return None
	return (
		frappe.db.get_value("GST HSN Code", {"hsn_code": "999900"}, "name")
		or frappe.db.get_value("GST HSN Code", {"hsn_code": ["like", "99%"]}, "name")
		or frappe.db.get_value("GST HSN Code", {}, "name")
	)


def setup_consulting_billing():
	"""Seed service/asset masters and enforce non-stock consulting billing."""
	_ensure_item_groups()
	_ensure_service_items()
	_ensure_asset_category()
	_configure_stock_for_services()
	_ensure_supplier_group()
	# Ensure PI / Asset custom fields exist
	try:
		from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
		from instacertify.setup.custom_fields import CUSTOM_FIELDS

		subset = {
			k: CUSTOM_FIELDS[k]
			for k in ("Purchase Invoice", "Sales Invoice", "Asset")
			if k in CUSTOM_FIELDS
		}
		if subset:
			create_custom_fields(subset, update=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "consulting billing custom fields")


def _ensure_item_groups():
	groups = [
		("Instacertify Services", "All Item Groups", 1),
		("Certification Services", "Instacertify Services", 0),
		("Testing Services", "Instacertify Services", 0),
		("Consulting Services", "Instacertify Services", 0),
		("Laboratory Purchases", "Instacertify Services", 0),
		("Organizational Assets", "All Item Groups", 0),
	]
	for name, parent, is_group in groups:
		if frappe.db.exists("Item Group", name):
			continue
		if not frappe.db.exists("Item Group", parent):
			continue
		try:
			frappe.get_doc(
				{
					"doctype": "Item Group",
					"item_group_name": name,
					"parent_item_group": parent,
					"is_group": is_group,
				}
			).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Item Group {name}")


def _ensure_service_items():
	"""Non-stock sell + buy service items (no warehouse)."""
	items = [
		# Sell to customer
		{
			"item_code": "CERTIFICATION-SVC",
			"item_name": "Certification Service",
			"item_group": "Certification Services",
			"is_sales_item": 1,
			"is_purchase_item": 0,
			"description": "Sell certification / compliance services to customers (non-stock).",
		},
		{
			"item_code": "CONSULTING-SVC",
			"item_name": "Consulting Service",
			"item_group": "Consulting Services",
			"is_sales_item": 1,
			"is_purchase_item": 0,
			"description": "Sell consulting services to customers (non-stock).",
		},
		{
			"item_code": "TESTING-SVC-SELL",
			"item_name": "Testing Service (Customer)",
			"item_group": "Testing Services",
			"is_sales_item": 1,
			"is_purchase_item": 0,
			"description": "Sell testing coordination / pass-through testing to customers.",
		},
		# Buy from labs
		{
			"item_code": "LAB-TESTING-BUY",
			"item_name": "Laboratory Testing (Purchase)",
			"item_group": "Laboratory Purchases",
			"is_sales_item": 0,
			"is_purchase_item": 1,
			"description": "Buy testing / lab services from external laboratories (non-stock).",
		},
		{
			"item_code": "LAB-SERVICE-BUY",
			"item_name": "Laboratory Service (Purchase)",
			"item_group": "Laboratory Purchases",
			"is_sales_item": 0,
			"is_purchase_item": 1,
			"description": "Buy other lab services / NABL work from suppliers (non-stock).",
		},
	]
	for spec in items:
		group = spec["item_group"]
		if not frappe.db.exists("Item Group", group):
			group = "Services" if frappe.db.exists("Item Group", "Services") else "All Item Groups"
		existing = frappe.db.exists("Item", spec["item_code"])
		payload = {
			**SERVICE_ITEM_DEFAULTS,
			"item_name": spec["item_name"],
			"item_group": group,
			"stock_uom": "Nos",
			"is_sales_item": spec["is_sales_item"],
			"is_purchase_item": spec["is_purchase_item"],
			"description": spec["description"],
		}
		hsn = _default_service_hsn()
		if hsn and frappe.get_meta("Item").has_field("gst_hsn_code"):
			payload["gst_hsn_code"] = hsn
		try:
			if existing:
				frappe.db.set_value("Item", spec["item_code"], payload, update_modified=False)
			else:
				frappe.get_doc({"doctype": "Item", "item_code": spec["item_code"], **payload}).insert(
					ignore_permissions=True
				)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Service item {spec['item_code']}")
			# Retry under Services group
			try:
				payload["item_group"] = (
					"Services" if frappe.db.exists("Item Group", "Services") else "All Item Groups"
				)
				if not frappe.db.exists("Item", spec["item_code"]):
					frappe.get_doc(
						{"doctype": "Item", "item_code": spec["item_code"], **payload}
					).insert(ignore_permissions=True)
			except Exception:
				frappe.log_error(frappe.get_traceback(), f"Service item retry {spec['item_code']}")

	# Force existing Instacertify service catalog items to non-stock
	for name in frappe.get_all(
		"Item",
		filters={"item_group": ["in", [
			"Certification Services",
			"Testing Services",
			"Consulting Services",
			"Laboratory Purchases",
			"Services",
			"Instacertify Services",
		]]},
		pluck="name",
	):
		frappe.db.set_value(
			"Item",
			name,
			{"is_stock_item": 0, "include_item_in_manufacturing": 0},
			update_modified=False,
		)


def _ensure_asset_category():
	if not frappe.db.exists("DocType", "Asset Category"):
		return
	if frappe.db.exists("Asset Category", "IT Equipment"):
		return
	company = frappe.db.get_single_value("Global Defaults", "default_company") or "Instacertify"
	if not frappe.db.exists("Company", company):
		return
	try:
		fixed_asset = frappe.db.get_value(
			"Account", {"account_type": "Fixed Asset", "company": company, "is_group": 0}, "name"
		)
		accum = frappe.db.get_value(
			"Account",
			{"account_type": "Accumulated Depreciation", "company": company, "is_group": 0},
			"name",
		)
		dep_exp = frappe.db.get_value(
			"Account",
			{"account_type": "Depreciation", "company": company, "is_group": 0},
			"name",
		)
		doc = {
			"doctype": "Asset Category",
			"asset_category_name": "IT Equipment",
		}
		if fixed_asset and frappe.get_meta("Asset Category").has_field("accounts"):
			row = {"company_name": company, "fixed_asset_account": fixed_asset}
			if accum:
				row["accumulated_depreciation_account"] = accum
			if dep_exp:
				row["depreciation_expense_account"] = dep_exp
			doc["accounts"] = [row]
		frappe.get_doc(doc).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Asset Category IT Equipment")


def _configure_stock_for_services():
	"""Consulting mode: company accounts so service PIs work without warehouse stock flows."""
	company = frappe.db.get_single_value("Global Defaults", "default_company") or "Instacertify"
	if not frappe.db.exists("Company", company):
		return
	updates = {}
	if not frappe.db.get_value("Company", company, "stock_received_but_not_billed"):
		acc = frappe.db.get_value(
			"Account",
			{"company": company, "account_type": "Stock Received But Not Billed", "is_group": 0},
			"name",
		)
		if acc:
			updates["stock_received_but_not_billed"] = acc
	if not frappe.db.get_value("Company", company, "default_expense_account"):
		exp = frappe.db.get_value(
			"Account",
			{"company": company, "account_name": "Administrative Expenses", "is_group": 0},
			"name",
		) or frappe.db.get_value(
			"Account",
			{"company": company, "account_name": "Cost of Goods Sold", "is_group": 0},
			"name",
		)
		if exp:
			updates["default_expense_account"] = exp
	if updates:
		frappe.db.set_value("Company", company, updates, update_modified=False)


def _default_service_expense_account(company: str | None = None) -> str | None:
	company = company or frappe.db.get_single_value("Global Defaults", "default_company") or "Instacertify"
	return frappe.db.get_value("Company", company, "default_expense_account") or frappe.db.get_value(
		"Account",
		{"company": company, "account_name": "Administrative Expenses", "is_group": 0},
		"name",
	)


def _ensure_supplier_group():
	if not frappe.db.exists("DocType", "Supplier Group"):
		return
	if frappe.db.exists("Supplier Group", "All Supplier Groups") and not frappe.db.exists(
		"Supplier Group", "Laboratories"
	):
		try:
			frappe.get_doc(
				{
					"doctype": "Supplier Group",
					"supplier_group_name": "Laboratories",
					"parent_supplier_group": "All Supplier Groups",
					"is_group": 0,
				}
			).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Supplier Group Laboratories")


def strip_warehouse_from_service_items(doc):
	"""Clear warehouse / stock flags on non-stock (service) invoice lines."""
	if hasattr(doc, "update_stock"):
		# Consulting invoices should not update stock
		has_stock_item = False
		for row in doc.get("items") or []:
			if row.get("item_code") and frappe.db.get_value("Item", row.item_code, "is_stock_item"):
				has_stock_item = True
				break
		if not has_stock_item:
			doc.update_stock = 0

	for row in doc.get("items") or []:
		if not row.get("item_code"):
			continue
		is_stock = frappe.db.get_value("Item", row.item_code, "is_stock_item")
		if not is_stock:
			for wh_field in ("warehouse", "target_warehouse", "from_warehouse", "to_warehouse"):
				if hasattr(row, wh_field):
					row.set(wh_field, None)


@frappe.whitelist()
def ensure_supplier_for_laboratory(laboratory: str):
	"""Create or return Supplier linked to an IC Laboratory (for Purchase Invoice)."""
	if not laboratory or not frappe.db.exists("IC Laboratory", laboratory):
		frappe.throw(_("Laboratory is required"))

	lab = frappe.get_doc("IC Laboratory", laboratory)
	if lab.get("supplier") and frappe.db.exists("Supplier", lab.supplier):
		return {"supplier": lab.supplier, "created": False}

	supplier_name = (lab.laboratory_name or laboratory).strip()
	existing = frappe.db.exists("Supplier", supplier_name)
	if existing:
		lab.db_set("supplier", existing, update_modified=False)
		return {"supplier": existing, "created": False}

	group = "Laboratories" if frappe.db.exists("Supplier Group", "Laboratories") else None
	doc = frappe.get_doc(
		{
			"doctype": "Supplier",
			"supplier_name": supplier_name,
			"supplier_group": group,
			"supplier_type": "Company",
			"country": lab.get("country") or "India",
		}
	)
	doc.insert(ignore_permissions=True)
	lab.db_set("supplier", doc.name, update_modified=False)
	return {"supplier": doc.name, "created": True}


@frappe.whitelist()
def create_lab_purchase_invoice(
	laboratory: str | None = None,
	supplier: str | None = None,
	testing_request: str | None = None,
	project: str | None = None,
	amount: float | None = None,
	item_code: str | None = None,
	qty: float = 1,
	description: str | None = None,
):
	"""Create a non-stock Purchase Invoice for buying lab services."""
	if laboratory and not supplier:
		supplier = ensure_supplier_for_laboratory(laboratory)["supplier"]
	if testing_request and not laboratory:
		laboratory = frappe.db.get_value("IC Testing Request", testing_request, "laboratory")
		if laboratory and not supplier:
			supplier = ensure_supplier_for_laboratory(laboratory)["supplier"]
		if not project:
			project = frappe.db.get_value("IC Testing Request", testing_request, "project")

	if not supplier:
		frappe.throw(_("Supplier or Laboratory is required to buy lab services"))

	item_code = item_code or "LAB-TESTING-BUY"
	if not frappe.db.exists("Item", item_code):
		setup_consulting_billing()
	if not frappe.db.exists("Item", item_code):
		frappe.throw(_("Purchase service item {0} is missing").format(item_code))

	company = frappe.db.get_single_value("Global Defaults", "default_company") or "Instacertify"
	rate = flt(amount)
	if not rate and testing_request:
		# Prefer lab library buying price when available on TR
		rate = flt(
			frappe.db.get_value("IC Testing Request", testing_request, "suggested_selling_price")
		)
	if not rate:
		rate = 0

	desc = description
	if not desc and testing_request:
		tr = frappe.db.get_value(
			"IC Testing Request",
			testing_request,
			["title", "test_name", "product"],
			as_dict=True,
		)
		if tr:
			desc = f"{tr.test_name or tr.title or 'Lab testing'} — {tr.product or ''}".strip(" —")

	pi = frappe.get_doc(
		{
			"doctype": "Purchase Invoice",
			"supplier": supplier,
			"company": company,
			"posting_date": today(),
			"update_stock": 0,
			"items": [
				{
					"item_code": item_code,
					"qty": qty or 1,
					"rate": rate,
					"description": desc,
					"project": project,
					"expense_account": _default_service_expense_account(company),
				}
			],
		}
	)
	if pi.meta.has_field("ic_laboratory") and laboratory:
		pi.ic_laboratory = laboratory
	if pi.meta.has_field("ic_testing_request") and testing_request:
		pi.ic_testing_request = testing_request
	if pi.meta.has_field("ic_project") and project:
		pi.ic_project = project
	if pi.meta.has_field("ic_consulting_note"):
		pi.ic_consulting_note = _(
			"Consulting purchase: lab service (non-stock). No warehouse required."
		)

	strip_warehouse_from_service_items(pi)
	pi.insert(ignore_permissions=True)
	return {"name": pi.name, "supplier": supplier, "grand_total": pi.grand_total}


@frappe.whitelist()
def get_consulting_billing_summary():
	"""Quick counts for consulting buy / sell / assets (no warehouse)."""
	return {
		"sales_invoices": frappe.db.count("Sales Invoice", {"docstatus": ["<", 2]}),
		"purchase_invoices": frappe.db.count("Purchase Invoice", {"docstatus": ["<", 2]}),
		"lab_suppliers": frappe.db.count("Supplier", {"supplier_group": "Laboratories"})
		if frappe.db.exists("Supplier Group", "Laboratories")
		else frappe.db.count("Supplier"),
		"assets": frappe.db.count("Asset") if frappe.db.exists("DocType", "Asset") else 0,
		"mode": "consulting_no_warehouse",
		"buy_item": "LAB-TESTING-BUY",
		"sell_item": "CONSULTING-SVC",
	}
