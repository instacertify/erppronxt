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
		"At Laboratory": "Lab",
		"At Instacertify Warehouse": "Warehouse",
		"In Transit to Client": "→ Client",
		"Returned to Client": "Client",
		Discarded: "Discarded",
	};

	page.main.html(`
		<div class="ic-ts">
			<div class="ic-ts-head">
				<div>
					<div class="ic-ts-kicker">${__("Laboratory · Testing · Custody")}</div>
					<div class="ic-ts-title">${__("Testing & Samples")}</div>
					<div class="ic-ts-sub">${__(
						"Pick a test → suggested standards → labs with phone & address → generate a Testing Request. Manage every TR and sample journey in the second menu."
					)}</div>
				</div>
				<div class="ic-ts-tools">
					<button type="button" class="btn btn-default btn-sm" id="ic-ts-labs">${__("Laboratories")}</button>
				</div>
			</div>

			<nav class="ic-ts-tabs" role="tablist" aria-label="${__("Testing & Samples menus")}">
				<button type="button" class="ic-ts-tab is-active" data-tab="generate" role="tab" aria-selected="true">
					${__("1. Generate Testing Request")}
				</button>
				<button type="button" class="ic-ts-tab" data-tab="journey" role="tab" aria-selected="false">
					${__("2. Manage TR & Sample Journey")}
				</button>
			</nav>

			<section class="ic-ts-panel" id="ic-ts-panel-generate" role="tabpanel">
				<div class="ic-ts-card">
					<div class="ic-ts-card-title">${__("Generate from Laboratory Library")}</div>
					<div class="ic-ts-card-sub">${__(
						"Select Test Name first. Applicable standards are suggested next. Then choose a lab (phone & address shown) and generate the Testing Request with samples."
					)}</div>

					<div class="ic-ts-steps" aria-hidden="true">
						<span class="ic-ts-step is-on" data-step="1">${__("Test")}</span>
						<span class="ic-ts-step" data-step="2">${__("Standard")}</span>
						<span class="ic-ts-step" data-step="3">${__("Lab")}</span>
						<span class="ic-ts-step" data-step="4">${__("Generate")}</span>
					</div>

					<div class="ic-ts-form" id="ic-ts-form"></div>

					<div class="ic-ts-section" id="ic-ts-standards-wrap" hidden>
						<div class="ic-ts-section-title">${__("Suggested applicable standards")}</div>
						<div class="ic-ts-chips" id="ic-ts-standards"></div>
					</div>

					<div class="ic-ts-section" id="ic-ts-labs-wrap" hidden>
						<div class="ic-ts-section-title">${__("Labs offering this standard")}</div>
						<div class="ic-ts-card-sub" style="margin-top:0">${__(
							"Select one laboratory. Phone and address are shown for coordination."
						)}</div>
						<div id="ic-ts-lab-list" class="ic-ts-lab-list"></div>
					</div>

					<div class="ic-ts-selected" id="ic-ts-selected" hidden></div>

					<div class="ic-ts-actions">
						<button type="button" class="btn btn-primary btn-lg" id="ic-ts-generate" disabled>
							${__("Generate Testing Request + Samples")}
						</button>
					</div>
				</div>
			</section>

			<section class="ic-ts-panel" id="ic-ts-panel-journey" role="tabpanel" hidden>
				<div class="ic-ts-card ic-ts-board-wrap">
					<div class="ic-ts-card-title">${__("All Testing Requests — sample journey")}</div>
					<div class="ic-ts-card-sub">${__(
						"Every generated TR appears here. Update where each sample is (customer → office → lab → warehouse → client) for the product journey."
					)}</div>
					<div class="ic-ts-filters">
						<div class="ic-ts-filter" id="ic-ts-filter-customer"></div>
						<div class="ic-ts-filter" id="ic-ts-filter-project"></div>
						<button type="button" class="btn btn-xs btn-default" id="ic-ts-clear-filters">${__("Clear")}</button>
						<button type="button" class="btn btn-xs btn-default" id="ic-ts-refresh">${__("Refresh")}</button>
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
		filter_customer: "",
		filter_project: "",
		tab: "generate",
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
					state.customer = form.get_value("customer");
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
					state.project = form.get_value("project");
				},
			},
			{ fieldtype: "Column Break" },
			{
				fieldname: "product",
				fieldtype: "Data",
				label: __("Product"),
				change() {
					state.product = form.get_value("product");
				},
			},
			{
				fieldname: "number_of_samples",
				fieldtype: "Int",
				label: __("Number of Samples"),
				default: 1,
				change() {
					state.number_of_samples = cint(form.get_value("number_of_samples")) || 1;
				},
			},
			{ fieldtype: "Section Break", label: __("1 — Select Test Name") },
			{
				fieldname: "test_name",
				fieldtype: "Autocomplete",
				label: __("Test Name"),
				reqd: 1,
				description: __("From Active laboratory libraries"),
				change() {
					const v = form.get_value("test_name") || "";
					if (v === state.test_name) return;
					state.test_name = v;
					state.applicable_standard = "";
					state.selected_offer = null;
					clear_lab_selection();
					form.set_value("applicable_standard", "");
					load_standards_for_test();
				},
			},
			{ fieldtype: "Column Break" },
			{
				fieldname: "applicable_standard",
				fieldtype: "Autocomplete",
				label: __("Applicable Standard"),
				description: __("Suggested after Test Name — or type to filter"),
				change() {
					const v = form.get_value("applicable_standard") || "";
					if (v === state.applicable_standard) return;
					state.applicable_standard = v;
					state.selected_offer = null;
					clear_lab_selection();
					if (v) {
						load_labs();
					} else {
						page.main.find("#ic-ts-labs-wrap").prop("hidden", true).find("#ic-ts-lab-list").empty();
						set_step(state.test_name ? 2 : 1);
					}
				},
			},
		],
		body: page.main.find("#ic-ts-form"),
	});
	form.make();

	const filter_customer = frappe.ui.form.make_control({
		parent: page.main.find("#ic-ts-filter-customer"),
		df: {
			fieldtype: "Link",
			options: "Customer",
			label: __("Filter customer"),
			change() {
				state.filter_customer = filter_customer.get_value();
				load_board();
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
				state.filter_project = filter_project.get_value();
				load_board();
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
		page.main.find("#ic-ts-selected").prop("hidden", true).empty();
		page.main.find("#ic-ts-generate").prop("disabled", true);
		page.main.find(".ic-ts-lab-card").removeClass("is-selected");
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

	function switch_tab(tab) {
		state.tab = tab;
		page.main.find(".ic-ts-tab").each(function () {
			const on = $(this).data("tab") === tab;
			$(this).toggleClass("is-active", on).attr("aria-selected", on ? "true" : "false");
		});
		page.main.find("#ic-ts-panel-generate").prop("hidden", tab !== "generate");
		page.main.find("#ic-ts-panel-journey").prop("hidden", tab !== "journey");
		if (tab === "journey") load_board();
	}

	function load_library_options() {
		frappe.call({
			method: "instacertify.laboratory.api.get_test_name_options",
			callback(r) {
				const vals = (r.message || []).map((o) => o.value || o);
				form.set_df_property("test_name", "options", vals.join("\n"));
				const ctrl = form.get_field("test_name");
				if (ctrl && ctrl.set_data) ctrl.set_data(vals);
			},
		});
	}

	function load_standards_for_test() {
		const test_name = form.get_value("test_name");
		const $wrap = page.main.find("#ic-ts-standards-wrap");
		const $labs = page.main.find("#ic-ts-labs-wrap");
		if (!test_name) {
			$wrap.prop("hidden", true).find("#ic-ts-standards").empty();
			$labs.prop("hidden", true);
			set_step(1);
			return;
		}
		set_step(2);
		frappe.call({
			method: "instacertify.laboratory.api.get_standards_for_test",
			args: { test_name },
			callback(r) {
				state.standards = r.message || [];
				render_standards(state.standards);
				// Also refresh standard autocomplete options
				const vals = state.standards.map((o) => o.value || o);
				form.set_df_property("applicable_standard", "options", vals.join("\n"));
				const ctrl = form.get_field("applicable_standard");
				if (ctrl && ctrl.set_data) ctrl.set_data(vals);

				if (state.standards.length === 1) {
					const only = state.standards[0].value || state.standards[0];
					form.set_value("applicable_standard", only);
					state.applicable_standard = only;
					load_labs();
				} else if (!state.standards.length) {
					// No standard mapped — still try labs by test alone
					load_labs();
				}
			},
		});
	}

	function render_standards(standards) {
		const $box = page.main.find("#ic-ts-standards");
		const $wrap = page.main.find("#ic-ts-standards-wrap");
		if (!standards.length) {
			$wrap.prop("hidden", false);
			$box.html(
				`<div class="text-muted">${__(
					"No applicable standard listed for this test yet — labs will be shown by test name."
				)}</div>`
			);
			return;
		}
		$wrap.prop("hidden", false);
		$box.html(
			standards
				.map((s, idx) => {
					const label = s.value || s;
					const count = s.lab_count ? ` · ${s.lab_count} ${__("lab scope(s)")}` : "";
					const active = state.applicable_standard === label ? "is-active" : "";
					return `<button type="button" class="ic-ts-chip ${active}" data-idx="${idx}">
						${frappe.utils.escape_html(label)}<span class="ic-ts-chip-meta">${frappe.utils.escape_html(count)}</span>
					</button>`;
				})
				.join("")
		);
		$box.find(".ic-ts-chip").on("click", function () {
			const s = standards[cint($(this).data("idx"))];
			const label = s.value || s;
			form.set_value("applicable_standard", label);
			state.applicable_standard = label;
			$box.find(".ic-ts-chip").removeClass("is-active");
			$(this).addClass("is-active");
			clear_lab_selection();
			load_labs();
		});
	}

	function load_labs() {
		const test_name = form.get_value("test_name") || "";
		const standard = form.get_value("applicable_standard") || state.applicable_standard || "";
		if (!test_name && !standard) {
			page.main.find("#ic-ts-labs-wrap").prop("hidden", true);
			return;
		}
		set_step(3);
		frappe.call({
			method: "instacertify.laboratory.api.get_labs_for_standard",
			args: {
				applicable_standard: standard || "",
				test_name: test_name || "",
			},
			callback(r) {
				state.offers = r.message || [];
				render_labs(state.offers);
			},
		});
	}

	function render_labs(offers) {
		const $wrap = page.main.find("#ic-ts-labs-wrap");
		const $list = page.main.find("#ic-ts-lab-list");
		$wrap.prop("hidden", false);
		if (!offers.length) {
			$list.html(
				`<div class="ic-ts-empty">${__(
					"No Active labs list this test/standard. Add scope & prices on Laboratories first."
				)}</div>`
			);
			return;
		}
		$list.html(
			offers
				.map((o, idx) => {
					const buy = format_currency(o.purchase_price || 0, o.currency || "INR");
					const sell = format_currency(o.selling_price || 0, o.currency || "INR");
					const phone = o.phone || "—";
					const address = o.address || o.location || "—";
					const contact = o.contact_person
						? `<div class="ic-ts-lab-line"><span class="text-muted">${__("Contact")}</span> ${frappe.utils.escape_html(
								o.contact_person
						  )}</div>`
						: "";
					const selected =
						state.selected_offer && state.selected_offer.scope_row === o.scope_row
							? "is-selected"
							: "";
					return `<article class="ic-ts-lab-card ${selected}" data-idx="${idx}" role="button" tabindex="0">
						<div class="ic-ts-lab-top">
							<div>
								<div class="ic-ts-lab-name">${frappe.utils.escape_html(o.laboratory_name || "")}</div>
								<div class="text-muted" style="font-size:12px">${frappe.utils.escape_html(o.test_name || "")}
									${o.applicable_standard ? ` · ${frappe.utils.escape_html(o.applicable_standard)}` : ""}
								</div>
							</div>
							<div class="ic-ts-lab-prices">
								<div><span class="text-muted">${__("Buy")}</span> <b>${frappe.utils.escape_html(buy)}</b></div>
								<div><span class="text-muted">${__("Sell")}</span> <b>${frappe.utils.escape_html(sell)}</b></div>
							</div>
						</div>
						<div class="ic-ts-lab-line"><span class="text-muted">${__("Phone")}</span> ${frappe.utils.escape_html(
							phone
						)}</div>
						<div class="ic-ts-lab-line"><span class="text-muted">${__("Address")}</span> ${frappe.utils.escape_html(
							address
						)}</div>
						${contact}
						<div class="ic-ts-lab-pick">${__("Select this lab")}</div>
					</article>`;
				})
				.join("")
		);
		$list.find(".ic-ts-lab-card").on("click keypress", function (e) {
			if (e.type === "keypress" && e.which !== 13 && e.which !== 32) return;
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
		page.main.find(".ic-ts-lab-card").removeClass("is-selected");
		page.main
			.find(`.ic-ts-lab-card[data-idx]`)
			.filter(function () {
				return state.offers[cint($(this).data("idx"))]?.scope_row === offer.scope_row;
			})
			.addClass("is-selected");

		const buy = format_currency(offer.purchase_price || 0, offer.currency || "INR");
		page.main.find("#ic-ts-selected").prop("hidden", false).html(`
			<div class="ic-ts-selected-inner">
				<div class="ic-ts-selected-label">${__("Selected laboratory")}</div>
				<div class="ic-ts-selected-name">${frappe.utils.escape_html(offer.laboratory_name || "")}</div>
				<div class="text-muted" style="font-size:12px;margin-top:4px">
					${frappe.utils.escape_html(offer.phone || "—")}
					· ${frappe.utils.escape_html(offer.address || offer.location || "—")}
					· ${__("Buying")} ${frappe.utils.escape_html(buy)}
				</div>
			</div>
		`);
		page.main.find("#ic-ts-generate").prop("disabled", false);
		set_step(4);
		frappe.show_alert({
			message: __("Selected {0}", [offer.laboratory_name || offer.laboratory]),
			indicator: "green",
		});
	}

	function generate() {
		const customer = form.get_value("customer");
		if (!customer) {
			frappe.msgprint(__("Select a Customer first"));
			return;
		}
		if (!state.selected_offer && !form.get_value("test_name")) {
			frappe.msgprint(__("Select a Test Name, then an Applicable Standard and a Laboratory."));
			return;
		}
		if (!state.selected_offer) {
			frappe.msgprint(__("Select a laboratory from the list (phone & address) before generating."));
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
				applicable_standard:
					form.get_value("applicable_standard") || offer.applicable_standard || "",
				laboratory: offer.laboratory || "",
				lab_scope_row: offer.scope_row || "",
				lab_offer: offer.value || "",
				number_of_samples: cint(form.get_value("number_of_samples")) || 1,
			},
			freeze: true,
			freeze_message: __("Generating Testing Request and samples…"),
			callback(r) {
				const m = r.message || {};
				frappe.show_alert({
					message: __("Created {0} with {1} sample(s)", [
						m.testing_request,
						(m.samples || []).length,
					]),
					indicator: "green",
				});
				frappe.msgprint({
					title: __("Testing Request generated"),
					indicator: "green",
					message: `
						<p>${__("Request")}: <a href="/app/ic-testing-request/${encodeURIComponent(
							m.testing_request
						)}">${frappe.utils.escape_html(m.testing_request)}</a></p>
						<p>${__("Lab")}: ${frappe.utils.escape_html(m.laboratory || "—")}
							${
								m.library_buying_price
									? ` · ${__("Buying")} ${format_currency(m.library_buying_price)}`
									: ""
							}</p>
						<p class="text-muted">${__(
							"Open menu 2 — Manage TR & Sample Journey — to update sample locations for this product."
						)}</p>
					`,
					primary_action: {
						label: __("Manage journey"),
						action() {
							frappe.hide_msgprint();
							if (customer) {
								filter_customer.set_value(customer);
								state.filter_customer = customer;
							}
							switch_tab("journey");
						},
					},
				});
				load_board();
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
					message: __("Sample location → {0}", [location]),
					indicator: "green",
				});
				load_board();
			},
		});
	}

	function journey_bar(loc) {
		const idx = JOURNEY_STEPS.indexOf(loc);
		return `<div class="ic-ts-journey" title="${frappe.utils.escape_html(loc || "")}">
			${JOURNEY_STEPS.map((step, i) => {
				const on = idx >= 0 && i <= idx;
				const cur = i === idx;
				return `<span class="ic-ts-jdot ${on ? "is-on" : ""} ${cur ? "is-current" : ""}" title="${frappe.utils.escape_html(
					step
				)}"></span>`;
			}).join("")}
		</div>`;
	}

	function render_board(rows) {
		const $board = page.main.find("#ic-ts-board");
		if (!rows.length) {
			$board.html(
				`<div class="ic-ts-empty">${__(
					"No testing requests yet. Use menu 1 to generate one from the laboratory library."
				)}</div>`
			);
			return;
		}
		const html = rows
			.map((tr) => {
				const samples = (tr.samples || [])
					.map((s) => {
						const loc = s.sample_location || s.status || "—";
						const color = custody_color(loc);
						const btns = JOURNEY_STEPS.map(
							(l) =>
								`<button type="button" class="btn btn-xs btn-default ic-ts-loc" data-sample="${frappe.utils.escape_html(
									s.name
								)}" data-loc="${frappe.utils.escape_html(l)}" ${
									loc === l ? "disabled" : ""
								}>${frappe.utils.escape_html(LOC_SHORT[l] || l)}</button>`
						).join("");
						return `<div class="ic-ts-sample">
							<div class="ic-ts-sample-top">
								<a href="/app/ic-sample-tracking/${encodeURIComponent(s.name)}"><b>${frappe.utils.escape_html(
									s.tracking_number || s.name
								)}</b></a>
								<span class="ic-ts-pill" style="background:${color}22;color:${color}">${frappe.utils.escape_html(
									loc
								)}</span>
							</div>
							${journey_bar(loc)}
							<div class="text-muted" style="font-size:12px;margin:4px 0 6px">${frappe.utils.escape_html(
								s.sample_description || ""
							)}</div>
							<div class="ic-ts-loc-btns">${btns}</div>
						</div>`;
					})
					.join("");
				return `<article class="ic-ts-tr">
					<div class="ic-ts-tr-head">
						<div>
							<a href="/app/ic-testing-request/${encodeURIComponent(tr.name)}"><b>${frappe.utils.escape_html(
								tr.name
							)}</b></a>
							<span class="text-muted"> · ${frappe.utils.escape_html(tr.status || "")}</span>
							<div style="font-weight:600;margin-top:2px">${frappe.utils.escape_html(tr.title || tr.product || "")}</div>
							<div class="text-muted" style="font-size:12px">
								${frappe.utils.escape_html(tr.test_name || "—")}
								${tr.applicable_standard ? ` · ${frappe.utils.escape_html(tr.applicable_standard)}` : ""}
								· ${frappe.utils.escape_html(tr.laboratory_name || tr.laboratory || "—")}
								${
									tr.library_buying_price
										? ` · ${__("Buy")} ${format_currency(tr.library_buying_price)}`
										: ""
								}
							</div>
						</div>
						<div class="ic-ts-tr-links">
							${
								tr.customer
									? `<a class="btn btn-xs btn-default" href="/app/customer/${encodeURIComponent(
											tr.customer
									  )}">${__("Customer")}</a>`
									: ""
							}
							${
								tr.project
									? `<a class="btn btn-xs btn-default" href="/app/project/${encodeURIComponent(
											tr.project
									  )}">${__("Project")}</a>`
									: ""
							}
						</div>
					</div>
					<div class="ic-ts-samples">${samples || `<div class="text-muted">${__("No samples linked")}</div>`}</div>
				</article>`;
			})
			.join("");
		$board.html(html);
		$board.find(".ic-ts-loc").on("click", function () {
			set_location($(this).data("sample"), $(this).data("loc"));
		});
	}

	function load_board() {
		frappe.call({
			method: "instacertify.testing.events.list_testing_samples_board",
			args: {
				customer: state.filter_customer || "",
				project: state.filter_project || "",
				limit: 50,
			},
			callback(r) {
				render_board(r.message || []);
			},
		});
	}

	page.main.find(".ic-ts-tab").on("click", function () {
		switch_tab($(this).data("tab"));
	});
	page.main.find("#ic-ts-generate").on("click", generate);
	page.main.find("#ic-ts-refresh").on("click", load_board);
	page.main.find("#ic-ts-labs").on("click", () => frappe.set_route("List", "IC Laboratory"));
	page.main.find("#ic-ts-clear-filters").on("click", () => {
		filter_customer.set_value("");
		filter_project.set_value("");
		state.filter_customer = "";
		state.filter_project = "";
		load_board();
	});

	if (frappe.route_options) {
		if (frappe.route_options.customer) {
			form.set_value("customer", frappe.route_options.customer);
			filter_customer.set_value(frappe.route_options.customer);
			state.filter_customer = frappe.route_options.customer;
		}
		if (frappe.route_options.project) {
			form.set_value("project", frappe.route_options.project);
			filter_project.set_value(frappe.route_options.project);
			state.filter_project = frappe.route_options.project;
		}
		if (frappe.route_options.tab === "journey") {
			switch_tab("journey");
		}
		frappe.route_options = null;
	}

	set_step(1);
	load_library_options();
	load_board();
};

frappe.pages["testing-samples"].on_page_show = function () {
	/* board refreshes when opening Manage tab */
};
