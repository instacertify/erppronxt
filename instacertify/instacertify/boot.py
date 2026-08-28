# Copyright (c) Instacertify
"""Boot session branding."""

from __future__ import annotations

import frappe


def boot_session(bootinfo):
	bootinfo["instacertify"] = {
		"primary_color": "#065175",
		"accent_color": "#EC6820",
		"surface_color": "#f3f8fb",
		"theme": "light",
		"app_name": "Instacertify",
		"logo": "/assets/instacertify/images/instacertify_logo.png",
		"icon": "/assets/instacertify/images/instacertify_icon.png",
		"app_logo": "/assets/instacertify/images/instacertify_app_logo.png",
		"favicon": "/assets/instacertify/images/favicon-32.png",
		"default_workspace": "Instacertify Home",
	}
	# Soft-brand desk — light hue only
	try:
		bootinfo["sitename"] = "Instacertify ERP"
		bootinfo["app_logo_url"] = "/assets/instacertify/images/instacertify_app_logo.png"
		bootinfo["desk_theme"] = "light"
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

	# Prefer Instacertify Home as the desk landing workspace
	try:
		bootinfo["home_page"] = "workspace"
		# Surfaced for client redirect if user has no default_workspace yet
		if not bootinfo.get("user", {}).get("default_workspace"):
			bootinfo.setdefault("user", {})
			# user may be a string in some boots — keep workspace hint on instacertify map
			pass
	except Exception:
		pass
