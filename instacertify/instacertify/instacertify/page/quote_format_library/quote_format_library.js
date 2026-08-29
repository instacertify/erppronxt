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
		{ key: "Consulting", label: __("Consulting"), hint: __("BIS, TEC, WPC, consultancy packs"), slug: "consulting" },
		{ key: "Testing", label: __("Testing"), hint: __("Lab test & sample commercials"), slug: "testing" },
		{ key: "Renewal", label: __("Renewal"), hint: __("Certificate / licence renewals"), slug: "renewal" },
		{ key: "Other", label: __("Other"), hint: __("Custom / miscellaneous"), slug: "other" },
	];

	function cat_slug(type) {
		const map = {
			Consulting: "consulting",
			Testing: "testing",
			Renewal: "renewal",
			Other: "other",
			Service: "consulting",
			"Multiple Products / Multiple Services": "other",
		};
		return map[type] || "other";
	}

	page.main.html(`
		<div class="ic-quote-lib">
			<div class="ic-quote-lib-head">
				<div>
					<div class="ic-quote-lib-kicker">${__("Quote formats")}</div>
					<div class="ic-quote-lib-title">${__("Library by category")}</div>
					<div class="ic-quote-lib-sub">${__(
						"Browse by category. Click Edit Template to change headings, narrative, and pricing. Or use a template in a new quotation."
					)}</div>
				</div>
				<div class="ic-quote-lib-tools">
					<input type="search" class="form-control" id="ic-qlib-search"
						placeholder="${__("Search name, family, tags…")}" />
					<button type="button" class="btn btn-default btn-sm" id="ic-qlib-dl-xlsx">${__("Excel Template")}</button>
					<button type="button" class="btn btn-default btn-sm" id="ic-qlib-dl-csv">${__("CSV Template")}</button>
					<button type="button" class="btn btn-default btn-sm" id="ic-qlib-import">${__("Import Spreadsheet")}</button>
					<button type="button" class="btn btn-default btn-sm" id="ic-qlib-upload">${__("Upload Format File")}</button>
					<button type="button" class="btn btn-default btn-sm" id="ic-qlib-list">${__("Full List")}</button>
					<button type="button" class="btn btn-primary btn-sm" id="ic-qlib-new">${__("New Template")}</button>
				</div>
			</div>
			<div class="ic-quote-lib-cats" id="ic-qlib-cats" role="tablist" aria-label="${__("Quote categories")}"></div>
			<div class="ic-quote-lib-tag-bar" id="ic-qlib-tags" aria-label="${__("Tags")}"></div>
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
		tag: "",
		search: "",
		active_only: 1,
		catalog: null,
	};
	if (frappe.route_options) {
		frappe.route_options = null;
	}

	const $cats = page.main.find("#ic-qlib-cats");
	const $tags = page.main.find("#ic-qlib-tags");
	const $grid = page.main.find("#ic-qlib-grid");

	function esc(s) {
		return frappe.utils.escape_html(s || "");
	}

	function collect_tags(templates) {
		const map = {};
		(templates || []).forEach((t) => {
			(t.tags || []).forEach((tag) => {
				map[tag] = (map[tag] || 0) + 1;
			});
		});
		return Object.keys(map)
			.sort((a, b) => a.localeCompare(b))
			.map((tag) => ({ tag, count: map[tag] }));
	}

	function download_template(fmt) {
		frappe.call({
			method: "instacertify.setup.library_upload.download_quote_format_upload_template",
			args: { fmt },
			freeze: true,
			freeze_message: __("Preparing {0}…", [fmt === "csv" ? "CSV" : "Excel"]),
			callback(r) {
				const m = r.message || {};
				if (m.file_url) window.open(m.file_url, "_blank");
			},
		});
	}

	function open_import() {
		const d = new frappe.ui.Dialog({
			title: __("Import Quote Formats (CSV / Excel)"),
			fields: [
				{
					fieldname: "file",
					fieldtype: "Attach",
					label: __("Spreadsheet File"),
					reqd: 1,
					description: __(
						"Upload the filled CSV or Excel template (.csv / .xlsx). Matching template_name updates; new names create."
					),
					options: (window.instacertify && instacertify.attach_options) || {},
				},
			],
			primary_action_label: __("Import"),
			primary_action(values) {
				frappe.call({
					method: "instacertify.setup.library_upload.import_quote_templates_from_spreadsheet",
					args: { file_url: values.file },
					freeze: true,
					freeze_message: __("Importing spreadsheet…"),
					callback(r) {
						d.hide();
						const m = r.message || {};
						frappe.msgprint({
							title: __("Import complete"),
							indicator: m.skipped_count ? "orange" : "green",
							message: m.message
								|| __(
									"{0} created, {1} updated, {2} skipped",
									[m.created_count || 0, m.updated_count || 0, m.skipped_count || 0]
								),
						});
						load();
					},
				});
			},
		});
		d.show();
		if (window.instacertify && instacertify.add_file_manager_hint) {
			instacertify.add_file_manager_hint(d, "file");
		}
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
					const slug = c.key ? cat_slug(c.key) : "all";
					return `<button type="button" class="ic-quote-lib-cat cat-${slug}${active ? " active" : ""}"
						data-cat="${esc(c.key)}" role="tab" aria-selected="${active ? "true" : "false"}">
						<span class="ic-quote-lib-cat-swatch" aria-hidden="true"></span>
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
			render_tag_bar();
			render_templates();
		});
	}

	function render_tag_bar() {
		const base = ((state.catalog && state.catalog.templates) || []).filter((t) => {
			if (state.category && t.quotation_type !== state.category) return false;
			return true;
		});
		const tags = collect_tags(base);
		if (!tags.length) {
			$tags.html(
				`<div class="ic-quote-lib-tag-empty">${__(
					"No tags yet — add a tags column when importing CSV/Excel."
				)}</div>`
			);
			return;
		}
		const chips = [
			`<button type="button" class="ic-quote-lib-tag${state.tag ? "" : " active"}" data-tag="">${__(
				"All tags"
			)}</button>`,
		].concat(
			tags.map(
				(t) =>
					`<button type="button" class="ic-quote-lib-tag${
						state.tag === t.tag ? " active" : ""
					}" data-tag="${esc(t.tag)}">${esc(t.tag)} <span>${t.count}</span></button>`
			)
		);
		$tags.html(chips.join(""));
		$tags.find(".ic-quote-lib-tag").on("click", function () {
			state.tag = $(this).data("tag") || "";
			render_tag_bar();
			render_templates();
		});
	}

	function render_templates() {
		const cat = state.category || "";
		const meta = CATEGORIES.find((c) => c.key === cat);
		page.main.find("#ic-qlib-panel-title").text(meta ? meta.label : __("All categories"));
		let sub = meta ? meta.hint : __("Browse every quote format in the library.");
		if (state.tag) {
			sub = __("Filtered by tag: {0}", [state.tag]);
		}
		page.main.find("#ic-qlib-panel-sub").text(sub);

		const rows = ((state.catalog && state.catalog.templates) || []).filter((t) => {
			if (cat && t.quotation_type !== cat) return false;
			if (state.active_only && !cint(t.is_active)) return false;
			if (state.tag) {
				const tags = (t.tags || []).map((x) => String(x).toLowerCase());
				if (tags.indexOf(String(state.tag).toLowerCase()) < 0) return false;
			}
			if (state.search) {
				const q = state.search.toLowerCase();
				const blob = [t.template_name, t.service_family, t.service_name, t.quotation_type]
					.concat(t.tags || [])
					.join(" ")
					.toLowerCase();
				if (blob.indexOf(q) < 0) return false;
			}
			return true;
		});

		if (!rows.length) {
			$grid.html(
				`<div class="ic-quote-lib-empty">
					<div>${__("No templates in this view yet.")}</div>
					<button type="button" class="btn btn-primary btn-sm" id="ic-qlib-empty-new">${__("Add template")}</button>
					<button type="button" class="btn btn-default btn-sm" id="ic-qlib-empty-import">${__("Import spreadsheet")}</button>
				</div>`
			);
			$grid.find("#ic-qlib-empty-new").on("click", () => open_new(cat));
			$grid.find("#ic-qlib-empty-import").on("click", open_import);
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
					const tagHtml = (t.tags || [])
						.map((tag) => `<span class="ic-quote-lib-card-tag">${esc(tag)}</span>`)
						.join("");
					return `<article class="ic-quote-lib-card cat-${cat_slug(t.quotation_type)}" data-name="${esc(t.name)}">
						<div class="ic-quote-lib-card-top">
							<div class="ic-quote-lib-card-type cat-${cat_slug(t.quotation_type)}">${esc(t.quotation_type)}</div>
							${active}
						</div>
						<h3 class="ic-quote-lib-card-name">${esc(t.template_name || t.name)}</h3>
						<div class="ic-quote-lib-card-meta">${esc(family) || "&nbsp;"}${hasFile}</div>
						${tagHtml ? `<div class="ic-quote-lib-card-tags">${tagHtml}</div>` : ""}
						<div class="ic-quote-lib-card-actions">
							<button type="button" class="btn btn-primary btn-xs ic-qlib-open">${__("Edit Template")}</button>
							<button type="button" class="btn btn-default btn-xs ic-qlib-use">${__("Use in Quotation")}</button>
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
		$grid.find(".ic-quote-lib-card-tag").on("click", function (e) {
			e.stopPropagation();
			state.tag = $(this).text();
			render_tag_bar();
			render_templates();
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
				render_tag_bar();
				render_templates();
			},
		});
	}

	page.main.find("#ic-qlib-dl-xlsx").on("click", () => download_template("xlsx"));
	page.main.find("#ic-qlib-dl-csv").on("click", () => download_template("csv"));
	page.main.find("#ic-qlib-import").on("click", open_import);
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
