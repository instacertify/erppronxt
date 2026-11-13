# Copyright (c) Instacertify
"""Customer share text cleanup does not rewrite stored quotations."""

from frappe.tests.utils import FrappeTestCase

from instacertify.quotation.print_sections import clean_customer_text


class TestCleanCustomerText(FrappeTestCase):
	def test_splits_glued_payment_terms_and_drops_heading(self):
		raw = (
			"Payment Terms – MSDS / SDS Preparation100% Advance Payment against Proforma Invoice (PI)."
			"18% GST applicable extra as per Government taxation norms."
			"MSDS / SDS preparation process will commence upon receipt of payment."
			"&nbsp;&nbsp;&nbsp;"
		)
		text = clean_customer_text(raw, "Payment Terms")
		self.assertFalse(text.lower().startswith("payment terms"))
		self.assertIn("MSDS / SDS Preparation", text)
		self.assertNotIn("&nbsp;", text)
		self.assertIn("100% Advance Payment", text)
		self.assertIn("18% GST applicable", text)
		self.assertIn("MSDS / SDS preparation process", text)
		self.assertIn("\n", text)
		self.assertNotIn("norms.MSDS", text)

	def test_html_paragraphs_become_lines(self):
		raw = "<p>Payment Terms</p><p>100% advance.</p><p>Work starts after payment.</p>"
		text = clean_customer_text(raw, "Payment Terms")
		self.assertNotIn("<p>", text)
		self.assertIn("100% advance.", text)
		self.assertIn("Work starts after payment.", text)
		self.assertFalse(text.lower().startswith("payment terms"))
