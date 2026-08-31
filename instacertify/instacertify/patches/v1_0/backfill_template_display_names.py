# Copyright (c) Instacertify
"""Backfill display_name from template_name for quote / checklist templates."""

from __future__ import annotations

import frappe


def execute():
	for doctype in ("IC Quotation Template", "IC Document Checklist Template"):
		if not frappe.db.exists("DocType", doctype):
			continue
		meta = frappe.get_meta(doctype)
		if not meta.has_field("display_name"):
			continue
		frappe.db.sql(
			f"""
			UPDATE `tab{doctype}`
			SET display_name = template_name
			WHERE IFNULL(display_name, '') = ''
			  AND IFNULL(template_name, '') != ''
			"""
		)
