# Copyright (c) Instacertify
"""Dashboard charts and number cards."""

from __future__ import annotations

import json

import frappe
from frappe.utils import add_days, get_first_day, nowdate


def _friendly(name: str) -> str:
	return name[3:] if name.startswith("IC ") else name


def _ensure_renamed(doctype: str, old: str, new: str):
	if old == new:
		return new
	if frappe.db.exists(doctype, old) and not frappe.db.exists(doctype, new):
		try:
			frappe.rename_doc(doctype, old, new, force=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Rename {doctype} {old} → {new}")
	return new if frappe.db.exists(doctype, new) else old


def _list_filters(doctype: str, filters) -> list:
	"""Convert dict / short filters into Number Card list format.

	Clickable Number Cards require:
	  [["DocType", "field", "operator", value], ...]
	A plain dict breaks widget click (no .reduce).
	"""
	out = []
	if not filters:
		return out
	if isinstance(filters, dict):
		for field, value in filters.items():
			if isinstance(value, (list, tuple)) and len(value) == 2 and value[0] in (
				"=",
				"!=",
				">",
				"<",
				">=",
				"<=",
				"like",
				"not like",
				"in",
				"not in",
				"between",
				"Timespan",
			):
				out.append([doctype, field, value[0], value[1]])
			elif isinstance(value, (list, tuple)) and value and value[0] == "in":
				out.append([doctype, field, "in", value[1]])
			elif isinstance(value, (list, tuple)) and value and value[0] == "not in":
				out.append([doctype, field, "not in", value[1]])
			elif isinstance(value, (list, tuple)):
				# already ["in", [...]] style from our defs
				op = value[0] if value and isinstance(value[0], str) else "="
				val = value[1] if len(value) > 1 else value
				out.append([doctype, field, op, val])
			else:
				out.append([doctype, field, "=", value])
		return out
	if isinstance(filters, list):
		for f in filters:
			if not isinstance(f, (list, tuple)):
				continue
			if len(f) == 4 and f[0] == doctype:
				out.append(list(f))
			elif len(f) == 3:
				out.append([doctype, f[0], f[1], f[2]])
			elif len(f) == 4:
				out.append(list(f))
		return out
	return out


def ensure_number_cards():
	today = nowdate()
	week_start = str(add_days(today, -6))
	month_start = str(get_first_day(today))
	deadline_end = str(add_days(today, 14))

	cards = [
		("New Leads", "Lead", {"status": "Lead"}, 0, "Daily"),
		("Active Leads", "Lead", {"status": ["in", ["Open", "Replied", "Opportunity"]]}, 0, "Daily"),
		(
			"Leads to Contact",
			"Lead",
			[
				["status", "not in", ["Converted", "Do Not Contact"]],
				["ic_next_contact_date", "<=", today],
			],
			0,
			"Daily",
		),
		("Leads This Week", "Lead", [["creation", ">=", week_start]], 1, "Weekly"),
		("Leads This Month", "Lead", [["creation", ">=", month_start]], 1, "Monthly"),
		(
			"Quotations Sent",
			"Quotation",
			{"ic_workflow_status": ["in", ["Shared with Customer", "Customer Review"]]},
			0,
			"Daily",
		),
		("Quotations Accepted", "Quotation", {"ic_workflow_status": "Accepted"}, 0, "Daily"),
		("Active Projects", "Project", {"status": ["not in", ["Completed", "Cancelled"]]}, 0, "Daily"),
		("Pending Tasks", "Task", {"status": ["in", ["Open", "Working"]]}, 0, "Daily"),
		(
			"Open Tickets",
			"Helpdesk Ticket",
			{"status": ["in", ["Open", "In Progress", "Waiting on Customer"]]},
			0,
			"Daily",
		),
		(
			"Pending Documents",
			"IC Document Request",
			{"status": ["in", ["Sent to Customer", "Partially Uploaded"]]},
			0,
			"Daily",
		),
		(
			"Testing Requests",
			"IC Testing Request",
			{"status": ["not in", ["Report Shared with Customer"]]},
			0,
			"Daily",
		),
		(
			"Upcoming Deadlines",
			"Project",
			{
				"status": ["not in", ["Completed", "Cancelled"]],
				"ic_deadline": ["<=", deadline_end],
			},
			0,
			"Daily",
		),
		(
			"AMC Due Soon",
			"Project",
			{
				"ic_requires_amc": 1,
				"ic_amc_status": ["in", ["Scheduled", "Reminded"]],
				"ic_amc_contact_date": ["<=", str(add_days(today, 31))],
			},
			0,
			"Daily",
		),
		(
			"Samples Transit to Office",
			"IC Sample Tracking",
			{"sample_location": "In Transit to Office"},
			0,
			"Daily",
		),
		(
			"Samples At Office",
			"IC Sample Tracking",
			{"sample_location": "At Instacertify Office"},
			0,
			"Daily",
		),
		(
			"Samples Transit to Lab",
			"IC Sample Tracking",
			{"sample_location": "In Transit to Lab"},
			0,
			"Daily",
		),
		(
			"Samples At Laboratory",
			"IC Sample Tracking",
			{"sample_location": "At Laboratory"},
			0,
			"Daily",
		),
		(
			"Samples In Storage",
			"IC Sample Tracking",
			{"sample_location": "At Instacertify Storage"},
			0,
			"Daily",
		),
		(
			"Samples Discarded",
			"IC Sample Tracking",
			{"sample_location": "Discarded"},
			0,
			"Daily",
		),
	]
	for name, dt, filters, pct, interval in cards:
		if not frappe.db.exists("DocType", dt):
			continue
		# migrate legacy IC-prefixed card names
		_ensure_renamed("Number Card", f"IC {name}", name)
		list_filters = _list_filters(dt, filters)
		try:
			payload = {
				"label": name,
				"document_type": dt,
				"type": "Document Type",
				"function": "Count",
				"filters_json": json.dumps(list_filters),
				"is_public": 1,
				"module": "Instacertify",
				"show_percentage_stats": pct,
				"stats_time_interval": interval,
			}
			if frappe.db.exists("Number Card", name):
				frappe.db.set_value("Number Card", name, payload, update_modified=False)
			else:
				doc = frappe.get_doc({"doctype": "Number Card", "name": name, **payload})
				doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
				if doc.name != name and not frappe.db.exists("Number Card", name):
					frappe.rename_doc("Number Card", doc.name, name, force=True)
				elif doc.name != name and frappe.db.exists("Number Card", name):
					frappe.delete_doc("Number Card", doc.name, force=True, ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Number Card {name}")


def ensure_dashboard_charts():
	today = nowdate()
	d7 = str(add_days(today, -6))
	d30 = str(add_days(today, -29))

	charts = [
		{
			"chart_name": "Leads by Source",
			"document_type": "Lead",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "ic_lead_source_detail",
			"type": "Donut",
			"filters_json": "[]",
			"timeseries": 0,
		},
		{
			"chart_name": "Leads by Status",
			"document_type": "Lead",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "status",
			"type": "Bar",
			"filters_json": "[]",
			"timeseries": 0,
		},
		{
			"chart_name": "Leads Last 7 Days by Source",
			"document_type": "Lead",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "ic_lead_source_detail",
			"type": "Pie",
			"filters_json": json.dumps([["Lead", "creation", ">=", d7, False]]),
			"timeseries": 0,
		},
		{
			"chart_name": "Leads Last 30 Days by Source",
			"document_type": "Lead",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "ic_lead_source_detail",
			"type": "Donut",
			"filters_json": json.dumps([["Lead", "creation", ">=", d30, False]]),
			"timeseries": 0,
		},
		{
			"chart_name": "Leads Last 30 Days by Project Type",
			"document_type": "Lead",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "ic_project_type",
			"type": "Pie",
			"filters_json": json.dumps([["Lead", "creation", ">=", d30, False]]),
			"timeseries": 0,
		},
		{
			"chart_name": "Leads Last 30 Days by Status",
			"document_type": "Lead",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "status",
			"type": "Bar",
			"filters_json": json.dumps([["Lead", "creation", ">=", d30, False]]),
			"timeseries": 0,
		},
		{
			"chart_name": "Lead Trend Weekly",
			"document_type": "Lead",
			"chart_type": "Count",
			"based_on": "creation",
			"time_interval": "Weekly",
			"timespan": "Last Quarter",
			"type": "Line",
			"timeseries": 1,
			"filters_json": "[]",
		},
		{
			"chart_name": "Quotations by Status",
			"document_type": "Quotation",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "ic_workflow_status",
			"type": "Donut",
			"filters_json": "[]",
			"timeseries": 0,
		},
		{
			"chart_name": "Projects by Status",
			"document_type": "Project",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "ic_project_stage",
			"type": "Bar",
			"filters_json": "[]",
			"timeseries": 0,
		},
		{
			"chart_name": "Projects by Priority",
			"document_type": "Project",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "ic_priority",
			"type": "Pie",
			"filters_json": "[]",
			"timeseries": 0,
		},
		{
			"chart_name": "Testing Requests by Stage",
			"document_type": "IC Testing Request",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "status",
			"type": "Bar",
			"filters_json": "[]",
			"timeseries": 0,
		},
		{
			"chart_name": "Samples by Location",
			"document_type": "IC Sample Tracking",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "sample_location",
			"type": "Donut",
			"filters_json": "[]",
			"timeseries": 0,
		},
	]
	for chart in charts:
		if not frappe.db.exists("DocType", chart["document_type"]):
			continue
		gbf = chart.get("group_by_based_on")
		if gbf and chart["document_type"] == "Lead" and gbf.startswith("ic_"):
			if not frappe.get_meta("Lead").has_field(gbf):
				continue
		name = chart["chart_name"]
		_ensure_renamed("Dashboard Chart", f"IC {name}", name)
		try:
			values = {
				"document_type": chart["document_type"],
				"chart_type": chart["chart_type"],
				"type": chart["type"],
				"filters_json": chart.get("filters_json") or "[]",
				"timeseries": chart.get("timeseries", 0),
				"is_public": 1,
				"module": "Instacertify",
			}
			if chart.get("group_by_based_on"):
				values["group_by_based_on"] = chart["group_by_based_on"]
				values["group_by_type"] = chart.get("group_by_type") or "Count"
			if chart.get("based_on"):
				values["based_on"] = chart["based_on"]
				values["time_interval"] = chart.get("time_interval")
				values["timespan"] = chart.get("timespan")

			if frappe.db.exists("Dashboard Chart", name):
				frappe.db.set_value("Dashboard Chart", name, values, update_modified=False)
			else:
				frappe.get_doc({"doctype": "Dashboard Chart", "chart_name": name, **values}).insert(
					ignore_permissions=True
				)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Chart {name}")
