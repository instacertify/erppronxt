# Copyright (c) Instacertify
"""Admin Excel download of list rows and the quotation sections that print with them."""

from __future__ import annotations

import io
from typing import Any

import frappe
from frappe import _

from instacertify.quotation.print_sections import quote_section_on, quote_section_order, quote_section_text
from instacertify.setup.role_profiles import assert_can_export

# Lists an admin may download. Passwords and tokens are never included.
LIST_COLUMNS: dict[str, list[tuple[str, str]]] = {
	"Lead": [
		("name", "Lead"),
		("lead_name", "Name"),
		("company_name", "Company"),
		("status", "Status"),
		("email_id", "Email"),
		("mobile_no", "Phone"),
		("source", "Source"),
		("ic_lead_source_detail", "Source detail"),
		("ic_project_type", "Inquiry for"),
		("ic_request_category", "Category"),
		("city", "City"),
		("state", "State"),
		("ic_next_contact_date", "Next contact"),
		("ic_call_remarks", "Remarks"),
		("creation", "Created"),
	],
	"Customer": [
		("name", "Customer"),
		("customer_name", "Customer name"),
		("customer_group", "Group"),
		("territory", "Territory"),
		("customer_type", "Type"),
		("mobile_no", "Phone"),
		("email_id", "Email"),
		("ic_state", "State"),
		("ic_website_link", "Website"),
		("creation", "Created"),
	],
	"Sales Invoice": [
		("name", "Invoice"),
		("customer", "Customer"),
		("customer_name", "Customer name"),
		("posting_date", "Date"),
		("status", "Status"),
		("currency", "Currency"),
		("grand_total", "Grand total"),
		("outstanding_amount", "Outstanding"),
		("due_date", "Due date"),
	],
}


def _testing(doc) -> bool:
	return (doc.get("ic_quotation_type") or "") in ("Testing", "Multiple Products / Multiple Services")


def _plain(value) -> str:
	text = quote_section_text(value or "")
	if len(text) > 2000:
		return text[:2000]
	return text


def _shown(doc, field: str) -> str:
	return "Yes" if quote_section_on(doc, field) else "No"


def _first(doc, *names: str, default: str = "") -> str:
	for name in names:
		value = _plain(doc.get(name))
		if value:
			return value
	return default


# key, show field, heading fields (testing, otherwise), default heading, body fields
_SECTIONS: list[tuple] = [
	("about", "ic_show_about", ("ic_label_about_testing", "ic_label_about"), "ABOUT", ("ic_about_testing", "ic_about_service", "ic_scope_of_work")),
	("applicable_standards", "ic_show_applicable_standards", ("ic_label_applicable_standards", "ic_label_standard"), "Applicable Standards", ("ic_applicable_standards_text", "ic_standard_narrative", "ic_applicable_standard")),
	("process", "ic_show_process", ("ic_label_process",), "Process", ("ic_process_steps",)),
	("validity", "ic_show_validity", ("ic_label_validity",), "Validity", ("ic_validity_text",)),
	("sample_required", "ic_show_sample_required", ("ic_label_samples_requirements", "ic_label_sample_required"), "Sample Required", ("ic_sample_required", "ic_samples_note")),
	("documents_required", "ic_show_documents_required", ("ic_label_documents_required",), "Documents Required", ("ic_documents_required",)),
	("timelines", "ic_show_timelines", ("ic_label_timeline", "ic_label_timelines"), "Timeline", ("ic_timeline_details", "ic_estimated_timeline")),
	("deliverables", "ic_show_deliverables", ("ic_label_deliverable",), "Deliverables", ("ic_deliverables",)),
	("commercials", "ic_show_commercials", ("ic_label_commercials",), "Commercials", ("ic_commercials_notes",)),
	("payment_terms", "ic_show_payment_terms", ("ic_label_payment_term", "ic_label_payment_terms"), "Payment Terms", ("ic_payment_terms",)),
	("banking", "ic_show_banking", ("ic_label_banking",), "Our Banking Details", ("ic_bank_account",)),
	("cancellation", "ic_show_cancellation", ("ic_label_cancellation",), "Cancellation & Refund Policy", ("ic_cancellation_policy",)),
	("force_majeure", "ic_show_force_majeure", ("ic_label_force_majeure",), "Force Majeure", ("ic_force_majeure",)),
	("confidentiality", "ic_show_confidentiality", ("ic_label_confidentiality",), "Confidentiality & Data Protection", ("ic_confidentiality",)),
	("terms", "ic_show_terms", ("ic_label_terms",), "Terms and Conditions", ("ic_terms_and_conditions",)),
	("sample_handling", "ic_show_sample_handling", ("ic_label_sample_handling",), "Sample handling & disposal policy", ("ic_sample_handling_policy",)),
]


def quotation_export_header() -> list[str]:
	header = [
		"Quotation",
		"Customer",
		"Customer name",
		"Date",
		"Status",
		"Type",
		"Quote format",
		"Currency",
		"Section order",
		"Subject heading",
		"Subject",
		"Test lines",
		"Commercial lines",
	]
	for key, _show, _heads, default, _body in _SECTIONS:
		title = default
		header.extend([f"{title} shown", f"{title} heading", f"{title} text"])
	return header


def quotation_export_row(doc, test_count: int = 0, cost_count: int = 0) -> list[Any]:
	testing = _testing(doc)
	order = quote_section_order(doc)
	row: list[Any] = [
		doc.get("name") or "",
		doc.get("party_name") or "",
		doc.get("customer_name") or "",
		str(doc.get("transaction_date") or ""),
		doc.get("status") or "",
		doc.get("ic_quotation_type") or "",
		doc.get("ic_quotation_template") or "",
		doc.get("currency") or "",
		", ".join(order),
		_plain(doc.get("ic_label_subject")) or "Subject",
		_plain(doc.get("ic_subject")),
		test_count,
		cost_count,
	]
	for key, show, heads, default, bodies in _SECTIONS:
		heading_fields = (heads[0],) if testing and len(heads) > 1 else (heads[-1],)
		if key == "about" and not testing:
			heading_fields = ("ic_label_about",)
		if key == "applicable_standards" and not testing:
			heading_fields = ("ic_label_standard",)
		if key == "sample_required" and not testing:
			heading_fields = ("ic_label_sample_required",)
		if key == "timelines" and not testing:
			heading_fields = ("ic_label_timelines",)
		if key == "payment_terms" and not testing:
			heading_fields = ("ic_label_payment_terms",)
		body_fields = bodies
		if key == "about":
			body_fields = ("ic_about_testing", "ic_scope_of_work") if testing else ("ic_about_service", "ic_scope_of_work")
		row.append(_shown(doc, show))
		row.append(_first(doc, *heading_fields, default=default))
		row.append(_first(doc, *body_fields))
	return row


def _rows_for_doctype(doctype: str) -> tuple[str, list[list[Any]]]:
	columns = LIST_COLUMNS[doctype]
	meta = frappe.get_meta(doctype)
	fields = ["name"]
	for field, _label in columns:
		if field != "name" and meta.has_field(field):
			fields.append(field)
	records = frappe.get_all(doctype, fields=fields, limit=5000, order_by="modified desc")
	header = [label for field, label in columns if field == "name" or meta.has_field(field)]
	kept = [(field, label) for field, label in columns if field == "name" or meta.has_field(field)]
	rows = [header]
	for rec in records:
		rows.append([rec.get(field) if rec.get(field) is not None else "" for field, _label in kept])
	return doctype[:31], rows


def _template_rows() -> list[list[Any]]:
	meta = frappe.get_meta("IC Quotation Template")
	base = [
		("name", "Template ID"),
		("display_name", "Display name"),
		("template_name", "Template name"),
		("quotation_type", "Type"),
		("service_family", "Service family"),
		("is_active", "Active"),
		("section_order", "Section order"),
	]
	extra = []
	for df in meta.fields:
		if df.fieldname and (df.fieldname.startswith("show_") or df.fieldname.startswith("label_")):
			extra.append((df.fieldname, df.label or df.fieldname))
	columns = [(f, label) for f, label in base + extra if meta.has_field(f) or f == "name"]
	fields = [f for f, _label in columns if f != "name"]
	records = frappe.get_all("IC Quotation Template", fields=["name", *fields], limit=2000, order_by="modified desc")
	rows = [[label for _f, label in columns]]
	for rec in records:
		rows.append([rec.get(field) if rec.get(field) is not None else "" for field, _label in columns])
	return rows


def build_workbook(doctype: str) -> tuple[str, bytes]:
	"""Return (filename, xlsx bytes) for an allowed list."""
	import xlsxwriter

	sheets: list[tuple[str, list[list[Any]]]] = []
	if doctype == "Quotation":
		quotes = frappe.get_all(
			"Quotation",
			fields=[
				"name",
				"party_name",
				"customer_name",
				"transaction_date",
				"status",
				"currency",
				"ic_quotation_type",
				"ic_quotation_template",
				"ic_section_order",
				"ic_subject",
				"ic_label_subject",
			],
			limit=2000,
			order_by="modified desc",
		)
		names = [q.name for q in quotes]
		# Pull the section fields in one pass per quote via get_doc only when few;
		# for the list, a second get_all of the long fields keeps it one query.
		qmeta = frappe.get_meta("Quotation")
		detail_fields = ["name"]
		for _key, show, heads, _default, bodies in _SECTIONS:
			for field in (*heads, *bodies, show):
				if field not in detail_fields and qmeta.has_field(field):
					detail_fields.append(field)
		details = {}
		if names:
			for row in frappe.get_all("Quotation", filters={"name": ["in", names]}, fields=detail_fields, limit=len(names)):
				details[row.name] = row
		test_rows = frappe.get_all(
			"IC Quotation Test Item",
			filters={"parent": ["in", names]} if names else {"name": ["in", ["__none__"]]},
			fields=[
				"parent",
				"idx",
				"test_name",
				"applicable_standard",
				"description",
				"number_of_samples",
				"sample_requirement",
				"currency",
				"suggested_selling_price",
				"testing_charges",
			],
			order_by="parent asc, idx asc",
			limit=20000,
		) if names else []
		cost_rows = frappe.get_all(
			"IC Quotation Cost Item",
			filters={"parent": ["in", names]} if names else {"name": ["in", ["__none__"]]},
			fields=[
				"parent",
				"idx",
				"particulars",
				"description",
				"qty",
				"currency",
				"amount",
				"total_amount",
				"charges_display",
				"exclude_from_total",
			],
			order_by="parent asc, idx asc",
			limit=20000,
		) if names else []
		test_count: dict[str, int] = {}
		for line in test_rows:
			test_count[line.parent] = test_count.get(line.parent, 0) + 1
		cost_count: dict[str, int] = {}
		for line in cost_rows:
			cost_count[line.parent] = cost_count.get(line.parent, 0) + 1
		customers = {q.name: q.customer_name for q in quotes}
		quote_sheet = [quotation_export_header()]
		for q in quotes:
			doc = details.get(q.name) or q
			doc.ic_quotation_type = q.get("ic_quotation_type")
			doc.ic_section_order = q.get("ic_section_order")
			doc.party_name = q.get("party_name")
			doc.customer_name = q.get("customer_name")
			doc.transaction_date = q.get("transaction_date")
			doc.status = q.get("status")
			doc.currency = q.get("currency")
			doc.ic_quotation_template = q.get("ic_quotation_template")
			doc.name = q.name
			quote_sheet.append(quotation_export_row(doc, test_count.get(q.name, 0), cost_count.get(q.name, 0)))
		tests = [[
			"Quotation",
			"Customer name",
			"Row",
			"Test",
			"Standard",
			"Description",
			"No. of samples",
			"Sample required",
			"Currency",
			"Unit price",
			"Total",
		]]
		for line in test_rows:
			tests.append([
				line.parent,
				customers.get(line.parent, ""),
				line.idx,
				line.test_name or "",
				line.applicable_standard or "",
				_plain(line.description),
				line.number_of_samples or "",
				_plain(line.sample_requirement),
				line.currency or "",
				line.suggested_selling_price or "",
				line.testing_charges or "",
			])
		costs = [[
			"Quotation",
			"Customer name",
			"Row",
			"Particulars",
			"Description",
			"Qty",
			"Currency",
			"Unit price",
			"Total",
			"Custom value",
			"Do not sum",
		]]
		for line in cost_rows:
			costs.append([
				line.parent,
				customers.get(line.parent, ""),
				line.idx,
				line.particulars or "",
				_plain(line.description),
				line.qty or "",
				line.currency or "",
				line.amount or "",
				line.total_amount or "",
				line.charges_display or "",
				"Yes" if line.exclude_from_total else "No",
			])
		sheets = [("Quotations", quote_sheet), ("Test lines", tests), ("Commercial lines", costs)]
		filename = "Instacertify_Quotations.xlsx"
	elif doctype == "IC Quotation Template":
		sheets = [("Quote formats", _template_rows())]
		filename = "Instacertify_Quote_Formats.xlsx"
	elif doctype in LIST_COLUMNS:
		sheet_name, rows = _rows_for_doctype(doctype)
		sheets = [(sheet_name, rows)]
		filename = f"Instacertify_{doctype.replace(' ', '_')}.xlsx"
	else:
		frappe.throw(_("This list cannot be downloaded."))

	buf = io.BytesIO()
	wb = xlsxwriter.Workbook(buf, {"in_memory": True})
	head = wb.add_format({"bold": True, "bg_color": "#065175", "font_color": "#FFFFFF", "text_wrap": True, "valign": "top"})
	cell = wb.add_format({"text_wrap": True, "valign": "top"})
	for name, rows in sheets:
		ws = wb.add_worksheet(name[:31])
		for r, row in enumerate(rows):
			for c, value in enumerate(row):
				ws.write(r, c, "" if value is None else value, head if r == 0 else cell)
		if rows and rows[0]:
			ws.freeze_panes(1, 0)
			ws.autofilter(0, 0, max(len(rows) - 1, 0), len(rows[0]) - 1)
			ws.set_column(0, len(rows[0]) - 1, 22)
	wb.close()
	buf.seek(0)
	return filename, buf.getvalue()


@frappe.whitelist()
def download_list_excel(doctype: str):
	"""Download the list, and for quotations every print section, as an Excel file."""
	assert_can_export()
	doctype = (doctype or "").strip()
	if doctype not in set(LIST_COLUMNS) | {"Quotation", "IC Quotation Template"}:
		frappe.throw(_("This list cannot be downloaded."))
	if not frappe.has_permission(doctype, "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	filename, content = build_workbook(doctype)
	frappe.local.response.filename = filename
	frappe.local.response.filecontent = content
	frappe.local.response.type = "binary"
