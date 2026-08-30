# Copyright (c) Instacertify
"""Brand assets: full wordmark for headers, circular mark for favicon/small UI."""

from __future__ import annotations

import frappe

# Full horizontal wordmark — headers, letterhead, splash, portal
LOGO_FULL = "/assets/instacertify/images/instacertify_logo.png"
LETTERHEAD = "/assets/instacertify/images/instacertify_letterhead.png"
# Circular checkmark (favicon) — home icon logo, navbar, small spaces
LOGO_ICON = "/assets/instacertify/images/favicon-48.png"
APP_LOGO = "/assets/instacertify/images/favicon-48.png"
FAVICON = "/assets/instacertify/images/favicon.ico"
FAVICON_PNG = "/assets/instacertify/images/favicon-32.png"
FAVICON_16 = "/assets/instacertify/images/favicon-16.png"
APPLE_TOUCH = "/assets/instacertify/images/apple-touch-icon.png"
ICON_192 = "/assets/instacertify/images/instacertify_icon_192.png"
ICON_512 = "/assets/instacertify/images/instacertify_icon_512.png"
STAMP = "/assets/instacertify/images/instacertify_stamp.png"

# Injected into Website Settings so every page (login, desk, portal) uses Instacertify identity
HEAD_HTML = f"""
<link rel="icon" href="{FAVICON}" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="{FAVICON_PNG}">
<link rel="icon" type="image/png" sizes="16x16" href="{FAVICON_16}">
<link rel="apple-touch-icon" sizes="180x180" href="{APPLE_TOUCH}">
<link rel="shortcut icon" href="{FAVICON_PNG}" type="image/png">
<meta name="application-name" content="Instacertify">
<meta name="apple-mobile-web-app-title" content="Instacertify">
<meta property="og:site_name" content="Instacertify">
<meta property="og:image" content="{LOGO_ICON}">
""".strip()


def ensure_branding():
	"""Apply Instacertify logos across desk, website, company, and IC Settings."""
	_website_settings()
	_navbar_settings()
	_ic_settings_logos()
	_company_logo()
	_system_app_name()
	frappe.clear_cache()


def _website_settings():
	try:
		ws = frappe.get_single("Website Settings")
		# Browser tab / site identity — circular Instacertify mark
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
		# Full favicon set + app name meta (survives theme/template defaults)
		ws.head_html = _merge_head_html(ws.head_html or "")
		ws.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Website branding")


def _merge_head_html(existing: str) -> str:
	"""Replace prior Instacertify favicon head block; keep other custom head HTML."""
	# Drop lines that look like our previous inject, then prepend fresh block
	keep = []
	skip_tokens = (
		"/assets/instacertify/images/favicon",
		"/assets/instacertify/images/apple-touch-icon",
		'application-name" content="Instacertify"',
		'apple-mobile-web-app-title" content="Instacertify"',
		'og:site_name" content="Instacertify"',
		'og:image" content="/assets/instacertify/images/favicon-48.png"',
	)
	for line in existing.splitlines():
		if any(tok in line for tok in skip_tokens):
			continue
		keep.append(line)
	rest = "\n".join(keep).strip()
	return (HEAD_HTML + ("\n" + rest if rest else "")).strip()


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
		doc.legal_name = "INSTACERTIFY LABS PRIVATE LIMITED"
		doc.address_line = "PK 01 SECTOR 63A NOIDA, GAUTAM BUDDHA NAGAR, UTTAR PRADESH-201301, INDIA"
		doc.cin = "U74999UP2022PTC170291"
		doc.gstin = "09AAGCI8396C1Z7"
		doc.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "IC Settings logos")


def _company_logo():
	"""Stamp Instacertify mark on every Company that has no logo yet; force Instacertify company."""
	try:
		if not frappe.get_meta("Company").has_field("company_logo"):
			return
		# Named Instacertify company always gets the logo
		for name in frappe.get_all("Company", pluck="name"):
			if name.strip().lower() in ("instacertify", "instacertify labs", "instacertify labs private limited"):
				frappe.db.set_value("Company", name, "company_logo", LOGO_FULL, update_modified=False)
				continue
			cur = frappe.db.get_value("Company", name, "company_logo")
			if not cur:
				frappe.db.set_value("Company", name, "company_logo", LOGO_FULL, update_modified=False)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Company logo")


def _system_app_name():
	try:
		ss = frappe.get_single("System Settings")
		changed = False
		if hasattr(ss, "app_name") and ss.app_name != "Instacertify":
			ss.app_name = "Instacertify"
			changed = True
		# Some builds expose desk title / language defaults here
		if changed:
			ss.save(ignore_permissions=True)
		elif hasattr(ss, "app_name"):
			# still force via db in case save is skipped
			frappe.db.set_value("System Settings", "System Settings", "app_name", "Instacertify", update_modified=False)
	except Exception:
		pass
