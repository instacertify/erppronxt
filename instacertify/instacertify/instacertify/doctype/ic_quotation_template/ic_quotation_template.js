// Copyright (c) Instacertify
frappe.ui.form.on("IC Quotation Template", {
	refresh(frm) {
		frm.set_intro(
			__(
				"Fully editable quote format — rename with Display Name (keeps system Template ID stable). Edit print headings, narrative text, and price lines. Use Print / PDF to test after Save."
			),
			"blue"
		);

		_render_edit_guide(frm);
		_toggle_sections(frm);
		_lock_template_id(frm);
		_unlock_template_content_fields(frm);
		if (frm.fields_dict.bank_account) {
			frm.set_query("bank_account", () => ({ filters: { is_active: 1 } }));
			frm.set_df_property(
				"bank_account",
				"description",
				__(
					"Select which bank account prints on quotes from this format. Account number, IFSC, and UPI come from IC Bank Account and are not edited here."
				)
			);
		}

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
			frm.add_custom_button(__("Rename Display Name"), () => {
				frappe.prompt(
					[
						{
							fieldname: "display_name",
							fieldtype: "Data",
							label: __("Display Name"),
							reqd: 1,
							default: frm.doc.display_name || frm.doc.template_name || "",
						},
					],
					(values) => {
						frappe.call({
							method: "instacertify.quotation.events.rename_quotation_template_display_name",
							args: {
								template: frm.doc.name,
								display_name: values.display_name,
							},
							freeze: true,
							callback() {
								frm.reload_doc();
								frappe.show_alert({
									message: __("Display name updated (Template ID unchanged)"),
									indicator: "green",
								});
							},
						});
					},
					__("Rename Template"),
					__("Save")
				);
			}, __("Actions"));

			frm.add_custom_button(__("Duplicate Template"), () => {
				frappe.prompt(
					[
						{
							fieldname: "template_name",
							fieldtype: "Data",
							label: __("New Display Name"),
							reqd: 1,
							default: (frm.doc.display_name || frm.doc.template_name || "") + " Copy",
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

			frm.add_custom_button(__("Cut"), () => {
				const label = frm.doc.display_name || frm.doc.template_name || frm.doc.name;
				frappe.confirm(
					__("Cut (delete) template <b>{0}</b>? This cannot be undone.", [
						frappe.utils.escape_html(label),
					]),
					() => {
						frappe.call({
							method: "instacertify.quotation.events.delete_quotation_template",
							args: { template: frm.doc.name },
							freeze: true,
							callback() {
								frappe.show_alert({
									message: __("Template deleted"),
									indicator: "orange",
								});
								frappe.set_route("quote-format-library");
							},
						});
					}
				);
			}, __("Actions"));

			frm.add_custom_button(__("New Quotation from Template"), () => {
				const qtype =
					frm.doc.quotation_type === "Service" ? "Consulting" : frm.doc.quotation_type;
				frappe.call({
					method: "instacertify.quotation.events.get_quotation_template_payload",
					args: { template: frm.doc.name },
					freeze: true,
					freeze_message: __("Loading quote format…"),
					callback(r) {
						instacertify._pending_quote_format = {
							skip: 0,
							quotation_type: qtype || "Consulting",
							payload: r.message || {},
						};
						frappe.model.with_doctype("Quotation", () => {
							frappe.new_doc("Quotation", {
								ic_quotation_type: qtype,
								ic_quotation_template: frm.doc.name,
								ic_service_family: frm.doc.service_family,
							});
						});
					},
				});
			}, __("Actions"));

			frm.add_custom_button(__("Print"), () => {
				_preview_template(frm, "print");
			}, __("Test"));

			frm.add_custom_button(__("Download PDF"), () => {
				_preview_template(frm, "pdf");
			}, __("Test"));

			frm.add_custom_button(__("Jump to Pricing"), () => {
				frm.scroll_to_field("cost_items");
			});

			frm.add_custom_button(__("Jump to Headings"), () => {
				frm.scroll_to_field("label_about");
			});

			frm.add_custom_button(__("Show All Print Sections"), () => {
				_set_all_print_sections(frm, 1);
			}, __("Print Sections"));

			frm.add_custom_button(__("Hide All Print Sections"), () => {
				_set_all_print_sections(frm, 0);
			}, __("Print Sections"));
		}
	},

	quotation_type(frm) {
		_toggle_sections(frm);
		_render_edit_guide(frm);
	},
});

const IC_TEMPLATE_SHOW_FIELDS = [
	"show_about",
	"show_applicable_standards",
	"show_process",
	"show_validity",
	"show_sample_required",
	"show_documents_required",
	"show_timelines",
	"show_deliverables",
	"show_commercials",
	"show_payment_terms",
	"show_banking",
	"show_cancellation",
	"show_force_majeure",
	"show_confidentiality",
	"show_terms",
	"show_sample_handling",
];

function _set_all_print_sections(frm, value) {
	IC_TEMPLATE_SHOW_FIELDS.forEach((f) => {
		if (frm.fields_dict[f]) {
			frm.set_value(f, value);
		}
	});
	frappe.show_alert({
		message: value
			? __("All print sections set to Show")
			: __("All print sections set to Hide"),
		indicator: value ? "green" : "orange",
	});
}
function _lock_template_id(frm) {
	if (!frm.fields_dict.template_name) return;
	// Template ID is the document name — editable only on create.
	frm.set_df_property("template_name", "read_only", frm.is_new() ? 0 : 1);
	if (frm.fields_dict.display_name) {
		frm.set_df_property("display_name", "reqd", 0);
	}
}

/** Unlock all template content except system Template ID; banking stays Link-only. */
function _unlock_template_content_fields(frm) {
	if (!frm || !frm.fields_dict) return;
	Object.keys(frm.fields_dict).forEach((fieldname) => {
		const df = frm.fields_dict[fieldname].df;
		if (!df) return;
		if (
			[
				"Section Break",
				"Column Break",
				"Tab Break",
				"HTML",
				"Heading",
				"Button",
				"Fold",
			].includes(df.fieldtype)
		) {
			return;
		}
		if (fieldname === "template_name" && !frm.is_new()) return;
		// bank_account Link stays choosable; details live on IC Bank Account
		frm.set_df_property(fieldname, "read_only", 0);
	});
	[
		"section_print_sections",
		"section_print_labels",
		"section_consulting_narrative",
		"section_testing_narrative",
		"section_scope",
		"section_cost",
		"section_testing",
		"section_policies",
		"section_service",
	].forEach((f) => {
		if (frm.fields_dict[f]) frm.toggle_display(f, true);
	});
	IC_TEMPLATE_SHOW_FIELDS.forEach((f) => {
		if (frm.fields_dict[f]) {
			frm.set_df_property(f, "read_only", 0);
			if (frm.doc[f] == null) frm.doc[f] = 1;
		}
	});
	// Child tables — keep editable
	["cost_items", "test_items", "format_library"].forEach((table) => {
		const grid = frm.fields_dict[table] && frm.fields_dict[table].grid;
		if (!grid || !grid.docfields) return;
		(grid.docfields || []).forEach((df) => {
			if (!df || !df.fieldname) return;
			if (["Section Break", "Column Break"].includes(df.fieldtype)) return;
			grid.update_docfield_property(df.fieldname, "read_only", 0);
		});
	});
}

function _preview_template(frm, mode) {
	const run = () => {
		frappe.call({
			method: "instacertify.quotation.events.ensure_template_preview_quotation",
			args: { template: frm.doc.name },
			freeze: true,
			freeze_message: mode === "pdf" ? __("Preparing PDF…") : __("Preparing print preview…"),
			callback(r) {
				const m = r.message || {};
				if (!m.quotation) {
					frappe.msgprint(__("Could not build preview quotation."));
					return;
				}
				const fmt = m.print_format || "Instacertify Quotation";
				if (mode === "pdf") {
					const url = frappe.urllib.get_full_url(
						"/api/method/instacertify.utils.pdf.download_quotation_pdf?" +
							$.param({ name: m.quotation, print_format: fmt })
					);
					window.open(url, "_blank");
				} else {
					const url = frappe.urllib.get_full_url(
						"/printview?" +
							$.param({
								doctype: "Quotation",
								name: m.quotation,
								format: fmt,
								no_letterhead: 0,
								_lang: frappe.boot.lang || "en",
							})
					);
					window.open(url, "_blank");
				}
			},
		});
	};

	if (frm.is_dirty && frm.is_dirty()) {
		frm.save().then(run);
	} else {
		run();
	}
}

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
				<li><b>${__("Fully editable")}</b>: ${__("Every heading, narrative, Sample Required, Force Majeure, Terms, commercials, and print-section toggle — edit freely. Banking account number / IFSC / UPI stay on IC Bank Account (select account only).")}</li>
				<li><b>${__("Display Name")}</b>: ${__("Rename anytime — does not change Template ID or linked quotes.")}</li>
				<li><b>${__("Print Sections")}</b>: ${__("Uncheck Sample Required, Force Majeure, Terms, Banking, etc. to hide that row on Print/PDF. Use Print Sections → Show/Hide All.")}</li>
				<li><b>${__("Section 2 — Rename headings")}</b>: ${__("Change printed names (ABOUT, Commercials, Payment Terms, column titles).")}</li>
				<li><b>${__("Narrative sections")}</b>: ${__("Edit all body text for {0} quotes.", [__(qtype)])}</li>
				<li><b>${__("Section 6 — Pricing")}</b>: ${__("Add default amounts the sales team can change on each quote. Set Revenue = Do Not Count as Revenue for govt/lab/third-party lines (shown on the quote, not counted as Instacertify revenue).")}</li>
				<li><b>${__("Policies")}</b>: ${__("Payment terms, cancellation, confidentiality, T&Cs.")}</li>
				<li><b>${__("Test")}</b>: ${__("After Save, use Test → Print or Test → Download PDF to preview the customer layout.")}</li>
			</ul>
			<div style="margin-top:8px;color:var(--text-muted,#6c7680);">
				${__("Default amounts copy onto new quotations and stay editable there for the sales team.")}
			</div>
		</div>
	`);
}
