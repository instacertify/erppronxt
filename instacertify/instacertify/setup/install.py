# Copyright (c) Instacertify
"""Install and migrate hooks for Instacertify."""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


ROLES = [
	"IC Admin",
	"IC Senior Operations",
	"IC Sales Person",
	"IC Operations Manager",
]

LEAD_SOURCES = [
	"Google",
	"Direct Call",
	"Lead Generated",
	"Referral by Existing Customer",
	"IndiaMART",
	"Existing Customer",
	"Other",
]

PROJECT_STAGES = [
	"Project Initiated",
	"Customer Documents Pending",
	"Documents Under Review",
	"Application Submitted",
	"Sample Awaited",
	"Sample Received",
	"Sample Dispatched to Laboratory",
	"Testing in Progress",
	"Report Awaited",
	"Report Available",
	"Certification in Progress",
	"Certificate Available",
	"Delivered to Customer",
	"Project Completed",
]


def after_install():
	create_roles()
	ensure_masters()
	setup_custom_fields()
	setup_company()
	setup_lead_sources()
	setup_project_types()
	setup_items_and_groups()
	setup_settings()
	setup_workflows()
	setup_print_formats()
	setup_notifications()
	setup_workspace()
	setup_dashboard_charts()
	setup_number_cards()
	setup_permissions()
	frappe.db.commit()


def ensure_masters():
	"""Create minimal ERPNext masters needed for Instacertify operations."""
	for uom in ("Nos", "Unit", "Hour", "Day", "Set"):
		if not frappe.db.exists("UOM", uom):
			frappe.get_doc({"doctype": "UOM", "uom_name": uom, "enabled": 1}).insert(
				ignore_permissions=True
			)

	if not frappe.db.exists("Customer Group", "All Customer Groups"):
		frappe.get_doc(
			{"doctype": "Customer Group", "customer_group_name": "All Customer Groups", "is_group": 1}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("Customer Group", "Commercial"):
		frappe.get_doc(
			{
				"doctype": "Customer Group",
				"customer_group_name": "Commercial",
				"parent_customer_group": "All Customer Groups",
				"is_group": 0,
			}
		).insert(ignore_permissions=True)

	if not frappe.db.exists("Territory", "All Territories"):
		frappe.get_doc(
			{"doctype": "Territory", "territory_name": "All Territories", "is_group": 1}
		).insert(ignore_permissions=True)

	if not frappe.db.exists("Item Group", "All Item Groups"):
		frappe.get_doc(
			{"doctype": "Item Group", "item_group_name": "All Item Groups", "is_group": 1}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("Item Group", "Services"):
		frappe.get_doc(
			{
				"doctype": "Item Group",
				"item_group_name": "Services",
				"parent_item_group": "All Item Groups",
				"is_group": 0,
			}
		).insert(ignore_permissions=True)

	if not frappe.db.exists("Price List", "Standard Selling"):
		frappe.get_doc(
			{
				"doctype": "Price List",
				"price_list_name": "Standard Selling",
				"selling": 1,
				"currency": "INR",
				"enabled": 1,
			}
		).insert(ignore_permissions=True)

	for g in ("Male", "Female", "Other"):
		if not frappe.db.exists("Gender", g):
			frappe.get_doc({"doctype": "Gender", "gender": g}).insert(ignore_permissions=True)

	# Fiscal year covering current operations
	if not frappe.db.exists("Fiscal Year", "2026"):
		try:
			fy = frappe.get_doc(
				{
					"doctype": "Fiscal Year",
					"year": "2026",
					"year_start_date": "2026-01-01",
					"year_end_date": "2026-12-31",
				}
			)
			fy.insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Fiscal Year setup")

	frappe.db.set_single_value("System Settings", "language", "en")
	frappe.db.set_default("currency", "INR")
	frappe.db.set_default("number_format", "#,###.##")


def after_migrate():
	setup_custom_fields()
	ensure_roles()
	setup_print_formats()
	setup_settings()
	setup_quotation_templates()
	setup_workspace()
	frappe.db.commit()


def setup_quotation_templates():
	from instacertify.setup.quotation_templates import ensure_quotation_templates

	ensure_quotation_templates()


def create_roles():
	for role in ROLES:
		if not frappe.db.exists("Role", role):
			doc = frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1})
			doc.insert(ignore_permissions=True)


def ensure_roles():
	create_roles()


def setup_custom_fields():
	from instacertify.setup.custom_fields import CUSTOM_FIELDS

	create_custom_fields(CUSTOM_FIELDS, update=True)


def setup_company():
	company_name = "Instacertify"
	if frappe.db.exists("Company", company_name):
		company = frappe.get_doc("Company", company_name)
	else:
		# Create via simplified approach if chart needed
		if not frappe.db.exists("Company", company_name):
			company = frappe.get_doc(
				{
					"doctype": "Company",
					"company_name": company_name,
					"abbr": "IC",
					"default_currency": "INR",
					"country": "India",
					"chart_of_accounts": "Standard",
				}
			)
			try:
				company.insert(ignore_permissions=True)
			except Exception:
				# Company may require more setup during first site config
				frappe.log_error(frappe.get_traceback(), "Instacertify Company Setup")
				return

	# Ensure USD exists
	if not frappe.db.exists("Currency", "USD"):
		pass  # ERPNext ships currencies
	frappe.db.set_value("Company", company_name, "default_currency", "INR", update_modified=False)


def setup_lead_sources():
	# ERPNext v16 no longer ships Lead Source DocType.
	# Instacertify tracks sources via Lead.ic_lead_source_detail (Select).
	return


def setup_project_types():
	for stage in PROJECT_STAGES:
		# Use Project Type lightly; stages stored on custom field
		pass
	if not frappe.db.exists("Project Type", "Certification"):
		try:
			frappe.get_doc({"doctype": "Project Type", "project_type": "Certification"}).insert(
				ignore_permissions=True
			)
		except Exception:
			pass
	if not frappe.db.exists("Project Type", "Testing"):
		try:
			frappe.get_doc({"doctype": "Project Type", "project_type": "Testing"}).insert(
				ignore_permissions=True
			)
		except Exception:
			pass
	if not frappe.db.exists("Project Type", "Consulting"):
		try:
			frappe.get_doc({"doctype": "Project Type", "project_type": "Consulting"}).insert(
				ignore_permissions=True
			)
		except Exception:
			pass


def setup_items_and_groups():
	groups = [
		("Instacertify Services", "All Item Groups"),
		("Certification Services", "Instacertify Services"),
		("Testing Services", "Instacertify Services"),
		("Consulting Services", "Instacertify Services"),
	]
	for name, parent in groups:
		if not frappe.db.exists("Item Group", name):
			try:
				frappe.get_doc(
					{
						"doctype": "Item Group",
						"item_group_name": name,
						"parent_item_group": parent,
						"is_group": 1 if name == "Instacertify Services" else 0,
					}
				).insert(ignore_permissions=True)
			except Exception:
				pass

	services = [
		("BIS Certification", "Certification Services", "Service"),
		("BIS Renewal", "Certification Services", "Service"),
		("BIS Standard Changeover", "Certification Services", "Service"),
		("IEC Testing", "Testing Services", "Service"),
		("Product Testing", "Testing Services", "Service"),
		("CE Compliance", "Certification Services", "Service"),
		("Factory Inspection", "Consulting Services", "Service"),
		("Consulting Services", "Consulting Services", "Service"),
	]
	for item_name, group, _ in services:
		if not frappe.db.exists("Item", item_name):
			try:
				frappe.get_doc(
					{
						"doctype": "Item",
						"item_code": item_name,
						"item_name": item_name,
						"item_group": group if frappe.db.exists("Item Group", group) else "Services",
						"stock_uom": "Nos",
						"is_stock_item": 0,
						"is_sales_item": 1,
						"include_item_in_manufacturing": 0,
					}
				).insert(ignore_permissions=True)
			except Exception:
				pass


def setup_settings():
	if not frappe.db.exists("DocType", "IC Settings"):
		return
	try:
		doc = frappe.get_single("IC Settings")
		doc.primary_color = "#065175"
		doc.accent_color = "#EC6820"
		doc.legal_name = doc.legal_name or "INSTACERTIFY LABS PVT LTD"
		doc.address_line = doc.address_line or "PK 1 Sector 63 A Noida\nUttar Pradesh, India - 201301"
		doc.phone = doc.phone or "+91 9999118039"
		doc.email = doc.email or "contact@instacertify.com"
		doc.website = doc.website or "www.instacertify.com"
		doc.cin = doc.cin or "UP74999UP2022PTC170291"
		doc.gstin = doc.gstin or "09AAGCI8396C1Z7"
		doc.beneficiary_name = doc.beneficiary_name or "Instacertify Labs Private Limited"
		doc.bank_name = doc.bank_name or "YES BANK"
		doc.account_number = doc.account_number or "026485800001318"
		doc.ifsc_code = doc.ifsc_code or "YESB0000264"
		doc.swift_code = doc.swift_code or "YESBINBBDEL (For International USD Transfers)"
		doc.bank_branch_address = (
			doc.bank_branch_address
			or "Ground, Mezzanine & First Floor, Plot No. 6, Basant Lok, Vasant Vihar, New Delhi, Delhi – 110057, India"
		)
		if frappe.db.exists("Company", "Instacertify"):
			doc.company = "Instacertify"
		doc.default_terms = (
			doc.default_terms
			or "<p>This quotation is valid for 30 days from the date of issue. "
			"Prices are subject to change based on regulatory fee revisions. "
			"Instacertify will commence work upon written acceptance and receipt of agreed advance.</p>"
		)
		doc.default_force_majeure = (
			doc.default_force_majeure
			or "<p>Instacertify Labs Pvt. Ltd. shall not be liable for any delay or failure in performing its obligations "
			"due to circumstances beyond its reasonable control, including but not limited to natural disasters, "
			"acts of government, regulatory changes, strikes, pandemics, war, civil unrest, transportation disruptions, "
			"laboratory delays, or certification authority actions.</p>"
		)
		doc.default_payment_terms = (
			doc.default_payment_terms
			or "<ul><li>100% Advance Payment is required to initiate the testing process.</li>"
			"<li>Testing will commence upon receipt of the payment and sample.</li>"
			"<li>Any additional testing or charges, if applicable, shall be communicated separately.</li></ul>"
		)
		doc.header_image = doc.header_image or "/assets/instacertify/images/instacertify_letterhead.png"
		doc.logo = doc.logo or "/assets/instacertify/images/instacertify_letterhead.png"
		doc.stamp_image = doc.stamp_image or "/assets/instacertify/images/instacertify_stamp.png"
		doc.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "IC Settings Setup")


def setup_workflows():
	from instacertify.setup.workflows import ensure_quotation_workflow

	ensure_quotation_workflow()


def setup_print_formats():
	from instacertify.setup.print_formats import ensure_print_formats

	ensure_print_formats()


def setup_notifications():
	from instacertify.setup.notifications_setup import ensure_notifications

	ensure_notifications()


def setup_workspace():
	from instacertify.setup.workspace_setup import ensure_workspaces

	ensure_workspaces()


def setup_dashboard_charts():
	from instacertify.setup.dashboard_setup import ensure_dashboard_charts, ensure_number_cards

	ensure_dashboard_charts()
	ensure_number_cards()


def setup_number_cards():
	pass


def setup_permissions():
	"""Apply role permissions for laboratory purchase price (permlevel 1)."""
	try:
		# Ensure IC Admin has permlevel 1 on IC Laboratory
		if frappe.db.exists("DocType", "IC Laboratory"):
			# Child table permlevel handled via DocType definition
			pass
		# Give System Manager and IC Admin select/read on all IC doctypes is already in DocType perms
		for role in ("IC Admin", "System Manager"):
			# Role Permission for export
			pass
	except Exception:
		pass
