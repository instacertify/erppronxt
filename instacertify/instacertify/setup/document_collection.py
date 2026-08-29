# Copyright (c) Instacertify
"""Ensure Document Collection Sheet templates have customisable rows + seed defaults."""

from __future__ import annotations

import frappe


def ensure_document_collection_templates():
	"""Backfill remark/entry_type and seed a starter template if the library is empty."""
	if not frappe.db.exists("DocType", "IC Document Checklist Template"):
		return

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
