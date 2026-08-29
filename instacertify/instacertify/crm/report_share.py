# Copyright (c) Instacertify
"""Share test reports with customers via link + 8-digit access code."""

from __future__ import annotations

import secrets

import frappe
from frappe import _
from frappe.utils import cint, now_datetime, strip_html


REPORT_CATEGORIES = {
	"Testing",
	"Samples",
	"Records",
	"Test Reports",
}


def _new_access_code() -> str:
	"""Eight-digit numerical code (10000000–99999999)."""
	return f"{secrets.randbelow(90000000) + 10000000:08d}"


def _new_share_token() -> str:
	return secrets.token_urlsafe(24)


def _is_report_file(file_row: dict | None = None, *, file_url: str | None = None, file_name: str | None = None, category: str | None = None) -> bool:
	row = file_row or {}
	url = (file_url or row.get("file_url") or "").lower()
	name = (file_name or row.get("file_name") or row.get("label") or "").lower()
	cat = category or row.get("category") or ""
	if cat in REPORT_CATEGORIES:
		return True
	if "report" in name or "report" in url:
		return True
	if url.endswith(".pdf") and cat in {"Testing", "Samples", "Records", "Uploaded", "Documents"}:
		# PDFs on testing/samples/records are typically reports
		if cat in {"Testing", "Samples", "Records"}:
			return True
	return False


def _share_url(token: str) -> str:
	return frappe.utils.get_url(f"/ic-report/{token}")


def _find_active_share(*, customer: str, file_url: str) -> str | None:
	return frappe.db.get_value(
		"IC Report Share",
		{"customer": customer, "file_url": file_url, "status": "Active"},
		"name",
	)


def _upsert_share(
	*,
	customer: str,
	file_url: str,
	file_name: str | None = None,
	source_doctype: str | None = None,
	source_name: str | None = None,
	title: str | None = None,
	rotate_code: bool = False,
	force_token: str | None = None,
	force_access_code: str | None = None,
):
	if not file_url:
		frappe.throw(_("Report file is required"))

	existing = _find_active_share(customer=customer, file_url=file_url)
	fname = (file_name or file_url.rstrip("/").split("/")[-1] or "report.pdf").strip()[:140]
	share_title = strip_html(title or fname)[:140]
	actor = frappe.session.user if frappe.session.user not in (None, "Guest") else "Administrator"

	if existing and not rotate_code and not force_token:
		doc = frappe.get_doc("IC Report Share", existing)
	elif existing:
		doc = frappe.get_doc("IC Report Share", existing)
		doc.access_code = force_access_code or _new_access_code()
		doc.share_token = force_token or _new_share_token()
		doc.shared_on = now_datetime()
		doc.shared_by = actor
		doc.title = share_title
		doc.file_name = fname
		doc.source_doctype = source_doctype or doc.source_doctype
		doc.source_name = source_name or doc.source_name
		doc.share_url = _share_url(doc.share_token)
		doc.save(ignore_permissions=True)
	else:
		token = force_token or _new_share_token()
		doc = frappe.get_doc(
			{
				"doctype": "IC Report Share",
				"title": share_title,
				"customer": customer,
				"file_url": file_url,
				"file_name": fname,
				"source_doctype": source_doctype,
				"source_name": source_name,
				"share_token": token,
				"access_code": force_access_code or _new_access_code(),
				"share_url": _share_url(token),
				"shared_on": now_datetime(),
				"shared_by": actor,
				"status": "Active",
			}
		)
		doc.insert(ignore_permissions=True)

	if doc.source_doctype == "IC Testing Request" and doc.source_name:
		_sync_testing_request_share(doc)

	return doc


@frappe.whitelist()
def create_customer_report_share(
	customer: str,
	file_url: str,
	file_name: str | None = None,
	source_doctype: str | None = None,
	source_name: str | None = None,
	title: str | None = None,
	rotate_code: int | bool = 0,
):
	"""Create or refresh a share link + 8-digit code for a customer report file."""
	from instacertify.crm.customer_permissions import assert_can_read_customer_data

	assert_can_read_customer_data(customer)
	doc = _upsert_share(
		customer=customer,
		file_url=file_url,
		file_name=file_name,
		source_doctype=source_doctype,
		source_name=source_name,
		title=title,
		rotate_code=bool(cint(rotate_code)),
	)
	return _share_payload(doc)


@frappe.whitelist()
def get_customer_report_share(customer: str, file_url: str):
	from instacertify.crm.customer_permissions import assert_can_read_customer_data

	assert_can_read_customer_data(customer)
	name = _find_active_share(customer=customer, file_url=file_url)
	if not name:
		return None
	return _share_payload(frappe.get_doc("IC Report Share", name))


@frappe.whitelist()
def revoke_customer_report_share(customer: str, file_url: str | None = None, share_name: str | None = None):
	from instacertify.crm.customer_permissions import assert_can_read_customer_data

	assert_can_read_customer_data(customer)
	name = share_name or (
		_find_active_share(customer=customer, file_url=file_url) if file_url else None
	)
	if not name:
		frappe.throw(_("No active share found"))
	doc = frappe.get_doc("IC Report Share", name)
	if doc.customer != customer:
		frappe.throw(_("Not allowed"), frappe.PermissionError)
	doc.status = "Revoked"
	doc.save(ignore_permissions=True)
	return {"ok": True}


def enrich_drive_files_with_shares(customer: str, files: list[dict]) -> list[dict]:
	"""Attach share_url / access_code / shareable flags onto drive file rows."""
	if not files:
		return files
	active = frappe.get_all(
		"IC Report Share",
		filters={"customer": customer, "status": "Active"},
		fields=["name", "file_url", "share_token", "access_code", "share_url", "title"],
	)
	by_url = {r.file_url: r for r in active if r.file_url}
	for f in files:
		url = f.get("file_url")
		shareable = _is_report_file(f)
		f["shareable"] = bool(shareable)
		share = by_url.get(url) if url else None
		if share:
			f["share_name"] = share.name
			f["share_token"] = share.share_token
			f["access_code"] = share.access_code
			f["share_url"] = share.share_url or _share_url(share.share_token)
		else:
			f["share_name"] = None
			f["share_token"] = None
			f["access_code"] = None
			f["share_url"] = None
	return files


def _share_payload(doc) -> dict:
	url = doc.share_url or _share_url(doc.share_token)
	return {
		"name": doc.name,
		"title": doc.title,
		"customer": doc.customer,
		"file_url": doc.file_url,
		"file_name": doc.file_name,
		"share_token": doc.share_token,
		"access_code": doc.access_code,
		"share_url": url,
		"shared_on": str(doc.shared_on or ""),
		"status": doc.status,
		"source_doctype": doc.source_doctype,
		"source_name": doc.source_name,
	}


def _sync_testing_request_share(share_doc):
	try:
		tr = frappe.get_doc("IC Testing Request", share_doc.source_name)
		tr.share_token = share_doc.share_token
		if frappe.get_meta("IC Testing Request").has_field("share_access_code"):
			tr.share_access_code = share_doc.access_code
		tr.report_shared_on = share_doc.shared_on or now_datetime()
		if tr.test_report and tr.status in (
			"Report Available",
			"Report Uploaded",
			"Report Shared with Customer",
		):
			tr.status = "Report Shared with Customer"
		tr.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "sync testing request report share")


def share_from_testing_request(testing_request: str) -> dict:
	"""Used by Testing Request Actions → Share with Customer."""
	doc = frappe.get_doc("IC Testing Request", testing_request)
	if not doc.test_report:
		frappe.throw(_("Please upload the test report first"))
	if not doc.customer:
		frappe.throw(_("Customer is required to share the report"))
	share = _upsert_share(
		customer=doc.customer,
		file_url=doc.test_report,
		file_name=(doc.test_report or "").rstrip("/").split("/")[-1],
		source_doctype="IC Testing Request",
		source_name=doc.name,
		title=doc.title or doc.test_name or doc.name,
		rotate_code=False,
	)
	return _share_payload(share)


@frappe.whitelist(allow_guest=True)
def get_report_gate(token: str):
	"""Public: metadata only — never returns the file until code is verified."""
	doc = _get_active_share_by_token(token)
	return {
		"title": strip_html(doc.title or "") or _("Test Report"),
		"file_name": strip_html(doc.file_name or ""),
		"customer": doc.customer,
		"requires_code": True,
		"portal_notice": _(
			"Enter the 8-digit access code shared with you to view or download this report."
		),
	}


@frappe.whitelist(allow_guest=True)
def unlock_report(token: str, access_code: str):
	"""Public: verify 8-digit code and return view/download URL."""
	doc = _get_active_share_by_token(token)
	code = "".join(ch for ch in str(access_code or "") if ch.isdigit())
	if len(code) != 8 or code != str(doc.access_code or ""):
		frappe.throw(_("Invalid access code. Enter the 8-digit code shown next to the share link."), frappe.AuthenticationError)
	return {
		"title": strip_html(doc.title or "") or _("Test Report"),
		"file_name": strip_html(doc.file_name or ""),
		"file_url": doc.file_url,
		"shared_on": str(doc.shared_on or ""),
		"portal_notice": _("You can view or download this report. This link does not provide access to Instacertify ERP."),
	}


def _get_active_share_by_token(token: str):
	if not token:
		frappe.throw(_("Invalid report link"), frappe.PermissionError)
	# Prefer IC Report Share; fall back to Testing Request share_token for older links
	name = frappe.db.get_value("IC Report Share", {"share_token": token, "status": "Active"}, "name")
	if name:
		return frappe.get_doc("IC Report Share", name, ignore_permissions=True)

	tr_name = frappe.db.get_value("IC Testing Request", {"share_token": token}, "name")
	if not tr_name:
		frappe.throw(_("Invalid report link"), frappe.PermissionError)
	tr = frappe.get_doc("IC Testing Request", tr_name)
	if (tr.status or "") != "Report Shared with Customer":
		frappe.throw(_("This report is not shared with the customer yet"), frappe.PermissionError)
	if not (tr.customer and tr.test_report):
		frappe.throw(_("This report cannot be opened"), frappe.PermissionError)

	existing_code = None
	if frappe.get_meta("IC Testing Request").has_field("share_access_code"):
		existing_code = tr.get("share_access_code")
	share = _upsert_share(
		customer=tr.customer,
		file_url=tr.test_report,
		file_name=(tr.test_report or "").rstrip("/").split("/")[-1],
		source_doctype="IC Testing Request",
		source_name=tr.name,
		title=tr.title or tr.test_name or tr.name,
		force_token=token,
		force_access_code=existing_code if existing_code and len(str(existing_code)) == 8 else None,
	)
	return share
