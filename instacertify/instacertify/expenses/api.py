# Copyright (c) Instacertify
"""Expense claim helpers."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime, today


@frappe.whitelist()
def create_expense_claim(
	title: str,
	category: str,
	amount: float,
	description: str,
	expense_date: str | None = None,
	payment_mode: str | None = None,
	receipt: str | None = None,
	project: str | None = None,
	currency: str | None = None,
) -> dict:
	"""Create an expense claim for the current user (travel / petty / office / etc.)."""
	title = (title or "").strip()
	category = (category or "").strip() or "Travel"
	description = (description or "").strip()
	if not title:
		frappe.throw(_("Title is required"))
	if not description:
		frappe.throw(_("Description is required"))
	try:
		amount = float(amount or 0)
	except Exception:
		amount = 0
	if amount <= 0:
		frappe.throw(_("Amount must be greater than zero"))

	allowed = {
		"Travel",
		"Petty Cash",
		"Office",
		"Conveyance",
		"Lodging",
		"Meals",
		"Communication",
		"Other",
	}
	if category not in allowed:
		frappe.throw(_("Invalid category"))

	employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
	doc = frappe.get_doc(
		{
			"doctype": "IC Expense Claim",
			"title": title,
			"category": category,
			"expense_date": expense_date or today(),
			"amount": amount,
			"currency": currency or "INR",
			"description": description,
			"payment_mode": payment_mode or "Self",
			"receipt": receipt,
			"project": project,
			"claimed_by": frappe.session.user,
			"employee": employee,
			"status": "Draft",
		}
	)
	doc.insert()
	frappe.db.commit()
	return {"name": doc.name, "status": doc.status, "category": doc.category}


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
