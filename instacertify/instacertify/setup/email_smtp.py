# Copyright (c) Instacertify
"""Outgoing SMTP setup so password reset and other mail can be sent."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint


def _require_email_admin():
	roles = set(frappe.get_roles())
	if not roles & {"System Manager", "IC Admin"}:
		frappe.throw(_("Only a System Manager can configure outgoing email."), frappe.PermissionError)


@frappe.whitelist()
def outgoing_email_ready():
	"""Whether a default outgoing mailbox exists. No secrets."""
	if not frappe.db.exists("DocType", "Email Account"):
		return {"configured": 0}
	name = frappe.db.get_value("Email Account", {"default_outgoing": 1, "enable_outgoing": 1}, "name")
	return {"configured": 1 if name else 0}


@frappe.whitelist()
def get_outgoing_email():
	"""Non-secret status of the default outgoing mailbox."""
	_require_email_admin()
	if not frappe.db.exists("DocType", "Email Account"):
		return {"configured": 0}
	row = frappe.db.get_value(
		"Email Account",
		{"default_outgoing": 1},
		["name", "email_id", "smtp_server", "smtp_port", "awaiting_password"],
		as_dict=True,
	)
	if not row:
		return {"configured": 0}
	row["configured"] = 1
	row["awaiting_password"] = cint(row.awaiting_password)
	return row


@frappe.whitelist()
def save_outgoing_email(
	email_id: str,
	smtp_server: str,
	smtp_port: int | str = 587,
	password: str | None = None,
	send_test: int | str = 0,
):
	"""Create or update the default outgoing Email Account. Password is stored by Frappe, not in IC Settings."""
	_require_email_admin()
	email_id = (email_id or "").strip()
	smtp_server = (smtp_server or "").strip()
	port = cint(smtp_port) or 587
	if not email_id or "@" not in email_id:
		frappe.throw(_("Enter a valid From email address."))
	if not smtp_server:
		frappe.throw(_("Enter the SMTP server, for example smtp.gmail.com."))

	name = frappe.db.get_value("Email Account", {"email_id": email_id}, "name")
	if name:
		doc = frappe.get_doc("Email Account", name)
	else:
		doc = frappe.new_doc("Email Account")
		doc.email_id = email_id
		doc.email_account_name = email_id

	doc.enable_outgoing = 1
	doc.default_outgoing = 1
	doc.enable_incoming = 0
	doc.smtp_server = smtp_server
	doc.smtp_port = port
	meta = frappe.get_meta("Email Account")
	use_ssl = 1 if port == 465 else 0
	if meta.has_field("use_ssl_for_outgoing"):
		doc.use_ssl_for_outgoing = use_ssl
	if meta.has_field("use_tls"):
		doc.use_tls = 0 if use_ssl else 1
	if meta.has_field("no_smtp_authentication"):
		doc.no_smtp_authentication = 0
	if meta.has_field("login_id_is_different"):
		doc.login_id_is_different = 0
	if password:
		doc.password = password
		if meta.has_field("awaiting_password"):
			doc.awaiting_password = 0
	elif doc.is_new():
		frappe.throw(_("Enter the mailbox password or app password."))

	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	# One default outgoing mailbox.
	others = frappe.get_all(
		"Email Account",
		filters={"default_outgoing": 1, "name": ["!=", doc.name]},
		pluck="name",
	)
	for other in others:
		frappe.db.set_value("Email Account", other, "default_outgoing", 0, update_modified=False)

	tested = 0
	if cint(send_test):
		frappe.sendmail(
			recipients=[email_id],
			subject=_("Instacertify SMTP test"),
			message=_("Outgoing email is configured. Password reset and other messages can be sent."),
			now=True,
		)
		tested = 1

	frappe.db.commit()
	return {"name": doc.name, "email_id": doc.email_id, "smtp_server": smtp_server, "tested": tested}
