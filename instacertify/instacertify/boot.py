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
	}
	# Soft-brand desk — light hue only
	try:
		bootinfo["sitename"] = "Instacertify ERP"
		bootinfo["app_logo_url"] = "/assets/instacertify/images/instacertify_app_logo.png"
		bootinfo["desk_theme"] = "light"
	except Exception:
		pass
