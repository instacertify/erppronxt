# Copyright (c) Instacertify
"""User create and password reset without a mandatory email."""

from __future__ import annotations

import frappe
from frappe.core.doctype.user.user import User


class ICUser(User):
	def validate(self):
		# A typed password is the login. Do not also require a welcome or reset email.
		if self.get("new_password"):
			self.send_welcome_email = 0
			self.flags.no_welcome_mail = True
		super().validate()

	def set_new_password(self, new_password=None):
		try:
			super().set_new_password(new_password)
		except frappe.OutgoingEmailError:
			# Password is already stored. A missing mailbox must not undo the reset.
			frappe.clear_last_message()
			frappe.log_error(
				title="User password saved without email",
				message=frappe.get_traceback(),
			)
