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
	# Frappe 16 left nav reads Workspace Sidebar — not Workspace.links.
	# GST / Gameplan only patch an existing sidebar; rebuild the full nav here.
	_ensure_instacertify_home_sidebar()
	_ensure_hrms_expenses_sidebar()
	_ensure_unified_testing_samples_sidebar()
	from instacertify.setup.navigation_icons import ensure_navigation_icons

	ensure_navigation_icons()
	# Programmatic workspaces have no JSON fixtures — clear module/app so
	# frappe.model.sync.remove_orphan_entities does not delete them on migrate.
	for ws_name in ("Instacertify Home", "HRMS & Expenses"):
		_protect_workspace_from_orphan_cleanup(ws_name)


def _protect_workspace_from_orphan_cleanup(name: str):
	"""Keep public workspaces but exclude them from migrate orphan deletion.

	Orphan cleanup only targets public workspaces with both module and app set
	that lack a matching JSON fixture under the app tree.
	"""
	if not frappe.db.exists("Workspace", name):
		return
	frappe.db.set_value(
		"Workspace",
		name,
		{"module": None, "app": None},
		update_modified=False,
	)


def _sidebar_link(
	label: str,
	*,
	link_type: str | None = "DocType",
	link_to: str | None = None,
	url: str | None = None,
	icon: str = "file",
	child: int = 0,
	section: bool = False,
) -> dict:
	if section:
		return {
			"type": "Section Break",
			"label": label,
			"icon": icon,
			"child": 0,
			"collapsible": 1,
			"indent": 0,
			"keep_closed": 0,
			"show_arrow": 0,
		}
	row = {
		"type": "Link",
		"label": label,
		"link_type": link_type,
		"link_to": link_to,
		"url": url,
		"icon": icon,
		"child": child,
		"collapsible": 1,
		"indent": 0,
		"keep_closed": 0,
		"show_arrow": 0,
	}
	return row


def _link_target_exists(link_type: str | None, link_to: str | None, url: str | None = None) -> bool:
	if url or (link_type or "").upper() == "URL":
		return True
	if not link_to:
		return False
	lt = link_type or "DocType"
	if lt == "Workspace":
		return bool(frappe.db.exists("Workspace", link_to))
	if lt == "Page":
		return bool(frappe.db.exists("Page", link_to))
	if lt == "Report":
		return bool(frappe.db.exists("Report", link_to))
	if lt == "Dashboard":
		return bool(frappe.db.exists("Dashboard", link_to))
	return bool(frappe.db.exists("DocType", link_to))


def _save_workspace_sidebar(title: str, header_icon: str, items: list[dict]):
	"""Create or replace a Workspace Sidebar (Frappe 16 desk left nav)."""
	safe_items = []
	for row in items:
		if row.get("type") == "Section Break":
			safe_items.append(row)
			continue
		if not _link_target_exists(row.get("link_type"), row.get("link_to"), row.get("url")):
			continue
		safe_items.append(row)

	if frappe.db.exists("Workspace Sidebar", title):
		sb = frappe.get_doc("Workspace Sidebar", title)
		sb.header_icon = header_icon or sb.header_icon
		sb.set("items", [])
		for row in safe_items:
			sb.append("items", row)
	else:
		sb = frappe.get_doc(
			{
				"doctype": "Workspace Sidebar",
				"title": title,
				"header_icon": header_icon,
				"items": safe_items,
			}
		)

	sb.flags.ignore_permissions = True
	sb.flags.ignore_links = True
	sb.flags.ignore_validate = True
	try:
		if sb.is_new():
			sb.insert(ignore_permissions=True)
		else:
			sb.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"workspace sidebar {title}")


def _ensure_instacertify_home_sidebar():
	"""Build the Instacertify Home left sidebar (Quotation, Customer, Testing, …).

	Workspace.links alone do not drive Frappe 16 navigation — Workspace Sidebar does.
	After ERPNext setup / migrate, GST may leave only a GST-only sidebar; rebuild here.
	"""
	if not frappe.db.exists("Workspace", "Instacertify Home"):
		return

	gameplan = False
	try:
		gameplan = "gameplan" in frappe.get_installed_apps()
	except Exception:
		pass

	items = [
		_sidebar_link(
			"Home",
			link_type="Workspace",
			link_to="Instacertify Home",
			icon="layout-dashboard",
		),
	]
	if gameplan:
		items.append(
			_sidebar_link("Gameplan", link_type="URL", url="/g", icon="message-circle")
		)

	items.extend(
		[
			_sidebar_link("Leads", link_to="Lead", icon="users"),
			_sidebar_link("Customers", link_to="Customer", icon="building"),
			_sidebar_link("Quotations", link_to="Quotation", icon="file-text"),
			_sidebar_link("Projects", link_to="Project", icon="briefcase"),
			_sidebar_link(
				"Testing & Samples",
				link_type="Page",
				link_to="testing-samples",
				icon="flask-conical",
			),
			_sidebar_link("Laboratories", link_to="IC Laboratory", icon="microscope"),
			_sidebar_link(
				"Document Requests",
				link_to="IC Document Request",
				icon="clipboard-list",
			),
			_sidebar_link("Helpdesk", link_to="Helpdesk Ticket", icon="headset"),
			_sidebar_link("Team Calendar", link_to="Event", icon="calendar"),
			_sidebar_link(
				"Lead Reminders",
				link_type="Page",
				link_to="lead-reminders",
				icon="phone",
			),
			_sidebar_link("GST & Invoicing", icon="landmark", section=True),
			_sidebar_link("Sales Invoice", link_to="Sales Invoice", icon="receipt", child=1),
			_sidebar_link(
				"Purchase Invoice",
				link_to="Purchase Invoice",
				icon="shopping-cart",
				child=1,
			),
			_sidebar_link("Payment Entry", link_to="Payment Entry", icon="banknote", child=1),
			_sidebar_link("GSTR-1", link_to="GSTR-1", icon="badge-indian-rupee", child=1),
			_sidebar_link("GSTR-3B", link_to="GSTR 3B Report", icon="calculator", child=1),
			_sidebar_link(
				"GST Return Log",
				link_to="GST Return Log",
				icon="file-spreadsheet",
				child=1,
			),
			_sidebar_link("GST Settings", link_to="GST Settings", icon="settings", child=1),
			_sidebar_link("File Expense", link_to="IC Expense Claim", icon="wallet"),
			_sidebar_link("HRMS Lifecycle", link_to="Employee", icon="id-card"),
		]
	)
	_save_workspace_sidebar("Instacertify Home", "layout-dashboard", items)


def _ensure_hrms_expenses_sidebar():
	"""Left nav for the HRMS & Expenses workspace."""
	if not frappe.db.exists("Workspace", "HRMS & Expenses"):
		return
	items = [
		_sidebar_link(
			"Home",
			link_type="Workspace",
			link_to="HRMS & Expenses",
			icon="id-card",
		),
		_sidebar_link("Job Applicant", link_to="Job Applicant", icon="user-plus"),
		_sidebar_link("Job Offer", link_to="Job Offer", icon="file-check"),
		_sidebar_link("Employee", link_to="Employee", icon="square-user-round"),
		_sidebar_link(
			"Employee Onboarding",
			link_to="Employee Onboarding",
			icon="user-star",
		),
		_sidebar_link("Joining Letters", link_to="IC Joining Letter", icon="mail"),
		_sidebar_link("Attendance", link_to="Attendance", icon="calendar-check"),
		_sidebar_link("Leave Application", link_to="Leave Application", icon="plane"),
		_sidebar_link("Salary Slip", link_to="Salary Slip", icon="banknote"),
		_sidebar_link("Payroll Entry", link_to="Payroll Entry", icon="circle-dollar-sign"),
		_sidebar_link("File Expense", link_to="IC Expense Claim", icon="wallet"),
		_sidebar_link("Expense Claim", link_to="Expense Claim", icon="wallet"),
		_sidebar_link(
			"Employee Separation",
			link_to="Employee Separation",
			icon="log-out",
		),
		_sidebar_link(
			"Full and Final",
			link_to="Full and Final Statement",
			icon="scale",
		),
	]
	_save_workspace_sidebar("HRMS & Expenses", "id-card", items)


def _ensure_unified_testing_samples_sidebar():
	"""Sidebar: one Testing & Samples entry (not separate Testing Requests + Samples)."""
	sidebar_name = "Instacertify Home"
	if not frappe.db.exists("Workspace Sidebar", sidebar_name):
		return

	sb = frappe.get_doc("Workspace Sidebar", sidebar_name)
	remove_labels = {
		"testing requests",
		"samples",
		"sample tracking",
		"testing request",
	}
	remove_links = {"IC Testing Request", "IC Sample Tracking"}

	kept = []
	unified = None
	for row in list(sb.items or []):
		label = (row.label or "").strip()
		link_to = (row.link_to or "").strip()
		label_l = label.lower()
		if label_l in remove_labels or link_to in remove_links:
			continue
		if label_l in {"testing & samples", "testing and samples"} or link_to == "testing-samples":
			unified = row
			continue
		kept.append(row)

	# Build unified Page link
	unified_vals = {
		"type": "Link",
		"label": "Testing & Samples",
		"link_type": "Page",
		"link_to": "testing-samples",
		"icon": "flask-conical",
		"child": 0,
		"collapsible": 1,
		"indent": 0,
		"keep_closed": 0,
		"show_arrow": 0,
	}

	# Insert after Projects when possible
	insert_at = next(
		(i + 1 for i, r in enumerate(kept) if (r.label or "").strip().lower() == "projects"),
		min(6, len(kept)),
	)
	sb.set("items", [])
	for i, row in enumerate(kept):
		if i == insert_at:
			sb.append("items", unified_vals)
		sb.append(
			"items",
			{
				"label": row.label,
				"link_type": row.link_type,
				"type": row.type,
				"link_to": row.link_to,
				"icon": row.icon,
				"url": row.url,
				"child": row.child,
				"collapsible": row.collapsible,
				"indent": row.indent,
				"keep_closed": getattr(row, "keep_closed", 0),
				"show_arrow": getattr(row, "show_arrow", 0),
				"filters": row.filters,
				"route_options": row.route_options,
			},
		)
	if insert_at >= len(kept):
		sb.append("items", unified_vals)

	sb.flags.ignore_permissions = True
	sb.flags.ignore_links = True
	sb.flags.ignore_validate = True
	try:
		sb.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "unified testing samples sidebar")


def _ensure_home_html_block():
	name = "Home Dashboard"
	html = """
<div id="ic-home-root">
  <div class="ic-greeting">
    <div class="ic-greeting-brand">
      <img class="ic-home-brand-icon" src="/assets/instacertify/images/favicon-48.png" width="48" height="48" alt="Instacertify" />
      <span class="ic-greeting-brand-text">Insta<span>certify</span></span>
    </div>
    <h2 id="ic-greet-title">Welcome</h2>
    <div class="ic-datetime"><span id="ic-date"></span> · <span id="ic-time"></span></div>
  </div>

  <section class="ic-today" id="ic-today" aria-live="polite">
    <div class="ic-today-head">
      <div class="ic-today-title">Needs attention</div>
      <div class="ic-today-sub">Live counts across the company. Click one to open the list.</div>
    </div>
    <div class="ic-today-list" id="ic-today-list"><span class="ic-today-wait">Checking your records…</span></div>
  </section>

  <div class="ic-workdesk-grid">
    <section class="ic-workdesk-panel ic-wd-tasks">
      <div class="ic-workdesk-head">
        <div>
          <div class="ic-workdesk-title">My tasks</div>
          <div class="ic-workdesk-sub">Open work assigned to you</div>
        </div>
        <a class="ic-view-all" href="/app/task">All tasks</a>
      </div>
      <div id="ic-my-tasks"></div>
    </section>
    <section class="ic-workdesk-panel ic-wd-calendar">
      <div class="ic-workdesk-head">
        <div>
          <div class="ic-workdesk-title">Team calendar</div>
          <div class="ic-workdesk-sub">Sessions · book for teammates · 30‑min alerts</div>
        </div>
        <div class="ic-workdesk-actions">
          <a class="ic-view-all ic-schedule-session" href="/app/event/new">Schedule session</a>
          <a class="ic-view-all" href="/app/event/view/calendar">Open calendar</a>
        </div>
      </div>
      <div id="ic-my-calendar"></div>
    </section>
    <section class="ic-workdesk-panel ic-wd-leads">
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

  <div class="ic-section-label">At a glance</div>
  <div class="ic-summary-grid" id="ic-summary-grid"></div>

  <div class="ic-explore-panel" id="ic-explore-panel">
    <div class="ic-explore-head">
      <div>
        <div class="ic-explore-title">Explore Instacertify</div>
        <div class="ic-explore-sub" id="ic-explore-hint">Organised in tiles — tap any square to open</div>
      </div>
    </div>
    <div class="ic-explore-grid" id="ic-explore-grid"></div>
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
  // Home loads in the background, so a missing permission hides that panel
  // instead of raising a "Permission Error" box over the page.
  function canRead(doctype) {
    if (!doctype) return true;
    try { return !!frappe.model.can_read(doctype); } catch (e) { return true; }
  }
  function hidePanel(id) {
    const el = root_element.getElementById(id);
    const panel = el && (el.closest(".ic-workdesk-panel") || el.closest(".ic-lead-prompt-panel") || el);
    if (panel) panel.style.display = "none";
  }
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
      "Leads to Contact": ["Lead", {status: ["not in", ["Converted", "Do Not Contact"]], ic_next_contact_date: ["between", ["2000-01-01", today]]}],
      "Pending Tasks": ["Task", {status: ["in", ["Open", "Working"]]}],
      "Open Tickets": ["Helpdesk Ticket", {status: ["in", ["Open", "In Progress", "Waiting on Customer"]]}],
      "Open Complaints": ["Helpdesk Ticket", {status: ["in", ["Open", "In Progress", "Waiting on Customer"]], ticket_type: "Complaint"}],
      "Quotations Sent": ["Quotation", {ic_workflow_status: ["in", ["Shared with Customer", "Customer Review"]]}],
      "Quotations Accepted": ["Quotation", {ic_workflow_status: "Accepted"}],
      "Active Projects": ["Project", {status: ["not in", ["Completed", "Cancelled"]]}],
      "Upcoming Deadlines": ["Project", {status: ["not in", ["Completed", "Cancelled"]], ic_deadline: ["<=", deadline_end]}],
      "Pending Documents": ["IC Document Request", {status: ["in", ["Sent to Customer", "Partially Uploaded"]]}],
      "Testing Requests": ["testing-samples"],
      "Testing & Samples": ["testing-samples"],
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
    if (hit.length === 1 && typeof hit[0] === "string" && hit[0].indexOf("-") >= 0 && hit[0] === hit[0].toLowerCase()) {
      frappe.set_route(hit[0]);
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
        return `<button type="button" class="ic-explore-card accent-${esc(c.accent || "teal")}" data-idx="${idx}" title="${esc(c.subtitle || "")}">
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
      const roles = frappe.user_roles || [];
      const has = (list) => list.some((r) => roles.indexOf(r) >= 0);
      let focus = "all";
      if (!has(["IC Admin", "System Manager"])) {
        if (has(["IC Sales Manager", "IC Sales Executive", "IC Sales Person", "Sales User", "Sales Manager"])) focus = "sales";
        else if (has(["IC Projects Manager", "IC Projects Executive", "IC Operations Manager", "IC Ops Executive", "IC Senior Operations", "Projects User", "Projects Manager"])) focus = "delivery";
      }
      const homeRoot = root_element.getElementById("ic-home-root");
      if (homeRoot) homeRoot.classList.add("ic-focus-" + focus);
      // label, value, team, needs-attention tone, wording for one / many
      const items = [
        ["Leads to Contact", data.leads_to_contact, "sales", "danger", "lead to follow up today", "leads to follow up today"],
        ["Open Complaints", data.open_complaints, "support", "danger", "open complaint", "open complaints"],
        ["Upcoming Deadlines", data.upcoming_deadlines, "delivery", "warn", "project deadline within 14 days", "project deadlines within 14 days"],
        ["Pending Tasks", data.pending_tasks, "delivery", "warn", "open task", "open tasks"],
        ["Pending Documents", data.pending_documents, "delivery", "warn", "document request waiting on the customer", "document requests waiting on the customer"],
        ["Open Tickets", data.open_tickets, "support", "warn", "open helpdesk ticket", "open helpdesk tickets"],
        ["AMC Due Soon", data.amc_due_soon, "delivery", "warn", "AMC renewal due within a month", "AMC renewals due within a month"],
        ["Quotations Sent", data.quotations_sent, "sales", "info", "quotation awaiting the customer", "quotations awaiting the customer"],
        ["Quotations Accepted", data.quotations_accepted, "sales", "ok", "accepted quotation to start", "accepted quotations to start"],
        ["Testing Requests", data.testing_requests, "delivery", "info", "testing request in progress", "testing requests in progress"],
        ["New Leads", data.new_leads, "sales", "", "", ""],
        ["Active Leads", data.active_leads, "sales", "", "", ""],
        ["Active Projects", data.active_projects, "delivery", "", "", ""],
      ];
      // a count the user cannot open would only lead to a "not permitted" page
      const record_type = {
        "Leads to Contact": "Lead", "New Leads": "Lead", "Active Leads": "Lead",
        "Open Complaints": "Helpdesk Ticket", "Open Tickets": "Helpdesk Ticket",
        "Upcoming Deadlines": "Project", "AMC Due Soon": "Project", "Active Projects": "Project",
        "Pending Tasks": "Task", "Pending Documents": "IC Document Request",
        "Testing Requests": "IC Testing Request",
        "Quotations Sent": "Quotation", "Quotations Accepted": "Quotation",
      };
      const mine = (team) => (focus !== "all" && team === focus ? 0 : 1);
      const severity = { danger: 0, warn: 1, info: 2, ok: 3, "": 4 };

      const today = root_element.getElementById("ic-today-list");
      if (today) {
        const due = items
          .filter((i) => i[3] && (i[1] || 0) > 0 && canRead(record_type[i[0]]))
          .sort((a, b) => mine(a[2]) - mine(b[2]) || severity[a[3]] - severity[b[3]])
          .slice(0, 6);
        today.innerHTML = due.length
          ? due.map((i) =>
              `<button type="button" class="ic-today-item tone-${i[3]}" data-kpi="${frappe.utils.escape_html(i[0])}">
                <span class="ic-today-count">${i[1]}</span>
                <span class="ic-today-text">${frappe.utils.escape_html(i[1] === 1 ? i[4] : i[5])}</span>
                <span class="ic-today-go" aria-hidden="true">View</span>
              </button>`
            ).join("")
          : `<span class="ic-today-clear">Nothing is waiting right now.</span>`;
        today.querySelectorAll(".ic-today-item").forEach((el) => {
          el.onclick = function () { openKpi(el.getAttribute("data-kpi")); };
        });
      }

      const teamOrder = { sales: 0, delivery: 1, support: 2 };
      const cards = items.slice().sort((a, b) => mine(a[2]) - mine(b[2]) || teamOrder[a[2]] - teamOrder[b[2]]);
      const grid = root_element.getElementById("ic-summary-grid");
      if (!grid) return;
      grid.innerHTML = cards.filter((i) => canRead(record_type[i[0]])).map((i) => {
        const value = i[1] || 0;
        const cls = !value ? "is-zero" : (i[3] === "danger" || i[3] === "warn" ? "tone-" + i[3] : "");
        return `<div class="ic-summary-card is-clickable ${cls}" data-kpi="${frappe.utils.escape_html(i[0])}" role="button" tabindex="0" title="Click to open the list"><div class="label">${frappe.utils.escape_html(i[0])}</div><div class="value">${value}</div></div>`;
      }).join("");
      bindKpiClicks(grid);
      grid.querySelectorAll(".ic-summary-card").forEach((el) => {
        el.onkeydown = function (ev) { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); el.click(); } };
      });
    }
  });

  if (!canRead("Lead")) hidePanel("ic-my-leads");
  frappe.call({
    method: "instacertify.hr.dashboard.get_workdesk_insights",
    args: { limit: 8 },
    silent: true,
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

  if (!canRead("Lead")) hidePanel("ic-lead-hub");
  else frappe.call({
    method: "instacertify.crm.dashboard.get_lead_contact_prompts",
    args: { limit: 10 },
    silent: true,
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
        return `<div class="ic-lead-prompt ic-lead-hub-card ${urg}" role="link" tabindex="0" data-href="/app/lead/${encodeURIComponent(row.name)}">
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
        </div>`;
      }).join("");
      // A phone link inside a card link is not valid HTML and broke the card apart,
      // so the card is a plain block that opens the lead on click or Enter.
      el.querySelectorAll(".ic-lead-hub-card[data-href]").forEach((card) => {
        const open_lead = (ev) => {
          if (ev.target.closest && ev.target.closest("a")) return;
          const href = card.getAttribute("data-href");
          if (ev.ctrlKey || ev.metaKey) { window.open(href, "_blank"); return; }
          frappe.set_route(href.replace(/^\/app\//, "").split("/").map(decodeURIComponent));
        };
        card.addEventListener("click", open_lead);
        card.addEventListener("keydown", (ev) => { if (ev.key === "Enter") open_lead(ev); });
      });
    }
  });

  if (!canRead("Helpdesk Ticket")) hidePanel("ic-helpdesk-panel");
  else frappe.call({
    method: "instacertify.helpdesk.api.get_open_ticket_summary",
    args: { limit: 8 },
    silent: true,
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
      // Show only the HR links this person is allowed to open; the others ended
      // in a "Not permitted" pop-up.
      const canOpen = (route) => {
        const slug = String(route || "").split("?")[0].split("/").filter(Boolean)[1];
        return !!(slug && frappe.router && frappe.router.routes && frappe.router.routes[slug]);
      };
      if (links) {
        links.innerHTML = (d.links || []).filter(l => canOpen(l.route)).map(l =>
          `<a class="ic-hr-link" href="${esc(l.route)}">${esc(l.label)}</a>`
        ).join("");
      }
      const hrAll = root_element.querySelector(".ic-hr-panel .ic-workdesk-head .ic-view-all");
      if (hrAll && !canOpen(hrAll.getAttribute("href"))) hrAll.style.setProperty("display", "none", "important");
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


def _css_version() -> str:
	"""Modified time of the app stylesheet, so a deploy is not hidden by the browser cache."""
	import os

	path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public", "css", "instacertify.css")
	try:
		return str(int(os.path.getmtime(path)))
	except OSError:
		return "1"


def _upsert_html_block(name, html, script, style=None):
	legacy = f"IC {name}" if not name.startswith("IC ") else None
	if legacy and frappe.db.exists("Custom HTML Block", legacy) and not frappe.db.exists("Custom HTML Block", name):
		try:
			frappe.rename_doc("Custom HTML Block", legacy, name, force=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Rename HTML block {legacy}")

	# Shadow DOM blocks only see desk.bundle.css unless style is set here.
	block_style = (style if style is not None else _SHADOW_THEME_CSS).replace(
		"__IC_CSS_VERSION__", _css_version()
	)

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
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap");
@import url("/assets/instacertify/css/instacertify.css?v=__IC_CSS_VERSION__");
:host, * {
  font-family: "Inter", "Segoe UI", sans-serif !important;
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
  background: #ffffff;
  color: #21263c;
  border: 1px solid #e3e6ef;
  border-radius: 12px;
  padding: 20px 22px;
  margin-bottom: 16px;
  box-shadow: 0 1px 2px rgba(33, 38, 60, 0.05), 0 8px 24px rgba(33, 38, 60, 0.04);
}
.ic-greeting-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: clamp(1.85rem, 3.2vw, 2.45rem);
  font-weight: 800;
  letter-spacing: -0.04em;
  line-height: 1.05;
  color: #21263c;
  margin: 0 0 8px;
  font-family: "Inter", sans-serif !important;
  text-shadow: none;
}
.ic-home-brand-icon {
  width: 48px;
  height: 48px;
  flex: 0 0 48px;
  border-radius: 50%;
  object-fit: contain;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.18);
  background: transparent;
}
.ic-greeting-brand-text,
.ic-greeting-brand-text span,
.ic-greeting-brand > span:not(.ic-greeting-brand-text) { color: #21263c !important; }
.ic-greeting h2 {
  margin: 0 0 6px;
  font-weight: 500;
  font-size: 1.05rem;
  color: #21263c !important;
  font-family: "Inter", sans-serif !important;
}
.ic-greeting .ic-datetime { opacity: 1; font-size: 0.88rem; color: #6c718a; }

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
  box-shadow: inset 4px 0 0 #EC691F, 0 10px 24px rgba(236,105,31,0.1) !important;
}
.ic-lead-prompt.upcoming, .ic-lead-hub-card.upcoming {
  background: linear-gradient(165deg, #f0f9fc 0%, #fff 55%) !important;
  box-shadow: inset 4px 0 0 #1565C0, 0 10px 24px rgba(10,143,181,0.08) !important;
}
.ic-lead-prompt-when.overdue { background: #c0392b !important; color: #fff !important; }
.ic-lead-prompt-when.today { background: #EC691F !important; color: #fff !important; }
.ic-lead-prompt-when.upcoming { background: #1565C0 !important; color: #fff !important; }
.ic-lead-hub-counts {
  background: linear-gradient(90deg, #EC691F, #C45512) !important;
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
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 200px), 1fr)) !important;
  gap: 12px !important;
  width: 100% !important;
  align-items: stretch !important;
}
.ic-explore-card, .ic-summary-card {
  aspect-ratio: auto !important;
  display: flex !important;
  flex-direction: column !important;
  overflow: hidden !important;
  border-radius: 12px !important;
  min-height: 112px !important;
  height: auto !important;
}
.ic-summary-card {
  justify-content: space-between !important;
  padding: 14px 12px !important;
  border: 1px solid rgba(13,71,161,0.1) !important;
  border-top: 4px solid #0D47A1 !important;
  border-left: 1px solid rgba(13,71,161,0.1) !important;
}
.ic-summary-card:nth-child(3n+1) { border-top-color: #0D47A1 !important; }
.ic-summary-card:nth-child(3n+2) { border-top-color: #EC691F !important; }
.ic-summary-card:nth-child(3n) { border-top-color: #1565C0 !important; }
.ic-summary-card:nth-child(3n) .value { color: #1565C0 !important; }
.ic-summary-card.accent .value, .ic-summary-card:nth-child(even) .value { color: #EC691F !important; }
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
.ic-explore-card.accent-citrus { border-top: 4px solid #EC691F; }
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
  aspect-ratio: auto !important;
  min-height: 112px !important;
  height: auto !important;
  padding: 12px !important;
  border-radius: 12px !important;
}
.ic-lead-prompt-list {
  display: grid !important;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 220px), 1fr)) !important;
  gap: 12px !important;
  width: 100% !important;
  align-items: stretch !important;
}
.ic-lead-prompt, .ic-lead-hub-card {
  aspect-ratio: auto !important;
  min-height: 120px !important;
  height: auto !important;
  overflow: hidden !important;
  display: flex !important;
  flex-direction: column !important;
}
.ic-workdesk-grid {
  display: grid !important;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr)) !important;
  gap: 12px !important;
  width: 100% !important;
  align-items: stretch !important;
}
@media (max-width: 900px) {
  .ic-summary-grid, .ic-explore-grid, .ic-project-grid, .ic-lead-prompt-list {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }
}
@media (max-width: 560px) {
  .ic-summary-grid, .ic-explore-grid, .ic-project-grid, .ic-lead-prompt-list, .ic-workdesk-grid {
    grid-template-columns: 1fr !important;
  }
  .ic-greeting { padding: 16px !important; }
}

/* ==========================================================================
   Home layout: what needs attention first, then my work, numbers, shortcuts.
   Uses the desk design tokens (they inherit into this block).
   ========================================================================== */
#ic-home-root { color: var(--ic-ink, #21263c); }
#ic-home-root *, #ic-crm-tracker * { font-family: "Inter", "Segoe UI", sans-serif !important; }

.ic-greeting {
  display: flex !important;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 14px;
  padding: 12px 16px !important;
  margin-bottom: 12px !important;
  background: var(--fg-color, #fff) !important;
  background-image: none !important;
  border: 1px solid var(--ic-border, #e3e6ef) !important;
  border-radius: 12px !important;
  box-shadow: none !important;
}
.ic-greeting::before, .ic-greeting::after { display: none !important; }
.ic-greeting-brand { font-size: 18px !important; font-weight: 700 !important; margin: 0 !important; gap: 8px !important; letter-spacing: -0.02em !important; }
.ic-home-brand-icon { width: 28px !important; height: 28px !important; flex: 0 0 28px !important; box-shadow: none !important; }
.ic-greeting h2 { margin: 0 !important; font-size: 15px !important; font-weight: 600 !important; padding-left: 14px; border-left: 1px solid var(--ic-border, #e3e6ef); }
.ic-greeting .ic-datetime { margin-left: auto; font-size: 13px !important; color: var(--ic-muted, #6c718a) !important; }

.ic-today {
  background: var(--fg-color, #fff);
  border: 1px solid var(--ic-border, #e3e6ef);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 12px;
}
.ic-today-head { display: flex; flex-wrap: wrap; align-items: baseline; gap: 2px 12px; margin-bottom: 10px; }
.ic-today-title, .ic-section-label, .ic-workdesk-title, .ic-lead-prompt-title, .ic-explore-title, .ic-crm-tracker-title, .ic-project-section-head h3 {
  font-size: 15px !important;
  font-weight: 600 !important;
  letter-spacing: -0.01em !important;
  color: var(--ic-ink, #21263c) !important;
  margin: 0 !important;
}
.ic-section-label { margin: 16px 0 8px !important; }
.ic-today-sub, .ic-workdesk-sub, .ic-lead-prompt-sub, .ic-explore-sub { font-size: 12px !important; color: var(--ic-muted, #6c718a) !important; }
.ic-today-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 260px), 1fr)); gap: 8px; }
.ic-today-item {
  display: flex; align-items: center; gap: 10px;
  min-height: 48px; padding: 8px 12px;
  text-align: left; cursor: pointer;
  background: var(--tone-bg);
  border: 1px solid transparent; border-left: 3px solid var(--tone);
  border-radius: 10px;
  color: var(--ic-ink, #21263c);
}
.ic-today-item:hover { border-color: var(--tone); }
.ic-today-item:focus-visible, .ic-summary-card:focus-visible, .ic-explore-card:focus-visible, .ic-view-all:focus-visible {
  outline: 2px solid var(--ic-accent, #408dfb); outline-offset: 2px;
}
.ic-today-count { flex: 0 0 auto; min-width: 28px; font-size: 20px; font-weight: 700; line-height: 1; color: var(--tone); font-variant-numeric: tabular-nums; }
.ic-today-text { flex: 1 1 auto; font-size: 13px; font-weight: 500; line-height: 1.3; }
.ic-today-go { flex: 0 0 auto; font-size: 12px; font-weight: 600; color: var(--tone); }
.ic-today-item.tone-danger { --tone: var(--ic-danger, #c02626); --tone-bg: var(--ic-danger-bg, #fdecec); }
.ic-today-item.tone-warn { --tone: var(--ic-warn, #955700); --tone-bg: var(--ic-warn-bg, #fff4e5); }
.ic-today-item.tone-info { --tone: var(--ic-info, #1b62b0); --tone-bg: var(--ic-info-bg, #ebf3fe); }
.ic-today-item.tone-ok { --tone: var(--ic-ok, #0b7a4a); --tone-bg: var(--ic-ok-bg, #e5f8ef); }
.ic-today-clear, .ic-today-wait { font-size: 13px; color: var(--ic-muted, #6c718a); }
.ic-today-clear { color: var(--ic-ok, #0b7a4a); font-weight: 500; }

/* My work: three panels that are only as tall as what is in them */
.ic-workdesk-grid { margin-bottom: 4px; align-items: start !important; }
.ic-workdesk-panel, .ic-hr-panel, .ic-lead-prompt-panel {
  background: var(--fg-color, #fff) !important;
  background-image: none !important;
  border: 1px solid var(--ic-border, #e3e6ef) !important;
  border-left: 1px solid var(--ic-border, #e3e6ef) !important;
  border-radius: 12px !important;
  box-shadow: none !important;
  padding: 14px 16px !important;
  min-height: 0 !important;
  height: auto !important;
  margin: 0 0 12px !important;
}
.ic-workdesk-head, .ic-lead-prompt-header { display: flex !important; flex-wrap: wrap; align-items: flex-start; justify-content: space-between; gap: 8px 12px; margin-bottom: 8px !important; }
.ic-workdesk-head > div:first-child, .ic-lead-prompt-header > div:first-child { flex: 1 1 140px; min-width: 0; }
.ic-workdesk-actions, .ic-lead-hub-actions { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.ic-view-all {
  display: inline-flex !important; align-items: center;
  min-height: 30px; padding: 4px 10px !important; margin: 0 !important;
  font-size: 12px !important; font-weight: 600 !important;
  color: var(--ic-ink, #21263c) !important;
  background: var(--fg-color, #fff) !important;
  border: 1px solid var(--ic-border, #e3e6ef) !important;
  border-radius: 8px !important;
  text-decoration: none !important; white-space: nowrap;
}
.ic-view-all:hover { border-color: var(--ic-accent, #408dfb) !important; }
.ic-workdesk-row { min-height: 0 !important; }
.ic-lead-prompt-empty { padding: 4px 0 !important; margin: 0 !important; font-size: 13px !important; color: var(--ic-muted, #6c718a) !important; background: none !important; border: 0 !important; text-align: left !important; }
.ic-focus-sales .ic-wd-leads, .ic-focus-delivery .ic-wd-tasks { order: -1; }

/* Numbers: quiet when zero, amber or red only when something is waiting */
.ic-summary-grid { grid-template-columns: repeat(auto-fit, minmax(min(100%, 150px), 1fr)) !important; gap: 8px !important; margin-bottom: 16px; }
.ic-summary-card {
  min-height: 0 !important;
  padding: 10px 12px !important;
  background: var(--fg-color, #fff) !important;
  background-image: none !important;
  border: 1px solid var(--ic-border, #e3e6ef) !important;
  border-top: 1px solid var(--ic-border, #e3e6ef) !important;
  border-radius: 10px !important;
  box-shadow: none !important;
  gap: 4px;
}
.ic-summary-card:nth-child(n) { border-top-color: var(--ic-border, #e3e6ef) !important; }
.ic-summary-card::before, .ic-summary-card::after { display: none !important; }
.ic-summary-grid .ic-summary-card.ic-summary-card, .ic-summary-grid .ic-summary-card.accent { background: var(--fg-color, #fff) !important; background-image: none !important; }
.ic-summary-card:hover { border-color: var(--ic-accent, #408dfb) !important; transform: none !important; }
.ic-summary-card .label { font-size: 11px !important; font-weight: 600 !important; letter-spacing: 0.04em; color: var(--ic-muted, #6c718a) !important; }
.ic-summary-card .value, .ic-summary-card.accent .value, .ic-summary-card:nth-child(even) .value, .ic-summary-card:nth-child(3n) .value {
  font-size: 22px !important; font-weight: 700 !important; line-height: 1.15 !important;
  color: var(--ic-ink, #21263c) !important; font-variant-numeric: tabular-nums;
}
.ic-summary-card.is-zero .value { color: #9aa0b5 !important; font-weight: 600 !important; }
.ic-summary-card.tone-warn .value { color: var(--ic-warn, #955700) !important; }
.ic-summary-card.tone-danger .value { color: var(--ic-danger, #c02626) !important; }
.ic-summary-card.tone-warn { border-left: 3px solid var(--ic-warn, #955700) !important; }
.ic-summary-card.tone-danger { border-left: 3px solid var(--ic-danger, #c02626) !important; }

/* Shortcuts: one compact row per tile; the description shows on hover */
.ic-explore-panel { margin-bottom: 16px !important; }
.ic-explore-head { margin-bottom: 8px; }
.ic-explore-grid { grid-template-columns: repeat(auto-fit, minmax(min(100%, 230px), 1fr)) !important; gap: 8px !important; }
.ic-explore-card {
  flex-direction: row !important; align-items: center !important; gap: 10px;
  min-height: 52px !important; padding: 8px 12px !important;
  background: var(--fg-color, #fff) !important; background-image: none !important;
  border: 1px solid var(--ic-border, #e3e6ef) !important;
  border-top: 1px solid var(--ic-border, #e3e6ef) !important;
  border-radius: 10px !important; box-shadow: none !important;
  transition: border-color 0.12s ease !important;
}
.ic-explore-card:hover { transform: none !important; box-shadow: none !important; border-color: var(--ic-accent, #408dfb) !important; }
.ic-explore-card-top { display: contents !important; }
.ic-explore-icon { order: 1; width: 30px !important; height: 30px !important; flex: 0 0 30px !important; background: var(--ic-accent-soft, #ebf3fe) !important; color: var(--ic-action, #065175) !important; }
.ic-explore-card-title { order: 2; flex: 1 1 auto; min-width: 0; font-size: 13px !important; font-weight: 600 !important; color: var(--ic-ink, #21263c) !important; -webkit-line-clamp: 2; }
.ic-explore-card-meta { order: 3; margin-left: 0 !important; flex: 0 0 auto; }
.ic-explore-card-title { word-break: normal !important; overflow-wrap: normal !important; hyphens: none !important; line-height: 1.25 !important; }
.ic-explore-card-sub { display: none !important; }
.ic-explore-card::before, .ic-explore-card::after { display: none !important; }
.ic-explore-count { background: var(--ic-neutral-bg, #eceef4) !important; color: var(--ic-neutral, #565b73) !important; font-size: 11px !important; border-radius: 999px !important; }
.ic-explore-action { background: var(--ic-warn-bg, #fff4e5) !important; color: var(--ic-warn, #955700) !important; font-size: 10.5px !important; }

/* Follow-up, helpdesk, chat, HR: status colours follow the same five meanings */
.ic-lead-prompt-list { gap: 8px !important; }
.ic-lead-prompt, .ic-lead-hub-card { min-height: 0 !important; border-radius: 10px !important; }
.ic-lead-hub-card[data-href] { cursor: pointer; }
.ic-lead-hub-card:focus-visible { outline: 2px solid var(--ic-accent, #408dfb); outline-offset: 2px; }
.ic-lead-prompt-list { grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr)) !important; }
.ic-lead-prompt.overdue, .ic-lead-hub-card.overdue { background: var(--ic-danger-bg, #fdecec) !important; background-image: none !important; box-shadow: inset 3px 0 0 var(--ic-danger, #c02626) !important; }
.ic-lead-prompt.today, .ic-lead-hub-card.today { background: var(--ic-warn-bg, #fff4e5) !important; background-image: none !important; box-shadow: inset 3px 0 0 var(--ic-warn, #955700) !important; }
.ic-lead-prompt.upcoming, .ic-lead-hub-card.upcoming { background: var(--fg-color, #fff) !important; background-image: none !important; box-shadow: inset 3px 0 0 var(--ic-info, #1b62b0) !important; border: 1px solid var(--ic-border, #e3e6ef); }
.ic-lead-prompt-when { border-radius: 999px !important; font-size: 11px !important; font-weight: 600 !important; padding: 2px 8px !important; }
.ic-lead-prompt-when.overdue, .ic-lead-hub-chip.overdue { background: var(--ic-danger, #c02626) !important; color: #fff !important; }
.ic-lead-prompt-when.today { background: var(--ic-warn, #955700) !important; color: #fff !important; }
.ic-lead-prompt-when.upcoming, .ic-lead-hub-chip.upcoming { background: var(--ic-info, #1b62b0) !important; color: #fff !important; }
.ic-lead-hub-counts { background: var(--ic-warn-bg, #fff4e5) !important; background-image: none !important; color: var(--ic-warn, #955700) !important; border-radius: 999px !important; font-size: 12px !important; font-weight: 600 !important; padding: 5px 10px !important; }
.ic-lead-hub-legend { margin-bottom: 8px; }
.ic-lead-prompt-connected { display: inline-block; white-space: nowrap; }
.ic-lead-hub-grid { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important; gap: 8px 12px !important; }
.ic-lead-hub-grid .ic-lead-hub-cell:nth-child(3) { grid-column: 1 / -1; }
.ic-explore-count { -webkit-text-fill-color: var(--ic-neutral, #565b73) !important; }
.ic-lead-hub-counts { -webkit-text-fill-color: var(--ic-warn, #955700) !important; }
.ic-hr-columns { gap: 8px !important; align-items: start !important; }
.ic-hr-columns > div { aspect-ratio: auto !important; overflow: visible !important; min-height: 0 !important; height: auto !important; padding: 10px 12px !important; border-radius: 10px !important; background: var(--subtle-fg, #f7f8fc) !important; border: 1px solid var(--ic-border, #e3e6ef) !important; }
.ic-hr-col-title { font-size: 11px !important; font-weight: 600 !important; letter-spacing: 0.04em; color: var(--ic-muted, #6c718a) !important; }
.ic-hr-links { margin-top: 10px !important; }
.ic-hr-link { min-height: 30px; font-size: 12px !important; }
.ic-project-section-head { margin: 4px 0 8px !important; align-items: center; }
.ic-project-empty { padding: 12px 16px !important; min-height: 0 !important; font-size: 13px; color: var(--ic-muted, #6c718a); text-align: left !important; border-radius: 10px !important; }
.ic-crm-tracker-title { margin-bottom: 8px !important; }

@media (max-width: 560px) {
  .ic-greeting h2 { padding-left: 0; border-left: 0; flex: 1 1 100%; }
  .ic-greeting .ic-datetime { margin-left: 0; }
  .ic-today-go { display: none; }
  .ic-summary-grid, .ic-explore-grid { grid-template-columns: repeat(2, minmax(0, 1fr)) !important; }
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
      colors: colors || ["#0D47A1", "#EC691F", "#2a9d8f", "#e9c46a", "#264653", "#f4a261"]
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
      makeChart(root_element.getElementById("ic-crm-month-bar"), "bar", month.map(x=>x.label), month.map(x=>x.count), ["#EC691F", "#FFAB91"]);
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
		{"id": "sc_testing", "type": "shortcut", "data": {"shortcut_name": "Testing & Samples", "col": 2}},
		{"id": "sc_labs", "type": "shortcut", "data": {"shortcut_name": "Laboratories", "col": 2}},
		{"id": "sc_quote_templates", "type": "shortcut", "data": {"shortcut_name": "Quote Format Library", "col": 2}},
		{"id": "sc_docs", "type": "shortcut", "data": {"shortcut_name": "Documents Collection Sheets", "col": 2}},
		{"id": "sc_doc_lib", "type": "shortcut", "data": {"shortcut_name": "Document Collection Library", "col": 2}},
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
		{"label": "Testing & Samples", "link_to": "testing-samples", "type": "Page"},
		{"label": "Laboratories", "link_to": "IC Laboratory", "type": "DocType", "doc_view": "List"},
		{"label": "Quote Format Library", "link_to": "quote-format-library", "type": "Page", "doc_view": ""},
		{"label": "Documents Collection Sheets", "link_to": "IC Document Request", "type": "DocType", "doc_view": "List"},
		{"label": "Document Collection Library", "link_to": "document-collection-library", "type": "Page"},
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
		{"label": "Testing & Samples", "link_type": "Page", "link_to": "testing-samples", "type": "Link"},
		{"label": "Laboratory Library", "type": "Card Break"},
		{"label": "Register / Manage Labs", "link_type": "DocType", "link_to": "IC Laboratory", "type": "Link"},
		{"label": "Upload Laboratory / Scope", "link_type": "DocType", "link_to": "IC Laboratory", "type": "Link"},
		{"label": "Documents", "type": "Card Break"},
		{"label": "Documents Collection Sheets", "link_type": "DocType", "link_to": "IC Document Request", "type": "Link"},
		{"label": "Document Collection Library", "link_type": "Page", "link_to": "document-collection-library", "type": "Link"},
		{"label": "Sample Dispatch Collection Sheets", "link_type": "DocType", "link_to": "IC Sample Dispatch Collection", "type": "Link"},
		{"label": "Document Collection Sheet Templates", "link_type": "DocType", "link_to": "IC Document Checklist Template", "type": "Link"},
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
		{"label": "Bank Accounts", "link_type": "DocType", "link_to": "IC Bank Account", "type": "Link"},
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

	_protect_workspace_from_orphan_cleanup(name)


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
		{"public": 1, "is_hidden": 0, "sequence_id": sequence_id, "module": None, "app": None},
		update_modified=False,
	)
