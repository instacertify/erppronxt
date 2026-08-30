# Copyright (c) Instacertify
import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class ICProjectUpdate(Document):
	def before_insert(self):
		if not self.update_date:
			self.update_date = now_datetime()
		if not self.updated_by:
			self.updated_by = frappe.session.user

	def before_save(self):
		if not self.updated_by:
			self.updated_by = frappe.session.user
