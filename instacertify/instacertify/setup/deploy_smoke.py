# Copyright (c) Instacertify
"""Post-deploy smoke checks for Hostinger / production.

Usage:
  bench --site <site> execute instacertify.setup.deploy_smoke.run
"""

from __future__ import annotations

import frappe


REQUIRED_DOCTYPES = (
	"IC Testing Request",
	"IC Sample Tracking",
	"IC Laboratory",
	"IC Test Request Form",
	"IC Quotation Template",
	"IC Document Request",
	"IC Settings",
	"Customer",
	"Quotation",
	"Project",
	"Event",
)


def run():
	"""Print OK/FAIL lines; raise if any critical check fails."""
	failures: list[str] = []
	lines: list[str] = []

	def check(label: str, ok: bool, detail: str = ""):
		status = "OK" if ok else "FAIL"
		msg = f"{status}  {label}" + (f" — {detail}" if detail else "")
		lines.append(msg)
		print(msg)
		if not ok:
			failures.append(label)

	apps = frappe.get_installed_apps()
	check("instacertify installed", "instacertify" in apps, ",".join(apps))
	check("erpnext installed", "erpnext" in apps)

	for dt in REQUIRED_DOCTYPES:
		check(f"DocType {dt}", bool(frappe.db.exists("DocType", dt)))

	check(
		"Workspace Instacertify Home",
		bool(frappe.db.exists("Workspace", "Instacertify Home")),
	)
	check(
		"Workspace Sidebar Instacertify Home",
		bool(frappe.db.exists("Workspace Sidebar", "Instacertify Home")),
	)
	# Frappe 16 left nav — must include core ops links (not GST-only)
	sidebar_labels = set()
	if frappe.db.exists("Workspace Sidebar", "Instacertify Home"):
		sidebar_labels = {
			(r.label or "").strip()
			for r in frappe.get_all(
				"Workspace Sidebar Item",
				filters={"parent": "Instacertify Home"},
				fields=["label"],
			)
		}
	for label in ("Quotations", "Customers", "Leads", "Testing & Samples"):
		check(f"Sidebar has {label}", label in sidebar_labels)
	check(
		"Custom HTML Block Home Dashboard",
		bool(frappe.db.exists("Custom HTML Block", "Home Dashboard")),
	)

	# Public assets present on disk (desk JS/CSS)
	try:
		js = frappe.get_app_path("instacertify", "public", "js", "instacertify.js")
		css = frappe.get_app_path("instacertify", "public", "css", "instacertify.css")
		import os

		check("public/js/instacertify.js", os.path.isfile(js))
		check("public/css/instacertify.css", os.path.isfile(css))
	except Exception as e:
		check("public assets", False, str(e))

	# Favicon / brand images used on desk + Hostinger static assets
	try:
		import os

		img = frappe.get_app_path("instacertify", "public", "images", "favicon-32.png")
		check("favicon-32.png", os.path.isfile(img))
		check(
			"favicon.ico",
			os.path.isfile(frappe.get_app_path("instacertify", "public", "images", "favicon.ico")),
		)
		check(
			"apple-touch-icon.png",
			os.path.isfile(
				frappe.get_app_path("instacertify", "public", "images", "apple-touch-icon.png")
			),
		)
	except Exception as e:
		check("favicon", False, str(e))

	# Site identity — Website Settings must point at Instacertify favicon
	try:
		ws_favicon = frappe.db.get_single_value("Website Settings", "favicon") or ""
		ws_app = frappe.db.get_single_value("Website Settings", "app_name") or ""
		check(
			"Website Settings favicon",
			"instacertify" in ws_favicon.lower() and "favicon" in ws_favicon.lower(),
			ws_favicon or "(empty)",
		)
		check("Website Settings app_name", ws_app == "Instacertify", ws_app or "(empty)")
	except Exception as e:
		check("Website Settings branding", False, str(e))

	# Soft: customer history API
	cust = frappe.db.get_value("Customer", {}, "name")
	if cust:
		try:
			from instacertify.crm.events import get_customer_history

			d = get_customer_history(cust)
			check(
				"get_customer_history",
				isinstance(d, dict),
				f"customer={cust} samples={len(d.get('samples') or [])}",
			)
		except Exception as e:
			check("get_customer_history", False, str(e))
	else:
		lines.append("SKIP  get_customer_history — no Customer yet")
		print(lines[-1])

	print("---")
	print(f"site={frappe.local.site}")
	if failures:
		frappe.throw(
			"Deploy smoke failed: " + ", ".join(failures),
			title="Instacertify Deploy Smoke",
		)
	return {"ok": True, "checks": len(lines), "site": frappe.local.site}
