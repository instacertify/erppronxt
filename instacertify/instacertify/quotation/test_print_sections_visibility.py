# Copyright (c) Instacertify
"""Tests: untick Validity / Payment Terms / Estimated Timelines hides form+print."""

import frappe
from frappe.tests.utils import FrappeTestCase

from instacertify.quotation.print_sections import quote_section_on, quote_section_order


def _render_quote_print(doc, print_format_name: str) -> str:
	"""Render Instacertify quote print HTML without saving (avoids ERPNext totals validate)."""
	pf = frappe.get_doc("Print Format", print_format_name)
	return frappe.render_template(pf.html, {"doc": doc})


def _dummy_quote(qtype="Consulting", **flags):
	doc = frappe._dict(
		name="TEST-IC-SECTION-QTN",
		doctype="Quotation",
		quotation_to="Customer",
		party_name="Test Customer",
		customer_name="Test Customer",
		transaction_date=frappe.utils.today(),
		ic_quotation_type=qtype,
		ic_subject="Test Quote Sections",
		ic_validity_text="VALIDITY_MARKER_UNIQUE",
		ic_validity_days=45,
		ic_payment_terms="PAYMENT_TERMS_MARKER_UNIQUE",
		ic_estimated_timeline="TIMELINE_MARKER_UNIQUE",
		ic_timeline_details="TIMELINE_DETAILS_MARKER_UNIQUE",
		ic_sample_required="SAMPLE_BODY",
		currency="INR",
	)
	for f in (
		"ic_show_validity",
		"ic_show_payment_terms",
		"ic_show_timelines",
		"ic_show_about",
		"ic_show_commercials",
		"ic_show_banking",
		"ic_show_terms",
		"ic_show_sample_required",
		"ic_show_deliverables",
		"ic_show_cancellation",
		"ic_show_force_majeure",
		"ic_show_confidentiality",
		"ic_show_sample_handling",
		"ic_show_applicable_standards",
		"ic_show_process",
		"ic_show_documents_required",
	):
		doc[f] = 1
	doc.update(flags)
	return doc


class TestQuoteSectionUntick(FrappeTestCase):
	def test_quote_section_on_defaults_true(self):
		doc = frappe._dict()
		self.assertTrue(quote_section_on(doc, "ic_show_validity"))
		self.assertTrue(quote_section_on(doc, "ic_show_payment_terms"))
		self.assertTrue(quote_section_on(doc, "ic_show_timelines"))

	def test_quote_section_on_explicit_off(self):
		doc = frappe._dict(
			ic_show_validity=0,
			ic_show_payment_terms="0",
			ic_show_timelines=False,
		)
		self.assertFalse(quote_section_on(doc, "ic_show_validity"))
		self.assertFalse(quote_section_on(doc, "ic_show_payment_terms"))
		self.assertFalse(quote_section_on(doc, "ic_show_timelines"))

	def test_quote_section_on_explicit_on(self):
		doc = frappe._dict(ic_show_validity=1, ic_show_payment_terms=1, ic_show_timelines=1)
		self.assertTrue(quote_section_on(doc, "ic_show_validity"))
		self.assertTrue(quote_section_on(doc, "ic_show_payment_terms"))
		self.assertTrue(quote_section_on(doc, "ic_show_timelines"))

	def test_section_order_includes_target_keys(self):
		for qtype in ("Testing", "Consulting", None):
			order = quote_section_order(frappe._dict(ic_quotation_type=qtype or "Consulting"))
			self.assertIn("validity", order)
			self.assertIn("payment_terms", order)
			self.assertIn("timelines", order)


class TestQuotePrintHideSections(FrappeTestCase):
	def test_consulting_hide_validity_payment_timelines(self):
		doc = _dummy_quote(
			"Consulting",
			ic_show_validity=0,
			ic_show_payment_terms=0,
			ic_show_timelines=0,
		)
		html = _render_quote_print(doc, "Instacertify Consulting Quotation")
		self.assertNotIn("VALIDITY_MARKER_UNIQUE", html)
		self.assertNotIn("PAYMENT_TERMS_MARKER_UNIQUE", html)
		self.assertNotIn("TIMELINE_MARKER_UNIQUE", html)
		self.assertNotIn("TIMELINE_DETAILS_MARKER_UNIQUE", html)

	def test_consulting_show_when_checked(self):
		doc = _dummy_quote(
			"Consulting",
			ic_show_validity=1,
			ic_show_payment_terms=1,
			ic_show_timelines=1,
		)
		html = _render_quote_print(doc, "Instacertify Consulting Quotation")
		self.assertIn("VALIDITY_MARKER_UNIQUE", html)
		self.assertIn("PAYMENT_TERMS_MARKER_UNIQUE", html)
		self.assertIn("TIMELINE_DETAILS_MARKER_UNIQUE", html)

	def test_testing_hide_validity_payment_timelines(self):
		doc = _dummy_quote(
			"Testing",
			ic_show_validity=0,
			ic_show_payment_terms=0,
			ic_show_timelines=0,
		)
		html = _render_quote_print(doc, "Instacertify Testing Quotation")
		self.assertNotIn("VALIDITY_MARKER_UNIQUE", html)
		self.assertNotIn("PAYMENT_TERMS_MARKER_UNIQUE", html)
		self.assertNotIn("TIMELINE_MARKER_UNIQUE", html)

	def test_testing_show_when_checked(self):
		doc = _dummy_quote(
			"Testing",
			ic_show_validity=1,
			ic_show_payment_terms=1,
			ic_show_timelines=1,
		)
		html = _render_quote_print(doc, "Instacertify Testing Quotation")
		self.assertIn("VALIDITY_MARKER_UNIQUE", html)
		self.assertIn("PAYMENT_TERMS_MARKER_UNIQUE", html)
		self.assertIn("TIMELINE_MARKER_UNIQUE", html)

	def test_no_repeated_payment_heading_inside_body(self):
		doc = _dummy_quote("Consulting", ic_show_payment_terms=1)
		html = _render_quote_print(doc, "Instacertify Consulting Quotation")
		self.assertNotIn("Payment Terms &amp; Conditions", html)
		self.assertNotIn("Payment Terms & Conditions", html)

	def test_no_repeated_sample_heading_inside_body(self):
		doc = _dummy_quote("Consulting", ic_show_sample_required=1, ic_sample_required="SAMPLE_BODY")
		html = _render_quote_print(doc, "Instacertify Consulting Quotation")
		self.assertIn("SAMPLE_BODY", html)
		self.assertEqual(html.count('class="cq-h">Sample Required'), 0)


class TestSoftRefreshHelpersPresent(FrappeTestCase):
	def test_instacertify_js_has_soft_refresh(self):
		path = frappe.get_app_path("instacertify", "public", "js", "instacertify.js")
		with open(path, encoding="utf-8") as f:
			js = f.read()
		self.assertIn("refresh_grid_row_soft", js)
		self.assertIn("refresh_grid_soft", js)
		self.assertIn("needsDecoration", js)
		self.assertIn("applyIncludeLive", js)
		self.assertIn("ic-banner-sig", js)
		self.assertIn("if (needsDecoration()) schedule()", js)
