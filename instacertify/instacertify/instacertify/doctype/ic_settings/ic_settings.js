// Copyright (c) Instacertify
frappe.ui.form.on("IC Settings", {
	refresh(frm) {
		if (!frappe.user.has_role("System Manager") && !frappe.user.has_role("IC Admin")) return;
		frm.add_custom_button(__("Sync website leads"), () => {
			frappe.call({
				method: "instacertify.crm.website_leads.sync_website_leads",
				args: { full: 1 },
				freeze: true,
				freeze_message: __("Importing website enquiries…"),
				callback(r) {
					const m = r.message || {};
					if (!m.ok) {
						frappe.msgprint(m.error || __("Website lead sync failed."));
						return;
					}
					frappe.show_alert({
						message: __("Created {0}, updated {1}", [m.created || 0, m.updated || 0]),
						indicator: "green",
					});
					frm.reload_doc();
				},
			});
		});
	}
});
