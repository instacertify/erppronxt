# Copyright (c) Instacertify
import frappe
from frappe import _
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
		self._sync_linked_tests_from_primary()
		self._enforce_same_lab_multi_test()

	def _sync_linked_tests_from_primary(self):
		"""Keep primary Testing Request mirrored in the linked_tests table."""
		if not self.meta.has_field("linked_tests"):
			return
		if not self.testing_request:
			return
		existing = {row.testing_request for row in (self.get("linked_tests") or []) if row.testing_request}
		if self.testing_request in existing:
			return
		tr = frappe.db.get_value(
			"IC Testing Request",
			self.testing_request,
			["test_name", "applicable_standard", "laboratory"],
			as_dict=True,
		) or {}
		self.append(
			"linked_tests",
			{
				"testing_request": self.testing_request,
				"test_name": tr.get("test_name"),
				"applicable_standard": tr.get("applicable_standard"),
				"laboratory": tr.get("laboratory"),
			},
		)

	def _enforce_same_lab_multi_test(self):
		"""One physical sample may cover multiple tests only at the same laboratory."""
		labs = set()
		if self.laboratory:
			labs.add(self.laboratory)

		# Primary TR lab
		if self.testing_request and frappe.db.exists("IC Testing Request", self.testing_request):
			tr_lab = frappe.db.get_value("IC Testing Request", self.testing_request, "laboratory")
			if tr_lab:
				labs.add(tr_lab)
				if self.laboratory and tr_lab != self.laboratory:
					frappe.throw(
						_(
							"Sample {0} is assigned to laboratory {1}, but primary Testing Request {2} uses {3}. "
							"One sample cannot be used for tests at different labs."
						).format(
							self.tracking_number or self.name,
							frappe.bold(self.laboratory),
							frappe.bold(self.testing_request),
							frappe.bold(tr_lab),
						),
						title=_("Same-lab only"),
					)

		seen_trs = set()
		for row in self.get("linked_tests") or []:
			tr_name = row.testing_request
			if not tr_name:
				continue
			if tr_name in seen_trs:
				frappe.throw(_("Testing Request {0} is linked more than once on this sample.").format(tr_name))
			seen_trs.add(tr_name)
			tr_lab = row.laboratory or frappe.db.get_value("IC Testing Request", tr_name, "laboratory")
			if tr_lab:
				row.laboratory = tr_lab
				labs.add(tr_lab)
			# Fill display fields
			if not row.test_name or not row.applicable_standard or not row.laboratory:
				meta = frappe.db.get_value(
					"IC Testing Request",
					tr_name,
					["test_name", "applicable_standard", "laboratory"],
					as_dict=True,
				) or {}
				row.test_name = row.test_name or meta.get("test_name")
				row.applicable_standard = row.applicable_standard or meta.get("applicable_standard")
				row.laboratory = row.laboratory or meta.get("laboratory")
				if row.laboratory:
					labs.add(row.laboratory)

		if len(labs) > 1:
			lab_labels = []
			for lab in sorted(labs):
				title = frappe.db.get_value("IC Laboratory", lab, "laboratory_name") or lab
				lab_labels.append(str(title))
			frappe.throw(
				_(
					"Sample {0} is linked to tests at more than one laboratory ({1}). "
					"One sample can be used for multiple tests only at the same lab — not across different labs."
				).format(self.tracking_number or self.name, ", ".join(lab_labels)),
				title=_("Same-lab only"),
			)

		# If sample has no lab yet but linked tests agree, adopt it
		if not self.laboratory and len(labs) == 1:
			self.laboratory = next(iter(labs))

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
