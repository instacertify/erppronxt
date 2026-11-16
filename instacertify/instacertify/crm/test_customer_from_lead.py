# Copyright (c) Instacertify
"""Country / profile copy when a lead is converted to a customer."""

import unittest

from instacertify.utils.values import pick_nonempty


class TestCustomerFromLead(unittest.TestCase):
	def test_uses_lead_value_when_customer_empty(self):
		self.assertEqual(pick_nonempty("", "India"), "India")
		self.assertEqual(pick_nonempty(None, "United States"), "United States")
		self.assertEqual(pick_nonempty("  ", "India"), "India")

	def test_keeps_existing_customer_value(self):
		self.assertEqual(pick_nonempty("UAE", "India"), "UAE")
		self.assertEqual(pick_nonempty(" INR ", "USD"), "INR")

	def test_empty_when_both_missing(self):
		self.assertIsNone(pick_nonempty("", ""))
		self.assertIsNone(pick_nonempty(None, None))
