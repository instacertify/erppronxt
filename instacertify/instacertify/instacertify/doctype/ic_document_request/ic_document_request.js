// Copyright (c) Instacertify
frappe.ui.form.on("IC Document Request", {
	refresh(frm) {
		frm.add_custom_button(__("Open Library"), () => {
			frappe.set_route("document-collection-library");
		});
	},
});
