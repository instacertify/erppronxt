# Copyright (c) Instacertify
"""Dashboard charts and number cards."""

from __future__ import annotations

import frappe


def ensure_number_cards():
	cards = [
		("IC New Leads", "Lead", '{"status":"Lead"}'),
		("IC Active Leads", "Lead", '{"status":["in",["Open","Replied","Opportunity"]]}'),
		(
			"IC Quotations Sent",
			"Quotation",
			'{"ic_workflow_status":["in",["Shared with Customer","Customer Review"]]}',
		),
		("IC Quotations Accepted", "Quotation", '{"ic_workflow_status":"Accepted"}'),
		("IC Active Projects", "Project", '{"status":["not in",["Completed","Cancelled"]]}'),
		("IC Pending Tasks", "Task", '{"status":["in",["Open","Working"]]}'),
		(
			"IC Testing Requests",
			"IC Testing Request",
			'{"status":["not in",["Report Shared with Customer"]]}',
		),
		(
			"IC Upcoming Deadlines",
			"Project",
			'{"status":["not in",["Completed","Cancelled"]]}',
		),
	]
	for name, dt, filters in cards:
		if not frappe.db.exists("DocType", dt):
			continue
		if frappe.db.exists("Number Card", name):
			continue
		try:
			frappe.get_doc(
				{
					"doctype": "Number Card",
					"name": name,
					"label": name.replace("IC ", ""),
					"document_type": dt,
					"function": "Count",
					"filters_json": filters,
					"is_public": 1,
					"module": "Instacertify",
					"show_percentage_stats": 0,
					"stats_time_interval": "Daily",
				}
			).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Number Card {name}")


def ensure_dashboard_charts():
	charts = [
		{
			"name": "IC Leads by Source",
			"document_type": "Lead",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "ic_lead_source_detail",
			"is_public": 1,
			"module": "Instacertify",
			"type": "Donut",
		},
		{
			"name": "IC Leads by Status",
			"document_type": "Lead",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "status",
			"is_public": 1,
			"module": "Instacertify",
			"type": "Bar",
		},
		{
			"name": "IC Quotations by Status",
			"document_type": "Quotation",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "ic_workflow_status",
			"is_public": 1,
			"module": "Instacertify",
			"type": "Donut",
		},
		{
			"name": "IC Projects by Status",
			"document_type": "Project",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "ic_project_stage",
			"is_public": 1,
			"module": "Instacertify",
			"type": "Bar",
		},
		{
			"name": "IC Projects by Priority",
			"document_type": "Project",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "ic_priority",
			"is_public": 1,
			"module": "Instacertify",
			"type": "Pie",
		},
		{
			"name": "IC Testing Requests by Stage",
			"document_type": "IC Testing Request",
			"chart_type": "Group By",
			"group_by_type": "Count",
			"group_by_based_on": "status",
			"is_public": 1,
			"module": "Instacertify",
			"type": "Bar",
		},
	]
	for chart in charts:
		if not frappe.db.exists("DocType", chart["document_type"]):
			continue
		if frappe.db.exists("Dashboard Chart", chart["name"]):
			continue
		try:
			doc = frappe.get_doc({"doctype": "Dashboard Chart", **chart, "timeseries": 0})
			doc.insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Chart {chart['name']}")
