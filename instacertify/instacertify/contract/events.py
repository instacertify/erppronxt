# Copyright (c) Instacertify
"""IC Contract — create from quotation terms, share, guest accept-by-name, PDF."""

from __future__ import annotations

import secrets

import frappe
from frappe import _
from frappe.utils import now_datetime, strip_html


def _plain(value) -> str:
	if value in (None, ""):
		return ""
	return strip_html(str(value)).strip()


def _party_from_quotation(qt) -> tuple[str, str | None, str | None]:
	"""Return (party_name, lead, customer)."""
	lead = None
	customer = None
	party_name = qt.get("customer_name") or qt.get("party_name") or qt.name
	if qt.quotation_to == "Lead" and qt.party_name:
		lead = qt.party_name
		party_name = (
			frappe.db.get_value("Lead", lead, "ic_party_name")
			or frappe.db.get_value("Lead", lead, "company_name")
			or frappe.db.get_value("Lead", lead, "lead_name")
			or party_name
		)
		cust = frappe.db.get_value("Customer", {"lead_name": lead}, "name")
		if cust:
			customer = cust
	elif qt.quotation_to == "Customer" and qt.party_name:
		customer = qt.party_name
		party_name = frappe.db.get_value("Customer", customer, "customer_name") or party_name
		lead = frappe.db.get_value("Customer", customer, "lead_name")
	return party_name, lead, customer


def _build_contract_body(qt) -> str:
	parts = []
	blocks = [
		(_("Scope of Work"), qt.get("ic_scope_of_work")),
		(_("Deliverables"), qt.get("ic_deliverables")),
		(_("Payment Terms"), qt.get("ic_payment_terms")),
		(_("Terms and Conditions"), qt.get("ic_terms_and_conditions")),
		(_("Cancellation Policy"), qt.get("ic_cancellation_policy")),
		(_("Confidentiality"), qt.get("ic_confidentiality")),
		(_("Force Majeure"), qt.get("ic_force_majeure")),
	]
	for title, value in blocks:
		text = _plain(value)
		if not text:
			continue
		parts.append(f"<h3>{frappe.utils.escape_html(title)}</h3>")
		parts.append(f"<div>{value}</div>" if "<" in str(value or "") else f"<p>{frappe.utils.escape_html(text)}</p>")
	if not parts:
		parts.append("<p>Contract terms will be added from the quotation.</p>")
	return "\n".join(parts)


def _latest_quotation_for_lead(lead: str) -> str | None:
	rows = frappe.get_all(
		"Quotation",
		filters={"quotation_to": "Lead", "party_name": lead, "docstatus": ["<", 2]},
		fields=["name"],
		order_by="modified desc",
		limit=1,
	)
	if rows:
		return rows[0].name
	# Also via customer converted from lead
	customers = frappe.get_all("Customer", filters={"lead_name": lead}, pluck="name")
	if customers:
		rows = frappe.get_all(
			"Quotation",
			filters={"quotation_to": "Customer", "party_name": ["in", customers], "docstatus": ["<", 2]},
			fields=["name"],
			order_by="modified desc",
			limit=1,
		)
		if rows:
			return rows[0].name
	return None


@frappe.whitelist()
def create_contract_from_quotation(quotation: str):
	"""Create (or refresh draft) IC Contract from quotation commercial terms."""
	qt = frappe.get_doc("Quotation", quotation)
	party_name, lead, customer = _party_from_quotation(qt)

	existing = frappe.db.get_value(
		"IC Contract",
		{"quotation": qt.name, "status": ["in", ["Draft", "Shared with Customer"]]},
		"name",
	)
	if existing:
		doc = frappe.get_doc("IC Contract", existing)
		if doc.status == "Accepted":
			frappe.throw(_("An accepted contract already exists for this quotation: {0}").format(existing))
	else:
		doc = frappe.new_doc("IC Contract")
		doc.quotation = qt.name

	doc.title = f"Contract — {party_name}"
	doc.party_name = party_name
	doc.lead = lead
	doc.customer = customer
	doc.currency = qt.currency or "INR"
	doc.commercial_value = qt.get("ic_total_quoted_value") or qt.get("grand_total") or 0
	doc.scope_of_work = qt.get("ic_scope_of_work")
	doc.deliverables = qt.get("ic_deliverables")
	doc.payment_terms = qt.get("ic_payment_terms")
	doc.terms_and_conditions = qt.get("ic_terms_and_conditions")
	doc.cancellation_policy = qt.get("ic_cancellation_policy")
	doc.confidentiality = qt.get("ic_confidentiality")
	doc.force_majeure = qt.get("ic_force_majeure")
	doc.contract_body = _build_contract_body(qt)
	doc.status = "Draft"
	doc.share_token = ""
	doc.customer_signed_name = ""
	doc.accepted_on = None

	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)

	return {"contract": doc.name, "status": doc.status}


@frappe.whitelist()
def create_contract_from_lead(lead: str):
	"""Create contract from the lead's latest quotation terms."""
	quotation = _latest_quotation_for_lead(lead)
	if not quotation:
		frappe.throw(
			_("No quotation found for this lead. Create a quotation with terms first, then share the contract.")
		)
	return create_contract_from_quotation(quotation)


@frappe.whitelist()
def share_contract(contract: str):
	"""Generate / refresh guest share link for the contract."""
	doc = frappe.get_doc("IC Contract", contract)
	if doc.status == "Cancelled":
		frappe.throw(_("Cancelled contracts cannot be shared"))
	if not (doc.contract_body or doc.terms_and_conditions or doc.payment_terms):
		frappe.throw(_("Add contract terms before sharing with the customer"))

	token = doc.share_token or secrets.token_urlsafe(24)
	now = now_datetime()
	doc.db_set(
		{
			"share_token": token,
			"status": "Shared with Customer",
			"shared_on": now,
		},
		update_modified=True,
	)
	url = _portal_url(token)
	return {"url": url, "token": token, "contract": doc.name}


@frappe.whitelist()
def open_contract_for_edit(contract: str):
	"""Re-open shared/accepted contract for staff edits; invalidate old link until re-share."""
	doc = frappe.get_doc("IC Contract", contract)
	doc.db_set(
		{
			"status": "Draft",
			"share_token": "",
			"revision_number": int(doc.revision_number or 0) + 1,
		},
		update_modified=True,
	)
	return {"contract": doc.name, "status": "Draft", "revision_number": int(doc.revision_number or 0) + 1}


def _portal_url(token: str) -> str:
	base = None
	try:
		base = frappe.db.get_single_value("IC Settings", "portal_base_url")
	except Exception:
		base = None
	base = (base or "").rstrip("/")
	if base:
		return f"{base}/ic-contract/{token}"
	return frappe.utils.get_url(f"/ic-contract/{token}")


def _contract_from_token(token: str):
	if not (token or "").strip():
		frappe.throw(_("Invalid contract link"), frappe.PermissionError)
	name = frappe.db.get_value("IC Contract", {"share_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid contract link"), frappe.PermissionError)
	return frappe.get_doc("IC Contract", name)


def _guest_payload(doc, token: str) -> dict:
	status = doc.status or "Draft"
	can_sign = status == "Shared with Customer"
	return {
		"reference": doc.name,
		"title": _plain(doc.title),
		"party_name": _plain(doc.party_name),
		"status": status,
		"revision_number": doc.revision_number or 0,
		"currency": doc.currency or "INR",
		"commercial_value": doc.commercial_value,
		"scope_of_work": _plain(doc.scope_of_work),
		"deliverables": _plain(doc.deliverables),
		"payment_terms": _plain(doc.payment_terms),
		"terms_and_conditions": _plain(doc.terms_and_conditions),
		"cancellation_policy": _plain(doc.cancellation_policy),
		"confidentiality": _plain(doc.confidentiality),
		"force_majeure": _plain(doc.force_majeure),
		"contract_body": _plain(doc.contract_body),
		"customer_signed_name": _plain(doc.customer_signed_name),
		"customer_remarks": _plain(doc.customer_remarks),
		"accepted_on": str(doc.accepted_on or ""),
		"can_sign": 1 if can_sign else 0,
		"is_accepted": 1 if status == "Accepted" else 0,
		"pdf_url": f"/api/method/instacertify.contract.events.download_contract_pdf?token={token}",
		"portal_notice": _(
			"Review this contract carefully. Download a copy, then accept by typing your full name. "
			"This page does not provide access to Instacertify ERP."
		),
	}


@frappe.whitelist(allow_guest=True)
def get_contract(token: str):
	doc = _contract_from_token(token)
	return _guest_payload(doc, token)


@frappe.whitelist(allow_guest=True)
def customer_accept_contract(token: str, customer_name: str, remarks: str | None = None):
	"""Guest: accept / sign contract by typing their name."""
	doc = _contract_from_token(token)
	if doc.status == "Accepted":
		return {
			"status": "Accepted",
			"message": _("This contract was already accepted. Thank you."),
			"customer_signed_name": doc.customer_signed_name,
		}
	if doc.status != "Shared with Customer":
		frappe.throw(_("This contract is not open for acceptance right now."), frappe.PermissionError)

	name = (customer_name or "").strip()
	if len(name) < 2:
		frappe.throw(_("Please type your full name to accept and sign this contract."))

	# Soft match against party name when available (not a hard block — guest may use legal name)
	party = (doc.party_name or "").strip().lower()
	typed = name.lower()
	if party and party not in typed and typed not in party:
		# still allow, but require a reasonably long signature
		if len(name) < 3:
			frappe.throw(_("Please type your full legal name to accept this contract."))

	now = now_datetime()
	values = {
		"status": "Accepted",
		"customer_signed_name": name,
		"accepted_on": now,
	}
	if remarks:
		values["customer_remarks"] = remarks.strip()
	frappe.db.set_value("IC Contract", doc.name, values, update_modified=True)

	try:
		_notify_accepted(doc, name)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "IC Contract accept notify")

	return {
		"status": "Accepted",
		"message": _("Thank you. The contract has been accepted and signed."),
		"customer_signed_name": name,
	}


@frappe.whitelist(allow_guest=True)
def download_contract_pdf(token: str):
	"""Guest-safe PDF download for a shared contract."""
	doc = _contract_from_token(token)
	try:
		pdf = _contract_pdf_bytes(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "IC Contract portal PDF")
		frappe.throw(
			_("PDF could not be generated right now. Please try again or contact Instacertify."),
			title=_("PDF generation failed"),
		)
	frappe.local.response.filename = f"{doc.name}.pdf"
	frappe.local.response.filecontent = pdf
	frappe.local.response.type = "pdf"


def _contract_pdf_bytes(doc) -> bytes:
	from instacertify.utils.pdf import make_pdf

	sections = []
	for title, value in (
		(_("Scope of Work"), doc.scope_of_work),
		(_("Deliverables"), doc.deliverables),
		(_("Payment Terms"), doc.payment_terms),
		(_("Terms and Conditions"), doc.terms_and_conditions),
		(_("Cancellation Policy"), doc.cancellation_policy),
		(_("Confidentiality"), doc.confidentiality),
		(_("Force Majeure"), doc.force_majeure),
	):
		text = _plain(value)
		if text:
			sections.append(f"<h3>{frappe.utils.escape_html(title)}</h3><div style='white-space:pre-wrap'>{frappe.utils.escape_html(text)}</div>")

	body = _plain(doc.contract_body)
	if body and not sections:
		sections.append(f"<div style='white-space:pre-wrap'>{frappe.utils.escape_html(body)}</div>")

	sign_block = ""
	if doc.status == "Accepted" and doc.customer_signed_name:
		sign_block = f"""
		<div style="margin-top:28px;padding:14px;border:1px solid #c8dae6;border-radius:12px;">
			<p><b>Accepted / Signed by:</b> {frappe.utils.escape_html(doc.customer_signed_name)}</p>
			<p><b>Accepted on:</b> {frappe.utils.escape_html(str(doc.accepted_on or ''))}</p>
		</div>
		"""

	html = f"""
	<html><head><meta charset="utf-8"/>
	<style>
	body {{ font-family: Poppins, Segoe UI, sans-serif; color:#152833; font-size:12px; }}
	h1 {{ color:#065175; font-size:20px; margin:0 0 8px; }}
	h3 {{ color:#065175; margin:18px 0 6px; font-size:13px; }}
	.meta {{ color:#5a7382; margin-bottom:16px; }}
	</style></head><body>
	<h1>{frappe.utils.escape_html(doc.title or doc.name)}</h1>
	<div class="meta">
		<div><b>Reference:</b> {frappe.utils.escape_html(doc.name)} · Rev {int(doc.revision_number or 0)}</div>
		<div><b>Party:</b> {frappe.utils.escape_html(doc.party_name or '')}</div>
		<div><b>Status:</b> {frappe.utils.escape_html(doc.status or '')}</div>
		<div><b>Commercial value:</b> {frappe.utils.escape_html(str(doc.commercial_value or 0))} {frappe.utils.escape_html(doc.currency or '')}</div>
	</div>
	{''.join(sections)}
	{sign_block}
	</body></html>
	"""
	original_user = frappe.session.user
	elevated = False
	if original_user == "Guest":
		frappe.set_user("Administrator")
		elevated = True
	try:
		return make_pdf(html)
	finally:
		if elevated:
			frappe.set_user(original_user)


def _notify_accepted(doc, signed_name: str):
	recipients = []
	if doc.lead:
		owner = frappe.db.get_value("Lead", doc.lead, "lead_owner")
		if owner and owner not in ("Guest", "Administrator"):
			recipients.append(owner)
	for role in ("IC Admin", "Sales Manager"):
		for u in frappe.get_all("Has Role", filters={"role": role, "parenttype": "User"}, pluck="parent"):
			if u not in recipients and u not in ("Guest", "Administrator"):
				recipients.append(u)
	if not recipients:
		return
	frappe.sendmail(
		recipients=recipients[:8],
		subject=_("Contract accepted: {0}").format(doc.name),
		message=_(
			"Contract <b>{0}</b> for <b>{1}</b> was accepted / signed by <b>{2}</b>."
		).format(
			frappe.utils.escape_html(doc.name),
			frappe.utils.escape_html(doc.party_name or ""),
			frappe.utils.escape_html(signed_name),
		),
		delayed=True,
		now=False,
	)
