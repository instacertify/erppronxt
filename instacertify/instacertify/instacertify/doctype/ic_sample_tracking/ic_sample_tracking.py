# Copyright (c) Instacertify
import secrets

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class ICSampleTracking(Document):
	def before_insert(self):
		if not self.tracking_number:
			self.tracking_number = make_autoname("SMP-TRK-.YYYY.-.#####")

	def after_insert(self):
		self._ensure_qr()

	def validate(self):
		if self.status == "Sample Received" and not self.sample_received_date:
			self.sample_received_date = frappe.utils.today()

	def on_update(self):
		if not self.qr_code:
			self._ensure_qr()

	def _ensure_qr(self):
		from instacertify.utils.qr import generate_and_attach_qr, verification_url

		try:
			generate_and_attach_qr(
				"IC Sample Tracking",
				self.name,
				"qr_code",
				verification_url("IC Sample Tracking", self.name),
			)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Sample QR")
