# Copyright (c) Instacertify
"""Ensure Document Collection Sheet templates have customisable rows + seed defaults."""

from __future__ import annotations

import frappe

from instacertify.documents.format_fields import INCLUDE_FIELDNAMES


def _backfill_include_flags(doctype: str):
	"""Existing rows get include_*=1 so optional format fields stay visible after migrate."""
	if not frappe.db.exists("DocType", doctype):
		return
	meta = frappe.get_meta(doctype)
	for flag in INCLUDE_FIELDNAMES:
		if not meta.has_field(flag):
			continue
		# NULL → 1 (new column). Leave intentional 0 alone after first backfill.
		frappe.db.sql(
			f"""
			UPDATE `tab{doctype}`
			SET `{flag}` = 1
			WHERE `{flag}` IS NULL
			"""
		)


def _one_time_include_flags_default():
	"""First deploy of format-field checks: force include=1 on all existing sheets/templates."""
	key = "ic_doc_format_fields_backfilled_v1"
	if frappe.db.get_global(key):
		return
	for doctype in ("IC Document Checklist Template", "IC Document Request"):
		if not frappe.db.exists("DocType", doctype):
			continue
		meta = frappe.get_meta(doctype)
		for flag in INCLUDE_FIELDNAMES:
			if not meta.has_field(flag):
				continue
			frappe.db.sql(f"UPDATE `tab{doctype}` SET `{flag}` = 1")
	frappe.db.set_global(key, "1")


def ensure_document_collection_templates():
	"""Backfill remark/entry_type and seed a starter template if the library is empty."""
	if not frappe.db.exists("DocType", "IC Document Checklist Template"):
		return

	_one_time_include_flags_default()
	_backfill_include_flags("IC Document Checklist Template")
	_backfill_include_flags("IC Document Request")

	item_meta = frappe.get_meta("IC Document Checklist Item")
	has_remark = item_meta.has_field("remark")
	has_entry = item_meta.has_field("entry_type")

	if has_remark or has_entry:
		# Copy legacy description → remark where empty
		templates = frappe.get_all("IC Document Checklist Template", pluck="name")
		for name in templates:
			doc = frappe.get_doc("IC Document Checklist Template", name)
			changed = False
			for row in doc.items or []:
				if has_remark and not row.get("remark") and row.get("description"):
					row.remark = row.description
					changed = True
				if has_entry and not row.get("entry_type"):
					row.entry_type = "Upload File"
					changed = True
			if changed:
				doc.save(ignore_permissions=True)

	if frappe.db.count("IC Document Checklist Template") == 0:
		doc = frappe.get_doc(
			{
				"doctype": "IC Document Checklist Template",
				"template_name": "Standard Customer Documents",
				"service_name": "General",
				"category": "General",
				"is_active": 1,
				"notes": "Starter template — customise Name / Remark / Mandatory / Collect As.",
				"include_company_address": 1,
				"include_product_name": 1,
				"include_product_model": 1,
				"include_product_brand": 1,
				"include_data_collection_remarks": 1,
				"include_data_fields": 1,
				"include_sample_dispatch": 0,
				"include_remarks": 1,
				"items": [
					{
						"document_name": "Company Registration / GST Certificate",
						"remark": "Clear scan of GST certificate or incorporation proof",
						"is_mandatory": 1,
						"entry_type": "Upload File",
						"category": "Customer Documents",
					},
					{
						"document_name": "Authorized Signatory Name",
						"remark": "Full name as on ID / letterhead",
						"is_mandatory": 1,
						"entry_type": "Fill Field",
						"category": "Customer Documents",
					},
					{
						"document_name": "Product Datasheet",
						"remark": "PDF or Word datasheet for the model under scope",
						"is_mandatory": 1,
						"entry_type": "Upload File",
						"category": "Technical Documents",
					},
					{
						"document_name": "Factory Address",
						"remark": "Complete manufacturing address with pin code",
						"is_mandatory": 1,
						"entry_type": "Fill Field",
						"category": "Customer Documents",
					},
					{
						"document_name": "Authorization Letter",
						"remark": "On company letterhead if applying via consultant",
						"is_mandatory": 0,
						"entry_type": "Upload File",
						"category": "Applications",
					},
				],
			}
		)
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
