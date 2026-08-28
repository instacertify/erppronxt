# Copyright (c) Instacertify
"""Ensure Desk / portal navigation targets resolve (no 404 landings)."""

from __future__ import annotations

import json
import re

import frappe
from frappe import get_hooks


# Desk pages that must exist for Instacertify Home / Explore
REQUIRED_PAGES = (
	"project-board",
	"team-collaboration",
)

# DocTypes linked from Home Quick Links / Explore / HR workdesk
REQUIRED_DOCTYPES = (
	"Lead",
	"Customer",
	"Quotation",
	"Project",
	"Task",
	"Event",
	"Helpdesk Ticket",
	"Employee",
	"IC Testing Request",
	"IC Laboratory",
	"IC Quotation Template",
	"IC Expense Claim",
	"IC Sample Tracking",
	"IC Document Request",
	"IC Sample Dispatch Collection",
	"Sales Invoice",
	"Purchase Invoice",
)

# Public portal templates (website_route_rules → www module)
REQUIRED_PORTALS = (
	("/ic-quotation/", "ic_quotation"),
	("/ic-documents/", "ic_documents"),
	("/ic-dispatch/", "ic_dispatch"),
	("/ic-report/", "ic_report"),
	("/ic-verify/", "ic_verify"),
)

# Hard-coded Home HTML paths that must resolve to a DocType or Page
HOME_HREFS = (
	"/app/task",
	"/app/event/new",
	"/app/event/view/calendar",
	"/app/lead",
	"/app/helpdesk-ticket",
	"/app/helpdesk-ticket/new",
	"/app/team-collaboration",
	"/app/employee",
	"/app/project-board",
)


def _ok(checks: list, msg: str):
	checks.append({"ok": True, "msg": msg})


def _fail(checks: list, msg: str):
	checks.append({"ok": False, "msg": msg})


def _slug_to_doctype(slug: str) -> str | None:
	slug = (slug or "").split("?")[0].strip("/")
	if not slug:
		return None
	# Exact scrub match
	for dt in frappe.get_all("DocType", pluck="name"):
		if frappe.scrub(dt).replace("_", "-") == slug or dt.lower().replace(" ", "-") == slug:
			return dt
	return None


def _href_resolves(path: str) -> tuple[bool, str]:
	parts = path.split("?")[0].strip("/").split("/")
	if len(parts) < 2 or parts[0] != "app":
		return False, "not an /app path"
	key = parts[1]
	if key in REQUIRED_PAGES or frappe.db.exists("Page", key):
		return True, f"Page {key}"
	if key == "workspaces":
		name = "/".join(parts[2:]).replace("%20", " ")
		return bool(frappe.db.exists("Workspace", name)), f"Workspace {name}"
	if key == "query-report":
		name = "/".join(parts[2:]).replace("%20", " ")
		return bool(frappe.db.exists("Report", name)), f"Report {name}"
	if key == "event" and len(parts) >= 3 and parts[2] in ("new", "view"):
		return bool(frappe.db.exists("DocType", "Event")), "Event"
	if len(parts) >= 3 and parts[2] == "new":
		dt = _slug_to_doctype(key)
		return bool(dt and frappe.db.exists("DocType", dt)), f"New {dt or key}"
	dt = _slug_to_doctype(key)
	if dt and frappe.db.exists("DocType", dt):
		return True, f"DocType {dt}"
	return False, f"unresolved slug {key}"


@frappe.whitelist()
def run_link_health_qc() -> dict:
	"""Validate Pages, DocTypes, portal routes, and Home hrefs used in navigation."""
	checks: list[dict] = []

	if frappe.db.exists("Workspace", "Instacertify Home"):
		_ok(checks, "Workspace Instacertify Home exists")
	else:
		_fail(checks, "Workspace Instacertify Home missing")

	for page in REQUIRED_PAGES:
		if frappe.db.exists("Page", page):
			_ok(checks, f"Page {page}")
		else:
			_fail(checks, f"Page {page} missing")

	for dt in REQUIRED_DOCTYPES:
		if frappe.db.exists("DocType", dt):
			_ok(checks, f"DocType {dt}")
		else:
			_fail(checks, f"DocType {dt} missing")

	rules = get_hooks("website_route_rules") or []
	rule_blob = json.dumps(rules)
	for prefix, template in REQUIRED_PORTALS:
		if prefix.rstrip("/") in rule_blob or template in rule_blob:
			_ok(checks, f"Portal route {prefix} → {template}")
		else:
			_fail(checks, f"Portal route missing for {prefix} ({template})")
		# Template module file
		path = frappe.get_app_path("instacertify", "www", f"{template}.py")
		if frappe.utils.cstr(path) and __import__("os").path.exists(path):
			_ok(checks, f"www/{template}.py present")
		else:
			_fail(checks, f"www/{template}.py missing")

	for href in HOME_HREFS:
		ok, detail = _href_resolves(href)
		(_ok if ok else _fail)(checks, f"Home href {href} → {detail}")

	# Workspace Quick Links must not reference missing shortcut labels
	if frappe.db.exists("Workspace", "Instacertify Home"):
		ws = frappe.get_doc("Workspace", "Instacertify Home")
		labels = {s.label for s in (ws.shortcuts or [])}
		try:
			content = json.loads(ws.content or "[]")
		except Exception:
			content = []
			_fail(checks, "Instacertify Home content JSON invalid")
		for block in content:
			if block.get("type") != "shortcut":
				continue
			name = (block.get("data") or {}).get("shortcut_name")
			if name and name not in labels:
				_fail(checks, f"Orphan Quick Link tile: {name}")
			elif name:
				_ok(checks, f"Quick Link tile OK: {name}")

		for s in ws.shortcuts or []:
			stype = s.type or "DocType"
			target = s.link_to
			if stype == "Page" and not frappe.db.exists("Page", target):
				_fail(checks, f"Shortcut Page missing: {s.label} → {target}")
			elif stype == "DocType" and not frappe.db.exists("DocType", target):
				_fail(checks, f"Shortcut DocType missing: {s.label} → {target}")
			elif stype == "DocType" and frappe.get_meta(target).issingle and (s.doc_view or "") == "List":
				_fail(checks, f"Single DocType shortcut must not use List view: {s.label}")
			else:
				_ok(checks, f"Shortcut OK: {s.label}")

	# Team Collaboration breadcrumb must not point at generic /app/home only
	collab_js = frappe.get_app_path(
		"instacertify", "instacertify", "page", "team_collaboration", "team_collaboration.js"
	)
	try:
		text = open(collab_js, encoding="utf-8").read()
		if re.search(r'route:\s*["\']/app/home["\']', text):
			_fail(checks, "Team Collaboration breadcrumb still uses /app/home")
		elif "Instacertify Home" in text or "workspaces/Instacertify" in text:
			_ok(checks, "Team Collaboration breadcrumb points at Instacertify Home")
		else:
			_fail(checks, "Team Collaboration breadcrumb target unclear")
	except Exception as e:
		_fail(checks, f"Could not read team_collaboration.js: {e}")

	failed = [c for c in checks if not c["ok"]]
	return {
		"ok": not failed,
		"passed": len(checks) - len(failed),
		"failed": len(failed),
		"failures": failed,
		"checks": checks,
	}
