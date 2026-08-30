// Copyright (c) Instacertify
frappe.ui.form.on("IC Laboratory", {
	refresh(frm) {
		// Keep contact + accreditation + scope table editable
		[
			"contact_person",
			"contact_designation",
			"phone",
			"email",
			"address",
			"accreditation_details",
			"accreditation_scope",
			"scope_sheet",
			"accreditation_certificate",
			"accreditation_scope_pdf",
			"test_scopes",
		].forEach((f) => {
			if (frm.fields_dict[f]) {
				frm.set_df_property(f, "read_only", 0);
				frm.set_df_property(f, "hidden", 0);
			}
		});
	},
});
