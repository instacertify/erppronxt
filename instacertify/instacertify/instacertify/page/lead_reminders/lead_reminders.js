frappe.pages["lead-reminders"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Lead Reminders"),
		single_column: true,
	});

	frappe.breadcrumbs.add({
		label: __("Instacertify Home"),
		route: "/app/instacertify-home",
	});

	page.set_title(__("Lead Reminders"));
	page.main.addClass("ic-lead-reminders-page");

	const PAGE_SIZE = 20;
	const state = {
		filter: (frappe.route_options && frappe.route_options.filter) || "all",
		rows: [],
		shown: PAGE_SIZE,
		due_count: 0,
		upcoming_count: 0,
	};

	page.main.html(`
		<div class="ic-lr-page">
			<header class="ic-lr-hero">
				<div class="ic-lr-hero-copy">
					<div class="ic-lr-kicker">${__("CRM follow-up")}</div>
					<h1 class="ic-lr-title">${__("Lead Reminders")}</h1>
					<p class="ic-lr-sub">${__(
						"All follow-ups in one outlined table. Open a row to update the lead, phone, and remarks."
					)}</p>
				</div>
				<div class="ic-lr-hero-actions">
					<span class="ic-lr-counts" id="ic-lr-counts"></span>
					<button type="button" class="btn btn-default btn-sm ic-lr-btn" id="ic-lr-refresh">
						${__("Refresh")}
					</button>
					<a class="btn btn-primary btn-sm ic-lr-btn" href="/app/lead/new">
						${__("New Lead")}
					</a>
					<a class="btn btn-primary btn-sm ic-lr-btn" href="/app/lead">
						${__("All Leads")}
					</a>
				</div>
			</header>
			<div class="ic-lr-filters" id="ic-lr-filters" role="tablist">
				<button type="button" class="ic-lr-filter" data-filter="all">${__("All")}</button>
				<button type="button" class="ic-lr-filter" data-filter="due">${__("Due now")}</button>
				<button type="button" class="ic-lr-filter" data-filter="upcoming">${__("Upcoming")}</button>
				<button type="button" class="ic-lr-filter" data-filter="mine">${__("Assigned to me")}</button>
			</div>
			<div class="ic-lr-table-wrap" id="ic-lr-board">
				<div class="ic-lr-empty">${__("Loading reminders…")}</div>
			</div>
		</div>
	`);

	const $board = page.main.find("#ic-lr-board");
	const $counts = page.main.find("#ic-lr-counts");
	const $filters = page.main.find("#ic-lr-filters");

	function esc(v) {
		return frappe.utils.escape_html(v == null ? "" : String(v));
	}

	function setActiveFilter() {
		$filters.find(".ic-lr-filter").each(function () {
			const on = $(this).attr("data-filter") === state.filter;
			$(this).toggleClass("is-active", on).toggleClass("active", on);
		});
	}

	function urgencyLabel(urg) {
		if (urg === "overdue") return __("Overdue");
		if (urg === "today") return __("Today");
		return __("Upcoming");
	}

	function rowHtml(row) {
		const person = esc(row.contact_person || row.title || row.name);
		const company = esc(row.company || "");
		const when = esc(row.due_label || row.ic_next_contact_date || "—");
		const phone = esc(row.phone || "—");
		const owner = esc(row.call_with || "—");
		const stage = esc(row.pipeline_stage || row.status || "—");
		const urg = esc(row.urgency || "upcoming");
		let note = row.has_remarks ? String(row.remarks || "") : "";
		if (note.length > 140) note = note.slice(0, 137) + "…";
		note = note ? esc(note) : `<span class="muted">${__("No remarks yet")}</span>`;
		const phoneHref = row.phone ? "tel:" + String(row.phone).replace(/\s+/g, "") : "";
		const phoneCell = row.phone
			? phoneHref
				? `<a class="ic-lr-phone" href="${phoneHref}" onclick="event.stopPropagation()">${phone}</a>`
				: phone
			: "—";
		return `<tr class="ic-lr-row ${urg}" data-name="${esc(row.name)}" tabindex="0">
			<td>
				<div class="ic-lr-person">${person}</div>
				${company ? `<div class="ic-lr-company">${company}</div>` : ""}
				<div class="ic-lr-id">${esc(row.name)}</div>
			</td>
			<td><span class="ic-lr-badge ${urg}">${when}</span>
				<div class="ic-lr-urg-label">${urgencyLabel(row.urgency)}</div>
			</td>
			<td>${phoneCell}</td>
			<td>${owner}</td>
			<td>${stage}</td>
			<td class="ic-lr-remarks">${note}</td>
			<td class="ic-lr-actions">
				<a class="btn btn-xs btn-primary ic-lr-open" href="/app/lead/${encodeURIComponent(row.name)}">${__(
					"Open"
				)}</a>
			</td>
		</tr>`;
	}

	function render() {
		const rows = state.rows || [];
		const total = rows.length;
		if (!total) {
			$board.html(
				`<div class="ic-lr-empty">${__(
					"No reminders in this view. Set Next Contact Date on a Lead to see it here."
				)}</div>`
			);
			return;
		}
		const shown = Math.min(state.shown, total);
		const slice = rows.slice(0, shown);
		const remaining = total - shown;
		const moreBar =
			remaining > 0
				? `<div class="ic-lr-show-more-bar">
					<span class="ic-lr-show-more-meta">${__("Showing {0} of {1} follow-ups", [
						shown,
						total,
					])}</span>
					<button type="button" class="btn btn-sm btn-primary ic-lr-btn" id="ic-lr-show-more">
						${__("Show more")} (${Math.min(PAGE_SIZE, remaining)})
					</button>
				</div>`
				: `<div class="ic-lr-show-more-bar is-all">
					<span class="ic-lr-show-more-meta">${__("Showing all {0} follow-ups", [total])}</span>
				</div>`;

		$board.html(`
			<div class="ic-lr-table-scroll">
				<table class="ic-lr-table" role="table">
					<thead>
						<tr>
							<th>${__("Whom to call")}</th>
							<th>${__("When")}</th>
							<th>${__("Phone")}</th>
							<th>${__("Connect with")}</th>
							<th>${__("Status")}</th>
							<th>${__("Customer remarks")}</th>
							<th></th>
						</tr>
					</thead>
					<tbody>${slice.map(rowHtml).join("")}</tbody>
				</table>
			</div>
			${moreBar}
		`);

		$board.find(".ic-lr-row").on("click", function (e) {
			if ($(e.target).closest("a,button").length) return;
			const name = $(this).attr("data-name");
			if (name) frappe.set_route("Form", "Lead", name);
		});
		$board.find(".ic-lr-row").on("keydown", function (e) {
			if (e.key === "Enter" || e.key === " ") {
				e.preventDefault();
				$(this).trigger("click");
			}
		});
		$board.find("#ic-lr-show-more").on("click", function () {
			state.shown += PAGE_SIZE;
			render();
		});
	}

	function load() {
		setActiveFilter();
		state.shown = PAGE_SIZE;
		$board.html(`<div class="ic-lr-empty">${__("Loading reminders…")}</div>`);
		frappe.call({
			method: "instacertify.crm.dashboard.get_lead_reminders_page",
			args: { limit: 200, filter: state.filter },
			callback(r) {
				const d = r.message || {};
				state.rows = d.prompts || [];
				state.due_count = d.due_count || 0;
				state.upcoming_count = d.upcoming_count || 0;
				$counts.text(
					__((state.due_count || 0) + " due · " + (state.upcoming_count || 0) + " upcoming")
				);
				render();
			},
		});
	}

	$filters.on("click", ".ic-lr-filter", function () {
		state.filter = $(this).attr("data-filter") || "all";
		load();
	});
	page.main.find("#ic-lr-refresh").on("click", () => load());

	load();
};

frappe.pages["lead-reminders"].on_page_show = function () {
	if (frappe.route_options && frappe.route_options.filter) {
		frappe.route_options = null;
	}
};
