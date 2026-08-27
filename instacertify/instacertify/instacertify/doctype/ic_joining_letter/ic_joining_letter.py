# Copyright (c) Instacertify
import secrets

import frappe
from frappe.model.document import Document


class ICJoiningLetter(Document):
	def before_insert(self):
		if not self.verification_code:
			self.verification_code = secrets.token_hex(4).upper()

	def after_insert(self):
		self._ensure_qr()

	def on_update(self):
		if not self.qr_code:
			self._ensure_qr()

	def _ensure_qr(self):
		from instacertify.utils.qr import generate_and_attach_qr, verification_url

		try:
			generate_and_attach_qr(
				"IC Joining Letter",
				self.name,
				"qr_code",
				verification_url("IC Joining Letter", self.name),
			)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Joining Letter QR")
