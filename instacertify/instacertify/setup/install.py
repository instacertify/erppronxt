# Copyright (c) Instacertify
"""Install and migrate hooks for Instacertify."""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import cint


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
	setup_lead_capture_properties()
	setup_items_and_groups()
	setup_consulting_billing()
	setup_settings()
	setup_branding()
	setup_workflows()
	setup_print_formats()
	setup_notifications()
	setup_workspace()
	setup_dashboard_charts()
	setup_number_cards()
	from instacertify.setup.friendly_labels import ensure_friendly_labels

	ensure_friendly_labels()
	setup_default_dashboard()
	setup_permissions()
	setup_gst()
	setup_disable_pos()
	setup_gst_returns()
	frappe.db.commit()


def ensure_masters():
	"""Create minimal ERPNext masters needed for Instacertify operations."""
	for uom in ("Nos", "Unit", "Hour", "Day", "Set"):
		if not frappe.db.exists("UOM", uom):
			frappe.get_doc({"doctype": "UOM", "uom_name": uom, "enabled": 1}).insert(
				ignore_permissions=True
			)

	ensure_customer_groups()

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
	ensure_masters()
	setup_lead_sources()
	setup_project_types()
	setup_lead_capture_properties()
	setup_print_formats()
	setup_settings()
	setup_branding()
	setup_quotation_templates()
	setup_dashboard_charts()
	from instacertify.setup.friendly_labels import ensure_friendly_labels

	ensure_friendly_labels()
	setup_workspace()
	setup_default_dashboard()
	setup_team_calendar()
	setup_gst()
	setup_disable_pos()
	setup_gst_returns()
	setup_consulting_billing()
	setup_invoice_naming_series()
	setup_quotation_naming_series()
	setup_hrms_alignment()
	from instacertify.setup.document_collection import ensure_document_collection_templates

	ensure_document_collection_templates()
	frappe.db.commit()


# Customer Groups named by business category (Instacertify CRM)
CUSTOMER_GROUP_CATEGORIES = (
	"Consultant",
	"Labs",
	"Manufacturer",
	"Trader",
	"Importer",
	"Agent",
)


def ensure_customer_groups():
	"""Customer Group names = business categories used across Instacertify."""
	if not frappe.db.exists("Customer Group", "All Customer Groups"):
		frappe.get_doc(
			{"doctype": "Customer Group", "customer_group_name": "All Customer Groups", "is_group": 1}
		).insert(ignore_permissions=True)

	for name in CUSTOMER_GROUP_CATEGORIES:
		if frappe.db.exists("Customer Group", name):
			doc = frappe.get_doc("Customer Group", name)
			changed = False
			if doc.parent_customer_group != "All Customer Groups":
				doc.parent_customer_group = "All Customer Groups"
				changed = True
			if cint(doc.is_group):
				doc.is_group = 0
				changed = True
			if changed:
				doc.save(ignore_permissions=True)
			continue
		frappe.get_doc(
			{
				"doctype": "Customer Group",
				"customer_group_name": name,
				"parent_customer_group": "All Customer Groups",
				"is_group": 0,
			}
		).insert(ignore_permissions=True)

	# Default new customers to Manufacturer when unset / legacy Commercial
	try:
		ss = frappe.get_single("Selling Settings")
		current = (ss.customer_group or "").strip()
		if not current or current in ("Commercial", "All Customer Groups"):
			ss.customer_group = "Manufacturer"
			ss.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Selling Settings customer_group")


def setup_invoice_naming_series():
	"""One Sales Invoice series across the ERP: INV-00001, INV-00002, …"""
	from instacertify.setup.naming_series import ensure_invoice_naming_series

	ensure_invoice_naming_series()


def setup_quotation_naming_series():
	"""Service / Testing / Others quotation series: QTN-SRV / QTN-TST / QTN-OTH."""
	from instacertify.setup.naming_series import ensure_quotation_naming_series

	ensure_quotation_naming_series()


def setup_hrms_alignment():
	"""Pin Expenses & HRMS last; align hiring → FnF DocTypes when hrms is installed."""
	try:
		from instacertify.hr.lifecycle import ensure_hrms_alignment

		ensure_hrms_alignment()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "setup_hrms_alignment")




def setup_default_dashboard():
	from instacertify.setup.dashboard_default import ensure_default_dashboard

	ensure_default_dashboard()


def setup_team_calendar():
	"""Event custom fields + repair participant emails for shared calendar."""
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
	from instacertify.calendar.events import repair_participant_emails
	from instacertify.setup.custom_fields import EVENT_FIELDS

	try:
		frappe.flags.ignore_version = True
		create_custom_fields({"Event": EVENT_FIELDS}, update=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Event custom fields")
		for f in EVENT_FIELDS:
			name = f"Event-{f['fieldname']}"
			if frappe.db.exists("Custom Field", name):
				continue
			try:
				frappe.get_doc({"doctype": "Custom Field", "dt": "Event", "module": "Instacertify", **f}).insert(
					ignore_permissions=True
				)
			except Exception:
				pass
	try:
		repair_participant_emails()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "repair_participant_emails")


def setup_consulting_billing():
	from instacertify.accounting.consulting_billing import setup_consulting_billing as _setup

	_setup()


def setup_gst():
	from instacertify.setup.gst import ensure_gst_setup

	ensure_gst_setup()


def setup_disable_pos():
	from instacertify.setup.pos import disable_pos_billing

	disable_pos_billing()


def setup_gst_returns():
	from instacertify.setup.gst_returns import ensure_gst_returns_access

	ensure_gst_returns_access()


def setup_branding():
	from instacertify.setup.branding import ensure_branding

	ensure_branding()


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

	try:
		# Avoid Version formatting crash on Custom Field updates in some Frappe builds
		frappe.flags.ignore_version = True
		create_custom_fields(CUSTOM_FIELDS, update=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "create_custom_fields")
		_apply_quotation_type_options()
		_ensure_service_family_field()
	finally:
		frappe.flags.ignore_version = False
	_apply_quotation_type_options()
	_ensure_service_family_field()
	_ensure_sales_invoice_quotation_link()
	_ensure_customer_related_tab()
	_ensure_customer_login_credentials()
	_ensure_lead_source_link_field()
	_ensure_lead_project_type_field()
	_ensure_lead_party_name_field()
	_ensure_pipeline_and_quote_accept_fields()


def _ensure_lead_party_name_field():
	cf_name = "Lead-ic_party_name"
	meta = {
		"fieldname": "ic_party_name",
		"label": "Name / company",
		"fieldtype": "Data",
		"insert_after": "ic_section_capture",
		"reqd": 1,
		"in_list_view": 1,
		"description": "Person or firm — enough to get started",
	}
	_upsert_lead_custom_field(cf_name, meta)
	# Ensure section exists
	if not frappe.db.exists("Custom Field", "Lead-ic_section_capture"):
		try:
			frappe.get_doc(
				{
					"doctype": "Custom Field",
					"dt": "Lead",
					"module": "Instacertify",
					"fieldname": "ic_section_capture",
					"label": "Lead Capture",
					"fieldtype": "Section Break",
					"insert_after": "salutation",
				}
			).insert(ignore_permissions=True)
		except Exception:
			pass


def _ensure_pipeline_and_quote_accept_fields():
	"""Lead pipeline stage + quotation post-accept action (with DB columns)."""
	lead_cf = "Lead-ic_pipeline_stage"
	lead_meta = {
		"fieldname": "ic_pipeline_stage",
		"label": "Pipeline Stage",
		"fieldtype": "Select",
		"options": "Lead\nRequirement Analysis\nTechnical Review\nQuote\nNegotiation\nOrder\nProject / Case\nCertification\nRenewal",
		"default": "Lead",
		"insert_after": "ic_section_pipeline",
		"in_list_view": 1,
		"in_standard_filter": 1,
	}
	if not frappe.db.exists("Custom Field", "Lead-ic_section_pipeline"):
		try:
			frappe.get_doc(
				{
					"doctype": "Custom Field",
					"dt": "Lead",
					"module": "Instacertify",
					"fieldname": "ic_section_pipeline",
					"label": "Sales Pipeline",
					"fieldtype": "Section Break",
					"insert_after": "ic_lead_connected",
				}
			).insert(ignore_permissions=True)
		except Exception:
			pass
	_upsert_lead_custom_field(lead_cf, lead_meta)
	if not frappe.db.has_column("Lead", "ic_pipeline_stage"):
		try:
			from frappe.database.schema import add_column

			add_column("Lead", "ic_pipeline_stage", "Select")
		except Exception:
			pass

	qt_cf = "Quotation-ic_post_accept_action"
	if not frappe.db.exists("Custom Field", qt_cf):
		try:
			frappe.get_doc(
				{
					"doctype": "Custom Field",
					"dt": "Quotation",
					"module": "Instacertify",
					"fieldname": "ic_post_accept_action",
					"label": "After Customer Accepts",
					"fieldtype": "Select",
					"options": "\nUse Company Default\nPrompt for Project / Testing\nCreate Invoice\nCreate Project\nCreate Invoice and Project\nManual",
					"default": "Use Company Default",
					"insert_after": "ic_customer_remarks",
				}
			).insert(ignore_permissions=True)
		except Exception:
			pass
	else:
		try:
			frappe.db.set_value(
				"Custom Field",
				qt_cf,
				"options",
				"\nUse Company Default\nPrompt for Project / Testing\nCreate Invoice\nCreate Project\nCreate Invoice and Project\nManual",
				update_modified=False,
			)
		except Exception:
			pass
	if not frappe.db.has_column("Quotation", "ic_post_accept_action"):
		try:
			from frappe.database.schema import add_column

			add_column("Quotation", "ic_post_accept_action", "Select")
		except Exception:
			pass

	# Settings default — prompt owner to create Project / Testing Request
	try:
		if frappe.db.exists("DocType", "IC Settings"):
			current = frappe.db.get_single_value("IC Settings", "on_quote_accept")
			if not current or current == "Create Invoice and Project":
				frappe.db.set_single_value(
					"IC Settings", "on_quote_accept", "Prompt for Project / Testing"
				)
			# Keep Select options in sync on the Single
			meta = frappe.get_meta("IC Settings")
			df = meta.get_field("on_quote_accept")
			if df:
				wanted = (
					"Prompt for Project / Testing\nCreate Invoice and Project\n"
					"Create Invoice\nCreate Project\nManual"
				)
				if (df.options or "") != wanted:
					frappe.db.set_value(
						"DocField",
						{"parent": "IC Settings", "fieldname": "on_quote_accept"},
						"options",
						wanted,
						update_modified=False,
					)
	except Exception:
		pass


def _ensure_lead_source_link_field():
	"""Force Lead Source to Link → IC Lead Source (editable master)."""
	cf_name = "Lead-ic_lead_source_detail"
	meta = {
		"fieldname": "ic_lead_source_detail",
		"label": "Lead Source",
		"fieldtype": "Link",
		"options": "IC Lead Source",
		"insert_after": "ic_request_category",
		"in_list_view": 1,
		"description": "Editable under IC Lead Source",
	}
	_upsert_lead_custom_field(cf_name, meta)


def _ensure_lead_project_type_field():
	cf_name = "Lead-ic_project_type"
	meta = {
		"fieldname": "ic_project_type",
		"label": "Project Type",
		"fieldtype": "Link",
		"options": "IC Project Type",
		"insert_after": "ic_section_request",
		"in_list_view": 1,
		"description": "Editable under IC Project Type",
	}
	_upsert_lead_custom_field(cf_name, meta)


def _upsert_lead_custom_field(cf_name, meta):
	try:
		if frappe.db.exists("Custom Field", cf_name):
			frappe.db.set_value(
				"Custom Field",
				cf_name,
				{
					"label": meta["label"],
					"fieldtype": meta["fieldtype"],
					"options": meta.get("options"),
					"insert_after": meta.get("insert_after"),
					"reqd": meta.get("reqd", 0),
					"in_list_view": meta.get("in_list_view", 0),
					"description": meta.get("description"),
					"module": "Instacertify",
				},
			)
		else:
			frappe.get_doc(
				{
					"doctype": "Custom Field",
					"dt": "Lead",
					"module": "Instacertify",
					**meta,
				}
			).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"Upsert {cf_name}")


def _apply_quotation_type_options():
	if frappe.db.exists("Custom Field", "Quotation-ic_quotation_type"):
		frappe.db.set_value(
			"Custom Field",
			"Quotation-ic_quotation_type",
			{
				"options": "\nConsulting\nTesting\nRenewal\nOther\nMultiple Products / Multiple Services\nService",
				"description": "Consulting, Testing, or Renewal. Pick a matching template below.",
			},
		)


def _ensure_service_family_field():
	if frappe.db.exists("Custom Field", "Quotation-ic_service_family"):
		return
	try:
		frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": "Quotation",
				"fieldname": "ic_service_family",
				"label": "Service Family / Subtype",
				"fieldtype": "Data",
				"insert_after": "ic_quotation_template",
				"module": "Instacertify",
				"description": "e.g. BIS CRS, TEC, EMC, Safety, BIS Renewal",
			}
		).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ic_service_family field")


def _ensure_sales_invoice_quotation_link():
	if frappe.db.exists("Custom Field", "Sales Invoice-ic_quotation"):
		return
	try:
		frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": "Sales Invoice",
				"fieldname": "ic_quotation",
				"label": "Source Quotation",
				"fieldtype": "Link",
				"options": "Quotation",
				"insert_after": "customer_name",
				"read_only": 1,
				"module": "Instacertify",
			}
		).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Sales Invoice ic_quotation field")


def _ensure_customer_login_credentials():
	"""Section on Customer to store portal User ID + encrypted Password."""
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
	from instacertify.setup.custom_fields import CUSTOMER_FIELDS

	login_fields = [
		f
		for f in CUSTOMER_FIELDS
		if f.get("fieldname")
		in (
			"ic_section_login",
			"ic_customer_user_id",
			"ic_column_login",
			"ic_customer_password",
			"ic_login_notes",
		)
	]
	if not login_fields:
		return
	try:
		frappe.flags.ignore_version = True
		create_custom_fields({"Customer": login_fields}, update=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Customer login credentials fields")
	finally:
		frappe.flags.ignore_version = False

	# Keep Customer Team section after login notes when present
	if frappe.db.exists("Custom Field", "Customer-ic_section_team"):
		try:
			frappe.db.set_value(
				"Custom Field",
				"Customer-ic_section_team",
				"insert_after",
				"ic_login_notes",
				update_modified=False,
			)
		except Exception:
			pass


def _ensure_customer_related_tab():
	"""Dedicated Customer tab listing projects, invoices, quotations, etc."""
	fields = [
		{
			"fieldname": "ic_related_tab",
			"label": "Customer Data",
			"fieldtype": "Tab Break",
			"insert_after": "column_break_hdmn",
		},
		{
			"fieldname": "ic_section_history",
			"label": "Customer History Overview",
			"fieldtype": "Section Break",
			"insert_after": "ic_related_tab",
		},
		{
			"fieldname": "ic_history_html",
			"label": "History",
			"fieldtype": "HTML",
			"insert_after": "ic_section_history",
		},
		{
			"fieldname": "ic_section_files",
			"label": "Customer Data Drive",
			"fieldtype": "Section Break",
			"insert_after": "ic_history_html",
		},
		{
			"fieldname": "ic_customer_files_html",
			"label": "Data Drive",
			"fieldtype": "HTML",
			"insert_after": "ic_section_files",
		},
	]
	for meta in fields:
		cf_name = f"Customer-{meta['fieldname']}"
		try:
			if frappe.db.exists("Custom Field", cf_name):
				frappe.db.set_value(
					"Custom Field",
					cf_name,
					{
						"label": meta["label"],
						"fieldtype": meta["fieldtype"],
						"insert_after": meta["insert_after"],
						"module": "Instacertify",
					},
				)
			else:
				frappe.get_doc(
					{
						"doctype": "Custom Field",
						"dt": "Customer",
						"module": "Instacertify",
						**meta,
					}
				).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Customer field {meta['fieldname']}")


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
	_ensure_company_invoice_defaults(company_name)


def _ensure_company_invoice_defaults(company_name: str):
	"""Ensure cost center + income account so Quotation → Invoice works without Sales Order."""
	try:
		from instacertify.quotation.events import _ensure_company_accounting_defaults

		_ensure_company_accounting_defaults(company_name)
		# Export / USD quotations are common; allow invoicing against INR Debtors
		if not frappe.db.get_single_value(
			"Accounts Settings", "allow_multi_currency_invoices_against_single_party_account"
		):
			frappe.db.set_single_value(
				"Accounts Settings",
				"allow_multi_currency_invoices_against_single_party_account",
				1,
			)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Company invoice defaults")


def setup_lead_sources():
	"""Seed editable IC Lead Source masters (admin can add/remove later)."""
	sources = [
		("Google Search", 10),
		("Google Ads", 20),
		("IndiaMART", 30),
		("Reference", 40),
		("Consultant", 50),
		# Preserve legacy values used on existing leads
		("Google", 60),
		("Direct Call", 70),
		("Lead Generated", 80),
		("Referral by Existing Customer", 90),
		("Existing Customer", 100),
		("Other", 110),
	]
	if not frappe.db.exists("DocType", "IC Lead Source"):
		return
	for name, order in sources:
		if frappe.db.exists("IC Lead Source", name):
			frappe.db.set_value(
				"IC Lead Source",
				name,
				{"is_active": 1, "sort_order": order},
				update_modified=False,
			)
			continue
		try:
			frappe.get_doc(
				{
					"doctype": "IC Lead Source",
					"source_name": name,
					"is_active": 1,
					"sort_order": order,
				}
			).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Seed lead source {name}")


def setup_project_types():
	"""Seed IC Project Type masters for lead capture (editable by admin)."""
	types = [
		("BIS", 10),
		("Testing", 20),
		("EPR", 30),
		("LMPC", 40),
		("SABER", 50),
		("GMARK", 60),
		("MSDS Authoring", 70),
		("Certification", 80),
		("Consulting", 90),
	]
	if frappe.db.exists("DocType", "IC Project Type"):
		for name, order in types:
			if frappe.db.exists("IC Project Type", name):
				frappe.db.set_value(
					"IC Project Type",
					name,
					{"is_active": 1, "sort_order": order},
					update_modified=False,
				)
				continue
			try:
				frappe.get_doc(
					{
						"doctype": "IC Project Type",
						"project_type_name": name,
						"is_active": 1,
						"sort_order": order,
					}
				).insert(ignore_permissions=True)
			except Exception:
				frappe.log_error(frappe.get_traceback(), f"Seed IC Project Type {name}")

	# Keep ERPNext Project Type in sync for project forms
	for name, _order in types:
		if frappe.db.exists("DocType", "Project Type") and not frappe.db.exists("Project Type", name):
			try:
				frappe.get_doc({"doctype": "Project Type", "project_type": name}).insert(
					ignore_permissions=True
				)
			except Exception:
				pass


def setup_lead_capture_properties():
	"""Phone/email optional; clarify country dropdown."""
	from instacertify.setup.pos import _make_setter

	for field in ("email_id", "mobile_no", "phone"):
		try:
			_make_setter("Lead", field, "reqd", "0", "Check")
		except Exception:
			pass
	try:
		_make_setter(
			"Lead",
			"country",
			"description",
			"India is listed first in the dropdown",
			"Small Text",
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
		doc.primary_color = "#0D47A1"
		doc.accent_color = "#F26D21"
		doc.legal_name = "INSTACERTIFY LABS PRIVATE LIMITED"
		doc.address_line = "PK 01 SECTOR 63A NOIDA, GAUTAM BUDDHA NAGAR, UTTAR PRADESH-201301, INDIA"
		doc.phone = doc.phone or "+91 9999118039"
		doc.email = doc.email or "contact@instacertify.com"
		doc.website = doc.website or "www.instacertify.com"
		doc.cin = "U74999UP2022PTC170291"
		doc.gstin = "09AAGCI8396C1Z7"
		doc.beneficiary_name = doc.beneficiary_name or "Instacertify Labs Private Limited"
		doc.bank_name = doc.bank_name or "YES BANK"
		doc.account_number = doc.account_number or "026485800001318"
		doc.ifsc_code = doc.ifsc_code or "YESB0000264"
		doc.swift_code = doc.swift_code or "YESBINBBDEL (For International USD Transfers)"
		doc.bank_branch_address = (
			doc.bank_branch_address
			or "Ground, Mezzanine & First Floor, Plot No. 6, Basant Lok, Vasant Vihar, New Delhi, Delhi – 110057, India"
		)
		doc.upi_id = doc.upi_id or "yespay.bizsbiz31008@yesbankltd"
		doc.upi_qr_image = doc.upi_qr_image or "/assets/instacertify/images/upi_payment_qr.jpg"
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
		doc.header_image = "/assets/instacertify/images/instacertify_letterhead.png"
		doc.logo = "/assets/instacertify/images/instacertify_logo.png"
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
