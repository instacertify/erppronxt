#!/usr/bin/env python3
"""Generate Instacertify DocType JSON definitions."""
from __future__ import annotations

import json
import os
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "instacertify"


def write_doctype(module_path: str, name: str, data: dict):
	folder = APP / module_path / "doctype" / name
	folder.mkdir(parents=True, exist_ok=True)
	(folder / "__init__.py").write_text("")
	data.setdefault("doctype", "DocType")
	data.setdefault("engine", "InnoDB")
	data.setdefault("module", "Instacertify")
	data.setdefault("naming_rule", "By fieldname") if "autoname" in data and data["autoname"].startswith("field:") else None
	path = folder / f"{name}.json"
	path.write_text(json.dumps(data, indent=1) + "\n")
	controller = name.replace(" ", "_").lower() if False else name
	py = folder / f"{name}.py"
	if not py.exists():
		class_name = "".join(p.title() for p in name.split("_"))
		py.write_text(
			f'import frappe\nfrom frappe.model.document import Document\n\n\nclass {class_name}(Document):\n\tpass\n'
		)
	js = folder / f"{name}.js"
	if not js.exists():
		dt_label = data.get("name", name)
		js.write_text(
			f'// Copyright (c) Instacertify\nfrappe.ui.form.on("{dt_label}", {{\n\trefresh(frm) {{\n\t}}\n}});\n'
		)
	print(f"Wrote {path}")


def field(**kwargs):
	defaults = {"doctype": "DocField"}
	defaults.update(kwargs)
	return defaults


def perm(**kwargs):
	defaults = {
		"doctype": "DocPerm",
		"role": "System Manager",
		"read": 1,
		"write": 1,
		"create": 1,
		"delete": 1,
		"submit": 0,
		"cancel": 0,
		"amend": 0,
		"report": 1,
		"export": 1,
		"import": 0,
		"share": 1,
		"print": 1,
		"email": 1,
	}
	defaults.update(kwargs)
	return defaults


STANDARD_PERMS = [
	perm(role="System Manager"),
	perm(role="IC Admin"),
	perm(role="IC Senior Operations", delete=0),
	perm(role="IC Operations Manager", delete=0),
	perm(role="IC Sales Person", delete=0, export=0),
]


def main():
	# ---------- Consultant Referral ----------
	write_doctype(
		"crm",
		"consultant_referral",
		{
			"name": "Consultant Referral",
			"autoname": "naming_series:",
			"naming_rule": "By \"Naming Series\" field",
			"module": "Instacertify",
			"is_submittable": 0,
			"track_changes": 1,
			"search_fields": "consultant_name,email,phone",
			"title_field": "consultant_name",
			"sort_field": "modified",
			"sort_order": "DESC",
			"fields": [
				field(fieldname="naming_series", fieldtype="Select", label="Series", options="CR-.YYYY.-.####", default="CR-.YYYY.-.####", reqd=1),
				field(fieldname="consultant_name", fieldtype="Data", label="Consultant / Referral Person", reqd=1, in_list_view=1),
				field(fieldname="column_break_1", fieldtype="Column Break"),
				field(fieldname="status", fieldtype="Select", label="Status", options="Active\nInactive", default="Active", in_list_view=1),
				field(fieldname="section_contact", fieldtype="Section Break", label="Contact"),
				field(fieldname="email", fieldtype="Data", label="Email", options="Email"),
				field(fieldname="phone", fieldtype="Data", label="Phone", options="Phone"),
				field(fieldname="column_break_2", fieldtype="Column Break"),
				field(fieldname="organization", fieldtype="Data", label="Organization"),
				field(fieldname="city", fieldtype="Data", label="City"),
				field(fieldname="section_notes", fieldtype="Section Break", label="Notes"),
				field(fieldname="remarks", fieldtype="Text Editor", label="Remarks"),
			],
			"permissions": STANDARD_PERMS,
		},
	)

	# ---------- IC Quotation Template ----------
	write_doctype(
		"quotation",
		"ic_quotation_template",
		{
			"name": "IC Quotation Template",
			"autoname": "field:template_name",
			"naming_rule": "By fieldname",
			"module": "Instacertify",
			"track_changes": 1,
			"title_field": "template_name",
			"search_fields": "template_name,quotation_type,service_name",
			"sort_field": "modified",
			"sort_order": "DESC",
			"fields": [
				field(fieldname="template_name", fieldtype="Data", label="Template Name", reqd=1, unique=1, in_list_view=1),
				field(fieldname="quotation_type", fieldtype="Select", label="Quotation Type",
					options="Service\nTesting\nOther\nMultiple Products / Multiple Services", reqd=1, in_list_view=1),
				field(fieldname="column_break_1", fieldtype="Column Break"),
				field(fieldname="is_active", fieldtype="Check", label="Active", default=1, in_list_view=1),
				field(fieldname="section_service", fieldtype="Section Break", label="Service / Certification"),
				field(fieldname="service_name", fieldtype="Data", label="Service Name"),
				field(fieldname="certification_type", fieldtype="Data", label="Certification Type"),
				field(fieldname="applicable_standard", fieldtype="Data", label="Applicable Standard"),
				field(fieldname="column_break_2", fieldtype="Column Break"),
				field(fieldname="estimated_timeline", fieldtype="Data", label="Estimated Timeline"),
				field(fieldname="validity_days", fieldtype="Int", label="Validity (Days)", default=30),
				field(fieldname="section_scope", fieldtype="Section Break", label="Scope & Deliverables"),
				field(fieldname="scope_of_work", fieldtype="Text Editor", label="Scope of Work"),
				field(fieldname="deliverables", fieldtype="Text Editor", label="Deliverables"),
				field(fieldname="terms_and_conditions", fieldtype="Text Editor", label="Terms and Conditions"),
				field(fieldname="force_majeure", fieldtype="Text Editor", label="Force Majeure"),
				field(fieldname="section_cost", fieldtype="Section Break", label="Default Cost Structure"),
				field(fieldname="cost_items", fieldtype="Table", label="Cost Items", options="IC Quotation Cost Item"),
				field(fieldname="section_testing", fieldtype="Section Break", label="Default Testing Structure",
					depends_on="eval:doc.quotation_type=='Testing' || doc.quotation_type=='Multiple Products / Multiple Services'"),
				field(fieldname="test_items", fieldtype="Table", label="Test Items", options="IC Quotation Test Item"),
			],
			"permissions": [
				perm(role="System Manager"),
				perm(role="IC Admin"),
				perm(role="IC Senior Operations", delete=0),
				perm(role="IC Operations Manager", delete=0),
				perm(role="IC Sales Person", delete=0),
			],
		},
	)

	# Child: Cost Item
	write_doctype(
		"quotation",
		"ic_quotation_cost_item",
		{
			"name": "IC Quotation Cost Item",
			"module": "Instacertify",
			"istable": 1,
			"editable_grid": 1,
			"fields": [
				field(fieldname="cost_component", fieldtype="Select", label="Cost Component", in_list_view=1, reqd=1,
					options="Consulting Charges\nTesting Charges\nGovernment Fees\nCertification Authority Fees\nLaboratory Charges\nOther Charges"),
				field(fieldname="description", fieldtype="Data", label="Description", in_list_view=1),
				field(fieldname="amount", fieldtype="Currency", label="Amount", in_list_view=1, reqd=1, options="currency"),
				field(fieldname="payment_destination", fieldtype="Select", label="Payment Destination", in_list_view=1, reqd=1,
					options="Payable to Instacertify\nPayable Directly to Government\nPayable Directly to Laboratory\nPayable to Third Party"),
				field(fieldname="is_passthrough", fieldtype="Check", label="Pass-Through", in_list_view=1,
					description="Not counted as Instacertify revenue"),
				field(fieldname="currency", fieldtype="Link", options="Currency", label="Currency", hidden=1),
			],
			"permissions": [],
		},
	)

	# Child: Test Item on quotation/template
	write_doctype(
		"quotation",
		"ic_quotation_test_item",
		{
			"name": "IC Quotation Test Item",
			"module": "Instacertify",
			"istable": 1,
			"editable_grid": 1,
			"fields": [
				field(fieldname="product_name", fieldtype="Data", label="Product Name", in_list_view=1, reqd=1),
				field(fieldname="test_name", fieldtype="Data", label="Test Name", in_list_view=1, reqd=1),
				field(fieldname="applicable_standard", fieldtype="Data", label="Applicable Standard", in_list_view=1),
				field(fieldname="number_of_samples", fieldtype="Int", label="Number of Samples", default=1, in_list_view=1),
				field(fieldname="sample_type", fieldtype="Data", label="Sample Type"),
				field(fieldname="laboratory", fieldtype="Link", options="IC Laboratory", label="Laboratory", in_list_view=1),
				field(fieldname="laboratory_location", fieldtype="Data", label="Laboratory Location", fetch_from="laboratory.location"),
				field(fieldname="laboratory_accreditation", fieldtype="Data", label="Laboratory Accreditation"),
				field(fieldname="testing_timeline", fieldtype="Data", label="Testing Timeline"),
				field(fieldname="testing_charges", fieldtype="Currency", label="Testing Charges", in_list_view=1, options="currency"),
				field(fieldname="currency", fieldtype="Link", options="Currency", label="Currency", hidden=1),
			],
			"permissions": [],
		},
	)

	# Child: Multi product
	write_doctype(
		"quotation",
		"ic_quotation_product",
		{
			"name": "IC Quotation Product",
			"module": "Instacertify",
			"istable": 1,
			"editable_grid": 1,
			"fields": [
				field(fieldname="product_name", fieldtype="Data", label="Product Name", in_list_view=1, reqd=1),
				field(fieldname="product_description", fieldtype="Small Text", label="Description"),
				field(fieldname="services", fieldtype="Small Text", label="Services (comma-separated)", in_list_view=1),
				field(fieldname="applicable_standards", fieldtype="Data", label="Applicable Standards"),
				field(fieldname="estimated_value", fieldtype="Currency", label="Estimated Value", in_list_view=1, options="currency"),
				field(fieldname="currency", fieldtype="Link", options="Currency", label="Currency", hidden=1),
			],
			"permissions": [],
		},
	)

	# ---------- Laboratory ----------
	write_doctype(
		"laboratory",
		"ic_laboratory",
		{
			"name": "IC Laboratory",
			"autoname": "naming_series:",
			"naming_rule": "By \"Naming Series\" field",
			"module": "Instacertify",
			"track_changes": 1,
			"title_field": "laboratory_name",
			"search_fields": "laboratory_name,location,city,country",
			"image_field": "logo",
			"sort_field": "laboratory_name",
			"sort_order": "ASC",
			"fields": [
				field(fieldname="naming_series", fieldtype="Select", label="Series", options="LAB-.####", default="LAB-.####", reqd=1),
				field(fieldname="laboratory_name", fieldtype="Data", label="Laboratory Name", reqd=1, in_list_view=1),
				field(fieldname="logo", fieldtype="Attach Image", label="Logo"),
				field(fieldname="column_break_1", fieldtype="Column Break"),
				field(fieldname="status", fieldtype="Select", label="Status", options="Active\nInactive", default="Active", in_list_view=1),
				field(fieldname="location", fieldtype="Data", label="Location", in_list_view=1),
				field(fieldname="section_address", fieldtype="Section Break", label="Address & Contact"),
				field(fieldname="address", fieldtype="Small Text", label="Address"),
				field(fieldname="city", fieldtype="Data", label="City"),
				field(fieldname="state", fieldtype="Data", label="State"),
				field(fieldname="country", fieldtype="Link", options="Country", label="Country"),
				field(fieldname="column_break_2", fieldtype="Column Break"),
				field(fieldname="contact_person", fieldtype="Data", label="Contact Person"),
				field(fieldname="email", fieldtype="Data", label="Email", options="Email"),
				field(fieldname="phone", fieldtype="Data", label="Phone", options="Phone"),
				field(fieldname="website", fieldtype="Data", label="Website", options="URL"),
				field(fieldname="section_accreditation", fieldtype="Section Break", label="Accreditation"),
				field(fieldname="accreditation_details", fieldtype="Text Editor", label="Accreditation Details"),
				field(fieldname="accreditation_scope", fieldtype="Text Editor", label="Accreditation Scope"),
				field(fieldname="column_break_3", fieldtype="Column Break"),
				field(fieldname="scope_sheet", fieldtype="Attach", label="Laboratory Scope Sheet"),
				field(fieldname="accreditation_certificate", fieldtype="Attach", label="Accreditation Certificate"),
				field(fieldname="accreditation_scope_pdf", fieldtype="Attach", label="Accreditation Scope PDF"),
				field(fieldname="section_tests", fieldtype="Section Break", label="Available Tests & Scope"),
				field(fieldname="test_scopes", fieldtype="Table", label="Test Scopes", options="IC Laboratory Test Scope"),
				field(fieldname="section_notes", fieldtype="Section Break", label="Notes"),
				field(fieldname="remarks", fieldtype="Text Editor", label="Remarks"),
			],
			"permissions": STANDARD_PERMS,
		},
	)

	write_doctype(
		"laboratory",
		"ic_laboratory_test_scope",
		{
			"name": "IC Laboratory Test Scope",
			"module": "Instacertify",
			"istable": 1,
			"editable_grid": 1,
			"fields": [
				field(fieldname="test_name", fieldtype="Data", label="Test Name", in_list_view=1, reqd=1),
				field(fieldname="applicable_standard", fieldtype="Data", label="Applicable Standard", in_list_view=1),
				field(fieldname="category", fieldtype="Data", label="Category"),
				field(fieldname="purchase_price", fieldtype="Currency", label="Buying Price", in_list_view=1,
					permlevel=1, description="Lab buy / cost price — Admin only"),
				field(fieldname="selling_price", fieldtype="Currency", label="Suggested Selling Price", in_list_view=1,
					description="Default selling price on Testing quotations (editable per quote)"),
				field(fieldname="margin", fieldtype="Currency", label="Margin", in_list_view=1, permlevel=1,
					read_only=1, description="Suggested Selling − Buying (Admin only)"),
				field(fieldname="currency", fieldtype="Link", options="Currency", label="Currency", default="INR"),
				field(fieldname="is_active", fieldtype="Check", label="Active", default=1),
			],
			"permissions": [],
		},
	)

	# ---------- Testing Request ----------
	write_doctype(
		"testing",
		"ic_testing_request",
		{
			"name": "IC Testing Request",
			"autoname": "naming_series:",
			"naming_rule": "By \"Naming Series\" field",
			"module": "Instacertify",
			"is_submittable": 0,
			"track_changes": 1,
			"track_seen": 1,
			"title_field": "title",
			"search_fields": "customer,project,product,test_name",
			"sort_field": "modified",
			"sort_order": "DESC",
			"fields": [
				field(fieldname="naming_series", fieldtype="Select", label="Series", options="TR-.YYYY.-.####", default="TR-.YYYY.-.####", reqd=1),
				field(fieldname="title", fieldtype="Data", label="Title", reqd=1, in_list_view=1),
				field(fieldname="column_break_1", fieldtype="Column Break"),
				field(fieldname="status", fieldtype="Select", label="Status", in_list_view=1, default="Testing Request Created",
					options="Testing Request Created\nSample Awaited\nSample Received\nSample Dispatched to Laboratory\nTesting in Progress\nReport Available\nReport Uploaded\nReport Shared with Customer"),
				field(fieldname="section_links", fieldtype="Section Break", label="Links"),
				field(fieldname="customer", fieldtype="Link", options="Customer", label="Customer", reqd=1, in_list_view=1),
				field(fieldname="project", fieldtype="Link", options="Project", label="Project", in_list_view=1),
				field(fieldname="quotation", fieldtype="Link", options="Quotation", label="Quotation"),
				field(fieldname="column_break_2", fieldtype="Column Break"),
				field(fieldname="assigned_person", fieldtype="Link", options="User", label="Assigned Person", in_list_view=1),
				field(fieldname="priority", fieldtype="Select", label="Priority", options="Low\nMedium\nHigh\nUrgent", default="Medium"),
				field(fieldname="testing_timeline", fieldtype="Data", label="Testing Timeline"),
				field(fieldname="expected_completion", fieldtype="Date", label="Expected Completion"),
				field(fieldname="section_product", fieldtype="Section Break", label="Product & Test"),
				field(fieldname="product", fieldtype="Data", label="Product", reqd=1),
				field(fieldname="test_name", fieldtype="Data", label="Test", reqd=1),
				field(fieldname="applicable_standard", fieldtype="Data", label="Applicable Standard"),
				field(fieldname="column_break_3", fieldtype="Column Break"),
				field(fieldname="number_of_samples", fieldtype="Int", label="Number of Samples", default=1),
				field(fieldname="laboratory", fieldtype="Link", options="IC Laboratory", label="Laboratory"),
				field(fieldname="laboratory_location", fieldtype="Data", label="Laboratory Location", fetch_from="laboratory.location"),
				field(fieldname="section_items", fieldtype="Section Break", label="Additional Tests"),
				field(fieldname="test_items", fieldtype="Table", label="Test Items", options="IC Testing Request Item"),
				field(fieldname="section_report", fieldtype="Section Break", label="Report"),
				field(fieldname="test_report", fieldtype="Attach", label="Test Report"),
				field(fieldname="report_shared_on", fieldtype="Datetime", label="Report Shared On", read_only=1),
				field(fieldname="share_token", fieldtype="Data", label="Share Token", read_only=1, hidden=1),
				field(fieldname="qr_code", fieldtype="Attach Image", label="QR Code", read_only=1),
				field(fieldname="section_notes", fieldtype="Section Break", label="Notes"),
				field(fieldname="remarks", fieldtype="Text Editor", label="Remarks"),
			],
			"permissions": STANDARD_PERMS,
		},
	)

	write_doctype(
		"testing",
		"ic_testing_request_item",
		{
			"name": "IC Testing Request Item",
			"module": "Instacertify",
			"istable": 1,
			"editable_grid": 1,
			"fields": [
				field(fieldname="product", fieldtype="Data", label="Product", in_list_view=1),
				field(fieldname="test_name", fieldtype="Data", label="Test Name", in_list_view=1, reqd=1),
				field(fieldname="applicable_standard", fieldtype="Data", label="Applicable Standard", in_list_view=1),
				field(fieldname="number_of_samples", fieldtype="Int", label="Samples", default=1, in_list_view=1),
				field(fieldname="laboratory", fieldtype="Link", options="IC Laboratory", label="Laboratory", in_list_view=1),
			],
			"permissions": [],
		},
	)

	# ---------- Sample Tracking ----------
	write_doctype(
		"testing",
		"ic_sample_tracking",
		{
			"name": "IC Sample Tracking",
			"autoname": "naming_series:",
			"naming_rule": "By \"Naming Series\" field",
			"module": "Instacertify",
			"track_changes": 1,
			"title_field": "sample_description",
			"search_fields": "tracking_number,customer,project,sample_description",
			"sort_field": "modified",
			"sort_order": "DESC",
			"fields": [
				field(fieldname="naming_series", fieldtype="Select", label="Series", options="SMP-.YYYY.-.####", default="SMP-.YYYY.-.####", reqd=1),
				field(fieldname="tracking_number", fieldtype="Data", label="Sample Tracking Number", read_only=1, in_list_view=1,
					description="Auto-generated unique tracking number"),
				field(fieldname="column_break_1", fieldtype="Column Break"),
				field(fieldname="status", fieldtype="Select", label="Status", in_list_view=1, default="Sample Awaited",
					options="Sample Awaited\nSample Received\nSample Dispatched to Laboratory\nTesting in Progress\nReport Available\nReport Uploaded\nReport Shared with Customer"),
				field(fieldname="qr_code", fieldtype="Attach Image", label="QR Code", read_only=1),
				field(fieldname="section_links", fieldtype="Section Break", label="Links"),
				field(fieldname="customer", fieldtype="Link", options="Customer", label="Customer", reqd=1, in_list_view=1),
				field(fieldname="project", fieldtype="Link", options="Project", label="Project"),
				field(fieldname="testing_request", fieldtype="Link", options="IC Testing Request", label="Testing Request"),
				field(fieldname="column_break_2", fieldtype="Column Break"),
				field(fieldname="laboratory", fieldtype="Link", options="IC Laboratory", label="Laboratory"),
				field(fieldname="section_receipt", fieldtype="Section Break", label="Sample Receipt"),
				field(fieldname="sample_received_date", fieldtype="Date", label="Sample Received Date"),
				field(fieldname="quantity", fieldtype="Float", label="Quantity", default=1),
				field(fieldname="sample_description", fieldtype="Small Text", label="Sample Description", reqd=1, in_list_view=1),
				field(fieldname="column_break_3", fieldtype="Column Break"),
				field(fieldname="sample_condition", fieldtype="Select", label="Sample Condition",
					options="Good\nDamaged\nIncomplete\nOther"),
				field(fieldname="received_by", fieldtype="Link", options="User", label="Received By"),
				field(fieldname="dispatch_date", fieldtype="Date", label="Dispatched to Lab Date"),
				field(fieldname="section_notes", fieldtype="Section Break", label="Notes"),
				field(fieldname="remarks", fieldtype="Text Editor", label="Remarks"),
			],
			"permissions": STANDARD_PERMS,
		},
	)

	# ---------- Document Request ----------
	write_doctype(
		"documents",
		"ic_document_checklist_template",
		{
			"name": "IC Document Checklist Template",
			"autoname": "field:template_name",
			"naming_rule": "By fieldname",
			"module": "Instacertify",
			"track_changes": 1,
			"title_field": "template_name",
			"fields": [
				field(fieldname="template_name", fieldtype="Data", label="Template Name", reqd=1, unique=1, in_list_view=1),
				field(fieldname="service_name", fieldtype="Data", label="Service", in_list_view=1),
				field(fieldname="is_active", fieldtype="Check", label="Active", default=1),
				field(fieldname="section_items", fieldtype="Section Break", label="Required Documents"),
				field(fieldname="items", fieldtype="Table", label="Documents", options="IC Document Checklist Item"),
			],
			"permissions": STANDARD_PERMS,
		},
	)

	write_doctype(
		"documents",
		"ic_document_checklist_item",
		{
			"name": "IC Document Checklist Item",
			"module": "Instacertify",
			"istable": 1,
			"editable_grid": 1,
			"fields": [
				field(fieldname="document_name", fieldtype="Data", label="Document Name", in_list_view=1, reqd=1),
				field(fieldname="category", fieldtype="Select", label="Category", in_list_view=1,
					options="Customer Documents\nApplications\nTechnical Documents\nTesting Documents\nTest Reports\nCertificates\nFinal Deliverables\nProject Records\nOther"),
				field(fieldname="is_mandatory", fieldtype="Check", label="Mandatory", default=1, in_list_view=1),
				field(fieldname="description", fieldtype="Small Text", label="Description"),
			],
			"permissions": [],
		},
	)

	write_doctype(
		"documents",
		"ic_document_request",
		{
			"name": "IC Document Request",
			"autoname": "naming_series:",
			"naming_rule": "By \"Naming Series\" field",
			"module": "Instacertify",
			"track_changes": 1,
			"title_field": "title",
			"search_fields": "customer,project,title",
			"fields": [
				field(fieldname="naming_series", fieldtype="Select", label="Series", options="DR-.YYYY.-.####", default="DR-.YYYY.-.####", reqd=1),
				field(fieldname="title", fieldtype="Data", label="Title", reqd=1, in_list_view=1),
				field(fieldname="column_break_1", fieldtype="Column Break"),
				field(fieldname="status", fieldtype="Select", label="Status", in_list_view=1, default="Draft",
					options="Draft\nSent to Customer\nPartially Uploaded\nUnder Review\nCompleted\nCancelled"),
				field(fieldname="share_token", fieldtype="Data", label="Share Token", read_only=1, hidden=1),
				field(fieldname="section_links", fieldtype="Section Break", label="Links"),
				field(fieldname="customer", fieldtype="Link", options="Customer", label="Customer", reqd=1, in_list_view=1),
				field(fieldname="project", fieldtype="Link", options="Project", label="Project", in_list_view=1),
				field(fieldname="quotation", fieldtype="Link", options="Quotation", label="Quotation"),
				field(fieldname="column_break_2", fieldtype="Column Break"),
				field(fieldname="checklist_template", fieldtype="Link", options="IC Document Checklist Template", label="Checklist Template"),
				field(fieldname="assigned_to", fieldtype="Link", options="User", label="Assigned To"),
				field(fieldname="sent_on", fieldtype="Datetime", label="Sent On", read_only=1),
				field(fieldname="section_items", fieldtype="Section Break", label="Requested Documents"),
				field(fieldname="items", fieldtype="Table", label="Documents", options="IC Document Request Item"),
				field(fieldname="section_notes", fieldtype="Section Break", label="Notes"),
				field(fieldname="remarks", fieldtype="Text Editor", label="Remarks"),
			],
			"permissions": STANDARD_PERMS,
		},
	)

	write_doctype(
		"documents",
		"ic_document_request_item",
		{
			"name": "IC Document Request Item",
			"module": "Instacertify",
			"istable": 1,
			"editable_grid": 1,
			"fields": [
				field(fieldname="document_name", fieldtype="Data", label="Document Name", in_list_view=1, reqd=1),
				field(fieldname="category", fieldtype="Select", label="Category", in_list_view=1,
					options="Customer Documents\nApplications\nTechnical Documents\nTesting Documents\nTest Reports\nCertificates\nFinal Deliverables\nProject Records\nOther"),
				field(fieldname="is_mandatory", fieldtype="Check", label="Mandatory", default=1),
				field(fieldname="status", fieldtype="Select", label="Status", in_list_view=1, default="Pending",
					options="Pending\nUploaded\nApproved\nRejected\nReplacement Requested"),
				field(fieldname="uploaded_file", fieldtype="Attach", label="Uploaded File", in_list_view=1),
				field(fieldname="review_remarks", fieldtype="Small Text", label="Review Remarks"),
				field(fieldname="uploaded_on", fieldtype="Datetime", label="Uploaded On", read_only=1),
			],
			"permissions": [],
		},
	)

	write_doctype(
		"documents",
		"ic_project_record",
		{
			"name": "IC Project Record",
			"autoname": "naming_series:",
			"naming_rule": "By \"Naming Series\" field",
			"module": "Instacertify",
			"track_changes": 1,
			"title_field": "subject",
			"fields": [
				field(fieldname="naming_series", fieldtype="Select", label="Series", options="PRR-.YYYY.-.####", default="PRR-.YYYY.-.####", reqd=1),
				field(fieldname="subject", fieldtype="Data", label="Subject", reqd=1, in_list_view=1),
				field(fieldname="record_type", fieldtype="Select", label="Type", in_list_view=1, reqd=1,
					options="Project Remark\nImportant Commitment\nIncident\nImportant Customer Note\nDocument\nDeliverable\nCertificate\nOther"),
				field(fieldname="column_break_1", fieldtype="Column Break"),
				field(fieldname="customer", fieldtype="Link", options="Customer", label="Customer", in_list_view=1),
				field(fieldname="project", fieldtype="Link", options="Project", label="Project", in_list_view=1),
				field(fieldname="category", fieldtype="Select", label="Document Category",
					options="Customer Documents\nApplications\nTechnical Documents\nTesting Documents\nTest Reports\nCertificates\nFinal Deliverables\nProject Records\nOther"),
				field(fieldname="section_content", fieldtype="Section Break", label="Content"),
				field(fieldname="content", fieldtype="Text Editor", label="Content"),
				field(fieldname="attachment", fieldtype="Attach", label="Attachment"),
				field(fieldname="recorded_by", fieldtype="Link", options="User", label="Recorded By", default="__user"),
			],
			"permissions": STANDARD_PERMS,
		},
	)

	# ---------- Project Update ----------
	write_doctype(
		"project",
		"ic_project_update",
		{
			"name": "IC Project Update",
			"autoname": "naming_series:",
			"naming_rule": "By \"Naming Series\" field",
			"module": "Instacertify",
			"track_changes": 1,
			"title_field": "subject",
			"fields": [
				field(fieldname="naming_series", fieldtype="Select", label="Series", options="PU-.YYYY.-.####", default="PU-.YYYY.-.####", reqd=1),
				field(fieldname="project", fieldtype="Link", options="Project", label="Project", reqd=1, in_list_view=1),
				field(fieldname="subject", fieldtype="Data", label="Subject", reqd=1, in_list_view=1),
				field(fieldname="column_break_1", fieldtype="Column Break"),
				field(fieldname="update_date", fieldtype="Datetime", label="Update Date", default="Now", in_list_view=1),
				field(fieldname="progress_percentage", fieldtype="Percent", label="Progress %", in_list_view=1),
				field(fieldname="project_stage", fieldtype="Select", label="Project Stage",
					options="\nProject Initiated\nCustomer Documents Pending\nDocuments Under Review\nApplication Submitted\nSample Awaited\nSample Received\nSample Dispatched to Laboratory\nTesting in Progress\nReport Awaited\nReport Available\nCertification in Progress\nCertificate Available\nDelivered to Customer\nProject Completed"),
				field(fieldname="pending_action", fieldtype="Data", label="Pending Action"),
				field(fieldname="section_details", fieldtype="Section Break", label="Details"),
				field(fieldname="remarks", fieldtype="Text Editor", label="Remarks"),
				field(fieldname="attachment", fieldtype="Attach", label="Attachment"),
				field(fieldname="working_hours", fieldtype="Float", label="Working Hours"),
				field(fieldname="updated_by", fieldtype="Link", options="User", label="Updated By", default="__user"),
			],
			"permissions": STANDARD_PERMS,
		},
	)

	# ---------- Joining Letter ----------
	write_doctype(
		"hr",
		"ic_joining_letter",
		{
			"name": "IC Joining Letter",
			"autoname": "naming_series:",
			"naming_rule": "By \"Naming Series\" field",
			"module": "Instacertify",
			"track_changes": 1,
			"title_field": "employee_name",
			"fields": [
				field(fieldname="naming_series", fieldtype="Select", label="Series", options="JL-.YYYY.-.####", default="JL-.YYYY.-.####", reqd=1),
				field(fieldname="employee", fieldtype="Link", options="Employee", label="Employee", reqd=1, in_list_view=1),
				field(fieldname="employee_name", fieldtype="Data", label="Employee Name", fetch_from="employee.employee_name", in_list_view=1),
				field(fieldname="column_break_1", fieldtype="Column Break"),
				field(fieldname="joining_date", fieldtype="Date", label="Joining Date", in_list_view=1),
				field(fieldname="designation", fieldtype="Link", options="Designation", label="Designation", fetch_from="employee.designation"),
				field(fieldname="department", fieldtype="Link", options="Department", label="Department", fetch_from="employee.department"),
				field(fieldname="section_letter", fieldtype="Section Break", label="Letter"),
				field(fieldname="letter_content", fieldtype="Text Editor", label="Letter Content"),
				field(fieldname="qr_code", fieldtype="Attach Image", label="QR Code", read_only=1),
				field(fieldname="verification_code", fieldtype="Data", label="Verification Code", read_only=1),
			],
			"permissions": [
				perm(role="System Manager"),
				perm(role="IC Admin"),
				perm(role="IC Senior Operations", delete=0, create=0),
				perm(role="Employee", read=1, write=0, create=0, delete=0, export=0, share=0, email=0, print=1, report=0),
			],
		},
	)

	write_doctype(
		"hr",
		"ic_employee_document",
		{
			"name": "IC Employee Document",
			"autoname": "naming_series:",
			"naming_rule": "By \"Naming Series\" field",
			"module": "Instacertify",
			"track_changes": 1,
			"title_field": "document_title",
			"fields": [
				field(fieldname="naming_series", fieldtype="Select", label="Series", options="ED-.YYYY.-.####", default="ED-.YYYY.-.####", reqd=1),
				field(fieldname="employee", fieldtype="Link", options="Employee", label="Employee", reqd=1, in_list_view=1),
				field(fieldname="document_title", fieldtype="Data", label="Document Title", reqd=1, in_list_view=1),
				field(fieldname="column_break_1", fieldtype="Column Break"),
				field(fieldname="document_type", fieldtype="Select", label="Document Type", in_list_view=1,
					options="Joining Letter\nSalary Slip\nID Proof\nContract\nOther"),
				field(fieldname="attachment", fieldtype="Attach", label="Attachment"),
				field(fieldname="issue_date", fieldtype="Date", label="Issue Date"),
			],
			"permissions": [
				perm(role="System Manager"),
				perm(role="IC Admin"),
				perm(role="Employee", read=1, write=0, create=0, delete=0, export=0),
			],
		},
	)

	# ---------- Settings ----------
	write_doctype(
		"setup",
		"ic_settings",
		{
			"name": "IC Settings",
			"module": "Instacertify",
			"issingle": 1,
			"fields": [
				field(fieldname="section_branding", fieldtype="Section Break", label="Branding"),
				field(fieldname="company", fieldtype="Link", options="Company", label="Company"),
				field(fieldname="primary_color", fieldtype="Color", label="Primary Color", default="#0D47A1"),
				field(fieldname="accent_color", fieldtype="Color", label="Accent Color", default="#EC691F"),
				field(fieldname="column_break_1", fieldtype="Column Break"),
				field(fieldname="logo", fieldtype="Attach Image", label="Instacertify Logo"),
				field(fieldname="header_image", fieldtype="Attach Image", label="Header Asset"),
				field(fieldname="section_quotation", fieldtype="Section Break", label="Quotation Defaults"),
				field(fieldname="default_terms", fieldtype="Text Editor", label="Default Terms and Conditions"),
				field(fieldname="default_force_majeure", fieldtype="Text Editor", label="Default Force Majeure"),
				field(fieldname="quotation_validity_days", fieldtype="Int", label="Default Validity (Days)", default=30),
				field(fieldname="section_portal", fieldtype="Section Break", label="Customer Portal"),
				field(fieldname="portal_base_url", fieldtype="Data", label="Portal Base URL",
					description="Leave blank to use site URL"),
			],
			"permissions": [
				perm(role="System Manager"),
				perm(role="IC Admin"),
			],
		},
	)

	print("All DocTypes generated.")


if __name__ == "__main__":
	main()
