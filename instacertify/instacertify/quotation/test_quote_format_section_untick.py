# Copyright (c) Instacertify
"""Quote Format unchecked sections stay hidden on quote form flags + Print/PDF."""

import frappe
from frappe.tests.utils import FrappeTestCase

from instacertify.quotation.print_sections import (
	quote_section_on,
	quote_show_flags,
	template_show_defaults,
)


def _render(doc, print_format_name: str) -> str:
	pf = frappe.get_doc("Print Format", print_format_name)
	return frappe.render_template(pf.html, {"doc": doc})


def _dummy_quote(**flags):
	doc = frappe._dict(
		name="TEST-FORMAT-UNTICK",
		doctype="Quotation",
		ic_quotation_type="Consulting",
		ic_validity_text="VALIDITY_MARKER_UNIQUE",
		ic_payment_terms="PAYMENT_TERMS_MARKER_UNIQUE",
		ic_timeline_details="TIMELINE_DETAILS_MARKER_UNIQUE",
		ic_estimated_timeline="TIMELINE_MARKER_UNIQUE",
		ic_sample_required="SAMPLE_BODY",
		currency="INR",
		transaction_date=frappe.utils.today(),
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


class TestTemplateShowDefaults(FrappeTestCase):
	def test_unchecked_template_maps_to_zero(self):
		tmpl = frappe._dict(
			show_validity=0,
			show_payment_terms=0,
			show_timelines=0,
			show_about=1,
		)
		flags = template_show_defaults(tmpl)
		self.assertEqual(flags["ic_show_validity"], 0)
		self.assertEqual(flags["ic_show_payment_terms"], 0)
		self.assertEqual(flags["ic_show_timelines"], 0)
		self.assertEqual(flags["ic_show_about"], 1)

	def test_payload_includes_unchecked_zeros(self):
		# Use an in-memory template-like object via get_quotation_template_payload path
		from instacertify.quotation.events import _template_field_map

		tmpl = frappe._dict(
			name="X",
			template_name="X",
			display_name="X",
			quotation_type="Consulting",
			show_validity=0,
			show_payment_terms=0,
			show_timelines=0,
			show_about=1,
			show_commercials=1,
			show_banking=1,
			show_terms=1,
			show_sample_required=1,
			show_deliverables=1,
			show_cancellation=1,
			show_force_majeure=1,
			show_confidentiality=1,
			show_sample_handling=1,
			show_applicable_standards=1,
			show_process=1,
			show_documents_required=1,
			get=lambda k, d=None: tmpl[k] if k in tmpl else d,
		)
		# frappe._dict already has .get — rebuild properly
		tmpl = frappe._dict(
			{
				"name": "X",
				"template_name": "X",
				"display_name": "X",
				"quotation_type": "Consulting",
				"show_validity": 0,
				"show_payment_terms": 0,
				"show_timelines": 0,
				"show_about": 1,
				"show_commercials": 1,
				"show_banking": 1,
				"show_terms": 1,
				"show_sample_required": 1,
				"show_deliverables": 1,
				"show_cancellation": 1,
				"show_force_majeure": 1,
				"show_confidentiality": 1,
				"show_sample_handling": 1,
				"show_applicable_standards": 1,
				"show_process": 1,
				"show_documents_required": 1,
			}
		)
		fields = _template_field_map(tmpl)
		self.assertEqual(fields.get("ic_show_validity"), 0)
		self.assertEqual(fields.get("ic_show_payment_terms"), 0)
		self.assertEqual(fields.get("ic_show_timelines"), 0)

	def test_print_hides_sections_from_format_flags(self):
		doc = _dummy_quote(
			ic_show_validity=0,
			ic_show_payment_terms=0,
			ic_show_timelines=0,
		)
		html = _render(doc, "Instacertify Consulting Quotation")
		self.assertNotIn("VALIDITY_MARKER_UNIQUE", html)
		self.assertNotIn("PAYMENT_TERMS_MARKER_UNIQUE", html)
		self.assertNotIn("TIMELINE_DETAILS_MARKER_UNIQUE", html)

	def test_quote_show_flags_helper(self):
		doc = _dummy_quote(ic_show_validity=0, ic_show_payment_terms=1)
		flags = quote_show_flags(doc)
		self.assertEqual(flags["ic_show_validity"], 0)
		self.assertEqual(flags["ic_show_payment_terms"], 1)
		self.assertFalse(quote_section_on(doc, "ic_show_validity"))
		self.assertTrue(quote_section_on(doc, "ic_show_payment_terms"))
