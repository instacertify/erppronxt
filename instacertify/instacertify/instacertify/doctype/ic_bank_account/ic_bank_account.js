// Copyright (c) Instacertify
frappe.ui.form.on("IC Bank Account", {
	refresh(frm) {
		frm.set_intro(
			__(
				"Bank accounts listed here appear in the Quotation Bank selector. Print/PDF uses the account chosen on each quote."
			),
			"blue"
		);
	},
});
