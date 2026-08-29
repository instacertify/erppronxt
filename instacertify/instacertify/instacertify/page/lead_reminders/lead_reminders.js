frappe.pages["lead-reminders"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Lead Reminders"),
		single_column: true,
	});

	frappe.breadcrumbs.add({
		label: __("Instacertify Home"),
		route: "/app/workspaces/Instacertify%20Home",
	});

	page.set_title(__("Lead Reminders"));
	page.main.addClass("ic-lead-reminders-page");

	const state = {
		filter: (frappe.route_options && frappe.route_options.filter) || "all",
		rows: [],
	};

	page.main.html(`
		<div class="ic-lr-page">
			<header class="ic-lr-hero">
				<div>
					<div class="ic-lr-kicker">${__("CRM follow-up")}</div>
					<h1 class="ic-lr-title">${__("Lead Reminders")}</h1>
					<p class="ic-lr-sub">${__("Soft cards for overdue, today, and upcoming calls. Tap a card to open the lead.")}</p>
				</div>
				<div class="ic-lr-hero-actions">
					<span class="ic-lr-counts" id="ic-lr-counts"></span>
					<button type="button" class="btn btn-default btn-sm" id="ic-lr-refresh">${__("Refresh")}</button>
					<a class="btn btn-primary btn-sm" href="/app/lead">${__("All Leads")}</a>
				</div>
			</header>
			<div class="ic-lr-filters" id="ic-lr-filters" role="tablist">
				<button type="button" class="ic-lr-filter" data-filter="all">${__("All")}</button>
				<button type="button" class="ic-lr-filter" data-filter="due">${__("Due now")}</button>
				<button type="button" class="ic-lr-filter" data-filter="upcoming">${__("Upcoming")}</button>
				<button type="button" class="ic-lr-filter" data-filter="mine">${__("Assigned to me")}</button>
			</div>
			<div class="ic-lr-grid" id="ic-lr-grid">
				<div class="ic-lr-empty">${__("Loading reminders…")}</div>
			</div>
		</div>
	`);

	const $grid = page.main.find("#ic-lr-grid");
	const $counts = page.main.find("#ic-lr-counts");
	const $filters = page.main.find("#ic-lr-filters");

	function esc(v) {
		return frappe.utils.escape_html(v == null ? "" : String(v));
	}

	function setActiveFilter() {
		$filters.find(".ic-lr-filter").each(function () {
			const on = $(this).attr("data-filter") === state.filter;
			$(this).toggleClass("active", on);
		});
	}

	function cardHtml(row) {
		const person = esc(row.contact_person || row.title || row.name);
		const company = esc(row.company || "");
		const when = esc(row.due_label || row.ic_next_contact_date || "—");
		const phone = esc(row.phone || "");
		const owner = esc(row.call_with || "");
		const urg = esc(row.urgency || "upcoming");
		let note = row.has_remarks ? String(row.remarks || "") : "";
		if (note.length > 110) note = note.slice(0, 107) + "…";
		note = esc(note);
		const phoneHref = row.phone ? "tel:" + String(row.phone).replace(/\s+/g, "") : "";
		const phoneBit = phone
			? phoneHref
				? `<a class="ic-lr-phone" href="${phoneHref}" onclick="event.stopPropagation()">${phone}</a>`
				: `<span>${phone}</span>`
			: "";
		const meta = [phoneBit, owner].filter(Boolean).join(" · ");
		return `<a class="ic-lr-card ${urg}" href="/app/lead/${encodeURIComponent(row.name)}">
			<div class="ic-lr-card-top">
				<span class="ic-lr-badge ${urg}">${when}</span>
			</div>
			<div class="ic-lr-card-name">${person}</div>
			${company ? `<div class="ic-lr-card-company">${company}</div>` : ""}
			${meta ? `<div class="ic-lr-card-meta">${meta}</div>` : ""}
			${note ? `<div class="ic-lr-card-note">${note}</div>` : `<div class="ic-lr-card-note muted">${__("No remarks yet")}</div>`}
		</a>`;
	}

	function render() {
		const rows = state.rows || [];
		if (!rows.length) {
			$grid.html(
				`<div class="ic-lr-empty">${__(
					"No reminders in this view. Set Next Contact Date on a Lead to see it here."
				)}</div>`
			);
			return;
		}
		$grid.html(rows.map(cardHtml).join(""));
	}

	function load() {
		setActiveFilter();
		$grid.html(`<div class="ic-lr-empty">${__("Loading reminders…")}</div>`);
		frappe.call({
			method: "instacertify.crm.dashboard.get_lead_reminders_page",
			args: { limit: 60, filter: state.filter },
			callback(r) {
				const d = r.message || {};
				state.rows = d.prompts || [];
				$counts.text(
					__((d.due_count || 0) + " due · " + (d.upcoming_count || 0) + " upcoming")
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
	// Re-enter with route options filter if provided
	if (frappe.route_options && frappe.route_options.filter) {
		frappe.route_options = null;
	}
};
