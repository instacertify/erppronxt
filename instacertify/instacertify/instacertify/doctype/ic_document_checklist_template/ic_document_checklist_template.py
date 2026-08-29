# Copyright (c) Instacertify
import frappe
from frappe import _
from frappe.model.document import Document


class ICDocumentChecklistTemplate(Document):
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
