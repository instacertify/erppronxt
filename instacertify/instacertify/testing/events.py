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
	if doc.status == "Sample Received" and not doc.sample_received_date:
		doc.sample_received_date = frappe.utils.today()
	if not doc.qr_code and doc.tracking_number:
		_attach_sample_qr(doc)


def _attach_sample_qr(doc):
	from instacertify.utils.qr import generate_and_attach_qr, verification_url

	try:
		# Save first if new
		if doc.is_new():
			return
		generate_and_attach_qr(
			"IC Sample Tracking",
			doc.name,
			"qr_code",
			verification_url("IC Sample Tracking", doc.name),
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Sample QR")


def on_update_testing_request(doc, method=None):
	if doc.has_value_changed("status"):
		_sync_sample_status(doc)
		_notify_status_change(doc)
	if doc.test_report and doc.status == "Report Available":
		doc.db_set("status", "Report Uploaded", update_modified=False)


def _sync_sample_status(doc):
	samples = frappe.get_all(
		"IC Sample Tracking", filters={"testing_request": doc.name}, pluck="name"
	)
	for name in samples:
		frappe.db.set_value("IC Sample Tracking", name, "status", doc.status)


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
	# notify
	for user in set(filter(None, [doc.owner, "Administrator"])):
		try:
			frappe.get_doc(
				{
					"doctype": "Notification Log",
					"subject": f"Sample Received: {doc.tracking_number}",
					"email_content": f"Sample {doc.tracking_number} received",
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
