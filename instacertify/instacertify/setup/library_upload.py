# Copyright (c) Instacertify
"""Upload helpers for Quote Format Library and Laboratory Scope Library."""

from __future__ import annotations

import csv
import io
from pathlib import Path

import frappe
from frappe import _
from frappe.utils.file_manager import get_file

from instacertify.utils.files import assert_internal_file


def _guess_file_type(filename: str | None) -> str:
	name = (filename or "").lower()
	if name.endswith(".pdf"):
		return "PDF"
	if name.endswith((".doc", ".docx")):
		return "DOCX"
	if name.endswith((".htm", ".html")):
		return "HTML"
	if name.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
		return "Image"
	if name.endswith((".xls", ".xlsx", ".csv")):
		return "Excel/CSV"
	return "Other"


@frappe.whitelist()
def create_quote_format_from_upload(
	template_name: str,
	quotation_type: str,
	file_url: str | None = None,
	service_family: str | None = None,
	template_notes: str | None = None,
	is_active: int = 1,
):
	"""Create (or update) an IC Quotation Template and attach an uploaded quote format."""
	template_name = (template_name or "").strip()
	quotation_type = (quotation_type or "").strip() or "Consulting"
	if not template_name:
		frappe.throw(_("Template Name is required"))
	if quotation_type not in (
		"Consulting",
		"Testing",
		"Renewal",
		"Other",
		"Multiple Products / Multiple Services",
		"Service",
	):
		frappe.throw(_("Invalid quotation type: {0}").format(quotation_type))

	exists = frappe.db.exists("IC Quotation Template", template_name)
	if exists:
		doc = frappe.get_doc("IC Quotation Template", template_name)
	else:
		doc = frappe.new_doc("IC Quotation Template")
		doc.template_name = template_name

	doc.quotation_type = quotation_type
	if service_family:
		doc.service_family = service_family
	if template_notes:
		doc.template_notes = template_notes
	doc.is_active = 1 if int(is_active or 1) else 0

	if file_url:
		file_url = assert_internal_file(file_url, "Quote format file")
		doc.uploaded_format = file_url
		label = Path(str(file_url).split("/")[-1] or "Quote Format").name
		# Avoid duplicate rows for same file
		already = any((r.attach_file or "") == file_url for r in (doc.format_library or []))
		if not already:
			doc.append(
				"format_library",
				{
					"file_label": label,
					"attach_file": file_url,
					"file_type": _guess_file_type(label),
					"remarks": "Uploaded via Quote Format Library",
				},
			)

	doc.save(ignore_permissions=False)
	frappe.db.commit()
	return {"template": doc.name, "uploaded_format": doc.uploaded_format}


@frappe.whitelist()
def create_laboratory_from_upload(
	laboratory_name: str,
	location: str | None = None,
	accreditation_scope: str | None = None,
	scope_file: str | None = None,
	contact_person: str | None = None,
	email: str | None = None,
	phone: str | None = None,
	status: str = "Active",
):
	"""Create a laboratory with name + scope text/file for the Lab Library."""
	laboratory_name = (laboratory_name or "").strip()
	if not laboratory_name:
		frappe.throw(_("Laboratory Name is required"))

	existing = frappe.db.get_value("IC Laboratory", {"laboratory_name": laboratory_name}, "name")
	if existing:
		doc = frappe.get_doc("IC Laboratory", existing)
	else:
		doc = frappe.new_doc("IC Laboratory")
		doc.laboratory_name = laboratory_name

	doc.status = status or "Active"
	if location:
		doc.location = location
	if accreditation_scope:
		doc.accreditation_scope = accreditation_scope
	if scope_file:
		scope_file = assert_internal_file(scope_file, "Laboratory scope file")
		# Prefer scope_sheet; also keep PDF field when file is PDF
		doc.scope_sheet = scope_file
		if str(scope_file).lower().endswith(".pdf"):
			doc.accreditation_scope_pdf = scope_file
	if contact_person:
		doc.contact_person = contact_person
	if email:
		doc.email = email
	if phone:
		doc.phone = phone

	doc.save(ignore_permissions=False)
	frappe.db.commit()
	return {"laboratory": doc.name, "laboratory_name": doc.laboratory_name}


@frappe.whitelist()
def import_laboratory_scopes_csv(laboratory: str, file_url: str):
	"""Import test scope rows (name, standard, category, selling_price) from CSV/Excel-as-CSV."""
	if not laboratory or not frappe.db.exists("IC Laboratory", laboratory):
		frappe.throw(_("Laboratory not found"))
	if not file_url:
		frappe.throw(_("Select a CSV from My Device or File Library first"))

	file_url = assert_internal_file(file_url, "CSV file")
	_fname, content = get_file(file_url)
	if isinstance(content, bytes):
		text = content.decode("utf-8-sig", errors="ignore")
	else:
		text = str(content)

	reader = csv.DictReader(io.StringIO(text))
	if not reader.fieldnames:
		frappe.throw(_("CSV has no header row"))

	def pick(row, *keys):
		lower = {(k or "").strip().lower(): v for k, v in row.items()}
		for key in keys:
			if key in lower and lower[key] not in (None, ""):
				return str(lower[key]).strip()
		return ""

	doc = frappe.get_doc("IC Laboratory", laboratory)
	added = 0
	for row in reader:
		test_name = pick(row, "test_name", "test", "name", "scope", "test name")
		if not test_name:
			continue
		standard = pick(row, "applicable_standard", "standard", "applicable standard")
		category = pick(row, "category", "type")
		selling = pick(row, "selling_price", "price", "selling price", "rate")
		purchase = pick(row, "purchase_price", "buying_price", "cost", "buying price")
		doc.append(
			"test_scopes",
			{
				"test_name": test_name,
				"applicable_standard": standard,
				"category": category,
				"selling_price": float(selling or 0) if selling else 0,
				"purchase_price": float(purchase or 0) if purchase else 0,
				"is_active": 1,
			},
		)
		added += 1

	if not added:
		frappe.throw(_("No scope rows found. Use headers like test_name, applicable_standard, selling_price."))

	doc.save(ignore_permissions=False)
	frappe.db.commit()
	return {"laboratory": doc.name, "added": added}


@frappe.whitelist()
def get_library_summary():
	"""Counts for Home / explore prompts."""
	return {
		"quote_templates": frappe.db.count("IC Quotation Template", {"is_active": 1}),
		"laboratories": frappe.db.count("IC Laboratory", {"status": "Active"}),
		"labs_with_scope_file": frappe.db.count(
			"IC Laboratory",
			{"status": "Active", "scope_sheet": ["is", "set"]},
		),
		"templates_with_upload": frappe.db.sql(
			"""
			select count(*) from `tabIC Quotation Template`
			where ifnull(uploaded_format,'') != '' or ifnull(uploaded_template_pack,'') != ''
			"""
		)[0][0],
	}


def _public_file(file_name: str, content: str | bytes, content_type: str | None = None) -> dict:
	"""Create or reuse a public File and return its URL."""
	existing = frappe.db.get_value("File", {"file_name": file_name, "is_private": 0}, "file_url")
	if existing:
		return {"ok": True, "file_url": existing, "file_name": file_name}
	doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": file_name,
			"content": content,
			"is_private": 0,
		}
	)
	if content_type:
		doc.content_type = content_type
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": True, "file_url": doc.file_url, "file_name": file_name}


@frappe.whitelist()
def download_lab_scope_template() -> dict:
	"""Downloadable CSV template for laboratory scope row import."""
	content = (
		"test_name,applicable_standard,category,selling_price,purchase_price\n"
		"EMI/EMC Radiated Emission,CISPR 32,EMC,25000,18000\n"
		"Safety Insulation Resistance,IEC 62368-1,Safety,8000,5500\n"
		"RF Conducted Spurious,ETSI EN 300 328,RF,15000,11000\n"
	)
	return _public_file("IC_Laboratory_Scope_Upload_Template.csv", content, "text/csv")


@frappe.whitelist()
def download_quote_format_upload_template() -> dict:
	"""Downloadable CSV template for quotation / quote-format library uploads."""
	# Remove stale HTML sample if present so users are not served the old format.
	for stale in (
		"IC_Quote_Format_Upload_Template.html",
		"IC_Quotation_Upload_Template.html",
	):
		try:
			name = frappe.db.get_value("File", {"file_name": stale, "is_private": 0}, "name")
			if name:
				frappe.delete_doc("File", name, ignore_permissions=True, force=True)
		except Exception:
			pass

	buf = io.StringIO()
	writer = csv.writer(buf)
	writer.writerow(
		[
			"template_name",
			"quotation_type",
			"service_family",
			"service_name",
			"certification_type",
			"applicable_standard",
			"estimated_timeline",
			"validity_days",
			"scope_of_work",
			"deliverables",
			"payment_terms",
			"template_notes",
			"is_active",
		]
	)
	writer.writerow(
		[
			"BIS CRS Consulting",
			"Consulting",
			"BIS CRS",
			"BIS CRS Registration Support",
			"BIS CRS",
			"IS 13252",
			"4–6 weeks",
			"90",
			"Application preparation, portal filing, and liaison until registration.",
			"Draft application pack; filing tracker; registration certificate handoff.",
			"50% advance; balance on grant of registration.",
			"Sample consulting quote template — edit before use.",
			"1",
		]
	)
	writer.writerow(
		[
			"EMC Testing Package",
			"Testing",
			"EMC",
			"EMI/EMC Lab Testing",
			"EMC",
			"CISPR 32",
			"2–3 weeks",
			"60",
			"Radiated and conducted emission tests as per CISPR 32.",
			"Test report PDF; raw data pack.",
			"100% before sample dispatch.",
			"Sample testing quote template — edit before use.",
			"1",
		]
	)
	writer.writerow(
		[
			"BIS Renewal",
			"Renewal",
			"BIS Renewal",
			"BIS Licence Renewal",
			"BIS",
			"",
			"3–5 weeks",
			"90",
			"Renewal documentation, portal update, and follow-up.",
			"Renewed licence copy.",
			"40% advance; balance on renewal.",
			"Sample renewal quote template — edit before use.",
			"1",
		]
	)
	content = buf.getvalue()

	# Force-refresh public file (overwrite if an older CSV exists)
	existing = frappe.db.get_value(
		"File", {"file_name": "IC_Quotation_Upload_Template.csv", "is_private": 0}, "name"
	)
	if existing:
		try:
			frappe.delete_doc("File", existing, ignore_permissions=True, force=True)
			frappe.db.commit()
		except Exception:
			pass

	return _public_file("IC_Quotation_Upload_Template.csv", content, "text/csv")


@frappe.whitelist()
def import_quote_templates_csv(file_url: str):
	"""Create/update IC Quotation Template rows from a CSV upload template."""
	if not file_url:
		frappe.throw(_("Select a CSV from My Device or File Library first"))

	file_url = assert_internal_file(file_url, "CSV file")
	_fname, content = get_file(file_url)
	if isinstance(content, bytes):
		text = content.decode("utf-8-sig", errors="ignore")
	else:
		text = str(content)

	reader = csv.DictReader(io.StringIO(text))
	if not reader.fieldnames:
		frappe.throw(_("CSV has no header row"))

	def pick(row, *keys):
		lower = {(k or "").strip().lower().replace(" ", "_"): v for k, v in row.items()}
		# also allow spaces in headers
		for k, v in list(row.items()):
			lower[(k or "").strip().lower()] = v
		for key in keys:
			if key in lower and lower[key] not in (None, ""):
				return str(lower[key]).strip()
		return ""

	allowed_types = {
		"Consulting",
		"Testing",
		"Renewal",
		"Other",
		"Multiple Products / Multiple Services",
		"Service",
	}
	created = []
	updated = []
	for row in reader:
		template_name = pick(row, "template_name", "template", "name")
		if not template_name:
			continue
		qtype = pick(row, "quotation_type", "quote_type", "type") or "Consulting"
		if qtype not in allowed_types:
			frappe.throw(_("Invalid quotation_type '{0}' for {1}").format(qtype, template_name))

		exists = frappe.db.exists("IC Quotation Template", template_name)
		doc = (
			frappe.get_doc("IC Quotation Template", template_name)
			if exists
			else frappe.new_doc("IC Quotation Template")
		)
		if not exists:
			doc.template_name = template_name

		doc.quotation_type = qtype
		doc.service_family = pick(row, "service_family", "service family") or doc.service_family
		doc.service_name = pick(row, "service_name", "service", "service / consultancy title") or doc.service_name
		doc.certification_type = pick(row, "certification_type", "certification type") or doc.certification_type
		doc.applicable_standard = (
			pick(row, "applicable_standard", "standard", "applicable standard") or doc.applicable_standard
		)
		doc.estimated_timeline = (
			pick(row, "estimated_timeline", "timeline", "estimated timeline") or doc.estimated_timeline
		)
		validity = pick(row, "validity_days", "validity", "validity days")
		if validity:
			try:
				doc.validity_days = int(float(validity))
			except Exception:
				pass
		for field, keys in (
			("scope_of_work", ("scope_of_work", "scope", "scope of work")),
			("deliverables", ("deliverables", "deliverable")),
			("payment_terms", ("payment_terms", "payment terms")),
			("template_notes", ("template_notes", "notes", "template notes")),
			("about_service", ("about_service", "about")),
			("terms_and_conditions", ("terms_and_conditions", "terms", "t&c")),
		):
			val = pick(row, *keys)
			if val and hasattr(doc, field):
				setattr(doc, field, val)

		active = pick(row, "is_active", "active")
		if active != "":
			doc.is_active = 1 if str(active).strip().lower() in ("1", "yes", "true", "y", "active") else 0
		elif not exists:
			doc.is_active = 1

		doc.save(ignore_permissions=False)
		(updated if exists else created).append(doc.name)

	if not created and not updated:
		frappe.throw(
			_(
				"No template rows found. Use headers like template_name, quotation_type, service_family, scope_of_work."
			)
		)

	frappe.db.commit()
	return {
		"created": len(created),
		"updated": len(updated),
		"templates": created + updated,
	}
