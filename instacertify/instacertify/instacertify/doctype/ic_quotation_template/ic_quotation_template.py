# Copyright (c) Instacertify
from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname


def _slugify_template_id(value: str) -> str:
	"""Stable system id from a display label (safe for autoname)."""
	text = (value or "").strip()
	if not text:
		return ""
	cleaned = "".join(ch if (ch.isalnum() or ch in (" ", "-", "_")) else " " for ch in text)
	cleaned = " ".join(cleaned.split()).strip()
	return cleaned[:140]


class ICQuotationTemplate(Document):
	def before_insert(self):
		# Display name is what users rename; template_name stays the document name / Link key.
		if not (self.display_name or "").strip():
			self.display_name = (self.template_name or "").strip() or "Quotation Template"
		if not (self.template_name or "").strip():
			self.template_name = _slugify_template_id(self.display_name) or "Quotation Template"
		base = self.template_name
		if frappe.db.exists("IC Quotation Template", base):
			self.template_name = make_autoname(f"{base}-.#")

	def validate(self):
		if not (self.display_name or "").strip():
			self.display_name = (self.template_name or "").strip() or "Quotation Template"
		# Never allow changing the system Template ID after create — that would break Links / hierarchy.
		if not self.is_new():
			previous = self.get_doc_before_save()
			if previous and previous.template_name and self.template_name != previous.template_name:
				frappe.throw(
					"Template ID cannot be changed after creation. Rename using Display Name instead.",
					title="Template ID locked",
				)
