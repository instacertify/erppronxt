# Copyright (c) Instacertify
"""Quotation events and API."""

from __future__ import annotations

import secrets

import frappe
from frappe import _
from frappe.utils import now_datetime


def validate_quotation(doc, method=None):
	_calculate_test_line_totals(doc)
	_calculate_revenue_split(doc)
	if not doc.ic_revision_number and doc.ic_revision_number != 0:
		doc.ic_revision_number = 0
	if doc.ic_quotation_type == "Testing" and not doc.ic_subject:
		doc.ic_subject = "Testing"
	_apply_testing_defaults(doc)


def _calculate_test_line_totals(doc):
	for row in doc.get("ic_test_items") or []:
		units = float(row.number_of_samples or 0) or 1
		if row.per_unit_charges:
			row.testing_charges = float(row.per_unit_charges) * units
		elif row.testing_charges and not row.per_unit_charges:
			row.per_unit_charges = float(row.testing_charges) / units


def _apply_testing_defaults(doc):
	if doc.ic_quotation_type != "Testing":
		return
	try:
		settings = frappe.get_cached_doc("IC Settings")
	except Exception:
		return
	if not doc.ic_payment_terms and settings.get("default_payment_terms"):
		doc.ic_payment_terms = settings.default_payment_terms
	if not doc.ic_sample_handling_policy and settings.get("default_sample_handling"):
		doc.ic_sample_handling_policy = settings.default_sample_handling
	if not doc.ic_cancellation_policy and settings.get("default_cancellation_policy"):
		doc.ic_cancellation_policy = settings.default_cancellation_policy
	if not doc.ic_confidentiality and settings.get("default_confidentiality"):
		doc.ic_confidentiality = settings.default_confidentiality
	if not doc.ic_force_majeure and settings.get("default_force_majeure"):
		doc.ic_force_majeure = settings.default_force_majeure


def on_submit_quotation(doc, method=None):
	_ensure_qr(doc)


def on_update_after_submit(doc, method=None):
	_ensure_qr(doc)


def _calculate_revenue_split(doc):
	commercial = 0.0
	passthrough = 0.0
	for row in doc.get("ic_cost_items") or []:
		amount = float(row.amount or 0)
		is_pass = row.is_passthrough or row.payment_destination in (
			"Payable Directly to Government",
			"Payable Directly to Laboratory",
			"Payable to Third Party",
		)
		if is_pass:
			row.is_passthrough = 1
			passthrough += amount
		else:
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
def apply_quotation_template(quotation: str, template: str):
	"""Populate quotation fields from IC Quotation Template."""
	qt = frappe.get_doc("Quotation", quotation)
	tmpl = frappe.get_doc("IC Quotation Template", template)
	qt.ic_quotation_type = tmpl.quotation_type
	qt.ic_quotation_template = tmpl.name
	qt.ic_service_name = tmpl.service_name
	qt.ic_certification_type = tmpl.certification_type
	qt.ic_applicable_standard = tmpl.applicable_standard
	qt.ic_estimated_timeline = tmpl.estimated_timeline
	qt.ic_scope_of_work = tmpl.scope_of_work
	qt.ic_deliverables = tmpl.deliverables
	qt.ic_terms_and_conditions = tmpl.terms_and_conditions
	qt.ic_force_majeure = tmpl.force_majeure
	qt.set("ic_cost_items", [])
	for row in tmpl.cost_items or []:
		qt.append(
			"ic_cost_items",
			{
				"cost_component": row.cost_component,
				"description": row.description,
				"amount": row.amount,
				"payment_destination": row.payment_destination,
				"is_passthrough": row.is_passthrough,
			},
		)
	qt.set("ic_test_items", [])
	for row in tmpl.test_items or []:
		qt.append(
			"ic_test_items",
			{
				"product_name": row.product_name,
				"test_name": row.test_name,
				"applicable_standard": row.applicable_standard,
				"number_of_samples": row.number_of_samples,
				"sample_type": row.sample_type,
				"laboratory": row.laboratory,
				"laboratory_location": row.laboratory_location,
				"laboratory_accreditation": row.laboratory_accreditation,
				"testing_timeline": row.testing_timeline,
				"testing_charges": row.testing_charges,
			},
		)
	qt.save(ignore_permissions=True)
	return qt.as_dict()


@frappe.whitelist()
def share_with_customer(quotation: str):
	doc = frappe.get_doc("Quotation", quotation)
	if not doc.ic_share_token:
		doc.ic_share_token = secrets.token_urlsafe(24)
	doc.ic_workflow_status = "Shared with Customer"
	doc.ic_shared_on = now_datetime()
	_ensure_qr(doc)
	doc.save(ignore_permissions=True)
	if hasattr(doc, "workflow_state"):
		try:
			frappe.db.set_value("Quotation", doc.name, "workflow_state", "IC Shared with Customer")
		except Exception:
			pass
	_notify_share(doc)
	url = frappe.utils.get_url(f"/ic-quotation/{doc.ic_share_token}")
	return {"url": url, "token": doc.ic_share_token}


@frappe.whitelist(allow_guest=True)
def customer_accept_quotation(token: str, remarks: str | None = None):
	name = frappe.db.get_value("Quotation", {"ic_share_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid quotation link"), frappe.PermissionError)
	doc = frappe.get_doc("Quotation", name)
	doc.ic_workflow_status = "Accepted"
	if remarks:
		doc.ic_customer_remarks = remarks
	doc.status = "Open"
	doc.save(ignore_permissions=True)
	frappe.db.set_value("Quotation", name, "workflow_state", "IC Accepted", update_modified=False)
	_notify_acceptance(doc)
	return {"status": "Accepted", "quotation": name}


@frappe.whitelist(allow_guest=True)
def customer_request_changes(token: str, remarks: str):
	name = frappe.db.get_value("Quotation", {"ic_share_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid quotation link"), frappe.PermissionError)
	doc = frappe.get_doc("Quotation", name)
	doc.ic_workflow_status = "Changes Requested"
	doc.ic_customer_remarks = remarks
	doc.save(ignore_permissions=True)
	frappe.db.set_value(
		"Quotation", name, "workflow_state", "IC Changes Requested", update_modified=False
	)
	_notify_changes(doc)
	return {"status": "Changes Requested", "quotation": name}


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
			"ic_assigned_employee": qt.ic_assigned_salesperson
			if hasattr(qt, "ic_assigned_salesperson")
			else qt.owner,
		}
	)
	# Map estimated end from timeline if possible
	project.insert(ignore_permissions=True)

	# Create starter tasks
	for subject in (
		"Collect customer documents",
		"Review technical documents",
		"Prepare application package",
	):
		frappe.get_doc(
			{
				"doctype": "Task",
				"subject": subject,
				"project": project.name,
				"status": "Open",
				"priority": "Medium",
			}
		).insert(ignore_permissions=True)

	_notify_project_assigned(project)
	return {"project": project.name}


def _notify_share(doc):
	recipients = list({doc.owner, frappe.db.get_value("User", {"role_profile_name": "IC Admin"}, "name") or "Administrator"})
	_send_notification("Quotation Shared", doc, recipients)


def _notify_acceptance(doc):
	recipients = [doc.owner, "Administrator"]
	assigned = frappe.db.get_value("Quotation", doc.name, "owner")
	_send_notification("Quotation Accepted", doc, recipients + [assigned])


def _notify_changes(doc):
	_send_notification("Quotation Changes Requested", doc, [doc.owner, "Administrator"])


def _notify_project_assigned(project):
	recipients = [project.ic_assigned_employee or project.owner, "Administrator"]
	_send_notification("New Project Assigned", project, recipients)


def _send_notification(subject, doc, recipients):
	for user in set(filter(None, recipients)):
		if not frappe.db.exists("User", user):
			continue
		try:
			notification = frappe.get_doc(
				{
					"doctype": "Notification Log",
					"subject": f"{subject}: {doc.name}",
					"email_content": f"{subject} for {doc.doctype} {doc.name}",
					"document_type": doc.doctype,
					"document_name": doc.name,
					"for_user": user,
					"type": "Alert",
					"from_user": frappe.session.user,
				}
			)
			notification.insert(ignore_permissions=True)
		except Exception:
			pass
