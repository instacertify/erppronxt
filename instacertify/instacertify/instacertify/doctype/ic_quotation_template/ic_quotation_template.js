# Copyright (c) Instacertify
frappe.ui.form.on("IC Quotation Template", {
	refresh(frm) {
		frm.set_intro(
			__(
				"Fully editable quote format — rename print headings, edit narrative text, and set every price line. Active templates appear when creating a Quotation of the same category."
			),
			"blue"
		);

		_render_edit_guide(frm);
		_toggle_sections(frm);

		frm.add_custom_button(__("Upload Quote Format"), () => {
			instacertify.open_quote_format_upload({
				template_name: frm.doc.template_name,
				quotation_type: frm.doc.quotation_type,
				on_done(name) {
					if (name === frm.doc.name) frm.reload_doc();
					else frappe.set_route("Form", "IC Quotation Template", name);
				},
			});
		}, __("Library"));

		frm.add_custom_button(__("Quote Format Library"), () => {
			frappe.set_route("quote-format-library");
		}, __("Library"));

		if (!frm.is_new()) {
			frm.add_custom_button(__("Duplicate Template"), () => {
				frappe.prompt(
					[
						{
							fieldname: "template_name",
							fieldtype: "Data",
							label: "New Template Name",
							reqd: 1,
							default: (frm.doc.template_name || "") + " Copy",
						},
					],
					(values) => {
						frappe.call({
							method: "instacertify.quotation.events.duplicate_quotation_template",
							args: {
								template: frm.doc.name,
								new_name: values.template_name,
							},
							freeze: true,
							callback(r) {
								frappe.set_route("Form", "IC Quotation Template", r.message.template);
							},
						});
					},
					__("Duplicate Quotation Template"),
					__("Create")
				);
			}, __("Actions"));

			frm.add_custom_button(__("New Quotation from Template"), () => {
				frappe.new_doc("Quotation", {
					ic_quotation_type:
						frm.doc.quotation_type === "Service" ? "Consulting" : frm.doc.quotation_type,
					ic_quotation_template: frm.doc.name,
					ic_service_family: frm.doc.service_family,
				});
			}, __("Actions"));

			frm.add_custom_button(__("Jump to Pricing"), () => {
				frm.scroll_to_field("cost_items");
			});

			frm.add_custom_button(__("Jump to Headings"), () => {
				frm.scroll_to_field("label_about");
			});
		}
	},

	quotation_type(frm) {
		_toggle_sections(frm);
		_render_edit_guide(frm);
	},
});

function _toggle_sections(frm) {
	const consulting = ["Consulting", "Renewal", "Other", "Service"].includes(frm.doc.quotation_type);
	const testing =
		frm.doc.quotation_type === "Testing"
		|| frm.doc.quotation_type === "Multiple Products / Multiple Services";
	frm.toggle_display("section_service", consulting);
	frm.toggle_display("section_consulting_narrative", consulting);
	frm.toggle_display("section_scope", consulting);
	frm.toggle_display("section_testing_narrative", testing);
	frm.toggle_display("section_testing", testing);
	frm.toggle_display("section_cost", true);
	frm.toggle_display("section_policies", true);
}

function _render_edit_guide(frm) {
	const wrap = frm.fields_dict.edit_guide_html;
	if (!wrap || !wrap.$wrapper) return;
	const qtype = frm.doc.quotation_type || "Consulting";
	wrap.$wrapper.html(`
		<div class="ic-tmpl-edit-guide" style="
			border:1px solid var(--border-color,#d1d8dd);
			background:var(--control-bg,#f8f9fa);
			border-radius:6px;padding:12px 14px;margin:4px 0 10px;
			font-size:13px;line-height:1.45;">
			<div style="font-weight:600;margin-bottom:6px;">${__("What you can edit on this template")}</div>
			<ul style="margin:0 0 0 18px;padding:0;">
				<li><b>${__("Section 2 — Rename headings")}</b>: ${__("Change printed names (ABOUT, Commercials, Payment Terms, column titles).")}</li>
				<li><b>${__("Narrative sections")}</b>: ${__("Edit all body text for {0} quotes.", [__(qtype)])}</li>
				<li><b>${__("Section 6 — Pricing")}</b>: ${__("Add/remove lines, rename each line, set amounts or free-text charges, mark revenue vs pass-through.")}</li>
				<li><b>${__("Policies")}</b>: ${__("Payment terms, cancellation, confidentiality, T&Cs.")}</li>
			</ul>
			<div style="margin-top:8px;color:var(--text-muted,#6c7680);">
				${__("After Save, use this template when creating a Quotation — all values stay editable on the quote too.")}
			</div>
		</div>
	`);
}
