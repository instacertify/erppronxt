# Copyright (c) Instacertify
"""Boot session branding."""

from __future__ import annotations

import frappe


def boot_session(bootinfo):
	bootinfo["instacertify"] = {
		"primary_color": "#0D47A1",
		"accent_color": "#EC691F",
		"surface_color": "#E7F1FC",
		"theme": "light",
		"app_name": "Instacertify",
		"logo": "/assets/instacertify/images/instacertify_logo.png",
		"icon": "/assets/instacertify/images/favicon-48.png",
		"app_logo": "/assets/instacertify/images/favicon-48.png",
		"favicon": "/assets/instacertify/images/favicon-32.png",
		"default_workspace": "Instacertify Home",
	}
	# Soft-brand desk — light hue only
	try:
		bootinfo["sitename"] = "Instacertify"
		bootinfo["app_logo_url"] = "/assets/instacertify/images/favicon-48.png"
		bootinfo["desk_theme"] = "light"
		# Browser / PWA-facing identity in boot payload
		bootinfo["favicon"] = "/assets/instacertify/images/favicon-32.png"
		bootinfo["app_name"] = "Instacertify"
	except Exception:
		pass

	# Ensure friendly labels (no "IC" abbreviation) are in the boot translation map
	try:
		from instacertify.setup.friendly_labels import FRIENDLY_LABELS

		messages = bootinfo.get("__messages") or {}
		for source, target in FRIENDLY_LABELS.items():
			messages[source] = target
		bootinfo["__messages"] = messages
	except Exception:
		pass

	# Frappe 16: boot.home_page must be a real Desk *Page* (e.g. "desktop").
	# Legacy value "workspace" is not a Page anymore → "Page workspace not found".
	# Landing on Instacertify Home is handled by User.default_workspace + client go_home().
	try:
		if bootinfo.get("home_page") in (None, "", "workspace", "Workspace", "workspaces"):
			bootinfo["home_page"] = "desktop"
		user = bootinfo.get("user")
		if isinstance(user, dict) and not user.get("default_workspace"):
			user["default_workspace"] = {
				"name": "Instacertify Home",
				"title": "Instacertify Home",
				"public": 1,
			}
	except Exception:
		pass

	# Fix missing Address.tax_category / Contact.is_billing_contact before party queries
	try:
		from instacertify.setup.contact_billing import ensure_party_address_contact_fields

		ensure_party_address_contact_fields()
	except Exception:
		pass
