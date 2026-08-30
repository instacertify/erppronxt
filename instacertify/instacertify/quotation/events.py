# Copyright (c) Instacertify
"""Quotation events and API."""

from __future__ import annotations

import secrets

import frappe
from frappe import _
from frappe.utils import cint, now_datetime


def validate_quotation(doc, method=None):
	from instacertify.setup.contact_billing import ensure_party_address_contact_fields
	from instacertify.setup.service_quote import apply_quote_customer_only_rules, ensure_service_quote_rules

	# Avoid MySQL 1054 on Address.tax_category / Contact.is_billing_contact
	ensure_party_address_contact_fields()
	ensure_service_quote_rules()
	apply_quote_customer_only_rules(doc)
	_calculate_test_line_totals(doc)
	_calculate_revenue_split(doc)
	if not doc.ic_revision_number and doc.ic_revision_number != 0:
		doc.ic_revision_number = 0
	if doc.ic_quotation_type == "Testing" and not doc.ic_subject:
		doc.ic_subject = "Testing"
	from instacertify.setup.naming_series import apply_quotation_series

	apply_quotation_series(doc)
	_apply_quotation_defaults(doc)
	from instacertify.team.assignees import sync_assignees

	sync_assignees(
		doc,
		table_field="ic_assignees",
		primary_field="ic_primary_assignee",
		default_user=None,  # Assignees optional — do not auto-assign owner on create
	)
	if doc.quotation_to == "Customer" and doc.party_name:
		from instacertify.accounting.billing import apply_transaction_billing_defaults

		apply_transaction_billing_defaults(doc, customer_field="party_name")
	from instacertify.accounting.consulting_billing import strip_warehouse_from_service_items

	strip_warehouse_from_service_items(doc)
	# Pipeline: preparing a quote moves the lead to Quote stage
	if doc.ic_workflow_status in (None, "", "Draft", "Internal Review", "Ready to Share"):
		try:
			_advance_linked_lead(doc, "Quote")
		except Exception:
			pass


def before_insert_quotation(doc, method=None):
	from instacertify.setup.naming_series import apply_quotation_series

	apply_quotation_series(doc)


def after_insert_quotation(doc, method=None):
	"""Quote No = naming-series document name (e.g. QTN-SRV-00001)."""
	_sync_quote_number_from_name(doc)


def on_update_quotation(doc, method=None):
	_sync_quote_number_from_name(doc)


def _sync_quote_number_from_name(doc):
	"""Keep ic_quote_number aligned with series-generated name unless manually overridden."""
	if doc.is_new() or not doc.name or doc.name.startswith("new-"):
		return
	if not doc.meta.has_field("ic_quote_number"):
		return
	current = (doc.get("ic_quote_number") or "").strip()
	# Auto-fill when blank; also replace placeholder text
	if not current or current.startswith("new-"):
		frappe.db.set_value(
			"Quotation", doc.name, "ic_quote_number", doc.name, update_modified=False
		)
		doc.ic_quote_number = doc.name


def _calculate_test_line_totals(doc):
	for row in doc.get("ic_test_items") or []:
		units = float(row.number_of_samples or 0) or 1
		if row.per_unit_charges:
			row.testing_charges = float(row.per_unit_charges) * units
		elif row.testing_charges and not row.per_unit_charges:
			row.per_unit_charges = float(row.testing_charges) / units


def _apply_quotation_defaults(doc):
	try:
		settings = frappe.get_cached_doc("IC Settings")
	except Exception:
		return
	if not doc.ic_payment_terms and settings.get("default_payment_terms"):
		doc.ic_payment_terms = settings.default_payment_terms
	if doc.ic_quotation_type == "Testing":
		if not doc.ic_sample_handling_policy and settings.get("default_sample_handling"):
			doc.ic_sample_handling_policy = settings.default_sample_handling
	if not doc.ic_cancellation_policy and settings.get("default_cancellation_policy"):
		doc.ic_cancellation_policy = settings.default_cancellation_policy
	if not doc.ic_confidentiality and settings.get("default_confidentiality"):
		doc.ic_confidentiality = settings.default_confidentiality
	if not doc.ic_force_majeure and settings.get("default_force_majeure"):
		doc.ic_force_majeure = settings.default_force_majeure


# Keep old name for any external callers
def _apply_testing_defaults(doc):
	_apply_quotation_defaults(doc)

def on_submit_quotation(doc, method=None):
	_ensure_qr(doc)


def on_update_after_submit(doc, method=None):
	_ensure_qr(doc)


def _calculate_revenue_split(doc):
	commercial = 0.0
	passthrough = 0.0
	for row in doc.get("ic_cost_items") or []:
		amount = float(row.amount or 0)
		# Prefer explicit Revenue select; fall back to checkbox / payment destination
		treatment = (row.get("revenue_treatment") or "").strip()
		if treatment == "Do Not Count as Revenue":
			is_pass = True
		elif treatment == "Counted Revenue":
			is_pass = False
		else:
			is_pass = bool(row.is_passthrough) or row.payment_destination in (
				"Payable Directly to Government",
				"Payable Directly to Laboratory",
				"Payable to Third Party",
			)
		if is_pass:
			row.is_passthrough = 1
			row.revenue_treatment = "Do Not Count as Revenue"
			passthrough += amount
		else:
			row.is_passthrough = 0
			row.revenue_treatment = "Counted Revenue"
			commercial += amount
	doc.ic_commercial_value = commercial
	doc.ic_passthrough_value = passthrough
	doc.ic_total_quoted_value = commercial + passthrough


def _ensure_qr(doc):
	if doc.get("ic_qr_code"):
		return
	from instacertify.utils.qr import generate_and_attach_qr, verification_url

	try:
		generate_and_attach_qr(
			"Quotation", doc.name, "ic_qr_code", verification_url("Quotation", doc.name)
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Quotation QR")


@frappe.whitelist()
def list_quote_formats_for_type(quotation_type: str | None = None):
	"""Active Quote Format Library entries for a major category (create-quote picker)."""
	quotation_type = (quotation_type or "").strip()
	majors = {"Consulting", "Testing", "Renewal", "Other"}
	filters: dict = {"is_active": 1}
	if quotation_type in majors:
		filters["quotation_type"] = quotation_type
	elif quotation_type == "Service":
		filters["quotation_type"] = "Consulting"
	elif quotation_type:
		filters["quotation_type"] = quotation_type

	rows = frappe.get_all(
		"IC Quotation Template",
		filters=filters,
		fields=[
			"name",
			"template_name",
			"quotation_type",
			"service_family",
			"service_name",
			"template_notes",
			"uploaded_format",
		],
		order_by="template_name asc",
		limit_page_length=300,
	)
	out = []
	for r in rows:
		label_parts = [r.template_name or r.name]
		if r.service_family:
			label_parts.append(f"— {r.service_family}")
		elif r.service_name:
			label_parts.append(f"— {r.service_name}")
		out.append(
			{
				"name": r.name,
				"label": " ".join(label_parts),
				"template_name": r.template_name,
				"quotation_type": r.quotation_type,
				"service_family": r.service_family,
				"service_name": r.service_name,
				"template_notes": r.template_notes,
				"has_format_file": 1 if r.uploaded_format else 0,
			}
		)
	return {"formats": out, "count": len(out), "category": quotation_type}


_LABEL_FIELDS = (
	"label_about",
	"label_standard",
	"label_process",
	"label_validity",
	"label_commercials",
	"label_particulars_col",
	"label_charges_col",
	"label_payment_terms",
	"label_timelines",
	"label_sample_required",
	"label_documents_required",
	"label_banking",
	"label_cancellation",
	"label_force_majeure",
	"label_confidentiality",
	"label_subject",
	"label_about_testing",
	"label_applicable_standards",
	"label_samples_requirements",
	"label_deliverable",
	"label_timeline",
	"label_payment_term",
	"label_sample_handling",
)


def _template_field_map(tmpl) -> dict:
	"""Scalar quotation fields filled from an IC Quotation Template."""
	qtype = "Consulting" if tmpl.quotation_type == "Service" else tmpl.quotation_type
	fields = {
		"ic_quotation_type": qtype,
		"ic_quotation_template": tmpl.name,
		"ic_service_family": tmpl.get("service_family"),
		"ic_service_name": tmpl.service_name,
		"ic_certification_type": tmpl.certification_type,
		"ic_applicable_standard": tmpl.applicable_standard,
		"ic_estimated_timeline": tmpl.estimated_timeline,
		"ic_validity_days": tmpl.validity_days,
		"ic_about_service": tmpl.get("about_service"),
		"ic_standard_narrative": tmpl.get("standard_narrative"),
		"ic_process_steps": tmpl.get("process_steps"),
		"ic_validity_text": tmpl.get("validity_text"),
		"ic_timeline_details": tmpl.get("timeline_details"),
		"ic_sample_required": tmpl.get("sample_required"),
		"ic_documents_required": tmpl.get("documents_required"),
		"ic_commercials_notes": tmpl.get("commercials_notes"),
		"ic_scope_of_work": tmpl.scope_of_work,
		"ic_deliverables": tmpl.deliverables,
		"ic_payment_terms": tmpl.get("payment_terms"),
		"ic_cancellation_policy": tmpl.get("cancellation_policy"),
		"ic_confidentiality": tmpl.get("confidentiality"),
		"ic_terms_and_conditions": tmpl.terms_and_conditions,
		"ic_force_majeure": tmpl.force_majeure,
		"ic_subject": tmpl.get("subject"),
		"ic_about_testing": tmpl.get("about_testing"),
		"ic_applicable_standards_text": tmpl.get("applicable_standards_text"),
		"ic_samples_note": tmpl.get("samples_note"),
		"ic_gst_note": tmpl.get("gst_note"),
		"ic_sample_handling_policy": tmpl.get("sample_handling_policy"),
	}
	for key in _LABEL_FIELDS:
		fields[f"ic_{key}"] = tmpl.get(key)
	return fields


def _template_cost_rows(tmpl) -> list[dict]:
	rows = []
	for row in tmpl.cost_items or []:
		treatment = (row.get("revenue_treatment") or "").strip()
		if treatment == "Do Not Count as Revenue":
			is_pass = True
		elif treatment == "Counted Revenue":
			is_pass = False
		else:
			is_pass = cint(row.is_passthrough) or row.payment_destination in (
				"Payable Directly to Government",
				"Payable Directly to Laboratory",
				"Payable to Third Party",
			)
			treatment = "Do Not Count as Revenue" if is_pass else "Counted Revenue"
		rows.append(
			{
				"cost_component": row.cost_component,
				"particulars": row.get("particulars"),
				"description": row.description,
				"amount": row.amount,
				"charges_display": row.get("charges_display"),
				"payment_destination": row.payment_destination,
				"revenue_treatment": treatment,
				"is_passthrough": 1 if is_pass else 0,
			}
		)
	return rows


def _template_test_rows(tmpl) -> list[dict]:
	return [
		{
			"product_name": row.product_name,
			"test_name": row.test_name,
			"applicable_standard": row.applicable_standard,
			"number_of_samples": row.number_of_samples,
			"per_unit_charges": row.get("per_unit_charges"),
			"sample_requirement": row.get("sample_requirement"),
			"sample_type": row.sample_type,
			"laboratory": row.laboratory,
			"laboratory_location": row.laboratory_location,
			"laboratory_accreditation": row.laboratory_accreditation,
			"testing_timeline": row.testing_timeline,
			"testing_charges": row.testing_charges,
		}
		for row in (tmpl.test_items or [])
	]


@frappe.whitelist()
def get_quotation_template_payload(template: str):
	"""Return format-library values to apply on a new or existing quotation (editable after)."""
	if not template or not frappe.db.exists("IC Quotation Template", template):
		frappe.throw(_("Quote format not found"))
	tmpl = frappe.get_doc("IC Quotation Template", template)
	fields = _template_field_map(tmpl)
	return {
		"template": tmpl.name,
		"template_name": tmpl.template_name,
		"quotation_type": fields["ic_quotation_type"],
		"fields": fields,
		"cost_items": _template_cost_rows(tmpl),
		"test_items": _template_test_rows(tmpl),
		"message": _("Format loaded — edit headings and values on the form as needed."),
	}


@frappe.whitelist()
def apply_quotation_template(quotation: str, template: str):
	"""Populate quotation fields from IC Quotation Template."""
	qt = frappe.get_doc("Quotation", quotation)
	payload = get_quotation_template_payload(template)
	for key, val in (payload.get("fields") or {}).items():
		if key == "ic_subject" and not val:
			continue
		qt.set(key, val)
	qt.set("ic_cost_items", [])
	for row in payload.get("cost_items") or []:
		qt.append("ic_cost_items", row)
	qt.set("ic_test_items", [])
	for row in payload.get("test_items") or []:
		qt.append("ic_test_items", row)
	qt.save(ignore_permissions=True)
	return qt.as_dict()


@frappe.whitelist()
def duplicate_quotation_template(template: str, new_name: str):
	"""Clone an existing template under a new name."""
	src = frappe.get_doc("IC Quotation Template", template)
	name = (new_name or "").strip()
	if not name:
		frappe.throw(_("Template name is required"))
	if frappe.db.exists("IC Quotation Template", name):
		frappe.throw(_("Template {0} already exists").format(name), frappe.DuplicateEntryError)
	doc = frappe.copy_doc(src)
	doc.template_name = name
	doc.insert(ignore_permissions=True)
	return {"template": doc.name}


_PREVIEW_LEAD_NAME = "Template Preview (Internal)"
_PREVIEW_TITLE_PREFIX = "[Template Preview]"


def _ensure_preview_party() -> tuple[str, str]:
	"""Return (quotation_to, party_name) for template Print/PDF previews."""
	lead = frappe.db.get_value("Lead", {"lead_name": _PREVIEW_LEAD_NAME}, "name")
	if not lead:
		doc = frappe.get_doc(
			{
				"doctype": "Lead",
				"lead_name": _PREVIEW_LEAD_NAME,
				"company_name": _PREVIEW_LEAD_NAME,
				"status": "Lead",
				"ic_party_name": _PREVIEW_LEAD_NAME,
			}
		)
		doc.insert(ignore_permissions=True)
		lead = doc.name
	return "Lead", lead


def _preview_item_code() -> str:
	item = (
		frappe.db.get_value("Item", {"item_code": "CONSULTING-SVC", "disabled": 0}, "name")
		or frappe.db.get_value("Item", {"disabled": 0, "is_sales_item": 1}, "name")
		or frappe.db.get_value("Item", {"disabled": 0}, "name")
	)
	if not item:
		frappe.throw(_("Create at least one sales Item before previewing a quote template."))
	return item


def _preview_title(template_name: str) -> str:
	base = f"{_PREVIEW_TITLE_PREFIX} {template_name or 'Quote'}".strip()
	return base[:140]


@frappe.whitelist()
def ensure_template_preview_quotation(template: str):
	"""Create or refresh a draft Quotation used to Print / PDF-test a template."""
	if not template or not frappe.db.exists("IC Quotation Template", template):
		frappe.throw(_("Quote format not found"))
	frappe.has_permission("IC Quotation Template", "read", throw=True)

	tmpl = frappe.get_doc("IC Quotation Template", template)
	qtype = tmpl.quotation_type or "Consulting"
	if qtype == "Service":
		qtype = "Consulting"
	title = _preview_title(tmpl.template_name)

	existing = frappe.db.get_value(
		"Quotation",
		{
			"ic_quotation_template": tmpl.name,
			"docstatus": 0,
			"title": title,
		},
		"name",
	)
	# Fallback: any draft preview for this template (title prefix)
	if not existing:
		existing = frappe.db.get_value(
			"Quotation",
			{
				"ic_quotation_template": tmpl.name,
				"docstatus": 0,
				"title": ["like", f"{_PREVIEW_TITLE_PREFIX}%"],
			},
			"name",
			order_by="modified desc",
		)

	from instacertify.utils.pdf import quotation_print_format

	if existing:
		apply_quotation_template(existing, tmpl.name)
		qt = frappe.get_doc("Quotation", existing)
		qt.db_set("title", title, update_modified=False)
		fmt = quotation_print_format(qt) or "Instacertify Quotation"
		return {
			"quotation": qt.name,
			"print_format": fmt,
			"template": tmpl.name,
			"template_name": tmpl.template_name,
			"message": _("Preview quotation refreshed from template."),
		}

	quotation_to, party = _ensure_preview_party()
	company = (
		frappe.db.get_single_value("Global Defaults", "default_company")
		or frappe.db.get_value("Company", {}, "name")
	)
	if not company:
		frappe.throw(_("Set a default Company before previewing templates."))

	item_code = _preview_item_code()
	default_rate = 0.0
	for row in tmpl.cost_items or []:
		treatment = (row.get("revenue_treatment") or "").strip()
		is_pass = treatment == "Do Not Count as Revenue" or cint(row.is_passthrough)
		if not is_pass and float(row.amount or 0) > 0:
			default_rate = float(row.amount or 0)
			break
	if not default_rate and tmpl.cost_items:
		default_rate = float(tmpl.cost_items[0].amount or 0)

	qt = frappe.get_doc(
		{
			"doctype": "Quotation",
			"title": title,
			"quotation_to": quotation_to,
			"party_name": party,
			"company": company,
			"transaction_date": frappe.utils.today(),
			"order_type": "Sales",
			"ic_quotation_type": qtype,
			"ic_quotation_template": tmpl.name,
			"items": [{"item_code": item_code, "qty": 1, "rate": default_rate or 1}],
		}
	)
	qt.insert(ignore_permissions=True)
	apply_quotation_template(qt.name, tmpl.name)
	qt.reload()
	qt.db_set("title", title, update_modified=False)
	fmt = quotation_print_format(qt) or "Instacertify Quotation"
	return {
		"quotation": qt.name,
		"print_format": fmt,
		"template": tmpl.name,
		"template_name": tmpl.template_name,
		"message": _("Preview quotation created from template."),
	}


@frappe.whitelist()
def save_quotation_as_template(quotation: str, template_name: str | None = None, overwrite: int = 0):
	"""Save any quotation (Service/Testing/Other) as an editable IC Quotation Template."""
	qt = frappe.get_doc("Quotation", quotation)
	name = (template_name or qt.ic_service_name or qt.ic_subject or qt.name or "Quotation Template").strip()
	exists = frappe.db.exists("IC Quotation Template", name)
	if exists and not int(overwrite or 0):
		frappe.throw(
			_("Template {0} already exists. Pass overwrite=1 to replace it.").format(name),
			frappe.DuplicateEntryError,
		)
	if exists:
		tmpl = frappe.get_doc("IC Quotation Template", name)
	else:
		tmpl = frappe.new_doc("IC Quotation Template")
		tmpl.template_name = name

	tmpl.quotation_type = (
		"Consulting"
		if (qt.ic_quotation_type or "Consulting") in ("Service", "Consulting")
		else qt.ic_quotation_type or "Consulting"
	)
	tmpl.is_active = 1
	tmpl.service_family = qt.get("ic_service_family")
	tmpl.service_name = qt.ic_service_name
	tmpl.certification_type = qt.ic_certification_type
	tmpl.applicable_standard = qt.ic_applicable_standard
	tmpl.estimated_timeline = qt.ic_estimated_timeline
	tmpl.validity_days = qt.ic_validity_days or 90
	tmpl.about_service = qt.ic_about_service
	tmpl.standard_narrative = qt.ic_standard_narrative
	tmpl.process_steps = qt.ic_process_steps
	tmpl.validity_text = qt.ic_validity_text
	tmpl.timeline_details = qt.ic_timeline_details
	tmpl.sample_required = qt.ic_sample_required
	tmpl.documents_required = qt.ic_documents_required
	tmpl.commercials_notes = qt.ic_commercials_notes
	tmpl.scope_of_work = qt.ic_scope_of_work
	tmpl.deliverables = qt.ic_deliverables
	tmpl.payment_terms = qt.ic_payment_terms
	tmpl.cancellation_policy = qt.ic_cancellation_policy
	tmpl.confidentiality = qt.ic_confidentiality
	tmpl.terms_and_conditions = qt.ic_terms_and_conditions
	tmpl.force_majeure = qt.ic_force_majeure
	tmpl.subject = qt.ic_subject
	tmpl.about_testing = qt.ic_about_testing
	tmpl.applicable_standards_text = qt.ic_applicable_standards_text
	tmpl.samples_note = qt.ic_samples_note
	tmpl.gst_note = qt.ic_gst_note
	tmpl.sample_handling_policy = qt.ic_sample_handling_policy
	for key in _LABEL_FIELDS:
		tmpl.set(key, qt.get(f"ic_{key}"))

	tmpl.set("cost_items", [])
	for row in qt.get("ic_cost_items") or []:
		is_pass = cint(row.is_passthrough) or (row.get("revenue_treatment") == "Do Not Count as Revenue")
		tmpl.append(
			"cost_items",
			{
				"cost_component": row.cost_component,
				"particulars": row.get("particulars"),
				"description": row.description,
				"amount": row.amount,
				"charges_display": row.get("charges_display"),
				"payment_destination": row.payment_destination,
				"revenue_treatment": row.get("revenue_treatment")
				or ("Do Not Count as Revenue" if is_pass else "Counted Revenue"),
				"is_passthrough": 1 if is_pass else 0,
			},
		)
	tmpl.set("test_items", [])
	for row in qt.get("ic_test_items") or []:
		tmpl.append(
			"test_items",
			{
				"product_name": row.product_name,
				"test_name": row.test_name,
				"applicable_standard": row.applicable_standard,
				"number_of_samples": row.number_of_samples,
				"per_unit_charges": row.get("per_unit_charges"),
				"sample_requirement": row.get("sample_requirement"),
				"sample_type": row.sample_type,
				"laboratory": row.laboratory,
				"laboratory_location": row.laboratory_location,
				"laboratory_accreditation": row.laboratory_accreditation,
				"testing_timeline": row.testing_timeline,
				"testing_charges": row.testing_charges,
			},
		)

	if exists:
		tmpl.save(ignore_permissions=True)
	else:
		tmpl.insert(ignore_permissions=True)

	qt.db_set("ic_quotation_template", tmpl.name, update_modified=False)
	return {"template": tmpl.name}

@frappe.whitelist()
def share_with_customer(quotation: str):
	doc = frappe.get_doc("Quotation", quotation)
	token = doc.ic_share_token or secrets.token_urlsafe(24)
	now = now_datetime()
	frappe.db.set_value(
		"Quotation",
		doc.name,
		{
			"ic_share_token": token,
			"ic_workflow_status": "Shared with Customer",
			"ic_shared_on": now,
		},
		update_modified=True,
	)
	doc.ic_share_token = token
	doc.ic_workflow_status = "Shared with Customer"
	doc.ic_shared_on = now
	try:
		_ensure_qr(doc)
		if doc.get("ic_qr_code"):
			frappe.db.set_value("Quotation", doc.name, "ic_qr_code", doc.ic_qr_code, update_modified=False)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Quotation QR on share")
	_set_workflow_state(doc.name, "IC Shared with Customer")
	_advance_linked_lead(doc, "Negotiation")
	_notify_share(doc)
	url = _portal_url(token)
	return {"url": url, "token": token}


def _portal_url(token: str) -> str:
	base = None
	try:
		base = frappe.db.get_single_value("IC Settings", "portal_base_url")
	except Exception:
		base = None
	base = (base or "").rstrip("/")
	if base:
		return f"{base}/ic-quotation/{token}"
	return frappe.utils.get_url(f"/ic-quotation/{token}")


def _set_workflow_state(name: str, state: str):
	try:
		if frappe.db.has_column("Quotation", "workflow_state"):
			frappe.db.set_value("Quotation", name, "workflow_state", state, update_modified=False)
	except Exception:
		pass


CUSTOMER_DECIDABLE_STATUSES = (
	"Shared with Customer",
	"Customer Review",
	"Ready to Share",
	"Changes Requested",
)


def _quotation_from_token(token: str):
	"""Resolve shared quotation; Guest must present a live share token."""
	if not (token or "").strip():
		frappe.throw(_("Invalid quotation link"), frappe.PermissionError)
	name = frappe.db.get_value("Quotation", {"ic_share_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid quotation link"), frappe.PermissionError)
	return frappe.get_doc("Quotation", name)


def _assert_customer_can_decide(doc):
	status = doc.ic_workflow_status or "Draft"
	if status not in CUSTOMER_DECIDABLE_STATUSES:
		frappe.throw(
			_("This quotation is not open for customer feedback right now."),
			frappe.PermissionError,
		)


@frappe.whitelist(allow_guest=True)
def customer_accept_quotation(token: str, remarks: str | None = None):
	"""Guest portal: record acceptance + feedback only. No Desk access / doc creation as Guest."""
	doc = _quotation_from_token(token)
	name = doc.name
	if doc.ic_workflow_status in ("Accepted",):
		return {
			"status": "Accepted",
			"message": _("This quotation was already approved. Thank you."),
		}
	_assert_customer_can_decide(doc)

	values = {"ic_workflow_status": "Accepted", "status": "Open"}
	if remarks:
		values["ic_customer_remarks"] = remarks
	frappe.db.set_value("Quotation", name, values, update_modified=True)
	doc.reload()
	_set_workflow_state(name, "IC Accepted")
	_advance_linked_lead(doc, "Order")
	_notify_acceptance(doc)

	# Invoice / Project creation runs as system job — never as Guest
	action = _resolve_post_accept_action(doc)
	try:
		frappe.enqueue(
			"instacertify.quotation.events.process_post_accept_actions",
			quotation=name,
			action=action,
			queue="short",
			enqueue_after_commit=True,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Enqueue post-accept actions")

	return {
		"status": "Accepted",
		"message": _(
			"Thank you — your approval was recorded. Our team will follow up. You can download the PDF from this page."
		),
	}


def process_post_accept_actions(quotation: str, action: str | None = None):
	"""Background: create invoice/project after customer accepts (staff context).

	When action is Prompt / Manual, only notify — owner is prompted on Desk to
	create a Project or Testing Request.
	"""
	doc = frappe.get_doc("Quotation", quotation)
	action = action or _resolve_post_accept_action(doc)

	# Always ensure owner gets a follow-up ToDo / alert to create Project / Testing
	_ensure_accept_followup_todo(doc)

	if action in ("Prompt for Project / Testing", "Manual", "Prompt"):
		return

	if action in ("Create Invoice", "Create Invoice and Project"):
		try:
			create_invoice_from_quotation(quotation, submit=0)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Auto invoice on quote accept")
	if action in ("Create Project", "Create Invoice and Project"):
		try:
			start_project_from_quotation(quotation)
			_advance_linked_lead(doc, "Project / Case")
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Auto project on quote accept")


def _resolve_post_accept_action(doc) -> str:
	choice = (doc.get("ic_post_accept_action") or "Use Company Default").strip()
	if choice and choice not in ("Use Company Default", ""):
		return choice
	try:
		setting = frappe.db.get_single_value("IC Settings", "on_quote_accept")
	except Exception:
		setting = None
	return setting or "Prompt for Project / Testing"


@frappe.whitelist()
def get_quotation_accept_followup(quotation: str):
	"""Desk: whether to prompt creating Project / Testing Request after approval."""
	qt = frappe.get_doc("Quotation", quotation)
	status = qt.ic_workflow_status or ""
	if status != "Accepted" and qt.get("workflow_state") != "IC Accepted":
		return {"prompt": 0}

	project = frappe.db.get_value("Project", {"ic_quotation": qt.name}, "name")
	testing = frappe.get_all(
		"IC Testing Request",
		filters={"quotation": qt.name},
		pluck="name",
		limit=5,
	)
	has_test_lines = bool(qt.get("ic_test_items"))
	is_testing_quote = (qt.get("ic_quotation_type") or "").strip() in ("Testing", "Test")

	needs_project = not project
	needs_testing = (has_test_lines or is_testing_quote) and not testing

	action = _resolve_post_accept_action(qt)

	return {
		"prompt": 1 if (needs_project or needs_testing) else 0,
		"quotation": qt.name,
		"customer": qt.party_name if qt.quotation_to == "Customer" else None,
		"quotation_type": qt.get("ic_quotation_type"),
		"project": project,
		"testing_requests": testing,
		"needs_project": 1 if needs_project else 0,
		"needs_testing": 1 if needs_testing else 0,
		"has_test_lines": 1 if has_test_lines else 0,
		"action_mode": action,
		"message": _(
			"Customer approved quotation {0}. Create a Project and/or Testing Request to continue delivery."
		).format(qt.name),
	}


def _ensure_accept_followup_todo(doc):
	"""Assign owner a ToDo to create Project / Testing Request after approval."""
	owner = doc.owner
	assignee = doc.get("ic_assigned_salesperson") or owner
	if not assignee or not frappe.db.exists("User", assignee) or assignee == "Guest":
		assignee = owner if owner and owner != "Guest" else "Administrator"
	if not assignee or not frappe.db.exists("User", assignee):
		return

	existing = frappe.db.get_value(
		"ToDo",
		{
			"reference_type": "Quotation",
			"reference_name": doc.name,
			"status": "Open",
			"allocated_to": assignee,
		},
		"name",
	)
	if existing:
		return

	try:
		frappe.get_doc(
			{
				"doctype": "ToDo",
				"allocated_to": assignee,
				"description": _(
					"Customer approved quotation {0}. Create a Project or Testing Request to start delivery."
				).format(doc.name),
				"reference_type": "Quotation",
				"reference_name": doc.name,
				"assigned_by": frappe.session.user
				if frappe.session.user not in (None, "Guest")
				else "Administrator",
				"priority": "High",
				"status": "Open",
				"date": frappe.utils.today(),
			}
		).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Accept follow-up ToDo")


def _acceptance_payload(doc):
	"""Internal/staff payload — not returned to guests."""
	return {
		"status": "Accepted",
		"quotation": doc.name,
		"invoice": frappe.db.get_value("Sales Invoice", {"ic_quotation": doc.name, "docstatus": ["<", 2]}, "name"),
		"project": frappe.db.get_value("Project", {"ic_quotation": doc.name}, "name"),
	}


@frappe.whitelist(allow_guest=True)
def customer_reject_quotation(token: str, remarks: str | None = None):
	"""Reject is no longer offered — customers may Approve or Ask to Revise only."""
	_quotation_from_token(token)  # validate token still exists
	frappe.throw(
		_("Rejecting a quotation is not available. Please Approve or Ask to Revise instead."),
		title=_("Action not available"),
	)


@frappe.whitelist(allow_guest=True)
def customer_request_changes(token: str, remarks: str):
	doc = _quotation_from_token(token)
	name = doc.name
	_assert_customer_can_decide(doc)
	if not (remarks or "").strip():
		frappe.throw(_("Please enter remarks explaining the revision you need"))
	frappe.db.set_value(
		"Quotation",
		name,
		{"ic_workflow_status": "Changes Requested", "ic_customer_remarks": remarks},
		update_modified=True,
	)
	doc.reload()
	_set_workflow_state(name, "IC Changes Requested")
	_advance_linked_lead(doc, "Negotiation")
	_notify_changes(doc)
	return {
		"status": "Changes Requested",
		"message": _("Revision request submitted. We will send an updated quote."),
	}


@frappe.whitelist(allow_guest=True)
def download_quotation_pdf(token: str):
	"""Guest-safe PDF download for a shared quotation link."""
	name = frappe.db.get_value("Quotation", {"ic_share_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid quotation link"), frappe.PermissionError)

	try:
		from instacertify.utils.pdf import get_quotation_pdf_bytes

		pdf = get_quotation_pdf_bytes(name, no_letterhead=1)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Quotation portal PDF")
		frappe.throw(
			_("PDF could not be generated right now. Please try again or contact Instacertify."),
			title=_("PDF generation failed"),
		)

	frappe.local.response.filename = f"{name}.pdf"
	frappe.local.response.filecontent = pdf
	frappe.local.response.type = "pdf"


@frappe.whitelist()
def open_quotation_for_revision(quotation: str):
	"""Re-open a Changes Requested / rejected quote for editing (owner, managers, admin)."""
	doc = frappe.get_doc("Quotation", quotation)
	_assert_can_revise(doc)
	if doc.docstatus == 1:
		frappe.throw(_("Submitted quotations must be amended / cancelled before revising"))
	if doc.docstatus == 2:
		frappe.throw(_("Cancelled quotations cannot be revised"))

	doc.ic_revision_number = int(doc.ic_revision_number or 0) + 1
	doc.ic_workflow_status = "Draft"
	# Invalidate old customer link until staff re-shares
	frappe.db.set_value(
		"Quotation",
		doc.name,
		{
			"ic_revision_number": doc.ic_revision_number,
			"ic_workflow_status": "Draft",
			"ic_share_token": "",
		},
		update_modified=True,
	)
	_set_workflow_state(doc.name, "IC Draft")
	_advance_linked_lead(doc, "Quote")
	_notify_revision_opened(doc)
	return {
		"quotation": doc.name,
		"ic_revision_number": doc.ic_revision_number,
		"ic_workflow_status": "Draft",
		"customer_remarks": doc.ic_customer_remarks,
	}


def _assert_can_revise(doc):
	user = frappe.session.user
	roles = set(frappe.get_roles(user))
	if user in ("Administrator", doc.owner):
		return
	if roles.intersection({"System Manager", "IC Admin", "Sales Manager", "IC Senior Operations"}):
		return
	frappe.throw(_("Only the quote owner, sales managers, or admin can revise this quotation"))


def _advance_linked_lead(doc, stage: str):
	"""Move linked Lead pipeline stage forward when quote progresses."""
	try:
		if not frappe.db.has_column("Lead", "ic_pipeline_stage"):
			return
	except Exception:
		return

	lead_name = None
	if doc.quotation_to == "Lead":
		lead_name = doc.party_name
	elif doc.get("opportunity"):
		opp = frappe.db.get_value(
			"Opportunity", doc.opportunity, ["opportunity_from", "party_name"], as_dict=True
		)
		if opp and opp.opportunity_from == "Lead":
			lead_name = opp.party_name
	if not lead_name and doc.quotation_to == "Customer" and doc.party_name:
		# Prefer lead that converted to this customer
		lead_name = frappe.db.get_value(
			"Lead", {"status": "Converted", "company_name": doc.customer_name}, "name"
		)
		if not lead_name:
			lead_name = frappe.db.get_value("Customer", doc.party_name, "lead_name")

	if not lead_name or not frappe.db.exists("Lead", lead_name):
		return

	order = [
		"Lead",
		"Requirement Analysis",
		"Technical Review",
		"Quote",
		"Negotiation",
		"Order",
		"Project / Case",
		"Certification",
		"Renewal",
	]
	current = frappe.db.get_value("Lead", lead_name, "ic_pipeline_stage") or "Lead"
	try:
		if order.index(stage) >= order.index(current if current in order else "Lead"):
			frappe.db.set_value("Lead", lead_name, "ic_pipeline_stage", stage, update_modified=False)
	except ValueError:
		frappe.db.set_value("Lead", lead_name, "ic_pipeline_stage", stage, update_modified=False)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "advance lead pipeline")


@frappe.whitelist()
def start_project_from_quotation(quotation: str):
	qt = frappe.get_doc("Quotation", quotation)
	if qt.ic_workflow_status != "Accepted" and qt.get("workflow_state") != "IC Accepted":
		# Allow if explicitly accepted via status
		if qt.ic_workflow_status not in ("Accepted",):
			frappe.throw(_("Quotation must be Accepted before starting a project"))

	existing = frappe.db.get_value("Project", {"ic_quotation": qt.name}, "name")
	if existing:
		return {"project": existing}

	customer = None
	if qt.quotation_to == "Customer":
		customer = qt.party_name

	products = []
	for p in qt.get("ic_products") or []:
		products.append(f"{p.product_name}: {p.services or ''}")
	if qt.ic_service_name:
		products.append(qt.ic_service_name)

	testing = []
	for t in qt.get("ic_test_items") or []:
		testing.append(f"{t.product_name} / {t.test_name} ({t.applicable_standard or ''})")

	project = frappe.get_doc(
		{
			"doctype": "Project",
			"project_name": f"{qt.ic_service_name or 'Project'} – {qt.party_name}",
			"customer": customer,
			"company": qt.company,
			"expected_start_date": frappe.utils.today(),
			"priority": "Medium",
			"ic_project_stage": "Project Initiated",
			"ic_priority": "High" if qt.get("ic_priority") == "High" else "Medium",
			"ic_quotation": qt.name,
			"ic_progress_percentage": 5,
			"ic_pending_action": "Collect customer documents",
			"ic_products_services": "\n".join(products),
			"ic_deliverables": frappe.utils.strip_html(qt.ic_deliverables or "")[:500],
			"ic_testing_requirements": "\n".join(testing),
			"ic_timeline": frappe.utils.strip_html(qt.get("ic_timeline_details") or "")[:500],
			"ic_assigned_employee": (
				qt.get("ic_primary_assignee")
				or getattr(qt, "ic_assigned_salesperson", None)
				or qt.owner
			),
		}
	)
	# Seed team: quotation assignees first, then legacy salesperson / ops / owner
	from instacertify.team.assignees import get_assignee_users

	team_users = []
	for u in get_assignee_users(qt, primary_field="ic_primary_assignee") + [
		getattr(qt, "ic_assigned_salesperson", None),
		getattr(qt, "ic_assigned_operations_manager", None),
		qt.owner,
	]:
		if u and u not in team_users and frappe.db.exists("User", u):
			team_users.append(u)
	for i, user in enumerate(team_users):
		project.append(
			"ic_team_members",
			{
				"user": user,
				"full_name": frappe.db.get_value("User", user, "full_name") or user,
				"role_on_project": "Primary" if i == 0 else "Member",
			},
		)
	# Map estimated end from timeline if possible
	project.insert(ignore_permissions=True)

	# Create starter tasks — assign the same people
	from instacertify.team.assignees import append_assignees_from_users

	for subject in (
		"Collect customer documents",
		"Review technical documents",
		"Prepare application package",
	):
		task = frappe.get_doc(
			{
				"doctype": "Task",
				"subject": subject,
				"project": project.name,
				"status": "Open",
				"priority": "Medium",
				"ic_customer": customer,
			}
		)
		append_assignees_from_users(task, team_users)
		task.insert(ignore_permissions=True)

	_notify_project_assigned(project)
	_advance_linked_lead(qt, "Project / Case")

	# Auto-create testing requests from lab-scoped quotation lines
	testing_result = {"created": [], "existing": []}
	if qt.get("ic_test_items"):
		try:
			from instacertify.testing.events import create_testing_requests_from_quotation

			testing_result = create_testing_requests_from_quotation(qt.name, project.name)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Create testing requests from quotation")

	return {
		"project": project.name,
		"testing_requests": testing_result.get("created") or [],
		"existing_testing_requests": testing_result.get("existing") or [],
	}


@frappe.whitelist()
def create_invoice_from_quotation(quotation: str, submit: int = 0):
	"""Create Sales Invoice directly from an accepted Quotation (no Sales Order).

	Uses quotation line items when present; otherwise builds invoice lines from
	Instacertify cost/commercial rows per payment terms (advance billing).
	"""
	qt = frappe.get_doc("Quotation", quotation)
	if qt.ic_workflow_status != "Accepted" and qt.get("workflow_state") != "IC Accepted":
		frappe.throw(_("Invoice can be created only after the customer confirms / Accepts the quotation"))

	existing = frappe.db.get_value(
		"Sales Invoice",
		{"ic_quotation": qt.name, "docstatus": ["<", 2]},
		"name",
	)
	if existing:
		return {"invoice": existing, "created": 0}

	# Prepare billable items on draft quotations, then submit
	if qt.docstatus == 0:
		_ensure_quotation_items(qt)
		qt.reload()
		qt.submit()
		qt.reload()
	elif qt.docstatus == 2:
		frappe.throw(_("Cancelled quotations cannot be invoiced"))

	has_items = any(not getattr(row, "is_alternative", 0) for row in (qt.items or []))
	if has_items:
		from erpnext.selling.doctype.quotation.quotation import make_sales_invoice

		si = make_sales_invoice(qt.name)
	else:
		si = _build_invoice_from_cost_items(qt)

	if isinstance(si, str):
		si = frappe.get_doc("Sales Invoice", si)

	si.ic_quotation = qt.name
	from instacertify.setup.naming_series import apply_sales_invoice_series

	apply_sales_invoice_series(si)
	payment_terms_text = frappe.utils.strip_html(qt.ic_payment_terms or "") or (
		qt.payment_terms_template or "As per quotation"
	)
	si.remarks = (
		(si.remarks or "").strip()
		+ f"\nInvoice against Quotation {qt.name} (customer confirmed)."
		+ f"\nPayment Terms: {payment_terms_text}"
	).strip()
	if qt.get("payment_terms_template") and not si.get("payment_terms_template"):
		si.payment_terms_template = qt.payment_terms_template
	if qt.get("payment_schedule") and not si.get("payment_schedule"):
		si.set("payment_schedule", [])
		for row in qt.payment_schedule:
			si.append(
				"payment_schedule",
				{
					"payment_term": row.payment_term,
					"due_date": row.due_date,
					"invoice_portion": row.invoice_portion,
					"payment_amount": row.payment_amount,
					"description": row.description,
				},
			)

	_set_invoice_defaults(si)
	si.run_method("set_missing_values")
	si.run_method("calculate_taxes_and_totals")
	_set_invoice_defaults(si)  # re-apply after set_missing_values may clear cost centers

	si.flags.ignore_permissions = True
	if si.is_new():
		si.insert(ignore_permissions=True)
	else:
		si.save(ignore_permissions=True)

	if int(submit or 0):
		si.submit()

	try:
		frappe.db.set_value("Quotation", qt.name, "status", "Ordered")
	except Exception:
		pass

	return {"invoice": si.name, "created": 1}


def _build_invoice_from_cost_items(qt):
	"""Manual Sales Invoice when Quotation has commercials but no standard items."""
	customer = qt.party_name if qt.quotation_to == "Customer" else None
	if not customer:
		from erpnext.selling.doctype.quotation.quotation import _make_customer

		cust = _make_customer(qt.name, ignore_permissions=True)
		customer = cust.name if cust else None
	if not customer:
		frappe.throw(_("Customer is required to create an invoice"))

	item_code = _default_service_item(qt.company)
	si = frappe.new_doc("Sales Invoice")
	si.customer = customer
	si.company = qt.company
	si.currency = qt.currency
	si.conversion_rate = qt.conversion_rate or 1
	si.selling_price_list = qt.selling_price_list
	si.ic_quotation = qt.name
	si.posting_date = frappe.utils.today()
	si.due_date = frappe.utils.today()

	for row in qt.get("ic_cost_items") or []:
		amount = float(row.amount or 0)
		if amount <= 0:
			continue
		label = row.particulars or row.description or row.cost_component or "Service Charges"
		si.append(
			"items",
			{
				"item_code": item_code,
				"item_name": label[:140],
				"description": label,
				"qty": 1,
				"rate": amount,
				"uom": frappe.db.get_value("Item", item_code, "stock_uom") or "Nos",
			},
		)

	if not si.items:
		frappe.throw(_("No billable commercial amounts found on this quotation"))

	_set_invoice_defaults(si)
	si.run_method("set_missing_values")
	si.run_method("calculate_taxes_and_totals")
	return si


def _set_invoice_defaults(si):
	"""Fill cost center / income account so invoice validates without Sales Order.

	ERPNext's Quotation → Sales Invoice mapper clears item cost_center; SI
	validation then fails with 'Cost Center None does not belong to company'.
	"""
	from instacertify.setup.naming_series import apply_sales_invoice_series

	apply_sales_invoice_series(si)
	if not si.get("items"):
		frappe.throw(_("Quotation has no items to invoice. Add items or cost breakdown first."))

	company = si.company
	cost_center, income_account = _ensure_company_accounting_defaults(company)
	_ensure_party_account_currency(si)

	for item in si.items:
		if not item.cost_center and cost_center:
			item.cost_center = cost_center
		if not item.income_account and income_account:
			item.income_account = income_account


def _ensure_party_account_currency(si):
	"""Allow Quotation currency (e.g. USD) to invoice when only INR Debtors exist."""
	if not si.customer or not si.currency:
		return
	company_currency = frappe.get_cached_value("Company", si.company, "default_currency")
	if si.currency == company_currency:
		return
	# Prefer enabling multi-currency against single party account (common for export invoices)
	if not frappe.db.get_single_value(
		"Accounts Settings", "allow_multi_currency_invoices_against_single_party_account"
	):
		frappe.db.set_single_value(
			"Accounts Settings",
			"allow_multi_currency_invoices_against_single_party_account",
			1,
		)


def _ensure_company_accounting_defaults(company: str) -> tuple[str | None, str | None]:
	"""Ensure Company has a leaf cost center and default income account for invoicing."""
	if not company:
		return None, None

	cost_center = frappe.get_cached_value("Company", company, "cost_center")
	if cost_center and not frappe.db.exists("Cost Center", cost_center):
		cost_center = None
	if not cost_center:
		cost_center = frappe.db.get_value("Cost Center", {"company": company, "is_group": 0}, "name")
	if not cost_center:
		abbr = frappe.get_cached_value("Company", company, "abbr") or "IC"
		parent_name = f"{company} - {abbr}"
		if not frappe.db.exists("Cost Center", parent_name):
			parent = frappe.get_doc(
				{
					"doctype": "Cost Center",
					"cost_center_name": company,
					"company": company,
					"is_group": 1,
					"parent_cost_center": None,
				}
			)
			parent.flags.ignore_permissions = True
			parent.flags.ignore_mandatory = True
			parent.insert()
		main_name = f"Main - {abbr}"
		if not frappe.db.exists("Cost Center", main_name):
			main = frappe.get_doc(
				{
					"doctype": "Cost Center",
					"cost_center_name": "Main",
					"company": company,
					"is_group": 0,
					"parent_cost_center": parent_name,
				}
			)
			main.flags.ignore_permissions = True
			main.insert()
		cost_center = main_name
		frappe.db.set_value(
			"Company",
			company,
			{
				"cost_center": cost_center,
				"round_off_cost_center": cost_center,
				"depreciation_cost_center": cost_center,
			},
			update_modified=False,
		)

	income_account = frappe.get_cached_value("Company", company, "default_income_account")
	if income_account and not frappe.db.exists("Account", income_account):
		income_account = None
	if not income_account:
		abbr = frappe.get_cached_value("Company", company, "abbr") or "IC"
		for label in ("Service", "Sales"):
			candidate = f"{label} - {abbr}"
			if frappe.db.exists("Account", candidate):
				income_account = candidate
				break
		if not income_account:
			income_account = frappe.db.get_value(
				"Account",
				{"company": company, "root_type": "Income", "is_group": 0},
				"name",
			)
		if income_account:
			frappe.db.set_value(
				"Company",
				company,
				"default_income_account",
				income_account,
				update_modified=False,
			)

	return cost_center, income_account


def _ensure_quotation_items(qt):
	"""Ensure Quotation has sellable non-stock items so invoice mapping works.

	Maps free-text cost / test / product labels to non-stock Items (no inventory).
	"""
	from instacertify.setup.service_quote import ensure_nonstock_item_for_label

	qt = frappe.get_doc("Quotation", qt.name)
	if qt.docstatus != 0:
		return
	has_items = any(not getattr(row, "is_alternative", 0) for row in (qt.items or []))
	if has_items:
		return

	changed = False
	for row in qt.get("ic_cost_items") or []:
		amount = float(row.amount or 0)
		if amount <= 0:
			continue
		label = (
			row.particulars or row.description or row.cost_component or "Service Charges"
		).strip()
		item_code = ensure_nonstock_item_for_label(label)
		qt.append(
			"items",
			{
				"item_code": item_code,
				"item_name": label[:140],
				"description": label,
				"qty": 1,
				"rate": amount,
				"uom": frappe.db.get_value("Item", item_code, "stock_uom") or "Nos",
			},
		)
		changed = True

	if not changed:
		for row in qt.get("ic_test_items") or []:
			amount = float(row.testing_charges or row.per_unit_charges or 0)
			if amount <= 0:
				continue
			label = (
				row.test_name
				or row.applicable_standard
				or row.product_name
				or "Testing Service"
			).strip()
			item_code = ensure_nonstock_item_for_label(label)
			qt.append(
				"items",
				{
					"item_code": item_code,
					"item_name": label[:140],
					"description": label,
					"qty": 1,
					"rate": amount,
					"uom": frappe.db.get_value("Item", item_code, "stock_uom") or "Nos",
				},
			)
			changed = True

	if not changed:
		for row in qt.get("ic_products") or []:
			label = (row.product_name or "").strip()
			amount = float(row.estimated_value or 0)
			if not label and amount <= 0:
				continue
			label = label or "Customer Product"
			item_code = ensure_nonstock_item_for_label(label)
			qt.append(
				"items",
				{
					"item_code": item_code,
					"item_name": label[:140],
					"description": label,
					"qty": 1,
					"rate": amount,
					"uom": frappe.db.get_value("Item", item_code, "stock_uom") or "Nos",
				},
			)
			changed = True

	if not changed:
		frappe.throw(
			_("Add Quotation Items, Cost / Commercial lines, or Test lines before creating an invoice")
		)

	qt.save(ignore_permissions=True)


def _default_service_item(company: str | None = None) -> str:
	from instacertify.setup.service_quote import ensure_nonstock_item_for_label

	return ensure_nonstock_item_for_label("Customer Product / Service")


def _notify_share(doc):
	recipients = list({doc.owner, frappe.db.get_value("User", {"role_profile_name": "IC Admin"}, "name") or "Administrator"})
	_send_notification("Quotation Shared", doc, recipients)


def _quotation_notify_recipients(doc) -> list[str]:
	from instacertify.team.assignees import get_assignee_users

	return get_assignee_users(doc, primary_field="ic_primary_assignee") + [
		doc.owner,
		"Administrator",
		doc.get("ic_assigned_salesperson"),
	]


def _notify_acceptance(doc):
	_send_notification(
		_("Quotation Accepted — create Project or Testing Request"),
		doc,
		_quotation_notify_recipients(doc),
		body=_(
			"Customer approved {0}. Open the quotation and create a Project and/or Testing Request to continue."
		).format(doc.name),
	)
	_ensure_accept_followup_todo(doc)


def _notify_changes(doc):
	_send_notification("Quotation Changes Requested", doc, _quotation_notify_recipients(doc))


def _notify_rejection(doc):
	_send_notification("Quotation Rejected by Customer", doc, _quotation_notify_recipients(doc))


def _notify_revision_opened(doc):
	_send_notification(
		f"Quotation opened for revision (Rev {doc.ic_revision_number})",
		doc,
		_quotation_notify_recipients(doc),
	)


def _notify_project_assigned(project):
	from instacertify.project.events import get_project_assignee_users

	recipients = get_project_assignee_users(project) + [project.owner, "Administrator"]
	_send_notification("New Project Assigned", project, recipients)


def _send_notification(subject, doc, recipients, body: str | None = None):
	for user in set(filter(None, recipients)):
		if not frappe.db.exists("User", user):
			continue
		try:
			notification = frappe.get_doc(
				{
					"doctype": "Notification Log",
					"subject": f"{subject}: {doc.name}",
					"email_content": body
					or f"{subject} for {doc.doctype} {doc.name}",
					"document_type": doc.doctype,
					"document_name": doc.name,
					"for_user": user,
					"type": "Alert",
					"from_user": frappe.session.user if frappe.session.user != "Guest" else "Administrator",
				}
			)
			notification.insert(ignore_permissions=True)
		except Exception:
			pass
