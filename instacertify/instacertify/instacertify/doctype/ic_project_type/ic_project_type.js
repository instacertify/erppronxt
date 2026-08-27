// Copyright (c) Instacertify
frappe.ui.form.on("IC Project Type", {
	refresh(frm) {
		frm.set_intro(
			__("Add or remove project types here (BIS, Testing, EPR, …). Active types appear on Lead capture."),
			"blue"
		);
	},
});
