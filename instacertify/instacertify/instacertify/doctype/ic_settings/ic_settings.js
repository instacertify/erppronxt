// Copyright (c) Instacertify
frappe.ui.form.on("IC Settings", {
	refresh(frm) {
		if (!frappe.user.has_role("System Manager") && !frappe.user.has_role("IC Admin")) return;
		frm.add_custom_button(__("Configure SMTP"), () => {
			if (instacertify.open_smtp_setup) instacertify.open_smtp_setup();
		});
	}
});
