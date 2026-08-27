# Copyright (c) Instacertify
from frappe.model.document import Document


class ProjectChatMessage(Document):
	def before_insert(self):
		import frappe

		if not self.sender:
			self.sender = frappe.session.user
		if not self.sender_name and self.sender:
			self.sender_name = frappe.db.get_value("User", self.sender, "full_name") or self.sender
