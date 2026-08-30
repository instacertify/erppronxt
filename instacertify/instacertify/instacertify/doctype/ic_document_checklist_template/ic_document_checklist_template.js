// Copyright (c) Instacertify
frappe.ui.form.on("IC Document Checklist Template", {
	refresh(frm) {
		frm.add_custom_button(__("Open Library"), () => {
			frappe.set_route("document-collection-library");
		});
		frm.set_intro(
			__(
				"Use Format Fields (optional) to check/uncheck built-in Data Collection fields. Unchecked fields are hidden on sheets created from this template."
			),
			"blue"
		);
		if (!frm.is_new()) {
			frm.add_custom_button(__("Use for Customer"), () => {
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
							default: __("Documents — {0}", [frm.doc.template_name || frm.doc.name]),
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
