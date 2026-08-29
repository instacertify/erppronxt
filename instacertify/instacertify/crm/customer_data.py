# Copyright (c) Instacertify
"""Customer Data Drive — write-through for every customer-collected artifact."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime, strip_html


def resolve_customer(
	*,
	customer: str | None = None,
	lead: str | None = None,
	project: str | None = None,
	quotation: str | None = None,
) -> str | None:
	"""Best-effort resolve a Customer name from related links."""
	if customer and frappe.db.exists("Customer", customer):
		return customer
	if project and frappe.db.exists("Project", project):
		cust = frappe.db.get_value("Project", project, "customer")
		if cust:
			return cust
	if quotation and frappe.db.exists("Quotation", quotation):
		qt = frappe.db.get_value(
			"Quotation", quotation, ["quotation_to", "party_name"], as_dict=True
		) or {}
		if qt.get("quotation_to") == "Customer" and qt.get("party_name"):
			return qt.party_name
		if qt.get("quotation_to") == "Lead" and qt.get("party_name"):
			lead = qt.party_name
	if lead and frappe.db.has_column("Customer", "lead_name"):
		cust = frappe.db.get_value("Customer", {"lead_name": lead}, "name")
		if cust:
			return cust
	return None


def attach_file_to_customer_data(
	customer: str | None,
	file_url: str | None,
	*,
	source_doctype: str | None = None,
	source_name: str | None = None,
	label: str | None = None,
	category: str = "Documents",
) -> str | None:
	"""Copy/link an uploaded file onto Customer Data Drive. Returns File name or None."""
	if not customer or not file_url:
		return None
	if not frappe.db.exists("Customer", customer):
		return None
	url = str(file_url).strip()
	if not url or not (url.startswith("/") or url.startswith("http")):
		return None

	from instacertify.crm.events import _ensure_customer_drive_folder

	folder = _ensure_customer_drive_folder(customer)
	fname = (label or url.rstrip("/").split("/")[-1] or "upload").strip()[:140]
	# Skip if already attached to this customer with same URL
	existing = frappe.db.exists(
		"File",
		{
			"attached_to_doctype": "Customer",
			"attached_to_name": customer,
			"file_url": url,
			"is_folder": 0,
		},
	)
	if existing:
		return existing

	# Prefer copying by content hash if a File row already exists for this URL
	src = frappe.db.get_value(
		"File",
		{"file_url": url, "is_folder": 0},
		["name", "content_hash", "file_name", "is_private", "file_size"],
		as_dict=True,
	)
	if src and src.content_hash:
		dup = frappe.db.exists(
			"File",
			{
				"attached_to_doctype": "Customer",
				"attached_to_name": customer,
				"content_hash": src.content_hash,
				"is_folder": 0,
			},
		)
		if dup:
			return dup

	try:
		doc = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": fname,
				"file_url": url,
				"folder": folder,
				"is_private": int(src.is_private) if src else 1,
				"attached_to_doctype": "Customer",
				"attached_to_name": customer,
				"content_hash": src.content_hash if src else None,
				"file_size": src.file_size if src else None,
			}
		)
		# Keep a readable prefix so Data Drive shows source context
		if source_doctype and source_name and not (label or "").startswith(source_doctype):
			prefix = f"{category}-{source_name}-"
			if not doc.file_name.startswith(prefix):
				doc.file_name = (prefix + doc.file_name)[:140]
		doc.insert(ignore_permissions=True)
		return doc.name
	except Exception:
		frappe.log_error(frappe.get_traceback(), "attach_file_to_customer_data")
		return None


def save_collected_data_snapshot(
	customer: str | None,
	*,
	title: str,
	source_doctype: str,
	source_name: str,
	payload: dict[str, Any],
	category: str = "Collected Data",
) -> str | None:
	"""Persist structured customer-submitted fields as a text file on Customer Data Drive."""
	if not customer or not frappe.db.exists("Customer", customer):
		return None
	from instacertify.crm.events import _ensure_customer_drive_folder

	folder = _ensure_customer_drive_folder(customer)
	clean = {}
	for k, v in (payload or {}).items():
		if v in (None, "", [], {}):
			continue
		if isinstance(v, str):
			clean[k] = strip_html(v).strip()
		else:
			clean[k] = v
	if not clean:
		return None

	lines = [
		f"Customer Data — {title}",
		f"Source: {source_doctype} {source_name}",
		f"Collected on: {now_datetime()}",
		"",
	]
	for k, v in clean.items():
		if isinstance(v, (dict, list)):
			lines.append(f"{k}: {json.dumps(v, ensure_ascii=False, indent=2)}")
		else:
			lines.append(f"{k}: {v}")
	content = "\n".join(lines) + "\n"
	fname = f"{category}-{source_name}-{frappe.generate_hash()[:6]}.txt"[:140]

	try:
		# Avoid flooding identical snapshots: skip if latest same source has identical content hash
		file_doc = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": fname,
				"folder": folder,
				"is_private": 1,
				"attached_to_doctype": "Customer",
				"attached_to_name": customer,
				"content": content,
			}
		)
		file_doc.insert(ignore_permissions=True)
		return file_doc.name
	except Exception:
		frappe.log_error(frappe.get_traceback(), "save_collected_data_snapshot")
		return None


def mirror_profile_fields(customer: str | None, values: dict[str, Any]):
	"""Copy submitted company/GST/contact fields onto Customer when blank."""
	if not customer or not frappe.db.exists("Customer", customer):
		return
	meta = frappe.get_meta("Customer")
	updates = {}
	mapping = {
		"gstin": ["ic_gst_number", "gstin"],
		"company_legal_name": ["customer_name"],
		"company_address": ["ic_factory_address", "primary_address"],
		"data_contact_email": ["email_id"],
		"data_contact_phone": ["mobile_no"],
	}
	# Direct keys that already match Customer fields
	for key, val in (values or {}).items():
		if val in (None, ""):
			continue
		targets = mapping.get(key, [key] if meta.has_field(key) else [])
		for field in targets:
			if not meta.has_field(field):
				continue
			current = frappe.db.get_value("Customer", customer, field)
			if current in (None, ""):
				updates[field] = strip_html(str(val)).strip() if isinstance(val, str) else val
	if updates:
		try:
			frappe.db.set_value("Customer", customer, updates, update_modified=False)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "mirror_profile_fields")


def ingest_document_upload(doc, row):
	"""After portal checklist upload → Customer Data Drive."""
	customer = resolve_customer(customer=doc.get("customer"), project=doc.get("project"))
	attach_file_to_customer_data(
		customer,
		row.get("uploaded_file"),
		source_doctype="IC Document Request",
		source_name=doc.name,
		label=row.get("document_name") or "Document",
		category="Documents",
	)


def ingest_data_collection(doc):
	"""After Data Collection Sheet submit → snapshot + profile mirror."""
	customer = resolve_customer(customer=doc.get("customer"), project=doc.get("project"))
	payload = {
		"company_legal_name": doc.get("company_legal_name"),
		"gstin": doc.get("gstin"),
		"company_address": doc.get("company_address"),
		"data_contact_person": doc.get("data_contact_person"),
		"data_contact_phone": doc.get("data_contact_phone"),
		"data_contact_email": doc.get("data_contact_email"),
		"product_name": doc.get("product_name"),
		"product_model": doc.get("product_model"),
		"product_brand": doc.get("product_brand"),
		"data_collection_remarks": doc.get("data_collection_remarks"),
	}
	extra = []
	for row in doc.get("data_fields") or []:
		extra.append(
			{
				"label": row.get("field_label") or row.get("field_name") or row.name,
				"value": row.get("field_value"),
			}
		)
	if extra:
		payload["custom_fields"] = extra
	save_collected_data_snapshot(
		customer,
		title="Documents Data Collection",
		source_doctype="IC Document Request",
		source_name=doc.name,
		payload=payload,
		category="Collected Data",
	)
	mirror_profile_fields(customer, payload)


def ingest_sample_dispatch(doc):
	"""After sample dispatch / POD submit → files + snapshot."""
	customer = resolve_customer(customer=doc.get("customer"), project=doc.get("project"))
	if doc.get("pod_attachment"):
		attach_file_to_customer_data(
			customer,
			doc.get("pod_attachment"),
			source_doctype=doc.doctype,
			source_name=doc.name,
			label="POD",
			category="Samples",
		)
	payload = {
		"contact_person": doc.get("contact_person"),
		"contact_phone": doc.get("contact_phone"),
		"contact_email": doc.get("contact_email"),
		"dispatch_from_address": doc.get("dispatch_from_address"),
		"sample_description": doc.get("sample_description"),
		"sample_quantity": doc.get("sample_quantity"),
		"sample_condition": doc.get("sample_condition"),
		"packaging_details": doc.get("packaging_details"),
		"courier_name": doc.get("courier_name"),
		"tracking_number": doc.get("tracking_number"),
		"dispatch_date": str(doc.get("dispatch_date") or ""),
		"expected_delivery": str(doc.get("expected_delivery") or ""),
		"customer_remarks": doc.get("customer_remarks") or doc.get("sample_dispatch_remarks"),
	}
	save_collected_data_snapshot(
		customer,
		title="Sample Dispatch Collection",
		source_doctype=doc.doctype,
		source_name=doc.name,
		payload=payload,
		category="Collected Data",
	)


def ingest_sample_report(doc):
	"""After sample / testing report upload → Customer Data Drive + Project Record with timestamp."""
	customer = resolve_customer(customer=doc.get("customer"), project=doc.get("project"))
	file_url = doc.get("test_report")
	if not file_url:
		return

	stamp = doc.get("report_uploaded_on") or now_datetime()
	stamp_str = str(stamp)
	tracking = doc.get("tracking_number") or doc.get("title") or doc.name
	label = f"Test Report {tracking} ({stamp_str[:16]})"

	attach_file_to_customer_data(
		customer,
		file_url,
		source_doctype=doc.doctype,
		source_name=doc.name,
		label=label,
		category="Test Reports",
	)

	# Project / customer record with explicit date-time in the body
	if frappe.db.exists("DocType", "IC Project Record") and customer:
		subject = f"Test Report — {tracking}"
		existing = frappe.db.exists(
			"IC Project Record",
			{
				"subject": subject,
				"attachment": file_url,
				"customer": customer,
			},
		)
		if not existing:
			try:
				frappe.get_doc(
					{
						"doctype": "IC Project Record",
						"subject": subject,
						"record_type": "Deliverable",
						"customer": customer,
						"project": doc.get("project"),
						"category": "Test Reports",
						"content": (
							f"<p>Test report uploaded from <b>{frappe.utils.escape_html(doc.doctype)}</b> "
							f"<b>{frappe.utils.escape_html(doc.name)}</b>.</p>"
							f"<p>Uploaded on: <b>{frappe.utils.escape_html(stamp_str)}</b></p>"
							f"<p>Uploaded by: {frappe.utils.escape_html(doc.get('report_uploaded_by') or frappe.session.user)}</p>"
							f"<p>{frappe.utils.escape_html(doc.get('sample_description') or doc.get('test_name') or '')}</p>"
						),
						"attachment": file_url,
						"recorded_by": doc.get("report_uploaded_by") or frappe.session.user,
					}
				).insert(ignore_permissions=True)
			except Exception:
				frappe.log_error(frappe.get_traceback(), "ingest_sample_report project record")

	save_collected_data_snapshot(
		customer,
		title=f"Test Report — {tracking}",
		source_doctype=doc.doctype,
		source_name=doc.name,
		payload={
			"tracking_number": doc.get("tracking_number"),
			"sample_description": doc.get("sample_description") or doc.get("test_name"),
			"report_uploaded_on": stamp_str,
			"report_uploaded_by": doc.get("report_uploaded_by") or frappe.session.user,
			"test_report": file_url,
			"status": doc.get("status"),
		},
		category="Test Reports",
	)


def ingest_contract_acceptance(doc):
	"""After guest contract accept → signature snapshot on Customer Data."""
	customer = resolve_customer(
		customer=doc.get("customer"),
		lead=doc.get("lead"),
		quotation=doc.get("quotation"),
	)
	payload = {
		"customer_signed_name": doc.get("customer_signed_name"),
		"accepted_on": str(doc.get("accepted_on") or ""),
		"customer_remarks": doc.get("customer_remarks"),
		"title": doc.get("title"),
		"status": doc.get("status"),
		"commercial_value": doc.get("commercial_value"),
	}
	save_collected_data_snapshot(
		customer,
		title="Contract Acceptance",
		source_doctype="IC Contract",
		source_name=doc.name,
		payload=payload,
		category="Collected Data",
	)
