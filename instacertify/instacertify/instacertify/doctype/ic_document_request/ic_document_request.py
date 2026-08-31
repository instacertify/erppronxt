# Copyright (c) Instacertify
import frappe
from frappe import _
from frappe.model.document import Document


class ICDocumentRequest(Document):
	def validate(self):
		if not self.customer:
			frappe.throw(_("Customer is mandatory for a Documents Collection Sheet"))
		if self.share_token and self.meta.has_field("share_url") and not self.share_url:
			self.share_url = frappe.utils.get_url(f"/ic-documents/{self.share_token}")
		# Keep Customer Data Fields section on when fill rows exist
		if self.meta.has_field("include_data_fields") and (self.get("data_fields") or []):
			self.include_data_fields = 1

	def on_update(self):
		# Keep Customer Data Drive in sync when staff save filled data / uploads on desk.
		if not self.customer:
			return
		if self.flags.get("skip_customer_ingest"):
			return
		try:
			from instacertify.crm.customer_data import ingest_data_collection, ingest_document_upload

			has_data = any(
				[
					self.get("company_legal_name"),
					self.get("gstin"),
					self.get("company_address"),
					self.get("data_contact_person"),
					self.get("data_contact_phone"),
					self.get("data_contact_email"),
					self.get("product_name"),
					self.get("product_model"),
					self.get("product_brand"),
					self.get("data_collection_remarks"),
					any((r.get("field_value") or "").strip() for r in (self.get("data_fields") or [])),
				]
			)
			has_uploads = any(r.get("uploaded_file") for r in (self.get("items") or []))
			if not has_data and not has_uploads:
				return
			if has_data:
				ingest_data_collection(self)
			# Only (re)attach uploads that changed on this save when possible
			before = self.get_doc_before_save()
			before_files = {}
			if before:
				before_files = {r.name: r.get("uploaded_file") for r in (before.get("items") or []) if r.name}
			for row in self.get("items") or []:
				url = row.get("uploaded_file")
				if not url:
					continue
				if before_files.get(row.name) == url:
					continue
				ingest_document_upload(self, row)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "IC Document Request customer ingest")
