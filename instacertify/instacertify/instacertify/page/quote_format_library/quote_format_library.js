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

	if (typeof instacertify !== "undefined" && instacertify.enable_full_width_desk) {
		instacertify.enable_full_width_desk();
	}

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

	function normalize_type(type) {
		if (type === "Service") return "Consulting";
		if (type === "Multiple Products / Multiple Services") return "Other";
		if (["Consulting", "Testing", "Renewal", "Other"].includes(type)) return type;
		return "Other";
	}

	page.main.html(`
		<div class="ic-quote-lib">
			<header class="ic-quote-lib-head">
				<div class="ic-quote-lib-head-copy">
					<div class="ic-quote-lib-kicker">${__("Quote formats")}</div>
					<h1 class="ic-quote-lib-title">${__("Format Library")}</h1>
					<p class="ic-quote-lib-sub">${__(
						"Browse by category, then by service family. Click a row to edit. Use Print or PDF to test."
					)}</p>
				</div>
				<div class="ic-quote-lib-toolbar">
					<input type="search" class="form-control ic-quote-lib-search" id="ic-qlib-search"
						placeholder="${__("Search templates…")}" />
					<label class="ic-quote-lib-active-only">
						<input type="checkbox" id="ic-qlib-active" checked />
						${__("Active only")}
					</label>
					<div class="dropdown ic-quote-lib-manage">
						<button type="button" class="btn btn-default btn-sm ic-qlib-manage-btn" aria-haspopup="true" aria-expanded="false">
							${__("Manage")} ▾
						</button>
						<div class="dropdown-menu dropdown-menu-right ic-qlib-manage-menu" style="display:none;">
							<a class="dropdown-item" href="#" id="ic-qlib-dl-xlsx">${__("Download Excel Template")}</a>
							<a class="dropdown-item" href="#" id="ic-qlib-dl-csv">${__("Download CSV Template")}</a>
							<a class="dropdown-item" href="#" id="ic-qlib-import">${__("Import Spreadsheet")}</a>
							<a class="dropdown-item" href="#" id="ic-qlib-upload">${__("Upload Format File")}</a>
							<div class="dropdown-divider"></div>
							<a class="dropdown-item" href="#" id="ic-qlib-list">${__("Open Full List")}</a>
						</div>
					</div>
					<button type="button" class="btn btn-primary btn-sm" id="ic-qlib-new">${__("New Template")}</button>
				</div>
			</header>

			<nav class="ic-quote-lib-tabs" id="ic-qlib-cats" role="tablist" aria-label="${__("Major categories")}"></nav>
			<div class="ic-quote-lib-tag-bar" id="ic-qlib-tags" aria-label="${__("Tags")}"></div>

			<div class="ic-quote-lib-body">
				<aside class="ic-quote-lib-rail" id="ic-qlib-rail" aria-label="${__("Jump to category")}"></aside>
				<div class="ic-quote-lib-main">
					<div class="ic-quote-lib-status" id="ic-qlib-status"></div>
					<div class="ic-quote-lib-sections" id="ic-qlib-grid" aria-live="polite"></div>
				</div>
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
		collapsed: {},
	};
	if (frappe.route_options) {
		frappe.route_options = null;
	}

	const $cats = page.main.find("#ic-qlib-cats");
	const $tags = page.main.find("#ic-qlib-tags");
	const $rail = page.main.find("#ic-qlib-rail");
	const $grid = page.main.find("#ic-qlib-grid");
	const $status = page.main.find("#ic-qlib-status");

	function esc(s) {
		return frappe.utils.escape_html(s || "");
	}

	function format_money(n) {
		const v = flt(n || 0);
		try {
			return format_currency(v);
		} catch (e) {
			return String(v);
		}
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

	function filtered_rows() {
		const cat = state.category || "";
		return ((state.catalog && state.catalog.templates) || []).filter((t) => {
			const ntype = normalize_type(t.quotation_type);
			if (cat && ntype !== cat && t.quotation_type !== cat) return false;
			if (state.active_only && !cint(t.is_active)) return false;
			if (state.tag) {
				const tags = (t.tags || []).map((x) => String(x).toLowerCase());
				if (tags.indexOf(String(state.tag).toLowerCase()) < 0) return false;
			}
			if (state.search) {
				const q = state.search.toLowerCase();
				const blob = [
					t.display_name,
					t.template_name,
					t.service_family,
					t.service_name,
					t.quotation_type,
				]
					.concat(t.tags || [])
					.join(" ")
					.toLowerCase();
				if (blob.indexOf(q) < 0) return false;
			}
			return true;
		});
	}

	function group_by_family(rows) {
		const map = {};
		const order = [];
		(rows || []).forEach((t) => {
			const fam = (t.service_family || t.service_name || "").trim() || __("General");
			if (!map[fam]) {
				map[fam] = [];
				order.push(fam);
			}
			map[fam].push(t);
		});
		order.sort((a, b) => {
			if (a === __("General")) return 1;
			if (b === __("General")) return -1;
			return a.localeCompare(b);
		});
		return order.map((fam) => ({
			family: fam,
			rows: map[fam].sort((a, b) =>
				String(a.display_name || a.template_name || a.name).localeCompare(
					String(b.display_name || b.template_name || b.name)
				)
			),
		}));
	}

	function shown_name(t) {
		return (t && (t.display_name || t.template_name || t.name)) || "";
	}

	function rename_template(row) {
		if (!row || !row.name) return;
		frappe.prompt(
			[
				{
					fieldname: "display_name",
					fieldtype: "Data",
					label: __("Display Name"),
					reqd: 1,
					default: shown_name(row),
				},
			],
			(values) => {
				frappe.call({
					method: "instacertify.quotation.events.rename_quotation_template_display_name",
					args: { template: row.name, display_name: values.display_name },
					freeze: true,
					callback() {
						frappe.show_alert({
							message: __("Display name updated (Template ID unchanged)"),
							indicator: "green",
						});
						load();
					},
				});
			},
			__("Rename Template"),
			__("Save")
		);
	}

	function open_template(name) {
		if (!name) return;
		frappe.set_route("Form", "IC Quotation Template", name);
	}

	function use_template(row) {
		if (!row) return;
		const qtype =
			row.quotation_type === "Service" ? "Consulting" : row.quotation_type || "Consulting";
		// Prefetch payload, then open a new Quotation — never call apply on unsaved new- names
		frappe.call({
			method: "instacertify.quotation.events.get_quotation_template_payload",
			args: { template: row.name },
			freeze: true,
			freeze_message: __("Loading quote format…"),
			callback(r) {
				instacertify._pending_quote_format = {
					skip: 0,
					quotation_type: qtype,
					payload: r.message || {},
				};
				frappe.model.with_doctype("Quotation", () => {
					frappe.new_doc("Quotation", {
						ic_quotation_type: qtype,
						ic_quotation_template: row.name,
						ic_service_family: row.service_family,
					});
				});
			},
			error() {
				frappe.msgprint({
					title: __("Could not load format"),
					indicator: "red",
					message: __(
						"Could not load this template. Try Edit, or open New Quotation from the list."
					),
				});
			},
		});
	}

	function preview_template(name, mode) {
		if (!name) return;
		frappe.call({
			method: "instacertify.quotation.events.ensure_template_preview_quotation",
			args: { template: name },
			freeze: true,
			freeze_message: mode === "pdf" ? __("Preparing PDF…") : __("Preparing print preview…"),
			callback(r) {
				const m = r.message || {};
				if (!m.quotation) {
					frappe.msgprint(__("Could not build preview quotation."));
					return;
				}
				const fmt = m.print_format || "Instacertify Quotation";
				if (mode === "pdf") {
					const url = frappe.urllib.get_full_url(
						"/api/method/instacertify.utils.pdf.download_quotation_pdf?" +
							$.param({ name: m.quotation, print_format: fmt })
					);
					window.open(url, "_blank");
				} else {
					const url = frappe.urllib.get_full_url(
						"/printview?" +
							$.param({
								doctype: "Quotation",
								name: m.quotation,
								format: fmt,
								no_letterhead: 0,
								_lang: frappe.boot.lang || "en",
							})
					);
					window.open(url, "_blank");
				}
			},
		});
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
			{ key: "", label: __("All"), count: total, slug: "all" },
		].concat(
			CATEGORIES.map((c) => ({
				key: c.key,
				label: c.label,
				count: counts[c.key] || 0,
				slug: c.slug,
			}))
		);

		$cats.html(
			chips
				.map((c) => {
					const active = (state.category || "") === (c.key || "");
					return `<button type="button" class="ic-quote-lib-tab cat-${c.slug}${active ? " active" : ""}"
						data-cat="${esc(c.key)}" role="tab" aria-selected="${active ? "true" : "false"}">
						<span class="ic-quote-lib-tab-label">${esc(c.label)}</span>
						<span class="ic-quote-lib-tab-count">${c.count}</span>
					</button>`;
				})
				.join("")
		);

		$cats.find(".ic-quote-lib-tab").on("click", function () {
			state.category = $(this).data("cat") || "";
			state.tag = "";
			render_cats();
			render_rail();
			render_tag_bar();
			render_templates();
		});
	}

	function render_rail() {
		const counts = (state.catalog && state.catalog.counts) || {};
		const total = Object.values(counts).reduce((a, b) => a + (b || 0), 0);
		const items = [
			{ key: "", label: __("All categories"), count: total, slug: "all" },
		].concat(
			CATEGORIES.map((c) => ({
				key: c.key,
				label: c.label,
				count: counts[c.key] || 0,
				slug: c.slug,
				hint: c.hint,
			}))
		);

		$rail.html(
			`<div class="ic-quote-lib-rail-title">${__("Categories")}</div>` +
				items
					.map((c) => {
						const active = (state.category || "") === (c.key || "");
						return `<button type="button" class="ic-quote-lib-rail-item cat-${c.slug}${
							active ? " active" : ""
						}" data-cat="${esc(c.key)}">
							<span class="ic-quote-lib-rail-swatch" aria-hidden="true"></span>
							<span class="ic-quote-lib-rail-label">${esc(c.label)}</span>
							<span class="ic-quote-lib-rail-count">${c.count}</span>
						</button>`;
					})
					.join("")
		);

		$rail.find(".ic-quote-lib-rail-item").on("click", function () {
			state.category = $(this).data("cat") || "";
			state.tag = "";
			render_cats();
			render_rail();
			render_tag_bar();
			render_templates();
			const $sec = $grid.find(`.ic-quote-lib-section[data-cat="${state.category}"]`);
			if ($sec.length) {
				$("html, body").animate({ scrollTop: $sec.offset().top - 80 }, 200);
			}
		});
	}

	function render_tag_bar() {
		const base = ((state.catalog && state.catalog.templates) || []).filter((t) => {
			if (state.category) {
				const ntype = normalize_type(t.quotation_type);
				if (ntype !== state.category && t.quotation_type !== state.category) return false;
			}
			return true;
		});
		const tags = collect_tags(base);
		if (!tags.length) {
			$tags.html("").hide();
			return;
		}
		$tags.show();
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
		$tags.html(`<span class="ic-quote-lib-tag-label">${__("Filter by tag")}</span>` + chips.join(""));
		$tags.find(".ic-quote-lib-tag").on("click", function () {
			state.tag = $(this).data("tag") || "";
			render_tag_bar();
			render_templates();
		});
	}

	function row_html(t) {
		const family = t.service_family || t.service_name || "";
		const active = cint(t.is_active);
		const lines = cint(t.cost_line_count);
		const passLines = cint(t.passthrough_line_count);
		const amount =
			lines > 0
				? `<span class="ic-quote-lib-row-amount">${esc(format_money(t.default_amount_total))}</span>
					<span class="ic-quote-lib-row-lines">${lines} ${__("lines")}${
						passLines ? ` · ${passLines} ${__("not revenue")}` : ""
				  }</span>`
				: `<span class="ic-quote-lib-row-amount muted">${__("No amounts")}</span>`;
		const tagHtml = (t.tags || [])
			.slice(0, 4)
			.map((tag) => `<span class="ic-quote-lib-card-tag">${esc(tag)}</span>`)
			.join("");

		return `<article class="ic-quote-lib-row cat-${cat_slug(t.quotation_type)}" data-name="${esc(
			t.name
		)}" tabindex="0" role="button" title="${__("Click to edit")}">
			<div class="ic-quote-lib-row-main">
				<div class="ic-quote-lib-row-name">${esc(shown_name(t))}</div>
				<div class="ic-quote-lib-row-meta">
					${family ? `<span>${esc(family)}</span>` : ""}
					${
						t.template_name && shown_name(t) !== t.template_name
							? `<span class="text-muted" title="${__("Template ID")}">${esc(t.template_name)}</span>`
							: ""
					}
					${active ? `<span class="ic-quote-lib-badge on">${__("Active")}</span>` : `<span class="ic-quote-lib-badge off">${__("Inactive")}</span>`}
					${t.uploaded_format ? `<span class="ic-quote-lib-file">${__("File")}</span>` : ""}
					${tagHtml}
				</div>
			</div>
			<div class="ic-quote-lib-row-pricing">${amount}</div>
			<div class="ic-quote-lib-row-actions">
				<button type="button" class="btn btn-primary btn-xs ic-qlib-open">${__("Edit")}</button>
				<button type="button" class="btn btn-default btn-xs ic-qlib-rename" title="${__("Rename display name")}">${__("Rename")}</button>
				<button type="button" class="btn btn-default btn-xs ic-qlib-use">${__("Use")}</button>
				<button type="button" class="btn btn-default btn-xs ic-qlib-print" title="${__("Print")}">${__("Print")}</button>
				<button type="button" class="btn btn-default btn-xs ic-qlib-pdf" title="${__("PDF")}">${__("PDF")}</button>
			</div>
		</article>`;
	}

	function bind_row_actions($scope, rows) {
		$scope.find(".ic-qlib-open").on("click", function (e) {
			e.stopPropagation();
			open_template($(this).closest(".ic-quote-lib-row").data("name"));
		});
		$scope.find(".ic-qlib-rename").on("click", function (e) {
			e.stopPropagation();
			const name = $(this).closest(".ic-quote-lib-row").data("name");
			rename_template(rows.find((r) => r.name === name));
		});
		$scope.find(".ic-qlib-use").on("click", function (e) {
			e.stopPropagation();
			const name = $(this).closest(".ic-quote-lib-row").data("name");
			use_template(rows.find((r) => r.name === name));
		});
		$scope.find(".ic-qlib-print").on("click", function (e) {
			e.stopPropagation();
			preview_template($(this).closest(".ic-quote-lib-row").data("name"), "print");
		});
		$scope.find(".ic-qlib-pdf").on("click", function (e) {
			e.stopPropagation();
			preview_template($(this).closest(".ic-quote-lib-row").data("name"), "pdf");
		});
		$scope.find(".ic-quote-lib-row").on("click", function (e) {
			if ($(e.target).closest("button, a, .ic-quote-lib-card-tag").length) return;
			open_template($(this).data("name"));
		});
		$scope.find(".ic-quote-lib-row").on("keydown", function (e) {
			if (e.key === "Enter" || e.key === " ") {
				e.preventDefault();
				open_template($(this).data("name"));
			}
		});
		$scope.find(".ic-quote-lib-card-tag").on("click", function (e) {
			e.stopPropagation();
			state.tag = $(this).text();
			render_tag_bar();
			render_templates();
		});
		$scope.find(".ic-qlib-toggle").on("click", function (e) {
			e.stopPropagation();
			const key = $(this).data("collapse");
			state.collapsed[key] = !state.collapsed[key];
			render_templates();
		});
	}

	function family_block_html(catKey, group) {
		const collapseKey = `${catKey}::${group.family}`;
		const collapsed = !!state.collapsed[collapseKey];
		const rowsHtml = group.rows.map(row_html).join("");
		return `<div class="ic-quote-lib-family${collapsed ? " is-collapsed" : ""}" data-family="${esc(
			group.family
		)}">
			<button type="button" class="ic-quote-lib-family-head ic-qlib-toggle" data-collapse="${esc(
				collapseKey
			)}">
				<span class="ic-quote-lib-family-chevron" aria-hidden="true"></span>
				<span class="ic-quote-lib-family-name">${esc(group.family)}</span>
				<span class="ic-quote-lib-family-count">${group.rows.length}</span>
			</button>
			<div class="ic-quote-lib-list">${rowsHtml}</div>
		</div>`;
	}

	function render_templates() {
		const cat = state.category || "";
		const meta = CATEGORIES.find((c) => c.key === cat);
		const rows = filtered_rows();

		let status = meta
			? __("{0} · {1} templates", [meta.label, rows.length])
			: __("All categories · {0} templates", [rows.length]);
		if (state.tag) status += ` · ${__("tag")}: ${state.tag}`;
		if (state.search) status += ` · “${state.search}”`;
		$status.text(status);

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

		const sections = cat
			? [{ key: cat, label: meta ? meta.label : cat, hint: meta ? meta.hint : "", rows }]
			: CATEGORIES.map((c) => ({
					key: c.key,
					label: c.label,
					hint: c.hint,
					rows: rows.filter((t) => normalize_type(t.quotation_type) === c.key),
			  })).filter((s) => s.rows.length);

		if (!cat) {
			const known = new Set(CATEGORIES.map((c) => c.key));
			const orphan = rows.filter((t) => !known.has(normalize_type(t.quotation_type)));
			if (orphan.length) {
				sections.push({
					key: "Other",
					label: __("Other"),
					hint: __("Uncategorized templates"),
					rows: orphan,
				});
			}
		}

		$grid.html(
			sections
				.map((sec) => {
					const slug = cat_slug(sec.key);
					const families = group_by_family(sec.rows);
					const body = families.map((g) => family_block_html(sec.key, g)).join("");
					return `<section class="ic-quote-lib-section cat-${slug}" data-cat="${esc(sec.key)}" id="ic-qlib-sec-${slug}">
						<header class="ic-quote-lib-section-head">
							<div class="ic-quote-lib-section-title-row">
								<span class="ic-quote-lib-section-swatch" aria-hidden="true"></span>
								<h2 class="ic-quote-lib-section-title">${esc(sec.label)}</h2>
								<span class="ic-quote-lib-section-count">${sec.rows.length}</span>
							</div>
							<p class="ic-quote-lib-section-hint">${esc(sec.hint || "")}</p>
						</header>
						<div class="ic-quote-lib-families">${body}</div>
					</section>`;
				})
				.join("")
		);

		bind_row_actions($grid, rows);
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
				render_rail();
				render_tag_bar();
				render_templates();
			},
		});
	}

	page.main.find("#ic-qlib-dl-xlsx").on("click", (e) => {
		e.preventDefault();
		download_template("xlsx");
	});
	page.main.find("#ic-qlib-dl-csv").on("click", (e) => {
		e.preventDefault();
		download_template("csv");
	});
	page.main.find("#ic-qlib-import").on("click", (e) => {
		e.preventDefault();
		open_import();
	});
	page.main.find("#ic-qlib-upload").on("click", (e) => {
		e.preventDefault();
		instacertify.open_quote_format_upload({
			quotation_type: state.category || "Consulting",
			on_done() {
				load();
			},
		});
	});
	page.main.find("#ic-qlib-list").on("click", (e) => {
		e.preventDefault();
		const filters = {};
		if (state.category) filters.quotation_type = state.category;
		frappe.set_route("List", "IC Quotation Template", filters);
	});
	page.main.find("#ic-qlib-new").on("click", () => open_new(state.category));
	page.main.find("#ic-qlib-active").on("change", function () {
		state.active_only = this.checked ? 1 : 0;
		render_templates();
	});
	const $manageBtn = page.main.find(".ic-qlib-manage-btn");
	const $manageMenu = page.main.find(".ic-qlib-manage-menu");
	$manageBtn.on("click", function (e) {
		e.stopPropagation();
		const open = $manageMenu.is(":visible");
		$manageMenu.toggle(!open);
		$manageBtn.attr("aria-expanded", open ? "false" : "true");
	});
	$(document).on("click.ic-qlib-manage", () => {
		$manageMenu.hide();
		$manageBtn.attr("aria-expanded", "false");
	});
	$manageMenu.on("click", (e) => e.stopPropagation());
	let timer = null;
	page.main.find("#ic-qlib-search").on("input", function () {
		state.search = ($(this).val() || "").trim();
		clearTimeout(timer);
		timer = setTimeout(render_templates, 200);
	});

	load();
};
