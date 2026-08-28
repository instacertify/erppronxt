# Copyright (c) Instacertify
"""Strip the IC abbreviation from user-facing labels.

DocType / Role / Workflow *names* stay stable for code & data.
Desk UI shows friendly translations instead.
"""

from __future__ import annotations

import frappe

# source → friendly label shown in desk
FRIENDLY_LABELS = {
	# DocTypes
	"IC Testing Request": "Testing Request",
	"IC Testing Request Item": "Testing Request Item",
	"IC Laboratory": "Laboratory",
	"IC Laboratory Test Scope": "Laboratory Test Scope",
	"IC Sample Tracking": "Sample Tracking",
	"IC Document Request": "Document Request",
	"IC Document Request Item": "Document Request Item",
	"IC Document Checklist Template": "Document Checklist Template",
	"IC Document Checklist Item": "Document Checklist Item",
	"IC Quotation Template": "Quotation Template",
	"IC Quotation Cost Item": "Quotation Cost Item",
	"IC Quotation Test Item": "Quotation Test Item",
	"IC Quotation Product": "Quotation Product",
	"IC Project Update": "Project Update",
	"IC Project Record": "Project Record",
	"IC Project Type": "Project Type",
	"IC Lead Source": "Lead Source",
	"IC Joining Letter": "Joining Letter",
	"IC Employee Document": "Employee Document",
	"IC Expense Claim": "Expense Claim",
	"IC Quote Format File": "Quote Format File",
	"IC Settings": "Settings",
	# Reports
	"IC Commercial Summary": "Commercial Summary",
	"IC Operations Overview": "Operations Overview",
	# Roles
	"IC Admin": "Admin",
	"IC Senior Operations": "Senior Operations",
	"IC Sales Person": "Sales",
	"IC Operations Manager": "Operations Manager",
	# Workflow
	"IC Quotation Workflow": "Quotation Workflow",
	"IC Draft": "Draft",
	"IC Internal Review": "Internal Review",
	"IC Ready to Share": "Ready to Share",
	"IC Shared with Customer": "Shared with Customer",
	"IC Customer Review": "Customer Review",
	"IC Accepted": "Accepted",
	"IC Changes Requested": "Changes Requested",
	"IC Rejected / Lost": "Rejected / Lost",
	"IC Submit for Review": "Submit for Review",
	"IC Approve for Sharing": "Approve for Sharing",
	"IC Share with Customer": "Share with Customer",
	"IC Mark Accepted": "Mark Accepted",
	"IC Request Changes": "Request Changes",
	"IC Revise": "Revise",
	"IC Reject": "Reject",
	# Notifications / misc
	"IC Quotation Accepted": "Quotation Accepted",
	"IC Quotation Changes Requested": "Quotation Changes Requested",
	"IC Home Dashboard": "Home Dashboard",
	"IC CRM Lead Tracker": "CRM Lead Tracker",
	"Project Team Member": "Team Member",
}


def strip_ic_prefix(name: str) -> str:
	if not name:
		return name
	if name.startswith("IC "):
		return name[3:]
	return name


def ensure_friendly_labels():
	"""Upsert English translations so desk never shows the IC abbreviation."""
	for source, target in FRIENDLY_LABELS.items():
		_upsert_translation(source, target)

	# Also strip IC from any remaining Instacertify Number Cards / Charts / Blocks
	_relabel_number_cards()
	_relabel_dashboard_charts()
	_relabel_custom_blocks()
	_relabel_notifications()


def _upsert_translation(source: str, target: str, language: str = "en"):
	if source == target:
		return
	existing = frappe.db.get_value(
		"Translation",
		{"language": language, "source_text": source},
		["name", "translated_text"],
		as_dict=True,
	)
	if existing:
		if existing.translated_text != target:
			frappe.db.set_value("Translation", existing.name, "translated_text", target, update_modified=False)
		return
	frappe.get_doc(
		{
			"doctype": "Translation",
			"language": language,
			"source_text": source,
			"translated_text": target,
		}
	).insert(ignore_permissions=True)


def _relabel_number_cards():
	import re

	for name in frappe.get_all(
		"Number Card",
		filters={"module": "Instacertify"},
		pluck="name",
	):
		friendly = strip_ic_prefix(name)
		label = re.sub(r"-\d+$", "", friendly)
		try:
			if name.startswith("IC "):
				if frappe.db.exists("Number Card", friendly):
					frappe.delete_doc("Number Card", name, force=True, ignore_permissions=True)
				else:
					frappe.rename_doc("Number Card", name, friendly, force=True)
					frappe.db.set_value("Number Card", friendly, "label", label, update_modified=False)
			else:
				frappe.db.set_value("Number Card", name, "label", label, update_modified=False)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Relabel Number Card {name}")


def _relabel_dashboard_charts():
	for name in frappe.get_all(
		"Dashboard Chart",
		filters={"module": "Instacertify"},
		pluck="name",
	):
		friendly = strip_ic_prefix(name)
		if friendly == name:
			continue
		try:
			if frappe.db.exists("Dashboard Chart", friendly):
				frappe.delete_doc("Dashboard Chart", name, force=True, ignore_permissions=True)
			else:
				frappe.rename_doc("Dashboard Chart", name, friendly, force=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Relabel Chart {name}")


def _relabel_custom_blocks():
	for old, new in (
		("IC Home Dashboard", "Home Dashboard"),
		("IC CRM Lead Tracker", "CRM Lead Tracker"),
	):
		if frappe.db.exists("Custom HTML Block", old) and not frappe.db.exists("Custom HTML Block", new):
			try:
				frappe.rename_doc("Custom HTML Block", old, new, force=True)
			except Exception:
				frappe.log_error(frappe.get_traceback(), f"Relabel block {old}")
		elif frappe.db.exists("Custom HTML Block", old):
			# keep content; just note translation covers display
			pass


def _relabel_notifications():
	for old, new in (
		("IC Quotation Accepted", "Quotation Accepted"),
		("IC Quotation Changes Requested", "Quotation Changes Requested"),
	):
		if frappe.db.exists("Notification", old) and not frappe.db.exists("Notification", new):
			try:
				frappe.rename_doc("Notification", old, new, force=True)
			except Exception:
				frappe.log_error(frappe.get_traceback(), f"Relabel Notification {old}")
