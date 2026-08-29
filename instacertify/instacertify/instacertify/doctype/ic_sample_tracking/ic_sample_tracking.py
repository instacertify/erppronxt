# Copyright (c) Instacertify
import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import now_datetime, today

# Physical custody locations used for list filters / dashboard cards
SAMPLE_LOCATIONS = (
	"With Customer",
	"In Transit to Office",
	"At Instacertify Office",
	"In Transit to Lab",
	"At Laboratory",
	"At Instacertify Storage",
	"Discarded",
)

STATUS_TO_LOCATION = {
	"Sample Awaited": "With Customer",
	"Sample Received": "At Instacertify Office",
	"In Transit to Office": "In Transit to Office",
	"At Instacertify Office": "At Instacertify Office",
	"In Transit to Lab": "In Transit to Lab",
	"Sample Dispatched to Laboratory": "In Transit to Lab",
	"At Laboratory": "At Laboratory",
	"At Instacertify Storage": "At Instacertify Storage",
	"Discarded": "Discarded",
}

LOCATION_TO_STATUS = {
	"With Customer": "Sample Awaited",
	"In Transit to Office": "In Transit to Office",
	"At Instacertify Office": "Sample Received",
	"In Transit to Lab": "In Transit to Lab",
	"At Laboratory": "At Laboratory",
	"At Instacertify Storage": "At Instacertify Storage",
	"Discarded": "Discarded",
}


class ICSampleTracking(Document):
	def before_insert(self):
		if not self.tracking_number:
			self.tracking_number = make_autoname("SMP-TRK-.YYYY.-.#####")

	def after_insert(self):
		self._ensure_qr()

	def validate(self):
		self._sync_custody()
		self._handle_receipt_and_discard()
		self._handle_report_upload()

	def on_update(self):
		if not self.qr_code:
			self._ensure_qr()
		# Push newly uploaded reports into customer records (idempotent attach)
		if self.test_report and self.has_value_changed("test_report"):
			try:
				from instacertify.crm.customer_data import ingest_sample_report

				ingest_sample_report(self)
			except Exception:
				frappe.log_error(frappe.get_traceback(), "ingest sample report")

	def _handle_report_upload(self):
		"""When a report file is attached, stamp date/time and move to Report Uploaded."""
		if not self.test_report:
			return
		prev = self.get_doc_before_save()
		prev_report = prev.test_report if prev else None
		if self.test_report != prev_report:
			self.report_uploaded_on = now_datetime()
			self.report_uploaded_by = frappe.session.user
			if self.status in ("Report Available", "Testing in Progress", "At Laboratory"):
				self.status = "Report Uploaded"
		elif not self.report_uploaded_on:
			self.report_uploaded_on = now_datetime()
			if not self.report_uploaded_by:
				self.report_uploaded_by = frappe.session.user

	def _sync_custody(self):
		prev = self.get_doc_before_save()
		prev_location = prev.sample_location if prev else None
		prev_status = prev.status if prev else None
		loc_changed = self.sample_location != prev_location
		status_changed = self.status != prev_status

		# Prefer explicit location edits; otherwise derive location from status
		if loc_changed and self.sample_location in LOCATION_TO_STATUS:
			self.status = LOCATION_TO_STATUS[self.sample_location]
		elif status_changed and self.status in STATUS_TO_LOCATION:
			self.sample_location = STATUS_TO_LOCATION[self.status]
		elif not self.sample_location and self.status in STATUS_TO_LOCATION:
			self.sample_location = STATUS_TO_LOCATION[self.status]

		if self.sample_location and self.sample_location != prev_location:
			self.location_updated_on = now_datetime()

	def _handle_receipt_and_discard(self):
		if self.status == "Sample Received" or self.sample_location == "At Instacertify Office":
			if not self.sample_received_date:
				self.sample_received_date = today()
			if not self.received_by:
				self.received_by = frappe.session.user

		if self.status == "Discarded" or self.sample_location == "Discarded":
			self.status = "Discarded"
			self.sample_location = "Discarded"
			if not self.discard_date:
				self.discard_date = today()
			if not self.discarded_by:
				self.discarded_by = frappe.session.user

		if self.status in ("In Transit to Lab", "Sample Dispatched to Laboratory") and not self.dispatch_date:
			self.dispatch_date = today()

	def _ensure_qr(self):
		from instacertify.utils.qr import generate_and_attach_qr, verification_url

		try:
			generate_and_attach_qr(
				"IC Sample Tracking",
				self.name,
				"qr_code",
				verification_url("IC Sample Tracking", self.name),
			)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Sample QR")
