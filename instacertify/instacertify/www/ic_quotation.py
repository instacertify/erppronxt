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
	context.token = token
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
	name = frappe.db.get_value("Quotation", {"ic_share_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid quotation link"), frappe.PermissionError)
	doc = frappe.get_doc("Quotation", name)

	cost_items = []
	for row in doc.get("ic_cost_items") or []:
		cost_items.append(
			{
				"particulars": _plain(row.particulars or row.cost_component or row.description),
				"amount": row.amount,
				"payment_destination": _plain(row.payment_destination),
			}
		)

	test_items = []
	for row in doc.get("ic_test_items") or []:
		qty = row.number_of_samples or 1
		unit = row.suggested_selling_price
		if unit in (None, ""):
			unit = row.per_unit_charges
		if unit in (None, ""):
			unit = (flt(row.testing_charges) / qty) if qty else 0
		test_items.append(
			{
				"test_name": _plain(row.test_name),
				"applicable_standard": _plain(row.applicable_standard),
				"description": _plain(getattr(row, "description", None) or ""),
				"quantity": qty,
				"price": unit,
				"amount": row.testing_charges if row.testing_charges not in (None, "") else flt(unit) * qty,
			}
		)

	status = doc.ic_workflow_status or "Draft"
	can_decide = status in DECIDABLE

	# Payment / UPI details from company settings (for portal prompt)
	pay = {}
	try:
		s = frappe.get_cached_doc("IC Settings")
		pay = {
			"beneficiary_name": _plain(s.beneficiary_name) or "Instacertify Labs Private Limited",
			"bank_name": _plain(s.bank_name) or "YES BANK",
			"account_number": _plain(s.account_number) or "026485800001318",
			"ifsc_code": _plain(s.ifsc_code) or "YESB0000264",
			"upi_id": _plain(getattr(s, "upi_id", None)) or "yespay.bizsbiz31008@yesbankltd",
			"prompt": _("Use the UPI ID below to pay, or transfer to our bank account."),
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
		"currency": doc.currency,
		"transaction_date": str(doc.transaction_date or ""),
		"valid_till": str(doc.valid_till or ""),
		"cost_items": cost_items,
		"test_items": test_items,
		"can_decide": 1 if can_decide else 0,
		"is_final": 1 if status in ("Accepted", "Rejected / Lost") else 0,
		"pdf_url": f"/api/method/instacertify.quotation.events.download_quotation_pdf?token={token}",
		"payment": pay,
		"portal_notice": _(
			"This secure link is for reviewing the quotation only. You can download the PDF and send feedback — it does not provide access to Instacertify ERP."
		),
	}
