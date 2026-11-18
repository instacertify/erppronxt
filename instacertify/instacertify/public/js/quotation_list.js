/* Quotation list: aligned columns, color by status and type. */
(function () {
	const settings = (frappe.listview_settings["Quotation"] = frappe.listview_settings["Quotation"] || {});
	delete settings.button;
	const prev = settings.onload;
	const TYPE_CLASS = {
		Consulting: "cat-consulting",
		Testing: "cat-testing",
		Renewal: "cat-renewal",
		Service: "cat-consulting",
		Other: "cat-other",
		"Multiple Products / Multiple Services": "cat-testing",
	};
	function quote_columns(listview) {
		const kept = (listview.columns || []).filter((col) => ["Subject", "Status"].includes(col.type));
		if (!kept.some((col) => col.type === "Status")) kept.push({ type: "Status" });
		[
			["customer_name", __("Customer")],
			["transaction_date", __("Date")],
			["ic_quotation_type", __("Type")],
			["currency", __("Currency")],
			["grand_total", __("Total")],
		].forEach(([fieldname, label]) => {
			const meta_df = frappe.meta.get_docfield("Quotation", fieldname);
			if (!meta_df) return;
			kept.push({ type: "Field", df: Object.assign({}, meta_df, { label, in_list_view: 1 }) });
		});
		return kept;
	}
	settings.add_fields = ["customer_name", "transaction_date", "ic_quotation_type", "currency", "grand_total", "status"];
	settings.formatters = Object.assign({}, settings.formatters || {}, {
		ic_quotation_type(value) {
			const text = (value || "").trim() || __("Not set");
			const kind = TYPE_CLASS[value] || "cat-other";
			return `<span class="ic-type-pill ${kind}">${frappe.utils.escape_html(text)}</span>`;
		},
	});
	settings.get_indicator = function (doc) {
		const status = doc.status || "Draft";
		const colors = {
			Draft: "gray",
			Open: "blue",
			Replied: "orange",
			Ordered: "green",
			Lost: "red",
			Expired: "red",
			Cancelled: "red",
		};
		return [__(status), colors[status] || "gray", "status,=," + status];
	};
	settings.onload = function (listview) {
		if (typeof prev === "function") prev(listview);
		if (window.instacertify && instacertify.patch_list_view) instacertify.patch_list_view();
		if (window.instacertify && instacertify.add_list_excel_button) instacertify.add_list_excel_button(listview);
		// Company repeats on every row; it stays available under "More filters".
		if (!listview._ic_quote_columns) {
			listview._ic_quote_columns = 1;
			const apply = () => {
				listview.columns = quote_columns(listview);
			};
			const setup_columns = listview.setup_columns.bind(listview);
			listview.setup_columns = function () {
				setup_columns();
				apply();
			};
			apply();
			if (listview.render_header) listview.render_header(true);
			if (listview.render_list) listview.render_list();
		}
	};
})();
