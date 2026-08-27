// Copyright (c) Instacertify
frappe.ui.form.on("IC Quotation Template", {
	refresh(frm) {
		frm.set_intro(
			__(
				"Create separate templates for each consulting service, testing package, or renewal quote. Active templates appear when making a Quotation of the same type."
			),
			"blue"
		);

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
					ic_quotation_type: frm.doc.quotation_type === "Service" ? "Consulting" : frm.doc.quotation_type,
					ic_quotation_template: frm.doc.name,
					ic_service_family: frm.doc.service_family,
				});
			}, __("Actions"));
		}

		frm.toggle_display(
			"section_service",
			["Consulting", "Renewal", "Service", "Other", "Multiple Products / Multiple Services"].includes(
				frm.doc.quotation_type
			)
		);
	},

	quotation_type(frm) {
		frm.trigger("refresh");
	},
});
