# Copyright (c) Instacertify
import frappe
from frappe.model.document import Document
from frappe.utils import strip_html


class ICLaboratory(Document):
	def validate(self):
		for field in ("accreditation_scope", "accreditation_details", "remarks"):
			val = self.get(field)
			if val and "<" in str(val):
				self.set(field, strip_html(val).strip())
		for row in self.test_scopes or []:
			purchase = float(row.purchase_price or 0)
			selling = float(row.selling_price or 0)
			row.margin = selling - purchase
			if not row.currency:
				row.currency = "INR"
			if row.is_active in (None, ""):
				row.is_active = 1
