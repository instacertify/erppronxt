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
def download_sample_sticker_8mm(sample: str):
	"""Download a PNG sticker (8mm height) with QR + sample tracking number aligned for thermal print."""
	doc = frappe.get_doc("IC Sample Tracking", sample)
	if not doc.tracking_number:
		frappe.throw(_("Sample has no tracking number yet — save the sample first"))
	from instacertify.utils.qr import render_sample_sticker_8mm_png, sample_qr_payload

	payload = sample_qr_payload(doc.tracking_number, doc.name)
	png = render_sample_sticker_8mm_png(doc.tracking_number, payload)
	fname = f"sample-sticker-8mm-{doc.tracking_number}.png".replace("/", "-")
	# Persist as public file for print / thermal driver pickup
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
	}


def on_update_testing_request(doc, method=None):
	if doc.has_value_changed("status"):
		_sync_sample_status(doc)
		_notify_status_change(doc)
	if doc.test_report and doc.status == "Report Available":
		doc.db_set("status", "Report Uploaded", update_modified=False)


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
	users = [doc.assigned_person, doc.owner, "Administrator"]
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
	doc = frappe.get_doc("IC Testing Request", testing_request)
	if not doc.test_report:
		frappe.throw("Please upload the test report first")
	if not doc.share_token:
		doc.share_token = secrets.token_urlsafe(24)
	doc.report_shared_on = now_datetime()
	doc.status = "Report Shared with Customer"
	doc.save(ignore_permissions=True)
	url = frappe.utils.get_url(f"/ic-report/{doc.share_token}")
	return {"url": url}


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

		title = f"{row.test_name} – {row.product_name or qt.party_name}"
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
				"assigned_person": qt.get("ic_assigned_salesperson") or qt.owner,
				"status": "Testing Request Created",
				"priority": "Medium",
			}
		)
		doc.insert(ignore_permissions=True)
		created.append(doc.name)

	return {"created": created, "existing": existing, "project": project}
