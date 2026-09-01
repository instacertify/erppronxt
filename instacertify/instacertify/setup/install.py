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
	"IC Ops Executive",
	"IC Sales Manager",
	"IC Sales Executive",
	"IC Projects Manager",
	"IC Projects Executive",
	"IC HR Manager",
	"IC HR Executive",
	"IC Finance Manager",
	"IC Finance Executive",
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
	from instacertify.setup.role_profiles import ensure_role_profiles

	ensure_role_profiles()
	ensure_masters()
	setup_custom_fields()
	setup_company()
	setup_lead_sources()
	setup_project_types()
	setup_lead_capture_properties()
	setup_items_and_groups()
	setup_consulting_billing()
	setup_service_quote_rules()
	setup_contact_billing_fields()
	setup_settings()
	from instacertify.accounting.banking import ensure_bank_accounts

	ensure_bank_accounts()
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
	from instacertify.setup.role_profiles import ensure_role_profiles

	ensure_role_profiles()
	ensure_masters()
	setup_lead_sources()
	setup_project_types()
	setup_lead_capture_properties()
	setup_print_formats()
	setup_settings()
	from instacertify.accounting.banking import ensure_bank_accounts

	ensure_bank_accounts()
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
	setup_service_quote_rules()
	setup_contact_billing_fields()
	setup_invoice_naming_series()
	setup_quotation_naming_series()
	setup_hrms_alignment()
	from instacertify.setup.document_collection import ensure_document_collection_templates

	ensure_document_collection_templates()
	_backfill_template_display_names()
	frappe.db.commit()


def _backfill_template_display_names():
	"""Copy template_name → display_name where the user-facing label is empty."""
	for doctype in ("IC Quotation Template", "IC Document Checklist Template"):
		if not frappe.db.exists("DocType", doctype):
			continue
		meta = frappe.get_meta(doctype)
		if not meta.has_field("display_name"):
			continue
		frappe.db.sql(
			f"""
			UPDATE `tab{doctype}`
			SET display_name = template_name
			WHERE IFNULL(display_name, '') = ''
			  AND IFNULL(template_name, '') != ''
			"""
		)


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


def setup_service_quote_rules():
	"""Customer-only mandatory quotes; free-text non-stock products/services."""
	from instacertify.setup.service_quote import ensure_service_quote_rules

	ensure_service_quote_rules()


def setup_contact_billing_fields():
	"""Ensure Address.tax_category + Contact.is_billing_contact (ERPNext party/quote)."""
	from instacertify.setup.contact_billing import ensure_party_address_contact_fields

	ensure_party_address_contact_fields()


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
	# Custom Field rows can exist without DB columns (e.g. after partial sync).
	# Force schema update so save/submit never hits Unknown column in SET.
	_sync_custom_field_columns(list(CUSTOM_FIELDS.keys()))
	_apply_quotation_type_options()
	_ensure_service_family_field()
	_ensure_sales_invoice_quotation_link()
	_ensure_customer_related_tab()
	_ensure_customer_login_credentials()
	_ensure_lead_source_link_field()
	_ensure_lead_project_type_field()
	_ensure_lead_party_name_field()
	_ensure_pipeline_and_quote_accept_fields()
	_ensure_quotation_bank_account_field()
	_ensure_quotation_print_section_fields()
	_ensure_quotation_section_order_field()
	_ensure_quotation_commercials_layout()
	_ensure_quotation_share_token_column()
	_ensure_test_item_samples_editable()
	_ensure_test_lines_on_consulting()
	_ensure_test_item_price_columns()


def _ensure_quotation_section_order_field():
	"""Hidden JSON/CSV field storing Print section sequence for each quotation."""
	cf_name = "Quotation-ic_section_order"
	try:
		if not frappe.db.exists("Custom Field", cf_name):
			frappe.get_doc(
				{
					"doctype": "Custom Field",
					"dt": "Quotation",
					"module": "Instacertify",
					"fieldname": "ic_section_order",
					"label": "Section Order (internal)",
					"fieldtype": "Small Text",
					"insert_after": "ic_show_sample_handling",
					"hidden": 1,
					"description": "Comma-separated section keys for Print/PDF order.",
				}
			).insert(ignore_permissions=True)
		if frappe.db.exists("Custom Field", "Quotation-ic_section_identity"):
			frappe.db.set_value(
				"Custom Field",
				"Quotation-ic_section_identity",
				"insert_after",
				"ic_section_order",
				update_modified=False,
			)
		if not frappe.db.has_column("Quotation", "ic_section_order"):
			from frappe.database.schema import add_column

			add_column("Quotation", "ic_section_order", "Small Text")
		frappe.clear_cache(doctype="Quotation")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ensure quotation section order field")


def _ensure_test_lines_on_consulting():
	"""Show Test Lines section on Consulting (+ related) quotes, not only Testing."""
	depends = (
		"eval:in_list(['Testing','Consulting','Renewal','Service','Other',"
		"'Multiple Products / Multiple Services'], doc.ic_quotation_type)"
	)
	try:
		if frappe.db.exists("Custom Field", "Quotation-ic_section_test_lines"):
			frappe.db.set_value(
				"Custom Field",
				"Quotation-ic_section_test_lines",
				{
					"depends_on": depends,
					"description": (
						"Available on Testing and Consulting quotes. "
						"Lab → Test → Standard fills Unit Price; "
						"Total = Unit Price × No. of Samples."
					),
					"label": "Test Lines — Laboratory, Scope & Charges",
				},
				update_modified=False,
			)
		frappe.clear_cache(doctype="Quotation")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ensure test lines on consulting")


def _ensure_test_item_price_columns():
	"""Purchase = internal (not list); Unit Price editable + listed; Total = Unit × samples."""
	try:
		frappe.db.sql(
			"""
			update `tabDocField`
			set label=%s, in_list_view=0, read_only=0, hidden=0,
			    description=%s
			where parent='IC Quotation Test Item' and fieldname='purchase_price'
			""",
			(
				"Purchase Price (internal)",
				"Lab buy / cost — editable for staff; never shown to the customer on Print/PDF",
			),
		)
		frappe.db.sql(
			"""
			update `tabDocField`
			set label=%s, in_list_view=1, read_only=0, bold=1, columns=2,
			    description=%s
			where parent='IC Quotation Test Item' and fieldname='suggested_selling_price'
			""",
			(
				"Unit Price",
				"Customer-facing unit price (printed as Price). "
				"Editable. Total Price = Unit Price × No. of Samples",
			),
		)
		frappe.db.sql(
			"""
			update `tabDocField`
			set label=%s, hidden=1, in_list_view=0,
			    description=%s
			where parent='IC Quotation Test Item' and fieldname='per_unit_charges'
			""",
			(
				"Selling Price / Unit",
				"Mirrors Unit Price for totals — hidden duplicate of suggested_selling_price",
			),
		)
		frappe.db.sql(
			"""
			update `tabDocField`
			set label=%s, in_list_view=1, read_only=1, bold=1, columns=2,
			    description=%s
			where parent='IC Quotation Test Item' and fieldname='testing_charges'
			""",
			(
				"Total Price",
				"Unit Price × No. of Samples (auto-calculated)",
			),
		)
		frappe.db.sql(
			"""
			update `tabDocField`
			set description=%s
			where parent='IC Quotation Test Item' and fieldname='number_of_samples'
			""",
			(
				"Editable on Template and every Quotation line. "
				"Total Price = Unit Price × No. of Samples. "
				"Also drives Sample Required text on print.",
			),
		)
		# Clear property setters that force Purchase into the grid list
		for fieldname, props in (
			("purchase_price", ["in_list_view", "read_only", "hidden", "label"]),
			("suggested_selling_price", ["in_list_view", "read_only", "hidden", "label"]),
			("per_unit_charges", ["in_list_view", "hidden", "label"]),
			("testing_charges", ["in_list_view", "read_only", "label"]),
		):
			for ps in frappe.get_all(
				"Property Setter",
				filters={
					"doc_type": "IC Quotation Test Item",
					"field_name": fieldname,
					"property": ["in", props],
				},
				pluck="name",
			):
				try:
					frappe.delete_doc("Property Setter", ps, force=1, ignore_permissions=True)
				except Exception:
					pass
		frappe.clear_cache(doctype="IC Quotation Test Item")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ensure test item price columns")


def _sync_custom_field_columns(doctypes: list[str] | None = None):
	"""Ensure Custom Field value columns exist on parent tables."""
	from frappe.model import no_value_fields, table_fields

	doctypes = doctypes or []
	for doctype in doctypes:
		if not doctype or not frappe.db.exists("DocType", doctype):
			continue
		try:
			needs_sync = False
			for cf in frappe.get_all(
				"Custom Field",
				filters={"dt": doctype},
				fields=["fieldname", "fieldtype", "is_virtual"],
			):
				if not cf.fieldname:
					continue
				if cf.fieldtype in no_value_fields or cf.fieldtype in table_fields:
					continue
				if cf.is_virtual:
					continue
				if not frappe.db.has_column(doctype, cf.fieldname):
					needs_sync = True
					break
			if needs_sync:
				frappe.db.updatedb(doctype)
				frappe.clear_cache(doctype=doctype)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"_sync_custom_field_columns:{doctype}")


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


def _ensure_quotation_bank_account_field():
	"""Ensure Quotation.ic_bank_account exists (Link → IC Bank Account)."""
	if not frappe.db.exists("DocType", "IC Bank Account"):
		return
	cf_name = "Quotation-ic_bank_account"
	payload = {
		"doctype": "Custom Field",
		"dt": "Quotation",
		"module": "Instacertify",
		"fieldname": "ic_bank_account",
		"label": "Bank Account for this Quote",
		"fieldtype": "Link",
		"options": "IC Bank Account",
		"insert_after": "ic_section_policies",
		"in_standard_filter": 1,
		"description": "Select YES BANK or Indian Overseas Bank. Print/PDF uses this account.",
	}
	try:
		if frappe.db.exists("Custom Field", cf_name):
			# Keep options / label current
			frappe.db.set_value(
				"Custom Field",
				cf_name,
				{
					"options": "IC Bank Account",
					"label": "Bank Account for this Quote",
					"fieldtype": "Link",
				},
				update_modified=False,
			)
		else:
			# Prefer inserting before payment terms when that field already exists
			if frappe.db.exists("Custom Field", "Quotation-ic_payment_terms"):
				payload["insert_after"] = "ic_section_policies"
			frappe.get_doc(payload).insert(ignore_permissions=True)
		if not frappe.db.has_column("Quotation", "ic_bank_account"):
			from frappe.database.schema import add_column

			add_column("Quotation", "ic_bank_account", "Link")
		# Point Payment Terms insert_after at bank field when both exist
		if frappe.db.exists("Custom Field", "Quotation-ic_payment_terms"):
			frappe.db.set_value(
				"Custom Field",
				"Quotation-ic_payment_terms",
				"insert_after",
				"ic_bank_account",
				update_modified=False,
			)
		frappe.clear_cache(doctype="Quotation")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ensure quotation bank account field")


def _ensure_quotation_print_section_fields():
	"""Ensure Quotation ic_show_* Check fields exist (print section toggles)."""
	from instacertify.quotation.print_sections import QUOTE_PRINT_SECTIONS
	from frappe.database.schema import add_column

	prev = "ic_label_sample_handling"
	section_cf = "Quotation-ic_section_print_sections"
	try:
		if not frappe.db.exists("Custom Field", section_cf):
			frappe.get_doc(
				{
					"doctype": "Custom Field",
					"dt": "Quotation",
					"module": "Instacertify",
					"fieldname": "ic_section_print_sections",
					"label": "Print Sections — Uncheck to Hide on PDF",
					"fieldtype": "Section Break",
					"insert_after": prev,
					"collapsible": 1,
					"description": "Uncheck any section to hide that row on Print/PDF.",
				}
			).insert(ignore_permissions=True)
		prev = "ic_section_print_sections"
		mid = (len(QUOTE_PRINT_SECTIONS) + 1) // 2
		for i, (_tmpl_key, quote_key, label) in enumerate(QUOTE_PRINT_SECTIONS):
			if i == mid:
				col = "Quotation-ic_column_print_sections"
				if not frappe.db.exists("Custom Field", col):
					frappe.get_doc(
						{
							"doctype": "Custom Field",
							"dt": "Quotation",
							"module": "Instacertify",
							"fieldname": "ic_column_print_sections",
							"fieldtype": "Column Break",
							"insert_after": prev,
						}
					).insert(ignore_permissions=True)
				prev = "ic_column_print_sections"
			cf_name = f"Quotation-{quote_key}"
			if not frappe.db.exists("Custom Field", cf_name):
				frappe.get_doc(
					{
						"doctype": "Custom Field",
						"dt": "Quotation",
						"module": "Instacertify",
						"fieldname": quote_key,
						"label": f"Show {label}",
						"fieldtype": "Check",
						"default": "1",
						"insert_after": prev,
					}
				).insert(ignore_permissions=True)
			# Always ensure DB column exists — Custom Field alone is not enough
			if not frappe.db.has_column("Quotation", quote_key):
				add_column("Quotation", quote_key, "Check")
			prev = quote_key
		if frappe.db.exists("Custom Field", "Quotation-ic_section_identity"):
			frappe.db.set_value(
				"Custom Field",
				"Quotation-ic_section_identity",
				"insert_after",
				prev,
				update_modified=False,
			)
		frappe.clear_cache(doctype="Quotation")
		# Force meta refresh so template apply never sees stale "field not found"
		try:
			frappe.get_meta("Quotation", cached=False)
		except Exception:
			pass
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ensure quotation print section fields")


def _ensure_quotation_commercials_layout():
	"""Stack Test Lines → Commercials → Final Costing; Customer+Currency banner after entry guide."""
	chain = [
		("Quotation-ic_customer_currency_banner", {
			"fieldname": "ic_customer_currency_banner",
			"label": "Customer & Currency",
			"fieldtype": "HTML",
			"insert_after": "ic_entry_guide",
		}),
		("Quotation-ic_quotation_type", {"insert_after": "ic_customer_currency_banner"}),
		("Quotation-ic_section_testing", {"insert_after": "ic_deliverables"}),
		("Quotation-ic_section_test_lines", {
			"label": "Test Lines — Laboratory, Scope & Charges",
			"insert_after": "ic_gst_note",
		}),
		("Quotation-ic_sample_handling_policy", {"insert_after": "ic_test_items"}),
		("Quotation-ic_section_costing", {
			"label": "Commercials / Cost Breakdown",
			"insert_after": "ic_sample_handling_policy",
		}),
		("Quotation-ic_cost_items", {"insert_after": "ic_section_costing"}),
		("Quotation-ic_section_cost_totals", {
			"label": "Final Costing (Testing + Commercials)",
			"insert_after": "ic_cost_items",
		}),
		("Quotation-ic_section_policies", {"insert_after": "ic_total_quoted_value"}),
	]
	try:
		for cf_name, updates in chain:
			if cf_name == "Quotation-ic_customer_currency_banner" and not frappe.db.exists(
				"Custom Field", cf_name
			):
				doc = frappe.get_doc(
					{
						"doctype": "Custom Field",
						"dt": "Quotation",
						"module": "Instacertify",
						**updates,
					}
				)
				doc.flags.ignore_permissions = True
				doc.insert()
				continue
			if not frappe.db.exists("Custom Field", cf_name):
				continue
			for key, val in updates.items():
				if key == "fieldname":
					continue
				cur = frappe.db.get_value("Custom Field", cf_name, key)
				if cur != val:
					frappe.db.set_value(
						"Custom Field", cf_name, key, val, update_modified=False
					)
		frappe.clear_cache(doctype="Quotation")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ensure quotation commercials layout")


def _ensure_quotation_share_token_column():
	"""Share with Customer needs ic_share_token / ic_shared_on columns on Quotation."""
	from frappe.database.schema import add_column

	for fieldname, fieldtype in (
		("ic_share_token", "Data"),
		("ic_shared_on", "Datetime"),
		("ic_workflow_status", "Data"),
	):
		try:
			if not frappe.db.has_column("Quotation", fieldname):
				add_column("Quotation", fieldname, fieldtype)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"ensure Quotation.{fieldname} column")
	frappe.clear_cache(doctype="Quotation")


def _ensure_test_item_samples_editable():
	"""No. of Samples + Sample Required must stay editable on Template and Quotation grids."""
	try:
		frappe.db.sql(
			"""
			update `tabDocField`
			set read_only=0, hidden=0, in_list_view=1, bold=1,
			    description=%s
			where parent='IC Quotation Test Item' and fieldname='number_of_samples'
			""",
			(
				"Editable on Template and every Quotation line. "
				"Total Price = Unit Price × No. of Samples.",
			),
		)
		frappe.db.sql(
			"""
			update `tabDocField`
			set read_only=0, hidden=0
			where parent='IC Quotation Test Item' and fieldname='sample_requirement'
			"""
		)
		# Drop property setters that locked these fields on older installs
		for fieldname in ("number_of_samples", "sample_requirement"):
			for ps in frappe.get_all(
				"Property Setter",
				filters={
					"doc_type": "IC Quotation Test Item",
					"field_name": fieldname,
					"property": ["in", ["read_only", "hidden"]],
				},
				pluck="name",
			):
				try:
					frappe.delete_doc("Property Setter", ps, force=1, ignore_permissions=True)
				except Exception:
					pass
		frappe.clear_cache(doctype="IC Quotation Test Item")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ensure test item samples editable")


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
				"reqd": 0,
				"description": "Optional category. Only Customer is required to create a quote.",
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
	"""Customer section: Website Link, Login ID, Password + multi-portal table."""
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
	from instacertify.setup.custom_fields import CUSTOMER_FIELDS

	login_fields = [
		f
		for f in CUSTOMER_FIELDS
		if f.get("fieldname")
		in (
			"ic_section_login",
			"ic_website_link",
			"ic_customer_user_id",
			"ic_column_login",
			"ic_customer_password",
			"ic_login_notes",
			"ic_section_more_portals",
			"ic_portal_credentials",
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

	# Keep labels visible and fields un-hidden (older deploys hid the legacy trio)
	for fname, props in (
		(
			"Customer-ic_section_login",
			{
				"hidden": 0,
				"collapsible": 0,
				"label": "Customer Login Credentials",
				"description": "Save website link, login ID, and password for this customer. Add more portals in the table below.",
			},
		),
		(
			"Customer-ic_website_link",
			{"hidden": 0, "label": "Website Link", "options": "URL", "insert_after": "ic_section_login"},
		),
		(
			"Customer-ic_customer_user_id",
			{"hidden": 0, "label": "Login ID", "insert_after": "ic_website_link"},
		),
		("Customer-ic_column_login", {"hidden": 0, "insert_after": "ic_customer_user_id"}),
		(
			"Customer-ic_customer_password",
			{"hidden": 0, "label": "Password", "insert_after": "ic_column_login"},
		),
		(
			"Customer-ic_login_notes",
			{"hidden": 0, "label": "Login Notes", "insert_after": "ic_customer_password"},
		),
		(
			"Customer-ic_section_more_portals",
			{
				"hidden": 0,
				"collapsible": 1,
				"label": "Additional Portal Logins",
				"insert_after": "ic_login_notes",
				"description": "Optional — add more portals (name, website link, user ID, password).",
			},
		),
		(
			"Customer-ic_portal_credentials",
			{
				"hidden": 0,
				"fieldtype": "Table",
				"options": "IC Customer Portal Credential",
				"label": "Portal Logins",
				"insert_after": "ic_section_more_portals",
			},
		),
	):
		if frappe.db.exists("Custom Field", fname):
			try:
				frappe.db.set_value("Custom Field", fname, props, update_modified=False)
			except Exception:
				pass
		elif fname == "Customer-ic_website_link" or fname == "Customer-ic_section_more_portals":
			# create_custom_fields above should have added these; ignore if still missing
			pass

	# Keep Customer Team section after portal table
	if frappe.db.exists("Custom Field", "Customer-ic_section_team"):
		try:
			frappe.db.set_value(
				"Custom Field",
				"Customer-ic_section_team",
				"insert_after",
				"ic_portal_credentials",
				update_modified=False,
			)
		except Exception:
			pass

	frappe.clear_cache(doctype="Customer")

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
		doc.accent_color = "#EC691F"
		doc.legal_name = "Instacertify Labs Private Limited"
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
	"""Apply role profiles + laboratory / export permissions."""
	try:
		from instacertify.setup.role_profiles import ensure_role_profiles

		ensure_role_profiles()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "setup_permissions / role_profiles")
