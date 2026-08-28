# Copyright (c) Instacertify
from frappe.model.document import Document


class ICExpenseClaim(Document):
	def before_insert(self):
		if not self.claimed_by:
			self.claimed_by = self.owner
		if not self.title and self.category:
			self.title = f"{self.category} expense"
		self.status = self.status or "Draft"

	def before_save(self):
		if self.docstatus == 0:
			self.status = "Draft"

	def on_submit(self):
		self.db_set("status", "Submitted")

	def on_cancel(self):
		self.db_set("status", "Rejected")
