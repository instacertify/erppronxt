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
		}
	},

	quotation_type(frm) {
		_toggle_sections(frm);
		_render_edit_guide(frm);
	},
});

function _lock_template_id(frm) {
	if (!frm.fields_dict.template_name) return;
	// Template ID is the document name — editable only on create.
	frm.set_df_property("template_name", "read_only", frm.is_new() ? 0 : 1);
	if (frm.fields_dict.display_name) {
		frm.set_df_property("display_name", "reqd", 0);
	}
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
				<li><b>${__("Display Name")}</b>: ${__("Rename anytime — does not change Template ID or linked quotes.")}</li>
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
