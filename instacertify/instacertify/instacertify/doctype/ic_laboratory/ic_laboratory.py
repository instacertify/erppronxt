# Copyright (c) Instacertify
import frappe
from frappe.model.document import Document


class ICLaboratory(Document):
	def validate(self):
		for row in self.test_scopes or []:
			purchase = float(row.purchase_price or 0)
			selling = float(row.selling_price or 0)
			row.margin = selling - purchase
