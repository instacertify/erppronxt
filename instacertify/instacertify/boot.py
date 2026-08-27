# Copyright (c) Instacertify
"""Boot session branding."""

from __future__ import annotations

import frappe


def boot_session(bootinfo):
	bootinfo["instacertify"] = {
		"primary_color": "#065175",
		"accent_color": "#EC6820",
		"app_name": "Instacertify",
	}
	# Soft-brand desk
	try:
		bootinfo["sitename"] = "Instacertify ERP"
	except Exception:
		pass
