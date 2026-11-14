/* Sales Invoice list: view the print or download the PDF from the row. */
frappe.listview_settings["Sales Invoice"] = frappe.listview_settings["Sales Invoice"] || {};

frappe.listview_settings["Sales Invoice"].onload = function (listview) {
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
