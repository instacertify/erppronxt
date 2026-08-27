# Copyright (c) Instacertify
"""Indian GST company setup (works with india_compliance)."""

from __future__ import annotations

import frappe

COMPANY = "Instacertify"
GSTIN = "09AAGCI8396C1Z7"
LEGAL_NAME = "INSTACERTIFY LABS PRIVATE LIMITED"
STATE = "Uttar Pradesh"
PINCODE = "201301"
ADDRESS_LINES = ("PK 01 SECTOR 63A NOIDA", "GAUTAM BUDDHA NAGAR")
CITY = "Noida"


def ensure_gst_setup():
	"""Configure Instacertify for Indian GST rules and overseas billing."""
	if not frappe.db.exists("Company", COMPANY):
		return

	_configure_company()
	_ensure_company_gst_address()
	_configure_gst_settings()
	_ensure_global_defaults_inr()
	_assign_default_item_tax_template()
	_sync_customer_gst_fields()


def _configure_company():
	values = {
		"default_currency": "INR",
		"country": "India",
	}
	if frappe.get_meta("Company").has_field("gstin"):
		values["gstin"] = GSTIN
	if frappe.get_meta("Company").has_field("gst_category"):
		values["gst_category"] = "Registered Regular"
	if frappe.get_meta("Company").has_field("default_gst_rate"):
		values["default_gst_rate"] = "18.0"

	frappe.db.set_value("Company", COMPANY, values, update_modified=False)

	# Keep IC Settings in sync for print letterheads
	if frappe.db.exists("DocType", "IC Settings"):
		try:
			settings = frappe.get_single("IC Settings")
			changed = False
			if hasattr(settings, "gstin") and settings.gstin != GSTIN:
				settings.gstin = GSTIN
				changed = True
			if hasattr(settings, "company_legal_name") and not settings.company_legal_name:
				settings.company_legal_name = LEGAL_NAME
				changed = True
			if changed:
				settings.save(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "IC Settings GST sync")


def _ensure_company_gst_address():
	existing = frappe.db.sql(
		"""
		select a.name
		from `tabAddress` a
		inner join `tabDynamic Link` dl on dl.parent = a.name
		where dl.link_doctype = 'Company' and dl.link_name = %s
		limit 1
		""",
		COMPANY,
	)
	if existing:
		addr_name = existing[0][0]
		updates = {
			"address_line1": ADDRESS_LINES[0],
			"address_line2": ADDRESS_LINES[1],
			"city": CITY,
			"state": STATE,
			"pincode": PINCODE,
			"country": "India",
			"is_your_company_address": 1,
		}
		if frappe.get_meta("Address").has_field("gstin"):
			updates["gstin"] = GSTIN
		if frappe.get_meta("Address").has_field("gst_state"):
			updates["gst_state"] = STATE
		if frappe.get_meta("Address").has_field("gst_category"):
			updates["gst_category"] = "Registered Regular"
		frappe.db.set_value("Address", addr_name, updates, update_modified=False)
		return

	doc = frappe.get_doc(
		{
			"doctype": "Address",
			"address_title": LEGAL_NAME,
			"address_type": "Billing",
			"address_line1": ADDRESS_LINES[0],
			"address_line2": ADDRESS_LINES[1],
			"city": CITY,
			"state": STATE,
			"pincode": PINCODE,
			"country": "India",
			"is_your_company_address": 1,
			"links": [{"link_doctype": "Company", "link_name": COMPANY}],
		}
	)
	if doc.meta.has_field("gstin"):
		doc.gstin = GSTIN
	if doc.meta.has_field("gst_state"):
		doc.gst_state = STATE
	if doc.meta.has_field("gst_category"):
		doc.gst_category = "Registered Regular"
	doc.insert(ignore_permissions=True)


def _configure_gst_settings():
	if not frappe.db.exists("DocType", "GST Settings"):
		return
	try:
		gs = frappe.get_single("GST Settings")
		# Export / foreign customers must be billable under GST rules
		if hasattr(gs, "enable_overseas_transactions"):
			gs.enable_overseas_transactions = 1
		if hasattr(gs, "round_off_gst_values"):
			gs.round_off_gst_values = 1
		if hasattr(gs, "hsn_wise_tax_breakup"):
			gs.hsn_wise_tax_breakup = 1
		gs.flags.ignore_permissions = True
		gs.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "GST Settings configure")


def _ensure_global_defaults_inr():
	frappe.db.set_single_value("Global Defaults", "default_company", COMPANY)
	frappe.db.set_single_value("Global Defaults", "default_currency", "INR")
	try:
		frappe.db.set_default("currency", "INR")
		frappe.db.set_default("company", COMPANY)
	except Exception:
		pass


def _assign_default_item_tax_template():
	"""Service items: SAC code + GST 18% item tax template."""
	template = "GST 18% - IC"
	# SAC for other professional / technical / business services
	default_sac = "998399"
	if frappe.db.exists("GST HSN Code", "998314"):
		default_sac = "998314"  # Other professional, technical and business services

	codes = frappe.get_all(
		"Item",
		filters={
			"is_sales_item": 1,
			"disabled": 0,
			"item_code": [
				"in",
				[
					"CONSULTING-SVC",
					"TESTING-SVC",
					"BIS Certification",
					"BIS Renewal",
					"IEC Testing",
					"Product Testing",
					"Consulting Services",
					"CE Compliance",
					"Factory Inspection",
				],
			],
		},
		pluck="name",
	)
	codes += frappe.get_all(
		"Item",
		filters={
			"is_sales_item": 1,
			"disabled": 0,
			"item_group": [
				"in",
				[
					"Certification Services",
					"Testing Services",
					"Consulting Services",
					"Instacertify Services",
					"Services",
				],
			],
		},
		pluck="name",
		limit=50,
	)

	for item_code in sorted(set(codes)):
		updates = {}
		if frappe.get_meta("Item").has_field("gst_hsn_code"):
			if not frappe.db.get_value("Item", item_code, "gst_hsn_code"):
				updates["gst_hsn_code"] = default_sac
		if updates:
			frappe.db.set_value("Item", item_code, updates, update_modified=False)

		if not frappe.db.exists("Item Tax Template", template):
			continue
		has = frappe.db.exists(
			"Item Tax", {"parent": item_code, "item_tax_template": template}
		)
		if has:
			continue
		try:
			item = frappe.get_doc("Item", item_code)
			item.append("taxes", {"item_tax_template": template, "tax_category": ""})
			item.flags.ignore_validate = True
			item.save(ignore_permissions=True)
		except Exception:
			# Direct child insert if Item validate (HSN) still blocks
			try:
				frappe.get_doc(
					{
						"doctype": "Item Tax",
						"parent": item_code,
						"parenttype": "Item",
						"parentfield": "taxes",
						"item_tax_template": template,
					}
				).insert(ignore_permissions=True)
			except Exception:
				frappe.log_error(frappe.get_traceback(), f"Item tax template {item_code}")


def _sync_customer_gst_fields():
	"""Keep Instacertify ic_gst_number aligned with india_compliance gstin."""
	if not frappe.get_meta("Customer").has_field("gstin"):
		return
	try:
		from india_compliance.gst_india.utils import validate_gstin
	except Exception:
		return

	rows = frappe.db.sql(
		"""
		select name, gstin, ic_gst_number
		from `tabCustomer`
		where ifnull(gstin,'') = '' and ifnull(ic_gst_number,'') != ''
		""",
		as_dict=True,
	)
	for row in rows:
		gstin = (row.ic_gst_number or "").strip().upper()
		try:
			validate_gstin(gstin)
		except Exception:
			continue
		frappe.db.set_value("Customer", row.name, "gstin", gstin, update_modified=False)
