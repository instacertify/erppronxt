// Instacertify — zippy Quick Lead on Lead list (loads with list view assets)
(function () {
	const base = frappe.listview_settings["Lead"] || {};
	const prev_onload = base.onload;
	frappe.listview_settings["Lead"] = Object.assign({}, base, {
		onload(listview) {
			if (typeof prev_onload === "function") {
				prev_onload(listview);
			}
			if (typeof instacertify !== "undefined" && instacertify.enable_full_width_desk) {
				instacertify.enable_full_width_desk();
			}
			if (listview.page && listview.page.wrapper) {
				listview.page.wrapper.addClass("ic-lead-list-page");
			}
			listview.page.set_primary_action(
				__("Quick Lead"),
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
		},
	});
})();
