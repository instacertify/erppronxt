# Copyright (c) Instacertify
"""Workspace and navigation setup."""

from __future__ import annotations

import json

import frappe


def ensure_workspaces():
	_ensure_home_html_block()
	_ensure_home_workspace()
	ensure_hrms_expenses_workspace()
	from instacertify.setup.gst_returns import ensure_gst_returns_access

	ensure_gst_returns_access()
	from instacertify.setup.navigation_icons import ensure_navigation_icons

	ensure_navigation_icons()


def _ensure_home_html_block():
	name = "Home Dashboard"
	html = """
<div id="ic-home-root">
  <div class="ic-greeting">
    <div class="ic-greeting-brand">Insta<span>certify</span></div>
    <h2 id="ic-greet-title">Welcome</h2>
    <div class="ic-datetime"><span id="ic-date"></span> · <span id="ic-time"></span></div>
  </div>

  <div class="ic-explore-panel" id="ic-explore-panel">
    <div class="ic-explore-head">
      <div>
        <div class="ic-explore-title">Explore Instacertify</div>
        <div class="ic-explore-sub" id="ic-explore-hint">Organised in tiles — tap any square to open</div>
      </div>
    </div>
    <div class="ic-explore-grid" id="ic-explore-grid"></div>
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
          <div class="ic-workdesk-title">Team calendar</div>
          <div class="ic-workdesk-sub">Sessions · book for teammates · 30‑min alerts</div>
        </div>
        <div style="display:flex;gap:8px;align-items:center;">
          <a class="ic-view-all ic-schedule-session" href="/app/event/new">Schedule session</a>
          <a class="ic-view-all" href="/app/event/view/calendar">Open calendar</a>
        </div>
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

  <div class="ic-lead-prompt-panel ic-lead-hub" id="ic-lead-hub">
    <div class="ic-lead-prompt-header">
      <div>
        <div class="ic-lead-prompt-title">Lead reminder hub</div>
        <div class="ic-lead-prompt-sub">Whom to call · who to connect with · customer remarks</div>
      </div>
      <div class="ic-lead-hub-actions">
        <span class="ic-lead-hub-counts" id="ic-lead-hub-counts"></span>
        <a class="ic-view-all" href="/app/lead">Open Leads</a>
      </div>
    </div>
    <div class="ic-lead-hub-legend">
      <span class="ic-lead-hub-chip overdue">Overdue / today</span>
      <span class="ic-lead-hub-chip upcoming">Upcoming</span>
      <span class="ic-lead-hub-chip tip">Tap a card to open the lead and log remarks</span>
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
    (root || root_element).querySelectorAll(".ic-summary-card[data-kpi]").forEach((el) => {
      el.style.cursor = "pointer";
      el.onclick = function () { openKpi(el.getAttribute("data-kpi")); };
    });
  }
  function refreshClock() {
    const t = root_element.getElementById("ic-greet-title");
    const d = root_element.getElementById("ic-date");
    const tm = root_element.getElementById("ic-time");
    if (t) t.textContent = greet();
    if (d) d.textContent = moment().format("dddd, D MMMM YYYY");
    if (tm) tm.textContent = moment().format("h:mm A");
  }
  refreshClock();
  setInterval(refreshClock, 30000);

  function empty(msg){ return "<div class='ic-lead-prompt-empty'>"+msg+"</div>"; }

  function openExploreCard(card) {
    if (!card) return;
    if (card.action === "upload_quote_format" && window.instacertify && instacertify.open_quote_format_upload) {
      instacertify.open_quote_format_upload();
      return;
    }
    if (card.action === "upload_laboratory" && window.instacertify && instacertify.open_laboratory_upload) {
      instacertify.open_laboratory_upload();
      return;
    }
    if (card.action === "new_expense") {
      if (window.instacertify && typeof instacertify.open_expense_file === "function") {
        instacertify.open_expense_file();
        return;
      }
      // Self-contained fallback dialog (shadow Home may load before app JS)
      const ed = new frappe.ui.Dialog({
        title: "File an Expense",
        fields: [
          {fieldname:"title", fieldtype:"Data", label:"Title", reqd:1},
          {fieldname:"category", fieldtype:"Select", label:"Category",
            options:"Travel\\nPetty Cash\\nOffice\\nConveyance\\nLodging\\nMeals\\nCommunication\\nOther",
            reqd:1, default:"Travel"},
          {fieldname:"expense_date", fieldtype:"Date", label:"Expense Date", reqd:1, default: frappe.datetime.get_today()},
          {fieldname:"amount", fieldtype:"Currency", label:"Amount", reqd:1},
          {fieldname:"description", fieldtype:"Small Text", label:"Description", reqd:1},
          {fieldname:"receipt", fieldtype:"Attach", label:"Receipt / Bill",
            description:"Select from My Device or File Library (internal drive).",
            options:{allow_web_link:false, allow_google_drive:false}},
        ],
        primary_action_label: "Save Expense",
        primary_action(values) {
          frappe.call({
            method: "instacertify.expenses.api.create_expense_claim",
            args: values,
            freeze: true,
            callback(r) {
              ed.hide();
              const name = r.message && r.message.name;
              frappe.show_alert({message: "Expense saved: " + (name||""), indicator:"green"});
              if (name) frappe.set_route("Form", "IC Expense Claim", name);
            }
          });
        }
      });
      ed.show();
      return;
    }
    const route = card.route || [];
    if (!route.length) return;
    if (route[0] === "List") {
      frappe.set_route.apply(null, route);
    } else if (route.length === 1) {
      frappe.set_route(route[0]);
    } else {
      frappe.set_route.apply(null, route);
    }
  }

  frappe.call({
    method: "instacertify.explore.dashboard.get_explore_prompts",
    callback(r) {
      const d = r.message || {};
      const grid = root_element.getElementById("ic-explore-grid");
      const hint = root_element.getElementById("ic-explore-hint");
      if (hint && d.hint) hint.textContent = d.hint;
      if (!grid) return;
      const cards = d.cards || [];
      if (!cards.length) {
        grid.innerHTML = empty("No explore options available for your role.");
        return;
      }
      grid.innerHTML = cards.map((c, idx) => {
        const count = (c.count != null)
          ? `<span class="ic-explore-count">${esc(c.count)}</span>`
          : "";
        const actionHint = c.action
          ? `<span class="ic-explore-action">${c.action.indexOf("upload") === 0 ? "Upload" : (c.action === "new_expense" ? "File" : "Open")}</span>`
          : "";
        const iconName = (c.icon || "file").replace(/[^a-z0-9\-]/gi, "");
        // Inline SVG — Custom HTML Blocks use shadow DOM so <use href="#icon-…"> cannot see desk sprites
        const iconHtml = icInlineIcon(iconName);
        return `<button type="button" class="ic-explore-card accent-${esc(c.accent || "teal")}" data-idx="${idx}">
          <div class="ic-explore-card-top">
            <span class="ic-explore-icon" aria-hidden="true">${iconHtml}</span>
            <span class="ic-explore-card-meta">${actionHint}${count}</span>
          </div>
          <div class="ic-explore-card-title">${esc(c.title)}</div>
          <div class="ic-explore-card-sub">${esc(c.subtitle || "")}</div>
        </button>`;
      }).join("");
      grid.querySelectorAll(".ic-explore-card").forEach((btn) => {
        btn.addEventListener("click", () => {
          const i = parseInt(btn.getAttribute("data-idx"), 10);
          openExploreCard(cards[i]);
        });
      });
    }
  });

  function icInlineIcon(name) {
    try {
      const id = "icon-" + name;
      const sym =
        (document.getElementById(id)) ||
        (document.querySelector && document.querySelector("#frappe-symbols #" + CSS.escape(id)));
      if (sym) {
        const viewBox = sym.getAttribute("viewBox") || "0 0 24 24";
        return `<svg class="icon icon-md ic-explore-svg" viewBox="${viewBox}" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">${sym.innerHTML}</svg>`;
      }
      if (window.frappe && frappe.utils && frappe.utils.icon) {
        // Fallback: still try sprite (works outside shadow); may be empty in shadow
        return frappe.utils.icon(name, "md", "", "", "ic-explore-svg", true);
      }
    } catch (e) { /* ignore */ }
    return `<svg class="icon icon-md" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.75"><rect x="4" y="4" width="16" height="16" rx="2"/><path d="M9 9h6v6H9z"/></svg>`;
  }

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
      const grid = root_element.getElementById("ic-summary-grid");
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
      const tasksEl = root_element.getElementById("ic-my-tasks");
      const calEl = root_element.getElementById("ic-my-calendar");
      const leadsEl = root_element.getElementById("ic-my-leads");
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
        root_element.querySelectorAll("a.ic-schedule-session").forEach((el) => {
          el.onclick = function (ev) {
            ev.preventDefault();
            if (window.instacertify && typeof instacertify.schedule_team_session === "function") {
              instacertify.schedule_team_session();
            } else {
              frappe.set_route("Form", "Event", "new");
            }
            return false;
          };
        });
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
    args: { limit: 10 },
    callback(r) {
      const el = root_element.getElementById("ic-lead-prompts");
      const counts = root_element.getElementById("ic-lead-hub-counts");
      if (!el) return;
      const d = r.message || {};
      const rows = d.prompts || [];
      if (counts) {
        counts.textContent = (d.due_count || 0) + " due · " + (d.upcoming_count || 0) + " upcoming";
      }
      if (!rows.length) {
        el.innerHTML = empty("No lead reminders yet. On a Lead set <b>Next Contact Date</b>, <b>Call / Lead Remarks</b> (what the customer said), and who is assigned — they show up here.");
        return;
      }
      el.innerHTML = rows.map(row => {
        const person = esc(row.contact_person || row.title || row.name);
        const company = esc(row.company || "");
        const when = esc(row.due_label || row.ic_next_contact_date || "—");
        const remarks = esc(row.remarks || row.ic_call_remarks || "No customer remarks yet");
        const phone = esc(row.phone || "—");
        const phoneHref = row.phone ? ("tel:" + String(row.phone).replace(/\\s+/g, "")) : "";
        const callWith = esc(row.call_with || "Unassigned");
        const connected = esc(row.connected_label || (row.ic_lead_connected ? "Connected" : "Not connected yet"));
        const connCls = row.ic_lead_connected ? "connected" : "not-connected";
        const urg = esc(row.urgency || "upcoming");
        const stage = esc(row.pipeline_stage || row.status || "");
        const phoneBlock = phoneHref
          ? `<a class="ic-lead-prompt-phone" href="${phoneHref}" onclick="event.stopPropagation()">${phone}</a>`
          : `<span class="ic-lead-prompt-phone">${phone}</span>`;
        return `<a class="ic-lead-prompt ic-lead-hub-card ${urg}" href="/app/lead/${encodeURIComponent(row.name)}">
          <div class="ic-lead-prompt-top">
            <div>
              <div class="ic-lead-hub-kicker">Call</div>
              <div class="ic-lead-prompt-name">${person}</div>
              ${company ? `<div class="ic-lead-hub-company">${company}</div>` : ""}
            </div>
            <span class="ic-lead-prompt-when ${urg}">${when}</span>
          </div>
          <div class="ic-lead-hub-grid">
            <div class="ic-lead-hub-cell">
              <div class="ic-lead-hub-label">Phone</div>
              <div class="ic-lead-hub-value">${phoneBlock}</div>
            </div>
            <div class="ic-lead-hub-cell">
              <div class="ic-lead-hub-label">Connect with</div>
              <div class="ic-lead-hub-value">${callWith}</div>
            </div>
            <div class="ic-lead-hub-cell">
              <div class="ic-lead-hub-label">Status</div>
              <div class="ic-lead-hub-value"><span class="ic-lead-prompt-connected ${connCls}">${connected}</span>${stage ? " · " + stage : ""}</div>
            </div>
          </div>
          <div class="ic-lead-hub-remarks-wrap">
            <div class="ic-lead-hub-label">Customer remarks</div>
            <div class="ic-lead-prompt-remarks ${row.has_remarks ? "" : "muted"}">${remarks}</div>
          </div>
        </a>`;
      }).join("");
    }
  });

  frappe.call({
    method: "instacertify.helpdesk.api.get_open_ticket_summary",
    args: { limit: 8 },
    callback(r) {
      const el = root_element.getElementById("ic-helpdesk-tickets");
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
      const el = root_element.getElementById("ic-collab-recent");
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
      const profile = root_element.getElementById("ic-hr-profile");
      const joining = root_element.getElementById("ic-hr-joining");
      const slips = root_element.getElementById("ic-hr-slips");
      const docs = root_element.getElementById("ic-hr-docs");
      const links = root_element.getElementById("ic-hr-links");
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
      const grid = root_element.getElementById("ic-project-grid");
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


def _upsert_html_block(name, html, script, style=None):
	legacy = f"IC {name}" if not name.startswith("IC ") else None
	if legacy and frappe.db.exists("Custom HTML Block", legacy) and not frappe.db.exists("Custom HTML Block", name):
		try:
			frappe.rename_doc("Custom HTML Block", legacy, name, force=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Rename HTML block {legacy}")

	# Shadow DOM blocks only see desk.bundle.css unless style is set here.
	block_style = style if style is not None else _SHADOW_THEME_CSS

	if frappe.db.exists("Custom HTML Block", name):
		doc = frappe.get_doc("Custom HTML Block", name)
		doc.html = html
		doc.script = script
		doc.style = block_style
		doc.private = 0
		doc.save(ignore_permissions=True)
	else:
		frappe.get_doc(
			{
				"doctype": "Custom HTML Block",
				"name": name,
				"html": html,
				"script": script,
				"style": block_style,
				"private": 0,
			}
		).insert(ignore_permissions=True)


# Injected into each Custom HTML Block shadow root (global app CSS does not pierce shadow DOM).
_SHADOW_THEME_CSS = """
@import url("https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap");
@import url("/assets/instacertify/css/instacertify.css");
:host, * {
  font-family: "Poppins", "Segoe UI", sans-serif !important;
  box-sizing: border-box;
}
#ic-home-root {
  width: 100% !important;
  max-width: none !important;
  display: block;
  box-sizing: border-box;
  margin: 0 !important;
  padding: 0 !important;
}
.ic-greeting {
  position: relative;
  overflow: hidden;
  width: 100% !important;
  max-width: none !important;
  box-sizing: border-box;
  background: linear-gradient(125deg, #0A3380 0%, #0D47A1 42%, #1565C0 78%, #f26d21 145%);
  color: #fff;
  border-radius: 14px;
  padding: 28px 28px 26px;
  margin-bottom: 20px;
  box-shadow: 0 10px 28px rgba(13, 71, 161, 0.07);
}
.ic-greeting-brand {
  font-size: clamp(1.85rem, 3.2vw, 2.45rem);
  font-weight: 800;
  letter-spacing: -0.04em;
  line-height: 1.05;
  color: #fff;
  margin: 0 0 8px;
  font-family: "Poppins", sans-serif !important;
}
.ic-greeting-brand span { color: #ffd7b8; }
.ic-greeting h2 {
  margin: 0 0 6px;
  font-weight: 500;
  font-size: 1.05rem;
  color: rgba(255,255,255,0.92) !important;
  font-family: "Poppins", sans-serif !important;
}
.ic-greeting .ic-datetime { opacity: 0.88; font-size: 0.88rem; color: #fff; }

/* Colorful prompts inside shadow (critical path; full CSS also imported) */
.ic-lead-prompt-title, .ic-workdesk-title {
  font-family: "Poppins", sans-serif !important;
  font-weight: 700;
  color: #0D47A1;
  letter-spacing: -0.02em;
}
.ic-lead-prompt.overdue, .ic-lead-hub-card.overdue {
  background: linear-gradient(165deg, #fff5f4 0%, #fff 55%) !important;
  box-shadow: inset 4px 0 0 #c0392b, 0 10px 24px rgba(192,57,43,0.08) !important;
}
.ic-lead-prompt.today, .ic-lead-hub-card.today {
  background: linear-gradient(165deg, #fff8f0 0%, #fff 55%) !important;
  box-shadow: inset 4px 0 0 #F26D21, 0 10px 24px rgba(242,109,33,0.1) !important;
}
.ic-lead-prompt.upcoming, .ic-lead-hub-card.upcoming {
  background: linear-gradient(165deg, #f0f9fc 0%, #fff 55%) !important;
  box-shadow: inset 4px 0 0 #1565C0, 0 10px 24px rgba(10,143,181,0.08) !important;
}
.ic-lead-prompt-when.overdue { background: #c0392b !important; color: #fff !important; }
.ic-lead-prompt-when.today { background: #F26D21 !important; color: #fff !important; }
.ic-lead-prompt-when.upcoming { background: #1565C0 !important; color: #fff !important; }
.ic-lead-hub-counts {
  background: linear-gradient(90deg, #F26D21, #C45512) !important;
  color: #fff !important;
  font-weight: 700 !important;
  border-radius: 8px;
  padding: 4px 10px;
}
.ic-lead-hub-chip.overdue { background: #c0392b !important; color: #fff !important; }
.ic-lead-hub-chip.upcoming { background: #1565C0 !important; color: #fff !important; }
.ic-lead-hub-remarks-wrap {
  background: rgba(13,71,161,0.04);
  border-radius: 10px;
  padding: 10px 12px;
  margin-top: 8px;
}
.ic-summary-card .value { font-family: "Poppins", sans-serif !important; font-weight: 800 !important; }
.ic-summary-grid, .ic-explore-grid, .ic-project-grid {
  display: grid !important;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 132px), 1fr)) !important;
  gap: 12px !important;
  width: 100% !important;
}
.ic-explore-card, .ic-summary-card {
  aspect-ratio: 1 / 1 !important;
  display: flex !important;
  flex-direction: column !important;
  overflow: hidden !important;
  border-radius: 12px !important;
  min-height: 0 !important;
}
.ic-summary-card {
  justify-content: space-between !important;
  padding: 14px 12px !important;
  border: 1px solid rgba(13,71,161,0.1) !important;
  border-top: 4px solid #0D47A1 !important;
  border-left: 1px solid rgba(13,71,161,0.1) !important;
}
.ic-summary-card:nth-child(3n+1) { border-top-color: #0D47A1 !important; }
.ic-summary-card:nth-child(3n+2) { border-top-color: #F26D21 !important; }
.ic-summary-card:nth-child(3n) { border-top-color: #1565C0 !important; }
.ic-summary-card:nth-child(3n) .value { color: #1565C0 !important; }
.ic-summary-card.accent .value, .ic-summary-card:nth-child(even) .value { color: #F26D21 !important; }
.ic-summary-card .label {
  font-size: 0.68rem !important;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #5a6f7a;
}
.ic-summary-card .value { margin-top: auto !important; font-size: 1.6rem !important; }
.ic-explore-panel { margin-bottom: 20px; }
.ic-explore-title {
  font-family: "Poppins", sans-serif !important;
  font-weight: 700;
  font-size: 1.05rem;
  color: #0D47A1;
  letter-spacing: -0.02em;
}
.ic-explore-sub { color: #5a6f7a; font-size: 0.86rem; margin-top: 2px; margin-bottom: 12px; }
.ic-explore-card {
  text-align: left;
  border: 1px solid rgba(13,71,161,0.12);
  padding: 12px;
  background: linear-gradient(165deg, #ffffff 0%, #f5fafc 100%);
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  box-shadow: 0 6px 16px rgba(13,71,161,0.05);
  font-family: "Poppins", sans-serif !important;
}
.ic-explore-card:hover { transform: translateY(-2px); box-shadow: 0 10px 22px rgba(13,71,161,0.1); }
.ic-explore-card.accent-coral { border-top: 4px solid #c0392b; }
.ic-explore-card.accent-citrus { border-top: 4px solid #F26D21; }
.ic-explore-card.accent-teal { border-top: 4px solid #0D47A1; }
.ic-explore-card-top { display:flex; justify-content: space-between; align-items:center; min-height: 28px; margin-bottom: 8px; flex-shrink: 0; gap: 8px; }
.ic-explore-icon {
  display:inline-flex; align-items:center; justify-content:center;
  width: 32px; height: 32px; flex: 0 0 32px;
  border-radius: 9px; background: #E7F1FC; color: #0D47A1;
}
.ic-explore-icon .icon, .ic-explore-icon svg { width: 18px; height: 18px; stroke: currentColor; color: inherit; }
.ic-explore-card-meta { display:inline-flex; align-items:center; gap: 6px; margin-left: auto; }
.ic-explore-count {
  background: #0D47A1; color: #fff; font-size: 0.72rem; font-weight: 700;
  border-radius: 8px; padding: 2px 8px;
}
.ic-explore-action {
  background: #FFF0E8; color: #C45512; font-size: 0.7rem; font-weight: 700;
  border-radius: 6px; padding: 2px 7px; text-transform: uppercase; letter-spacing: 0.04em;
}
.ic-explore-card-title { font-weight: 700; color: #0A3380; font-size: 0.9rem; line-height: 1.25;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.ic-explore-card-sub { color: #5a6f7a; font-size: 0.74rem; margin-top: auto; padding-top: 8px; line-height: 1.3;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.ic-project-tile {
  aspect-ratio: 1 / 1 !important;
  min-height: 0 !important;
  padding: 12px !important;
  border-radius: 12px !important;
}
.ic-lead-prompt-list {
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 132px), 1fr)) !important;
  gap: 12px !important;
  width: 100% !important;
}
.ic-lead-prompt, .ic-lead-hub-card {
  aspect-ratio: 1 / 1 !important;
  overflow: hidden !important;
  display: flex !important;
  flex-direction: column !important;
}
.ic-workdesk-grid {
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 220px), 1fr)) !important;
  gap: 12px !important;
  width: 100% !important;
}
"""


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
    <div class="ic-crm-chart-label">Lead reminder hub · Whom to call · Connect with · Customer remarks</div>
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
      colors: colors || ["#0D47A1", "#F26D21", "#2a9d8f", "#e9c46a", "#264653", "#f4a261"]
    });
  }
  frappe.call({
    method: "instacertify.crm.dashboard.get_lead_tracker_stats",
    callback(r) {
      const d = r.message || {};
      const kpi = root_element.getElementById("ic-crm-kpi");
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
      makeChart(root_element.getElementById("ic-crm-week-bar"), "bar", week.map(x=>x.label), week.map(x=>x.count), ["#0D47A1", "#90CAF9"]);
      const month = d.month_compare || [];
      makeChart(root_element.getElementById("ic-crm-month-bar"), "bar", month.map(x=>x.label), month.map(x=>x.count), ["#F26D21", "#FFAB91"]);
      const s7 = d.by_source_7d || [];
      makeChart(root_element.getElementById("ic-crm-source-7"), "pie", s7.map(x=>x.label), s7.map(x=>x.count));
      const p30 = d.by_project_type_30d || [];
      makeChart(root_element.getElementById("ic-crm-ptype-30"), "pie", p30.map(x=>x.label), p30.map(x=>x.count));
      const s30 = d.by_source_30d || [];
      makeChart(root_element.getElementById("ic-crm-source-30"), "donut", s30.map(x=>x.label), s30.map(x=>x.count));
      const st30 = d.by_status_30d || [];
      makeChart(root_element.getElementById("ic-crm-status-30"), "bar", st30.map(x=>x.label), st30.map(x=>x.count));
      (function renderFollowups(){
        const el = root_element.getElementById("ic-crm-leads-contact");
        const rows = d.leads_to_contact || [];
        if (el) {
          if (!rows.length) {
            el.innerHTML = "<div class='ic-lead-prompt-empty'>No leads due. Set Next Contact Date, Call / Lead Remarks, and Assigned Salesperson on Leads.</div>";
          } else {
            el.innerHTML = "<table class='ic-related-table'><thead><tr><th>Whom to call</th><th>When</th><th>Phone</th><th>Connect with</th><th>Connected</th><th>Customer remarks</th></tr></thead><tbody>" +
              rows.map(r => {
                const person = r.contact_person || r.title || r.ic_party_name || r.lead_name || r.name;
                const company = r.company || r.company_name || "";
                const title = company ? (person + " · " + company) : person;
                const when = r.due_label || r.ic_next_contact_date || "—";
                const connected = r.ic_lead_connected ? "<span class='ic-lead-prompt-connected connected'>Connected</span>" : "<span class='ic-lead-prompt-connected not-connected'>Not connected</span>";
                const remarks = r.remarks || r.ic_call_remarks || "—";
                const callWith = r.call_with || "Unassigned";
                return "<tr><td><a href='/app/lead/"+encodeURIComponent(r.name)+"'>"+frappe.utils.escape_html(title)+"</a></td><td><span class='ic-lead-prompt-when "+frappe.utils.escape_html(r.urgency||'')+"'>"+frappe.utils.escape_html(when)+"</span></td><td>"+frappe.utils.escape_html(r.phone||r.mobile_no||"—")+"</td><td>"+frappe.utils.escape_html(callWith)+"</td><td>"+connected+"</td><td>"+frappe.utils.escape_html(remarks)+"</td></tr>";
              }).join("") + "</tbody></table>";
          }
        }
        const amc = root_element.getElementById("ic-crm-amc-due");
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
		{"id": "nc_leads_week", "type": "number_card", "data": {"number_card_name": "Leads This Week", "col": 2}},
		{"id": "nc_leads_month", "type": "number_card", "data": {"number_card_name": "Leads This Month", "col": 2}},
		{"id": "nc_new_leads", "type": "number_card", "data": {"number_card_name": "New Leads", "col": 2}},
		{"id": "nc_active_leads", "type": "number_card", "data": {"number_card_name": "Active Leads", "col": 2}},
		{"id": "ic_cards_header", "type": "header", "data": {"text": "<span class=\"h5\">Operations Snapshot</span>", "col": 12}},
		{"id": "nc_quotes_sent", "type": "number_card", "data": {"number_card_name": "Quotations Sent", "col": 2}},
		{"id": "nc_quotes_accepted", "type": "number_card", "data": {"number_card_name": "Quotations Accepted", "col": 2}},
		{"id": "nc_active_projects", "type": "number_card", "data": {"number_card_name": "Active Projects", "col": 2}},
		{"id": "nc_pending_tasks", "type": "number_card", "data": {"number_card_name": "Pending Tasks", "col": 2}},
		{"id": "nc_open_tickets", "type": "number_card", "data": {"number_card_name": "Open Tickets", "col": 2}},
		{"id": "nc_pending_docs", "type": "number_card", "data": {"number_card_name": "Pending Documents", "col": 2}},
		{"id": "nc_leads_contact", "type": "number_card", "data": {"number_card_name": "Leads to Contact", "col": 2}},
		{"id": "nc_testing", "type": "number_card", "data": {"number_card_name": "Testing Requests", "col": 2}},
		{"id": "nc_deadlines", "type": "number_card", "data": {"number_card_name": "Upcoming Deadlines", "col": 2}},
		{"id": "nc_amc", "type": "number_card", "data": {"number_card_name": "AMC Due Soon", "col": 2}},
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
		{"id": "sc_leads", "type": "shortcut", "data": {"shortcut_name": "Leads", "col": 2}},
		{"id": "sc_customers", "type": "shortcut", "data": {"shortcut_name": "Customers", "col": 2}},
		{"id": "sc_quotations", "type": "shortcut", "data": {"shortcut_name": "Quotations", "col": 2}},
		{"id": "sc_projects", "type": "shortcut", "data": {"shortcut_name": "Projects", "col": 2}},
		{"id": "sc_project_board", "type": "shortcut", "data": {"shortcut_name": "Project Board", "col": 2}},
		{"id": "sc_collab", "type": "shortcut", "data": {"shortcut_name": "Team Collaboration", "col": 2}},
		{"id": "sc_calendar", "type": "shortcut", "data": {"shortcut_name": "Team Calendar", "col": 2}},
		{"id": "sc_testing", "type": "shortcut", "data": {"shortcut_name": "Testing Requests", "col": 2}},
		{"id": "sc_labs", "type": "shortcut", "data": {"shortcut_name": "Laboratories", "col": 2}},
		{"id": "sc_quote_templates", "type": "shortcut", "data": {"shortcut_name": "Quote Format Library", "col": 2}},
		{"id": "sc_samples", "type": "shortcut", "data": {"shortcut_name": "Samples", "col": 2}},
		{"id": "sc_docs", "type": "shortcut", "data": {"shortcut_name": "Documents Collection Sheets", "col": 2}},
		{"id": "sc_dispatch", "type": "shortcut", "data": {"shortcut_name": "Sample Dispatch Sheets", "col": 2}},
		{"id": "sc_helpdesk", "type": "shortcut", "data": {"shortcut_name": "Helpdesk", "col": 2}},
		{"id": "sc_sales_invoice", "type": "shortcut", "data": {"shortcut_name": "Sales Invoice", "col": 2}},
		{"id": "sc_purchase_invoice", "type": "shortcut", "data": {"shortcut_name": "Purchase Invoice", "col": 2}},
		{"id": "sc_asset", "type": "shortcut", "data": {"shortcut_name": "Asset", "col": 2}},
		{"id": "sc_gstr1", "type": "shortcut", "data": {"shortcut_name": "GSTR-1", "col": 2}},
		{"id": "sc_gstr3b", "type": "shortcut", "data": {"shortcut_name": "GSTR-3B", "col": 2}},
		{"id": "sc_gst_settings", "type": "shortcut", "data": {"shortcut_name": "GST Settings", "col": 2}},
		# Expenses & HRMS — always last (square tiles)
		{"id": "sc_hrms", "type": "shortcut", "data": {"shortcut_name": "HRMS Lifecycle", "col": 2}},
		{"id": "sc_expenses", "type": "shortcut", "data": {"shortcut_name": "File Expense", "col": 2}},

	]


	shortcuts = [
		{"label": "Leads", "link_to": "Lead", "type": "DocType", "doc_view": "List"},
		{"label": "Customers", "link_to": "Customer", "type": "DocType", "doc_view": "List"},
		{"label": "Quotations", "link_to": "Quotation", "type": "DocType", "doc_view": "List"},
		{"label": "Projects", "link_to": "Project", "type": "DocType", "doc_view": "List"},
		{"label": "Project Board", "link_to": "project-board", "type": "Page"},
		{"label": "Team Collaboration", "link_to": "team-collaboration", "type": "Page"},
		{"label": "Team Calendar", "link_to": "Event", "type": "DocType", "doc_view": "Calendar"},
		{"label": "Testing Requests", "link_to": "IC Testing Request", "type": "DocType", "doc_view": "List"},
		{"label": "Laboratories", "link_to": "IC Laboratory", "type": "DocType", "doc_view": "List"},
		{"label": "Quote Format Library", "link_to": "quote-format-library", "type": "Page", "doc_view": ""},
		{"label": "Samples", "link_to": "IC Sample Tracking", "type": "DocType", "doc_view": "List"},
		{"label": "Documents Collection Sheets", "link_to": "IC Document Request", "type": "DocType", "doc_view": "List"},
		{"label": "Sample Dispatch Sheets", "link_to": "IC Sample Dispatch Collection", "type": "DocType", "doc_view": "List"},
		{"label": "Helpdesk", "link_to": "Helpdesk Ticket", "type": "DocType", "doc_view": "List"},
		{"label": "Sales Invoice", "link_to": "Sales Invoice", "type": "DocType", "doc_view": "List"},
		{"label": "Purchase Invoice", "link_to": "Purchase Invoice", "type": "DocType", "doc_view": "List"},
		{"label": "Asset", "link_to": "Asset", "type": "DocType", "doc_view": "List"},
		{"label": "GSTR-1", "link_to": "GSTR-1", "type": "DocType", "doc_view": ""},
		{"label": "GSTR-3B", "link_to": "GSTR 3B Report", "type": "DocType", "doc_view": "List"},
		{"label": "GST Settings", "link_to": "GST Settings", "type": "DocType", "doc_view": ""},
		# Expenses & HRMS last
		{"label": "HRMS Lifecycle", "link_to": "Employee", "type": "DocType", "doc_view": "List"},
		{"label": "File Expense", "link_to": "IC Expense Claim", "type": "DocType", "doc_view": "List"},
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
		{"label": "Quote Format Library (by category)", "link_type": "Page", "link_to": "quote-format-library", "type": "Link"},
		{"label": "Quotation Templates (list)", "link_type": "DocType", "link_to": "IC Quotation Template", "type": "Link"},
		{"label": "Upload Quote Format", "link_type": "DocType", "link_to": "IC Quotation Template", "type": "Link"},
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
		{"label": "Upload Laboratory / Scope", "link_type": "DocType", "link_to": "IC Laboratory", "type": "Link"},
		{"label": "Testing Requests", "link_type": "DocType", "link_to": "IC Testing Request", "type": "Link"},
		{"label": "Documents", "type": "Card Break"},
		{"label": "Documents Collection Sheets", "link_type": "DocType", "link_to": "IC Document Request", "type": "Link"},
		{"label": "Sample Dispatch Collection Sheets", "link_type": "DocType", "link_to": "IC Sample Dispatch Collection", "type": "Link"},
		{"label": "Document Checklist Templates", "link_type": "DocType", "link_to": "IC Document Checklist Template", "type": "Link"},
		{"label": "Project Records", "link_type": "DocType", "link_to": "IC Project Record", "type": "Link"},
		{"label": "Calendar & Planner", "type": "Card Break"},
		{"label": "Event", "link_type": "DocType", "link_to": "Event", "type": "Link"},
		{"label": "Task", "link_type": "DocType", "link_to": "Task", "type": "Link"},
		{"label": "Assets", "type": "Card Break"},
		{"label": "Asset", "link_type": "DocType", "link_to": "Asset", "type": "Link"},
		{"label": "Asset Category", "link_type": "DocType", "link_to": "Asset Category", "type": "Link"},
		{"label": "Administration", "type": "Card Break"},
		{"label": "User", "link_type": "DocType", "link_to": "User", "type": "Link"},
		{"label": "Role", "link_type": "DocType", "link_to": "Role", "type": "Link"},
		{"label": "Settings", "link_type": "DocType", "link_to": "IC Settings", "type": "Link"},
		# Expenses & HRMS — always last on Instacertify Home
		{"label": "Expenses & HRMS (Hiring → FnF)", "type": "Card Break"},
		{"label": "File an Expense", "link_type": "DocType", "link_to": "IC Expense Claim", "type": "Link"},
		{"label": "My Expense Claims", "link_type": "DocType", "link_to": "IC Expense Claim", "type": "Link"},
		{"label": "Job Applicant", "link_type": "DocType", "link_to": "Job Applicant", "type": "Link"},
		{"label": "Job Offer", "link_type": "DocType", "link_to": "Job Offer", "type": "Link"},
		{"label": "Employee", "link_type": "DocType", "link_to": "Employee", "type": "Link"},
		{"label": "Employee Onboarding", "link_type": "DocType", "link_to": "Employee Onboarding", "type": "Link"},
		{"label": "Joining Letters", "link_type": "DocType", "link_to": "IC Joining Letter", "type": "Link"},
		{"label": "Employee Documents", "link_type": "DocType", "link_to": "IC Employee Document", "type": "Link"},
		{"label": "Attendance", "link_type": "DocType", "link_to": "Attendance", "type": "Link"},
		{"label": "Leave Application", "link_type": "DocType", "link_to": "Leave Application", "type": "Link"},
		{"label": "Salary Slip", "link_type": "DocType", "link_to": "Salary Slip", "type": "Link"},
		{"label": "Payroll Entry", "link_type": "DocType", "link_to": "Payroll Entry", "type": "Link"},
		{"label": "Employee Separation", "link_type": "DocType", "link_to": "Employee Separation", "type": "Link"},
		{"label": "Full and Final Statement", "link_type": "DocType", "link_to": "Full and Final Statement", "type": "Link"},
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
		elif stype == "URL":
			safe_shortcuts.append(s)
			continue
		elif dt and not frappe.db.exists("DocType", dt):
			continue
		# Single DocTypes must open Form — List view 500s / Not Found
		if stype == "DocType" and dt and frappe.get_meta(dt).issingle:
			s = dict(s)
			s["doc_view"] = ""
		safe_shortcuts.append(s)

	# Keep Quick Link tiles in sync with shortcuts that actually resolve (no dead tiles)
	safe_shortcut_labels = {s["label"] for s in safe_shortcuts}
	content = [
		block
		for block in content
		if not (
			block.get("type") == "shortcut"
			and (block.get("data") or {}).get("shortcut_name") not in safe_shortcut_labels
		)
	]

	from instacertify.setup.navigation_icons import apply_shortcut_icons

	safe_shortcuts = apply_shortcut_icons(safe_shortcuts)

	payload = {
		"doctype": "Workspace",
		"name": name,
		"label": name,
		"title": name,
		"icon": "layout-dashboard",
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
		ws.number_cards = []
		ws.charts = []
		for s in safe_shortcuts:
			ws.append("shortcuts", s)
		for l in safe_links:
			ws.append("links", l)
		ws.append("custom_blocks", {"custom_block_name": "Home Dashboard", "label": "Home Dashboard"})
		ws.append("custom_blocks", {"custom_block_name": "CRM Lead Tracker", "label": "CRM Lead Tracker"})
		for block in content:
			btype = block.get("type")
			data = block.get("data") or {}
			if btype == "number_card" and data.get("number_card_name"):
				nc = data["number_card_name"]
				if frappe.db.exists("Number Card", nc):
					ws.append(
						"number_cards",
						{"number_card_name": nc, "label": nc},
					)
			elif btype == "chart" and data.get("chart_name"):
				ch = data["chart_name"]
				if frappe.db.exists("Dashboard Chart", ch):
					ws.append("charts", {"chart_name": ch, "label": ch})
		ws.content = json.dumps(content)
		ws.save(ignore_permissions=True)
	else:
		ws = frappe.get_doc(payload)
		ws.append("custom_blocks", {"custom_block_name": "Home Dashboard", "label": "Home Dashboard"})
		ws.append("custom_blocks", {"custom_block_name": "CRM Lead Tracker", "label": "CRM Lead Tracker"})
		for block in content:
			btype = block.get("type")
			data = block.get("data") or {}
			if btype == "number_card" and data.get("number_card_name"):
				nc = data["number_card_name"]
				if frappe.db.exists("Number Card", nc):
					ws.append("number_cards", {"number_card_name": nc, "label": nc})
			elif btype == "chart" and data.get("chart_name"):
				ch = data["chart_name"]
				if frappe.db.exists("Dashboard Chart", ch):
					ws.append("charts", {"chart_name": ch, "label": ch})
		ws.insert(ignore_permissions=True)


def ensure_hrms_expenses_workspace():
	"""Dedicated workspace — Expenses & HRMS last in navigation (Hiring → FnF)."""
	name = "HRMS & Expenses"
	# High sequence so it sits after core Instacertify / GST / ops workspaces
	sequence_id = 80

	content = [
		{
			"id": "hrms_header",
			"type": "header",
			"data": {
				"text": "<span class=\"h5\">Employee lifecycle — Hiring to Full &amp; Final</span>",
				"col": 12,
			},
		},
		{"id": "sc_job_applicant", "type": "shortcut", "data": {"shortcut_name": "Job Applicant", "col": 3}},
		{"id": "sc_job_offer", "type": "shortcut", "data": {"shortcut_name": "Job Offer", "col": 3}},
		{"id": "sc_employee", "type": "shortcut", "data": {"shortcut_name": "Employee", "col": 3}},
		{"id": "sc_onboarding", "type": "shortcut", "data": {"shortcut_name": "Employee Onboarding", "col": 3}},
		{"id": "sc_joining", "type": "shortcut", "data": {"shortcut_name": "Joining Letters", "col": 3}},
		{"id": "sc_attendance", "type": "shortcut", "data": {"shortcut_name": "Attendance", "col": 3}},
		{"id": "sc_leave", "type": "shortcut", "data": {"shortcut_name": "Leave Application", "col": 3}},
		{"id": "sc_salary", "type": "shortcut", "data": {"shortcut_name": "Salary Slip", "col": 3}},
		{"id": "sc_payroll", "type": "shortcut", "data": {"shortcut_name": "Payroll Entry", "col": 3}},
		{"id": "sc_file_expense", "type": "shortcut", "data": {"shortcut_name": "File Expense", "col": 3}},
		{"id": "sc_expense_hrms", "type": "shortcut", "data": {"shortcut_name": "Expense Claim", "col": 3}},
		{"id": "sc_separation", "type": "shortcut", "data": {"shortcut_name": "Employee Separation", "col": 3}},
		{"id": "sc_fnf", "type": "shortcut", "data": {"shortcut_name": "Full and Final", "col": 3}},
	]

	shortcuts = [
		{"label": "Job Applicant", "link_to": "Job Applicant", "type": "DocType", "doc_view": "List"},
		{"label": "Job Offer", "link_to": "Job Offer", "type": "DocType", "doc_view": "List"},
		{"label": "Employee", "link_to": "Employee", "type": "DocType", "doc_view": "List"},
		{"label": "Employee Onboarding", "link_to": "Employee Onboarding", "type": "DocType", "doc_view": "List"},
		{"label": "Joining Letters", "link_to": "IC Joining Letter", "type": "DocType", "doc_view": "List"},
		{"label": "Attendance", "link_to": "Attendance", "type": "DocType", "doc_view": "List"},
		{"label": "Leave Application", "link_to": "Leave Application", "type": "DocType", "doc_view": "List"},
		{"label": "Salary Slip", "link_to": "Salary Slip", "type": "DocType", "doc_view": "List"},
		{"label": "Payroll Entry", "link_to": "Payroll Entry", "type": "DocType", "doc_view": "List"},
		{"label": "File Expense", "link_to": "IC Expense Claim", "type": "DocType", "doc_view": "List"},
		{"label": "Expense Claim", "link_to": "Expense Claim", "type": "DocType", "doc_view": "List"},
		{"label": "Employee Separation", "link_to": "Employee Separation", "type": "DocType", "doc_view": "List"},
		{"label": "Full and Final", "link_to": "Full and Final Statement", "type": "DocType", "doc_view": "List"},
	]

	links = [
		{"label": "1. Hiring", "type": "Card Break"},
		{"label": "Job Applicant", "link_type": "DocType", "link_to": "Job Applicant", "type": "Link"},
		{"label": "Job Offer", "link_type": "DocType", "link_to": "Job Offer", "type": "Link"},
		{"label": "Interview", "link_type": "DocType", "link_to": "Interview", "type": "Link"},
		{"label": "2. Onboarding", "type": "Card Break"},
		{"label": "Employee", "link_type": "DocType", "link_to": "Employee", "type": "Link"},
		{"label": "Employee Onboarding", "link_type": "DocType", "link_to": "Employee Onboarding", "type": "Link"},
		{"label": "Joining Letter (Instacertify)", "link_type": "DocType", "link_to": "IC Joining Letter", "type": "Link"},
		{"label": "Employee Documents", "link_type": "DocType", "link_to": "IC Employee Document", "type": "Link"},
		{"label": "3. Attendance & Leave", "type": "Card Break"},
		{"label": "Attendance", "link_type": "DocType", "link_to": "Attendance", "type": "Link"},
		{"label": "Attendance Request", "link_type": "DocType", "link_to": "Attendance Request", "type": "Link"},
		{"label": "Leave Application", "link_type": "DocType", "link_to": "Leave Application", "type": "Link"},
		{"label": "Holiday List", "link_type": "DocType", "link_to": "Holiday List", "type": "Link"},
		{"label": "4. Payroll", "type": "Card Break"},
		{"label": "Salary Structure", "link_type": "DocType", "link_to": "Salary Structure", "type": "Link"},
		{"label": "Salary Structure Assignment", "link_type": "DocType", "link_to": "Salary Structure Assignment", "type": "Link"},
		{"label": "Payroll Entry", "link_type": "DocType", "link_to": "Payroll Entry", "type": "Link"},
		{"label": "Salary Slip", "link_type": "DocType", "link_to": "Salary Slip", "type": "Link"},
		{"label": "5. Expenses", "type": "Card Break"},
		{"label": "File Expense (Instacertify)", "link_type": "DocType", "link_to": "IC Expense Claim", "type": "Link"},
		{"label": "Expense Claim (HRMS)", "link_type": "DocType", "link_to": "Expense Claim", "type": "Link"},
		{"label": "Expense Claim Type", "link_type": "DocType", "link_to": "Expense Claim Type", "type": "Link"},
		{"label": "6. Performance", "type": "Card Break"},
		{"label": "Appraisal", "link_type": "DocType", "link_to": "Appraisal", "type": "Link"},
		{"label": "Goal", "link_type": "DocType", "link_to": "Goal", "type": "Link"},
		{"label": "7. Exit & Full and Final", "type": "Card Break"},
		{"label": "Employee Separation", "link_type": "DocType", "link_to": "Employee Separation", "type": "Link"},
		{"label": "Full and Final Statement", "link_type": "DocType", "link_to": "Full and Final Statement", "type": "Link"},
	]

	safe_links = []
	for link in links:
		if link.get("type") == "Card Break":
			safe_links.append(link)
			continue
		dt = link.get("link_to")
		if dt and not frappe.db.exists("DocType", dt):
			continue
		safe_links.append(link)

	safe_shortcuts = []
	for s in shortcuts:
		dt = s.get("link_to")
		if dt and not frappe.db.exists("DocType", dt):
			continue
		safe_shortcuts.append(s)

	# Drop content shortcuts that were filtered out
	labels = {s["label"] for s in safe_shortcuts}
	safe_content = []
	for block in content:
		if block.get("type") == "shortcut":
			name_sc = (block.get("data") or {}).get("shortcut_name")
			if name_sc and name_sc not in labels:
				continue
		safe_content.append(block)

	from instacertify.setup.navigation_icons import apply_shortcut_icons

	safe_shortcuts = apply_shortcut_icons(safe_shortcuts)

	payload = {
		"doctype": "Workspace",
		"name": name,
		"label": name,
		"title": name,
		"icon": "id-card",
		"module": "Instacertify",
		"public": 1,
		"is_hidden": 0,
		"sequence_id": sequence_id,
		"content": json.dumps(safe_content),
		"shortcuts": safe_shortcuts,
		"links": safe_links,
	}

	if frappe.db.exists("Workspace", name):
		ws = frappe.get_doc("Workspace", name)
		ws.update(payload)
		ws.shortcuts = []
		ws.links = []
		for s in safe_shortcuts:
			ws.append("shortcuts", s)
		for l in safe_links:
			ws.append("links", l)
		ws.content = json.dumps(safe_content)
		ws.sequence_id = sequence_id
		ws.save(ignore_permissions=True)
	else:
		ws = frappe.get_doc(payload)
		ws.insert(ignore_permissions=True)

	frappe.db.set_value(
		"Workspace",
		name,
		{"public": 1, "is_hidden": 0, "sequence_id": sequence_id},
		update_modified=False,
	)
