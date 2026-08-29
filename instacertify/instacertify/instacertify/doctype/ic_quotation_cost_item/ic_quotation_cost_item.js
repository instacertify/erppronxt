// Copyright (c) Instacertify
/** Cost lines: free-text names + Counted Revenue vs Do Not Count as Revenue. */

function sync_revenue_from_treatment(cdt, cdn) {
	const row = locals[cdt][cdn];
	const treatment = row.revenue_treatment || "Counted Revenue";
	const is_pass = treatment === "Do Not Count as Revenue" ? 1 : 0;
	frappe.model.set_value(cdt, cdn, "is_passthrough", is_pass);
}

function sync_treatment_from_passthrough(cdt, cdn) {
	const row = locals[cdt][cdn];
	const treatment = cint(row.is_passthrough)
		? "Do Not Count as Revenue"
		: "Counted Revenue";
	if (row.revenue_treatment !== treatment) {
		frappe.model.set_value(cdt, cdn, "revenue_treatment", treatment);
	}
}

function sync_from_destination(cdt, cdn) {
	const row = locals[cdt][cdn];
	const dest = row.payment_destination || "";
	const pass_dest = [
		"Payable Directly to Government",
		"Payable Directly to Laboratory",
		"Payable to Third Party",
	];
	if (pass_dest.includes(dest)) {
		frappe.model.set_value(cdt, cdn, "revenue_treatment", "Do Not Count as Revenue");
	} else if (dest === "Payable to Instacertify") {
		frappe.model.set_value(cdt, cdn, "revenue_treatment", "Counted Revenue");
	}
}

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
	revenue_treatment(frm, cdt, cdn) {
		sync_revenue_from_treatment(cdt, cdn);
	},
	is_passthrough(frm, cdt, cdn) {
		sync_treatment_from_passthrough(cdt, cdn);
	},
	payment_destination(frm, cdt, cdn) {
		sync_from_destination(cdt, cdn);
	},
	cost_component(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.cost_component && !row.particulars) {
			frappe.model.set_value(cdt, cdn, "particulars", row.cost_component);
		}
		if (
			["Government Fees", "Certification Authority Fees", "Laboratory Charges"].includes(
				row.cost_component
			) &&
			(!row.revenue_treatment || row.revenue_treatment === "Counted Revenue")
		) {
			const dest =
				row.cost_component === "Laboratory Charges"
					? "Payable Directly to Laboratory"
					: "Payable Directly to Government";
			frappe.model.set_value(cdt, cdn, "payment_destination", dest);
		}
	},
	particulars(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.particulars && !row.cost_component) {
			frappe.model.set_value(cdt, cdn, "cost_component", row.particulars);
		}
	},
});
