# Copyright (c) Instacertify
"""Soften india_compliance Quotation validations — Customer only is mandatory."""

from __future__ import annotations

import frappe

_PATCHED = False


def patch_india_compliance_quotation_validate():
	"""Monkey-patch india_compliance validate_transaction for soft Quotation drafts.

	GST / company address / phone / email must not block creating a service quote.
	Only Customer is enforced by Instacertify.
	"""
	global _PATCHED
	if _PATCHED:
		return
	try:
		import india_compliance.gst_india.overrides.transaction as txn
	except Exception:
		return

	if getattr(txn.validate_transaction, "_ic_soft_quote", False):
		_PATCHED = True
		return

	_orig = txn.validate_transaction

	def _soft_validate_transaction(doc, method=None):
		if getattr(doc, "doctype", None) == "Quotation":
			from instacertify.accounting.billing import _ensure_company_address_on_transaction

			try:
				_ensure_company_address_on_transaction(doc)
			except Exception:
				pass
			doc.flags.ignore_mandatory = True
			if doc.meta.has_field("gst_category") and not doc.get("gst_category"):
				doc.gst_category = "Unregistered"
			try:
				return _orig(doc, method=method)
			except frappe.MandatoryError:
				frappe.clear_last_message()
				return False
			except Exception:
				# Draft quotes: never block on GST/HSN/account checks
				if int(getattr(doc, "docstatus", 0) or 0) == 0:
					frappe.log_error(frappe.get_traceback(), "Quotation GST soft-validate")
					frappe.clear_last_message()
					return False
				raise
		return _orig(doc, method=method)

	_soft_validate_transaction._ic_soft_quote = True
	txn.validate_transaction = _soft_validate_transaction
	_PATCHED = True


def validate_quotation_gst(doc, method=None):
	"""Optional hook entry — prefer patch_india_compliance_quotation_validate via boot."""
	patch_india_compliance_quotation_validate()
	from india_compliance.gst_india.overrides.transaction import validate_transaction

	return validate_transaction(doc, method=method)
