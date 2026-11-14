/* Lead list: quick capture and clear columns (source, product / service, phone).
   The slim filter row comes from instacertify.LIST_KEEP_FILTERS. */
(function () {
	const base = frappe.listview_settings["Lead"] || {};
	const prev_onload = base.onload;
	const prev_formatters = base.formatters || {};

	const COLUMNS = [
		["ic_lead_source_detail", __("Source")],
		["ic_project_type", __("Product / service")],
		["mobile_no", __("Phone")],
		["ic_next_contact_date", __("Next contact")],
	];

	/* Click a pill to show only leads with that source / product. */
	function pill(fieldname, value, kind, empty) {
		if (!value) {
			return `<span class="ic-lead-pill ic-lead-pill-empty">${empty}</span>`;
		}
		const safe = frappe.utils.escape_html(value);
		return `<span class="ic-lead-pill ic-lead-pill-${kind} ic-lead-pill-pick" data-ic-field="${fieldname}" data-ic-value="${safe}" title="${__(
			"Show only {0}",
			[safe]
		)}">${safe}</span>`;
	}

	/* Frappe's own ".filterable" click removes the filter and adds it again; when the list
	   was already filtered by that value the two steps raced and the filter was lost. */
	function pick(listview, fieldname, value) {
		const control = listview.page.fields_dict && listview.page.fields_dict[fieldname];
		if (control && control.get_value && control.get_value() === value) return;
		listview.filter_area.add([[listview.doctype, fieldname, "=", value]]);
	}

	function lead_columns(listview) {
		const kept = (listview.columns || []).filter((col) => ["Subject", "Tag", "Status"].includes(col.type));
		if (!kept.some((col) => col.type === "Status")) {
			kept.push({ type: "Status" });
		}
		COLUMNS.forEach(([fieldname, label]) => {
			const meta_df = frappe.meta.get_docfield("Lead", fieldname);
			if (!meta_df) return;
			kept.push({ type: "Field", df: Object.assign({}, meta_df, { label, in_list_view: 1 }) });
		});
		return kept;
	}

	frappe.listview_settings["Lead"] = Object.assign({}, base, {
		hide_name_column: true,
		add_fields: [
			"ic_lead_source_detail",
			"ic_project_type",
			"ic_request_category",
			"ic_next_contact_date",
			"mobile_no",
			"email_id",
			"ic_call_remarks",
			"status",
		],
		formatters: Object.assign({}, prev_formatters, {
			ic_lead_source_detail(value) {
				return pill("ic_lead_source_detail", value, "source", __("No source"));
			},
			ic_project_type(value) {
				return pill("ic_project_type", value, "service", __("No service"));
			},
		}),
		/* "Add Lead" opens the short capture box. The full form stays one click away. */
		primary_action() {
			if (window.instacertify && instacertify.open_quick_lead) {
				instacertify.open_quick_lead({
					on_done() {
						if (window.cur_list && cur_list.doctype === "Lead") cur_list.refresh();
					},
				});
			} else {
				frappe.new_doc("Lead");
			}
		},
		onload(listview) {
			if (typeof prev_onload === "function") prev_onload(listview);
			if (listview.page && listview.page.wrapper) {
				listview.page.wrapper.addClass("ic-lead-list-page");
			}

			if (!listview._ic_lead_columns) {
				listview._ic_lead_columns = 1;
				const setup_columns = listview.setup_columns.bind(listview);
				listview.setup_columns = function () {
					setup_columns();
					listview.columns = lead_columns(listview);
				};
				listview.columns = lead_columns(listview);
				if (listview.render_header) listview.render_header(true);
			}

			if (!listview._ic_lead_pick) {
				listview._ic_lead_pick = 1;
				listview.$result.on("click", ".ic-lead-pill-pick", (e) => {
					if (e.metaKey || e.ctrlKey) return;
					e.preventDefault();
					e.stopPropagation();
					const el = e.currentTarget;
					pick(listview, el.getAttribute("data-ic-field"), el.getAttribute("data-ic-value"));
				});
			}

			listview.page.add_inner_button(__("Full form"), () => frappe.new_doc("Lead"));
		},
	});
})();
