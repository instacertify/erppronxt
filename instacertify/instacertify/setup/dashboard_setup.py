# Copyright (c) Instacertify
"""Dashboard charts and number cards."""

from __future__ import annotations

import json

import frappe
from frappe.utils import add_days, get_first_day, nowdate


def ensure_number_cards():
	today = nowdate()
	week_start = str(add_days(today, -6))
	month_start = str(get_first_day(today))

	cards = [
		("IC New Leads", "Lead", {"status": "Lead"}, 0, "Daily"),
		("IC Active Leads", "Lead", {"status": ["in", ["Open", "Replied", "Opportunity"]]}, 0, "Daily"),
		("IC Leads This Week", "Lead", [["creation", ">=", week_start]], 1, "Weekly"),
		("IC Leads This Month", "Lead", [["creation", ">=", month_start]], 1, "Monthly"),
		(
			"IC Quotations Sent",
			"Quotation",
			{"ic_workflow_status": ["in", ["Shared with Customer", "Customer Review"]]},
			0,
			"Daily",
		),
		("IC Quotations Accepted", "Quotation", {"ic_workflow_status": "Accepted"}, 0, "Daily"),
		("IC Active Projects", "Project", {"status": ["not in", ["Completed", "Cancelled"]]}, 0, "Daily"),
		("IC Pending Tasks", "Task", {"status": ["in", ["Open", "Working"]]}, 0, "Daily"),
		(
			"IC Testing Requests",
			"IC Testing Request",
			{"status": ["not in", ["Report Shared with Customer"]]},
			0,
			"Daily",
		),
		(
			"IC Upcoming Deadlines",
			"Project",
			{"status": ["not in", ["Completed", "Cancelled"]]},
			0,
			"Daily",
		),
		(
			"IC Samples Transit to Office",
			"IC Sample Tracking",
			{"sample_location": "In Transit to Office"},
			0,
			"Daily",
		),
		(
			"IC Samples At Office",
			"IC Sample Tracking",
			{"sample_location": "At Instacertify Office"},
			0,
			"Daily",
		),
		(
			"IC Samples Transit to Lab",
			"IC Sample Tracking",
			{"sample_location": "In Transit to Lab"},
			0,
			"Daily",
		),
		(
			"IC Samples At Laboratory",
			"IC Sample Tracking",
			{"sample_location": "At Laboratory"},
			0,
			"Daily",
		),
		(
			"IC Samples In Storage",
			"IC Sample Tracking",
			{"sample_location": "At Instacertify Storage"},
			0,
			"Daily",
		),
		(
			"IC Samples Discarded",
			"IC Sample Tracking",
			{"sample_location": "Discarded"},
			0,
			"Daily",
		),
	]
	for name, dt, filters, pct, interval in cards:
		if not frappe.db.exists("DocType", dt):
			continue
		try:
			if frappe.db.exists("Number Card", name):
				frappe.db.set_value(
					"Number Card",
					name,
					{
						"label": name.replace("IC ", ""),
						"document_type": dt,
						"function": "Count",
						"filters_json": json.dumps(filters),
						"is_public": 1,
						"module": "Instacertify",
						"show_percentage_stats": pct,
						"stats_time_interval": interval,
					},
					update_modified=False,
				)
			else:
				doc = frappe.get_doc(
					{
						"doctype": "Number Card",
						"label": name,
						"document_type": dt,
						"function": "Count",
						"filters_json": json.dumps(filters),
						"is_public": 1,
						"module": "Instacertify",
						"show_percentage_stats": pct,
						"stats_time_interval": interval,
					}
				)
				doc.insert(ignore_permissions=True)
				if doc.name != name:
					frappe.rename_doc("Number Card", doc.name, name, force=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Number Card {name}")


def ensure_dashboard_charts():
	today = nowdate()
	d7 = str(add_days(today, -6))
	d30 = str(add_days(today, -29))

	charts = [
		{
			"chart_name": "IC Leads by Source",
			"document_type": "Lead",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "ic_lead_source_detail",
			"type": "Donut",
			"filters_json": "[]",
			"timeseries": 0,
		},
		{
			"chart_name": "IC Leads by Status",
			"document_type": "Lead",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "status",
			"type": "Bar",
			"filters_json": "[]",
			"timeseries": 0,
		},
		{
			"chart_name": "IC Leads Last 7 Days by Source",
			"document_type": "Lead",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "ic_lead_source_detail",
			"type": "Pie",
			"filters_json": json.dumps([["Lead", "creation", ">=", d7, False]]),
			"timeseries": 0,
		},
		{
			"chart_name": "IC Leads Last 30 Days by Source",
			"document_type": "Lead",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "ic_lead_source_detail",
			"type": "Donut",
			"filters_json": json.dumps([["Lead", "creation", ">=", d30, False]]),
			"timeseries": 0,
		},
		{
			"chart_name": "IC Leads Last 30 Days by Project Type",
			"document_type": "Lead",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "ic_project_type",
			"type": "Pie",
			"filters_json": json.dumps([["Lead", "creation", ">=", d30, False]]),
			"timeseries": 0,
		},
		{
			"chart_name": "IC Leads Last 30 Days by Status",
			"document_type": "Lead",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "status",
			"type": "Bar",
			"filters_json": json.dumps([["Lead", "creation", ">=", d30, False]]),
			"timeseries": 0,
		},
		{
			"chart_name": "IC Lead Trend Weekly",
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
			"chart_name": "IC Quotations by Status",
			"document_type": "Quotation",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "ic_workflow_status",
			"type": "Donut",
			"filters_json": "[]",
			"timeseries": 0,
		},
		{
			"chart_name": "IC Projects by Status",
			"document_type": "Project",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "ic_project_stage",
			"type": "Bar",
			"filters_json": "[]",
			"timeseries": 0,
		},
		{
			"chart_name": "IC Projects by Priority",
			"document_type": "Project",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "ic_priority",
			"type": "Pie",
			"filters_json": "[]",
			"timeseries": 0,
		},
		{
			"chart_name": "IC Testing Requests by Stage",
			"document_type": "IC Testing Request",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "status",
			"type": "Bar",
			"filters_json": "[]",
			"timeseries": 0,
		},
		{
			"chart_name": "IC Samples by Location",
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
