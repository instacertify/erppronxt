// Copyright (c) Instacertify
frappe.ui.form.on("IC Document Checklist Template", {
	refresh(frm) {
		frm.add_custom_button(__("Open Library"), () => {
			frappe.set_route("document-collection-library");
		});
		frm.set_intro(
			__(
				"Rename with Display Name anytime (Template ID stays fixed). Use Format Fields to check/uncheck built-in Data Collection fields. Unchecked fields are hidden on sheets created from this template."
			),
			"blue"
		);
		if (frm.fields_dict.template_name) {
			frm.set_df_property("template_name", "read_only", frm.is_new() ? 0 : 1);
		}
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
							method: "instacertify.documents.api.rename_checklist_template_display_name",
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

			frm.add_custom_button(__("Copy Template"), () => {
				const base = frm.doc.display_name || frm.doc.template_name || "";
				frappe.prompt(
					[
						{
							fieldname: "template_name",
							fieldtype: "Data",
							label: __("New Display Name"),
							reqd: 1,
							default: __("{0} Copy", [base]),
						},
					],
					(values) => {
						frappe.call({
							method: "instacertify.documents.api.duplicate_checklist_template",
							args: {
								template: frm.doc.name,
								new_name: values.template_name,
							},
							freeze: true,
							callback(r) {
								frappe.set_route(
									"Form",
									"IC Document Checklist Template",
									(r.message || {}).template
								);
							},
						});
					},
					__("Copy Document Template"),
					__("Copy")
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
							method: "instacertify.documents.api.delete_checklist_template",
							args: { template: frm.doc.name },
							freeze: true,
							callback() {
								frappe.show_alert({
									message: __("Template deleted"),
									indicator: "orange",
								});
								frappe.set_route("document-collection-library");
							},
						});
					}
				);
			}, __("Actions"));

			frm.add_custom_button(__("Use for Customer"), () => {
				const shown = frm.doc.display_name || frm.doc.template_name || frm.doc.name;
				const d = new frappe.ui.Dialog({
					title: __("Create Document Collection Request"),
					fields: [
						{
							fieldname: "customer",
							fieldtype: "Link",
							options: "Customer",
							label: __("Customer"),
							reqd: 1,
						},
						{
							fieldname: "title",
							fieldtype: "Data",
							label: __("Sheet Title"),
							default: __("Documents — {0}", [shown]),
						},
						{
							fieldname: "share",
							fieldtype: "Check",
							label: __("Generate customer share link now"),
							default: 1,
						},
					],
					primary_action_label: __("Create"),
					primary_action(values) {
						frappe.call({
							method: "instacertify.documents.api.create_document_request_for_customer",
							args: {
								customer: values.customer,
								title: values.title,
								template: frm.doc.name,
								share: values.share ? 1 : 0,
							},
							freeze: true,
							callback(r) {
								d.hide();
								const m = r.message || {};
								if (m.url) {
									frappe.msgprint({
										title: __("Customer share link"),
										indicator: "green",
										message: `<p><a href="${frappe.utils.escape_html(m.url)}" target="_blank" rel="noopener">${frappe.utils.escape_html(m.url)}</a></p>`,
									});
									if (navigator.clipboard) {
										navigator.clipboard.writeText(m.url).catch(() => {});
									}
								}
								if (m.document_request) {
									frappe.set_route("Form", "IC Document Request", m.document_request);
								}
							},
						});
					},
				});
				d.show();
			}, __("Actions"));
		}
	},
});
