# Copyright (c) Instacertify
"""Document request portal APIs — customer uploads, remarks, sample POD/tracking."""

from __future__ import annotations

import secrets

import frappe
from frappe import _
from frappe.utils import now_datetime, today

from instacertify.documents.format_fields import (
	copy_format_field_flags,
	format_field_flags,
	is_format_field_included,
)


ALLOWED_UPLOAD_EXTENSIONS = {
	".pdf",
	".png",
	".jpg",
	".jpeg",
	".webp",
	".gif",
	".bmp",
	".tif",
	".tiff",
	".xls",
	".xlsx",
	".csv",
	".doc",
	".docx",
}

OPEN_DOC_STATUSES = {
	"Sent to Customer",
	"Partially Uploaded",
	"Under Review",
	"Draft",
}


def _assert_allowed_upload(file_url: str | None):
	"""Accept only local File attachments with allowlisted extensions."""
	from instacertify.utils.files import assert_internal_file

	url = assert_internal_file(file_url, "File")
	fname = url.rsplit("/", 1)[-1].lower()
	ext = ""
	if "." in fname:
		ext = "." + fname.rsplit(".", 1)[-1]
	if ext not in ALLOWED_UPLOAD_EXTENSIONS:
		frappe.throw(
			_(
				"File type not allowed. Upload PDF, image (PNG/JPG/WEBP/GIF/TIFF), Excel/CSV, or Word documents."
			)
		)
	return url


def _assert_doc_request_open(doc):
	status = doc.status or "Draft"
	if status not in OPEN_DOC_STATUSES and status not in (
		"Sent to Customer",
		"Partially Uploaded",
		"Under Review",
	):
		frappe.throw(_("This document checklist is closed for uploads"), frappe.PermissionError)


def _assert_manager():
	roles = set(frappe.get_roles())
	if roles.intersection({"System Manager", "IC Admin", "IC Senior Operations", "IC Operations Manager"}):
		return
	frappe.throw(_("Only managers or admin can delete or replace customer documents"))


def _portal_base_url() -> str:
	"""Prefer IC Settings portal base URL when set."""
	try:
		base = frappe.db.get_single_value("IC Settings", "portal_base_url")
		if base:
			return str(base).rstrip("/")
	except Exception:
		pass
	return frappe.utils.get_url().rstrip("/")


def _share_url_for(token: str) -> str:
	return f"{_portal_base_url()}/ic-documents/{token}"


def _row_remark(row) -> str:
	return (row.get("remark") or row.get("description") or "").strip()


def _entry_type(row) -> str:
	et = (row.get("entry_type") or "Upload File").strip()
	return et if et in ("Upload File", "Fill Field") else "Upload File"


@frappe.whitelist()
def share_document_request(document_request: str):
	doc = frappe.get_doc("IC Document Request", document_request)
	if not doc.customer:
		frappe.throw(_("Customer is mandatory before sharing the collection sheet"))
	if not doc.share_token:
		doc.share_token = secrets.token_urlsafe(24)
	doc.status = "Sent to Customer"
	doc.sent_on = now_datetime()
	url = _share_url_for(doc.share_token)
	if frappe.get_meta("IC Document Request").has_field("share_url"):
		doc.share_url = url
	doc.save(ignore_permissions=True)
	return {"url": url, "token": doc.share_token}


@frappe.whitelist()
def get_document_checklist_templates(service_name: str | None = None):
	"""Dropdown options for Project → Generate / Share Document List."""
	filters = {"is_active": 1}
	if service_name:
		filters["service_name"] = service_name
	fields = ["name", "template_name", "service_name"]
	meta = frappe.get_meta("IC Document Checklist Template")
	if meta.has_field("category"):
		fields.append("category")
	if meta.has_field("display_name"):
		fields.append("display_name")
	rows = frappe.get_all(
		"IC Document Checklist Template",
		filters=filters,
		fields=fields,
		order_by="template_name asc",
		limit_page_length=200,
	)
	out = []
	for r in rows:
		label = (r.get("display_name") or r.template_name or r.name or "").strip()
		if r.service_name:
			label = f"{label} ({r.service_name})"
		item_fields = ["document_name", "category", "is_mandatory"]
		item_meta = frappe.get_meta("IC Document Checklist Item")
		if item_meta.has_field("entry_type"):
			item_fields.append("entry_type")
		if item_meta.has_field("remark"):
			item_fields.append("remark")
		items = frappe.get_all(
			"IC Document Checklist Item",
			filters={"parent": r.name},
			fields=item_fields,
			order_by="idx asc",
		)
		out.append(
			{
				"name": r.name,
				"label": label,
				"template_name": r.template_name,
				"display_name": (r.get("display_name") or r.template_name or r.name or "").strip(),
				"service_name": r.service_name,
				"category": r.get("category"),
				"item_count": len(items),
				"items": items,
			}
		)
	return out


@frappe.whitelist()
def get_document_collection_library(active_only: int | bool = 1, category: str | None = None):
	"""Catalog for Document Collection Sheet Library page."""
	filters = {}
	if int(active_only or 0):
		filters["is_active"] = 1
	if category:
		filters["category"] = category
	fields = ["name", "template_name", "service_name", "is_active", "modified"]
	meta = frappe.get_meta("IC Document Checklist Template")
	if meta.has_field("category"):
		fields.append("category")
	if meta.has_field("notes"):
		fields.append("notes")
	if meta.has_field("display_name"):
		fields.append("display_name")
	rows = frappe.get_all(
		"IC Document Checklist Template",
		filters=filters,
		fields=fields,
		order_by="template_name asc",
		limit_page_length=500,
	)
	item_meta = frappe.get_meta("IC Document Checklist Item")
	out = []
	for r in rows:
		item_fields = ["document_name", "category", "is_mandatory", "description"]
		if item_meta.has_field("entry_type"):
			item_fields.append("entry_type")
		if item_meta.has_field("remark"):
			item_fields.append("remark")
		items = frappe.get_all(
			"IC Document Checklist Item",
			filters={"parent": r.name},
			fields=item_fields,
			order_by="idx asc",
		)
		uploads = sum(1 for i in items if _entry_type(i) == "Upload File")
		fills = sum(1 for i in items if _entry_type(i) == "Fill Field")
		shown = (r.get("display_name") or r.template_name or r.name or "").strip()
		out.append(
			{
				"name": r.name,
				"template_name": r.template_name or r.name,
				"display_name": shown,
				"service_name": r.service_name,
				"category": r.get("category") or "General",
				"is_active": r.is_active,
				"notes": r.get("notes"),
				"modified": str(r.modified or ""),
				"item_count": len(items),
				"upload_count": uploads,
				"fill_count": fills,
				"items": [
					{
						"document_name": i.document_name,
						"remark": _row_remark(i),
						"is_mandatory": i.is_mandatory,
						"entry_type": _entry_type(i),
						"category": i.category,
					}
					for i in items
				],
			}
		)
	return out


@frappe.whitelist()
def preview_checklist_template(template: str):
	"""Return document rows for a checklist template (dialog preview)."""
	if not template or not frappe.db.exists("IC Document Checklist Template", template):
		frappe.throw(_("Checklist template not found"))
	tmpl = frappe.get_doc("IC Document Checklist Template", template)
	shown = (tmpl.get("display_name") or tmpl.template_name or tmpl.name or "").strip()
	return {
		"name": tmpl.name,
		"template_name": tmpl.template_name,
		"display_name": shown,
		"service_name": tmpl.get("service_name"),
		"category": tmpl.get("category"),
		"items": [
			{
				"document_name": row.document_name,
				"category": row.category,
				"is_mandatory": row.is_mandatory,
				"remark": _row_remark(row),
				"entry_type": _entry_type(row),
				"description": row.get("description"),
			}
			for row in (tmpl.items or [])
		],
	}


@frappe.whitelist()
def create_document_request_for_project(
	project: str,
	title: str | None = None,
	template: str | None = None,
	force_new: int | bool = 0,
	replace_items: int | bool = 1,
):
	"""Create (or reuse) document checklist for a project and return share link + document list.

	`template` — IC Document Checklist Template (dropdown).
	`force_new` — always create a fresh Document Request.
	`replace_items` — when a template is chosen, replace the checklist rows.
	"""
	proj = frappe.get_doc("Project", project)
	if not proj.customer:
		frappe.throw(_("Project must have a Customer before sharing a document checklist"))

	force_new = int(force_new or 0)
	replace_items = int(replace_items if replace_items is not None else 1)

	doc = None
	if not force_new:
		existing = frappe.db.get_value(
			"IC Document Request",
			{"project": project, "status": ["in", ["Draft", "Sent to Customer", "Partially Uploaded"]]},
			"name",
			order_by="modified desc",
		)
		if existing:
			doc = frappe.get_doc("IC Document Request", existing)

	if not doc:
		doc = frappe.get_doc(
			{
				"doctype": "IC Document Request",
				"title": title or f"Documents for {proj.project_name or proj.name}",
				"customer": proj.customer,
				"project": proj.name,
				"assigned_to": frappe.session.user,
				"status": "Draft",
			}
		)
		doc.insert(ignore_permissions=True)
	elif title:
		doc.title = title
		doc.save(ignore_permissions=True)

	if template:
		if replace_items or not doc.items:
			apply_checklist_template(doc.name, template)
			doc.reload()
	elif not doc.items:
		# Sensible default checklist (documents only — sample dispatch is a separate sheet)
		for name, cat in (
			("Company Registration / GST", "Customer Documents"),
			("Product Datasheet / Specs", "Technical Documents"),
			("Authorization Letter", "Applications"),
		):
			doc.append(
				"items",
				{"document_name": name, "category": cat, "is_mandatory": 1, "status": "Pending"},
			)
		doc.save(ignore_permissions=True)

	_ensure_default_data_fields(doc)

	doc.reload()
	share = share_document_request(doc.name)
	return share | {
		"document_request": doc.name,
		"title": doc.title,
		"status": doc.status,
		"checklist_template": doc.get("checklist_template"),
		"documents": [
			{
				"document_name": row.document_name,
				"category": row.category,
				"is_mandatory": row.is_mandatory,
				"status": row.status,
			}
			for row in (doc.items or [])
		],
	}


def _ensure_default_data_fields(doc):
	"""Seed Data Collection Sheet rows when empty (skipped if format hides Additional Data Fields)."""
	doc.reload()
	if doc.get("data_fields"):
		return
	if not frappe.get_meta("IC Document Request").has_field("data_fields"):
		return
	if not is_format_field_included(doc, "include_data_fields"):
		return
	for label, mandatory in (
		("Application / Scheme Name", 1),
		("Factory / Manufacturing Address", 1),
		("Authorized Signatory Name & Designation", 1),
		("Product Technical Specs Summary", 0),
		("Any Other Information", 0),
	):
		doc.append(
			"data_fields",
			{"field_label": label, "is_mandatory": mandatory, "field_value": ""},
		)
	doc.save(ignore_permissions=True)


def _apply_template_rows(doc, tmpl):
	"""Map template rows onto request items (Upload File) and data_fields (Fill Field)."""
	copy_format_field_flags(tmpl, doc)
	doc.set("items", [])
	has_data_fields_meta = frappe.get_meta("IC Document Request").has_field("data_fields")
	if has_data_fields_meta:
		doc.set("data_fields", [])

	# If the template defines Fill Field rows, always keep Additional Data Fields on.
	tmpl_has_fill = any(_entry_type(r) == "Fill Field" for r in (tmpl.items or []))
	if tmpl_has_fill and doc.meta.has_field("include_data_fields"):
		doc.include_data_fields = 1

	for row in tmpl.items or []:
		remark = _row_remark(row)
		entry = _entry_type(row)
		if entry == "Fill Field":
			if not has_data_fields_meta:
				continue
			doc.append(
				"data_fields",
				{
					"field_label": row.document_name,
					"is_mandatory": 1 if row.is_mandatory else 0,
					"help_text": remark,
					"field_value": "",
				},
			)
		else:
			payload = {
				"document_name": row.document_name,
				"category": row.category or "Customer Documents",
				"is_mandatory": 1 if row.is_mandatory else 0,
				"status": "Pending",
			}
			if frappe.get_meta("IC Document Request Item").has_field("remark"):
				payload["remark"] = remark
			doc.append("items", payload)
	if frappe.get_meta("IC Document Request").has_field("checklist_template"):
		doc.checklist_template = tmpl.name


@frappe.whitelist()
def apply_checklist_template(document_request: str, template: str):
	doc = frappe.get_doc("IC Document Request", document_request)
	tmpl = frappe.get_doc("IC Document Checklist Template", template)
	_apply_template_rows(doc, tmpl)
	doc.save(ignore_permissions=True)
	# Seed defaults only when template had no Fill Field rows.
	if not (doc.get("data_fields") or []):
		_ensure_default_data_fields(doc)
	return frappe.get_doc("IC Document Request", doc.name).as_dict()


@frappe.whitelist()
def create_document_request_for_customer(
	customer: str,
	title: str | None = None,
	template: str | None = None,
	project: str | None = None,
	share: int | bool = 1,
):
	"""Create a Documents Collection Sheet mapped to a Customer (required) from a template."""
	if not customer:
		frappe.throw(_("Customer is mandatory"))
	if not frappe.db.exists("Customer", customer):
		frappe.throw(_("Customer {0} not found").format(customer))

	cust_name = frappe.db.get_value("Customer", customer, "customer_name") or customer
	doc = frappe.get_doc(
		{
			"doctype": "IC Document Request",
			"title": title or f"Documents for {cust_name}",
			"customer": customer,
			"project": project or None,
			"assigned_to": frappe.session.user,
			"status": "Draft",
		}
	)
	doc.insert(ignore_permissions=True)

	if template:
		if not frappe.db.exists("IC Document Checklist Template", template):
			frappe.throw(_("Template {0} not found").format(template))
		apply_checklist_template(doc.name, template)
		doc.reload()
	else:
		if not doc.items:
			for name, cat in (
				("Company Registration / GST", "Customer Documents"),
				("Product Datasheet / Specs", "Technical Documents"),
				("Authorization Letter", "Applications"),
			):
				doc.append(
					"items",
					{"document_name": name, "category": cat, "is_mandatory": 1, "status": "Pending"},
				)
			doc.save(ignore_permissions=True)
		_ensure_default_data_fields(doc)
		doc.reload()

	result = {
		"document_request": doc.name,
		"title": doc.title,
		"status": doc.status,
		"customer": doc.customer,
		"checklist_template": doc.get("checklist_template"),
	}
	if int(share or 0):
		result.update(share_document_request(doc.name))
		doc.reload()
		result["status"] = doc.status
		if doc.get("share_url"):
			result["share_url"] = doc.share_url
	return result


@frappe.whitelist()
def save_document_request_as_template(
	document_request: str,
	template_name: str,
	service_name: str | None = None,
	category: str | None = None,
):
	"""Save an existing collection sheet as a reusable library template."""
	name = (template_name or "").strip()
	if not name:
		frappe.throw(_("Template name is required"))
	if frappe.db.exists("IC Document Checklist Template", name):
		frappe.throw(_("Template {0} already exists").format(name), frappe.DuplicateEntryError)

	doc = frappe.get_doc("IC Document Request", document_request)
	tmpl = frappe.get_doc(
		{
			"doctype": "IC Document Checklist Template",
			"template_name": name,
			"display_name": name,
			"service_name": service_name or "",
			"category": category or "Custom",
			"is_active": 1,
			"notes": f"Saved from {doc.name}",
		}
	)
	copy_format_field_flags(doc, tmpl)
	for row in doc.items or []:
		tmpl.append(
			"items",
			{
				"document_name": row.document_name,
				"remark": row.get("remark") or "",
				"is_mandatory": 1 if row.is_mandatory else 0,
				"entry_type": "Upload File",
				"category": row.category or "Customer Documents",
			},
		)
	if is_format_field_included(doc, "include_data_fields"):
		for row in doc.get("data_fields") or []:
			tmpl.append(
				"items",
				{
					"document_name": row.field_label,
					"remark": row.get("help_text") or "",
					"is_mandatory": 1 if row.is_mandatory else 0,
					"entry_type": "Fill Field",
					"category": "Other",
				},
			)
	if not tmpl.items:
		frappe.throw(_("This sheet has no rows to save as a template"))
	tmpl.insert(ignore_permissions=True)
	return {
		"template": tmpl.name,
		"template_name": tmpl.template_name,
		"display_name": tmpl.get("display_name") or tmpl.template_name,
	}


@frappe.whitelist()
def rename_checklist_template_display_name(template: str, display_name: str):
	"""Change only the user-facing label — does not rename the document or break Links."""
	label = (display_name or "").strip()
	if not label:
		frappe.throw(_("Display name is required"))
	if not template or not frappe.db.exists("IC Document Checklist Template", template):
		frappe.throw(_("Checklist template not found"))
	frappe.has_permission("IC Document Checklist Template", "write", throw=True)
	doc = frappe.get_doc("IC Document Checklist Template", template)
	if not doc.meta.has_field("display_name"):
		frappe.throw(_("Display Name field is not available yet — run migrate."))
	doc.display_name = label
	doc.save(ignore_permissions=True)
	return {
		"template": doc.name,
		"template_name": doc.template_name,
		"display_name": doc.display_name,
	}


@frappe.whitelist(allow_guest=True)
def get_document_request_by_token(token: str):
	name = frappe.db.get_value("IC Document Request", {"share_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid document link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Document Request", name)
	flags = format_field_flags(doc)
	include_data = bool(flags.get("include_data_fields", 1))
	return {
		"title": doc.title,
		"status": doc.status,
		"format_fields": flags,
		"courier_name": doc.get("courier_name"),
		"tracking_number": doc.get("tracking_number"),
		"dispatch_date": str(doc.get("dispatch_date") or ""),
		"pod_attachment": doc.get("pod_attachment"),
		"sample_dispatch_remarks": doc.get("sample_dispatch_remarks"),
		"company_legal_name": doc.get("company_legal_name"),
		"gstin": doc.get("gstin"),
		"company_address": doc.get("company_address") if flags.get("include_company_address", 1) else None,
		"data_contact_person": doc.get("data_contact_person"),
		"data_contact_phone": doc.get("data_contact_phone"),
		"data_contact_email": doc.get("data_contact_email"),
		"product_name": doc.get("product_name") if flags.get("include_product_name", 1) else None,
		"product_model": doc.get("product_model") if flags.get("include_product_model", 1) else None,
		"product_brand": doc.get("product_brand") if flags.get("include_product_brand", 1) else None,
		"data_collection_remarks": (
			doc.get("data_collection_remarks")
			if flags.get("include_data_collection_remarks", 1)
			else None
		),
		"data_fields": [
			{
				"name": row.name,
				"idx": row.idx,
				"field_label": row.field_label,
				"field_value": row.field_value,
				"is_mandatory": row.is_mandatory,
				"help_text": row.get("help_text"),
			}
			for row in (doc.get("data_fields") or [])
		]
		if include_data
		else [],
		"portal_notice": _(
			"This is your Documents Collection Sheet and Data Collection Sheet. "
			"Upload requested documents and fill the data fields. "
			"For sample courier / AWB details use the separate Sample Dispatch link from your coordinator. "
			"This link does not provide access to Instacertify ERP."
		),
		"allowed_types": "PDF, images (PNG/JPG/WEBP/GIF/TIFF), Excel/CSV, Word",
		"items": [
			{
				"idx": row.idx,
				"name": row.name,
				"document_name": row.document_name,
				"remark": row.get("remark") or "",
				"category": row.category,
				"is_mandatory": row.is_mandatory,
				"status": row.status,
				"uploaded_file": row.uploaded_file,
				"customer_remarks": row.get("customer_remarks"),
				"review_remarks": row.review_remarks,
				"entry_type": "Upload File",
			}
			for row in doc.items
		],
	}


@frappe.whitelist(allow_guest=True)
def upload_document_item(token: str, item_name: str, file_url: str, remarks: str | None = None):
	parent = frappe.db.get_value("IC Document Request", {"share_token": token}, "name")
	if not parent:
		frappe.throw(_("Invalid document link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Document Request", parent)
	_assert_doc_request_open(doc)
	file_url = _assert_allowed_upload(file_url)
	updated_row = None
	for row in doc.items:
		if row.name == item_name:
			row.uploaded_file = file_url
			row.status = "Uploaded"
			row.uploaded_on = now_datetime()
			if remarks is not None:
				row.customer_remarks = remarks
			updated_row = row
			break
	if not updated_row:
		frappe.throw(_("Document item not found"))
	pending = any(r.status == "Pending" for r in doc.items)
	doc.status = "Partially Uploaded" if pending else "Under Review"
	doc.save(ignore_permissions=True)

	_log_customer_upload(doc, updated_row)
	try:
		from instacertify.crm.customer_data import ingest_document_upload

		ingest_document_upload(doc, updated_row)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "customer data ingest upload")
	_notify_upload(doc)
	return {"status": doc.status, "item": updated_row.name}


@frappe.whitelist(allow_guest=True)
def save_item_remarks(token: str, item_name: str, remarks: str):
	parent = frappe.db.get_value("IC Document Request", {"share_token": token}, "name")
	if not parent:
		frappe.throw(_("Invalid document link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Document Request", parent)
	_assert_doc_request_open(doc)
	for row in doc.items:
		if row.name == item_name:
			row.customer_remarks = remarks
			doc.save(ignore_permissions=True)
			return {"ok": 1}
	frappe.throw(_("Document item not found"))


@frappe.whitelist(allow_guest=True)
def save_data_collection(
	token: str,
	company_legal_name: str | None = None,
	gstin: str | None = None,
	company_address: str | None = None,
	data_contact_person: str | None = None,
	data_contact_phone: str | None = None,
	data_contact_email: str | None = None,
	product_name: str | None = None,
	product_model: str | None = None,
	product_brand: str | None = None,
	data_collection_remarks: str | None = None,
	data_fields: str | list | None = None,
):
	"""Customer submits Documents Collection Sheet — Data Collection section."""
	import json

	parent = frappe.db.get_value("IC Document Request", {"share_token": token}, "name")
	if not parent:
		frappe.throw(_("Invalid document link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Document Request", parent)
	_assert_doc_request_open(doc)

	if frappe.get_meta("IC Document Request").has_field("company_legal_name"):
		# Explicit None = leave unchanged; empty string clears the field.
		def _set_if_provided(field: str, value):
			if value is None:
				return
			doc.set(field, value)

		_set_if_provided("company_legal_name", company_legal_name)
		_set_if_provided("gstin", gstin)
		_set_if_provided("data_contact_person", data_contact_person)
		_set_if_provided("data_contact_phone", data_contact_phone)
		_set_if_provided("data_contact_email", data_contact_email)
		if is_format_field_included(doc, "include_company_address"):
			_set_if_provided("company_address", company_address)
		if is_format_field_included(doc, "include_product_name"):
			_set_if_provided("product_name", product_name)
		if is_format_field_included(doc, "include_product_model"):
			_set_if_provided("product_model", product_model)
		if is_format_field_included(doc, "include_product_brand"):
			_set_if_provided("product_brand", product_brand)
		if is_format_field_included(doc, "include_data_collection_remarks"):
			_set_if_provided("data_collection_remarks", data_collection_remarks)

	if (
		data_fields is not None
		and frappe.get_meta("IC Document Request").has_field("data_fields")
		and is_format_field_included(doc, "include_data_fields")
	):
		if isinstance(data_fields, str):
			try:
				data_fields = json.loads(data_fields)
			except Exception:
				data_fields = []
		by_name = {str(r.get("name")): r for r in (data_fields or []) if r.get("name")}
		for row in doc.get("data_fields") or []:
			payload = by_name.get(row.name)
			if payload is not None:
				# Allow clearing: always take provided value (may be "")
				row.field_value = payload.get("field_value") if "field_value" in payload else (row.field_value or "")
				if row.field_value is None:
					row.field_value = ""

	if doc.status == "Sent to Customer":
		doc.status = "Partially Uploaded"
	doc.save(ignore_permissions=True)
	try:
		from instacertify.crm.customer_data import ingest_data_collection

		ingest_data_collection(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "customer data ingest collection")
	_notify_upload(doc, subject_prefix="Data collection updated")
	return {"ok": 1, "status": doc.status}


@frappe.whitelist(allow_guest=True)
def upload_portal_file(token: str, filename: str | None = None, filedata: str | None = None):
	"""Guest-safe file upload for Documents Collection Sheet (avoids core upload_file Guest limits).

	Accepts multipart via frappe.request OR base64 `filedata` (data URL / raw b64).
	Returns {file_url, file_name}.
	"""
	import base64
	from pathlib import Path

	parent = frappe.db.get_value("IC Document Request", {"share_token": token}, "name")
	if not parent:
		frappe.throw(_("Invalid document link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Document Request", parent)
	_assert_doc_request_open(doc)

	content = None
	fname = (filename or "").strip() or "upload.bin"

	files = getattr(frappe.request, "files", None) if getattr(frappe, "request", None) else None
	if files:
		fobj = files.get("file") or next(iter(files.values()), None)
		if fobj:
			content = fobj.stream.read()
			fname = fobj.filename or fname

	if content is None and filedata:
		raw = str(filedata)
		if "," in raw and raw.strip().lower().startswith("data:"):
			raw = raw.split(",", 1)[1]
		try:
			content = base64.b64decode(raw)
		except Exception:
			frappe.throw(_("Invalid file data"))

	if not content:
		frappe.throw(_("No file uploaded"))

	if len(content) > 20 * 1024 * 1024:
		frappe.throw(_("File too large (max 20 MB)"))

	ext = Path(fname).suffix.lower()
	if ext not in ALLOWED_UPLOAD_EXTENSIONS:
		frappe.throw(_("File type not allowed. Use PDF, image, Excel/CSV, or Word."))

	from frappe.utils.file_manager import save_file

	file_doc = save_file(fname, content, "IC Document Request", doc.name, is_private=1)
	return {"file_url": file_doc.file_url, "file_name": file_doc.file_name, "name": file_doc.name}


@frappe.whitelist()
def push_document_request_to_customer(document_request: str):
	"""Staff: write current sheet uploads + filled data onto Customer Data Drive."""
	doc = frappe.get_doc("IC Document Request", document_request)
	if not doc.customer:
		frappe.throw(_("Customer is mandatory to map collected data"))
	from instacertify.crm.customer_data import ingest_data_collection, ingest_document_upload

	ingest_data_collection(doc)
	for row in doc.items or []:
		if row.get("uploaded_file"):
			try:
				ingest_document_upload(doc, row)
			except Exception:
				frappe.log_error(frappe.get_traceback(), "push upload to customer")
	return {"ok": 1, "customer": doc.customer}


@frappe.whitelist(allow_guest=True)
def save_sample_dispatch(
	token: str,
	courier_name: str | None = None,
	tracking_number: str | None = None,
	dispatch_date: str | None = None,
	pod_attachment: str | None = None,
	sample_dispatch_remarks: str | None = None,
):
	"""Customer submits sample courier / POD / tracking for backend access."""
	parent = frappe.db.get_value("IC Document Request", {"share_token": token}, "name")
	if not parent:
		frappe.throw(_("Invalid document link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Document Request", parent)
	_assert_doc_request_open(doc)
	values = {
		"courier_name": courier_name,
		"tracking_number": tracking_number,
		"dispatch_date": dispatch_date or None,
		"sample_dispatch_remarks": sample_dispatch_remarks,
	}
	if pod_attachment:
		_assert_allowed_upload(pod_attachment)
		values["pod_attachment"] = pod_attachment
	frappe.db.set_value("IC Document Request", parent, values, update_modified=True)
	doc = frappe.get_doc("IC Document Request", parent)

	_log_sample_dispatch(doc)
	_sync_sample_tracking(doc)
	try:
		from instacertify.crm.customer_data import ingest_sample_dispatch

		ingest_sample_dispatch(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "customer data ingest sample dispatch (docs)")
	_notify_upload(doc, subject_prefix="Sample dispatch updated")
	return {
		"ok": 1,
		"courier_name": doc.courier_name,
		"tracking_number": doc.tracking_number,
		"pod_attachment": doc.pod_attachment,
	}


@frappe.whitelist()
def clear_document_item(document_request: str, item_name: str):
	"""Manager/admin delete a customer upload so a new file can be provided."""
	_assert_manager()
	doc = frappe.get_doc("IC Document Request", document_request)
	for row in doc.items:
		if row.name == item_name:
			row.uploaded_file = None
			row.status = "Pending"
			row.uploaded_on = None
			break
	else:
		frappe.throw(_("Document item not found"))
	pending = any(r.status in ("Pending", "Replacement Requested") for r in doc.items)
	uploaded = any(r.status in ("Uploaded", "Approved") for r in doc.items)
	if pending and uploaded:
		doc.status = "Partially Uploaded"
	elif pending:
		doc.status = "Sent to Customer" if doc.share_token else "Draft"
	doc.save(ignore_permissions=True)
	_log_staff_action(doc, f"Cleared upload for {item_name}")
	return doc.as_dict()


@frappe.whitelist()
def replace_document_item(document_request: str, item_name: str, file_url: str, remarks: str | None = None):
	"""Manager/admin replace customer document with a new file."""
	_assert_manager()
	file_url = _assert_allowed_upload(file_url)
	doc = frappe.get_doc("IC Document Request", document_request)
	for row in doc.items:
		if row.name == item_name:
			row.uploaded_file = file_url
			row.status = "Uploaded"
			row.uploaded_on = now_datetime()
			if remarks:
				row.review_remarks = remarks
			break
	else:
		frappe.throw(_("Document item not found"))
	doc.status = "Under Review"
	doc.save(ignore_permissions=True)
	_log_staff_action(doc, f"Replaced document {item_name}", attachment=file_url)
	return doc.as_dict()


@frappe.whitelist()
def review_document_item(document_request: str, item_name: str, action: str, remarks: str | None = None):
	doc = frappe.get_doc("IC Document Request", document_request)
	for row in doc.items:
		if row.name == item_name:
			if action == "approve":
				row.status = "Approved"
			elif action == "reject":
				row.status = "Rejected"
			elif action == "replace":
				row.status = "Replacement Requested"
			row.review_remarks = remarks
			break
	if all(r.status == "Approved" for r in doc.items):
		doc.status = "Completed"
	else:
		doc.status = "Under Review"
	doc.save(ignore_permissions=True)
	if action in ("reject", "replace"):
		for user in set(filter(None, [doc.assigned_to, doc.owner])):
			if frappe.db.exists("User", user):
				frappe.get_doc(
					{
						"doctype": "Notification Log",
						"subject": f"Document {action}: {doc.name}",
						"email_content": remarks or "",
						"document_type": "IC Document Request",
						"document_name": doc.name,
						"for_user": user,
						"type": "Alert",
						"from_user": frappe.session.user,
					}
				).insert(ignore_permissions=True)
	return doc.as_dict()


def _notify_upload(doc, subject_prefix: str = "Customer document uploaded"):
	for user in set(filter(None, [doc.assigned_to, doc.owner, "Administrator"])):
		if frappe.db.exists("User", user):
			try:
				frappe.get_doc(
					{
						"doctype": "Notification Log",
						"subject": f"{subject_prefix}: {doc.name}",
						"email_content": f"{subject_prefix} for {doc.name}",
						"document_type": "IC Document Request",
						"document_name": doc.name,
						"for_user": user,
						"type": "Alert",
						"from_user": frappe.session.user if frappe.session.user != "Guest" else "Guest",
					}
				).insert(ignore_permissions=True)
			except Exception:
				pass


def _recorder():
	user = frappe.session.user
	if user and user != "Guest" and frappe.db.exists("User", user):
		return user
	return "Administrator"


def _log_customer_upload(doc, row):
	if not frappe.db.exists("DocType", "IC Project Record"):
		return
	try:
		frappe.get_doc(
			{
				"doctype": "IC Project Record",
				"subject": f"Customer uploaded: {row.document_name}",
				"record_type": "Document",
				"customer": doc.customer,
				"project": doc.project,
				"category": row.category or "Customer Documents",
				"content": f"<p>Uploaded via document checklist {doc.name}.</p>"
				+ (f"<p>Remarks: {frappe.utils.escape_html(row.customer_remarks)}</p>" if row.get("customer_remarks") else ""),
				"attachment": row.uploaded_file,
				"recorded_by": _recorder(),
			}
		).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "document upload project record")


def _log_sample_dispatch(doc):
	if not frappe.db.exists("DocType", "IC Project Record"):
		return
	try:
		frappe.get_doc(
			{
				"doctype": "IC Project Record",
				"subject": f"Sample dispatch: {doc.tracking_number or doc.courier_name or doc.name}",
				"record_type": "Important Customer Note",
				"customer": doc.customer,
				"project": doc.project,
				"category": "Other",
				"content": (
					f"<p>Courier: {frappe.utils.escape_html(doc.courier_name or '—')}</p>"
					f"<p>Tracking: {frappe.utils.escape_html(doc.tracking_number or '—')}</p>"
					f"<p>Dispatch date: {doc.dispatch_date or '—'}</p>"
					f"<p>{frappe.utils.escape_html(doc.sample_dispatch_remarks or '')}</p>"
				),
				"attachment": doc.pod_attachment,
				"recorded_by": _recorder(),
			}
		).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "sample dispatch project record")


def _log_staff_action(doc, subject: str, attachment: str | None = None):
	if not doc.project or not frappe.db.exists("DocType", "IC Project Record"):
		return
	try:
		frappe.get_doc(
			{
				"doctype": "IC Project Record",
				"subject": subject,
				"record_type": "Document",
				"customer": doc.customer,
				"project": doc.project,
				"category": "Customer Documents",
				"content": f"<p>{frappe.utils.escape_html(subject)}</p><p>By {frappe.session.user}</p>",
				"attachment": attachment,
				"recorded_by": frappe.session.user,
			}
		).insert(ignore_permissions=True)
	except Exception:
		pass


def _sync_sample_tracking(doc):
	"""Push courier/tracking onto linked project samples when possible."""
	if not doc.project or not doc.tracking_number:
		return
	if not frappe.db.exists("DocType", "IC Sample Tracking"):
		return
	samples = frappe.get_all(
		"IC Sample Tracking",
		filters={"project": doc.project},
		fields=["name"],
		limit_page_length=5,
		order_by="modified desc",
	)
	for s in samples:
		try:
			vals = {"courier_awb": doc.tracking_number}
			if doc.courier_name:
				vals["courier_name"] = doc.courier_name
			if doc.dispatch_date:
				vals["dispatch_date"] = doc.dispatch_date
			frappe.db.set_value("IC Sample Tracking", s.name, vals, update_modified=False)
		except Exception:
			pass
