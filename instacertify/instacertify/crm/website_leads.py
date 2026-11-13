# Copyright (c) Instacertify
"""Pull read-only enquiries from the Instacertify website CMS into Lead."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, flt, get_datetime

DEFAULT_URL = "https://cms.instacertify.com/api/v1/integrations/leads"
MAX_PAGES = 30

_STATUS = {
	"new": "Lead",
	"open": "Open",
	"contacted": "Replied",
	"in_progress": "Open",
	"qualified": "Opportunity",
	"won": "Converted",
	"converted": "Converted",
	"lost": "Do Not Contact",
	"spam": "Do Not Contact",
}
_LOCKED = {"Converted", "Do Not Contact"}


def _service_bits(row: dict) -> tuple[str, str]:
	service = row.get("service")
	if isinstance(service, dict):
		return (service.get("title") or "").strip(), (service.get("path") or "").strip()
	return (str(service or "")).strip(), ""


def request_category(row: dict) -> str:
	title, path = _service_bits(row)
	blob = " ".join([str(row.get("type") or ""), title, path]).lower()
	if "test" in blob:
		return "Testing Request"
	if any(word in blob for word in ("cert", "bis", "registration", "epr", "msds")):
		return "Certification Request"
	return "Service Request"


def lead_status(website_status: str | None) -> str:
	return _STATUS.get((website_status or "").strip().lower(), "Lead")


def enquiry_text(row: dict) -> str:
	title, path = _service_bits(row)
	utm = row.get("utm") if isinstance(row.get("utm"), dict) else {}
	lines = [
		f"Website enquiry ({row.get('type') or 'lead'}, {row.get('status') or 'new'})",
	]
	if title:
		lines.append(f"Service: {title}")
	if path:
		lines.append(f"Service path: {path}")
	if row.get("product"):
		lines.append(f"Product: {row.get('product')}")
	if row.get("requirement"):
		lines.append(f"Requirement: {row.get('requirement')}")
	if row.get("message"):
		lines.append(f"Message: {row.get('message')}")
	if row.get("timeline"):
		lines.append(f"Timeline: {row.get('timeline')}")
	if row.get("source_page"):
		lines.append(f"Page: {row.get('source_page')}")
	if row.get("referrer"):
		lines.append(f"Referrer: {row.get('referrer')}")
	utm_bits = [utm.get(key) for key in ("source", "medium", "campaign", "term") if utm.get(key)]
	if utm_bits:
		lines.append("UTM: " + " / ".join(utm_bits))
	return "\n".join(lines)


def _api_key() -> str:
	key = ""
	try:
		if frappe.get_meta("IC Settings").has_field("website_lead_api_key"):
			key = frappe.utils.password.get_decrypted_password(
				"IC Settings", "IC Settings", "website_lead_api_key", raise_exception=False
			)
	except Exception:
		key = ""
	if not key:
		key = frappe.conf.get("ic_website_lead_api_key") or ""
	return str(key).strip()


def _api_url() -> str:
	url = ""
	try:
		if frappe.get_meta("IC Settings").has_field("website_lead_api_url"):
			url = frappe.db.get_single_value("IC Settings", "website_lead_api_url") or ""
	except Exception:
		url = ""
	return (url or DEFAULT_URL).strip().rstrip("/")


def _sync_enabled() -> bool:
	try:
		if frappe.get_meta("IC Settings").has_field("website_lead_sync_enabled"):
			return cint(frappe.db.get_single_value("IC Settings", "website_lead_sync_enabled")) != 0
	except Exception:
		return True
	return True


def _fetch_page(key: str, page: int, updated_after: str | None) -> dict:
	import requests

	params = {"per_page": 100, "page": page}
	if updated_after:
		params["updated_after"] = updated_after
	response = requests.get(
		_api_url(),
		headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
		params=params,
		timeout=45,
	)
	if response.status_code in (401, 403):
		frappe.throw(_("Website lead API rejected the key. Check the key on IC Settings."))
	response.raise_for_status()
	payload = response.json()
	if not isinstance(payload, dict):
		frappe.throw(_("Website lead API returned an unexpected response."))
	return payload


def _party_name(row: dict) -> str:
	name = (row.get("name") or "").strip()
	company = (row.get("company") or "").strip() if isinstance(row.get("company"), str) else ""
	return company or name or (row.get("email") or "Website enquiry")


def _apply_row(doc, row: dict, *, creating: bool) -> bool:
	"""Fill a Lead from a website row. Returns True when something changed."""
	changed = creating
	party = _party_name(row)[:140]
	if creating or not (doc.get("ic_party_name") or "").strip():
		doc.ic_party_name = party
		changed = True
	if creating or not doc.company_name:
		doc.company_name = ((row.get("company") or party) if isinstance(row.get("company"), str) else party)[:140]
		changed = True
	if creating or not (doc.first_name or doc.last_name):
		person = (row.get("name") or party).strip()
		doc.first_name = (person.split()[0] if person else party)[:140]
		changed = True
	if row.get("email") and (creating or not doc.email_id):
		doc.email_id = str(row.get("email")).strip()[:140]
		changed = True
	if row.get("phone") and (creating or not doc.mobile_no):
		doc.mobile_no = str(row.get("phone")).strip()[:20]
		changed = True
	country = row.get("country")
	if isinstance(country, str) and country and frappe.db.exists("Country", country) and (creating or not doc.country):
		doc.country = country
		changed = True

	text = enquiry_text(row)
	if creating or not (doc.get("ic_remarks") or "").strip():
		doc.ic_remarks = text
		changed = True
	if creating or not (doc.notes or "").strip():
		doc.notes = text
		changed = True

	category = request_category(row)
	if creating or not doc.get("ic_request_category"):
		doc.ic_request_category = category
		changed = True
	if row.get("timeline") and (creating or not doc.get("ic_expected_timeline")):
		doc.ic_expected_timeline = str(row.get("timeline"))[:140]
		changed = True
	if row.get("value") not in (None, "") and (creating or not doc.get("ic_estimated_value")):
		doc.ic_estimated_value = flt(row.get("value"))
		changed = True
	follow = row.get("follow_up_at")
	if follow and (creating or not doc.get("ic_next_contact_date")):
		try:
			doc.ic_next_contact_date = get_datetime(follow).date()
			changed = True
		except Exception:
			pass

	if frappe.db.exists("Lead Source", "Website") and (creating or not doc.source):
		doc.source = "Website"
		changed = True
	if frappe.db.exists("IC Lead Source", "Website") and (creating or not doc.get("ic_lead_source_detail")):
		doc.ic_lead_source_detail = "Website"
		changed = True

	status = lead_status(row.get("status"))
	if creating:
		doc.status = status
	elif doc.status not in _LOCKED and doc.status != status:
		doc.status = status
		changed = True

	doc.ic_website_lead_id = str(row.get("id") or "")[:140]
	return changed


def _upsert(row: dict) -> str:
	website_id = str(row.get("id") or "").strip()
	if not website_id:
		return "skipped"
	if row.get("anonymised"):
		return "skipped"
	existing = None
	if frappe.get_meta("Lead").has_field("ic_website_lead_id"):
		existing = frappe.db.get_value("Lead", {"ic_website_lead_id": website_id}, "name")
	if existing:
		doc = frappe.get_doc("Lead", existing)
		if _apply_row(doc, row, creating=False):
			doc.flags.ignore_permissions = True
			doc.save(ignore_permissions=True)
			return "updated"
		return "unchanged"
	doc = frappe.new_doc("Lead")
	_apply_row(doc, row, creating=True)
	doc.flags.ignore_permissions = True
	doc.flags.ignore_mandatory = False
	doc.insert(ignore_permissions=True)
	return "created"


@frappe.whitelist()
def sync_website_leads(full: int | str = 0):
	"""Import website enquiries. Incremental after the first successful sync unless full=1."""
	if frappe.session.user not in ("Administrator", "Guest") and not frappe.has_permission("Lead", "create"):
		frappe.throw(_("Not permitted to import leads."), frappe.PermissionError)
	if not _sync_enabled() and not cint(full):
		return {"ok": True, "skipped": 1, "reason": "sync disabled"}
	key = _api_key()
	if not key:
		return {
			"ok": False,
			"error": "Website lead API key is not set. Open IC Settings and paste the key.",
		}
	if not frappe.get_meta("Lead").has_field("ic_website_lead_id"):
		return {"ok": False, "error": "Run Migrate so the Website Lead ID field exists, then sync again."}

	updated_after = None
	if not cint(full):
		try:
			updated_after = frappe.db.get_single_value("IC Settings", "website_lead_last_sync")
		except Exception:
			updated_after = None
		if updated_after:
			updated_after = str(updated_after)[:10]

	created = updated = unchanged = skipped = 0
	pages = 0
	page = 1
	last_page = 1
	while page <= last_page and pages < MAX_PAGES:
		payload = _fetch_page(key, page, updated_after)
		rows = payload.get("data") or []
		meta = payload.get("meta") or {}
		last_page = cint(meta.get("last_page")) or 1
		for row in rows:
			if not isinstance(row, dict):
				skipped += 1
				continue
			result = _upsert(row)
			if result == "created":
				created += 1
			elif result == "updated":
				updated += 1
			elif result == "unchanged":
				unchanged += 1
			else:
				skipped += 1
		pages += 1
		page += 1

	now = frappe.utils.now_datetime()
	if frappe.get_meta("IC Settings").has_field("website_lead_last_sync"):
		frappe.db.set_single_value("IC Settings", "website_lead_last_sync", now, update_modified=False)
	frappe.db.commit()
	return {
		"ok": True,
		"created": created,
		"updated": updated,
		"unchanged": unchanged,
		"skipped": skipped,
		"pages": pages,
	}


def sync_website_leads_scheduled():
	"""Scheduler entry. Skips quietly when the key is not configured yet."""
	if not _api_key() or not _sync_enabled():
		return
	try:
		sync_website_leads()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Website lead sync")
