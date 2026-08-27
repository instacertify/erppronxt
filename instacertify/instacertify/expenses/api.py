# Copyright (c) Instacertify
"""Expense claim helpers."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist()
def set_expense_status(name: str, status: str, remarks: str | None = None) -> dict:
	"""Approve / reject / reimburse a submitted expense claim."""
	allowed = {"Approved", "Rejected", "Reimbursed"}
	if status not in allowed:
		frappe.throw(_("Invalid status"))
	if not frappe.has_permission("IC Expense Claim", "write"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	roles = set(frappe.get_roles())
	if not (roles & {"System Manager", "IC Admin", "IC Senior Operations", "IC Operations Manager", "Administrator"}):
		frappe.throw(_("Only managers can change expense status"), frappe.PermissionError)

	doc = frappe.get_doc("IC Expense Claim", name)
	if doc.docstatus != 1:
		frappe.throw(_("Submit the expense before approving"))

	updates = {"status": status}
	if remarks:
		updates["approver_remarks"] = remarks
	if status in ("Approved", "Reimbursed"):
		updates["approved_by"] = frappe.session.user
		updates["approved_on"] = now_datetime()
	doc.db_set(updates, update_modified=True)
	frappe.db.commit()
	return {"name": doc.name, "status": status}
