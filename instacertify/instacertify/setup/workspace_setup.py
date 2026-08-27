# Copyright (c) Instacertify
"""Workspace and navigation setup."""

from __future__ import annotations

import json

import frappe


def ensure_workspaces():
	_ensure_home_workspace()


def _ensure_home_workspace():
	name = "Instacertify Home"
	content = [
		{"id": "ic_header", "type": "header", "data": {"text": "<span class=\"h4\"><b>Instacertify Home</b></span>", "col": 12}},
		{"id": "ic_spacer1", "type": "spacer", "data": {"col": 12}},
		{"id": "ic_cards_header", "type": "header", "data": {"text": "<span class=\"h5\">Operations Snapshot</span>", "col": 12}},
		{"id": "nc_new_leads", "type": "number_card", "data": {"number_card_name": "IC New Leads", "col": 3}},
		{"id": "nc_active_leads", "type": "number_card", "data": {"number_card_name": "IC Active Leads", "col": 3}},
		{"id": "nc_quotes_sent", "type": "number_card", "data": {"number_card_name": "IC Quotations Sent", "col": 3}},
		{"id": "nc_quotes_accepted", "type": "number_card", "data": {"number_card_name": "IC Quotations Accepted", "col": 3}},
		{"id": "nc_active_projects", "type": "number_card", "data": {"number_card_name": "IC Active Projects", "col": 3}},
		{"id": "nc_pending_tasks", "type": "number_card", "data": {"number_card_name": "IC Pending Tasks", "col": 3}},
		{"id": "nc_testing", "type": "number_card", "data": {"number_card_name": "IC Testing Requests", "col": 3}},
		{"id": "nc_deadlines", "type": "number_card", "data": {"number_card_name": "IC Upcoming Deadlines", "col": 3}},
		{"id": "ic_charts_header", "type": "header", "data": {"text": "<span class=\"h5\">Insights</span>", "col": 12}},
		{"id": "chart_leads_source", "type": "chart", "data": {"chart_name": "IC Leads by Source", "col": 6}},
		{"id": "chart_quotes_status", "type": "chart", "data": {"chart_name": "IC Quotations by Status", "col": 6}},
		{"id": "chart_projects_status", "type": "chart", "data": {"chart_name": "IC Projects by Status", "col": 6}},
		{"id": "chart_projects_priority", "type": "chart", "data": {"chart_name": "IC Projects by Priority", "col": 6}},
		{"id": "ic_shortcuts_header", "type": "header", "data": {"text": "<span class=\"h5\">Quick Links</span>", "col": 12}},
		{"id": "sc_leads", "type": "shortcut", "data": {"shortcut_name": "Leads", "col": 3}},
		{"id": "sc_customers", "type": "shortcut", "data": {"shortcut_name": "Customers", "col": 3}},
		{"id": "sc_quotations", "type": "shortcut", "data": {"shortcut_name": "Quotations", "col": 3}},
		{"id": "sc_projects", "type": "shortcut", "data": {"shortcut_name": "Projects", "col": 3}},
		{"id": "sc_testing", "type": "shortcut", "data": {"shortcut_name": "Testing Requests", "col": 3}},
		{"id": "sc_labs", "type": "shortcut", "data": {"shortcut_name": "Laboratories", "col": 3}},
		{"id": "sc_samples", "type": "shortcut", "data": {"shortcut_name": "Samples", "col": 3}},
		{"id": "sc_docs", "type": "shortcut", "data": {"shortcut_name": "Document Requests", "col": 3}},
	]

	shortcuts = [
		{"label": "Leads", "link_to": "Lead", "type": "DocType", "doc_view": "List"},
		{"label": "Customers", "link_to": "Customer", "type": "DocType", "doc_view": "List"},
		{"label": "Quotations", "link_to": "Quotation", "type": "DocType", "doc_view": "List"},
		{"label": "Projects", "link_to": "Project", "type": "DocType", "doc_view": "List"},
		{"label": "Testing Requests", "link_to": "IC Testing Request", "type": "DocType", "doc_view": "List"},
		{"label": "Laboratories", "link_to": "IC Laboratory", "type": "DocType", "doc_view": "List"},
		{"label": "Samples", "link_to": "IC Sample Tracking", "type": "DocType", "doc_view": "List"},
		{"label": "Document Requests", "link_to": "IC Document Request", "type": "DocType", "doc_view": "List"},
	]

	links = [
		{"label": "CRM", "type": "Card Break"},
		{"label": "Lead", "link_type": "DocType", "link_to": "Lead", "type": "Link"},
		{"label": "Opportunity", "link_type": "DocType", "link_to": "Opportunity", "type": "Link"},
		{"label": "Consultant Referral", "link_type": "DocType", "link_to": "Consultant Referral", "type": "Link"},
		{"label": "Customers", "type": "Card Break"},
		{"label": "Customer", "link_type": "DocType", "link_to": "Customer", "type": "Link"},
		{"label": "Contact", "link_type": "DocType", "link_to": "Contact", "type": "Link"},
		{"label": "Address", "link_type": "DocType", "link_to": "Address", "type": "Link"},
		{"label": "Sales", "type": "Card Break"},
		{"label": "Quotation", "link_type": "DocType", "link_to": "Quotation", "type": "Link"},
		{"label": "IC Quotation Template", "link_type": "DocType", "link_to": "IC Quotation Template", "type": "Link"},
		{"label": "Sales Invoice", "link_type": "DocType", "link_to": "Sales Invoice", "type": "Link"},
		{"label": "Projects", "type": "Card Break"},
		{"label": "Project", "link_type": "DocType", "link_to": "Project", "type": "Link"},
		{"label": "Task", "link_type": "DocType", "link_to": "Task", "type": "Link"},
		{"label": "IC Project Update", "link_type": "DocType", "link_to": "IC Project Update", "type": "Link"},
		{"label": "Timesheet", "link_type": "DocType", "link_to": "Timesheet", "type": "Link"},
		{"label": "Testing", "type": "Card Break"},
		{"label": "IC Testing Request", "link_type": "DocType", "link_to": "IC Testing Request", "type": "Link"},
		{"label": "IC Sample Tracking", "link_type": "DocType", "link_to": "IC Sample Tracking", "type": "Link"},
		{"label": "Laboratory Library", "type": "Card Break"},
		{"label": "IC Laboratory", "link_type": "DocType", "link_to": "IC Laboratory", "type": "Link"},
		{"label": "Documents", "type": "Card Break"},
		{"label": "IC Document Request", "link_type": "DocType", "link_to": "IC Document Request", "type": "Link"},
		{"label": "IC Document Checklist Template", "link_type": "DocType", "link_to": "IC Document Checklist Template", "type": "Link"},
		{"label": "IC Project Record", "link_type": "DocType", "link_to": "IC Project Record", "type": "Link"},
		{"label": "Calendar & Planner", "type": "Card Break"},
		{"label": "Event", "link_type": "DocType", "link_to": "Event", "type": "Link"},
		{"label": "Task", "link_type": "DocType", "link_to": "Task", "type": "Link"},
		{"label": "HR & Profile", "type": "Card Break"},
		{"label": "Employee", "link_type": "DocType", "link_to": "Employee", "type": "Link"},
		{"label": "Attendance", "link_type": "DocType", "link_to": "Attendance", "type": "Link"},
		{"label": "IC Joining Letter", "link_type": "DocType", "link_to": "IC Joining Letter", "type": "Link"},
		{"label": "IC Employee Document", "link_type": "DocType", "link_to": "IC Employee Document", "type": "Link"},
		{"label": "Holiday List", "link_type": "DocType", "link_to": "Holiday List", "type": "Link"},
		{"label": "Assets", "type": "Card Break"},
		{"label": "Asset", "link_type": "DocType", "link_to": "Asset", "type": "Link"},
		{"label": "Asset Category", "link_type": "DocType", "link_to": "Asset Category", "type": "Link"},
		{"label": "Administration", "type": "Card Break"},
		{"label": "User", "link_type": "DocType", "link_to": "User", "type": "Link"},
		{"label": "Role", "link_type": "DocType", "link_to": "Role", "type": "Link"},
		{"label": "IC Settings", "link_type": "DocType", "link_to": "IC Settings", "type": "Link"},
	]

	# Filter Attendance if DocType missing (no HRMS)
	safe_links = []
	for link in links:
		if link.get("type") == "Card Break":
			safe_links.append(link)
			continue
		dt = link.get("link_to")
		if dt and not frappe.db.exists("DocType", dt):
			continue
		safe_links.append(link)

	payload = {
		"doctype": "Workspace",
		"name": name,
		"label": name,
		"title": name,
		"module": "Instacertify",
		"public": 1,
		"is_hidden": 0,
		"content": json.dumps(content),
		"shortcuts": shortcuts,
		"links": safe_links,
	}

	if frappe.db.exists("Workspace", name):
		ws = frappe.get_doc("Workspace", name)
		ws.update(payload)
		# clear child tables
		ws.shortcuts = []
		ws.links = []
		for s in shortcuts:
			ws.append("shortcuts", s)
		for l in safe_links:
			ws.append("links", l)
		ws.content = json.dumps(content)
		ws.save(ignore_permissions=True)
	else:
		ws = frappe.get_doc(payload)
		ws.insert(ignore_permissions=True)
