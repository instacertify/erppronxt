// Copyright (c) Instacertify
/** Cost lines: numeric or Custom Value text; Do Not Sum; Counted Revenue vs pass-through. */

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

function recalc_cost_line_total(cdt, cdn) {
	const row = locals[cdt][cdn];
	if (!row) return;
	let qty = cint(row.qty);
	if (!qty || qty < 1) {
		qty = 1;
		frappe.model.set_value(cdt, cdn, "qty", 1);
	}
	const unit = flt(row.amount);
	frappe.model.set_value(cdt, cdn, "total_amount", unit * qty);
}

function maybe_default_exclude_for_custom(cdt, cdn) {
	const row = locals[cdt][cdn];
	if (!row) return;
	const custom = (row.charges_display || "").trim();
	if (custom && flt(row.amount) === 0 && !cint(row.exclude_from_total)) {
		frappe.model.set_value(cdt, cdn, "exclude_from_total", 1);
	}
}

function refresh_parent_cost_totals(frm) {
	if (!frm) return;
	if (window.instacertify && typeof instacertify.refresh_quotation_cost_totals === "function") {
		instacertify.refresh_quotation_cost_totals(frm);
	} else if (frm.doc && frm.fields_dict.ic_total_quoted_value) {
		frm.refresh_field("ic_cost_items");
	}
}

frappe.ui.form.on("IC Quotation Cost Item", {
	form_render(frm, cdt, cdn) {
		const grid = frm.fields_dict.ic_cost_items && frm.fields_dict.ic_cost_items.grid;
		if (grid) {
			grid.update_docfield_property("amount", "read_only", 0);
			grid.update_docfield_property("qty", "read_only", 0);
			grid.update_docfield_property("charges_display", "hidden", 0);
			grid.update_docfield_property("charges_display", "in_list_view", 1);
			grid.update_docfield_property("exclude_from_total", "hidden", 0);
			grid.update_docfield_property("exclude_from_total", "in_list_view", 1);
			grid.update_docfield_property("line_label", "hidden", 0);
			grid.update_docfield_property("line_label", "in_list_view", 1);
			grid.update_docfield_property("currency", "hidden", 0);
			grid.update_docfield_property("currency", "in_list_view", 1);
		}
		const row = locals[cdt][cdn];
		if (row && !cint(row.qty)) {
			frappe.model.set_value(cdt, cdn, "qty", 1);
		}
		if (row && !(row.currency || "").trim() && frm.doc.currency) {
			frappe.model.set_value(cdt, cdn, "currency", frm.doc.currency);
		}
		recalc_cost_line_total(cdt, cdn);
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
		const custom = grid_row.get_field("charges_display");
		if (custom && custom.$input) {
			custom.$input.attr(
				"placeholder",
				__("At actuals / Included / TBD / any text")
			);
		}
		const lineRef = grid_row.get_field("line_label");
		if (lineRef && lineRef.$input) {
			lineRef.$input.attr("placeholder", __("A, B, C…"));
		}
	},
	amount(frm, cdt, cdn) {
		recalc_cost_line_total(cdt, cdn);
		refresh_parent_cost_totals(frm);
	},
	qty(frm, cdt, cdn) {
		recalc_cost_line_total(cdt, cdn);
		refresh_parent_cost_totals(frm);
	},
	charges_display(frm, cdt, cdn) {
		maybe_default_exclude_for_custom(cdt, cdn);
		refresh_parent_cost_totals(frm);
	},
	exclude_from_total(frm) {
		refresh_parent_cost_totals(frm);
	},
	currency(frm) {
		if (frm && window.instacertify && instacertify.render_customer_currency_banner) {
			instacertify.render_customer_currency_banner(frm);
		}
	},
	revenue_treatment(frm, cdt, cdn) {
		sync_revenue_from_treatment(cdt, cdn);
		refresh_parent_cost_totals(frm);
	},
	is_passthrough(frm, cdt, cdn) {
		sync_treatment_from_passthrough(cdt, cdn);
		refresh_parent_cost_totals(frm);
	},
	payment_destination(frm, cdt, cdn) {
		sync_from_destination(cdt, cdn);
		refresh_parent_cost_totals(frm);
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
