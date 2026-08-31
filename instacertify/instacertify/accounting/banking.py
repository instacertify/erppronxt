# Copyright (c) Instacertify
"""Resolve bank account details for quotations / invoices / print."""

from __future__ import annotations

from typing import Any

import frappe

# Stable seed titles (also used as DocType names via autoname field:account_title)
YES_BANK_TITLE = "YES BANK"
IOB_TITLE = "Indian Overseas Bank"

YES_BANK = {
	"account_title": YES_BANK_TITLE,
	"beneficiary_name": "Instacertify Labs Private Limited",
	"bank_name": "YES BANK",
	"account_number": "026485800001318",
	"ifsc_code": "YESB0000264",
	"swift_code": "YESBINBBDEL (For International USD Transfers)",
	"upi_id": "yespay.bizsbiz31008@yesbankltd",
	"branch_address": (
		"Ground, Mezzanine & First Floor, Plot No. 6, Basant Lok, "
		"Vasant Vihar, New Delhi, Delhi – 110057, India"
	),
	"gstin": "09AAGCI8396C1Z7",
	"is_default": 1,
	"is_active": 1,
}

IOB_BANK = {
	"account_title": IOB_TITLE,
	"beneficiary_name": "Instacertify Labs Private Limited",
	"bank_name": "Indian Overseas Bank",
	"account_number": "317802000000364",
	"ifsc_code": "IOBA0003178",
	"swift_code": "IOBAINBBE45 (For transfer in USD)",
	"upi_id": "",
	"branch_address": "Ground Floor, Block CH, Chhajarsi Sector 63 Noida - 201307",
	"gstin": "09AAGCI8396C1Z7",
	"is_default": 0,
	"is_active": 1,
}


def ensure_bank_accounts() -> None:
	"""Create YES BANK + Indian Overseas Bank if missing; sync titles from IC Settings when empty."""
	if not frappe.db.exists("DocType", "IC Bank Account"):
		return

	settings = None
	try:
		settings = frappe.get_single("IC Settings")
	except Exception:
		settings = None

	yes = dict(YES_BANK)
	if settings:
		# Prefer existing IC Settings values for the default YES BANK row
		yes["beneficiary_name"] = settings.get("beneficiary_name") or yes["beneficiary_name"]
		yes["bank_name"] = settings.get("bank_name") or yes["bank_name"]
		yes["account_number"] = settings.get("account_number") or yes["account_number"]
		yes["ifsc_code"] = settings.get("ifsc_code") or yes["ifsc_code"]
		yes["swift_code"] = settings.get("swift_code") or yes["swift_code"]
		yes["upi_id"] = settings.get("upi_id") or yes["upi_id"]
		yes["branch_address"] = settings.get("bank_branch_address") or yes["branch_address"]
		yes["gstin"] = settings.get("gstin") or yes["gstin"]

	for payload in (yes, dict(IOB_BANK)):
		_upsert_bank_account(payload)

	# Ensure exactly one default
	defaults = frappe.get_all(
		"IC Bank Account", filters={"is_default": 1, "is_active": 1}, pluck="name"
	)
	if not defaults:
		if frappe.db.exists("IC Bank Account", YES_BANK_TITLE):
			frappe.db.set_value("IC Bank Account", YES_BANK_TITLE, "is_default", 1)
	elif len(defaults) > 1:
		for name in defaults[1:]:
			frappe.db.set_value("IC Bank Account", name, "is_default", 0)

	# Point IC Settings.default_bank_account at the default row when blank
	try:
		default_name = get_default_bank_account_name()
		if default_name and frappe.db.exists("DocType", "IC Settings"):
			meta = frappe.get_meta("IC Settings")
			if meta.has_field("default_bank_account"):
				cur = frappe.db.get_single_value("IC Settings", "default_bank_account")
				if not cur:
					frappe.db.set_single_value("IC Settings", "default_bank_account", default_name)
	except Exception:
		pass


def _upsert_bank_account(payload: dict[str, Any]) -> str:
	title = payload["account_title"]
	if frappe.db.exists("IC Bank Account", title):
		doc = frappe.get_doc("IC Bank Account", title)
		# Fill blanks only — never overwrite user edits
		changed = False
		for key, val in payload.items():
			if key == "account_title":
				continue
			if key in ("is_default", "is_active"):
				continue
			if not doc.get(key) and val:
				doc.set(key, val)
				changed = True
		if changed:
			doc.save(ignore_permissions=True)
		return doc.name

	doc = frappe.get_doc({"doctype": "IC Bank Account", **payload})
	doc.insert(ignore_permissions=True)
	return doc.name


def get_default_bank_account_name() -> str | None:
	if not frappe.db.exists("DocType", "IC Bank Account"):
		return None
	# Prefer IC Settings pointer when set
	try:
		meta = frappe.get_meta("IC Settings")
		if meta.has_field("default_bank_account"):
			pref = frappe.db.get_single_value("IC Settings", "default_bank_account")
			if pref and frappe.db.exists("IC Bank Account", pref):
				return pref
	except Exception:
		pass
	name = frappe.db.get_value(
		"IC Bank Account", {"is_default": 1, "is_active": 1}, "name"
	)
	if name:
		return name
	return frappe.db.get_value("IC Bank Account", {"is_active": 1}, "name", order_by="creation asc")


def bank_as_dict(name: str | None = None) -> dict[str, Any]:
	"""Return printable bank fields; falls back to IC Settings / YES BANK defaults."""
	resolved = name or get_default_bank_account_name()
	if resolved and frappe.db.exists("IC Bank Account", resolved):
		d = frappe.get_cached_doc("IC Bank Account", resolved)
		return {
			"name": d.name,
			"account_title": d.account_title,
			"beneficiary_name": d.beneficiary_name or YES_BANK["beneficiary_name"],
			"bank_name": d.bank_name or "",
			"account_number": d.account_number or "",
			"ifsc_code": d.ifsc_code or "",
			"swift_code": d.swift_code or "",
			"upi_id": (d.upi_id or "").strip(),
			"branch_address": d.branch_address or "",
			"gstin": d.gstin or YES_BANK["gstin"],
		}

	# Legacy IC Settings flat fields
	try:
		s = frappe.get_cached_doc("IC Settings")
		return {
			"name": "",
			"account_title": s.bank_name or YES_BANK_TITLE,
			"beneficiary_name": s.beneficiary_name or YES_BANK["beneficiary_name"],
			"bank_name": s.bank_name or YES_BANK["bank_name"],
			"account_number": s.account_number or YES_BANK["account_number"],
			"ifsc_code": s.ifsc_code or YES_BANK["ifsc_code"],
			"swift_code": s.swift_code or YES_BANK["swift_code"],
			"upi_id": (s.upi_id or YES_BANK["upi_id"] or "").strip(),
			"branch_address": s.bank_branch_address or YES_BANK["branch_address"],
			"gstin": s.gstin or YES_BANK["gstin"],
		}
	except Exception:
		return {
			"name": "",
			"account_title": YES_BANK_TITLE,
			**{k: v for k, v in YES_BANK.items() if k not in ("is_default", "is_active", "account_title")},
		}


def bank_for_document(doc) -> dict[str, Any]:
	"""Resolve bank for a Quotation / Sales Invoice / template-like doc."""
	name = None
	if doc:
		name = doc.get("ic_bank_account") or doc.get("bank_account")
	return bank_as_dict(name)


@frappe.whitelist()
def get_bank_for_print(doctype: str | None = None, name: str | None = None, bank_account: str | None = None):
	"""Whitelisted helper for Jinja / client."""
	if bank_account:
		return bank_as_dict(bank_account)
	if doctype and name and frappe.db.exists(doctype, name):
		return bank_for_document(frappe.get_doc(doctype, name))
	return bank_as_dict(None)
