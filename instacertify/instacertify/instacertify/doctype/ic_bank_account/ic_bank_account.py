# Copyright (c) Instacertify
import frappe
from frappe.model.document import Document


class ICBankAccount(Document):
	def validate(self):
		self.account_title = (self.account_title or "").strip()
		if self.is_default and self.is_active:
			# Only one default active account
			others = frappe.get_all(
				"IC Bank Account",
				filters={"is_default": 1, "name": ["!=", self.name or ""]},
				pluck="name",
			)
			for name in others:
				frappe.db.set_value("IC Bank Account", name, "is_default", 0, update_modified=False)
