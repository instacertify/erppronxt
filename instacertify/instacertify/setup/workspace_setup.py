# Copyright (c) Instacertify
"""Workspace and navigation setup."""

from __future__ import annotations

import json

import frappe


def ensure_workspaces():
	_ensure_home_html_block()
	_ensure_home_workspace()
	from instacertify.setup.gst_returns import ensure_gst_returns_access

	ensure_gst_returns_access()


def _ensure_home_html_block():
	name = "IC Home Dashboard"
	html = """
<div id="ic-home-root">
  <div class="ic-greeting">
    <h2 id="ic-greet-title">Welcome</h2>
    <div class="ic-datetime"><span id="ic-date"></span> · <span id="ic-time"></span></div>
  </div>
  <div class="ic-summary-grid" id="ic-summary-grid"></div>
  <div style="margin:8px 0 10px;color:#065175;font-weight:600;">Ongoing Projects</div>
  <div class="ic-project-grid" id="ic-project-grid"></div>
</div>
"""
	script = """
(function() {
  function greet() {
    const hour = moment().hour();
    let g = "Good Evening";
    if (hour < 12) g = "Good Morning";
    else if (hour < 17) g = "Good Afternoon";
    return g + ", " + (frappe.session.user_fullname || "there");
  }
  function refreshClock() {
    const t = document.getElementById("ic-greet-title");
    const d = document.getElementById("ic-date");
    const tm = document.getElementById("ic-time");
    if (t) t.textContent = greet();
    if (d) d.textContent = moment().format("dddd, D MMMM YYYY");
    if (tm) tm.textContent = moment().format("h:mm A");
  }
  refreshClock();
  setInterval(refreshClock, 30000);
  frappe.call({
    method: "instacertify.project.events.get_dashboard_counts",
    callback(r) {
      const data = r.message || {};
      const items = [
        ["New Leads", data.new_leads],
        ["Active Leads", data.active_leads],
        ["Quotations Sent", data.quotations_sent],
        ["Awaiting Response", data.quotations_awaiting],
        ["Quotations Accepted", data.quotations_accepted, true],
        ["Active Projects", data.active_projects],
        ["Pending Tasks", data.pending_tasks],
        ["Pending Documents", data.pending_documents],
        ["Testing Requests", data.testing_requests],
        ["Upcoming Deadlines", data.upcoming_deadlines, true],
      ];
      const grid = document.getElementById("ic-summary-grid");
      if (!grid) return;
      grid.innerHTML = items.map(([label, value, accent]) =>
        `<div class="ic-summary-card ${accent ? "accent" : ""}"><div class="label">${label}</div><div class="value">${value ?? 0}</div></div>`
      ).join("");
    }
  });
  frappe.call({
    method: "instacertify.project.events.get_ongoing_project_cards",
    args: {limit: 8},
    callback(r) {
      const grid = document.getElementById("ic-project-grid");
      if (!grid) return;
      grid.innerHTML = (r.message || []).map(p => {
        const priority = p.ic_priority || "Medium";
        const progress = Math.round(p.progress || 0);
        const deadline = p.deadline ? frappe.datetime.str_to_user(p.deadline) : "-";
        return `<div class="ic-project-card priority-${frappe.utils.escape_html(priority)}" onclick="frappe.set_route('Form','Project','${p.name}')">
          <h4>${frappe.utils.escape_html(p.project_name || p.name)}</h4>
          <div class="meta"><b>Customer:</b> ${frappe.utils.escape_html(p.customer_name || p.customer || "-")}</div>
          <div class="meta"><b>Priority:</b> <span class="ic-badge ${priority.toLowerCase()}">${frappe.utils.escape_html(priority)}</span></div>
          <div class="meta"><b>Status:</b> ${frappe.utils.escape_html(p.ic_project_stage || p.status || "-")}</div>
          <div class="ic-progress"><span style="width:${progress}%"></span></div>
          <div class="meta"><b>Progress:</b> ${progress}%</div>
          <div class="meta"><b>Pending:</b> ${frappe.utils.escape_html(p.ic_pending_action || "-")}</div>
          <div class="meta"><b>Assigned:</b> ${frappe.utils.escape_html(p.ic_assigned_employee || "-")}</div>
          <div class="meta"><b>Deadline:</b> ${deadline}</div>
        </div>`;
      }).join("");
    }
  });
})();
"""
	if frappe.db.exists("Custom HTML Block", name):
		doc = frappe.get_doc("Custom HTML Block", name)
		doc.html = html
		doc.script = script
		doc.private = 0
		doc.save(ignore_permissions=True)
	else:
		frappe.get_doc(
			{
				"doctype": "Custom HTML Block",
				"name": name,
				"html": html,
				"script": script,
				"private": 0,
			}
		).insert(ignore_permissions=True)


def _ensure_home_workspace():
	name = "Instacertify Home"
	content = [
		{"id": "ic_home_block", "type": "custom_block", "data": {"custom_block_name": "IC Home Dashboard", "col": 12}},
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
		{"id": "sc_sales_invoice", "type": "shortcut", "data": {"shortcut_name": "Sales Invoice", "col": 3}},
		{"id": "sc_gstr1", "type": "shortcut", "data": {"shortcut_name": "GSTR-1", "col": 3}},
		{"id": "sc_gstr3b", "type": "shortcut", "data": {"shortcut_name": "GSTR-3B", "col": 3}},
		{"id": "sc_gst_settings", "type": "shortcut", "data": {"shortcut_name": "GST Settings", "col": 3}},
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
		{"label": "Sales Invoice", "link_to": "Sales Invoice", "type": "DocType", "doc_view": "List"},
		{"label": "GSTR-1", "link_to": "GSTR-1", "type": "DocType", "doc_view": ""},
		{"label": "GSTR-3B", "link_to": "GSTR 3B Report", "type": "DocType", "doc_view": "List"},
		{"label": "GST Settings", "link_to": "GST Settings", "type": "DocType", "doc_view": ""},
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
		{"label": "Quotation Templates", "link_type": "DocType", "link_to": "IC Quotation Template", "type": "Link"},
		{"label": "New Consulting Template", "link_type": "DocType", "link_to": "IC Quotation Template", "type": "Link"},
		{"label": "GST & Invoicing", "type": "Card Break"},
		{"label": "Sales Invoice", "link_type": "DocType", "link_to": "Sales Invoice", "type": "Link"},
		{"label": "Payment Entry", "link_type": "DocType", "link_to": "Payment Entry", "type": "Link"},
		{"label": "GSTR-1 (Generate / File)", "link_type": "DocType", "link_to": "GSTR-1", "type": "Link"},
		{"label": "GSTR-3B (Generate / File)", "link_type": "DocType", "link_to": "GSTR 3B Report", "type": "Link"},
		{"label": "GST Return Log", "link_type": "DocType", "link_to": "GST Return Log", "type": "Link"},
		{"label": "GST Settings", "link_type": "DocType", "link_to": "GST Settings", "type": "Link"},
		{"label": "GSTR-3B Details", "link_type": "Report", "link_to": "GSTR-3B Details", "type": "Link", "is_query_report": 1},
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

	# Filter missing DocTypes / Reports
	safe_links = []
	for link in links:
		if link.get("type") == "Card Break":
			safe_links.append(link)
			continue
		dt = link.get("link_to")
		link_type = link.get("link_type") or "DocType"
		if link_type == "Report":
			if dt and not frappe.db.exists("Report", dt):
				continue
		elif dt and not frappe.db.exists("DocType", dt):
			continue
		safe_links.append(link)

	safe_shortcuts = []
	for s in shortcuts:
		dt = s.get("link_to")
		if dt and not frappe.db.exists("DocType", dt):
			continue
		safe_shortcuts.append(s)

	payload = {
		"doctype": "Workspace",
		"name": name,
		"label": name,
		"title": name,
		"module": "Instacertify",
		"public": 1,
		"is_hidden": 0,
		"content": json.dumps(content),
		"shortcuts": safe_shortcuts,
		"links": safe_links,
	}

	if frappe.db.exists("Workspace", name):
		ws = frappe.get_doc("Workspace", name)
		ws.update(payload)
		# clear child tables
		ws.shortcuts = []
		ws.links = []
		ws.custom_blocks = []
		for s in safe_shortcuts:
			ws.append("shortcuts", s)
		for l in safe_links:
			ws.append("links", l)
		ws.append("custom_blocks", {"custom_block_name": "IC Home Dashboard", "label": "IC Home Dashboard"})
		ws.content = json.dumps(content)
		ws.save(ignore_permissions=True)
	else:
		ws = frappe.get_doc(payload)
		ws.append("custom_blocks", {"custom_block_name": "IC Home Dashboard", "label": "IC Home Dashboard"})
		ws.insert(ignore_permissions=True)
