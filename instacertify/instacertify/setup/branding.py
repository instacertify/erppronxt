# Copyright (c) Instacertify
"""Brand assets: full wordmark for headers, circular mark for favicon/small UI."""

from __future__ import annotations

import frappe

# Full horizontal wordmark — headers, letterhead, splash, portal
LOGO_FULL = "/assets/instacertify/images/instacertify_logo.png"
LETTERHEAD = "/assets/instacertify/images/instacertify_letterhead.png"
# Circular checkmark — favicon, navbar, small spaces
LOGO_ICON = "/assets/instacertify/images/instacertify_icon.png"
APP_LOGO = "/assets/instacertify/images/instacertify_app_logo.png"
FAVICON = "/assets/instacertify/images/favicon.ico"
FAVICON_PNG = "/assets/instacertify/images/favicon-32.png"
STAMP = "/assets/instacertify/images/instacertify_stamp.png"


def ensure_branding():
	"""Apply Instacertify logos across desk, website, company, and IC Settings."""
	_website_settings()
	_navbar_settings()
	_ic_settings_logos()
	_company_logo()
	_system_app_name()


def _website_settings():
	try:
		ws = frappe.get_single("Website Settings")
		# Small spaces / browser tab
		ws.favicon = FAVICON_PNG
		# Desk + login app mark (circular — fits navbar)
		ws.app_logo = APP_LOGO
		# Larger brand surfaces
		ws.banner_image = LOGO_FULL
		ws.splash_image = LOGO_FULL
		ws.footer_logo = LOGO_FULL
		ws.brand_html = (
			f'<img src="{LOGO_FULL}" alt="Instacertify" '
			f'style="max-height:42px;width:auto;" />'
		)
		ws.app_name = "Instacertify"
		ws.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Website branding")


def _navbar_settings():
	try:
		if not frappe.db.exists("DocType", "Navbar Settings"):
			return
		nav = frappe.get_single("Navbar Settings")
		nav.app_logo = APP_LOGO
		nav.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Navbar branding")


def _ic_settings_logos():
	try:
		doc = frappe.get_single("IC Settings")
		doc.logo = LOGO_FULL
		doc.header_image = LETTERHEAD
		doc.stamp_image = doc.stamp_image or STAMP
		doc.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "IC Settings logos")


def _company_logo():
	try:
		for name in ("Instacertify",):
			if not frappe.db.exists("Company", name):
				continue
			# Company.company_logo is standard in ERPNext
			if frappe.get_meta("Company").has_field("company_logo"):
				frappe.db.set_value("Company", name, "company_logo", LOGO_FULL)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Company logo")


def _system_app_name():
	try:
		ss = frappe.get_single("System Settings")
		if hasattr(ss, "app_name"):
			ss.app_name = "Instacertify"
			ss.save(ignore_permissions=True)
	except Exception:
		pass
