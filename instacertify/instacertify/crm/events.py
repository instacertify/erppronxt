# Copyright (c) Instacertify
"""Lead / CRM events."""

from __future__ import annotations

import frappe
from frappe import _


def before_validate_lead(doc, method=None):
	"""Run before ERPNext Lead.validate so party name satisfies core checks."""
	_sync_party_name(doc)


def validate_lead(doc, method=None):
	_sync_party_name(doc)
	_ensure_mandatory_name(doc)
	if not doc.get("ic_pipeline_stage"):
		doc.ic_pipeline_stage = "Lead"

	# Keep UTM source aligned for analytics when available
	if doc.get("ic_lead_source_detail") and hasattr(doc, "utm_source") and not doc.utm_source:
		source = doc.ic_lead_source_detail
		if frappe.db.exists("DocType", "UTM Source") and frappe.db.exists("UTM Source", source):
			doc.utm_source = source

	if doc.country == "India" and doc.get("ic_gst_number"):
		doc.ic_gst_number = (doc.ic_gst_number or "").strip().upper()


def _sync_party_name(doc):
	"""Keep ERPNext company_name / first_name in sync with mandatory party name."""
	party = (doc.get("ic_party_name") or "").strip()
	if not party:
		party = (doc.get("company_name") or doc.get("lead_name") or doc.get("first_name") or "").strip()
		if party:
			doc.ic_party_name = party
	if not party:
		return

	if not doc.company_name:
		doc.company_name = party
	if not (doc.first_name or doc.last_name or doc.middle_name):
		doc.first_name = party.split()[0][:140]


def _ensure_mandatory_name(doc):
	from frappe import _

	if not (doc.get("ic_party_name") or "").strip():
		frappe.throw(_("Name of Person / Firm is mandatory"))


@frappe.whitelist()
def get_customer_history(customer: str):
	"""Complete customer relationship overview for Customer Related Data tab."""
	if not customer:
		return {}
	from instacertify.crm.customer_permissions import assert_can_read_customer_data

	assert_can_read_customer_data(customer)

	def list_docs(doctype, filters, fields=None, limit=100):
		if not frappe.db.exists("DocType", doctype):
			return []
		try:
			# Caller already authorized for this customer's data — avoid child DocType
			# permission gaps (e.g. Dynamic Link) blocking the overview.
			return frappe.get_all(
				doctype,
				filters=filters,
				fields=fields or ["name", "modified"],
				order_by="modified desc",
				limit_page_length=limit,
			)
		except Exception:
			return []

	customer_name = frappe.db.get_value("Customer", customer, "customer_name") or customer

	leads = list_docs(
		"Lead",
		{"company_name": customer_name},
		["name", "status", "source", "ic_request_category", "modified"],
	)
	opportunities = list_docs(
		"Opportunity",
		{"party_name": customer, "opportunity_from": "Customer"},
		["name", "status", "opportunity_amount", "currency", "transaction_date", "title"],
	)
	quotations = list_docs(
		"Quotation",
		{"party_name": customer, "quotation_to": "Customer"},
		[
			"name",
			"status",
			"ic_workflow_status",
			"grand_total",
			"currency",
			"transaction_date",
			"valid_till",
		],
	)
	projects = list_docs(
		"Project",
		{"customer": customer},
		[
			"name",
			"project_name",
			"status",
			"ic_project_stage",
			"ic_progress_percentage",
			"ic_deadline",
			"expected_end_date",
			"ic_quotation",
		],
	)
	testing = list_docs(
		"IC Testing Request",
		{"customer": customer},
		[
			"name",
			"title",
			"status",
			"product",
			"test_name",
			"applicable_standard",
			"laboratory",
			"project",
			"quotation",
			"number_of_samples",
			"modified",
		],
	)
	# Resolve laboratory titles for customer history
	lab_ids = {t.get("laboratory") for t in testing if t.get("laboratory")}
	lab_map = {}
	if lab_ids and frappe.db.exists("DocType", "IC Laboratory"):
		for lab in frappe.get_all(
			"IC Laboratory",
			filters={"name": ["in", list(lab_ids)]},
			fields=["name", "laboratory_name", "location"],
		):
			lab_map[lab.name] = lab
	for t in testing:
		lab = lab_map.get(t.get("laboratory")) or {}
		t["laboratory_name"] = lab.get("laboratory_name") or t.get("laboratory")
		t["laboratory_city"] = lab.get("location") or ""

	sample_fields = [
		"name",
		"tracking_number",
		"status",
		"sample_location",
		"sample_description",
		"laboratory",
		"testing_request",
		"project",
		"modified",
	]
	if frappe.get_meta("IC Sample Tracking").has_field("quotation"):
		sample_fields.append("quotation")
	samples = list_docs(
		"IC Sample Tracking",
		{"customer": customer},
		sample_fields,
	)
	sample_lab_ids = {s.get("laboratory") for s in samples if s.get("laboratory")}
	missing_labs = sample_lab_ids - set(lab_map)
	if missing_labs:
		for lab in frappe.get_all(
			"IC Laboratory",
			filters={"name": ["in", list(missing_labs)]},
			fields=["name", "laboratory_name", "location"],
		):
			lab_map[lab.name] = lab
	for s in samples:
		lab = lab_map.get(s.get("laboratory")) or {}
		s["laboratory_name"] = lab.get("laboratory_name") or s.get("laboratory")
		s["custody_label"] = s.get("sample_location") or s.get("status") or "—"

	invoices = list_docs(
		"Sales Invoice",
		{"customer": customer, "docstatus": ["<", 2]},
		[
			"name",
			"grand_total",
			"outstanding_amount",
			"status",
			"currency",
			"posting_date",
			"docstatus",
			"ic_quotation",
		],
	)
	payments = list_docs(
		"Payment Entry",
		{"party_type": "Customer", "party": customer, "docstatus": ["<", 2]},
		[
			"name",
			"posting_date",
			"paid_amount",
			"received_amount",
			"currency",
			"status",
			"mode_of_payment",
			"docstatus",
			"payment_type",
		],
	)
	documents = list_docs(
		"IC Document Request",
		{"customer": customer},
		["name", "title", "status", "modified", "company_legal_name", "gstin", "product_name"],
	)
	sample_dispatches = list_docs(
		"IC Sample Dispatch Collection",
		{"customer": customer},
		["name", "status", "tracking_number", "courier_name", "submitted_on", "modified"],
	)
	contracts = list_docs(
		"IC Contract",
		{"customer": customer},
		["name", "title", "status", "customer_signed_name", "accepted_on", "modified"],
	)
	tickets = list_docs(
		"Helpdesk Ticket",
		{"customer": customer},
		[
			"name",
			"subject",
			"ticket_type",
			"status",
			"priority",
			"opened_on",
			"assigned_to",
			"modified",
		],
	)
	records = list_docs(
		"IC Project Record",
		{"customer": customer},
		["name", "subject", "record_type", "category", "modified"],
	)
	# Files attached to completed projects for this customer
	project_files = []
	completed_project_names = [
		p["name"]
		for p in projects
		if p.get("status") == "Completed" or p.get("ic_project_stage") == "Project Completed"
	]
	for pname in completed_project_names[:30]:
		files = frappe.get_all(
			"File",
			filters={
				"attached_to_doctype": "Project",
				"attached_to_name": pname,
				"is_folder": 0,
			},
			fields=["name", "file_name", "file_url", "creation", "attached_to_name", "content_hash"],
			order_by="creation desc",
			limit_page_length=30,
		)
		for f in files:
			f["project"] = pname
			f["source"] = "Project"
			project_files.append(f)
	# Also IC Project Record attachments for this customer
	for rec in records[:30]:
		files = frappe.get_all(
			"File",
			filters={
				"attached_to_doctype": "IC Project Record",
				"attached_to_name": rec["name"],
				"is_folder": 0,
			},
			fields=["name", "file_name", "file_url", "creation", "attached_to_name", "content_hash"],
			limit_page_length=15,
		)
		for f in files:
			f["project"] = rec["name"]
			f["record"] = rec["name"]
			f["source"] = "IC Project Record"
			project_files.append(f)

	# Files already saved on this Customer
	customer_files = frappe.get_all(
		"File",
		filters={
			"attached_to_doctype": "Customer",
			"attached_to_name": customer,
			"is_folder": 0,
		},
		fields=["name", "file_name", "file_url", "creation", "content_hash", "file_size"],
		order_by="creation desc",
		limit_page_length=200,
	)
	for f in customer_files:
		fname = f.get("file_name") or ""
		if fname.startswith("Collected Data-"):
			f["category"] = "Collected Data"
		elif fname.startswith("Documents-"):
			f["category"] = "Documents"
		elif fname.startswith("Samples-"):
			f["category"] = "Samples"
		elif fname.startswith("Contracts-"):
			f["category"] = "Contracts"
		else:
			f["category"] = "Uploaded"
		f["source"] = "Customer"
		f["source_doctype"] = "Customer"
		f["source_name"] = customer

	# Full data-drive index (all related sources)
	drive = _build_customer_data_drive(
		customer,
		projects=projects,
		quotations=quotations,
		invoices=invoices,
		testing=testing,
		samples=samples,
		documents=documents,
		tickets=tickets,
		records=records,
		opportunities=opportunities,
		customer_files=customer_files,
		project_files=project_files,
		sample_dispatches=sample_dispatches,
		contracts=contracts,
	)
	try:
		from instacertify.crm.report_share import enrich_drive_files_with_shares

		drive["files"] = enrich_drive_files_with_shares(customer, drive.get("files") or [])
	except Exception:
		frappe.log_error(frappe.get_traceback(), "enrich drive report shares")

	contacts = frappe.get_all(
		"Dynamic Link",
		filters={"link_doctype": "Customer", "link_name": customer, "parenttype": "Contact"},
		fields=["parent"],
	)
	contact_details = []
	for c in contacts:
		contact = frappe.db.get_value(
			"Contact",
			c.parent,
			[
				"name",
				"first_name",
				"last_name",
				"email_id",
				"mobile_no",
				"is_primary_contact",
				"designation",
			],
			as_dict=True,
		)
		if contact:
			contact_details.append(contact)

	accepted = [q for q in quotations if q.get("ic_workflow_status") == "Accepted"]
	active_quotes = [
		q
		for q in quotations
		if q.get("ic_workflow_status")
		in ("Shared with Customer", "Customer Review", "Ready to Share")
	]
	shared_quotes = [
		q
		for q in quotations
		if q.get("ic_workflow_status")
		in ("Shared with Customer", "Customer Review", "Accepted", "Ready to Share")
	]
	active_projects = [p for p in projects if p.get("status") not in ("Completed", "Cancelled")]
	completed_projects = [
		p
		for p in projects
		if p.get("status") == "Completed" or p.get("ic_project_stage") == "Project Completed"
	]

	billed = sum(
		float(i.get("grand_total") or 0) for i in invoices if int(i.get("docstatus") or 0) == 1
	)
	outstanding = sum(
		float(i.get("outstanding_amount") or 0)
		for i in invoices
		if int(i.get("docstatus") or 0) == 1
	)
	paid = sum(
		float(p.get("received_amount") or p.get("paid_amount") or 0)
		for p in payments
		if int(p.get("docstatus") or 0) == 1 and p.get("payment_type") == "Receive"
	)

	return {
		"customer": customer,
		"customer_name": customer_name,
		"leads": leads,
		"opportunities": opportunities,
		"quotations": quotations,
		"accepted_quotations": accepted,
		"active_quotations": active_quotes,
		"shared_quotations": shared_quotes,
		"projects": projects,
		"active_projects": active_projects,
		"completed_projects": completed_projects,
		"testing_requests": testing,
		"samples": samples,
		"invoices": invoices,
		"payments": payments,
		"documents": documents,
		"sample_dispatches": sample_dispatches,
		"contracts": contracts,
		"tickets": tickets,
		"open_tickets": [
			t for t in tickets if t.get("status") in ("Open", "In Progress", "Waiting on Customer")
		],
		"records": records,
		"project_files": project_files,
		"customer_files": customer_files,
		"completed_project_names": completed_project_names,
		"data_drive": drive,
		"contacts": contact_details,
		"amount_billed": billed,
		"outstanding_amount": outstanding,
		"amount_paid": paid,
	}


def _files_for(doctype: str, names: list, category: str, limit_each: int = 25) -> list[dict]:
	"""Collect File attachments for a set of documents."""
	out: list[dict] = []
	seen: set[str] = set()
	for name in names[:40]:
		if not name:
			continue
		files = frappe.get_all(
			"File",
			filters={
				"attached_to_doctype": doctype,
				"attached_to_name": name,
				"is_folder": 0,
			},
			fields=["name", "file_name", "file_url", "creation", "content_hash", "file_size", "is_private"],
			order_by="creation desc",
			limit_page_length=limit_each,
		)
		for f in files:
			key = f.get("content_hash") or f"{f.get('file_url')}|{f.get('file_name')}"
			if key in seen:
				continue
			seen.add(key)
			f["source"] = doctype
			f["category"] = category
			f["source_doctype"] = doctype
			f["source_name"] = name
			out.append(f)
	return out


def _attach_field_files(doctype: str, names: list, fieldnames: list[str], category: str) -> list[dict]:
	"""Pick up Attach / Attach Image field URLs that may not have a File child link."""
	out: list[dict] = []
	if not names or not frappe.db.exists("DocType", doctype):
		return out
	meta = frappe.get_meta(doctype)
	valid = [f for f in fieldnames if meta.has_field(f)]
	if not valid:
		return out
	for name in names[:40]:
		row = frappe.db.get_value(doctype, name, valid, as_dict=True) or {}
		for field in valid:
			url = (row.get(field) or "").strip()
			if not url or not (url.startswith("/") or url.startswith("http")):
				continue
			fname = url.rstrip("/").split("/")[-1] or field
			out.append(
				{
					"name": f"{doctype}-{name}-{field}",
					"file_name": fname,
					"file_url": url,
					"creation": None,
					"content_hash": None,
					"file_size": None,
					"source": doctype,
					"category": category,
					"source_doctype": doctype,
					"source_name": name,
					"from_attach_field": field,
				}
			)
	return out


def _sample_report_files(sample_names: list) -> list[dict]:
	"""Test reports on Sample Tracking with uploaded-on timestamp for Customer Data Drive."""
	out: list[dict] = []
	if not sample_names or not frappe.db.exists("DocType", "IC Sample Tracking"):
		return out
	meta = frappe.get_meta("IC Sample Tracking")
	if not meta.has_field("test_report"):
		return out
	fields = ["name", "test_report", "tracking_number", "modified"]
	if meta.has_field("report_uploaded_on"):
		fields.append("report_uploaded_on")
	try:
		rows = frappe.get_all(
			"IC Sample Tracking",
			filters={"name": ["in", sample_names], "test_report": ["!=", ""]},
			fields=fields,
			limit_page_length=200,
		)
	except Exception:
		return out
	for r in rows:
		url = (r.get("test_report") or "").strip()
		if not url:
			continue
		stamp = r.get("report_uploaded_on") or r.get("modified")
		fname = url.rstrip("/").split("/")[-1] or "test-report"
		out.append(
			{
				"name": f"IC Sample Tracking-{r.name}-test_report",
				"file_name": f"Test Report — {r.get('tracking_number') or r.name} — {fname}",
				"file_url": url,
				"creation": stamp,
				"content_hash": None,
				"source": "IC Sample Tracking",
				"category": "Test Reports",
				"source_doctype": "IC Sample Tracking",
				"source_name": r.name,
				"label": f"Test Report ({stamp})",
			}
		)
	return out


def _document_request_item_files(doc_names: list) -> list[dict]:
	"""Files uploaded on IC Document Request Item.uploaded_file."""
	out: list[dict] = []
	if not doc_names or not frappe.db.exists("DocType", "IC Document Request Item"):
		return out
	meta = frappe.get_meta("IC Document Request Item")
	file_field = "uploaded_file" if meta.has_field("uploaded_file") else (
		"file_url" if meta.has_field("file_url") else None
	)
	if not file_field:
		return out
	try:
		rows = frappe.get_all(
			"IC Document Request Item",
			filters={"parent": ["in", doc_names], file_field: ["!=", ""]},
			fields=["name", "parent", "document_name", file_field, "status", "modified"],
			limit_page_length=200,
		)
	except Exception:
		return out
	for r in rows:
		url = (r.get(file_field) or "").strip()
		if not url:
			continue
		fname = url.rstrip("/").split("/")[-1] or (r.get("document_name") or r.name)
		out.append(
			{
				"name": f"IC Document Request Item-{r.name}",
				"file_name": fname,
				"file_url": url,
				"creation": r.get("modified"),
				"content_hash": None,
				"source": "IC Document Request",
				"category": "Documents",
				"source_doctype": "IC Document Request",
				"source_name": r.get("parent"),
				"label": r.get("document_name"),
			}
		)
	return out


def _build_customer_data_drive(
	customer: str,
	*,
	projects: list,
	quotations: list,
	invoices: list,
	testing: list,
	samples: list,
	documents: list,
	tickets: list,
	records: list,
	opportunities: list,
	customer_files: list,
	project_files: list,
	sample_dispatches: list | None = None,
	contracts: list | None = None,
) -> dict:
	"""Unified drive index: every file related to this customer, by category."""
	files: list[dict] = []
	files.extend(customer_files or [])

	# Prefer full project set (not only completed) for the drive index
	project_names = [p["name"] for p in (projects or []) if p.get("name")]
	doc_names = [d["name"] for d in (documents or []) if d.get("name")]
	dispatch_names = [d["name"] for d in (sample_dispatches or []) if d.get("name")]
	contract_names = [c["name"] for c in (contracts or []) if c.get("name")]
	record_names = [r["name"] for r in (records or []) if r.get("name")]

	files.extend(_files_for("Project", project_names, "Projects"))
	files.extend(
		_files_for("Quotation", [q["name"] for q in (quotations or [])], "Quotes")
	)
	files.extend(
		_files_for("Sales Invoice", [i["name"] for i in (invoices or [])], "Invoices")
	)
	files.extend(
		_files_for("IC Testing Request", [t["name"] for t in (testing or [])], "Testing")
	)
	files.extend(
		_files_for("IC Sample Tracking", [s["name"] for s in (samples or [])], "Samples")
	)
	files.extend(_sample_report_files([s["name"] for s in (samples or [])]))
	files.extend(
		_attach_field_files(
			"IC Testing Request",
			[t["name"] for t in (testing or [])],
			["test_report"],
			"Test Reports",
		)
	)
	files.extend(_files_for("IC Document Request", doc_names, "Documents"))
	files.extend(_document_request_item_files(doc_names))
	files.extend(
		_attach_field_files(
			"IC Document Request",
			doc_names,
			["pod_attachment"],
			"Samples",
		)
	)
	files.extend(_files_for("IC Sample Dispatch Collection", dispatch_names, "Samples"))
	files.extend(
		_attach_field_files(
			"IC Sample Dispatch Collection",
			dispatch_names,
			["pod_attachment"],
			"Samples",
		)
	)
	files.extend(_files_for("IC Contract", contract_names, "Contracts"))
	files.extend(
		_files_for("Helpdesk Ticket", [t["name"] for t in (tickets or [])], "Support")
	)
	files.extend(_files_for("IC Project Record", record_names, "Records"))
	files.extend(
		_attach_field_files(
			"IC Project Record",
			record_names,
			["attachment"],
			"Records",
		)
	)
	files.extend(
		_files_for("Opportunity", [o["name"] for o in (opportunities or [])], "Quotes")
	)

	# Deduplicate by content hash / url+name (customer copies win as Uploaded / Collected Data)
	deduped: list[dict] = []
	seen: set[str] = set()
	priority_cats = {"Uploaded", "Collected Data"}
	for f in files:
		if f.get("category") not in priority_cats:
			continue
		key = f.get("content_hash") or f"{f.get('file_url')}|{f.get('file_name')}"
		seen.add(key)
		# Collected Data snapshots saved on Customer show as Collected Data
		if (f.get("file_name") or "").startswith("Collected Data-"):
			f["category"] = "Collected Data"
		deduped.append(f)
	for f in files:
		if f.get("category") in priority_cats:
			continue
		key = f.get("content_hash") or f"{f.get('file_url')}|{f.get('file_name')}"
		if key in seen:
			continue
		seen.add(key)
		if (f.get("file_name") or "").startswith("Collected Data-"):
			f["category"] = "Collected Data"
		deduped.append(f)

	# Also include any project_files already gathered that we might have missed
	for f in project_files or []:
		key = f.get("content_hash") or f"{f.get('file_url')}|{f.get('file_name')}"
		if key in seen:
			continue
		seen.add(key)
		row = dict(f)
		row.setdefault("category", "Projects")
		row.setdefault("source_doctype", row.get("source") or "Project")
		row.setdefault("source_name", row.get("project") or row.get("attached_to_name"))
		deduped.append(row)

	counts: dict[str, int] = {}
	for f in deduped:
		cat = f.get("category") or "Other"
		counts[cat] = counts.get(cat, 0) + 1

	deduped.sort(key=lambda x: str(x.get("creation") or ""), reverse=True)

	return {
		"files": deduped,
		"counts": counts,
		"total": len(deduped),
		"categories": [
			"Uploaded",
			"Collected Data",
			"Projects",
			"Quotes",
			"Invoices",
			"Testing",
			"Samples",
			"Documents",
			"Contracts",
			"Support",
			"Records",
			"Other",
		],
	}


@frappe.whitelist()
def get_customer_data_drive(customer: str):
	"""Return the Customer Data Drive index (files across all related records)."""
	hist = get_customer_history(customer)
	return hist.get("data_drive") or {"files": [], "counts": {}, "total": 0, "categories": []}


@frappe.whitelist()
def ensure_customer_drive_folder(customer: str) -> str:
	"""Ensure Home/Customer Drive/<customer> folder exists; return folder name."""
	from instacertify.crm.customer_permissions import assert_can_read_customer_data

	assert_can_read_customer_data(customer)
	return _ensure_customer_drive_folder(customer)


def _ensure_customer_drive_folder(customer: str) -> str:
	"""Ensure Home/Customer Drive/<customer> folder exists; return folder name."""
	root = "Home/Customer Drive"
	if not frappe.db.exists("File", {"is_folder": 1, "name": root}):
		try:
			frappe.get_doc(
				{
					"doctype": "File",
					"file_name": "Customer Drive",
					"is_folder": 1,
					"folder": "Home",
					"is_private": 1,
				}
			).insert(ignore_permissions=True)
		except Exception:
			pass
	# Folder names in Frappe File are path-like: Home/Customer Drive/CUST-0001
	safe = (customer or "Customer").replace("/", "-")[:120]
	folder = f"{root}/{safe}"
	if not frappe.db.exists("File", {"is_folder": 1, "name": folder}):
		try:
			frappe.get_doc(
				{
					"doctype": "File",
					"file_name": safe,
					"is_folder": 1,
					"folder": root,
					"is_private": 1,
				}
			).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Customer Drive folder")
	return folder


@frappe.whitelist()
def sync_customer_data_drive(customer: str):
	"""Copy all related-record files onto the Customer Data Drive."""
	if not customer or not frappe.db.exists("Customer", customer):
		frappe.throw(_("Customer is required"))
	from instacertify.crm.customer_permissions import assert_can_read_customer_data

	assert_can_read_customer_data(customer)

	folder = _ensure_customer_drive_folder(customer)
	drive = get_customer_data_drive(customer)
	existing_hashes = {
		h
		for h in frappe.get_all(
			"File",
			filters={
				"attached_to_doctype": "Customer",
				"attached_to_name": customer,
				"is_folder": 0,
			},
			pluck="content_hash",
		)
		if h
	}
	existing_names = set(
		frappe.get_all(
			"File",
			filters={
				"attached_to_doctype": "Customer",
				"attached_to_name": customer,
				"is_folder": 0,
			},
			pluck="file_name",
		)
	)

	copied = []
	skipped = 0
	for f in drive.get("files") or []:
		if f.get("category") == "Uploaded" and f.get("source_doctype") == "Customer":
			skipped += 1
			continue
		# Only copy real File docs (not synthetic attach-field rows)
		if not frappe.db.exists("File", f.get("name")):
			# Attach-field URL — create a File pointing at the same URL
			url = f.get("file_url")
			fname = f.get("file_name") or "file"
			prefix = f.get("source_name") or f.get("category") or "Drive"
			target_name = f"{prefix}-{fname}"
			if target_name in existing_names or fname in existing_names:
				skipped += 1
				continue
			if not url:
				skipped += 1
				continue
			try:
				new_file = frappe.get_doc(
					{
						"doctype": "File",
						"file_name": target_name,
						"file_url": url,
						"is_private": 1,
						"attached_to_doctype": "Customer",
						"attached_to_name": customer,
						"folder": folder,
					}
				)
				new_file.insert(ignore_permissions=True)
				existing_names.add(new_file.file_name)
				copied.append(new_file.file_name)
			except Exception:
				frappe.log_error(frappe.get_traceback(), f"Drive attach copy {fname}")
			continue
		try:
			prefix = f.get("source_name") or f.get("category") or ""
			result = _copy_file_to_customer(
				f["name"], customer, prefix, existing_hashes, existing_names, folder=folder
			)
			if result == "copied":
				copied.append(f.get("file_name"))
			else:
				skipped += 1
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Drive sync {f.get('name')}")

	return {
		"copied": len(copied),
		"skipped": skipped,
		"files": copied,
		"folder": folder,
		"total_indexed": drive.get("total") or 0,
	}


@frappe.whitelist()
def get_lead_history(lead: str):
	"""Linked quotations, opportunities, customer and support for a Lead."""
	if not lead or not frappe.db.exists("Lead", lead):
		return {}

	def list_docs(doctype, filters, fields=None, limit=80):
		if not frappe.db.exists("DocType", doctype):
			return []
		try:
			return frappe.get_list(
				doctype,
				filters=filters,
				fields=fields or ["name", "modified"],
				order_by="modified desc",
				limit_page_length=limit,
			)
		except Exception:
			return []

	lead_doc = frappe.db.get_value(
		"Lead",
		lead,
		[
			"name",
			"status",
			"company_name",
			"lead_name",
			"ic_party_name",
			"ic_pipeline_stage",
			"email_id",
			"mobile_no",
			"phone",
			"ic_next_contact_date",
			"ic_call_remarks",
			"ic_lead_connected",
			"ic_project_type",
			"ic_estimated_value",
		],
		as_dict=True,
	) or {}

	quotations = list_docs(
		"Quotation",
		{"party_name": lead, "quotation_to": "Lead"},
		[
			"name",
			"status",
			"ic_workflow_status",
			"grand_total",
			"currency",
			"transaction_date",
			"ic_quotation_type",
			"valid_till",
		],
	)
	# Also quotes created after conversion (party became Customer) via opportunity
	opportunities = list_docs(
		"Opportunity",
		{"party_name": lead, "opportunity_from": "Lead"},
		["name", "status", "opportunity_amount", "currency", "transaction_date", "title"],
	)
	# Quotes linked via Opportunity
	for opp in opportunities:
		extra = list_docs(
			"Quotation",
			{"opportunity": opp["name"]},
			[
				"name",
				"status",
				"ic_workflow_status",
				"grand_total",
				"currency",
				"transaction_date",
				"ic_quotation_type",
				"valid_till",
			],
		)
		seen = {q["name"] for q in quotations}
		for q in extra:
			if q["name"] not in seen:
				quotations.append(q)
				seen.add(q["name"])

	customer = None
	if frappe.db.has_column("Customer", "lead_name"):
		customer = frappe.db.get_value("Customer", {"lead_name": lead}, ["name", "customer_name"], as_dict=True)
	projects = []
	invoices = []
	if customer:
		projects = list_docs(
			"Project",
			{"customer": customer.name},
			["name", "project_name", "status", "ic_project_stage", "ic_quotation", "ic_deadline"],
		)
		invoices = list_docs(
			"Sales Invoice",
			{"customer": customer.name, "docstatus": ["<", 2]},
			["name", "grand_total", "status", "posting_date", "ic_quotation", "currency"],
		)

	tickets = list_docs(
		"Helpdesk Ticket",
		{"lead": lead} if frappe.get_meta("Helpdesk Ticket").has_field("lead") else {"name": "__none__"},
		["name", "subject", "status", "ticket_type", "priority", "modified"],
	)
	documents = list_docs(
		"IC Document Request",
		{"lead": lead} if frappe.get_meta("IC Document Request").has_field("lead") else {"name": "__none__"},
		["name", "title", "status", "modified"],
	)

	return {
		"lead": lead_doc,
		"quotations": quotations,
		"opportunities": opportunities,
		"customer": customer,
		"projects": projects,
		"invoices": invoices,
		"tickets": tickets,
		"documents": documents,
		"accepted_quotations": [q for q in quotations if q.get("ic_workflow_status") == "Accepted"],
		"open_quotations": [
			q
			for q in quotations
			if q.get("ic_workflow_status")
			in ("Draft", "Ready to Share", "Shared with Customer", "Customer Review", "Changes Requested")
		],
	}


@frappe.whitelist()
def get_quotation_links(quotation: str):
	"""Linked Lead/Customer, projects, invoices, testing and documents for a Quotation."""
	if not quotation or not frappe.db.exists("Quotation", quotation):
		return {}

	def list_docs(doctype, filters, fields=None, limit=50):
		if not frappe.db.exists("DocType", doctype):
			return []
		try:
			return frappe.get_list(
				doctype,
				filters=filters,
				fields=fields or ["name", "modified"],
				order_by="modified desc",
				limit_page_length=limit,
			)
		except Exception:
			return []

	q = frappe.db.get_value(
		"Quotation",
		quotation,
		[
			"name",
			"quotation_to",
			"party_name",
			"customer_name",
			"opportunity",
			"ic_workflow_status",
			"ic_quotation_type",
			"ic_parent_quotation",
			"grand_total",
			"currency",
			"status",
		],
		as_dict=True,
	) or {}

	party = {"doctype": q.get("quotation_to"), "name": q.get("party_name"), "label": q.get("customer_name")}
	lead = None
	customer = None
	if q.get("quotation_to") == "Lead" and q.get("party_name"):
		lead = frappe.db.get_value(
			"Lead",
			q.party_name,
			["name", "status", "ic_pipeline_stage", "ic_party_name", "company_name", "email_id", "mobile_no"],
			as_dict=True,
		)
	elif q.get("quotation_to") == "Customer" and q.get("party_name"):
		customer = frappe.db.get_value(
			"Customer", q.party_name, ["name", "customer_name", "lead_name"], as_dict=True
		)
		if customer and customer.get("lead_name"):
			lead = frappe.db.get_value(
				"Lead",
				customer.lead_name,
				["name", "status", "ic_pipeline_stage", "ic_party_name", "company_name"],
				as_dict=True,
			)

	projects = list_docs(
		"Project",
		{"ic_quotation": quotation},
		["name", "project_name", "status", "ic_project_stage", "customer", "ic_deadline", "percent_complete"],
	)
	invoices = list_docs(
		"Sales Invoice",
		{"ic_quotation": quotation, "docstatus": ["<", 2]},
		["name", "grand_total", "outstanding_amount", "status", "posting_date", "currency", "customer"],
	)
	testing = list_docs(
		"IC Testing Request",
		{"quotation": quotation},
		["name", "title", "status", "product", "project", "modified"],
	)
	documents = list_docs(
		"IC Document Request",
		{"quotation": quotation},
		["name", "title", "status", "project", "modified"],
	)
	samples = list_docs(
		"IC Sample Tracking",
		{"quotation": quotation} if frappe.get_meta("IC Sample Tracking").has_field("quotation") else {"name": "__none__"},
		["name", "tracking_number", "status", "sample_location", "modified"],
	)
	revisions = list_docs(
		"Quotation",
		{"ic_parent_quotation": quotation},
		["name", "ic_revision_number", "ic_workflow_status", "grand_total", "transaction_date"],
	)

	return {
		"quotation": q,
		"party": party,
		"lead": lead,
		"customer": customer,
		"opportunity": q.get("opportunity"),
		"projects": projects,
		"invoices": invoices,
		"testing_requests": testing,
		"documents": documents,
		"samples": samples,
		"revisions": revisions,
		"parent_quotation": q.get("ic_parent_quotation"),
	}


def _copy_file_to_customer(
	src_file_name, customer, prefix, existing_hashes, existing_names, folder: str | None = None
):
	"""Attach an existing File's URL onto Customer. Returns 'copied' | 'skipped'."""
	src = frappe.get_doc("File", src_file_name)
	if src.content_hash and src.content_hash in existing_hashes:
		return "skipped"
	target_name = f"{prefix}-{src.file_name}" if prefix else src.file_name
	if target_name in existing_names or src.file_name in existing_names:
		return "skipped"
	new_file = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": target_name,
			"file_url": src.file_url,
			"is_private": src.is_private,
			"attached_to_doctype": "Customer",
			"attached_to_name": customer,
			"content_hash": src.content_hash,
			"folder": folder or "Home/Attachments",
		}
	)
	new_file.insert(ignore_permissions=True)
	if src.content_hash:
		existing_hashes.add(src.content_hash)
	existing_names.add(new_file.file_name)
	return "copied"


@frappe.whitelist()
def import_completed_project_files(customer: str):
	"""Back-compat: sync completed project files into the Customer Data Drive."""
	return sync_customer_data_drive(customer)
