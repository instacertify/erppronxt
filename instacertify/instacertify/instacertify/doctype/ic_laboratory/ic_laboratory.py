# Copyright (c) Instacertify
import frappe
from frappe.model.document import Document
from frappe.utils import strip_html


def _default_lab_initials(name: str) -> str:
	parts = [p for p in (name or "").replace("-", " ").replace("_", " ").split() if p]
	if not parts:
		return ""
	if len(parts) == 1:
		return parts[0][:4].upper()
	return "".join(p[0] for p in parts[:4]).upper()


class ICLaboratory(Document):
	def validate(self):
		for field in ("accreditation_scope", "accreditation_details", "remarks", "address"):
			val = self.get(field)
			if val and "<" in str(val):
				self.set(field, strip_html(val).strip())

		# Normalize contact fields so Testing & Samples lists stay usable
		if self.contact_person:
			self.contact_person = str(self.contact_person).strip()
		if self.meta.has_field("contact_designation") and self.contact_designation:
			self.contact_designation = str(self.contact_designation).strip()
		if self.phone:
			self.phone = str(self.phone).strip()
		if self.email:
			self.email = str(self.email).strip()

		if self.meta.has_field("lab_initials"):
			initials = (self.lab_initials or "").strip().upper()
			if not initials:
				initials = _default_lab_initials(self.laboratory_name or self.name)
			self.lab_initials = initials[:12]

		for row in self.test_scopes or []:
			purchase = float(row.purchase_price or 0)
			selling = float(row.selling_price or 0)
			row.margin = selling - purchase
			if not row.currency:
				row.currency = "INR"
			if row.is_active in (None, ""):
				row.is_active = 1
			if row.test_name:
				row.test_name = str(row.test_name).strip()
			if row.applicable_standard:
				row.applicable_standard = str(row.applicable_standard).strip()
			if row.get("description"):
				row.description = strip_html(str(row.description)).strip()
