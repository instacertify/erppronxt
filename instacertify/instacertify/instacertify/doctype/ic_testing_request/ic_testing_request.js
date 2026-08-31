// Copyright (c) Instacertify
frappe.ui.form.on("IC Testing Request", {
	refresh(frm) {
		if (window.instacertify && typeof instacertify.ensure_form_save_button === "function") {
			instacertify.ensure_form_save_button(frm);
		}
	},
	onload_post_render(frm) {
		if (window.instacertify && typeof instacertify.ensure_form_save_button === "function") {
			instacertify.ensure_form_save_button(frm);
		}
	},
});
