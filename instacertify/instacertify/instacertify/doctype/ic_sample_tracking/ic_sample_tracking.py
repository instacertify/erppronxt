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
	"At Instacertify Warehouse",
	"At Instacertify Storage",  # legacy alias → warehouse
	"In Transit to Client",
	"Returned to Client",
	"Discarded",
)

# Locations that must not be overwritten when TR only advances report workflow
PRESERVE_LOCATIONS_ON_REPORT = frozenset(
	{
		"At Laboratory",
		"At Instacertify Warehouse",
		"At Instacertify Storage",
		"In Transit to Client",
		"Returned to Client",
		"Discarded",
	}
)

STATUS_TO_LOCATION = {
	"Sample Awaited": "With Customer",
	"Sample Received": "At Instacertify Office",
	"In Transit to Office": "In Transit to Office",
	"At Instacertify Office": "At Instacertify Office",
	"In Transit to Lab": "In Transit to Lab",
	"Sample Dispatched to Laboratory": "In Transit to Lab",
	"At Laboratory": "At Laboratory",
	"Testing in Progress": "At Laboratory",
	"At Instacertify Warehouse": "At Instacertify Warehouse",
	"At Instacertify Storage": "At Instacertify Warehouse",
	"In Transit to Client": "In Transit to Client",
	"Returned to Client": "Returned to Client",
	"Dispatched to Client": "In Transit to Client",
	"Discarded": "Discarded",
}

LOCATION_TO_STATUS = {
	"With Customer": "Sample Awaited",
	"In Transit to Office": "In Transit to Office",
	"At Instacertify Office": "Sample Received",
	"In Transit to Lab": "In Transit to Lab",
	"At Laboratory": "At Laboratory",
	"At Instacertify Warehouse": "At Instacertify Warehouse",
	"At Instacertify Storage": "At Instacertify Warehouse",
	"In Transit to Client": "In Transit to Client",
	"Returned to Client": "Returned to Client",
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

	def _handle_report_upload(self):
		"""When a report file is attached/replaced/cleared, stamp or reset metadata."""
		prev = self.get_doc_before_save()
		prev_report = (prev.test_report if prev else None) or ""
		curr_report = self.test_report or ""

		# Cleared — allow delete / modify cycle
		if prev_report and not curr_report:
			self.report_uploaded_on = None
			self.report_uploaded_by = None
			if self.status in ("Report Uploaded", "Report Shared with Customer"):
				self.status = "Report Available"
			return

		if not curr_report:
			return

		if curr_report != prev_report:
			self.report_uploaded_on = now_datetime()
			self.report_uploaded_by = frappe.session.user
			if self.status in (
				"Report Available",
				"Testing in Progress",
				"At Laboratory",
				"Sample Dispatched to Laboratory",
			):
				self.status = "Report Uploaded"
		elif not self.report_uploaded_on:
			self.report_uploaded_on = now_datetime()
			if not self.report_uploaded_by:
				self.report_uploaded_by = frappe.session.user

	def on_update(self):
		if not self.qr_code:
			self._ensure_qr()
		# Push newly uploaded / replaced reports into customer records
		if self.has_value_changed("test_report"):
			try:
				from instacertify.crm.customer_data import ingest_sample_report, clear_sample_report

				if self.test_report:
					ingest_sample_report(self)
				else:
					clear_sample_report(self)
			except Exception:
				frappe.log_error(frappe.get_traceback(), "ingest sample report")

	def _sync_custody(self):
		prev = self.get_doc_before_save()
		prev_location = prev.sample_location if prev else None
		prev_status = prev.status if prev else None
		loc_changed = self.sample_location != prev_location
		status_changed = self.status != prev_status

		if self.sample_location == "At Instacertify Storage":
			self.sample_location = "At Instacertify Warehouse"

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
		if self.status in ("In Transit to Client", "Dispatched to Client", "Returned to Client"):
			# Returned / outbound to client — keep dispatch_date for lab send; no extra stamp required
			pass

	def _ensure_qr(self):
		from instacertify.utils.qr import generate_and_attach_qr, sample_qr_payload

		if not self.tracking_number:
			return
		try:
			generate_and_attach_qr(
				"IC Sample Tracking",
				self.name,
				"qr_code",
				sample_qr_payload(self.tracking_number, self.name),
				box_size=6,
				border=1,
			)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Sample QR")

