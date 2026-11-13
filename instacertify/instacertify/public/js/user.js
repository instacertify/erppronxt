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
		frm.add_custom_button(__("Set Password"), () => ic_set_password_dialog(frm), __("Password"));
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
	const d = new frappe.ui.Dialog({
		title: __("Set Password"),
		fields: [
			{
				fieldname: "help",
				fieldtype: "HTML",
				options: `<p class="text-muted">${__(
					"Sets the password now. No email is sent."
				)}</p>`,
			},
			{
				fieldname: "new_password",
				fieldtype: "Password",
				label: __("New Password"),
				reqd: 1,
			},
			{
				fieldname: "confirm_password",
				fieldtype: "Password",
				label: __("Confirm Password"),
				reqd: 1,
			},
		],
		primary_action_label: __("Set Password"),
		primary_action(values) {
			if (values.new_password !== values.confirm_password) {
				frappe.msgprint(__("Passwords do not match."));
				return;
			}
			const logout = frm.doc.name === frappe.session.user ? 0 : 1;
			frappe.call({
				method: "frappe.core.doctype.user.user.change_password",
				args: {
					user: frm.doc.name,
					new_password: values.new_password,
					logout_all_sessions: logout,
				},
				freeze: true,
				freeze_message: __("Setting password…"),
				callback() {
					d.hide();
					frappe.show_alert({
						message: __("Password set. No email was sent."),
						indicator: "green",
					});
				},
			});
		},
	});
	d.show();
}
