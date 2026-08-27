# Copyright (c) Instacertify
"""Boot session branding."""

from __future__ import annotations

import frappe


def boot_session(bootinfo):
	bootinfo["instacertify"] = {
		"primary_color": "#065175",
		"accent_color": "#EC6820",
		"app_name": "Instacertify",
		"logo": "/assets/instacertify/images/instacertify_logo.png",
		"icon": "/assets/instacertify/images/instacertify_icon.png",
		"app_logo": "/assets/instacertify/images/instacertify_app_logo.png",
		"favicon": "/assets/instacertify/images/favicon-32.png",
	}
	# Soft-brand desk
	try:
		bootinfo["sitename"] = "Instacertify ERP"
		# Prefer Instacertify circular mark in desk chrome
		bootinfo["app_logo_url"] = "/assets/instacertify/images/instacertify_app_logo.png"
	except Exception:
		pass
