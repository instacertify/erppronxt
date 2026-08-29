# Copyright (c) Instacertify
frappe.ui.form.on("IC Quotation Cost Item", {
	form_render(frm, cdt, cdn) {
		const grid_row = frm.open_grid_row && frm.open_grid_row();
		if (!grid_row) return;
		const field = grid_row.get_field("cost_component");
		if (field && field.$input) {
			field.$input.attr(
				"placeholder",
				__("e.g. Consulting Charges, BIS Fee, Lab Testing…")
			);
		}
		const particulars = grid_row.get_field("particulars");
		if (particulars && particulars.$input) {
			particulars.$input.attr(
				"placeholder",
				__("Printed line name — change freely")
			);
		}
	},
	cost_component(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.cost_component && !row.particulars) {
			frappe.model.set_value(cdt, cdn, "particulars", row.cost_component);
		}
	},
	particulars(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.particulars && !row.cost_component) {
			frappe.model.set_value(cdt, cdn, "cost_component", row.particulars);
		}
	},
	payment_destination(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		const dest = row.payment_destination || "";
		const passthrough = [
			"Payable Directly to Government",
			"Payable Directly to Laboratory",
			"Payable to Third Party",
		].includes(dest);
		frappe.model.set_value(cdt, cdn, "is_passthrough", passthrough ? 1 : 0);
	},
});
