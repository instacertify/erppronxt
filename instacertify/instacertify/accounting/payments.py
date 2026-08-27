# Copyright (c) Instacertify
"""Payment / funds notifications for project handlers."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import fmt_money


def on_submit_payment_entry(doc, method=None):
	"""Notify project handlers how much was received (and remaining outstanding)."""
	if doc.payment_type not in ("Receive",):
		return
	if doc.party_type != "Customer" or not doc.party:
		return

	amount = float(doc.received_amount or doc.paid_amount or 0)
	currency = doc.paid_to_account_currency or doc.paid_from_account_currency or doc.currency
	invoice_names = [
		row.reference_name
		for row in (doc.references or [])
		if row.reference_doctype == "Sales Invoice" and row.reference_name
	]

	projects = _projects_for_payment(doc.party, invoice_names)
	if not projects:
		# Still notify sales/ops that money came in for the customer
		_notify_users(
			["Administrator"],
			subject=_("Funds received from {0}").format(doc.party),
			body=_(
				"Payment {0}: {1} received from {2}. No linked project found yet."
			).format(doc.name, fmt_money(amount, currency=currency), doc.party),
			doctype="Payment Entry",
			name=doc.name,
		)
		return

	for project in projects:
		outstanding = _customer_outstanding(doc.party, project.company)
		recipients = _project_recipients(project)
		body = _(
			"Payment {pay} received: {amount}.\n"
			"Customer: {customer}\n"
			"Project: {project} ({stage})\n"
			"Outstanding for customer (approx): {outstanding}"
		).format(
			pay=doc.name,
			amount=fmt_money(amount, currency=currency),
			customer=doc.party,
			project=project.name,
			stage=project.ic_project_stage or project.status or "",
			outstanding=fmt_money(outstanding, currency=currency),
		)
		_notify_users(
			recipients,
			subject=_("Funds received for {0}: {1}").format(
				project.project_name or project.name, fmt_money(amount, currency=currency)
			),
			body=body,
			doctype="Project",
			name=project.name,
		)
		# Timeline note on project
		try:
			frappe.get_doc(
				{
					"doctype": "IC Project Update",
					"project": project.name,
					"subject": f"Funds received: {fmt_money(amount, currency=currency)}",
					"remarks": body.replace("\n", "<br>"),
					"progress_percentage": project.ic_progress_percentage,
					"project_stage": project.ic_project_stage,
					"pending_action": project.ic_pending_action,
				}
			).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Payment project update")


def _projects_for_payment(customer: str, invoice_names: list[str]):
	projects = []
	seen = set()
	# Via linked invoices → quotation → project
	for inv in invoice_names:
		qt = frappe.db.get_value("Sales Invoice", inv, "ic_quotation")
		if qt:
			for row in frappe.get_all(
				"Project",
				filters={"ic_quotation": qt},
				fields=[
					"name",
					"project_name",
					"status",
					"ic_project_stage",
					"ic_progress_percentage",
					"ic_pending_action",
					"ic_assigned_employee",
					"owner",
					"company",
				],
			):
				if row.name not in seen:
					seen.add(row.name)
					projects.append(row)
		# Also projects linked on SI
		proj = frappe.db.get_value("Sales Invoice", inv, "project")
		if proj and proj not in seen:
			seen.add(proj)
			row = frappe.db.get_value(
				"Project",
				proj,
				[
					"name",
					"project_name",
					"status",
					"ic_project_stage",
					"ic_progress_percentage",
					"ic_pending_action",
					"ic_assigned_employee",
					"owner",
					"company",
				],
				as_dict=True,
			)
			if row:
				projects.append(row)

	if projects:
		return projects

	# Fallback: open projects for this customer
	return frappe.get_all(
		"Project",
		filters={"customer": customer, "status": ["not in", ["Completed", "Cancelled"]]},
		fields=[
			"name",
			"project_name",
			"status",
			"ic_project_stage",
			"ic_progress_percentage",
			"ic_pending_action",
			"ic_assigned_employee",
			"owner",
			"company",
		],
		limit_page_length=10,
		order_by="modified desc",
	)


def _project_recipients(project) -> list[str]:
	from instacertify.project.events import get_project_assignee_users

	return get_project_assignee_users(project) + [project.owner, "Administrator"]


def _customer_outstanding(customer: str, company: str | None = None) -> float:
	filters = {"customer": customer, "docstatus": 1, "outstanding_amount": [">", 0]}
	if company:
		filters["company"] = company
	rows = frappe.get_all(
		"Sales Invoice",
		filters=filters,
		fields=["outstanding_amount"],
		limit_page_length=200,
	)
	return sum(float(r.outstanding_amount or 0) for r in rows)


def _notify_users(recipients, subject, body, doctype, name):
	for user in set(filter(None, recipients)):
		if not frappe.db.exists("User", user):
			continue
		try:
			frappe.get_doc(
				{
					"doctype": "Notification Log",
					"subject": subject,
					"email_content": body,
					"document_type": doctype,
					"document_name": name,
					"for_user": user,
					"type": "Alert",
					"from_user": frappe.session.user,
				}
			).insert(ignore_permissions=True)
		except Exception:
			pass
