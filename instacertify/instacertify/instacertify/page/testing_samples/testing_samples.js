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
						"Three menus: generate a Testing Request from the lab library, list all requests, then manage each sample’s journey."
					)}</div>
				</div>
				<div class="ic-ts-tools">
					<button type="button" class="btn btn-default btn-sm" id="ic-ts-labs">${__("Laboratories")}</button>
				</div>
			</div>

			<nav class="ic-ts-tabs" role="tablist" aria-label="${__("Testing & Samples menus")}">
				<button type="button" class="ic-ts-tab is-active" data-tab="generate" role="tab" aria-selected="true">
					${__("Generate Testing Request")}
				</button>
				<button type="button" class="ic-ts-tab" data-tab="requests" role="tab" aria-selected="false">
					${__("Testing Requests List")}
				</button>
				<button type="button" class="ic-ts-tab" data-tab="journey" role="tab" aria-selected="false">
					${__("Sample Journey")}
				</button>
			</nav>

			<!-- —— Submenu: Generate —— -->
			<section class="ic-ts-panel" id="ic-ts-panel-generate" role="tabpanel">
				<div class="ic-ts-card">
					<div class="ic-ts-card-title">${__("Generate Testing Request")}</div>
					<div class="ic-ts-card-sub">${__(
						"Select Test Name → pick Applicable Standard from the list → select a Laboratory (phone, address, contact) → generate."
					)}</div>

					<div class="ic-ts-steps" aria-hidden="true">
						<span class="ic-ts-step is-on" data-step="1">${__("Test")}</span>
						<span class="ic-ts-step" data-step="2">${__("Standard")}</span>
						<span class="ic-ts-step" data-step="3">${__("Lab")}</span>
						<span class="ic-ts-step" data-step="4">${__("Generate")}</span>
					</div>

					<div class="ic-ts-form" id="ic-ts-form"></div>

					<div class="ic-ts-section" id="ic-ts-standards-wrap" hidden>
						<div class="ic-ts-section-title">${__("Applicable standards list")}</div>
						<div class="ic-ts-table-wrap">
							<table class="ic-ts-table" id="ic-ts-standards-table">
								<thead>
									<tr>
										<th>${__("Applicable Standard")}</th>
										<th style="text-align:right">${__("Lab scopes")}</th>
										<th></th>
									</tr>
								</thead>
								<tbody></tbody>
							</table>
						</div>
					</div>

					<div class="ic-ts-section" id="ic-ts-labs-wrap" hidden>
						<div class="ic-ts-section-title">${__("Laboratories list")}</div>
						<div class="ic-ts-card-sub" style="margin-top:0">${__(
							"All Active labs with this test/standard — phone, address, contact person & designation."
						)}</div>
						<div class="ic-ts-table-wrap">
							<table class="ic-ts-table" id="ic-ts-labs-table">
								<thead>
									<tr>
										<th>${__("Laboratory")}</th>
										<th>${__("Phone")}</th>
										<th>${__("Address")}</th>
										<th>${__("Contact")}</th>
										<th>${__("Designation")}</th>
										<th style="text-align:right">${__("Buying")}</th>
										<th style="text-align:right">${__("Selling")}</th>
										<th></th>
									</tr>
								</thead>
								<tbody></tbody>
							</table>
						</div>
					</div>

					<div class="ic-ts-selected" id="ic-ts-selected" hidden></div>

					<div class="ic-ts-actions">
						<button type="button" class="btn btn-primary btn-lg" id="ic-ts-generate" disabled>
							${__("Generate Testing Request + Samples")}
						</button>
					</div>
				</div>
			</section>

			<!-- —— Submenu: Testing Requests list —— -->
			<section class="ic-ts-panel" id="ic-ts-panel-requests" role="tabpanel" hidden>
				<div class="ic-ts-card">
					<div class="ic-ts-card-title">${__("Testing Requests — listing")}</div>
					<div class="ic-ts-card-sub">${__(
						"All generated Testing Requests. Open a row or jump to Sample Journey to update custody."
					)}</div>
					<div class="ic-ts-filters">
						<div class="ic-ts-filter" id="ic-ts-filter-customer-req"></div>
						<div class="ic-ts-filter" id="ic-ts-filter-project-req"></div>
						<button type="button" class="btn btn-xs btn-default" id="ic-ts-clear-filters-req">${__("Clear")}</button>
						<button type="button" class="btn btn-xs btn-default" id="ic-ts-refresh-req">${__("Refresh")}</button>
						<button type="button" class="btn btn-xs btn-primary" id="ic-ts-goto-generate">${__("+ Generate new")}</button>
					</div>
					<div class="ic-ts-table-wrap">
						<table class="ic-ts-table" id="ic-ts-requests-table">
							<thead>
								<tr>
									<th>${__("Testing Request")}</th>
									<th>${__("Status")}</th>
									<th>${__("Product / Test")}</th>
									<th>${__("Standard")}</th>
									<th>${__("Laboratory")}</th>
									<th>${__("Customer")}</th>
									<th>${__("Project")}</th>
									<th style="text-align:right">${__("Samples")}</th>
									<th style="text-align:right">${__("Buying")}</th>
									<th></th>
								</tr>
							</thead>
							<tbody></tbody>
						</table>
					</div>
					<div id="ic-ts-requests-empty" class="ic-ts-empty" hidden></div>
				</div>
			</section>

			<!-- —— Submenu: Sample Journey —— -->
			<section class="ic-ts-panel" id="ic-ts-panel-journey" role="tabpanel" hidden>
				<div class="ic-ts-card">
					<div class="ic-ts-card-title">${__("Sample journey — listing")}</div>
					<div class="ic-ts-card-sub">${__(
						"Manage where each sample is for every Testing Request (customer → office → lab → warehouse → client)."
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
		board_rows: [],
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
					clear_lab_selection();
					form.set_value("applicable_standard", "");
					load_standards_for_test();
				},
			},
			{ fieldtype: "Column Break" },
			{
				fieldname: "applicable_standard",
				fieldtype: "Data",
				label: __("Applicable Standard (selected)"),
				read_only: 1,
				description: __("Chosen from the standards list below"),
			},
		],
		body: page.main.find("#ic-ts-form"),
	});
	form.make();

	function make_filter(parent_sel, key) {
		return frappe.ui.form.make_control({
			parent: page.main.find(parent_sel),
			df: {
				fieldtype: "Link",
				options: key === "customer" ? "Customer" : "Project",
				label: key === "customer" ? __("Filter customer") : __("Filter project"),
				change() {
					const ctrl = key === "customer" ? filter_customer : filter_project;
					const val = ctrl.get_value();
					if (key === "customer") {
						state.filter_customer = val;
						if (filter_customer_req.get_value() !== val) filter_customer_req.set_value(val || "");
					} else {
						state.filter_project = val;
						if (filter_project_req.get_value() !== val) filter_project_req.set_value(val || "");
					}
					refresh_lists();
				},
			},
			render_input: true,
		});
	}

	const filter_customer = make_filter("#ic-ts-filter-customer", "customer");
	const filter_project = make_filter("#ic-ts-filter-project", "project");

	const filter_customer_req = frappe.ui.form.make_control({
		parent: page.main.find("#ic-ts-filter-customer-req"),
		df: {
			fieldtype: "Link",
			options: "Customer",
			label: __("Filter customer"),
			change() {
				const val = filter_customer_req.get_value();
				state.filter_customer = val;
				if (filter_customer.get_value() !== val) filter_customer.set_value(val || "");
				refresh_lists();
			},
		},
		render_input: true,
	});
	const filter_project_req = frappe.ui.form.make_control({
		parent: page.main.find("#ic-ts-filter-project-req"),
		df: {
			fieldtype: "Link",
			options: "Project",
			label: __("Filter project"),
			change() {
				const val = filter_project_req.get_value();
				state.filter_project = val;
				if (filter_project.get_value() !== val) filter_project.set_value(val || "");
				refresh_lists();
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
		page.main.find("#ic-ts-labs-table tbody tr").removeClass("is-selected");
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
		page.main.find("#ic-ts-panel-requests").prop("hidden", tab !== "requests");
		page.main.find("#ic-ts-panel-journey").prop("hidden", tab !== "journey");
		if (tab === "requests" || tab === "journey") refresh_lists();
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
		if (!test_name) {
			$wrap.prop("hidden", true);
			page.main.find("#ic-ts-labs-wrap").prop("hidden", true);
			set_step(1);
			return;
		}
		set_step(2);
		frappe.call({
			method: "instacertify.laboratory.api.get_standards_for_test",
			args: { test_name },
			callback(r) {
				state.standards = r.message || [];
				render_standards_table(state.standards);
				if (state.standards.length === 1) {
					pick_standard(state.standards[0].value || state.standards[0]);
				} else if (!state.standards.length) {
					load_labs();
				}
			},
		});
	}

	function render_standards_table(standards) {
		const $wrap = page.main.find("#ic-ts-standards-wrap");
		const $tbody = page.main.find("#ic-ts-standards-table tbody");
		$wrap.prop("hidden", false);
		if (!standards.length) {
			$tbody.html(
				`<tr><td colspan="3" class="text-muted">${__(
					"No applicable standard listed for this test — labs will be listed by test name."
				)}</td></tr>`
			);
			return;
		}
		$tbody.html(
			standards
				.map((s, idx) => {
					const label = s.value || s;
					const active = state.applicable_standard === label ? "is-selected" : "";
					return `<tr class="${active}" data-idx="${idx}">
						<td><b>${frappe.utils.escape_html(label)}</b></td>
						<td style="text-align:right">${cint(s.lab_count) || "—"}</td>
						<td style="text-align:right">
							<button type="button" class="btn btn-xs btn-default ic-ts-pick-std" data-idx="${idx}">
								${active ? __("Selected") : __("Select")}
							</button>
						</td>
					</tr>`;
				})
				.join("")
		);
		$tbody.find(".ic-ts-pick-std").on("click", function () {
			const s = standards[cint($(this).data("idx"))];
			pick_standard(s.value || s);
		});
		$tbody.find("tr[data-idx]").on("click", function (e) {
			if ($(e.target).closest("button").length) return;
			const s = standards[cint($(this).data("idx"))];
			pick_standard(s.value || s);
		});
	}

	function pick_standard(label) {
		state.applicable_standard = label;
		form.set_value("applicable_standard", label);
		clear_lab_selection();
		render_standards_table(state.standards);
		load_labs();
	}

	function load_labs() {
		const test_name = form.get_value("test_name") || "";
		const standard = state.applicable_standard || "";
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
				`<tr><td colspan="8" class="text-muted">${__(
					"No Active labs list this test/standard. Add scope & pricing on Laboratories."
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
						<td>
							<b>${frappe.utils.escape_html(o.laboratory_name || "")}</b>
							<div class="text-muted" style="font-size:11px">${frappe.utils.escape_html(o.test_name || "")}</div>
						</td>
						<td>${frappe.utils.escape_html(o.phone || "—")}</td>
						<td style="max-width:220px">${frappe.utils.escape_html(o.address || o.location || "—")}</td>
						<td>${frappe.utils.escape_html(o.contact_person || "—")}</td>
						<td>${frappe.utils.escape_html(o.contact_designation || "—")}</td>
						<td style="text-align:right;font-weight:700;color:#EC6820">${frappe.utils.escape_html(buy)}</td>
						<td style="text-align:right">${frappe.utils.escape_html(sell)}</td>
						<td style="text-align:right">
							<button type="button" class="btn btn-xs ${selected ? "btn-primary" : "btn-default"} ic-ts-pick-lab" data-idx="${idx}">
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
		const buy = format_currency(offer.purchase_price || 0, offer.currency || "INR");
		page.main.find("#ic-ts-selected").prop("hidden", false).html(`
			<div class="ic-ts-selected-inner">
				<div class="ic-ts-selected-label">${__("Selected laboratory")}</div>
				<div class="ic-ts-selected-name">${frappe.utils.escape_html(offer.laboratory_name || "")}</div>
				<div class="text-muted" style="font-size:12px;margin-top:4px">
					${frappe.utils.escape_html(offer.contact_person || "")}
					${offer.contact_designation ? ` (${frappe.utils.escape_html(offer.contact_designation)})` : ""}
					· ${frappe.utils.escape_html(offer.phone || "—")}
					· ${frappe.utils.escape_html(offer.address || offer.location || "—")}
					· ${__("Buying")} ${frappe.utils.escape_html(buy)}
				</div>
			</div>
		`);
		page.main.find("#ic-ts-generate").prop("disabled", false);
		set_step(4);
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
				frappe.show_alert({
					message: __("Created {0} with {1} sample(s)", [
						m.testing_request,
						(m.samples || []).length,
					]),
					indicator: "green",
				});
				if (customer) {
					filter_customer.set_value(customer);
					filter_customer_req.set_value(customer);
					state.filter_customer = customer;
				}
				switch_tab("requests");
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
				refresh_lists();
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

	function render_requests_table(rows) {
		const $tbody = page.main.find("#ic-ts-requests-table tbody");
		const $empty = page.main.find("#ic-ts-requests-empty");
		if (!rows.length) {
			$tbody.empty();
			$empty
				.prop("hidden", false)
				.text(__("No testing requests yet. Use Generate Testing Request to create one."));
			return;
		}
		$empty.prop("hidden", true);
		$tbody.html(
			rows
				.map((tr) => {
					const sample_count = (tr.samples || []).length || cint(tr.number_of_samples) || 0;
					const buy = tr.library_buying_price
						? format_currency(tr.library_buying_price)
						: "—";
					return `<tr>
						<td><a href="/app/ic-testing-request/${encodeURIComponent(tr.name)}"><b>${frappe.utils.escape_html(
							tr.name
						)}</b></a></td>
						<td>${frappe.utils.escape_html(tr.status || "")}</td>
						<td>${frappe.utils.escape_html(tr.product || tr.title || "—")}<div class="text-muted" style="font-size:11px">${frappe.utils.escape_html(
							tr.test_name || ""
						)}</div></td>
						<td>${frappe.utils.escape_html(tr.applicable_standard || "—")}</td>
						<td>${frappe.utils.escape_html(tr.laboratory_name || tr.laboratory || "—")}</td>
						<td>${
							tr.customer
								? `<a href="/app/customer/${encodeURIComponent(tr.customer)}">${frappe.utils.escape_html(
										tr.customer
								  )}</a>`
								: "—"
						}</td>
						<td>${
							tr.project
								? `<a href="/app/project/${encodeURIComponent(tr.project)}">${frappe.utils.escape_html(
										tr.project
								  )}</a>`
								: "—"
						}</td>
						<td style="text-align:right">${sample_count}</td>
						<td style="text-align:right">${frappe.utils.escape_html(buy)}</td>
						<td style="text-align:right;white-space:nowrap">
							<button type="button" class="btn btn-xs btn-default ic-ts-open-journey" data-tr="${frappe.utils.escape_html(
								tr.name
							)}">${__("Sample journey")}</button>
						</td>
					</tr>`;
				})
				.join("")
		);
		$tbody.find(".ic-ts-open-journey").on("click", function () {
			switch_tab("journey");
			const tr = $(this).data("tr");
			const $card = page.main.find(`.ic-ts-tr[data-tr="${CSS.escape(tr)}"]`);
			if ($card.length) {
				$("html, body").animate({ scrollTop: $card.offset().top - 80 }, 200);
				$card.addClass("ic-ts-flash");
				setTimeout(() => $card.removeClass("ic-ts-flash"), 1200);
			}
		});
	}

	function render_journey_board(rows) {
		const $board = page.main.find("#ic-ts-board");
		if (!rows.length) {
			$board.html(
				`<div class="ic-ts-empty">${__(
					"No testing requests yet. Generate one from the first submenu."
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
						return `<tr>
							<td><a href="/app/ic-sample-tracking/${encodeURIComponent(s.name)}"><b>${frappe.utils.escape_html(
								s.tracking_number || s.name
							)}</b></a>
							<div class="text-muted" style="font-size:11px">${frappe.utils.escape_html(
								s.sample_description || ""
							)}</div></td>
							<td><span class="ic-ts-pill" style="background:${color}22;color:${color}">${frappe.utils.escape_html(
								loc
							)}</span>${journey_bar(loc)}</td>
							<td><div class="ic-ts-loc-btns">${btns}</div></td>
						</tr>`;
					})
					.join("");
				return `<article class="ic-ts-tr" data-tr="${frappe.utils.escape_html(tr.name)}">
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
							</div>
						</div>
					</div>
					<div class="ic-ts-table-wrap">
						<table class="ic-ts-table">
							<thead><tr>
								<th>${__("Sample")}</th>
								<th>${__("Location")}</th>
								<th>${__("Update journey")}</th>
							</tr></thead>
							<tbody>${samples || `<tr><td colspan="3" class="text-muted">${__("No samples linked")}</td></tr>`}</tbody>
						</table>
					</div>
				</article>`;
			})
			.join("");
		$board.html(html);
		$board.find(".ic-ts-loc").on("click", function () {
			set_location($(this).data("sample"), $(this).data("loc"));
		});
	}

	function refresh_lists() {
		frappe.call({
			method: "instacertify.testing.events.list_testing_samples_board",
			args: {
				customer: state.filter_customer || "",
				project: state.filter_project || "",
				limit: 80,
			},
			callback(r) {
				state.board_rows = r.message || [];
				render_requests_table(state.board_rows);
				render_journey_board(state.board_rows);
			},
		});
	}

	page.main.find(".ic-ts-tab").on("click", function () {
		switch_tab($(this).data("tab"));
	});
	page.main.find("#ic-ts-generate").on("click", generate);
	page.main.find("#ic-ts-refresh, #ic-ts-refresh-req").on("click", refresh_lists);
	page.main.find("#ic-ts-labs").on("click", () => frappe.set_route("List", "IC Laboratory"));
	page.main.find("#ic-ts-goto-generate").on("click", () => switch_tab("generate"));
	page.main.find("#ic-ts-clear-filters, #ic-ts-clear-filters-req").on("click", () => {
		filter_customer.set_value("");
		filter_project.set_value("");
		filter_customer_req.set_value("");
		filter_project_req.set_value("");
		state.filter_customer = "";
		state.filter_project = "";
		refresh_lists();
	});

	if (frappe.route_options) {
		if (frappe.route_options.customer) {
			form.set_value("customer", frappe.route_options.customer);
			filter_customer.set_value(frappe.route_options.customer);
			filter_customer_req.set_value(frappe.route_options.customer);
			state.filter_customer = frappe.route_options.customer;
		}
		if (frappe.route_options.project) {
			form.set_value("project", frappe.route_options.project);
			filter_project.set_value(frappe.route_options.project);
			filter_project_req.set_value(frappe.route_options.project);
			state.filter_project = frappe.route_options.project;
		}
		if (frappe.route_options.tab) {
			switch_tab(frappe.route_options.tab);
		}
		frappe.route_options = null;
	}

	set_step(1);
	load_library_options();
	refresh_lists();
};

frappe.pages["testing-samples"].on_page_show = function () {};
