# Copyright (c) Instacertify
"""QC: Expenses & HRMS last + hiring→FnF alignment."""

from __future__ import annotations

import json

import frappe


def run_hrms_lifecycle_qc() -> dict:
	report = {"ok": [], "warn": [], "fail": []}

	def ok(m):
		report["ok"].append(m)

	def warn(m):
		report["warn"].append(m)

	def fail(m):
		report["fail"].append(m)

	frappe.set_user("Administrator")

	(ok if "hrms" in frappe.get_installed_apps() else fail)("hrms installed")

	from instacertify.hr.lifecycle import ensure_hrms_alignment, get_employee_lifecycle

	align = ensure_hrms_alignment()
	ok(f"alignment ok={len(align.get('ok') or [])} warn={len(align.get('warn') or [])}")
	for w in align.get("warn") or []:
		warn(w)

	life = get_employee_lifecycle()
	stage_keys = [s["key"] for s in life.get("stages") or []]
	for key in ("hiring", "onboarding", "attendance_leave", "payroll", "expenses", "exit_fnf"):
		(ok if key in stage_keys else fail)(f"lifecycle stage {key}")

	required = [
		"Job Applicant",
		"Job Offer",
		"Employee",
		"Employee Onboarding",
		"Attendance",
		"Leave Application",
		"Salary Slip",
		"Payroll Entry",
		"Expense Claim",
		"IC Expense Claim",
		"Employee Separation",
		"Full and Final Statement",
	]
	for dt in required:
		(ok if frappe.db.exists("DocType", dt) else fail)(f"DocType {dt}")

	(ok if frappe.db.exists("Workspace", "HRMS & Expenses") else fail)("Workspace HRMS & Expenses")
	seq = frappe.db.get_value("Workspace", "HRMS & Expenses", "sequence_id")
	if seq is not None and int(seq) >= 50:
		ok(f"HRMS workspace sequence_id={seq} (last-ish)")
	else:
		fail(f"HRMS workspace sequence_id unexpected: {seq}")

	# Explore: expenses / HR near end
	from instacertify.explore.dashboard import get_explore_prompts

	prompts = get_explore_prompts()
	cards = prompts.get("cards") or []
	priorities = {c.get("id"): c.get("priority") for c in cards}
	exp_p = priorities.get("expenses")
	hr_p = priorities.get("hr_lifecycle")
	if exp_p is not None and exp_p >= 90:
		ok(f"Explore expenses priority={exp_p} (last)")
	elif exp_p is None:
		warn("Explore expenses card not shown for this user")
	else:
		fail(f"Explore expenses priority too early: {exp_p}")
	if hr_p is not None and hr_p >= 90:
		ok(f"Explore HRMS priority={hr_p}")
	elif hr_p is None:
		warn("Explore hr_lifecycle card not shown")
	else:
		fail(f"Explore HRMS priority too early: {hr_p}")

	# Home shortcuts: File Expense should be after GST in content list
	ws = frappe.get_doc("Workspace", "Instacertify Home")
	labels = [s.label for s in (ws.shortcuts or [])]
	if "File Expense" in labels:
		idx = labels.index("File Expense")
		# Must be in the last two shortcuts (HRMS Lifecycle + File Expense)
		if idx >= len(labels) - 2:
			ok(f"Home File Expense shortcut near end idx={idx}/{len(labels)}")
		else:
			fail(f"Home File Expense not near end idx={idx}/{len(labels)} labels={labels}")
	else:
		warn("File Expense shortcut missing on Home")
	if "HRMS Lifecycle" in labels:
		ok("Home HRMS Lifecycle shortcut present")
	else:
		warn("HRMS Lifecycle shortcut missing on Home")

	report["summary"] = {
		"ok": len(report["ok"]),
		"warn": len(report["warn"]),
		"fail": len(report["fail"]),
		"passed": len(report["fail"]) == 0,
		"stages": stage_keys,
	}
	print(json.dumps(report, indent=2, default=str))
	return report
