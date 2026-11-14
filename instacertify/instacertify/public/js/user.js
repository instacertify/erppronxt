/* User create + password reset: type a password. Email is not required. */
frappe.ui.form.on("User", {
	refresh(frm) {
		if (frm.is_new()) {
			if (!frm._ic_password_ready && cint(frm.doc.send_welcome_email) && !frm.doc.new_password) {
				frm._ic_password_ready = 1;
				frm.set_value("send_welcome_email", 0);
			}
			ic_show_password_fields(frm);
			frm.set_intro(
				__(
					"Enter a password and save. No email is sent. The email field is only the login ID."
				),
				"blue"
			);
			frm.set_df_property(
				"new_password",
				"description",
				__("Login password. Saving does not send an email.")
			);
			frm.set_df_property(
				"send_welcome_email",
				"description",
				__("Leave this off when you set a password.")
			);
			return;
		}
		if (
			["Administrator", "Guest"].includes(frm.doc.name) ||
			!frm.has_perm("write") ||
			!cint(frm.doc.enabled)
		) {
			return;
		}
		frm.remove_custom_button(__("Reset Password"), __("Password"));
		frm.remove_custom_button(__("Change Password"), __("Password"));
		frm.remove_custom_button(__("Set Password"), __("Password"));
		frm.add_custom_button(__("Change Password"), () => ic_set_password_dialog(frm), __("Password"));
	},

	new_password(frm) {
		if (frm.doc.new_password) {
			frm.set_value("send_welcome_email", 0);
		}
	},

	validate(frm) {
		if (frm.is_new() && !frm.doc.new_password && !cint(frm.doc.send_welcome_email)) {
			frappe.msgprint(__("Enter a password. No email will be sent."));
			frappe.validated = false;
		}
	},
});

function ic_show_password_fields(frm) {
	["change_password", "new_password", "logout_all_sessions"].forEach((fieldname) => {
		if (frm.fields_dict[fieldname]) {
			frm.set_df_property(fieldname, "hidden", 0);
			frm.toggle_display(fieldname, true);
		}
	});
}

function ic_set_password_dialog(frm) {
	if (window.instacertify && instacertify.open_change_password) {
		instacertify.open_change_password(frm.doc.name);
	}
}
