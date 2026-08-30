# Copyright (c) Instacertify
"""Billing currency + GST helpers for Indian / export customers."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt


INDIA = "India"
EXPORT_CURRENCY = "USD"
DOMESTIC_CURRENCY = "INR"


def get_customer_country(customer: str | None = None, customer_doc=None) -> str | None:
	"""Resolve customer country from Instacertify field, address, or territory."""
	if not customer and not customer_doc:
		return None
	doc = customer_doc or frappe.get_cached_doc("Customer", customer)

	country = (getattr(doc, "ic_country", None) or "").strip() or None
	if country:
		return country

	# Primary billing address country
	addr = frappe.db.sql(
		"""
		select a.country
		from `tabAddress` a
		inner join `tabDynamic Link` dl on dl.parent = a.name
		where dl.link_doctype = 'Customer' and dl.link_name = %s
		order by a.is_primary_address desc, a.creation desc
		limit 1
		""",
		doc.name,
	)
	if addr and addr[0][0]:
		return addr[0][0]

	return None


def default_currency_for_country(country: str | None) -> str:
	if not country or country == INDIA:
		return DOMESTIC_CURRENCY
	return EXPORT_CURRENCY


def is_export_customer(country: str | None) -> bool:
	return bool(country and country != INDIA)


def apply_customer_billing_defaults(doc, force: bool = False):
	"""On Customer: set billing currency from country unless manually overridden.

	- India → INR, gst_category Registered / Unregistered based on GSTIN
	- Other country → USD, gst_category Overseas
	User can still change default_currency / ic_primary_currency freely;
	set ic_currency_manual=1 to stop auto-overwrite on next country change.
	"""
	country = get_customer_country(customer_doc=doc)
	suggested = default_currency_for_country(country)

	manual = cint_flag(getattr(doc, "ic_currency_manual", 0))
	if force or not manual:
		if not doc.default_currency or force or _currency_follows_country(doc, country):
			doc.default_currency = suggested
		if hasattr(doc, "ic_primary_currency"):
			if (
				not doc.ic_primary_currency
				or force
				or _currency_follows_country(doc, country, field="ic_primary_currency")
			):
				doc.ic_primary_currency = suggested

	# GST category / GSTIN sync for india_compliance
	gstin = (getattr(doc, "gstin", None) or getattr(doc, "ic_gst_number", None) or "").strip().upper()
	if gstin and _is_valid_gstin(gstin):
		if doc.meta.has_field("gstin"):
			doc.gstin = gstin
		if doc.meta.has_field("ic_gst_number"):
			doc.ic_gst_number = gstin
	elif gstin and not _is_valid_gstin(gstin):
		# Don't push invalid demo/placeholder GSTIN into india_compliance field
		if doc.meta.has_field("gstin") and doc.gstin == gstin:
			doc.gstin = ""

	if doc.meta.has_field("gst_category"):
		if is_export_customer(country):
			doc.gst_category = "Overseas"
		elif doc.get("gstin") and _is_valid_gstin(doc.gstin):
			if doc.gst_category in (None, "", "Overseas", "Unregistered"):
				doc.gst_category = "Registered Regular"
		elif not doc.gst_category or doc.gst_category == "Overseas":
			doc.gst_category = "Unregistered"

	_ensure_customer_billing_address(doc, country)


def _ensure_customer_billing_address(doc, country: str | None):
	"""Create/update primary billing Address so place of supply follows ic_state / country."""
	if not doc.name or doc.name.startswith("new-"):
		return
	state = (getattr(doc, "ic_state", None) or "").strip()
	country = country or INDIA
	if not state and country == INDIA:
		return

	existing = frappe.db.sql(
		"""
		select a.name
		from `tabAddress` a
		inner join `tabDynamic Link` dl on dl.parent = a.name
		where dl.link_doctype = 'Customer' and dl.link_name = %s
		order by a.is_primary_address desc, a.is_shipping_address asc
		limit 1
		""",
		doc.name,
	)
	values = {
		"country": country,
		"is_primary_address": 1,
		"is_shipping_address": 0,
		"address_type": "Billing",
	}
	if state:
		values["state"] = state
		if frappe.get_meta("Address").has_field("gst_state") and country == INDIA:
			values["gst_state"] = state
	if doc.get("gstin") and frappe.get_meta("Address").has_field("gstin"):
		values["gstin"] = doc.gstin
	if doc.meta.has_field("gst_category") and frappe.get_meta("Address").has_field("gst_category"):
		values["gst_category"] = doc.gst_category

	if existing:
		frappe.db.set_value("Address", existing[0][0], values, update_modified=False)
		return

	addr = frappe.get_doc(
		{
			"doctype": "Address",
			"address_title": doc.customer_name or doc.name,
			"address_line1": getattr(doc, "ic_factory_address", None) or (doc.customer_name or doc.name),
			"city": state or country,
			"links": [{"link_doctype": "Customer", "link_name": doc.name}],
			**values,
		}
	)
	try:
		addr.insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Customer billing address")


def _is_valid_gstin(gstin: str) -> bool:
	if not gstin or len(gstin) != 15:
		return False
	try:
		from india_compliance.gst_india.utils import validate_gstin

		validate_gstin(gstin)
		return True
	except ImportError:
		return gstin[:2].isdigit() and gstin.isalnum()
	except Exception:
		return False


def apply_transaction_billing_defaults(doc, customer_field: str = "customer"):
	"""On Quotation / Sales Invoice: auto currency + GST tax template from customer country.

	Respects ic_currency_manual so users can switch back to INR or any other currency.
	"""
	try:
		from instacertify.setup.quotation_billing import ensure_contact_billing_field

		ensure_contact_billing_field()
	except Exception:
		pass

	customer = doc.get(customer_field) or (
		doc.get("party_name") if doc.doctype == "Quotation" and doc.get("quotation_to") == "Customer" else None
	)
	if not customer:
		return

	try:
		_ensure_company_address_on_transaction(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ensure company address on transaction")

	country = get_customer_country(customer)
	suggested = default_currency_for_country(country)
	manual = cint_flag(getattr(doc, "ic_currency_manual", 0))

	if not manual:
		# Only auto-set when empty or still on the previous default for that country pattern
		if not doc.currency or doc.currency in (DOMESTIC_CURRENCY, EXPORT_CURRENCY):
			if doc.currency != suggested:
				doc.currency = suggested
				_set_conversion_rate(doc)

	try:
		_apply_gst_tax_template(doc, customer, country)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "apply GST tax template")


def _ensure_company_address_on_transaction(doc):
	"""india_compliance requires company address to fetch Company GSTIN."""
	company = doc.get("company") or "Instacertify"
	if doc.meta.has_field("company_address") and not doc.get("company_address"):
		addr = frappe.db.sql(
			"""
			select a.name
			from `tabAddress` a
			inner join `tabDynamic Link` dl on dl.parent = a.name
			where dl.link_doctype = 'Company' and dl.link_name = %s
			order by a.is_your_company_address desc, a.is_primary_address desc
			limit 1
			""",
			company,
		)
		if addr:
			doc.company_address = addr[0][0]

	if doc.get("company_address") and doc.meta.has_field("company_gstin") and not doc.get("company_gstin"):
		gstin = frappe.db.get_value("Address", doc.company_address, "gstin") or frappe.db.get_value(
			"Company", company, "gstin"
		)
		if gstin:
			doc.company_gstin = gstin

	# Customer / party billing address for place of supply
	customer = doc.get("customer") or (
		doc.get("party_name") if doc.doctype == "Quotation" and doc.get("quotation_to") == "Customer" else None
	)
	if customer and doc.meta.has_field("customer_address") and not doc.get("customer_address"):
		caddr = None
		try:
			from frappe.contacts.doctype.address.address import get_default_address

			caddr = get_default_address("Customer", customer)
		except Exception:
			caddr = None
		if not caddr:
			row = frappe.db.sql(
				"""
				select a.name
				from `tabAddress` a
				inner join `tabDynamic Link` dl on dl.parent = a.name
				where dl.link_doctype = 'Customer' and dl.link_name = %s
				order by a.is_primary_address desc
				limit 1
				""",
				customer,
			)
			caddr = row[0][0] if row else None
		if caddr:
			doc.customer_address = caddr


def mark_currency_manual(doc):
	"""Call when user explicitly changes currency on the form."""
	if doc.meta.has_field("ic_currency_manual"):
		doc.ic_currency_manual = 1


def cint_flag(value) -> int:
	try:
		return 1 if int(value or 0) else 0
	except Exception:
		return 0


def _currency_follows_country(doc, country, field: str = "default_currency") -> bool:
	"""True if current currency still matches previous auto rule (safe to overwrite)."""
	current = getattr(doc, field, None)
	if not current:
		return True
	return current in (DOMESTIC_CURRENCY, EXPORT_CURRENCY)


def _set_conversion_rate(doc):
	company = doc.get("company") or frappe.db.get_single_value("Global Defaults", "default_company")
	company_currency = frappe.get_cached_value("Company", company, "default_currency") or DOMESTIC_CURRENCY
	if doc.currency == company_currency:
		doc.conversion_rate = 1
		return
	try:
		from erpnext.setup.utils import get_exchange_rate

		doc.conversion_rate = get_exchange_rate(
			doc.currency,
			company_currency,
			doc.get("transaction_date") or doc.get("posting_date") or frappe.utils.today(),
		)
	except Exception:
		# Fallback: leave existing / 1 — user can edit
		if not flt(doc.conversion_rate):
			doc.conversion_rate = 1


def _apply_gst_tax_template(doc, customer: str, country: str | None):
	"""Align GST category with Indian rules; leave tax rows to india_compliance.

	india_compliance validates CGST/SGST vs IGST from place of supply. We only:
	- mark Overseas for export (no domestic GST unless is_export_with_gst)
	- suggest a taxes_and_charges template when still empty (non-blocking hint)
	"""
	if is_export_customer(country):
		if doc.meta.has_field("gst_category"):
			doc.gst_category = "Overseas"
		if (
			doc.meta.has_field("is_export_with_gst")
			and not doc.get("is_export_with_gst")
			and not cint_flag(getattr(doc, "ic_tax_manual", 0))
		):
			if doc.get("taxes_and_charges") and "Output GST" in (doc.taxes_and_charges or ""):
				doc.taxes_and_charges = None
				doc.set("taxes", [])
		return

	# Domestic India
	if doc.meta.has_field("gst_category") and doc.gst_category in (None, "", "Overseas"):
		cust_gstin = frappe.db.get_value("Customer", customer, "gstin")
		doc.gst_category = "Registered Regular" if cust_gstin else "Unregistered"

	if cint_flag(getattr(doc, "ic_tax_manual", 0)) or doc.get("taxes_and_charges"):
		return

	# Only auto-apply when customer state is known (avoid IGST/CGST mismatch)
	if not _customer_gst_state(customer, doc):
		return

	template = _pick_domestic_gst_template(
		company=doc.get("company") or "Instacertify", customer=customer, doc=doc
	)
	if template:
		doc.taxes_and_charges = template
		_load_taxes_from_template(doc, template)


def _pick_domestic_gst_template(company: str, customer: str, doc) -> str | None:
	in_state = f"Output GST In-state - {frappe.get_cached_value('Company', company, 'abbr') or 'IC'}"
	out_state = f"Output GST Out-state - {frappe.get_cached_value('Company', company, 'abbr') or 'IC'}"
	# Fallback exact names created by india_compliance
	if not frappe.db.exists("Sales Taxes and Charges Template", in_state):
		in_state = "Output GST In-state - IC"
	if not frappe.db.exists("Sales Taxes and Charges Template", out_state):
		out_state = "Output GST Out-state - IC"

	company_state = _company_gst_state(company)
	customer_state = _customer_gst_state(customer, doc)

	if company_state and customer_state and company_state == customer_state:
		return in_state if frappe.db.exists("Sales Taxes and Charges Template", in_state) else None
	return out_state if frappe.db.exists("Sales Taxes and Charges Template", out_state) else None


def _company_gst_state(company: str) -> str | None:
	addr = frappe.db.sql(
		"""
		select coalesce(nullif(a.gst_state,''), nullif(a.state,''))
		from `tabAddress` a
		inner join `tabDynamic Link` dl on dl.parent = a.name
		where dl.link_doctype = 'Company' and dl.link_name = %s
		limit 1
		""",
		company,
	)
	if addr and addr[0][0]:
		return addr[0][0]
	return "Uttar Pradesh"


def _customer_gst_state(customer: str, doc=None) -> str | None:
	state = None
	if doc and doc.get("place_of_supply"):
		# place_of_supply often like "09-Uttar Pradesh"
		pos = doc.place_of_supply
		if "-" in pos:
			state = pos.split("-", 1)[1].strip()
	if not state:
		state = frappe.db.get_value("Customer", customer, "ic_state")
	if not state:
		row = frappe.db.sql(
			"""
			select coalesce(nullif(a.gst_state,''), nullif(a.state,''))
			from `tabAddress` a
			inner join `tabDynamic Link` dl on dl.parent = a.name
			where dl.link_doctype = 'Customer' and dl.link_name = %s
			order by a.is_primary_address desc
			limit 1
			""",
			customer,
		)
		if row and row[0][0]:
			state = row[0][0]
	return state


def _load_taxes_from_template(doc, template: str):
	try:
		from erpnext.controllers.accounts_controller import get_taxes_and_charges

		taxes = get_taxes_and_charges("Sales Taxes and Charges Template", template)
		doc.set("taxes", [])
		for tax in taxes:
			doc.append("taxes", tax)
		if hasattr(doc, "calculate_taxes_and_totals"):
			doc.calculate_taxes_and_totals()
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"Load taxes {template}")


@frappe.whitelist()
def get_billing_defaults(customer: str) -> dict:
	"""API for desk JS: country, suggested currency, gst category, tax template hint."""
	if not customer:
		return {}
	country = get_customer_country(customer)
	currency = default_currency_for_country(country)
	cust = frappe.get_cached_doc("Customer", customer)
	return {
		"country": country,
		"currency": currency,
		"is_export": is_export_customer(country),
		"gst_category": getattr(cust, "gst_category", None),
		"gstin": getattr(cust, "gstin", None) or getattr(cust, "ic_gst_number", None),
		"state": getattr(cust, "ic_state", None),
		"preferred_currency": getattr(cust, "ic_primary_currency", None) or cust.default_currency,
	}
