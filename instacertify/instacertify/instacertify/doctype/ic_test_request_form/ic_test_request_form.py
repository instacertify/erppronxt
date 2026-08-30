# Copyright (c) Instacertify
from frappe.model.document import Document


class ICTestRequestForm(Document):
	def before_save(self):
		if self.testing_request and not self.title:
			self.title = f"TRF — {self.testing_request}"
