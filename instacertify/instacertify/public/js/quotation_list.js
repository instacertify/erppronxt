/* Quotation list: view and download icons on each row (drawn by instacertify.decorate_doc_list). */
(function () {
	const settings = (frappe.listview_settings["Quotation"] = frappe.listview_settings["Quotation"] || {});
	delete settings.button;
	const prev = settings.onload;
	settings.onload = function (listview) {
		if (typeof prev === "function") prev(listview);
		if (window.instacertify && instacertify.patch_list_view) instacertify.patch_list_view();
		if (window.instacertify && instacertify.add_list_excel_button) instacertify.add_list_excel_button(listview);
		// Company repeats on every row; it stays available under "More filters".
		if (!listview._ic_quote_columns) {
			listview._ic_quote_columns = 1;
			const trim = () => {
				listview.columns = (listview.columns || []).filter(
					(col) => !(col.df && col.df.fieldname === "company")
				);
			};
			const setup_columns = listview.setup_columns.bind(listview);
			listview.setup_columns = function () {
				setup_columns();
				trim();
			};
			trim();
			if (listview.render_header) listview.render_header(true);
		}
	};
})();
