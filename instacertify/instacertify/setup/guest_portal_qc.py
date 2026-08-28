# Copyright (c) Instacertify
"""Guest portal lockdown QC — consent/feedback + document uploads."""

from __future__ import annotations

import io

import frappe
from frappe.utils import get_url


@frappe.whitelist()
def run_guest_portal_qc() -> dict:
	report = {"ok": [], "warn": [], "fail": [], "urls": {}}

	def ok(m):
		report["ok"].append(m)

	def fail(m):
		report["fail"].append(m)

	def warn(m):
		report["warn"].append(m)

	# Pick a quotation and share it
	qtn = frappe.db.get_value("Quotation", {}, "name", order_by="modified desc")
	if not qtn:
		fail("No Quotation for portal QC")
		return report

	from instacertify.quotation.events import (
		share_with_customer,
		customer_accept_quotation,
		customer_reject_quotation,
		customer_request_changes,
		open_quotation_for_revision,
		download_quotation_pdf,
	)
	from instacertify.www.ic_quotation import get_quotation
	from instacertify.utils.pdf import download_pdf as desk_download_pdf

	share = share_with_customer(qtn)
	token = share.get("token")
	report["urls"]["quotation_portal"] = share.get("url")
	ok(f"Shared quotation {qtn}")

	# Guest payload has no desk name key
	frappe.set_user("Guest")
	try:
		payload = get_quotation(token)
		if "name" in payload and payload.get("name", "").startswith(("SAL-", "QTN-", "CRM-")):
			fail("Guest quotation payload still exposes desk name")
		else:
			ok("Guest quotation payload hides desk name")
		if not payload.get("pdf_url") or "download_quotation_pdf" not in payload["pdf_url"]:
			fail("Guest PDF URL missing token endpoint")
		else:
			ok("Guest PDF uses token endpoint")
		if "/app" in str(payload) or "/desk" in str(payload):
			fail("Guest payload contains desk path")
		else:
			ok("Guest payload has no /app or /desk paths")

		# Desk download blocked for Guest
		try:
			desk_download_pdf("Quotation", qtn)
			fail("Guest was able to call desk download_pdf")
		except Exception:
			ok("Guest blocked from desk download_pdf")

		# Draft decision blocked: temporarily force status
		frappe.set_user("Administrator")
		frappe.db.set_value("Quotation", qtn, "ic_workflow_status", "Draft", update_modified=False)
		frappe.set_user("Guest")
		try:
			customer_accept_quotation(token, remarks="should fail")
			fail("Guest accepted Draft quotation")
		except Exception:
			ok("Guest cannot decide on Draft quotation")

		# Restore shared status and accept
		frappe.set_user("Administrator")
		frappe.db.set_value(
			"Quotation", qtn, "ic_workflow_status", "Shared with Customer", update_modified=False
		)
		frappe.set_user("Guest")
		# Reject requires remarks
		try:
			customer_reject_quotation(token, remarks="")
			fail("Guest reject without remarks allowed")
		except Exception:
			ok("Guest reject requires remarks")

		# Feedback / revision remarks required
		try:
			customer_request_changes(token, remarks="  ")
			fail("Empty revision remarks allowed")
		except Exception:
			ok("Revision remarks required")

		# Accept OK
		res = customer_accept_quotation(token, remarks="Looks good — QC accept")
		if res.get("status") == "Accepted" and "invoice" not in res and "project" not in res:
			ok("Guest accept returns status only (no invoice/project)")
		else:
			fail(f"Guest accept leak/status issue: {res}")

		# Token PDF still works after accept (download allowed)
		frappe.set_user("Administrator")
		from instacertify.utils.pdf import get_quotation_pdf_bytes

		pdf = get_quotation_pdf_bytes(qtn)
		if pdf and pdf[:4] == b"%PDF":
			ok(f"Shareable PDF printable bytes={len(pdf)}")
		else:
			fail("Shareable PDF invalid")

		# Revision invalidates token
		open_quotation_for_revision(qtn)
		token_after = frappe.db.get_value("Quotation", qtn, "ic_share_token") or ""
		if not token_after:
			ok("Share token cleared on revision")
		else:
			fail("Share token still set after revision")
		frappe.set_user("Guest")
		try:
			get_quotation(token)
			fail("Old token still works after revision")
		except Exception:
			ok("Old portal token invalid after revision")
	except Exception as e:
		fail(f"Guest quotation QC: {e}")
	finally:
		frappe.set_user("Administrator")

	# Document portal allowed types + local file binding
	try:
		from instacertify.documents.api import (
			_assert_allowed_upload,
			ALLOWED_UPLOAD_EXTENSIONS,
			share_document_request,
			get_document_request_by_token,
			upload_document_item,
		)

		needed = {".pdf", ".png", ".jpg", ".jpeg", ".xlsx", ".csv", ".webp", ".gif"}
		if needed.issubset(ALLOWED_UPLOAD_EXTENSIONS):
			ok(f"Document allowed types include PDF/image/Excel/CSV ({len(ALLOWED_UPLOAD_EXTENSIONS)} exts)")
		else:
			fail(f"Missing upload types: {needed - ALLOWED_UPLOAD_EXTENSIONS}")

		# Reject external URL
		try:
			_assert_allowed_upload("https://evil.example/malware.pdf")
			fail("External PDF URL accepted")
		except Exception:
			ok("External upload URL rejected")

		dr = frappe.db.get_value("IC Document Request", {}, "name", order_by="modified desc")
		if not dr:
			# create minimal
			cust = frappe.db.get_value("Customer", {}, "name")
			doc = frappe.get_doc(
				{
					"doctype": "IC Document Request",
					"title": "Portal QC Docs",
					"customer": cust,
					"status": "Draft",
					"items": [
						{"document_name": "GST Certificate", "category": "Customer Documents", "is_mandatory": 1, "status": "Pending"}
					],
				}
			)
			doc.insert(ignore_permissions=True)
			dr = doc.name
		share = share_document_request(dr)
		report["urls"]["documents_portal"] = share.get("url")
		tok = share.get("token")
		frappe.set_user("Guest")
		payload = get_document_request_by_token(tok)
		if "customer" in payload or "project" in payload:
			fail("Document guest payload exposes customer/project")
		else:
			ok("Document guest payload hides customer/project")
		if not payload.get("items"):
			warn("Document request has no checklist items")
		else:
			ok(f"Document checklist items={len(payload['items'])}")

		# Create a local public csv file and attach
		frappe.set_user("Administrator")
		content = "col1,col2\na,b\n"
		f = frappe.get_doc(
			{"doctype": "File", "file_name": "portal_qc_scope.csv", "content": content, "is_private": 0}
		).insert(ignore_permissions=True)
		item = payload["items"][0]["name"]
		frappe.set_user("Guest")
		upload_document_item(tok, item, f.file_url, remarks="CSV uploaded via portal QC")
		ok("Guest CSV upload accepted")

		# Reject .exe disguised
		try:
			_assert_allowed_upload("/files/bad.exe")
			fail(".exe upload allowed")
		except Exception:
			ok(".exe upload rejected")
	except Exception as e:
		fail(f"Document portal QC: {e}")
	finally:
		frappe.set_user("Administrator")

	# Verify page lockdown
	try:
		from instacertify.www.ic_verify import ALLOWED_VERIFY_DOCTYPES

		if "IC Joining Letter" in ALLOWED_VERIFY_DOCTYPES or "Project" in ALLOWED_VERIFY_DOCTYPES:
			fail("Verify allowlist still includes Joining Letter / Project")
		else:
			ok("Verify allowlist excludes Joining Letter / Project")
	except Exception as e:
		fail(f"Verify allowlist: {e}")

	report["summary"] = {
		"ok": len(report["ok"]),
		"warn": len(report["warn"]),
		"fail": len(report["fail"]),
		"passed": len(report["fail"]) == 0,
	}
	return report
