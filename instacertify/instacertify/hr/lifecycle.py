# Copyright (c) Instacertify
"""Employee lifecycle alignment — Hiring → Onboarding → Attendance → Payroll → Expenses → Exit → FnF."""

from __future__ import annotations

import frappe
from frappe import _


# Ordered stages for ERPNext HRMS + Instacertify overlays
LIFECYCLE_STAGES = [
	{
		"key": "hiring",
		"title": _("Hiring"),
		"description": _("Job applicants and offers"),
		"doctypes": [
			{"label": _("Job Applicant"), "doctype": "Job Applicant"},
			{"label": _("Job Offer"), "doctype": "Job Offer"},
			{"label": _("Interview"), "doctype": "Interview"},
		],
	},
	{
		"key": "onboarding",
		"title": _("Onboarding"),
		"description": _("Employee master, boarding checklist, joining letter"),
		"doctypes": [
			{"label": _("Employee"), "doctype": "Employee"},
			{"label": _("Employee Onboarding"), "doctype": "Employee Onboarding"},
			{"label": _("Joining Letter"), "doctype": "IC Joining Letter"},
			{"label": _("Employee Documents"), "doctype": "IC Employee Document"},
		],
	},
	{
		"key": "attendance_leave",
		"title": _("Attendance & Leave"),
		"description": _("Daily attendance and leave applications"),
		"doctypes": [
			{"label": _("Attendance"), "doctype": "Attendance"},
			{"label": _("Attendance Request"), "doctype": "Attendance Request"},
			{"label": _("Leave Application"), "doctype": "Leave Application"},
			{"label": _("Holiday List"), "doctype": "Holiday List"},
			{"label": _("Shift Type"), "doctype": "Shift Type"},
		],
	},
	{
		"key": "payroll",
		"title": _("Payroll"),
		"description": _("Salary structures, payroll entry, salary slips"),
		"doctypes": [
			{"label": _("Salary Structure"), "doctype": "Salary Structure"},
			{"label": _("Salary Structure Assignment"), "doctype": "Salary Structure Assignment"},
			{"label": _("Payroll Entry"), "doctype": "Payroll Entry"},
			{"label": _("Salary Slip"), "doctype": "Salary Slip"},
			{"label": _("Additional Salary"), "doctype": "Additional Salary"},
		],
	},
	{
		"key": "expenses",
		"title": _("Expenses"),
		"description": _("Employee expense claims (travel, petty, office)"),
		"doctypes": [
			{"label": _("File Expense (Instacertify)"), "doctype": "IC Expense Claim"},
			{"label": _("Expense Claim (HRMS)"), "doctype": "Expense Claim"},
			{"label": _("Expense Claim Type"), "doctype": "Expense Claim Type"},
		],
	},
	{
		"key": "performance",
		"title": _("Performance"),
		"description": _("Appraisals and goals"),
		"doctypes": [
			{"label": _("Appraisal"), "doctype": "Appraisal"},
			{"label": _("Goal"), "doctype": "Goal"},
		],
	},
	{
		"key": "exit_fnf",
		"title": _("Exit & Full and Final"),
		"description": _("Separation checklist and FnF settlement"),
		"doctypes": [
			{"label": _("Employee Separation"), "doctype": "Employee Separation"},
			{"label": _("Full and Final Statement"), "doctype": "Full and Final Statement"},
		],
	},
]


def hrms_installed() -> bool:
	return "hrms" in frappe.get_installed_apps()


def _exists(doctype: str) -> bool:
	return bool(doctype and frappe.db.exists("DocType", doctype))


@frappe.whitelist()
def get_employee_lifecycle(employee: str | None = None) -> dict:
	"""Return hiring→FnF stages with available DocTypes and counts for an employee (optional)."""
	stages = []
	for stage in LIFECYCLE_STAGES:
		items = []
		for row in stage["doctypes"]:
			dt = row["doctype"]
			if not _exists(dt):
				continue
			count = None
			if employee and dt not in (
				"Job Applicant",
				"Job Offer",
				"Interview",
				"Holiday List",
				"Shift Type",
				"Salary Structure",
				"Expense Claim Type",
				"Payroll Entry",
			):
				try:
					meta = frappe.get_meta(dt)
					if meta.has_field("employee"):
						count = frappe.db.count(dt, {"employee": employee})
					elif dt == "Employee":
						count = 1 if frappe.db.exists("Employee", employee) else 0
				except Exception:
					count = None
			items.append(
				{
					"label": row["label"],
					"doctype": dt,
					"count": count,
					"route": ["List", dt],
				}
			)
		if not items:
			continue
		stages.append(
			{
				"key": stage["key"],
				"title": stage["title"],
				"description": stage["description"],
				"items": items,
			}
		)

	emp = None
	if employee and frappe.db.exists("Employee", employee):
		doc = frappe.get_doc("Employee", employee)
		emp = {
			"name": doc.name,
			"employee_name": doc.employee_name,
			"status": doc.status,
			"date_of_joining": str(doc.date_of_joining or ""),
			"relieving_date": str(doc.relieving_date or ""),
			"department": doc.department,
			"designation": doc.designation,
		}

	return {
		"hrms_installed": hrms_installed(),
		"employee": emp,
		"stages": stages,
		"note": _(
			"All employee work lives under the HRMS tab — Hiring through salary slips, expenses, and Full & Final."
		),
	}


def ensure_hrms_alignment():
	"""Idempotent setup: confirm HRMS DocTypes, pin workspaces, seed default expense claim types."""
	report = {"hrms": hrms_installed(), "ok": [], "warn": []}

	if not hrms_installed():
		report["warn"].append("hrms app not installed")
		return report

	for stage in LIFECYCLE_STAGES:
		for row in stage["doctypes"]:
			dt = row["doctype"]
			if _exists(dt):
				report["ok"].append(dt)
			elif dt.startswith("IC "):
				report["warn"].append(f"missing IC doctype {dt}")
			else:
				report["warn"].append(f"missing {dt}")

	# Seed a few Expense Claim Types if empty
	if _exists("Expense Claim Type") and not frappe.db.count("Expense Claim Type"):
		for name in ("Travel", "Food", "Telephone", "Medical", "Others"):
			try:
				frappe.get_doc({"doctype": "Expense Claim Type", "expense_type": name}).insert(
					ignore_permissions=True
				)
				report["ok"].append(f"Expense Claim Type:{name}")
			except Exception:
				pass

	from instacertify.setup.workspace_setup import ensure_hrms_expenses_workspace

	ensure_hrms_expenses_workspace()
	report["ok"].append("HRMS workspace")
	return report
