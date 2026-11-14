# Copyright (c) Instacertify
"""User create and password reset without a mandatory email."""

from __future__ import annotations

import frappe
from frappe import _
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


@frappe.whitelist()
def change_user_password(user: str, new_password: str, old_password: str | None = None):
	"""Change a password. Your own account requires the current password. No email is sent."""
	if not user or not new_password:
		frappe.throw(_("Enter the new password."))
	user = str(user).strip()
	new_password = str(new_password)
	old_password = (old_password or "").strip() or None

	is_self = user == frappe.session.user
	roles = set(frappe.get_roles())
	can_reset_others = bool(roles.intersection({"System Manager", "IC Admin"}))
	if not is_self and not can_reset_others:
		frappe.throw(_("Not permitted to change this password."), frappe.PermissionError)
	if not is_self and not frappe.has_permission("User", "write", user):
		frappe.throw(_("Not permitted to change this password."), frappe.PermissionError)

	if is_self:
		if not old_password:
			frappe.throw(_("Enter your current password."))
		try:
			frappe.utils.password.check_password(user, old_password)
		except frappe.AuthenticationError:
			frappe.throw(_("Current password is incorrect."), frappe.AuthenticationError)
	elif old_password:
		try:
			frappe.utils.password.check_password(user, old_password)
		except frappe.AuthenticationError:
			frappe.throw(_("Current password is incorrect."), frappe.AuthenticationError)

	if len(new_password) < 8:
		frappe.throw(_("Use at least 8 characters."))

	try:
		from frappe.core.doctype.user.user import test_password_strength

		strength = test_password_strength(new_password, user=user) or {}
		feedback = strength.get("feedback") or {}
		if feedback.get("password_policy_validation_passed") is False:
			warning = feedback.get("warning") or _("Password does not meet the site policy.")
			frappe.throw(str(warning))
	except (ImportError, TypeError):
		pass

	doc = frappe.get_doc("User", user)
	doc.flags.ignore_permissions = True
	doc.send_welcome_email = 0
	doc.flags.no_welcome_mail = True
	doc.new_password = new_password
	doc.save(ignore_permissions=True)
	return {"ok": True}
