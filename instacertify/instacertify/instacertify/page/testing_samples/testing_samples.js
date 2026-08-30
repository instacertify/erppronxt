frappe.pages["testing-samples"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Testing & Samples"),
		single_column: true,
	});

	frappe.breadcrumbs.add({
		label: __("Testing & Samples"),
		route: "/app/testing-samples",
	});

	page.set_title(__("Testing & Samples"));
	page.main.addClass("ic-ts-page");

	const JOURNEY_STEPS = [
		"With Customer",
		"In Transit to Office",
		"At Instacertify Office",
		"In Transit to Lab",
		"At Laboratory",
		"At Instacertify Warehouse",
		"In Transit to Client",
		"Returned to Client",
	];

	const LOC_SHORT = {
		"With Customer": "Customer",
		"In Transit to Office": "→ Office",
		"At Instacertify Office": "Office",
		"In Transit to Lab": "→ Lab",
		"At Laboratory": "At Lab",
		"At Instacertify Warehouse": "Warehouse",
		"In Transit to Client": "→ Client",
		"Returned to Client": "With Client",
	};

	page.main.html(`
		<div class="ic-ts">
			<div class="ic-ts-head">
				<div>
					<div class="ic-ts-kicker">${__("Laboratory · Testing · Custody")}</div>
					<div class="ic-ts-title">${__("Testing & Samples")}</div>
					<div class="ic-ts-sub">${__(
						"Generate a Testing Request from the lab library, then manage TRs and sample journey in clean tables."
					)}</div>
				</div>
				<div class="ic-ts-tools">
					<button type="button" class="btn btn-default btn-sm" id="ic-ts-labs">${__("Laboratories")}</button>
				</div>
			</div>

			<nav class="ic-ts-tabs" role="tablist">
				<button type="button" class="ic-ts-tab is-active" data-tab="generate" role="tab" aria-selected="true">
					<span class="ic-ts-tab-num">1</span>
					<span>
						<span class="ic-ts-tab-label">${__("Generate Testing Request")}</span>
						<span class="ic-ts-tab-hint">${__("Test → Standard → Lab → Create")}</span>
					</span>
				</button>
				<button type="button" class="ic-ts-tab" data-tab="manage" role="tab" aria-selected="false">
					<span class="ic-ts-tab-num">2</span>
					<span>
						<span class="ic-ts-tab-label">${__("Manage TR & Sample Journey")}</span>
						<span class="ic-ts-tab-hint">${__("Tabular list · update sample location")}</span>
					</span>
				</button>
			</nav>

			<!-- —— Generate —— -->
			<section class="ic-ts-panel" id="ic-ts-panel-generate" role="tabpanel">
				<div class="ic-ts-gen-layout">
					<div class="ic-ts-card ic-ts-gen-main">
						<div class="ic-ts-card-head">
							<div>
								<div class="ic-ts-card-title">${__("Generate Testing Request")}</div>
								<div class="ic-ts-card-sub">${__(
									"Select customer and test — related standards fill the dropdown (plus Other). Pick a standard to see labs that offer it."
								)}</div>
							</div>
						</div>

						<ol class="ic-ts-steps" aria-label="${__("Progress")}">
							<li class="ic-ts-step is-on is-current" data-step="1"><b>1</b> ${__("Customer & Test")}</li>
							<li class="ic-ts-step" data-step="2"><b>2</b> ${__("Standard")}</li>
							<li class="ic-ts-step" data-step="3"><b>3</b> ${__("Laboratory")}</li>
							<li class="ic-ts-step" data-step="4"><b>4</b> ${__("Create")}</li>
						</ol>

						<div class="ic-ts-form-shell">
							<div class="ic-ts-form" id="ic-ts-form"></div>
						</div>

						<div class="ic-ts-section" id="ic-ts-standards-wrap" hidden>
							<div class="ic-ts-section-head">
								<div class="ic-ts-section-title">${__("Applicable standards")}</div>
								<div class="ic-ts-card-sub" style="margin:0">${__(
									"Multiple standards may exist across labs — select one, or choose Other above."
								)}</div>
							</div>
							<div class="ic-ts-table-wrap">
								<table class="ic-ts-table ic-ts-table-select" id="ic-ts-standards-table">
									<thead>
										<tr>
											<th style="width:36px"></th>
											<th>${__("Applicable Standard")}</th>
											<th>${__("Labs that have this standard")}</th>
											<th style="text-align:right;width:72px">${__("Labs")}</th>
											<th style="width:110px"></th>
										</tr>
									</thead>
									<tbody></tbody>
								</table>
							</div>
						</div>

						<div class="ic-ts-section" id="ic-ts-labs-wrap" hidden>
							<div class="ic-ts-section-head">
								<div class="ic-ts-section-title">${__("Suggested laboratories")}</div>
								<div class="ic-ts-card-sub" style="margin:0" id="ic-ts-labs-hint">${__(
									"Labs offering the selected test and standard."
								)}</div>
							</div>
							<div class="ic-ts-table-wrap">
								<table class="ic-ts-table ic-ts-table-select" id="ic-ts-labs-table">
									<thead>
										<tr>
											<th style="width:36px"></th>
											<th>${__("Laboratory")}</th>
											<th>${__("Standard")}</th>
											<th>${__("Phone")}</th>
											<th>${__("Address")}</th>
											<th>${__("Contact")}</th>
											<th>${__("Designation")}</th>
											<th style="text-align:right">${__("Buying")}</th>
											<th style="text-align:right">${__("Selling")}</th>
											<th style="width:110px"></th>
										</tr>
									</thead>
									<tbody></tbody>
								</table>
							</div>
						</div>
					</div>

					<aside class="ic-ts-card ic-ts-summary" id="ic-ts-summary">
						<div class="ic-ts-summary-badge">${__("Summary")}</div>
						<div class="ic-ts-card-title">${__("Ready to create")}</div>
						<div class="ic-ts-summary-body" id="ic-ts-summary-body">
							<div class="text-muted">${__("Select customer, test, standard and laboratory.")}</div>
						</div>
						<button type="button" class="btn btn-primary btn-block ic-ts-btn-create" id="ic-ts-generate" disabled>
							${__("Generate Testing Request + Samples")}
						</button>
						<button type="button" class="btn btn-default btn-block" id="ic-ts-goto-manage">
							${__("Open Manage TR & Journey")}
						</button>
					</aside>
				</div>
			</section>

			<!-- —— Manage TR + Sample Journey —— -->
			<section class="ic-ts-panel" id="ic-ts-panel-manage" role="tabpanel" hidden>
				<div class="ic-ts-card ic-ts-manage-card">
					<div class="ic-ts-manage-head">
						<div>
							<div class="ic-ts-card-title">${__("Manage Testing Requests & Sample Journey")}</div>
							<div class="ic-ts-card-sub" style="margin-bottom:0">${__(
								"Tabular view of every Testing Request. Expand a row to update sample locations in the journey table."
							)}</div>
						</div>
						<button type="button" class="btn btn-primary btn-sm" id="ic-ts-goto-generate">${__("+ Generate new")}</button>
					</div>

					<div class="ic-ts-filters">
						<div class="ic-ts-filter" id="ic-ts-filter-customer"></div>
						<div class="ic-ts-filter" id="ic-ts-filter-project"></div>
						<button type="button" class="btn btn-sm btn-default" id="ic-ts-clear-filters">${__("Clear")}</button>
						<button type="button" class="btn btn-sm btn-default" id="ic-ts-refresh">${__("Refresh")}</button>
					</div>

					<div class="ic-ts-legend">
						<span class="ic-ts-legend-label">${__("Journey")}:</span>
						${JOURNEY_STEPS.map(
							(s) =>
								`<span class="ic-ts-legend-item"><i class="ic-ts-jdot is-on"></i>${frappe.utils.escape_html(
									LOC_SHORT[s] || s
								)}</span>`
						).join("")}
					</div>

					<div id="ic-ts-board" class="ic-ts-board" aria-live="polite"></div>
				</div>
			</section>
		</div>
	`);

	const state = {
		customer: "",
		project: "",
		product: "",
		test_name: "",
		applicable_standard: "",
		laboratory: "",
		lab_scope_row: "",
		lab_offer: "",
		number_of_samples: 1,
		offers: [],
		standards: [],
		selected_offer: null,
		board_rows: [],
		filter_customer: "",
		filter_project: "",
		expanded: {},
		tab: "generate",
		focus_tr: "",
	};

	const form = new frappe.ui.FieldGroup({
		fields: [
			{
				fieldname: "customer",
				fieldtype: "Link",
				options: "Customer",
				label: __("Customer"),
				reqd: 1,
				change() {
					state.customer = form.get_value("customer") || "";
					update_summary();
				},
			},
			{
				fieldname: "project",
				fieldtype: "Link",
				options: "Project",
				label: __("Project"),
				get_query() {
					const c = form.get_value("customer");
					return c ? { filters: { customer: c } } : {};
				},
				change() {
					state.project = form.get_value("project") || "";
					update_summary();
				},
			},
			{ fieldtype: "Column Break" },
			{
				fieldname: "product",
				fieldtype: "Data",
				label: __("Product"),
				change() {
					state.product = form.get_value("product") || "";
					update_summary();
				},
			},
			{
				fieldname: "number_of_samples",
				fieldtype: "Int",
				label: __("Number of Samples"),
				default: 1,
				change() {
					state.number_of_samples = cint(form.get_value("number_of_samples")) || 1;
					update_summary();
				},
			},
			{ fieldtype: "Section Break", label: __("1 — Test & Applicable Standard (interrelated)") },
			{
				fieldname: "test_name",
				fieldtype: "Autocomplete",
				label: __("Test Name"),
				reqd: 1,
				description: __("From Active lab libraries — includes Other for custom tests"),
				change() {
					const v = form.get_value("test_name") || "";
					if (v === state.test_name) return;
					state.test_name = v;
					state.applicable_standard = "";
					clear_lab_selection();
					state._skip_std_change = true;
					form.set_value("applicable_standard", "");
					state._skip_std_change = false;
					load_standards_for_test();
					update_summary();
				},
			},
			{ fieldtype: "Column Break" },
			{
				fieldname: "applicable_standard",
				fieldtype: "Autocomplete",
				label: __("Applicable Standard"),
				description: __("Standards related to the selected Test Name — pick Other if not listed"),
				change() {
					if (state._skip_std_change) return;
					const v = (form.get_value("applicable_standard") || "").trim();
					if (v === state.applicable_standard) return;
					state.applicable_standard = v;
					clear_lab_selection();
					// Refresh related test names when standard drives the filter
					if (v && !is_other(v)) {
						refresh_test_options_for_standard(v);
					}
					render_standards_table(state.standards);
					load_labs();
					update_summary();
				},
			},
		],
		body: page.main.find("#ic-ts-form"),
	});
	form.make();

	function is_other(v) {
		return String(v || "").trim().toLowerCase() === "other";
	}

	function set_autocomplete_options(fieldname, values) {
		form.set_df_property(fieldname, "options", values.join("\n"));
		const ctrl = form.get_field(fieldname);
		if (ctrl && ctrl.set_data) ctrl.set_data(values);
		else if (ctrl && ctrl.awesomplete) ctrl.awesomplete.list = values;
	}

	const filter_customer = frappe.ui.form.make_control({
		parent: page.main.find("#ic-ts-filter-customer"),
		df: {
			fieldtype: "Link",
			options: "Customer",
			label: __("Filter customer"),
			change() {
				state.filter_customer = filter_customer.get_value() || "";
				refresh_manage();
			},
		},
		render_input: true,
	});
	const filter_project = frappe.ui.form.make_control({
		parent: page.main.find("#ic-ts-filter-project"),
		df: {
			fieldtype: "Link",
			options: "Project",
			label: __("Filter project"),
			change() {
				state.filter_project = filter_project.get_value() || "";
				refresh_manage();
			},
		},
		render_input: true,
	});

	function set_step(n) {
		page.main.find(".ic-ts-step").each(function () {
			const s = cint($(this).data("step"));
			$(this).toggleClass("is-on", s <= n);
			$(this).toggleClass("is-current", s === n);
		});
	}

	function clear_lab_selection() {
		state.laboratory = "";
		state.lab_scope_row = "";
		state.lab_offer = "";
		state.selected_offer = null;
		page.main.find("#ic-ts-generate").prop("disabled", true);
		page.main.find("#ic-ts-labs-table tbody tr").removeClass("is-selected");
		update_summary();
	}

	function custody_color(loc) {
		const map = {
			"With Customer": "#1976d2",
			"In Transit to Office": "#ef6c00",
			"At Instacertify Office": "#2e7d32",
			"In Transit to Lab": "#ef6c00",
			"At Laboratory": "#6a1b9a",
			"At Instacertify Warehouse": "#00838f",
			"In Transit to Client": "#ef6c00",
			"Returned to Client": "#1565c0",
			Discarded: "#c62828",
		};
		return map[loc] || "#546e7a";
	}

	function next_locations(loc) {
		const idx = JOURNEY_STEPS.indexOf(loc);
		if (idx < 0) return JOURNEY_STEPS.slice(0, 3);
		// Prefer next step + nearby
		const next = JOURNEY_STEPS.slice(Math.max(0, idx), Math.min(JOURNEY_STEPS.length, idx + 3));
		return next.length ? next : JOURNEY_STEPS.slice(-3);
	}

	function switch_tab(tab) {
		state.tab = tab;
		page.main.find(".ic-ts-tab").each(function () {
			const on = $(this).data("tab") === tab;
			$(this).toggleClass("is-active", on).attr("aria-selected", on ? "true" : "false");
		});
		page.main.find("#ic-ts-panel-generate").prop("hidden", tab !== "generate");
		page.main.find("#ic-ts-panel-manage").prop("hidden", tab !== "manage");
		if (tab === "manage") refresh_manage();
	}

	function update_summary() {
		const offer = state.selected_offer;
		const rows = [
			[__("Customer"), state.customer || "—"],
			[__("Project"), state.project || "—"],
			[__("Product"), state.product || "—"],
			[__("Samples"), String(state.number_of_samples || 1)],
			[__("Test"), state.test_name || "—"],
			[__("Standard"), state.applicable_standard || "—"],
			[__("Laboratory"), offer ? offer.laboratory_name || offer.laboratory : "—"],
		];
		if (offer) {
			rows.push([__("Phone"), offer.phone || "—"]);
			rows.push([
				__("Contact"),
				[offer.contact_person, offer.contact_designation].filter(Boolean).join(" · ") || "—",
			]);
			rows.push([
				__("Buying"),
				format_currency(offer.purchase_price || 0, offer.currency || "INR"),
			]);
		}
		const html = rows
			.map(
				([k, v]) =>
					`<div class="ic-ts-sum-row"><span>${frappe.utils.escape_html(k)}</span><b>${frappe.utils.escape_html(
						String(v)
					)}</b></div>`
			)
			.join("");
		page.main.find("#ic-ts-summary-body").html(html);
		page.main.find("#ic-ts-generate").prop("disabled", !(state.customer && state.selected_offer));
	}

	function load_library_options() {
		frappe.call({
			method: "instacertify.laboratory.api.get_test_name_options",
			callback(r) {
				const vals = (r.message || []).map((o) => o.value || o);
				set_autocomplete_options("test_name", vals);
			},
		});
		// Standards empty until a test is chosen (still allow typing Other later)
		set_autocomplete_options("applicable_standard", [__("Other")]);
	}

	function refresh_test_options_for_standard(standard) {
		frappe.call({
			method: "instacertify.laboratory.api.get_test_name_options",
			args: { applicable_standard: standard || "" },
			callback(r) {
				const vals = (r.message || []).map((o) => o.value || o);
				set_autocomplete_options("test_name", vals);
			},
		});
	}

	function load_standards_for_test() {
		const test_name = form.get_value("test_name");
		const $wrap = page.main.find("#ic-ts-standards-wrap");
		if (!test_name) {
			$wrap.prop("hidden", true);
			page.main.find("#ic-ts-labs-wrap").prop("hidden", true);
			set_autocomplete_options("applicable_standard", [__("Other")]);
			set_step(1);
			return;
		}
		set_step(2);
		frappe.call({
			method: "instacertify.laboratory.api.get_standards_for_test",
			args: { test_name },
			callback(r) {
				state.standards = r.message || [];
				const vals = state.standards.map((o) => o.value || o);
				set_autocomplete_options("applicable_standard", vals);
				render_standards_table(state.standards);
				const real = state.standards.filter((s) => !is_other(s.value || s));
				if (real.length === 1) {
					pick_standard(real[0].value || real[0]);
				} else if (is_other(test_name)) {
					// Custom test — load labs only after a standard (or Other) is picked
					page.main.find("#ic-ts-labs-wrap").prop("hidden", true);
				} else if (!real.length) {
					load_labs();
				}
			},
		});
	}

	function render_standards_table(standards) {
		const $wrap = page.main.find("#ic-ts-standards-wrap");
		const $tbody = page.main.find("#ic-ts-standards-table tbody");
		$wrap.prop("hidden", false);
		const rows = (standards || []).filter((s) => !is_other(s.value || s));
		if (!rows.length) {
			$tbody.html(
				`<tr><td colspan="5" class="text-muted ic-ts-empty-row">${__(
					"No library standards for this test — pick Other in Applicable Standard, or labs will match by test name alone."
				)}</td></tr>`
			);
			return;
		}
		$tbody.html(
			rows
				.map((s, idx) => {
					const label = s.value || s;
					const labs = s.lab_names || (s.labs || []).map((l) => l.laboratory_name || l.name).join(", ");
					const active = state.applicable_standard === label ? "is-selected" : "";
					return `<tr class="${active}" data-idx="${idx}">
						<td class="ic-ts-radio-cell">
							<span class="ic-ts-radio ${active ? "is-on" : ""}" aria-hidden="true"></span>
						</td>
						<td><b>${frappe.utils.escape_html(label)}</b></td>
						<td class="ic-ts-labs-cell">${frappe.utils.escape_html(labs || "—")}</td>
						<td style="text-align:right">${cint(s.lab_count) || (s.labs || []).length || "—"}</td>
						<td style="text-align:right">
							<button type="button" class="btn btn-xs ${
								active ? "btn-primary" : "btn-default"
							} ic-ts-pick-std" data-idx="${idx}">
								${active ? __("Selected") : __("Select")}
							</button>
						</td>
					</tr>`;
				})
				.join("")
		);
		$tbody.find(".ic-ts-pick-std").on("click", function () {
			const s = rows[cint($(this).data("idx"))];
			pick_standard(s.value || s);
		});
		$tbody.find("tr[data-idx]").on("click", function (e) {
			if ($(e.target).closest("button").length) return;
			const s = rows[cint($(this).data("idx"))];
			pick_standard(s.value || s);
		});
	}

	function pick_standard(label) {
		state.applicable_standard = label;
		state._skip_std_change = true;
		form.set_value("applicable_standard", label);
		state._skip_std_change = false;
		clear_lab_selection();
		render_standards_table(state.standards);
		load_labs();
		update_summary();
	}

	function load_labs() {
		const test_name = form.get_value("test_name") || "";
		const standard = state.applicable_standard || form.get_value("applicable_standard") || "";
		if (!test_name && !standard) {
			page.main.find("#ic-ts-labs-wrap").prop("hidden", true);
			return;
		}
		if (is_other(test_name) && is_other(standard)) {
			page.main.find("#ic-ts-labs-wrap").prop("hidden", true);
			frappe.show_alert({
				message: __("Both Test and Standard are Other — pick a library value or choose a lab from Laboratories."),
				indicator: "orange",
			});
			return;
		}
		set_step(3);
		const hint = is_other(standard)
			? __("Showing labs that offer this test (standard is Other / custom).")
			: __("Suggested labs that have standard: {0}", [standard || "—"]);
		page.main.find("#ic-ts-labs-hint").text(hint);
		frappe.call({
			method: "instacertify.laboratory.api.get_labs_for_standard",
			args: { applicable_standard: standard || "", test_name: test_name || "" },
			callback(r) {
				state.offers = r.message || [];
				render_labs_table(state.offers);
			},
		});
	}

	function render_labs_table(offers) {
		const $wrap = page.main.find("#ic-ts-labs-wrap");
		const $tbody = page.main.find("#ic-ts-labs-table tbody");
		$wrap.prop("hidden", false);
		if (!offers.length) {
			$tbody.html(
				`<tr><td colspan="10" class="text-muted ic-ts-empty-row">${__(
					"No Active labs for this test/standard. Add scope & pricing on Laboratories, or pick Other and enter details manually later."
				)}</td></tr>`
			);
			return;
		}
		$tbody.html(
			offers
				.map((o, idx) => {
					const buy = format_currency(o.purchase_price || 0, o.currency || "INR");
					const sell = format_currency(o.selling_price || 0, o.currency || "INR");
					const selected =
						state.selected_offer && state.selected_offer.scope_row === o.scope_row
							? "is-selected"
							: "";
					return `<tr class="${selected}" data-idx="${idx}">
						<td class="ic-ts-radio-cell">
							<span class="ic-ts-radio ${selected ? "is-on" : ""}" aria-hidden="true"></span>
						</td>
						<td>
							<b>${frappe.utils.escape_html(o.laboratory_name || "")}</b>
							<div class="ic-ts-cell-sub">${frappe.utils.escape_html(o.test_name || "")}</div>
						</td>
						<td>${frappe.utils.escape_html(o.applicable_standard || "—")}</td>
						<td>${frappe.utils.escape_html(o.phone || "—")}</td>
						<td class="ic-ts-addr-cell">${frappe.utils.escape_html(o.address || o.location || "—")}</td>
						<td>${frappe.utils.escape_html(o.contact_person || "—")}</td>
						<td>${frappe.utils.escape_html(o.contact_designation || "—")}</td>
						<td class="ic-ts-money ic-ts-money-buy">${frappe.utils.escape_html(buy)}</td>
						<td class="ic-ts-money">${frappe.utils.escape_html(sell)}</td>
						<td style="text-align:right">
							<button type="button" class="btn btn-xs ${
								selected ? "btn-primary" : "btn-default"
							} ic-ts-pick-lab" data-idx="${idx}">
								${selected ? __("Selected") : __("Select")}
							</button>
						</td>
					</tr>`;
				})
				.join("")
		);
		$tbody.find(".ic-ts-pick-lab").on("click", function () {
			select_lab(offers[cint($(this).data("idx"))]);
		});
	}

	function select_lab(offer) {
		if (!offer) return;
		state.selected_offer = offer;
		state.laboratory = offer.laboratory;
		state.lab_scope_row = offer.scope_row;
		state.lab_offer = offer.value;
		if (offer.test_name) {
			state.test_name = offer.test_name;
			form.set_value("test_name", offer.test_name);
		}
		if (offer.applicable_standard) {
			state.applicable_standard = offer.applicable_standard;
			form.set_value("applicable_standard", offer.applicable_standard);
		}
		render_labs_table(state.offers);
		set_step(4);
		update_summary();
		frappe.show_alert({
			message: __("Lab selected — review summary and generate"),
			indicator: "green",
		});
	}

	function generate() {
		const customer = form.get_value("customer");
		if (!customer) {
			frappe.msgprint(__("Select a Customer first"));
			return;
		}
		if (!state.selected_offer) {
			frappe.msgprint(__("Select a laboratory from the list before generating."));
			return;
		}
		const offer = state.selected_offer;
		frappe.call({
			method: "instacertify.testing.events.create_testing_and_samples",
			args: {
				customer,
				project: form.get_value("project") || "",
				product: form.get_value("product") || "",
				test_name: form.get_value("test_name") || offer.test_name || "",
				applicable_standard: state.applicable_standard || offer.applicable_standard || "",
				laboratory: offer.laboratory || "",
				lab_scope_row: offer.scope_row || "",
				lab_offer: offer.value || "",
				number_of_samples: cint(form.get_value("number_of_samples")) || 1,
			},
			freeze: true,
			freeze_message: __("Generating Testing Request and samples…"),
			callback(r) {
				const m = r.message || {};
				state.focus_tr = m.testing_request || "";
				state.expanded[m.testing_request] = true;
				frappe.show_alert({
					message: __("Created {0} — manage sample journey below", [m.testing_request]),
					indicator: "green",
				});
				if (customer) {
					filter_customer.set_value(customer);
					state.filter_customer = customer;
				}
				switch_tab("manage");
			},
		});
	}

	function set_location(sample, location) {
		frappe.call({
			method: "instacertify.testing.events.set_sample_location",
			args: { sample, location },
			freeze: true,
			callback() {
				frappe.show_alert({
					message: __("Sample → {0}", [location]),
					indicator: "green",
				});
				refresh_manage();
			},
		});
	}

	function journey_mini(loc) {
		const idx = JOURNEY_STEPS.indexOf(loc);
		return `<div class="ic-ts-track-mini" title="${frappe.utils.escape_html(loc || "")}">
			${JOURNEY_STEPS.map((step, i) => {
				const on = idx >= 0 && i <= idx;
				const cur = i === idx;
				return `<span class="ic-ts-track-mini-dot ${on ? "is-on" : ""} ${cur ? "is-current" : ""}" title="${frappe.utils.escape_html(
					step
				)}"></span>`;
			}).join("")}
		</div>`;
	}

	function location_select(sample, loc) {
		const opts = JOURNEY_STEPS.map(
			(l) =>
				`<option value="${frappe.utils.escape_html(l)}" ${l === loc ? "selected" : ""}>${frappe.utils.escape_html(
					LOC_SHORT[l] || l
				)}</option>`
		).join("");
		return `<select class="form-control input-sm ic-ts-loc-select" data-sample="${frappe.utils.escape_html(
			sample.name
		)}" data-current="${frappe.utils.escape_html(loc || "")}">
			${opts}
			<option value="Discarded" ${loc === "Discarded" ? "selected" : ""}>${__("Discarded")}</option>
		</select>`;
	}

	function render_manage(rows) {
		const $board = page.main.find("#ic-ts-board");
		if (!rows.length) {
			$board.html(`
				<div class="ic-ts-empty">
					<div class="ic-ts-empty-title">${__("No Testing Requests yet")}</div>
					<div>${__("Use Generate Testing Request to create the first one from the lab library.")}</div>
					<button type="button" class="btn btn-primary btn-sm" style="margin-top:12px" id="ic-ts-empty-gen">${__(
						"Generate Testing Request"
					)}</button>
				</div>
			`);
			$board.find("#ic-ts-empty-gen").on("click", () => switch_tab("generate"));
			return;
		}

		const body = rows
			.map((tr) => {
				const open = !!state.expanded[tr.name];
				const samples = tr.samples || [];
				const buy = tr.library_buying_price ? format_currency(tr.library_buying_price) : "—";
				const focus = state.focus_tr === tr.name ? "ic-ts-flash" : "";

				const sample_table = !samples.length
					? `<div class="ic-ts-nested-empty text-muted">${__("No samples linked yet.")}</div>`
					: `<div class="ic-ts-table-wrap ic-ts-nested-wrap">
						<table class="ic-ts-table ic-ts-samples-table">
							<thead>
								<tr>
									<th>${__("Tracking #")}</th>
									<th>${__("Description")}</th>
									<th>${__("Location")}</th>
									<th>${__("Journey")}</th>
									<th style="min-width:140px">${__("Move to")}</th>
									<th style="width:72px"></th>
								</tr>
							</thead>
							<tbody>
								${samples
									.map((s) => {
										const loc = s.sample_location || s.status || "With Customer";
										const color = custody_color(loc);
										return `<tr>
											<td>
												<a href="/app/ic-sample-tracking/${encodeURIComponent(s.name)}"><b>${frappe.utils.escape_html(
													s.tracking_number || s.name
												)}</b></a>
											</td>
											<td class="ic-ts-desc-cell">${frappe.utils.escape_html(s.sample_description || "—")}</td>
											<td><span class="ic-ts-pill" style="background:${color}22;color:${color}">${frappe.utils.escape_html(
												loc
											)}</span></td>
											<td>${journey_mini(loc)}</td>
											<td>${location_select(s, loc)}</td>
											<td>
												<button type="button" class="btn btn-xs btn-default ic-ts-loc-apply" data-sample="${frappe.utils.escape_html(
													s.name
												)}">${__("Update")}</button>
											</td>
										</tr>`;
									})
									.join("")}
							</tbody>
						</table>
					</div>`;

				return `
					<tbody class="ic-ts-tr-group ${focus}" data-tr="${frappe.utils.escape_html(tr.name)}">
						<tr class="ic-ts-tr-row ${open ? "is-open" : ""}">
							<td class="ic-ts-expand-cell">
								<button type="button" class="ic-ts-expand-btn" data-tr="${frappe.utils.escape_html(
									tr.name
								)}" aria-expanded="${open ? "true" : "false"}" title="${__(
									"Show samples"
								)}">${open ? "▾" : "▸"}</button>
							</td>
							<td>
								<a class="ic-ts-tr-id" href="/app/ic-testing-request/${encodeURIComponent(tr.name)}">${frappe.utils.escape_html(
									tr.name
								)}</a>
								<div class="ic-ts-cell-sub">${frappe.utils.escape_html(tr.title || tr.product || "")}</div>
							</td>
							<td><span class="ic-ts-status">${frappe.utils.escape_html(tr.status || "—")}</span></td>
							<td>
								${
									tr.customer
										? `<a href="/app/customer/${encodeURIComponent(tr.customer)}">${frappe.utils.escape_html(
												tr.customer_name || tr.customer
										  )}</a>`
										: "—"
								}
								${
									tr.project
										? `<div class="ic-ts-cell-sub"><a href="/app/project/${encodeURIComponent(
												tr.project
										  )}">${frappe.utils.escape_html(tr.project)}</a></div>`
										: ""
								}
							</td>
							<td>
								<b>${frappe.utils.escape_html(tr.test_name || "—")}</b>
								<div class="ic-ts-cell-sub">${frappe.utils.escape_html(tr.applicable_standard || "—")}</div>
							</td>
							<td>${frappe.utils.escape_html(tr.laboratory_name || tr.laboratory || "—")}</td>
							<td class="ic-ts-money ic-ts-money-buy">${frappe.utils.escape_html(buy)}</td>
							<td style="text-align:center"><span class="ic-ts-count">${samples.length}</span></td>
							<td>
								<a class="btn btn-xs btn-default" href="/app/ic-testing-request/${encodeURIComponent(
									tr.name
								)}">${__("Open")}</a>
							</td>
						</tr>
						<tr class="ic-ts-tr-detail" ${open ? "" : "hidden"}>
							<td colspan="9">
								<div class="ic-ts-detail-inner">
									<div class="ic-ts-samples-title">${__("Samples on this Testing Request")} · ${samples.length}</div>
									${sample_table}
								</div>
							</td>
						</tr>
					</tbody>`;
			})
			.join("");

		$board.html(`
			<div class="ic-ts-table-wrap ic-ts-manage-table-wrap">
				<table class="ic-ts-table ic-ts-manage-table">
					<thead>
						<tr>
							<th style="width:40px"></th>
							<th>${__("Testing Request")}</th>
							<th>${__("Status")}</th>
							<th>${__("Customer / Project")}</th>
							<th>${__("Test / Standard")}</th>
							<th>${__("Laboratory")}</th>
							<th style="text-align:right">${__("Buying")}</th>
							<th style="text-align:center">${__("Samples")}</th>
							<th style="width:80px"></th>
						</tr>
					</thead>
					${body}
				</table>
			</div>
		`);

		$board.find(".ic-ts-expand-btn").on("click", function () {
			const name = $(this).data("tr");
			state.expanded[name] = !($(this).attr("aria-expanded") === "true");
			render_manage(state.board_rows);
		});
		$board.find(".ic-ts-tr-row").on("click", function (e) {
			if ($(e.target).closest("a,button,select").length) return;
			const name = $(this).closest(".ic-ts-tr-group").data("tr");
			state.expanded[name] = !state.expanded[name];
			render_manage(state.board_rows);
		});
		$board.find(".ic-ts-loc-apply").on("click", function (e) {
			e.stopPropagation();
			const sample = $(this).data("sample");
			const $sel = $board.find(`.ic-ts-loc-select[data-sample="${CSS.escape(sample)}"]`);
			const loc = $sel.val();
			const current = $sel.data("current");
			if (!loc || loc === current) {
				frappe.show_alert({ message: __("Location unchanged"), indicator: "blue" });
				return;
			}
			set_location(sample, loc);
		});
		$board.find(".ic-ts-loc-select").on("change", function () {
			// optional auto-apply on change for faster workflow
			const sample = $(this).data("sample");
			const loc = $(this).val();
			const current = $(this).data("current");
			if (loc && loc !== current) {
				set_location(sample, loc);
			}
		});

		if (state.focus_tr) {
			const $card = $board.find(`.ic-ts-tr-group[data-tr="${CSS.escape(state.focus_tr)}"]`);
			if ($card.length) {
				setTimeout(() => {
					$("html, body").animate({ scrollTop: $card.offset().top - 72 }, 250);
				}, 50);
			}
			setTimeout(() => {
				state.focus_tr = "";
			}, 1600);
		}
	}

	function refresh_manage() {
		frappe.call({
			method: "instacertify.testing.events.list_testing_samples_board",
			args: {
				customer: state.filter_customer || "",
				project: state.filter_project || "",
				limit: 80,
			},
			callback(r) {
				state.board_rows = r.message || [];
				// default expand all first time
				state.board_rows.forEach((tr) => {
					if (state.expanded[tr.name] === undefined) {
						// Keep table compact; expand when focused after generate
						state.expanded[tr.name] = state.focus_tr === tr.name;
					}
				});
				render_manage(state.board_rows);
			},
		});
	}

	page.main.find(".ic-ts-tab").on("click", function () {
		switch_tab($(this).data("tab"));
	});
	page.main.find("#ic-ts-generate").on("click", generate);
	page.main.find("#ic-ts-refresh").on("click", refresh_manage);
	page.main.find("#ic-ts-labs").on("click", () => frappe.set_route("List", "IC Laboratory"));
	page.main.find("#ic-ts-goto-generate").on("click", () => switch_tab("generate"));
	page.main.find("#ic-ts-goto-manage").on("click", () => switch_tab("manage"));
	page.main.find("#ic-ts-clear-filters").on("click", () => {
		filter_customer.set_value("");
		filter_project.set_value("");
		state.filter_customer = "";
		state.filter_project = "";
		refresh_manage();
	});

	if (frappe.route_options) {
		if (frappe.route_options.customer) {
			form.set_value("customer", frappe.route_options.customer);
			filter_customer.set_value(frappe.route_options.customer);
			state.filter_customer = frappe.route_options.customer;
			state.customer = frappe.route_options.customer;
		}
		if (frappe.route_options.project) {
			form.set_value("project", frappe.route_options.project);
			filter_project.set_value(frappe.route_options.project);
			state.filter_project = frappe.route_options.project;
			state.project = frappe.route_options.project;
		}
		if (frappe.route_options.tab === "manage" || frappe.route_options.tab === "journey") {
			switch_tab("manage");
		}
		frappe.route_options = null;
	}

	set_step(1);
	update_summary();
	load_library_options();
	refresh_manage();
};

frappe.pages["testing-samples"].on_page_show = function () {};
