# Copyright (c) Instacertify
import frappe
from frappe import _
from frappe.model.document import Document


class ICDocumentRequest(Document):
	def validate(self):
		if not self.customer:
			frappe.throw(_("Customer is mandatory for a Documents Collection Sheet"))
		if self.share_token and self.meta.has_field("share_url") and not self.share_url:
			self.share_url = frappe.utils.get_url(f"/ic-documents/{self.share_token}")
