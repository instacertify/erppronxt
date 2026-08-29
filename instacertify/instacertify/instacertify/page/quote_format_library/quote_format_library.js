frappe.pages["quote-format-library"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Quote Format Library"),
		single_column: true,
	});

	frappe.breadcrumbs.add({
		label: __("Quotations"),
		route: "/app/quotation",
	});

	page.set_title(__("Quote Format Library"));
	page.main.addClass("ic-quote-lib-page");

	const CATEGORIES = [
		{ key: "Consulting", label: __("Consulting"), hint: __("BIS, TEC, WPC, consultancy packs") },
		{ key: "Testing", label: __("Testing"), hint: __("Lab test & sample commercials") },
		{ key: "Renewal", label: __("Renewal"), hint: __("Certificate / licence renewals") },
		{ key: "Service", label: __("Service"), hint: __("General service quotes") },
		{ key: "Multiple Products / Multiple Services", label: __("Multi Product / Service"), hint: __("Bundled multi-line quotes") },
		{ key: "Other", label: __("Other"), hint: __("Everything else") },
	];

	page.main.html(`
		<div class="ic-quote-lib">
			<div class="ic-quote-lib-head">
				<div>
					<div class="ic-quote-lib-kicker">${__("Quote formats")}</div>
					<div class="ic-quote-lib-title">${__("Library by category")}</div>
					<div class="ic-quote-lib-sub">${__(
						"Pick a category, then open a template or start a quotation. Keep each catalog simple — one type per folder."
					)}</div>
				</div>
				<div class="ic-quote-lib-tools">
					<input type="search" class="form-control" id="ic-qlib-search"
						placeholder="${__("Search templates…")}" />
					<button type="button" class="btn btn-default btn-sm" id="ic-qlib-upload">${__("Upload Format")}</button>
					<button type="button" class="btn btn-default btn-sm" id="ic-qlib-list">${__("Full List")}</button>
					<button type="button" class="btn btn-primary btn-sm" id="ic-qlib-new">${__("New Template")}</button>
				</div>
			</div>
			<div class="ic-quote-lib-cats" id="ic-qlib-cats" role="tablist" aria-label="${__("Quote categories")}"></div>
			<div class="ic-quote-lib-panel">
				<div class="ic-quote-lib-panel-head">
					<div>
						<div class="ic-quote-lib-panel-title" id="ic-qlib-panel-title">${__("All categories")}</div>
						<div class="ic-quote-lib-panel-sub" id="ic-qlib-panel-sub"></div>
					</div>
					<label class="ic-quote-lib-active-only">
						<input type="checkbox" id="ic-qlib-active" checked />
						${__("Active only")}
					</label>
				</div>
				<div class="ic-quote-lib-grid" id="ic-qlib-grid" aria-live="polite"></div>
			</div>
		</div>
	`);

	let state = {
		category: frappe.route_options && frappe.route_options.quotation_type
			? frappe.route_options.quotation_type
			: "",
		search: "",
		active_only: 1,
		catalog: null,
	};
	if (frappe.route_options) {
		frappe.route_options = null;
	}

	const $cats = page.main.find("#ic-qlib-cats");
	const $grid = page.main.find("#ic-qlib-grid");

	function esc(s) {
		return frappe.utils.escape_html(s || "");
	}

	function render_cats() {
		const counts = (state.catalog && state.catalog.counts) || {};
		const total = Object.values(counts).reduce((a, b) => a + (b || 0), 0);
		const chips = [
			{
				key: "",
				label: __("All"),
				hint: __("Every template"),
				count: total,
			},
		].concat(
			CATEGORIES.map((c) => ({
				...c,
				count: counts[c.key] || 0,
			}))
		);

		$cats.html(
			chips
				.map((c) => {
					const active = (state.category || "") === (c.key || "");
					return `<button type="button" class="ic-quote-lib-cat${active ? " active" : ""}"
						data-cat="${esc(c.key)}" role="tab" aria-selected="${active ? "true" : "false"}">
						<span class="ic-quote-lib-cat-label">${esc(c.label)}</span>
						<span class="ic-quote-lib-cat-count">${c.count}</span>
						<span class="ic-quote-lib-cat-hint">${esc(c.hint || "")}</span>
					</button>`;
				})
				.join("")
		);

		$cats.find(".ic-quote-lib-cat").on("click", function () {
			state.category = $(this).data("cat") || "";
			render_cats();
			render_templates();
		});
	}

	function render_templates() {
		const cat = state.category || "";
		const meta = CATEGORIES.find((c) => c.key === cat);
		page.main.find("#ic-qlib-panel-title").text(meta ? meta.label : __("All categories"));
		page.main
			.find("#ic-qlib-panel-sub")
			.text(meta ? meta.hint : __("Browse every quote format in the library."));

		const rows = ((state.catalog && state.catalog.templates) || []).filter((t) => {
			if (cat && t.quotation_type !== cat) return false;
			if (state.active_only && !cint(t.is_active)) return false;
			if (state.search) {
				const q = state.search.toLowerCase();
				const blob = [t.template_name, t.service_family, t.service_name, t.quotation_type]
					.join(" ")
					.toLowerCase();
				if (blob.indexOf(q) < 0) return false;
			}
			return true;
		});

		if (!rows.length) {
			$grid.html(
				`<div class="ic-quote-lib-empty">
					<div>${__("No templates in this category yet.")}</div>
					<button type="button" class="btn btn-primary btn-sm" id="ic-qlib-empty-new">${__("Add template")}</button>
				</div>`
			);
			$grid.find("#ic-qlib-empty-new").on("click", () => open_new(cat));
			return;
		}

		$grid.html(
			rows
				.map((t) => {
					const family = t.service_family || t.service_name || "";
					const active = cint(t.is_active)
						? `<span class="ic-quote-lib-badge on">${__("Active")}</span>`
						: `<span class="ic-quote-lib-badge off">${__("Inactive")}</span>`;
					const hasFile = t.uploaded_format
						? `<span class="ic-quote-lib-file">${__("Format file")}</span>`
						: "";
					return `<article class="ic-quote-lib-card" data-name="${esc(t.name)}">
						<div class="ic-quote-lib-card-top">
							<div class="ic-quote-lib-card-type">${esc(t.quotation_type)}</div>
							${active}
						</div>
						<h3 class="ic-quote-lib-card-name">${esc(t.template_name || t.name)}</h3>
						<div class="ic-quote-lib-card-meta">${esc(family) || "&nbsp;"}${hasFile}</div>
						<div class="ic-quote-lib-card-actions">
							<button type="button" class="btn btn-default btn-xs ic-qlib-open">${__("Open")}</button>
							<button type="button" class="btn btn-primary btn-xs ic-qlib-use">${__("Use in Quotation")}</button>
						</div>
					</article>`;
				})
				.join("")
		);

		$grid.find(".ic-qlib-open").on("click", function (e) {
			e.stopPropagation();
			frappe.set_route("Form", "IC Quotation Template", $(this).closest(".ic-quote-lib-card").data("name"));
		});
		$grid.find(".ic-qlib-use").on("click", function (e) {
			e.stopPropagation();
			const name = $(this).closest(".ic-quote-lib-card").data("name");
			const row = rows.find((r) => r.name === name);
			const qtype =
				row && row.quotation_type === "Service" ? "Consulting" : (row && row.quotation_type) || "Consulting";
			frappe.new_doc("Quotation", {
				ic_quotation_type: qtype,
				ic_quotation_template: name,
				ic_service_family: row && row.service_family,
			});
		});
		$grid.find(".ic-quote-lib-card").on("dblclick", function () {
			frappe.set_route("Form", "IC Quotation Template", $(this).data("name"));
		});
	}

	function open_new(cat) {
		frappe.new_doc("IC Quotation Template", {
			quotation_type: cat || "Consulting",
			is_active: 1,
		});
	}

	function load() {
		frappe.call({
			method: "instacertify.setup.library_upload.get_quote_library_catalog",
			freeze: true,
			callback(r) {
				state.catalog = r.message || { counts: {}, templates: [] };
				render_cats();
				render_templates();
			},
		});
	}

	page.main.find("#ic-qlib-upload").on("click", () => {
		instacertify.open_quote_format_upload({
			quotation_type: state.category || "Consulting",
			on_done() {
				load();
			},
		});
	});
	page.main.find("#ic-qlib-list").on("click", () => {
		const filters = {};
		if (state.category) filters.quotation_type = state.category;
		frappe.set_route("List", "IC Quotation Template", filters);
	});
	page.main.find("#ic-qlib-new").on("click", () => open_new(state.category));
	page.main.find("#ic-qlib-active").on("change", function () {
		state.active_only = this.checked ? 1 : 0;
		render_templates();
	});
	let timer = null;
	page.main.find("#ic-qlib-search").on("input", function () {
		state.search = ($(this).val() || "").trim();
		clearTimeout(timer);
		timer = setTimeout(render_templates, 200);
	});

	load();
};
