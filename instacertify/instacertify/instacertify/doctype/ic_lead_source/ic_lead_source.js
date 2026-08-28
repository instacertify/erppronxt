// Copyright (c) Instacertify
frappe.ui.form.on("IC Lead Source", {
	refresh(frm) {
		frm.set_intro(
			__("Add or disable lead sources here. Active sources appear on Lead capture."),
			"blue"
		);
	},
});
