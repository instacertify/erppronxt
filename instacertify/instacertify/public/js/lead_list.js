/* Lead list: quick capture, source chips, and product/service on every row. */
(function () {
	const base = frappe.listview_settings["Lead"] || {};
	const prev_onload = base.onload;
	const prev_formatters = base.formatters || {};

	function pill(value, kind, empty) {
		if (!value) {
			return `<span class="ic-lead-pill ic-lead-pill-empty">${empty}</span>`;
		}
		return `<span class="ic-lead-pill ic-lead-pill-${kind}">${frappe.utils.escape_html(value)}</span>`;
	}

	function set_lead_filter(listview, fieldname, value) {
		const current = (listview.filter_area && listview.filter_area.get()) || [];
		const kept = current.filter((row) => row[1] !== fieldname);
		if (value) kept.push(["Lead", fieldname, "=", value]);
		listview.filter_area.clear(false);
		if (kept.length) listview.filter_area.add(kept);
		else listview.refresh();
	}

	function chip_bar(listview, fieldname, choices, all_label) {
		const bar = document.createElement("div");
		bar.className = "ic-lead-filter-bar";
		bar.dataset.field = fieldname;
		choices.forEach((choice) => {
			const btn = document.createElement("button");
			btn.type = "button";
			btn.className = "ic-lead-filter-chip" + (choice ? "" : " is-on");
			btn.textContent = choice || all_label;
			btn.addEventListener("click", () => {
				bar.querySelectorAll(".ic-lead-filter-chip").forEach((el) => el.classList.remove("is-on"));
				btn.classList.add("is-on");
				set_lead_filter(listview, fieldname, choice);
			});
			bar.appendChild(btn);
		});
		return bar;
	}

	function ensure_columns(listview) {
		const want = [
			["ic_lead_source_detail", __("Source")],
			["ic_project_type", __("Product / service")],
			["mobile_no", __("Phone")],
		];
		const have = new Set((listview.columns || []).map((col) => col.df && col.df.fieldname));
		let added = false;
		want.forEach(([fieldname, label]) => {
			if (have.has(fieldname)) return;
			const df = frappe.meta.get_docfield("Lead", fieldname) || {
				fieldname,
				label,
				fieldtype: "Data",
			};
			df.in_list_view = 1;
			df.label = label;
			const name_at = (listview.columns || []).findIndex(
				(col) => col.type === "Field" && col.df && col.df.fieldname === "name"
			);
			const column = { type: "Field", df };
			if (name_at > 0) listview.columns.splice(name_at, 0, column);
			else listview.columns.push(column);
			added = true;
		});
		if (added && listview.render_header) listview.render_header(true);
	}

	frappe.listview_settings["Lead"] = Object.assign({}, base, {
		add_fields: ["ic_lead_source_detail", "ic_project_type", "ic_request_category", "mobile_no", "email_id", "ic_call_remarks", "status"],
		formatters: Object.assign({}, prev_formatters, {
			ic_lead_source_detail(value) {
				return pill(value, "source", __("No source"));
			},
			ic_project_type(value) {
				return pill(value, "service", __("No service"));
			},
		}),
		onload(listview) {
			if (typeof prev_onload === "function") prev_onload(listview);
			if (typeof instacertify !== "undefined" && instacertify.enable_full_width_desk) {
				instacertify.enable_full_width_desk();
			}
			if (listview.page && listview.page.wrapper) {
				listview.page.wrapper.addClass("ic-lead-list-page");
			}
			ensure_columns(listview);
			listview.page.set_primary_action(
				__("New lead"),
				() => {
					if (window.instacertify && instacertify.open_quick_lead) {
						instacertify.open_quick_lead({
							on_done() {
								listview.refresh();
							},
						});
					} else {
						frappe.new_doc("Lead");
					}
				},
				"add"
			);
			listview.page.add_inner_button(__("Full form"), () => frappe.new_doc("Lead"));

			const host = listview.$result && listview.$result.parent();
			if (host && host.length) {
				host.find(".ic-lead-filter-bars").remove();
				const wrap = document.createElement("div");
				wrap.className = "ic-lead-filter-bars";
				wrap.appendChild(
					chip_bar(
						listview,
						"ic_lead_source_detail",
						["", "Website", "Google Search", "Google Ads", "IndiaMART", "Direct Call", "Reference", "Consultant"],
						__("All sources")
					)
				);
				wrap.appendChild(
					chip_bar(
						listview,
						"ic_project_type",
						["", "BIS", "Testing", "Certification", "Consulting", "EPR", "MSDS Authoring", "LMPC"],
						__("All products / services")
					)
				);
				listview.$result.before(wrap);
			}
		},
	});
})();
