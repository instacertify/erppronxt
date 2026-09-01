# Copyright (c) Instacertify
"""Customer quotation portal."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, strip_html


no_cache = 1

DECIDABLE = (
	"Shared with Customer",
	"Customer Review",
	"Ready to Share",
	"Changes Requested",
)


def get_context(context):
	token = frappe.form_dict.get("name") or frappe.form_dict.get("token")
	# Also accept token from trailing path when form_dict is empty
	if not token and getattr(frappe, "request", None) and frappe.request.path:
		path = frappe.request.path.rstrip("/")
		if "/ic-quotation/" in path:
			token = path.split("/ic-quotation/", 1)[-1].strip("/") or None
	context.token = token or ""
	context.csrf_token = frappe.sessions.get_csrf_token()
	frappe.db.commit()
	context.no_cache = 1
	context.show_sidebar = False
	# Never render website chrome that could lead guests into Desk
	context.no_header = 1
	context.no_footer = 1


def _plain(value) -> str:
	if value in (None, ""):
		return ""
	return strip_html(str(value)).strip()


@frappe.whitelist(allow_guest=True)
def get_quotation(token: str):
	"""Guest-safe quotation payload — no Desk IDs, no raw HTML injection surface."""
	from instacertify.quotation.events import _quotation_from_token

	doc = _quotation_from_token(token)

	cost_items = []
	for row in doc.get("ic_cost_items") or []:
		qty = int(row.get("qty") or 1) or 1
		unit = flt(row.amount)
		total = row.get("total_amount")
		if total in (None, ""):
			total = unit * qty
		cost_items.append(
			{
				"particulars": _plain(row.particulars or row.cost_component or row.description),
				"description": _plain(row.description or ""),
				"unit_price": unit,
				"quantity": qty,
				"amount": flt(total),
				"payment_destination": _plain(row.payment_destination),
			}
		)

	test_items = []
	for row in doc.get("ic_test_items") or []:
		qty = int(row.number_of_samples or 1) or 1
		unit = row.suggested_selling_price
		if unit in (None, ""):
			unit = row.per_unit_charges
		if unit in (None, ""):
			unit = (flt(row.testing_charges) / qty) if qty else 0
		amount = row.testing_charges
		if amount in (None, ""):
			amount = flt(unit) * qty
		test_items.append(
			{
				"test_name": _plain(row.test_name),
				"applicable_standard": _plain(row.applicable_standard),
				"description": _plain(getattr(row, "description", None) or ""),
				"quantity": qty,
				"number_of_samples": qty,
				"price": unit,
				"amount": amount,
				"total_price": amount,
			}
		)

	status = doc.ic_workflow_status or "Draft"
	can_decide = status in DECIDABLE

	# Payment / UPI details from selected bank account on the quote
	pay = {}
	try:
		from instacertify.accounting.banking import bank_for_document

		b = bank_for_document(doc)
		pay = {
			"beneficiary_name": _plain(b.get("beneficiary_name")) or "Instacertify Labs Private Limited",
			"bank_name": _plain(b.get("bank_name")) or "",
			"account_number": _plain(b.get("account_number")) or "",
			"ifsc_code": _plain(b.get("ifsc_code")) or "",
			"upi_id": _plain(b.get("upi_id")) or "",
			"swift_code": _plain(b.get("swift_code")) or "",
			"branch_address": _plain(b.get("branch_address")) or "",
			"gstin": _plain(b.get("gstin")) or "09AAGCI8396C1Z7",
			"prompt": _("Use the UPI ID below to pay, or transfer to our bank account.")
			if b.get("upi_id")
			else _("Transfer to our bank account using the details below."),
		}
	except Exception:
		pay = {
			"beneficiary_name": "Instacertify Labs Private Limited",
			"bank_name": "YES BANK",
			"account_number": "026485800001318",
			"ifsc_code": "YESB0000264",
			"upi_id": "yespay.bizsbiz31008@yesbankltd",
			"prompt": _("Use the UPI ID below to pay, or transfer to our bank account."),
		}

	# Prefer customer-facing title over internal Quotation name
	display_ref = doc.get("customer_name") or doc.get("party_name") or "Quotation"
	token_safe = (token or "").strip()
	return {
		"reference": display_ref,
		"customer_name": _plain(doc.customer_name or doc.party_name),
		"ic_revision_number": doc.ic_revision_number,
		"ic_quotation_type": doc.ic_quotation_type,
		"ic_workflow_status": status,
		"ic_service_name": _plain(doc.ic_service_name),
		"ic_estimated_timeline": _plain(doc.ic_estimated_timeline),
		"ic_scope_of_work": _plain(doc.ic_scope_of_work),
		"ic_deliverables": _plain(doc.ic_deliverables),
		"ic_payment_terms": _plain(doc.ic_payment_terms),
		"ic_customer_remarks": _plain(doc.ic_customer_remarks),
		"ic_show_about": 0 if doc.get("ic_show_about") in (0, "0", False) else 1,
		"ic_show_deliverables": 0 if doc.get("ic_show_deliverables") in (0, "0", False) else 1,
		"ic_show_commercials": 0 if doc.get("ic_show_commercials") in (0, "0", False) else 1,
		"ic_show_payment_terms": 0 if doc.get("ic_show_payment_terms") in (0, "0", False) else 1,
		"ic_show_sample_required": 0 if doc.get("ic_show_sample_required") in (0, "0", False) else 1,
		"ic_show_timelines": 0 if doc.get("ic_show_timelines") in (0, "0", False) else 1,
		"ic_sample_required": _plain(doc.get("ic_sample_required")),
		"currency": doc.currency,
		"transaction_date": str(doc.transaction_date or ""),
		"valid_till": str(doc.valid_till or ""),
		"cost_items": cost_items,
		"test_items": test_items,
		"can_decide": 1 if can_decide else 0,
		"is_final": 1 if status in ("Accepted", "Rejected / Lost") else 0,
		"pdf_url": f"/api/method/instacertify.quotation.events.download_quotation_pdf?token={token_safe}",
		"payment": pay,
		"portal_notice": _(
			"This secure link is for reviewing the quotation only. You can download the PDF and send feedback — it does not provide access to Instacertify ERP."
		),
	}
