# Copyright (c) Instacertify
"""Testing & sample events."""

from __future__ import annotations

import secrets

import frappe
from frappe import _
from frappe.model.naming import make_autoname
from frappe.utils import now_datetime


def before_insert_sample(doc, method=None):
	if not doc.tracking_number:
		doc.tracking_number = make_autoname("SMP-TRK-.YYYY.-.#####")


def validate_sample(doc, method=None):
	"""Hook backup — DocType.validate also syncs custody."""
	from instacertify.instacertify.doctype.ic_sample_tracking.ic_sample_tracking import (
		STATUS_TO_LOCATION,
	)

	if doc.status == "Sample Received" and not doc.sample_received_date:
		doc.sample_received_date = frappe.utils.today()
	if doc.status in STATUS_TO_LOCATION:
		doc.sample_location = STATUS_TO_LOCATION[doc.status]
	if not doc.qr_code and doc.tracking_number:
		_attach_sample_qr(doc)


def _attach_sample_qr(doc):
	from instacertify.utils.qr import generate_and_attach_qr, sample_qr_payload

	try:
		# Save first if new
		if doc.is_new() or not doc.tracking_number:
			return
		generate_and_attach_qr(
			"IC Sample Tracking",
			doc.name,
			"qr_code",
			sample_qr_payload(doc.tracking_number, doc.name),
			box_size=6,
			border=1,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Sample QR")


def validate_testing_request(doc, method=None):
	from instacertify.team.assignees import sync_assignees

	sync_assignees(
		doc,
		table_field="ic_assignees",
		primary_field="assigned_person",
		legacy_seed_field="assigned_person",
		default_user=doc.owner,
	)


@frappe.whitelist()
def regenerate_sample_qr(sample: str):
	"""Force-regenerate QR so it encodes the unique sample tracking number."""
	doc = frappe.get_doc("IC Sample Tracking", sample)
	if not doc.tracking_number:
		frappe.throw(_("Sample has no tracking number yet — save the sample first"))
	_attach_sample_qr(doc)
	doc.reload()
	return {"qr_code": doc.qr_code, "tracking_number": doc.tracking_number}


@frappe.whitelist()
def download_sample_sticker_50x25(sample: str):
	"""Download a 50×25 mm PNG sticker: QR + tracking number + www.instacertify.com."""
	doc = frappe.get_doc("IC Sample Tracking", sample)
	if not doc.tracking_number:
		frappe.throw(_("Sample has no tracking number yet — save the sample first"))
	from instacertify.utils.qr import render_sample_sticker_50x25_png, sample_qr_payload

	payload = sample_qr_payload(doc.tracking_number, doc.name)
	png = render_sample_sticker_50x25_png(doc.tracking_number, payload)
	fname = f"sample-sticker-50x25-{doc.tracking_number}.png".replace("/", "-")
	existing = frappe.db.get_value(
		"File",
		{
			"file_name": fname,
			"attached_to_doctype": "IC Sample Tracking",
			"attached_to_name": doc.name,
		},
		"name",
	)
	if existing:
		frappe.delete_doc("File", existing, ignore_permissions=True, force=True)
	file_doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": fname,
			"content": png,
			"is_private": 0,
			"attached_to_doctype": "IC Sample Tracking",
			"attached_to_name": doc.name,
		}
	)
	file_doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {
		"file_url": file_doc.file_url,
		"tracking_number": doc.tracking_number,
		"file_name": fname,
		"size_mm": "50x25",
	}


@frappe.whitelist()
def download_sample_sticker_8mm(sample: str):
	"""Back-compat alias — stickers are now 50×25 mm."""
	return download_sample_sticker_50x25(sample)


def on_update_testing_request(doc, method=None):
	if doc.has_value_changed("status"):
		_sync_sample_status(doc)
		_notify_status_change(doc)
	if doc.test_report and doc.status == "Report Available":
		doc.db_set("status", "Report Uploaded", update_modified=False)
	# When TR report is newly attached, push to linked samples + customer records
	if doc.test_report and doc.has_value_changed("test_report"):
		_propagate_report_to_samples(doc)
		try:
			from instacertify.crm.customer_data import ingest_sample_report

			# Reuse ingest with a lightweight shim (TR shares test_report field)
			ingest_sample_report(doc)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "ingest testing request report")


def _propagate_report_to_samples(doc):
	"""Copy test report onto linked Sample Tracking rows and stamp upload time."""
	meta = frappe.get_meta("IC Sample Tracking")
	if not meta.has_field("test_report"):
		return
	samples = frappe.get_all(
		"IC Sample Tracking",
		filters={"testing_request": doc.name},
		pluck="name",
	)
	stamp = now_datetime()
	for name in samples:
		values = {
			"test_report": doc.test_report,
			"status": "Report Uploaded",
		}
		if meta.has_field("report_uploaded_on"):
			values["report_uploaded_on"] = stamp
		if meta.has_field("report_uploaded_by"):
			values["report_uploaded_by"] = frappe.session.user
		frappe.db.set_value("IC Sample Tracking", name, values, update_modified=True)


def _sync_sample_status(doc):
	"""Mirror testing-request workflow onto linked samples without wiping custody."""
	from instacertify.instacertify.doctype.ic_sample_tracking.ic_sample_tracking import (
		STATUS_TO_LOCATION,
	)

	workflow_statuses = {
		"Testing in Progress",
		"Report Available",
		"Report Uploaded",
		"Report Shared with Customer",
		"Sample Dispatched to Laboratory",
		"Sample Received",
		"Sample Awaited",
	}
	if doc.status not in workflow_statuses and doc.status not in STATUS_TO_LOCATION:
		return

	samples = frappe.get_all(
		"IC Sample Tracking",
		filters={"testing_request": doc.name},
		fields=["name", "status", "sample_location"],
	)
	for row in samples:
		if row.status == "Discarded" or row.sample_location == "Discarded":
			continue
		values = {"status": doc.status}
		if doc.status in STATUS_TO_LOCATION:
			values["sample_location"] = STATUS_TO_LOCATION[doc.status]
		frappe.db.set_value("IC Sample Tracking", row.name, values)


@frappe.whitelist()
def set_sample_location(sample: str, location: str, discard_reason: str | None = None):
	"""Set physical custody location on a sample record."""
	from instacertify.instacertify.doctype.ic_sample_tracking.ic_sample_tracking import (
		LOCATION_TO_STATUS,
		SAMPLE_LOCATIONS,
	)

	if location not in SAMPLE_LOCATIONS:
		frappe.throw(_("Invalid sample location: {0}").format(location))
	doc = frappe.get_doc("IC Sample Tracking", sample)
	doc.sample_location = location
	doc.status = LOCATION_TO_STATUS.get(location, doc.status)
	if location == "Discarded" and discard_reason:
		doc.discard_reason = discard_reason
	doc.save(ignore_permissions=True)
	return doc.as_dict()


@frappe.whitelist()
def get_sample_custody_summary():
	"""Counts of samples by physical location for management views."""
	from instacertify.instacertify.doctype.ic_sample_tracking.ic_sample_tracking import (
		SAMPLE_LOCATIONS,
	)

	rows = frappe.db.sql(
		"""
		select ifnull(sample_location, '') as sample_location, count(*) as count
		from `tabIC Sample Tracking`
		group by ifnull(sample_location, '')
		""",
		as_dict=True,
	)
	counts = {loc: 0 for loc in SAMPLE_LOCATIONS}
	counts["Unset"] = 0
	for r in rows:
		loc = r.sample_location or "Unset"
		if loc in counts:
			counts[loc] = int(r.count or 0)
		else:
			counts["Unset"] = counts.get("Unset", 0) + int(r.count or 0)
	return counts


def _notify_status_change(doc):
	from instacertify.team.assignees import get_assignee_users

	users = get_assignee_users(doc, primary_field="assigned_person") + [
		doc.owner,
		"Administrator",
	]
	for user in set(filter(None, users)):
		if not frappe.db.exists("User", user):
			continue
		try:
			frappe.get_doc(
				{
					"doctype": "Notification Log",
					"subject": f"Testing Request {doc.name}: {doc.status}",
					"email_content": f"Status changed to {doc.status}",
					"document_type": "IC Testing Request",
					"document_name": doc.name,
					"for_user": user,
					"type": "Alert",
					"from_user": frappe.session.user,
				}
			).insert(ignore_permissions=True)
		except Exception:
			pass


@frappe.whitelist()
def share_report_with_customer(testing_request: str):
	from instacertify.crm.report_share import share_from_testing_request

	payload = share_from_testing_request(testing_request)
	return {
		"url": payload.get("share_url"),
		"access_code": payload.get("access_code"),
		"share_token": payload.get("share_token"),
		"name": payload.get("name"),
	}


@frappe.whitelist()
def upload_sample_report(sample: str, file_url: str):
	"""Upload / replace test report PDF on Sample Tracking when status is Report Available.

	Stamps date/time, sets status to Report Uploaded, syncs linked Testing Request,
	and writes the file into Customer records for download.
	"""
	from instacertify.utils.files import assert_internal_file

	if not sample:
		frappe.throw(_("Sample is required"))
	file_url = assert_internal_file(file_url, _("Test Report PDF"))
	_assert_pdf_report(file_url)

	doc = frappe.get_doc("IC Sample Tracking", sample)
	if doc.status not in (
		"Report Available",
		"Report Uploaded",
		"Report Shared with Customer",
		"Testing in Progress",
		"At Laboratory",
	):
		frappe.throw(
			_("Set status to Report Available before uploading the test report (current: {0})").format(
				doc.status
			)
		)

	doc.test_report = file_url
	doc.report_uploaded_on = now_datetime()
	doc.report_uploaded_by = frappe.session.user
	doc.status = "Report Uploaded"
	doc.save(ignore_permissions=True)

	# Mirror onto linked Testing Request so Share Report still works there
	if doc.testing_request and frappe.db.exists("IC Testing Request", doc.testing_request):
		tr = frappe.get_doc("IC Testing Request", doc.testing_request)
		tr.test_report = file_url
		if tr.status in (
			"Report Available",
			"Testing in Progress",
			"At Laboratory",
			"Sample Dispatched to Laboratory",
		):
			tr.status = "Report Uploaded"
		tr.save(ignore_permissions=True)

	# Customer records ingest runs from IC Sample Tracking.on_update
	doc.reload()
	return {
		"name": doc.name,
		"status": doc.status,
		"test_report": doc.test_report,
		"report_uploaded_on": str(doc.report_uploaded_on),
		"report_uploaded_by": doc.report_uploaded_by,
		"customer": doc.customer,
	}


@frappe.whitelist()
def delete_sample_report(sample: str):
	"""Remove the uploaded test report so a new PDF can be uploaded (status → Report Available)."""
	doc = frappe.get_doc("IC Sample Tracking", sample)
	if not doc.test_report:
		frappe.throw(_("No test report to delete"))

	old_url = doc.test_report
	doc.test_report = None
	doc.report_uploaded_on = None
	doc.report_uploaded_by = None
	if doc.status in ("Report Uploaded", "Report Shared with Customer"):
		doc.status = "Report Available"
	doc.save(ignore_permissions=True)

	if doc.testing_request and frappe.db.exists("IC Testing Request", doc.testing_request):
		tr = frappe.get_doc("IC Testing Request", doc.testing_request)
		if (tr.test_report or "") == old_url:
			tr.test_report = None
			if tr.status in ("Report Uploaded", "Report Shared with Customer"):
				tr.status = "Report Available"
			tr.save(ignore_permissions=True)

	doc.reload()
	return {
		"name": doc.name,
		"status": doc.status,
		"test_report": doc.test_report,
		"cleared": old_url,
	}


def _assert_pdf_report(file_url: str):
	"""Only accept PDF test reports."""
	name = (file_url or "").split("?")[0].rsplit("/", 1)[-1].lower()
	if name.endswith(".pdf"):
		return
	ftype = frappe.db.get_value("File", {"file_url": file_url}, "file_type") or ""
	if str(ftype).strip().upper() == "PDF":
		return
	frappe.throw(_("Test report must be a PDF file (.pdf)"))


@frappe.whitelist()
def mark_sample_report_available(sample: str):
	"""Mark sample as Report Available so ops can upload the lab report PDF."""
	doc = frappe.get_doc("IC Sample Tracking", sample)
	if doc.status == "Discarded":
		frappe.throw(_("Cannot mark a discarded sample as Report Available"))
	doc.status = "Report Available"
	doc.save(ignore_permissions=True)
	return doc.as_dict()


@frappe.whitelist()
def mark_sample_received(sample: str, quantity=None, condition=None, description=None):
	doc = frappe.get_doc("IC Sample Tracking", sample)
	doc.status = "Sample Received"
	doc.sample_location = "At Instacertify Office"
	doc.sample_received_date = frappe.utils.today()
	doc.received_by = frappe.session.user
	if quantity:
		doc.quantity = quantity
	if condition:
		doc.sample_condition = condition
	if description:
		doc.sample_description = description
	doc.save(ignore_permissions=True)
	if not doc.qr_code:
		_attach_sample_qr(doc)
	for user in set(filter(None, [doc.owner, "Administrator"])):
		try:
			frappe.get_doc(
				{
					"doctype": "Notification Log",
					"subject": f"Sample Received: {doc.tracking_number}",
					"email_content": f"Sample {doc.tracking_number} received at Instacertify office",
					"document_type": "IC Sample Tracking",
					"document_name": doc.name,
					"for_user": user,
					"type": "Alert",
					"from_user": frappe.session.user,
				}
			).insert(ignore_permissions=True)
		except Exception:
			pass
	return doc.as_dict()


@frappe.whitelist()
def create_testing_requests_from_quotation(quotation: str, project: str | None = None):
	"""Create IC Testing Request rows from Testing Quotation lab/test lines.

	Uses Laboratory Library assignments so ops can execute per lab scope.
	"""
	qt = frappe.get_doc("Quotation", quotation)
	if qt.quotation_to != "Customer" or not qt.party_name:
		frappe.throw(_("Quotation must be for a Customer"))

	if not project:
		project = frappe.db.get_value("Project", {"ic_quotation": qt.name}, "name")

	created = []
	existing = []
	for row in qt.get("ic_test_items") or []:
		if not row.test_name:
			continue
		filters = {
			"quotation": qt.name,
			"test_name": row.test_name,
			"customer": qt.party_name,
		}
		if row.laboratory:
			filters["laboratory"] = row.laboratory
		found = frappe.db.exists("IC Testing Request", filters)
		if found:
			existing.append(found)
			continue

		from instacertify.team.assignees import append_assignees_from_users, get_assignee_users

		title = f"{row.test_name} – {row.product_name or qt.party_name}"
		assignees = get_assignee_users(qt, primary_field="ic_primary_assignee")
		if not assignees:
			seed = qt.get("ic_assigned_salesperson") or qt.owner
			if seed:
				assignees = [seed]
		doc = frappe.get_doc(
			{
				"doctype": "IC Testing Request",
				"title": title[:140],
				"customer": qt.party_name,
				"project": project,
				"quotation": qt.name,
				"product": row.product_name or qt.ic_service_name or "Product",
				"test_name": row.test_name,
				"applicable_standard": row.applicable_standard,
				"number_of_samples": row.number_of_samples or 1,
				"laboratory": row.laboratory,
				"lab_test_scope": row.get("lab_test_scope"),
				"lab_scope_row": row.get("lab_scope_row"),
				"suggested_selling_price": row.get("suggested_selling_price")
				or row.get("per_unit_charges"),
				"testing_timeline": row.testing_timeline,
				"assigned_person": (assignees[0] if assignees else None),
				"status": "Testing Request Created",
				"priority": "Medium",
			}
		)
		append_assignees_from_users(doc, assignees)
		doc.insert(ignore_permissions=True)
		created.append(doc.name)

	return {"created": created, "existing": existing, "project": project}
