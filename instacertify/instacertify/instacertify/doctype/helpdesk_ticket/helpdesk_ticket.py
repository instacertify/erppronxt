# Copyright (c) Instacertify
"""Customer helpdesk tickets — complaints, queries, billing, certification issues."""

from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class HelpdeskTicket(Document):
	def before_insert(self):
		if not self.opened_on:
			self.opened_on = now_datetime()
		if not self.raised_by:
			self.raised_by = frappe.session.user
		self._fill_from_links()

	def validate(self):
		self._fill_from_links()
		if self.status in ("Resolved", "Closed") and not self.resolved_on:
			self.resolved_on = now_datetime()
		if self.status in ("Open", "In Progress", "Waiting on Customer"):
			self.resolved_on = None

	def _fill_from_links(self):
		"""Pull customer / contact defaults from linked CRM docs."""
		if self.project and not self.customer:
			self.customer = frappe.db.get_value("Project", self.project, "customer")
		if self.quotation and not self.customer:
			party = frappe.db.get_value(
				"Quotation", self.quotation, ["quotation_to", "party_name"], as_dict=True
			)
			if party and party.quotation_to == "Customer":
				self.customer = party.party_name
			elif party and party.quotation_to == "Lead" and not self.lead:
				self.lead = party.party_name
		if self.opportunity and not self.customer and not self.lead:
			opp = frappe.db.get_value(
				"Opportunity",
				self.opportunity,
				["opportunity_from", "party_name"],
				as_dict=True,
			)
			if opp:
				if opp.opportunity_from == "Customer":
					self.customer = opp.party_name
				elif opp.opportunity_from == "Lead":
					self.lead = opp.party_name
		if self.lead and not self.contact_person:
			lead = frappe.db.get_value(
				"Lead",
				self.lead,
				["lead_name", "company_name", "email_id", "mobile_no", "phone"],
				as_dict=True,
			)
			if lead:
				self.contact_person = self.contact_person or lead.lead_name or lead.company_name
				self.contact_email = self.contact_email or lead.email_id
				self.contact_phone = self.contact_phone or lead.mobile_no or lead.phone
		if self.customer and not self.contact_person:
			self.contact_person = frappe.db.get_value("Customer", self.customer, "customer_name")
