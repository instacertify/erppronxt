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

	const LOCATIONS = [
		"At Instacertify Office",
		"In Transit to Lab",
		"At Laboratory",
		"At Instacertify Warehouse",
		"In Transit to Client",
		"Returned to Client",
	];

	page.main.html(`
		<div class="ic-ts">
			<div class="ic-ts-head">
				<div>
					<div class="ic-ts-kicker">${__("Laboratory · Testing · Custody")}</div>
					<div class="ic-ts-title">${__("Testing & Samples")}</div>
					<div class="ic-ts-sub">${__(
						"One place: pull test & pricing from the Laboratory Library, generate a Testing Request with samples, then update where each sample is (lab, warehouse, or back to client)."
					)}</div>
				</div>
				<div class="ic-ts-tools">
					<button type="button" class="btn btn-default btn-sm" id="ic-ts-labs">${__("Laboratories")}</button>
					<button type="button" class="btn btn-default btn-sm" id="ic-ts-refresh">${__("Refresh board")}</button>
				</div>
			</div>

			<div class="ic-ts-grid">
				<section class="ic-ts-card" id="ic-ts-create">
					<div class="ic-ts-card-title">${__("Generate Testing Request")}</div>
					<div class="ic-ts-card-sub">${__(
						"Pricing and lab data come from Active laboratories. Samples are created with the request."
					)}</div>
					<div class="ic-ts-form" id="ic-ts-form"></div>
					<div class="ic-ts-lab-offers" id="ic-ts-offers" hidden></div>
					<div class="ic-ts-actions">
						<button type="button" class="btn btn-primary" id="ic-ts-generate">${__("Generate Testing Request + Samples")}</button>
					</div>
				</section>

				<section class="ic-ts-card ic-ts-board-wrap">
					<div class="ic-ts-card-title">${__("Active board — request & sample location")}</div>
					<div class="ic-ts-card-sub">${__(
						"After a Testing Request is generated, update sample location here as it moves to the lab, warehouse, or client."
					)}</div>
					<div class="ic-ts-filters">
						<div class="ic-ts-filter" id="ic-ts-filter-customer"></div>
						<div class="ic-ts-filter" id="ic-ts-filter-project"></div>
						<button type="button" class="btn btn-xs btn-default" id="ic-ts-clear-filters">${__("Clear")}</button>
					</div>
					<div id="ic-ts-board" class="ic-ts-board" aria-live="polite"></div>
				</section>
			</div>
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
		filter_customer: "",
		filter_project: "",
	};

	// —— Create form fields ——
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
			{ fieldtype: "Section Break", label: __("From Laboratory Library") },
			{
				fieldname: "test_name",
				fieldtype: "Autocomplete",
				label: __("Test"),
				description: __("From Active lab libraries"),
				change() {
					state.test_name = form.get_value("test_name");
					load_offers(true);
				},
			},
			{
				fieldname: "applicable_standard",
				fieldtype: "Autocomplete",
				label: __("Applicable Standard"),
				change() {
					state.applicable_standard = form.get_value("applicable_standard");
					load_offers(true);
				},
			},
			{ fieldtype: "Column Break" },
			{
				fieldname: "laboratory",
				fieldtype: "Link",
				options: "IC Laboratory",
				label: __("Laboratory"),
				get_query() {
					return { filters: { status: "Active" } };
				},
				change() {
					state.laboratory = form.get_value("laboratory");
				},
			},
			{
				fieldname: "price_html",
				fieldtype: "HTML",
				label: __("Library prices"),
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

	function set_price_html(offer) {
		const el = form.get_field("price_html");
		if (!el) return;
		if (!offer) {
			el.$wrapper.html(
				`<div class="text-muted">${__("Pick a test or standard to compare labs and buying rates.")}</div>`
			);
			return;
		}
		el.$wrapper.html(`
			<div class="ic-ts-price">
				<div><span class="text-muted">${__("Buying")}</span><b>${format_currency(
					offer.purchase_price || 0,
					offer.currency || "INR"
				)}</b></div>
				<div><span class="text-muted">${__("Selling")}</span><b>${format_currency(
					offer.selling_price || 0,
					offer.currency || "INR"
				)}</b></div>
				<div class="text-muted">${frappe.utils.escape_html(offer.laboratory_name || "")} · ${frappe.utils.escape_html(
					offer.location || ""
				)}</div>
			</div>
		`);
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
		frappe.call({
			method: "instacertify.laboratory.api.get_standard_options",
			callback(r) {
				const vals = (r.message || []).map((o) => o.value || o);
				form.set_df_property("applicable_standard", "options", vals.join("\n"));
				const ctrl = form.get_field("applicable_standard");
				if (ctrl && ctrl.set_data) ctrl.set_data(vals);
			},
		});
	}

	function load_offers(open_picker) {
		const test_name = form.get_value("test_name");
		const standard = form.get_value("applicable_standard");
		if (!test_name && !standard) {
			page.main.find("#ic-ts-offers").prop("hidden", true).empty();
			set_price_html(null);
			return;
		}
		frappe.call({
			method: "instacertify.laboratory.api.get_labs_for_standard",
			args: {
				applicable_standard: standard || "",
				test_name: test_name || "",
			},
			callback(r) {
				state.offers = r.message || [];
				render_offers(state.offers, open_picker);
			},
		});
	}

	function apply_offer(offer) {
		if (!offer) return;
		state.laboratory = offer.laboratory;
		state.lab_scope_row = offer.scope_row;
		state.lab_offer = offer.value;
		form.set_value("laboratory", offer.laboratory);
		if (offer.test_name) form.set_value("test_name", offer.test_name);
		if (offer.applicable_standard) form.set_value("applicable_standard", offer.applicable_standard);
		set_price_html(offer);
		frappe.show_alert({
			message: __("Selected {0} — buying {1}", [
				offer.laboratory_name || offer.laboratory,
				format_currency(offer.purchase_price || 0, offer.currency || "INR"),
			]),
			indicator: "green",
		});
	}

	function render_offers(offers, open_picker) {
		const $box = page.main.find("#ic-ts-offers");
		if (!offers.length) {
			$box.prop("hidden", false).html(
				`<div class="text-muted">${__("No Active labs list this test/standard yet.")}</div>`
			);
			return;
		}
		const rows = offers
			.map((o, idx) => {
				const buy = format_currency(o.purchase_price || 0, o.currency || "INR");
				const sell = format_currency(o.selling_price || 0, o.currency || "INR");
				return `<tr data-idx="${idx}" class="ic-ts-offer-row" style="cursor:pointer">
					<td><b>${frappe.utils.escape_html(o.laboratory_name || "")}</b></td>
					<td>${frappe.utils.escape_html(o.location || "—")}</td>
					<td>${frappe.utils.escape_html(o.test_name || "")}</td>
					<td style="text-align:right;font-weight:700;color:#EC6820">${frappe.utils.escape_html(buy)}</td>
					<td style="text-align:right">${frappe.utils.escape_html(sell)}</td>
				</tr>`;
			})
			.join("");
		$box.prop("hidden", false).html(`
			<div class="ic-ts-offers-title">${__("Choose lab — compare buying rates")}</div>
			<table class="table table-bordered table-hover" style="margin:0;background:#fff">
				<thead><tr>
					<th>${__("Laboratory")}</th><th>${__("Location")}</th><th>${__("Test")}</th>
					<th style="text-align:right">${__("Buying")}</th>
					<th style="text-align:right">${__("Selling")}</th>
				</tr></thead>
				<tbody>${rows}</tbody>
			</table>
		`);
		$box.find(".ic-ts-offer-row").on("click", function () {
			apply_offer(offers[cint($(this).data("idx"))]);
		});
		if (open_picker && offers.length === 1) {
			apply_offer(offers[0]);
		}
	}

	function generate() {
		const customer = form.get_value("customer");
		if (!customer) {
			frappe.msgprint(__("Select a Customer first"));
			return;
		}
		if (!form.get_value("test_name") && !form.get_value("applicable_standard") && !form.get_value("laboratory")) {
			frappe.msgprint(__("Pick a Test / Standard from the lab library, or choose a Laboratory."));
			return;
		}
		frappe.call({
			method: "instacertify.testing.events.create_testing_and_samples",
			args: {
				customer,
				project: form.get_value("project") || "",
				product: form.get_value("product") || "",
				test_name: form.get_value("test_name") || "",
				applicable_standard: form.get_value("applicable_standard") || "",
				laboratory: form.get_value("laboratory") || state.laboratory || "",
				lab_scope_row: state.lab_scope_row || "",
				lab_offer: state.lab_offer || "",
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
							${m.library_buying_price ? ` · ${__("Buying")} ${format_currency(m.library_buying_price)}` : ""}</p>
						<p class="text-muted">${__(
							"Samples start as With Customer / Sample Awaited. Update location on the board as they move."
						)}</p>
					`,
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

	function render_board(rows) {
		const $board = page.main.find("#ic-ts-board");
		if (!rows.length) {
			$board.html(
				`<div class="ic-ts-empty">${__(
					"No testing requests yet. Generate one from the laboratory library on the left."
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
						const btns = LOCATIONS.map(
							(l) =>
								`<button type="button" class="btn btn-xs btn-default ic-ts-loc" data-sample="${frappe.utils.escape_html(
									s.name
								)}" data-loc="${frappe.utils.escape_html(l)}" ${
									loc === l ? "disabled" : ""
								}>${frappe.utils.escape_html(l.replace("At Instacertify ", "").replace("In Transit to ", "→ "))}</button>`
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
							<div class="text-muted" style="font-size:12px;margin:2px 0 6px">${frappe.utils.escape_html(
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
				limit: 40,
			},
			callback(r) {
				render_board(r.message || []);
			},
		});
	}

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

	// Route options (from Project / Customer)
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
		frappe.route_options = null;
	}

	load_library_options();
	set_price_html(null);
	load_board();
};

frappe.pages["testing-samples"].on_page_show = function () {
	// no-op — board reloads on generate
};
