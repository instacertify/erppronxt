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
	name = "Home Dashboard"
	html = """
<div id="ic-home-root">
  <div class="ic-greeting">
    <h2 id="ic-greet-title">Welcome</h2>
    <div class="ic-datetime"><span id="ic-date"></span> · <span id="ic-time"></span></div>
  </div>
  <div class="ic-summary-grid" id="ic-summary-grid"></div>

  <div class="ic-workdesk-grid">
    <section class="ic-workdesk-panel">
      <div class="ic-workdesk-head">
        <div>
          <div class="ic-workdesk-title">My tasks</div>
          <div class="ic-workdesk-sub">Open work assigned to you</div>
        </div>
        <a class="ic-view-all" href="/app/task">All tasks</a>
      </div>
      <div id="ic-my-tasks"></div>
    </section>
    <section class="ic-workdesk-panel">
      <div class="ic-workdesk-head">
        <div>
          <div class="ic-workdesk-title">Calendar</div>
          <div class="ic-workdesk-sub">Upcoming 14 days</div>
        </div>
        <a class="ic-view-all" href="/app/event">Open calendar</a>
      </div>
      <div id="ic-my-calendar"></div>
    </section>
    <section class="ic-workdesk-panel">
      <div class="ic-workdesk-head">
        <div>
          <div class="ic-workdesk-title">My leads</div>
          <div class="ic-workdesk-sub">Owned by you</div>
        </div>
        <a class="ic-view-all" href="/app/lead">All leads</a>
      </div>
      <div id="ic-my-leads"></div>
    </section>
  </div>

  <div class="ic-lead-prompt-panel">
    <div class="ic-lead-prompt-header">
      <div>
        <div class="ic-lead-prompt-title">Lead contact prompts</div>
        <div class="ic-lead-prompt-sub">When to call · remarks · connected status</div>
      </div>
      <a class="ic-view-all" href="/app/lead">Open Leads</a>
    </div>
    <div id="ic-lead-prompts" class="ic-lead-prompt-list"></div>
  </div>

  <div class="ic-lead-prompt-panel" id="ic-helpdesk-panel">
    <div class="ic-lead-prompt-header">
      <div>
        <div class="ic-lead-prompt-title">Helpdesk</div>
        <div class="ic-lead-prompt-sub">Customer complaints · queries · open tickets</div>
      </div>
      <div>
        <a class="ic-view-all" href="/app/helpdesk-ticket/new" style="margin-right:12px;">Raise ticket</a>
        <a class="ic-view-all" href="/app/helpdesk-ticket">All tickets</a>
      </div>
    </div>
    <div id="ic-helpdesk-tickets" class="ic-lead-prompt-list"></div>
  </div>

  <div class="ic-lead-prompt-panel" id="ic-collab-panel">
    <div class="ic-lead-prompt-header">
      <div>
        <div class="ic-lead-prompt-title">Team Collaboration</div>
        <div class="ic-lead-prompt-sub">Project chats · discuss delivery with teammates</div>
      </div>
      <a class="ic-view-all" href="/app/team-collaboration">Open all chats</a>
    </div>
    <div id="ic-collab-recent" class="ic-lead-prompt-list"></div>
  </div>

  <div class="ic-hr-panel">
    <div class="ic-workdesk-head">
      <div>
        <div class="ic-workdesk-title">My HR</div>
        <div class="ic-workdesk-sub">Employment · joining letter · salary slips · documents</div>
      </div>
      <a class="ic-view-all" href="/app/employee">HR profile</a>
    </div>
    <div id="ic-hr-profile" class="ic-hr-profile"></div>
    <div class="ic-hr-columns">
      <div>
        <div class="ic-hr-col-title">Joining letters</div>
        <div id="ic-hr-joining"></div>
      </div>
      <div>
        <div class="ic-hr-col-title">Salary slips</div>
        <div id="ic-hr-slips"></div>
      </div>
      <div>
        <div class="ic-hr-col-title">Employment documents</div>
        <div id="ic-hr-docs"></div>
      </div>
    </div>
    <div id="ic-hr-links" class="ic-hr-links"></div>
  </div>

  <div class="ic-project-section-head">
    <h3>Ongoing Projects</h3>
    <a class="ic-view-all" href="/app/project-board">Open tile board</a>
  </div>
  <div class="ic-project-grid" id="ic-project-grid"></div>
</div>
"""
	script = """
(function() {
  function esc(v){ return frappe.utils.escape_html(v == null ? "" : String(v)); }
  function greet() {
    const hour = moment().hour();
    let g = "Good Evening";
    if (hour < 12) g = "Good Morning";
    else if (hour < 17) g = "Good Afternoon";
    return g + ", " + (frappe.session.user_fullname || "there");
  }
  function openKpi(label) {
    if (window.instacertify && typeof instacertify.open_kpi === "function") {
      instacertify.open_kpi(label);
      return;
    }
    const today = frappe.datetime.get_today();
    const week_start = frappe.datetime.add_days(today, -6);
    const deadline_end = frappe.datetime.add_days(today, 14);
    const amc_end = frappe.datetime.add_days(today, 31);
    const map = {
      "New Leads": ["Lead", {status: "Lead"}],
      "Active Leads": ["Lead", {status: ["in", ["Open", "Replied", "Opportunity"]]}],
      "Leads to Contact": ["Lead", {status: ["not in", ["Converted", "Do Not Contact"]], ic_next_contact_date: ["<=", today]}],
      "Pending Tasks": ["Task", {status: ["in", ["Open", "Working"]]}],
      "Open Tickets": ["Helpdesk Ticket", {status: ["in", ["Open", "In Progress", "Waiting on Customer"]]}],
      "Open Complaints": ["Helpdesk Ticket", {status: ["in", ["Open", "In Progress", "Waiting on Customer"]], ticket_type: "Complaint"}],
      "Quotations Sent": ["Quotation", {ic_workflow_status: ["in", ["Shared with Customer", "Customer Review"]]}],
      "Quotations Accepted": ["Quotation", {ic_workflow_status: "Accepted"}],
      "Active Projects": ["Project", {status: ["not in", ["Completed", "Cancelled"]]}],
      "Upcoming Deadlines": ["Project", {status: ["not in", ["Completed", "Cancelled"]], ic_deadline: ["<=", deadline_end]}],
      "Pending Documents": ["IC Document Request", {status: ["in", ["Sent to Customer", "Partially Uploaded"]]}],
      "Testing Requests": ["IC Testing Request", {status: ["not in", ["Report Shared with Customer"]]}],
      "AMC Due Soon": ["Project", {ic_requires_amc: 1, ic_amc_status: ["in", ["Scheduled", "Reminded"]], ic_amc_contact_date: ["<=", amc_end]}],
      "This Week": ["Lead", {creation: [">=", week_start]}],
      "Last 7 Days": ["Lead", {creation: [">=", week_start]}],
      "This Month": ["Lead", {creation: [">=", moment(today).startOf("month").format("YYYY-MM-DD")]}],
      "Last 30 Days": ["Lead", {creation: [">=", frappe.datetime.add_days(today, -29)]}],
    };
    const hit = map[label];
    if (!hit) {
      frappe.show_alert({message: "No list linked for " + label, indicator: "orange"});
      return;
    }
    frappe.route_options = hit[1] || {};
    frappe.set_route("List", hit[0]);
  }
  function bindKpiClicks(root) {
    (root || document).querySelectorAll(".ic-summary-card[data-kpi]").forEach((el) => {
      el.style.cursor = "pointer";
      el.onclick = function () { openKpi(el.getAttribute("data-kpi")); };
    });
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

  function empty(msg){ return "<div class='ic-lead-prompt-empty'>"+msg+"</div>"; }

  function projectTile(p) {
    if (window.instacertify && instacertify.project_tile_html) {
      return instacertify.project_tile_html(p);
    }
    const priority = p.priority || p.ic_priority || "Medium";
    const progress = Math.round(p.progress || 0);
    return `<article class="ic-project-tile priority-${esc(priority)}" data-name="${esc(p.name)}" onclick="frappe.set_route('Form','Project','${esc(p.name)}')">
      <h4 class="ic-project-tile-title">${esc(p.project_name || p.name)}</h4>
      <div class="ic-project-tile-customer">${esc(p.customer_name || p.customer || "-")}</div>
      <div class="ic-progress"><span style="width:${progress}%"></span></div>
    </article>`;
  }

  frappe.call({
    method: "instacertify.project.events.get_dashboard_counts",
    callback(r) {
      const data = r.message || {};
      const items = [
        ["New Leads", data.new_leads],
        ["Active Leads", data.active_leads],
        ["Leads to Contact", data.leads_to_contact, true],
        ["Pending Tasks", data.pending_tasks, true],
        ["Open Tickets", data.open_tickets, true],
        ["Open Complaints", data.open_complaints, true],
        ["Quotations Sent", data.quotations_sent],
        ["Quotations Accepted", data.quotations_accepted, true],
        ["Active Projects", data.active_projects],
        ["Upcoming Deadlines", data.upcoming_deadlines, true],
        ["Pending Documents", data.pending_documents],
        ["Testing Requests", data.testing_requests],
        ["AMC Due Soon", data.amc_due_soon, true],
      ];
      const grid = document.getElementById("ic-summary-grid");
      if (!grid) return;
      grid.innerHTML = items.map(([label, value, accent]) =>
        `<div class="ic-summary-card is-clickable ${accent ? "accent" : ""}" data-kpi="${frappe.utils.escape_html(label)}" title="Click to open list"><div class="label">${frappe.utils.escape_html(label)}</div><div class="value">${value ?? 0}</div></div>`
      ).join("");
      bindKpiClicks(grid);
    }
  });

  frappe.call({
    method: "instacertify.hr.dashboard.get_workdesk_insights",
    args: { limit: 8 },
    callback(r) {
      const d = r.message || {};
      const tasksEl = document.getElementById("ic-my-tasks");
      const calEl = document.getElementById("ic-my-calendar");
      const leadsEl = document.getElementById("ic-my-leads");
      if (tasksEl) {
        const rows = d.tasks || [];
        tasksEl.innerHTML = rows.length ? rows.map(t =>
          `<a class="ic-workdesk-row ${esc(t.urgency)}" href="/app/task/${encodeURIComponent(t.name)}">
            <div class="ic-workdesk-row-main">${esc(t.subject || t.name)}</div>
            <div class="ic-workdesk-row-meta"><span>${esc(t.status||"")}</span><span class="ic-lead-prompt-when ${esc(t.urgency)}">${esc(t.due_label)}</span></div>
          </a>`
        ).join("") : empty("No open tasks for you.");
      }
      if (calEl) {
        const rows = d.events || [];
        calEl.innerHTML = rows.length ? rows.map(e =>
          `<a class="ic-workdesk-row" href="/app/event/${encodeURIComponent(e.name)}">
            <div class="ic-workdesk-row-main">${esc(e.subject || e.name)}</div>
            <div class="ic-workdesk-row-meta"><span>${esc(e.when_label)}</span><span>${esc(e.time_label)}</span></div>
          </a>`
        ).join("") : empty("No upcoming events in the next 14 days.");
      }
      if (leadsEl) {
        const rows = d.my_leads || [];
        leadsEl.innerHTML = rows.length ? rows.map(l =>
          `<a class="ic-workdesk-row" href="/app/lead/${encodeURIComponent(l.name)}">
            <div class="ic-workdesk-row-main">${esc(l.title || l.name)}</div>
            <div class="ic-workdesk-row-meta"><span>${esc(l.status||"")}</span><span>${esc(l.ic_next_contact_date||"No contact date")}</span></div>
          </a>`
        ).join("") : empty("No active leads owned by you.");
      }
    }
  });

  frappe.call({
    method: "instacertify.crm.dashboard.get_lead_contact_prompts",
    args: { limit: 8 },
    callback(r) {
      const el = document.getElementById("ic-lead-prompts");
      if (!el) return;
      const d = r.message || {};
      const rows = d.prompts || [];
      if (!rows.length) {
        el.innerHTML = empty("No contact prompts yet. Set <b>Next Contact Date</b>, <b>Call Remarks</b>, and <b>Lead Connected</b> on a Lead.");
        return;
      }
      el.innerHTML = rows.map(row => {
        const title = esc(row.title || row.name);
        const when = esc(row.due_label || row.ic_next_contact_date || "—");
        const remarks = esc(row.ic_call_remarks || "No call remarks yet");
        const phone = esc(row.phone || "—");
        const connected = row.ic_lead_connected ? "Connected" : "Not connected";
        const connCls = row.ic_lead_connected ? "connected" : "not-connected";
        const urg = esc(row.urgency || "upcoming");
        return `<a class="ic-lead-prompt ${urg}" href="/app/lead/${encodeURIComponent(row.name)}">
          <div class="ic-lead-prompt-top">
            <div class="ic-lead-prompt-name">${title}</div>
            <span class="ic-lead-prompt-when ${urg}">${when}</span>
          </div>
          <div class="ic-lead-prompt-meta">
            <span class="ic-lead-prompt-connected ${connCls}">${connected}</span>
            <span class="ic-lead-prompt-phone">${phone}</span>
          </div>
          <div class="ic-lead-prompt-remarks">${remarks}</div>
        </a>`;
      }).join("");
    }
  });

  frappe.call({
    method: "instacertify.helpdesk.api.get_open_ticket_summary",
    args: { limit: 8 },
    callback(r) {
      const el = document.getElementById("ic-helpdesk-tickets");
      if (!el) return;
      const d = r.message || {};
      const rows = d.tickets || [];
      if (!rows.length) {
        el.innerHTML = empty("No open tickets. Raise a complaint or query from Customer, Lead, Project, or Helpdesk.");
        return;
      }
      el.innerHTML = rows.map(row => {
        const urg = (row.priority === "Urgent" || row.priority === "High") ? "overdue" : "upcoming";
        return `<a class="ic-lead-prompt ${urg}" href="/app/helpdesk-ticket/${encodeURIComponent(row.name)}">
          <div class="ic-lead-prompt-top">
            <div class="ic-lead-prompt-name">${esc(row.subject || row.name)}</div>
            <span class="ic-lead-prompt-when ${urg}">${esc(row.priority || "")}</span>
          </div>
          <div class="ic-lead-prompt-meta">
            <span class="ic-lead-prompt-connected">${esc(row.ticket_type || "")}</span>
            <span class="ic-lead-prompt-phone">${esc(row.status || "")}</span>
            <span>${esc(row.party || "")}</span>
          </div>
        </a>`;
      }).join("");
    }
  });

  frappe.call({
    method: "instacertify.collaboration.api.get_recent_chat_activity",
    args: { limit: 8 },
    callback(r) {
      const el = document.getElementById("ic-collab-recent");
      if (!el) return;
      const rows = (r.message && r.message.items) || [];
      if (!rows.length) {
        el.innerHTML = empty("No project chats yet. Open <a href='/app/team-collaboration'>Team Collaboration</a> or a Project to start discussing.");
        return;
      }
      el.innerHTML = rows.map(row => {
        return `<a class="ic-lead-prompt upcoming" href="/app/team-collaboration">
          <div class="ic-lead-prompt-top">
            <div class="ic-lead-prompt-name">${esc(row.project_name || row.project)}</div>
            <span class="ic-lead-prompt-when upcoming">${esc(row.time_label || "")}</span>
          </div>
          <div class="ic-lead-prompt-meta">
            <span class="ic-lead-prompt-connected">${esc(row.sender_name || "")}</span>
            <span class="ic-lead-prompt-phone">${esc(row.project || "")}</span>
          </div>
          <div class="ic-lead-prompt-remarks">${esc(row.plain || "")}</div>
        </a>`;
      }).join("");
      el.querySelectorAll("a.ic-lead-prompt").forEach((a, idx) => {
        a.addEventListener("click", (e) => {
          e.preventDefault();
          const row = rows[idx];
          frappe.route_options = { project: row.project };
          frappe.set_route("team-collaboration");
        });
      });
    }
  });

  frappe.call({
    method: "instacertify.hr.dashboard.get_my_hr_panel",
    callback(r) {
      const d = r.message || {};
      const profile = document.getElementById("ic-hr-profile");
      const joining = document.getElementById("ic-hr-joining");
      const slips = document.getElementById("ic-hr-slips");
      const docs = document.getElementById("ic-hr-docs");
      const links = document.getElementById("ic-hr-links");
      if (profile) {
        if (!d.employee) {
          profile.innerHTML = empty(esc(d.message || "Link your user to an Employee record to see HR documents."));
        } else {
          const e = d.employee;
          profile.innerHTML = `<div class="ic-hr-profile-card">
            <div class="ic-hr-name">${esc(e.employee_name)}</div>
            <div class="ic-hr-meta">${esc(e.designation || "—")} · ${esc(e.department || "—")}</div>
            <div class="ic-hr-meta">Joined ${esc(e.date_of_joining || "—")} · ${esc(e.status || "")}</div>
          </div>`;
        }
      }
      function docList(rows, emptyMsg, doctype) {
        if (!rows || !rows.length) return empty(emptyMsg);
        return rows.map(row => {
          const title = esc(row.document_title || row.employee_name || row.name);
          const meta = esc(row.issue_date || row.joining_date || row.document_type || "");
          const href = `/app/${frappe.router.slug(doctype)}/${encodeURIComponent(row.name)}`;
          const attach = row.attachment ? ` · <a href="${esc(row.attachment)}" target="_blank">Download</a>` : "";
          return `<a class="ic-workdesk-row" href="${href}"><div class="ic-workdesk-row-main">${title}</div><div class="ic-workdesk-row-meta"><span>${meta}</span>${attach}</div></a>`;
        }).join("");
      }
      if (joining) joining.innerHTML = docList(d.joining_letters, "No joining letter on file.", "IC Joining Letter");
      if (slips) slips.innerHTML = docList(d.salary_slips, "No salary slips uploaded yet.", "IC Employee Document");
      if (docs) docs.innerHTML = docList(d.documents, "No other employment documents.", "IC Employee Document");
      if (links) {
        links.innerHTML = (d.links || []).map(l =>
          `<a class="ic-hr-link" href="${esc(l.route)}">${esc(l.label)}</a>`
        ).join("");
      }
    }
  });

  frappe.call({
    method: "instacertify.project.events.get_ongoing_project_cards",
    args: {limit: 12},
    callback(r) {
      const grid = document.getElementById("ic-project-grid");
      if (!grid) return;
      const rows = r.message || [];
      if (!rows.length) {
        grid.innerHTML = "<div class='ic-project-empty'>No ongoing projects yet.</div>";
        return;
      }
      grid.innerHTML = rows.map(projectTile).join("");
      grid.querySelectorAll(".ic-project-tile").forEach((el) => {
        el.addEventListener("click", () => frappe.set_route("Form", "Project", el.getAttribute("data-name")));
      });
    }
  });
})();
"""
	_upsert_html_block(name, html, script)
	_ensure_crm_lead_tracker_block()


def _upsert_html_block(name, html, script):
	legacy = f"IC {name}" if not name.startswith("IC ") else None
	if legacy and frappe.db.exists("Custom HTML Block", legacy) and not frappe.db.exists("Custom HTML Block", name):
		try:
			frappe.rename_doc("Custom HTML Block", legacy, name, force=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Rename HTML block {legacy}")

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


def _ensure_crm_lead_tracker_block():
	name = "CRM Lead Tracker"
	html = """
<div id="ic-crm-tracker" class="ic-crm-tracker">
  <div class="ic-crm-tracker-title">CRM Lead Tracker</div>
  <div class="ic-summary-grid" id="ic-crm-kpi"></div>
  <div class="ic-crm-charts">
    <div class="ic-crm-chart-card"><div class="ic-crm-chart-label">This Week vs Last Week</div><div id="ic-crm-week-bar"></div></div>
    <div class="ic-crm-chart-card"><div class="ic-crm-chart-label">This Month vs Last Month</div><div id="ic-crm-month-bar"></div></div>
    <div class="ic-crm-chart-card"><div class="ic-crm-chart-label">Last 7 Days by Source</div><div id="ic-crm-source-7"></div></div>
    <div class="ic-crm-chart-card"><div class="ic-crm-chart-label">Last 30 Days by Project Type</div><div id="ic-crm-ptype-30"></div></div>
    <div class="ic-crm-chart-card"><div class="ic-crm-chart-label">Last 30 Days by Source</div><div id="ic-crm-source-30"></div></div>
    <div class="ic-crm-chart-card"><div class="ic-crm-chart-label">Last 30 Days by Status</div><div id="ic-crm-status-30"></div></div>
  </div>
  <div class="ic-crm-chart-card" style="margin-top:12px;min-height:auto;">
    <div class="ic-crm-chart-label">Lead contact prompts · When / Connected / Remarks</div>
    <div id="ic-crm-leads-contact"></div>
  </div>
  <div class="ic-crm-chart-card" style="margin-top:12px"><div class="ic-crm-chart-label">AMC Renewals Due (31 days)</div><div id="ic-crm-amc-due"></div></div>
</div>
"""
	script = """
(function() {
  function pctLabel(v) {
    const n = Number(v || 0);
    const arrow = n > 0 ? "▲" : (n < 0 ? "▼" : "•");
    return arrow + " " + Math.abs(n) + "%";
  }
  function makeChart(el, type, labels, values, colors) {
    if (!el) return;
    el.innerHTML = "";
    if (!(window.frappe && frappe.Chart)) {
      el.innerHTML = "<div class='text-muted'>Chart unavailable</div>";
      return;
    }
    if (!labels.length) {
      el.innerHTML = "<div class='text-muted'>No leads in this period</div>";
      return;
    }
    new frappe.Chart(el, {
      type: type,
      height: 220,
      data: {
        labels: labels,
        datasets: [{ name: "Leads", values: values }]
      },
      colors: colors || ["#065175", "#EC6820", "#2a9d8f", "#e9c46a", "#264653", "#f4a261"]
    });
  }
  frappe.call({
    method: "instacertify.crm.dashboard.get_lead_tracker_stats",
    callback(r) {
      const d = r.message || {};
      const kpi = document.getElementById("ic-crm-kpi");
      if (kpi) {
        const weekCls = (d.week_change_pct || 0) >= 0 ? "up" : "down";
        const monthCls = (d.month_change_pct || 0) >= 0 ? "up" : "down";
        kpi.innerHTML = [
          ["This Week", d.this_week],
          ["Last Week", d.last_week],
          ["Week Change", pctLabel(d.week_change_pct), weekCls],
          ["This Month", d.this_month],
          ["Last Month", d.last_month],
          ["Month Change", pctLabel(d.month_change_pct), monthCls],
          ["Last 7 Days", d.last_7_days],
          ["Last 30 Days", d.last_30_days, true],
        ].map(([label, value, extra]) => {
          const accent = extra === true ? "accent" : "";
          const trend = (extra === "up" || extra === "down") ? extra : "";
          const clickable = ["This Week", "This Month", "Last 7 Days", "Last 30 Days"].includes(label) ? "is-clickable" : "";
          const kpi = clickable ? ` data-kpi="${frappe.utils.escape_html(label)}" title="Click to open leads"` : "";
          return `<div class="ic-summary-card ${accent} ${trend} ${clickable}"${kpi}><div class="label">${label}</div><div class="value" style="font-size:${typeof value==='string'?'1.15rem':'1.6rem'}">${value ?? 0}</div></div>`;
        }).join("");
        if (window.instacertify && instacertify.bind_summary_card_clicks) {
          instacertify.bind_summary_card_clicks(kpi);
        } else {
          kpi.querySelectorAll(".ic-summary-card[data-kpi]").forEach((el) => {
            el.style.cursor = "pointer";
            el.onclick = () => {
              if (window.instacertify && instacertify.open_kpi) instacertify.open_kpi(el.getAttribute("data-kpi"));
            };
          });
        }
      }
      const week = d.week_compare || [];
      makeChart(document.getElementById("ic-crm-week-bar"), "bar", week.map(x=>x.label), week.map(x=>x.count), ["#065175", "#8fb6c9"]);
      const month = d.month_compare || [];
      makeChart(document.getElementById("ic-crm-month-bar"), "bar", month.map(x=>x.label), month.map(x=>x.count), ["#EC6820", "#f3b48d"]);
      const s7 = d.by_source_7d || [];
      makeChart(document.getElementById("ic-crm-source-7"), "pie", s7.map(x=>x.label), s7.map(x=>x.count));
      const p30 = d.by_project_type_30d || [];
      makeChart(document.getElementById("ic-crm-ptype-30"), "pie", p30.map(x=>x.label), p30.map(x=>x.count));
      const s30 = d.by_source_30d || [];
      makeChart(document.getElementById("ic-crm-source-30"), "donut", s30.map(x=>x.label), s30.map(x=>x.count));
      const st30 = d.by_status_30d || [];
      makeChart(document.getElementById("ic-crm-status-30"), "bar", st30.map(x=>x.label), st30.map(x=>x.count));
      (function renderFollowups(){
        const el = document.getElementById("ic-crm-leads-contact");
        const rows = d.leads_to_contact || [];
        if (el) {
          if (!rows.length) {
            el.innerHTML = "<div class='ic-lead-prompt-empty'>No leads due. Set Next Contact Date + Call Remarks on Leads.</div>";
          } else {
            el.innerHTML = "<table class='ic-related-table'><thead><tr><th>Lead</th><th>When</th><th>Phone</th><th>Connected</th><th>Call remarks</th></tr></thead><tbody>" +
              rows.map(r => {
                const title = r.title || r.ic_party_name || r.company_name || r.lead_name || r.name;
                const when = r.due_label || r.ic_next_contact_date || "—";
                const connected = r.ic_lead_connected ? "<span class='ic-lead-prompt-connected connected'>Connected</span>" : "<span class='ic-lead-prompt-connected not-connected'>Not connected</span>";
                return "<tr><td><a href='/app/lead/"+encodeURIComponent(r.name)+"'>"+frappe.utils.escape_html(title)+"</a></td><td><span class='ic-lead-prompt-when "+frappe.utils.escape_html(r.urgency||'')+"'>"+frappe.utils.escape_html(when)+"</span></td><td>"+frappe.utils.escape_html(r.phone||r.mobile_no||"—")+"</td><td>"+connected+"</td><td>"+frappe.utils.escape_html(r.ic_call_remarks||"—")+"</td></tr>";
              }).join("") + "</tbody></table>";
          }
        }
        const amc = document.getElementById("ic-crm-amc-due");
        const arows = d.amc_due || [];
        if (amc) {
          if (!arows.length) amc.innerHTML = "<div class='text-muted'>No AMC renewals due</div>";
          else amc.innerHTML = "<table class='ic-related-table'><thead><tr><th>Project</th><th>Customer</th><th>Contact Date</th><th>Status</th></tr></thead><tbody>" +
            arows.map(a => "<tr><td><a href='/app/project/"+encodeURIComponent(a.name)+"'>"+frappe.utils.escape_html(a.project_name||a.name)+"</a></td><td>"+frappe.utils.escape_html(a.customer||"—")+"</td><td>"+frappe.utils.escape_html(a.ic_amc_contact_date||"—")+"</td><td>"+frappe.utils.escape_html(a.ic_amc_status||"—")+"</td></tr>").join("") + "</tbody></table>";
        }
      })();
    }
  });
})();
"""
	_upsert_html_block(name, html, script)


def _ensure_home_workspace():
	name = "Instacertify Home"
	content = [
		{"id": "ic_home_block", "type": "custom_block", "data": {"custom_block_name": "Home Dashboard", "col": 12}},
		{"id": "ic_header", "type": "header", "data": {"text": "<span class=\"h4\"><b>Instacertify Home</b></span>", "col": 12}},
		{"id": "ic_spacer1", "type": "spacer", "data": {"col": 12}},
		{"id": "ic_crm_header", "type": "header", "data": {"text": "<span class=\"h5\">CRM Lead Tracker</span>", "col": 12}},
		{"id": "ic_crm_block", "type": "custom_block", "data": {"custom_block_name": "CRM Lead Tracker", "col": 12}},
		{"id": "nc_leads_week", "type": "number_card", "data": {"number_card_name": "Leads This Week", "col": 3}},
		{"id": "nc_leads_month", "type": "number_card", "data": {"number_card_name": "Leads This Month", "col": 3}},
		{"id": "nc_new_leads", "type": "number_card", "data": {"number_card_name": "New Leads", "col": 3}},
		{"id": "nc_active_leads", "type": "number_card", "data": {"number_card_name": "Active Leads", "col": 3}},
		{"id": "ic_cards_header", "type": "header", "data": {"text": "<span class=\"h5\">Operations Snapshot</span>", "col": 12}},
		{"id": "nc_quotes_sent", "type": "number_card", "data": {"number_card_name": "Quotations Sent", "col": 3}},
		{"id": "nc_quotes_accepted", "type": "number_card", "data": {"number_card_name": "Quotations Accepted", "col": 3}},
		{"id": "nc_active_projects", "type": "number_card", "data": {"number_card_name": "Active Projects", "col": 3}},
		{"id": "nc_pending_tasks", "type": "number_card", "data": {"number_card_name": "Pending Tasks", "col": 3}},
		{"id": "nc_open_tickets", "type": "number_card", "data": {"number_card_name": "Open Tickets", "col": 3}},
		{"id": "nc_pending_docs", "type": "number_card", "data": {"number_card_name": "Pending Documents", "col": 3}},
		{"id": "nc_leads_contact", "type": "number_card", "data": {"number_card_name": "Leads to Contact", "col": 3}},
		{"id": "nc_testing", "type": "number_card", "data": {"number_card_name": "Testing Requests", "col": 3}},
		{"id": "nc_deadlines", "type": "number_card", "data": {"number_card_name": "Upcoming Deadlines", "col": 3}},
		{"id": "nc_amc", "type": "number_card", "data": {"number_card_name": "AMC Due Soon", "col": 3}},
		{"id": "ic_samples_header", "type": "header", "data": {"text": "<span class=\"h5\">Sample Custody</span>", "col": 12}},
		{"id": "nc_smp_transit_office", "type": "number_card", "data": {"number_card_name": "Samples Transit to Office", "col": 2}},
		{"id": "nc_smp_office", "type": "number_card", "data": {"number_card_name": "Samples At Office", "col": 2}},
		{"id": "nc_smp_transit_lab", "type": "number_card", "data": {"number_card_name": "Samples Transit to Lab", "col": 2}},
		{"id": "nc_smp_lab", "type": "number_card", "data": {"number_card_name": "Samples At Laboratory", "col": 2}},
		{"id": "nc_smp_storage", "type": "number_card", "data": {"number_card_name": "Samples In Storage", "col": 2}},
		{"id": "nc_smp_discarded", "type": "number_card", "data": {"number_card_name": "Samples Discarded", "col": 2}},
		{"id": "ic_charts_header", "type": "header", "data": {"text": "<span class=\"h5\">Insights</span>", "col": 12}},
		{"id": "chart_leads_7d_source", "type": "chart", "data": {"chart_name": "Leads Last 7 Days by Source", "col": 6}},
		{"id": "chart_leads_30d_ptype", "type": "chart", "data": {"chart_name": "Leads Last 30 Days by Project Type", "col": 6}},
		{"id": "chart_leads_30d_source", "type": "chart", "data": {"chart_name": "Leads Last 30 Days by Source", "col": 6}},
		{"id": "chart_leads_status", "type": "chart", "data": {"chart_name": "Leads by Status", "col": 6}},
		{"id": "chart_lead_trend", "type": "chart", "data": {"chart_name": "Lead Trend Weekly", "col": 12}},
		{"id": "chart_quotes_status", "type": "chart", "data": {"chart_name": "Quotations by Status", "col": 6}},
		{"id": "chart_projects_status", "type": "chart", "data": {"chart_name": "Projects by Status", "col": 6}},
		{"id": "chart_projects_priority", "type": "chart", "data": {"chart_name": "Projects by Priority", "col": 6}},
		{"id": "chart_samples_location", "type": "chart", "data": {"chart_name": "Samples by Location", "col": 6}},
		{"id": "ic_shortcuts_header", "type": "header", "data": {"text": "<span class=\"h5\">Quick Links</span>", "col": 12}},
		{"id": "sc_leads", "type": "shortcut", "data": {"shortcut_name": "Leads", "col": 3}},
		{"id": "sc_customers", "type": "shortcut", "data": {"shortcut_name": "Customers", "col": 3}},
		{"id": "sc_quotations", "type": "shortcut", "data": {"shortcut_name": "Quotations", "col": 3}},
		{"id": "sc_projects", "type": "shortcut", "data": {"shortcut_name": "Projects", "col": 3}},
		{"id": "sc_project_board", "type": "shortcut", "data": {"shortcut_name": "Project Board", "col": 3}},
		{"id": "sc_collab", "type": "shortcut", "data": {"shortcut_name": "Team Collaboration", "col": 3}},
		{"id": "sc_testing", "type": "shortcut", "data": {"shortcut_name": "Testing Requests", "col": 3}},
		{"id": "sc_labs", "type": "shortcut", "data": {"shortcut_name": "Laboratories", "col": 3}},
		{"id": "sc_samples", "type": "shortcut", "data": {"shortcut_name": "Samples", "col": 3}},
		{"id": "sc_docs", "type": "shortcut", "data": {"shortcut_name": "Document Requests", "col": 3}},
		{"id": "sc_helpdesk", "type": "shortcut", "data": {"shortcut_name": "Helpdesk", "col": 3}},
		{"id": "sc_sales_invoice", "type": "shortcut", "data": {"shortcut_name": "Sales Invoice", "col": 3}},
		{"id": "sc_purchase_invoice", "type": "shortcut", "data": {"shortcut_name": "Purchase Invoice", "col": 3}},
		{"id": "sc_asset", "type": "shortcut", "data": {"shortcut_name": "Asset", "col": 3}},
		{"id": "sc_gstr1", "type": "shortcut", "data": {"shortcut_name": "GSTR-1", "col": 3}},
		{"id": "sc_gstr3b", "type": "shortcut", "data": {"shortcut_name": "GSTR-3B", "col": 3}},
		{"id": "sc_gst_settings", "type": "shortcut", "data": {"shortcut_name": "GST Settings", "col": 3}},
	]


	shortcuts = [
		{"label": "Leads", "link_to": "Lead", "type": "DocType", "doc_view": "List"},
		{"label": "Customers", "link_to": "Customer", "type": "DocType", "doc_view": "List"},
		{"label": "Quotations", "link_to": "Quotation", "type": "DocType", "doc_view": "List"},
		{"label": "Projects", "link_to": "Project", "type": "DocType", "doc_view": "List"},
		{"label": "Project Board", "link_to": "project-board", "type": "Page"},
		{"label": "Team Collaboration", "link_to": "team-collaboration", "type": "Page"},
		{"label": "Testing Requests", "link_to": "IC Testing Request", "type": "DocType", "doc_view": "List"},
		{"label": "Laboratories", "link_to": "IC Laboratory", "type": "DocType", "doc_view": "List"},
		{"label": "Samples", "link_to": "IC Sample Tracking", "type": "DocType", "doc_view": "List"},
		{"label": "Document Requests", "link_to": "IC Document Request", "type": "DocType", "doc_view": "List"},
		{"label": "Helpdesk", "link_to": "Helpdesk Ticket", "type": "DocType", "doc_view": "List"},
		{"label": "Sales Invoice", "link_to": "Sales Invoice", "type": "DocType", "doc_view": "List"},
		{"label": "Purchase Invoice", "link_to": "Purchase Invoice", "type": "DocType", "doc_view": "List"},
		{"label": "Asset", "link_to": "Asset", "type": "DocType", "doc_view": "List"},
		{"label": "GSTR-1", "link_to": "GSTR-1", "type": "DocType", "doc_view": ""},
		{"label": "GSTR-3B", "link_to": "GSTR 3B Report", "type": "DocType", "doc_view": "List"},
		{"label": "GST Settings", "link_to": "GST Settings", "type": "DocType", "doc_view": ""},
	]

	links = [
		{"label": "CRM", "type": "Card Break"},
		{"label": "Lead", "link_type": "DocType", "link_to": "Lead", "type": "Link"},
		{"label": "Opportunity", "link_type": "DocType", "link_to": "Opportunity", "type": "Link"},
		{"label": "Consultant Referral", "link_type": "DocType", "link_to": "Consultant Referral", "type": "Link"},
		{"label": "Lead Sources (edit)", "link_type": "DocType", "link_to": "IC Lead Source", "type": "Link"},
		{"label": "Project Types (edit)", "link_type": "DocType", "link_to": "IC Project Type", "type": "Link"},
		{"label": "Helpdesk", "type": "Card Break"},
		{"label": "Helpdesk Tickets", "link_type": "DocType", "link_to": "Helpdesk Ticket", "type": "Link"},
		{"label": "Raise Complaint / Ticket", "link_type": "DocType", "link_to": "Helpdesk Ticket", "type": "Link"},
		{"label": "Classic Issue (ERPNext)", "link_type": "DocType", "link_to": "Issue", "type": "Link"},
		{"label": "Customers", "type": "Card Break"},
		{"label": "Customer", "link_type": "DocType", "link_to": "Customer", "type": "Link"},
		{"label": "Contact", "link_type": "DocType", "link_to": "Contact", "type": "Link"},
		{"label": "Address", "link_type": "DocType", "link_to": "Address", "type": "Link"},
		{"label": "Sales", "type": "Card Break"},
		{"label": "Quotation", "link_type": "DocType", "link_to": "Quotation", "type": "Link"},
		{"label": "Quotation Templates", "link_type": "DocType", "link_to": "IC Quotation Template", "type": "Link"},
		{"label": "New Consulting Template", "link_type": "DocType", "link_to": "IC Quotation Template", "type": "Link"},
		{"label": "GST & Invoicing", "type": "Card Break"},
		{"label": "Sales Invoice (sell services to customer)", "link_type": "DocType", "link_to": "Sales Invoice", "type": "Link"},
		{"label": "Purchase Invoice (buy lab services)", "link_type": "DocType", "link_to": "Purchase Invoice", "type": "Link"},
		{"label": "Supplier (labs / vendors)", "link_type": "DocType", "link_to": "Supplier", "type": "Link"},
		{"label": "Asset (org purchases)", "link_type": "DocType", "link_to": "Asset", "type": "Link"},
		{"label": "Item (non-stock services)", "link_type": "DocType", "link_to": "Item", "type": "Link"},
		{"label": "Payment Entry", "link_type": "DocType", "link_to": "Payment Entry", "type": "Link"},
		{"label": "GSTR-1 (Generate / File)", "link_type": "DocType", "link_to": "GSTR-1", "type": "Link"},
		{"label": "GSTR-3B (Generate / File)", "link_type": "DocType", "link_to": "GSTR 3B Report", "type": "Link"},
		{"label": "GST Return Log", "link_type": "DocType", "link_to": "GST Return Log", "type": "Link"},
		{"label": "GST Settings", "link_type": "DocType", "link_to": "GST Settings", "type": "Link"},
		{"label": "GSTR-3B Details", "link_type": "Report", "link_to": "GSTR-3B Details", "type": "Link", "is_query_report": 1},
		{"label": "Projects", "type": "Card Break"},
		{"label": "Project", "link_type": "DocType", "link_to": "Project", "type": "Link"},
		{"label": "Project Board (tiles)", "link_type": "Page", "link_to": "project-board", "type": "Link"},
		{"label": "Team Collaboration", "link_type": "Page", "link_to": "team-collaboration", "type": "Link"},
		{"label": "Task", "link_type": "DocType", "link_to": "Task", "type": "Link"},
		{"label": "Team Chat Messages", "link_type": "DocType", "link_to": "Project Chat Message", "type": "Link"},
		{"label": "Project Updates", "link_type": "DocType", "link_to": "IC Project Update", "type": "Link"},
		{"label": "Timesheet", "link_type": "DocType", "link_to": "Timesheet", "type": "Link"},
		{"label": "Testing", "type": "Card Break"},
		{"label": "Testing Requests", "link_type": "DocType", "link_to": "IC Testing Request", "type": "Link"},
		{"label": "Sample Tracking", "link_type": "DocType", "link_to": "IC Sample Tracking", "type": "Link"},
		{"label": "Laboratory Library", "type": "Card Break"},
		{"label": "Register / Manage Labs", "link_type": "DocType", "link_to": "IC Laboratory", "type": "Link"},
		{"label": "Testing Requests", "link_type": "DocType", "link_to": "IC Testing Request", "type": "Link"},
		{"label": "Documents", "type": "Card Break"},
		{"label": "Document Requests (customer uploads)", "link_type": "DocType", "link_to": "IC Document Request", "type": "Link"},
		{"label": "Document Checklist Templates", "link_type": "DocType", "link_to": "IC Document Checklist Template", "type": "Link"},
		{"label": "Project Records", "link_type": "DocType", "link_to": "IC Project Record", "type": "Link"},
		{"label": "Calendar & Planner", "type": "Card Break"},
		{"label": "Event", "link_type": "DocType", "link_to": "Event", "type": "Link"},
		{"label": "Task", "link_type": "DocType", "link_to": "Task", "type": "Link"},
		{"label": "My HR & Employment", "type": "Card Break"},
		{"label": "My Employee Profile", "link_type": "DocType", "link_to": "Employee", "type": "Link"},
		{"label": "Joining Letters", "link_type": "DocType", "link_to": "IC Joining Letter", "type": "Link"},
		{"label": "Salary Slips & Documents", "link_type": "DocType", "link_to": "IC Employee Document", "type": "Link"},
		{"label": "Attendance", "link_type": "DocType", "link_to": "Attendance", "type": "Link"},
		{"label": "Holiday List", "link_type": "DocType", "link_to": "Holiday List", "type": "Link"},
		{"label": "Event Calendar", "link_type": "DocType", "link_to": "Event", "type": "Link"},
		{"label": "Assets", "type": "Card Break"},
		{"label": "Asset", "link_type": "DocType", "link_to": "Asset", "type": "Link"},
		{"label": "Asset Category", "link_type": "DocType", "link_to": "Asset Category", "type": "Link"},
		{"label": "Administration", "type": "Card Break"},
		{"label": "User", "link_type": "DocType", "link_to": "User", "type": "Link"},
		{"label": "Role", "link_type": "DocType", "link_to": "Role", "type": "Link"},
		{"label": "Settings", "link_type": "DocType", "link_to": "IC Settings", "type": "Link"},
	]

	# Filter missing DocTypes / Reports / Pages
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
		elif link_type == "Page":
			if dt and not frappe.db.exists("Page", dt):
				continue
		elif dt and not frappe.db.exists("DocType", dt):
			continue
		safe_links.append(link)

	safe_shortcuts = []
	for s in shortcuts:
		dt = s.get("link_to")
		stype = s.get("type") or "DocType"
		if stype == "Page":
			if dt and not frappe.db.exists("Page", dt):
				continue
		elif dt and not frappe.db.exists("DocType", dt):
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
		ws.append("custom_blocks", {"custom_block_name": "Home Dashboard", "label": "Home Dashboard"})
		ws.content = json.dumps(content)
		ws.save(ignore_permissions=True)
	else:
		ws = frappe.get_doc(payload)
		ws.append("custom_blocks", {"custom_block_name": "Home Dashboard", "label": "Home Dashboard"})
		ws.insert(ignore_permissions=True)
