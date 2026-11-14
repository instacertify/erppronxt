/* Sales Invoice list: view and download icons on each row (drawn by instacertify.decorate_doc_list). */
(function () {
	const settings = (frappe.listview_settings["Sales Invoice"] = frappe.listview_settings["Sales Invoice"] || {});
	const prev = settings.onload;
	settings.onload = function (listview) {
		if (typeof prev === "function") prev.call(this, listview);
		if (window.instacertify && instacertify.patch_list_view) instacertify.patch_list_view();
	};
})();
