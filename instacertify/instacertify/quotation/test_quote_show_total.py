# Copyright (c) Instacertify
"""Show Total / Final Costing can be unchecked when lines are optional choices."""

import frappe
from frappe.tests.utils import FrappeTestCase

from instacertify.quotation.print_sections import (
	quote_section_on,
	quote_totals_on,
	template_show_defaults,
)


def _render(doc, print_format_name: str) -> str:
	pf = frappe.get_doc("Print Format", print_format_name)
	return frappe.render_template(pf.html, {"doc": doc})


def _cost_row(**kwargs):
	row = frappe._dict(
		particulars="Optional Package A",
		description="Customer may choose",
		qty=1,
		unit_price=1000,
		amount=1000,
		currency="INR",
		exclude_from_total=0,
	)
	row.update(kwargs)
	return row


def _dummy_quote(**flags):
	doc = frappe._dict(
		name="TEST-SHOW-TOTAL",
		doctype="Quotation",
		ic_quotation_type="Consulting",
		currency="INR",
		transaction_date=frappe.utils.today(),
		ic_cost_items=[_cost_row()],
		ic_test_items=[],
		ic_show_commercials=1,
		ic_show_total=1,
	)
	doc.update(flags)
	return doc


class TestQuoteShowTotal(FrappeTestCase):
	def test_quote_totals_on_defaults_true(self):
		self.assertTrue(quote_totals_on(frappe._dict()))
		self.assertTrue(quote_section_on(frappe._dict(), "ic_show_total"))

	def test_quote_totals_on_explicit_off(self):
		self.assertFalse(quote_totals_on(frappe._dict(ic_show_total=0)))

	def test_template_show_total_maps(self):
		flags = template_show_defaults(frappe._dict(show_total=0, show_commercials=1))
		self.assertEqual(flags["ic_show_total"], 0)
		self.assertEqual(flags["ic_show_commercials"], 1)

	def test_consulting_print_hides_final_costing_when_total_off(self):
		on = _render(_dummy_quote(ic_show_total=1), "Instacertify Consulting Quotation")
		off = _render(_dummy_quote(ic_show_total=0), "Instacertify Consulting Quotation")
		self.assertIn("Final Costing", on)
		self.assertIn("Commercials Total", on)
		self.assertIn("Optional Package A", off)
		self.assertNotIn("Final Costing", off)
		self.assertNotIn("Commercials Total", off)

	def test_testing_print_hides_grand_total_when_total_off(self):
		doc = _dummy_quote(
			ic_quotation_type="Testing",
			ic_show_total=0,
			ic_test_items=[
				frappe._dict(
					test_name="EMI Test",
					applicable_standard="CISPR",
					description="",
					number_of_samples=1,
					suggested_selling_price=500,
					testing_charges=500,
					currency="INR",
				)
			],
		)
		html = _render(doc, "Instacertify Testing Quotation")
		self.assertIn("EMI Test", html)
		self.assertNotIn("Final Costing", html)
		self.assertNotIn("Testing Total", html)

	def test_do_not_sum_hides_final_costing(self):
		"""Any Do Not Sum line removes Final Costing even if Show Total is on."""
		doc = _dummy_quote(
			ic_show_total=1,
			ic_cost_items=[_cost_row(exclude_from_total=1, particulars="Optional A")],
		)
		self.assertFalse(quote_totals_on(doc))
		html = _render(doc, "Instacertify Consulting Quotation")
		self.assertIn("Optional A", html)
		self.assertNotIn("Final Costing", html)
		self.assertNotIn("Commercials Total", html)

	def test_template_cost_rows_copy_exclude_from_total(self):
		from instacertify.quotation.events import _template_cost_rows

		tmpl = frappe._dict(
			cost_items=[
				frappe._dict(
					cost_component="Optional Pack",
					particulars="Optional Pack",
					description="",
					amount=1000,
					qty=1,
					payment_destination="Payable to Instacertify",
					revenue_treatment="Counted Revenue",
					is_passthrough=0,
					exclude_from_total=1,
					line_label="A",
					currency="INR",
				)
			]
		)
		rows = _template_cost_rows(tmpl)
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0]["exclude_from_total"], 1)
		self.assertEqual(rows[0]["line_label"], "A")

	def test_js_lists_show_total_field(self):
		from pathlib import Path

		js = Path(frappe.get_app_path("instacertify", "public", "js", "instacertify.js")).read_text(
			encoding="utf-8"
		)
		self.assertIn('"ic_show_total"', js)
		self.assertIn("ic-show-total-opt", js)
		self.assertIn("sync_show_total_from_do_not_sum", js)

		events = Path(frappe.get_app_path("instacertify", "quotation", "events.py")).read_text(
			encoding="utf-8"
		)
		self.assertIn("exclude_from_total", events)
		self.assertIn('row.get("exclude_from_total")', events)
