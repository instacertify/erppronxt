# Copyright (c) Instacertify
from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname


def _slugify_template_id(value: str) -> str:
	text = (value or "").strip()
	if not text:
		return ""
	cleaned = "".join(ch if (ch.isalnum() or ch in (" ", "-", "_")) else " " for ch in text)
	cleaned = " ".join(cleaned.split()).strip()
	return cleaned[:140]


class ICDocumentChecklistTemplate(Document):
	def before_insert(self):
		if not (self.display_name or "").strip():
			self.display_name = (self.template_name or "").strip() or "Document Checklist"
		if not (self.template_name or "").strip():
			self.template_name = _slugify_template_id(self.display_name) or "Document Checklist"
		base = self.template_name
		if frappe.db.exists("IC Document Checklist Template", base):
			self.template_name = make_autoname(f"{base}-.#")

	def validate(self):
		if not self.items:
			frappe.throw(_("Add at least one collection row (Name + Collect As)"))
		for row in self.items:
			if not (row.document_name or "").strip():
				frappe.throw(_("Each row needs a Name"))
			# Backfill remark from legacy description
			if not row.get("remark") and row.get("description"):
				row.remark = row.description
			if not row.get("entry_type"):
				row.entry_type = "Upload File"
		if not (self.display_name or "").strip():
			self.display_name = (self.template_name or "").strip() or "Document Checklist"
		if not self.is_new():
			previous = self.get_doc_before_save()
			if previous and previous.template_name and self.template_name != previous.template_name:
				frappe.throw(
					_("Template ID cannot be changed after creation. Rename using Display Name instead."),
					title=_("Template ID locked"),
				)
