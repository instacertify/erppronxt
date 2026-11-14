/* Quotation list: keep New Quotation, and add View / PDF on each row. */
frappe.listview_settings["Quotation"] = frappe.listview_settings["Quotation"] || {};
frappe.listview_settings["Quotation"].button = {
	show() {
		return true;
	},
	get_label() {
		return __("View");
	},
	get_description(doc) {
		return __("View {0}", [doc.name]);
	},
	action(doc) {
		if (window.instacertify && instacertify.open_doc_preview) {
			instacertify.open_doc_preview("Quotation", doc.name);
		}
	},
};

(function () {
	const prev = frappe.listview_settings["Quotation"].onload;
	frappe.listview_settings["Quotation"].onload = function (listview) {
		if (typeof prev === "function") prev(listview);
		if (listview._ic_doc_actions) return;
		listview._ic_doc_actions = 1;
		const render = listview.render_list.bind(listview);
		listview.render_list = function () {
			const result = render();
			if (window.instacertify && instacertify.decorate_doc_list) {
				instacertify.decorate_doc_list(listview);
			}
			return result;
		};
		if (window.instacertify && instacertify.decorate_doc_list) {
			instacertify.decorate_doc_list(listview);
		}
	};
})();
