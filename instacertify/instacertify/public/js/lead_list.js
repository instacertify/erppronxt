// Instacertify — zippy Quick Lead on Lead list (loads with list view assets)
(function () {
	const base = frappe.listview_settings["Lead"] || {};
	const prev_onload = base.onload;
	frappe.listview_settings["Lead"] = Object.assign({}, base, {
		onload(listview) {
			if (typeof prev_onload === "function") {
				prev_onload(listview);
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
