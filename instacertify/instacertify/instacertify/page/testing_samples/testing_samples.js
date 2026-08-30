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

	/** Print 50×25 mm sample QR stickers (browser print dialog). */
	function print_qr_labels(labels) {
		if (window.instacertify && typeof instacertify.print_sample_qr_labels === "function") {
			instacertify.print_sample_qr_labels(labels);
			return;
		}
		if (!labels || !labels.length) return;
		const sheets = labels
			.map((lab) => {
				const trk = lab.tracking_number || lab.name || "";
				const sticker = lab.sticker_data_uri || lab.sticker_url || "";
				const qr = lab.qr_data_uri || lab.qr_code || "";
				if (sticker) {
					return `<div class="sheet"><img class="full" src="${frappe.utils.escape_html(
						sticker
					)}" alt="${frappe.utils.escape_html(trk)}"/></div>`;
				}
				return `<div class="sheet"><div class="sticker">
					${qr ? `<img class="qr" src="${frappe.utils.escape_html(qr)}" alt="QR"/>` : ""}
					<div class="meta">
						<div class="lbl">SAMPLE</div>
						<div class="trk">${frappe.utils.escape_html(trk)}</div>
						<div class="info">For more information visit<br><b>www.instacertify.com</b></div>
					</div>
				</div></div>`;
			})
			.join("");
		const w = window.open("", "_blank");
		if (!w) {
			frappe.msgprint(__("Please allow pop-ups to print QR labels."));
			return;
		}
		w.document.write(`<!doctype html><html><head><title>Print Sample QR</title>
			<style>
				@page { size: 50mm 25mm; margin: 0; }
				html, body { margin: 0; padding: 0; }
				.sheet { page-break-after: always; width: 50mm; height: 25mm; }
				.sheet:last-child { page-break-after: auto; }
				.sheet img.full { width: 50mm; height: 25mm; object-fit: contain; display: block; }
				.sticker { box-sizing: border-box; width: 50mm; height: 25mm; padding: 1.2mm 1.4mm;
					display: flex; align-items: center; gap: 1.6mm; font-family: Arial, sans-serif; }
				.sticker img.qr { width: 18mm; height: 18mm; image-rendering: pixelated; }
				.sticker .trk { font-family: monospace; font-size: 3.1mm; font-weight: 700; word-break: break-all; }
				.sticker .lbl { font-size: 2.1mm; font-weight: 700; }
				.sticker .info { font-size: 1.85mm; line-height: 1.25; }
				@media screen {
					body { padding: 16px; background: #eef2f5; }
					.sheet { margin: 0 auto 12px; background: #fff; border: 1px solid #cfd8dc; }
				}
			</style></head><body>${sheets}
			<script>window.onload=function(){setTimeout(function(){window.print()},200)}</script>
			</body></html>`);
		w.document.close();
	}

	/** Open sample QR dialog — works even if desk bundle failed to attach helpers. */
	function open_tr_qr_dialog(payload) {
		if (
			window.instacertify &&
			typeof instacertify.show_testing_request_sample_qr_dialog === "function"
		) {
			instacertify.show_testing_request_sample_qr_dialog(payload || {});
			return;
		}
		const labels = (payload && payload.labels) || [];
		if (!labels.length) {
			frappe.msgprint({
				title: __("No sample QR"),
				message: __("No sample tracking numbers found for this Testing Request."),
				indicator: "orange",
			});
			return;
		}
		const cards = labels
			.map((lab) => {
				const trk = lab.tracking_number || lab.name || "";
				const img =
					lab.sticker_data_uri || lab.qr_data_uri || lab.sticker_url || lab.qr_code || "";
				return `<div class="ic-ts-qr-card" data-sample="${frappe.utils.escape_html(lab.name)}" style="border:1.5px solid #9eb8c8;border-radius:12px;padding:12px;background:#fff;">
					<div style="font-size:11px;font-weight:700;color:#065175;margin-bottom:8px;">50 × 25 mm · unique sample QR</div>
					${
						img
							? `<img src="${frappe.utils.escape_html(img)}" alt="QR ${frappe.utils.escape_html(
									trk
							  )}" style="width:200px;height:100px;object-fit:contain;border:1px solid #cfd8dc;background:#fff;display:block;"/>`
							: `<div style="padding:20px;color:#c62828;">${__("QR image missing")}</div>`
					}
					<div style="margin-top:8px;font-size:12px;display:flex;justify-content:space-between;gap:8px;">
						<span>${__("Sample code")}</span>
						<b style="font-family:monospace;color:#065175;">${frappe.utils.escape_html(trk)}</b>
					</div>
					<div style="margin-top:10px;display:flex;flex-wrap:wrap;gap:6px;">
						<button type="button" class="btn btn-xs btn-primary ic-ts-print-one" data-sample="${frappe.utils.escape_html(
							lab.name
						)}">${__("Print QR")}</button>
						<button type="button" class="btn btn-xs btn-default ic-ts-dl-one" data-sample="${frappe.utils.escape_html(
							lab.name
						)}">${__("Download PNG")}</button>
						<a class="btn btn-xs btn-default" href="/app/ic-sample-tracking/${encodeURIComponent(
							lab.name
						)}">${__("Open")}</a>
					</div>
				</div>`;
			})
			.join("");
		const d = new frappe.ui.Dialog({
			title: __("Sample QR — {0}", [(payload && payload.testing_request) || ""]),
			size: "large",
			fields: [
				{
					fieldtype: "HTML",
					options: `<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px;">${cards}</div>`,
				},
			],
			primary_action_label: __("Print QR"),
			primary_action() {
				print_qr_labels(labels);
			},
			secondary_action_label: __("Close"),
			secondary_action() {
				d.hide();
			},
		});
		d.$body.find(".ic-ts-print-one").on("click", function () {
			const name = $(this).data("sample");
			const lab = labels.find((x) => x.name === name);
			if (lab) print_qr_labels([lab]);
		});
		d.$body.find(".ic-ts-dl-one").on("click", function () {
			const name = $(this).data("sample");
			const lab = labels.find((x) => x.name === name);
			if (!lab) return;
			const src = lab.sticker_data_uri || lab.sticker_url || lab.qr_data_uri || lab.qr_code || "";
			const fname = (lab.tracking_number || lab.name || "sample-qr") + ".png";
			if (window.instacertify && typeof instacertify.download_png === "function") {
				instacertify.download_png(src, fname);
			} else if (src) {
				const a = document.createElement("a");
				a.href = src;
				a.download = fname;
				a.target = "_blank";
				document.body.appendChild(a);
				a.click();
				a.remove();
			}
		});
		d.show();
	}

	function load_and_show_tr_qr(testing_request) {
		if (!testing_request) return;
		frappe.call({
			method: "instacertify.testing.events.get_testing_request_sample_labels",
			args: { testing_request },
			freeze: true,
			freeze_message: __("Loading sample QR labels…"),
			callback(r) {
				open_tr_qr_dialog(r.message || {});
			},
		});
	}

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
				<button type="button" class="ic-ts-tab ic-ts-tab-gen is-active" data-tab="generate" role="tab" aria-selected="true">
					<span class="ic-ts-tab-dot" aria-hidden="true"></span>
					<span class="ic-ts-tab-label">${__("Generate")}</span>
				</button>
				<button type="button" class="ic-ts-tab ic-ts-tab-manage" data-tab="manage" role="tab" aria-selected="false">
					<span class="ic-ts-tab-dot" aria-hidden="true"></span>
					<span class="ic-ts-tab-label">${__("Manage TR")}</span>
				</button>
			</nav>

			<!-- —— Generate —— -->
			<section class="ic-ts-panel" id="ic-ts-panel-generate" role="tabpanel">
				<div class="ic-ts-gen-layout">
					<div class="ic-ts-card ic-ts-gen-main">
						<div class="ic-ts-card-head">
							<div>
								<div class="ic-ts-card-title">${__("Generate")}</div>
								<div class="ic-ts-card-sub">${__(
									"Customer → Test → Standard → Lab. After create, unique 50×25 mm sample QR labels open automatically."
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

						<div class="ic-ts-section" id="ic-ts-reuse-wrap" hidden>
							<div class="ic-ts-section-head">
								<div class="ic-ts-section-title">${__("Reuse samples at this lab (optional)")}</div>
								<div class="ic-ts-card-sub" style="margin:0">${__(
									"One physical sample can cover multiple tests at the same laboratory — not at different labs. Select existing samples to link, or leave empty to create new ones."
								)}</div>
							</div>
							<div class="ic-ts-table-wrap">
								<table class="ic-ts-table" id="ic-ts-reuse-table">
									<thead>
										<tr>
											<th style="width:44px">${__("Use")}</th>
											<th>${__("Tracking #")}</th>
											<th>${__("Location")}</th>
											<th>${__("Description")}</th>
											<th>${__("Already linked tests")}</th>
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
						<div class="ic-ts-price-edit" id="ic-ts-price-edit" hidden>
							<div class="ic-ts-section-title" style="margin:10px 0 6px">${__("Buying / Selling (editable)")}</div>
							<div class="ic-ts-card-sub" style="margin:0 0 8px">${__(
								"Stored on the Testing Request for lab buy invoices and customer sell records."
							)}</div>
							<div class="ic-ts-price-grid">
								<label>${__("Buying")}
									<input type="number" step="0.01" min="0" class="form-control input-sm" id="ic-ts-buy-price"/>
								</label>
								<label>${__("Selling")}
									<input type="number" step="0.01" min="0" class="form-control input-sm" id="ic-ts-sell-price"/>
								</label>
								<label>${__("Currency")}
									<input type="text" class="form-control input-sm" id="ic-ts-price-currency" placeholder="INR"/>
								</label>
							</div>
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
							<div class="ic-ts-card-title">${__("Manage TR")}</div>
							<div class="ic-ts-card-sub" style="margin-bottom:0">${__(
								"All Testing Requests in one outlined table. Samples open in a bordered sub-table. Click QR / Print for labels."
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
		reuse_samples: [],
		reusable: [],
		board_rows: [],
		filter_customer: "",
		filter_project: "",
		expanded: {},
		tab: "generate",
		focus_tr: "",
		buy_price: null,
		sell_price: null,
		price_currency: "INR",
		manage_page_size: 20,
		manage_visible: 20,
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
					if (state.selected_offer) load_reusable_samples();
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
		state.reuse_samples = [];
		state.reusable = [];
		page.main.find("#ic-ts-generate").prop("disabled", true);
		page.main.find("#ic-ts-labs-table tbody tr").removeClass("is-selected");
		page.main.find("#ic-ts-reuse-wrap").prop("hidden", true);
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
		if (state.reuse_samples.length) {
			rows.push([__("Reuse samples"), String(state.reuse_samples.length)]);
		}
		if (offer) {
			rows.push([__("Phone"), offer.phone || "—"]);
			rows.push([
				__("Contact"),
				[offer.contact_person, offer.contact_designation].filter(Boolean).join(" · ") || "—",
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
		const $price = page.main.find("#ic-ts-price-edit");
		if (offer) {
			$price.prop("hidden", false);
			if (state.buy_price == null) {
				state.buy_price = flt(offer.purchase_price || 0);
			}
			if (state.sell_price == null) {
				state.sell_price = flt(offer.selling_price || 0);
			}
			if (!state.price_currency) {
				state.price_currency = offer.currency || "INR";
			}
			page.main.find("#ic-ts-buy-price").val(state.buy_price);
			page.main.find("#ic-ts-sell-price").val(state.sell_price);
			page.main.find("#ic-ts-price-currency").val(state.price_currency || "INR");
		} else {
			$price.prop("hidden", true);
			state.buy_price = null;
			state.sell_price = null;
			state.price_currency = "INR";
		}
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
		state.reuse_samples = [];
		state.buy_price = flt(offer.purchase_price || 0);
		state.sell_price = flt(offer.selling_price || 0);
		state.price_currency = offer.currency || "INR";
		if (offer.test_name) {
			state.test_name = offer.test_name;
			form.set_value("test_name", offer.test_name);
		}
		if (offer.applicable_standard) {
			state.applicable_standard = offer.applicable_standard;
			form.set_value("applicable_standard", offer.applicable_standard);
		}
		render_labs_table(state.offers);
		load_reusable_samples();
		set_step(4);
		update_summary();
		frappe.show_alert({
			message: __("Lab selected — edit buying/selling if needed, then generate"),
			indicator: "green",
		});
	}

	function load_reusable_samples() {
		const customer = form.get_value("customer");
		const laboratory = state.laboratory || (state.selected_offer && state.selected_offer.laboratory);
		const $wrap = page.main.find("#ic-ts-reuse-wrap");
		if (!customer || !laboratory) {
			$wrap.prop("hidden", true);
			return;
		}
		frappe.call({
			method: "instacertify.testing.events.get_reusable_samples",
			args: {
				customer,
				laboratory,
				project: form.get_value("project") || "",
			},
			callback(r) {
				state.reusable = r.message || [];
				render_reuse_table(state.reusable);
			},
		});
	}

	function render_reuse_table(rows) {
		const $wrap = page.main.find("#ic-ts-reuse-wrap");
		const $tbody = page.main.find("#ic-ts-reuse-table tbody");
		if (!rows.length) {
			$wrap.prop("hidden", true);
			return;
		}
		$wrap.prop("hidden", false);
		$tbody.html(
			rows
				.map((s) => {
					const checked = state.reuse_samples.includes(s.name) ? "checked" : "";
					const linked = (s.linked_testing_requests || []).join(", ") || "—";
					return `<tr data-sample="${frappe.utils.escape_html(s.name)}">
						<td>
							<input type="checkbox" class="ic-ts-reuse-check" data-sample="${frappe.utils.escape_html(
								s.name
							)}" ${checked} />
						</td>
						<td><b>${frappe.utils.escape_html(s.tracking_number || s.name)}</b></td>
						<td>${frappe.utils.escape_html(s.sample_location || s.status || "—")}</td>
						<td class="ic-ts-desc-cell">${frappe.utils.escape_html(s.sample_description || "—")}</td>
						<td class="ic-ts-cell-sub">${frappe.utils.escape_html(linked)}
							${s.linked_count ? ` <span class="ic-ts-count">${cint(s.linked_count)}</span>` : ""}
						</td>
					</tr>`;
				})
				.join("")
		);
		$tbody.find(".ic-ts-reuse-check").on("change", function () {
			const name = $(this).data("sample");
			if (this.checked) {
				if (!state.reuse_samples.includes(name)) state.reuse_samples.push(name);
			} else {
				state.reuse_samples = state.reuse_samples.filter((x) => x !== name);
			}
			update_summary();
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
		const buy = flt(page.main.find("#ic-ts-buy-price").val());
		const sell = flt(page.main.find("#ic-ts-sell-price").val());
		const currency = (page.main.find("#ic-ts-price-currency").val() || "INR").trim() || "INR";
		state.buy_price = buy;
		state.sell_price = sell;
		state.price_currency = currency;
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
				reuse_samples: state.reuse_samples || [],
				library_buying_price: buy,
				suggested_selling_price: sell,
				price_currency: currency,
			},
			freeze: true,
			freeze_message: __("Generating Testing Request and samples…"),
			callback(r) {
				const m = r.message || {};
				state.focus_tr = m.testing_request || "";
				state.expanded[m.testing_request] = true;
				frappe.show_alert({
					message: __("Created {0} — printable sample QR labels ready", [m.testing_request]),
					indicator: "green",
				});
				if (customer) {
					filter_customer.set_value(customer);
					state.filter_customer = customer;
				}
				const labels_payload = m.sample_labels || null;
				const open_labels = () => {
					if (labels_payload && (labels_payload.labels || []).length) {
						open_tr_qr_dialog(labels_payload);
					} else if (m.testing_request) {
						load_and_show_tr_qr(m.testing_request);
					}
				};
				open_labels();
				switch_tab("manage");
				if (m.testing_request) {
					frappe.confirm(
						__(
							"Create a Test Request Form (TRF) share link for the customer to fill sample/product details? Case handlers can fill the same form."
						),
						() => {
							frappe.call({
								method: "instacertify.trf.api.create_or_get_trf",
								args: { testing_request: m.testing_request, share: 1 },
								freeze: true,
								callback(tr) {
									const x = tr.message || {};
									const url = x.url || x.share_url || "";
									frappe.msgprint({
										title: __("TRF customer fill link"),
										message: `<p><a href="${frappe.utils.escape_html(
											url
										)}" target="_blank">${frappe.utils.escape_html(url)}</a></p>
										<p>
										<a class="btn btn-xs btn-primary" href="/app/ic-test-request-form/${encodeURIComponent(
											x.name
										)}">${__("Open TRF")}</a>
										<a class="btn btn-xs btn-default" href="/app/ic-test-request-form/${encodeURIComponent(
											x.name
										)}">${__("Edit TRF")}</a>
										</p>`,
										indicator: "green",
									});
								},
							});
						}
					);
				}
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
				state._keep_visible = true;
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

	function status_class(status) {
		const s = String(status || "").toLowerCase();
		if (s.includes("report") || s.includes("complete") || s.includes("closed")) return "is-done";
		if (s.includes("progress") || s.includes("testing") || s.includes("lab")) return "is-progress";
		if (s.includes("await") || s.includes("sample") || s.includes("dispatch")) return "is-wait";
		if (s.includes("cancel") || s.includes("hold")) return "is-hold";
		return "is-new";
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

		const page_size = cint(state.manage_page_size) || 20;
		let visible = cint(state.manage_visible) || page_size;
		if (visible < page_size) visible = page_size;
		// Keep focused TR in view after generate
		if (state.focus_tr) {
			const idx = rows.findIndex((r) => r.name === state.focus_tr);
			if (idx >= 0 && idx + 1 > visible) {
				visible = Math.ceil((idx + 1) / page_size) * page_size;
				state.manage_visible = visible;
			}
		}
		const total = rows.length;
		const shown = rows.slice(0, visible);
		const remaining = Math.max(0, total - shown.length);

		const body = shown
			.map((tr, i) => {
				const open = !!state.expanded[tr.name];
				const samples = tr.samples || [];
				const buy = tr.library_buying_price
					? format_currency(tr.library_buying_price, tr.price_currency || "INR")
					: "—";
				const sell = tr.suggested_selling_price
					? format_currency(tr.suggested_selling_price, tr.price_currency || "INR")
					: "—";
				const focus = state.focus_tr === tr.name ? "ic-ts-flash" : "";
				const zebra = i % 2 === 1 ? "is-alt" : "";

				const sample_table = !samples.length
					? `<div class="ic-ts-nested-empty text-muted">${__("No samples linked yet.")}</div>`
					: `<div class="ic-ts-table-wrap ic-ts-nested-wrap">
						<table class="ic-ts-table ic-ts-samples-table">
							<thead>
								<tr>
									<th>${__("Tracking #")}</th>
									<th>${__("Description")}</th>
									<th>${__("Location")}</th>
									<th>${__("Tests")}</th>
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
											<td style="text-align:center"><span class="ic-ts-count" title="${__(
												"Linked tests at same lab"
											)}">${cint(s.linked_test_count) || 1}</span></td>
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
						<tr class="ic-ts-tr-row ic-ts-tr-group ${open ? "is-open" : ""} ${zebra} ${focus}" data-tr="${frappe.utils.escape_html(
							tr.name
						)}">
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
							<td class="ic-ts-status-cell">
								<span class="ic-ts-status ${status_class(tr.status)}">${frappe.utils.escape_html(
									tr.status || "—"
								)}</span>
							</td>
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
							<td class="ic-ts-money ic-ts-money-buy">
								<div title="${__("Buying")}">${frappe.utils.escape_html(buy)}</div>
								<div class="ic-ts-cell-sub" title="${__("Selling")}">${__("Sell")}: ${frappe.utils.escape_html(
									sell
								)}</div>
							</td>
							<td style="text-align:center"><span class="ic-ts-count">${samples.length}</span></td>
							<td class="ic-ts-actions-cell">
								<button type="button" class="btn btn-xs ic-ts-btn-qr ic-ts-print-qr" data-tr="${frappe.utils.escape_html(
									tr.name
								)}" title="${__("View & print sample QR")}">${__("QR")}</button>
								<button type="button" class="btn btn-xs btn-default ic-ts-print-qr-direct" data-tr="${frappe.utils.escape_html(
									tr.name
								)}" title="${__("Print 50×25 mm QR labels")}">${__("Print")}</button>
								<button type="button" class="btn btn-xs btn-default ic-ts-trf-link" data-tr="${frappe.utils.escape_html(
									tr.name
								)}" data-trf="${frappe.utils.escape_html(tr.trf_name || "")}" data-url="${frappe.utils.escape_html(
									tr.trf_share_url || ""
								)}" title="${__(
									"Generate / copy TRF customer fill link"
								)}">${__("TRF Link")}</button>
								<button type="button" class="btn btn-xs btn-default ic-ts-trf-edit" data-tr="${frappe.utils.escape_html(
									tr.name
								)}" data-trf="${frappe.utils.escape_html(tr.trf_name || "")}" data-status="${frappe.utils.escape_html(
									tr.trf_status || ""
								)}" title="${__("Open / edit TRF (reopen if locked)")}">${__("Edit TRF")}</button>
								<button type="button" class="btn btn-xs btn-default ic-ts-trf-pdf" data-tr="${frappe.utils.escape_html(
									tr.name
								)}" data-trf="${frappe.utils.escape_html(tr.trf_name || "")}" data-pdf="${frappe.utils.escape_html(
									tr.trf_pdf_file || ""
								)}" title="${__("Download TRF PDF")}">${__("TRF PDF")}</button>
								<button type="button" class="btn btn-xs btn-default ic-ts-edit-price" data-tr="${frappe.utils.escape_html(
									tr.name
								)}" data-buy="${frappe.utils.escape_html(String(tr.library_buying_price ?? ""))}" data-sell="${frappe.utils.escape_html(
									String(tr.suggested_selling_price ?? "")
								)}" data-currency="${frappe.utils.escape_html(
									tr.price_currency || "INR"
								)}" title="${__("Edit buying / selling price")}">${__("Edit Price")}</button>
								<a class="btn btn-xs btn-default" href="/app/ic-testing-request/${encodeURIComponent(
									tr.name
								)}">${__("Open")}</a>
							</td>
						</tr>
						<tr class="ic-ts-tr-detail ${zebra}" data-tr="${frappe.utils.escape_html(tr.name)}" ${
					open ? "" : "hidden"
				}>
							<td colspan="9">
								<div class="ic-ts-detail-inner">
									<div class="ic-ts-samples-title">
										${__("Samples on this Testing Request")}
										<span class="ic-ts-samples-count">${samples.length}</span>
									</div>
									${sample_table}
								</div>
							</td>
						</tr>`;
			})
			.join("");

		const more_footer =
			remaining > 0
				? `<div class="ic-ts-show-more-bar">
					<span class="ic-ts-show-more-meta">${__("Showing {0} of {1} Testing Requests", [
						shown.length,
						total,
					])}</span>
					<button type="button" class="btn btn-sm btn-primary" id="ic-ts-show-more">
						${__("Show more Testing Requests")} (${remaining})
					</button>
				</div>`
				: total > page_size
					? `<div class="ic-ts-show-more-bar is-all">
						<span class="ic-ts-show-more-meta">${__("Showing all {0} Testing Requests", [total])}</span>
						<button type="button" class="btn btn-sm btn-default" id="ic-ts-show-less">${__(
							"Show less"
						)}</button>
					</div>`
					: `<div class="ic-ts-show-more-bar is-all">
						<span class="ic-ts-show-more-meta">${__("Showing {0} Testing Request(s)", [total])}</span>
					</div>`;

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
							<th style="width:320px">${__("Actions")}</th>
						</tr>
					</thead>
					<tbody class="ic-ts-manage-tbody">
						${body}
					</tbody>
				</table>
			</div>
			${more_footer}
		`);

		$board.find("#ic-ts-show-more").on("click", function () {
			state.manage_visible = (cint(state.manage_visible) || page_size) + page_size;
			render_manage(state.board_rows);
		});
		$board.find("#ic-ts-show-less").on("click", function () {
			state.manage_visible = page_size;
			render_manage(state.board_rows);
			const top = $board.offset();
			if (top) $("html, body").animate({ scrollTop: top.top - 72 }, 200);
		});
		$board.find(".ic-ts-expand-btn").on("click", function () {
			const name = $(this).data("tr");
			state.expanded[name] = !($(this).attr("aria-expanded") === "true");
			render_manage(state.board_rows);
		});
		$board.find(".ic-ts-tr-row").on("click", function (e) {
			if ($(e.target).closest("a,button,select").length) return;
			const name = $(this).data("tr");
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
		$board.find(".ic-ts-print-qr").on("click", function (e) {
			e.stopPropagation();
			const tr_name = $(this).data("tr");
			load_and_show_tr_qr(tr_name);
		});
		$board.find(".ic-ts-print-qr-direct").on("click", function (e) {
			e.stopPropagation();
			const tr_name = $(this).data("tr");
			frappe.call({
				method: "instacertify.testing.events.get_testing_request_sample_labels",
				args: { testing_request: tr_name },
				freeze: true,
				freeze_message: __("Preparing QR for print…"),
				callback(r) {
					const labels = (r.message && r.message.labels) || [];
					if (!labels.length) {
						frappe.msgprint({
							title: __("No sample QR"),
							message: __("No sample tracking numbers found for this Testing Request."),
							indicator: "orange",
						});
						return;
					}
					print_qr_labels(labels);
				},
			});
		});
		$board.find(".ic-ts-trf-link").on("click", function (e) {
			e.stopPropagation();
			const $btn = $(this);
			const tr_name = $btn.data("tr");
			const existing_url = $btn.data("url") || "";
			const existing_trf = $btn.data("trf") || "";
			const show_link = (x, refresh) => {
				const url = (x && (x.url || x.share_url)) || existing_url || "";
				const name = (x && x.name) || existing_trf || "";
				if (!url) {
					frappe.msgprint({
						title: __("TRF link"),
						message: __("Could not create a TRF share link."),
						indicator: "orange",
					});
					return;
				}
				frappe.msgprint({
					title: __("TRF customer fill link"),
					message: `<p><a href="${frappe.utils.escape_html(
						url
					)}" target="_blank" rel="noopener">${frappe.utils.escape_html(url)}</a></p>
					<p><button type="button" class="btn btn-xs btn-default" id="ic-ts-copy-trf-url">${__(
						"Copy link"
					)}</button>
					${
						name
							? ` <a class="btn btn-xs btn-primary" href="/app/ic-test-request-form/${encodeURIComponent(
									name
							  )}">${__("Open TRF")}</a>
							   <button type="button" class="btn btn-xs btn-default ic-ts-dlg-edit-trf" data-trf="${frappe.utils.escape_html(
									name
							  )}">${__("Edit TRF")}</button>`
							: ""
					}</p>`,
					indicator: "green",
				});
				setTimeout(() => {
					$("#ic-ts-copy-trf-url").on("click", () => {
						if (navigator.clipboard && navigator.clipboard.writeText) {
							navigator.clipboard.writeText(url).then(() => {
								frappe.show_alert({
									message: __("Link copied"),
									indicator: "green",
								});
							});
						} else {
							frappe.utils.copy_to_clipboard(url);
						}
					});
					$(".ic-ts-dlg-edit-trf").on("click", function () {
						open_edit_trf($(this).data("trf"));
					});
				}, 50);
				if (refresh) {
					state._keep_visible = true;
					refresh_manage();
				}
			};
			if (existing_url) {
				show_link({ url: existing_url, name: existing_trf }, false);
				return;
			}
			frappe.call({
				method: "instacertify.trf.api.create_or_get_trf",
				args: { testing_request: tr_name, share: 1 },
				freeze: true,
				freeze_message: __("Creating TRF share link…"),
				callback(r) {
					show_link(r.message || {}, true);
				},
			});
		});
		function open_edit_trf(trf_name, tr_name, status) {
			const go = (name) => {
				if (!name) {
					frappe.msgprint({
						title: __("Edit TRF"),
						message: __("No TRF found yet. Use TRF Link first."),
						indicator: "orange",
					});
					return;
				}
				frappe.set_route("Form", "IC Test Request Form", name);
			};
			if (!trf_name && tr_name) {
				frappe.call({
					method: "instacertify.trf.api.create_or_get_trf",
					args: { testing_request: tr_name, share: 0 },
					freeze: true,
					callback(r) {
						go((r.message || {}).name);
					},
				});
				return;
			}
			const locked = ["Submitted by Customer", "Under Review", "PDF Generated", "Completed"].includes(
				String(status || "")
			);
			if (trf_name && locked) {
				frappe.call({
					method: "instacertify.trf.api.reopen_trf_for_edit",
					args: { name: trf_name },
					freeze: true,
					callback() {
						frappe.show_alert({
							message: __("TRF reopened for edit"),
							indicator: "green",
						});
						state._keep_visible = true;
						refresh_manage();
						go(trf_name);
					},
				});
				return;
			}
			go(trf_name);
		}
		$board.find(".ic-ts-trf-edit").on("click", function (e) {
			e.stopPropagation();
			open_edit_trf($(this).data("trf"), $(this).data("tr"), $(this).data("status"));
		});
		$board.find(".ic-ts-edit-price").on("click", function (e) {
			e.stopPropagation();
			const tr_name = $(this).data("tr");
			const d = new frappe.ui.Dialog({
				title: __("Edit Price — {0}", [tr_name]),
				fields: [
					{
						fieldname: "library_buying_price",
						fieldtype: "Currency",
						label: __("Buying Price"),
						default: cint($(this).data("buy")) || flt($(this).data("buy")) || 0,
						options: "price_currency",
						reqd: 1,
					},
					{
						fieldname: "suggested_selling_price",
						fieldtype: "Currency",
						label: __("Selling Price"),
						default: flt($(this).data("sell")) || 0,
						options: "price_currency",
						reqd: 1,
					},
					{
						fieldname: "price_currency",
						fieldtype: "Link",
						options: "Currency",
						label: __("Currency"),
						default: $(this).data("currency") || "INR",
						reqd: 1,
					},
				],
				primary_action_label: __("Save Prices"),
				primary_action(values) {
					frappe.call({
						method: "instacertify.testing.events.update_testing_request_prices",
						args: {
							testing_request: tr_name,
							library_buying_price: values.library_buying_price,
							suggested_selling_price: values.suggested_selling_price,
							price_currency: values.price_currency,
						},
						freeze: true,
						callback() {
							d.hide();
							frappe.show_alert({
								message: __("Prices updated"),
								indicator: "green",
							});
							state._keep_visible = true;
							refresh_manage();
						},
					});
				},
			});
			d.show();
		});
		$board.find(".ic-ts-trf-pdf").on("click", function (e) {
			e.stopPropagation();
			const tr_name = $(this).data("tr");
			const trf_name = $(this).data("trf") || "";
			const pdf_url = $(this).data("pdf") || "";
			const open_pdf = (url) => {
				if (!url) {
					frappe.msgprint({
						title: __("TRF PDF"),
						message: __("PDF is not available yet. Fill the TRF first, then generate PDF."),
						indicator: "orange",
					});
					return;
				}
				window.open(url, "_blank");
			};
			if (pdf_url) {
				open_pdf(pdf_url);
				return;
			}
			const generate = (name) => {
				if (!name) {
					frappe.msgprint({
						title: __("TRF PDF"),
						message: __("Create a TRF link first, then fill the form before generating PDF."),
						indicator: "orange",
					});
					return;
				}
				frappe.call({
					method: "instacertify.trf.api.generate_trf_pdf",
					args: { name },
					freeze: true,
					freeze_message: __("Generating TRF PDF…"),
					callback(r) {
						const m = r.message || {};
						if (m.file_url) {
							frappe.show_alert({
								message: __("TRF PDF ready"),
								indicator: "green",
							});
							state._keep_visible = true;
							refresh_manage();
							open_pdf(m.file_url);
						} else {
							frappe.msgprint({
								title: __("TRF PDF"),
								message: __("Could not generate PDF."),
								indicator: "orange",
							});
						}
					},
				});
			};
			if (trf_name) {
				generate(trf_name);
				return;
			}
			frappe.call({
				method: "instacertify.trf.api.create_or_get_trf",
				args: { testing_request: tr_name, share: 0 },
				freeze: true,
				callback(r) {
					generate((r.message || {}).name || "");
				},
			});
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
				limit: 200,
			},
			callback(r) {
				state.board_rows = r.message || [];
				// Reset page window when filters refresh (keep size if already expanded mid-session)
				if (!state._keep_visible) {
					state.manage_visible = cint(state.manage_page_size) || 20;
				}
				state._keep_visible = false;
				// default expand rows that have samples so sample data shows in outlined tables
				state.board_rows.forEach((tr) => {
					if (state.expanded[tr.name] === undefined) {
						const has_samples = (tr.samples || []).length > 0;
						state.expanded[tr.name] =
							state.focus_tr === tr.name || has_samples;
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
	page.main.find("#ic-ts-buy-price, #ic-ts-sell-price, #ic-ts-price-currency").on("change input", function () {
		state.buy_price = flt(page.main.find("#ic-ts-buy-price").val());
		state.sell_price = flt(page.main.find("#ic-ts-sell-price").val());
		state.price_currency = (page.main.find("#ic-ts-price-currency").val() || "INR").trim() || "INR";
	});
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
