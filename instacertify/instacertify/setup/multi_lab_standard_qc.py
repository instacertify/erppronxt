# Copyright (c) Instacertify
"""QC: same standard offered by multiple labs at different prices."""

from __future__ import annotations

import frappe
from frappe.utils import flt

from instacertify.laboratory.api import get_labs_for_standard, get_standard_options


def run():
	"""Ensure multi-lab pricing lookup works for at least one shared standard."""
	standards = get_standard_options()
	shared = None
	offers = []
	for s in standards:
		offers = get_labs_for_standard(s["value"])
		labs = {o["laboratory"] for o in offers}
		if len(labs) >= 2:
			shared = s["value"]
			break

	# Seed a shared standard across two labs when missing (dev / demo sites)
	if not shared:
		labs = frappe.get_all(
			"IC Laboratory",
			filters={"status": "Active"},
			pluck="name",
			limit=2,
		)
		if len(labs) < 2:
			# Create two demo labs
			for title, city, price in (
				("Demo Lab Alpha", "Delhi", 12000),
				("Demo Lab Beta", "Mumbai", 9500),
			):
				name = frappe.db.get_value("IC Laboratory", {"laboratory_name": title}, "name")
				if not name:
					doc = frappe.get_doc(
						{
							"doctype": "IC Laboratory",
							"laboratory_name": title,
							"status": "Active",
							"location": city,
							"city": city,
							"test_scopes": [
								{
									"test_name": "Safety Test",
									"applicable_standard": "IEC 62368-1",
									"selling_price": price,
									"purchase_price": price * 0.7,
									"currency": "INR",
									"is_active": 1,
								}
							],
						}
					)
					doc.insert(ignore_permissions=True)
				else:
					doc = frappe.get_doc("IC Laboratory", name)
					has = any(
						(r.applicable_standard or "").strip().casefold() == "iec 62368-1"
						for r in (doc.test_scopes or [])
					)
					if not has:
						doc.append(
							"test_scopes",
							{
								"test_name": "Safety Test",
								"applicable_standard": "IEC 62368-1",
								"selling_price": price,
								"purchase_price": price * 0.7,
								"currency": "INR",
								"is_active": 1,
							},
						)
						doc.save(ignore_permissions=True)
				labs = frappe.get_all(
					"IC Laboratory",
					filters={"status": "Active", "laboratory_name": ["in", ["Demo Lab Alpha", "Demo Lab Beta"]]},
					pluck="name",
				)
			frappe.db.commit()
			shared = "IEC 62368-1"
			offers = get_labs_for_standard(shared)
		else:
			# Attach shared standard to existing two labs at different prices
			shared = "IEC 62368-1"
			for i, lab_name in enumerate(labs[:2]):
				doc = frappe.get_doc("IC Laboratory", lab_name)
				price = 10000 + i * 2500
				has = any(
					(r.applicable_standard or "").strip().casefold() == "iec 62368-1"
					for r in (doc.test_scopes or [])
				)
				if not has:
					doc.append(
						"test_scopes",
						{
							"test_name": "Safety Test",
							"applicable_standard": shared,
							"selling_price": price,
							"purchase_price": price * 0.65,
							"currency": "INR",
							"is_active": 1,
						},
					)
					doc.save(ignore_permissions=True)
			frappe.db.commit()
			offers = get_labs_for_standard(shared)

	labs = {o["laboratory"] for o in offers}
	prices = sorted({flt(o["selling_price"]) for o in offers})
	assert len(labs) >= 2, f"Expected ≥2 labs for {shared}, got {labs}"
	assert len(prices) >= 1, "Expected priced offers"
	# Sorted cheapest-first
	assert flt(offers[0]["selling_price"]) == min(prices)

	meta_q = frappe.get_meta("IC Quotation Test Item")
	meta_t = frappe.get_meta("IC Testing Request")
	assert meta_q.has_field("lab_offer"), "Quotation test item missing lab_offer"
	assert meta_t.has_field("lab_offer"), "Testing Request missing lab_offer"

	return {
		"ok": True,
		"standard": shared,
		"lab_count": len(labs),
		"offers": [
			{
				"laboratory": o["laboratory_name"],
				"location": o["location"],
				"selling_price": o["selling_price"],
			}
			for o in offers
		],
	}
