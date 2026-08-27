// Copyright (c) Instacertify
frappe.ui.form.on("Helpdesk Ticket", {
	refresh(frm) {
		if (frm.is_new()) return;
		if (frm.doc.customer) {
			frm.add_custom_button(__("Open Customer"), () => {
				frappe.set_route("Form", "Customer", frm.doc.customer);
			}, __("Go to"));
		}
		if (frm.doc.lead) {
			frm.add_custom_button(__("Open Lead"), () => {
				frappe.set_route("Form", "Lead", frm.doc.lead);
			}, __("Go to"));
		}
		if (frm.doc.project) {
			frm.add_custom_button(__("Open Project"), () => {
				frappe.set_route("Form", "Project", frm.doc.project);
			}, __("Go to"));
		}
		if (frm.doc.status === "Open") {
			frm.add_custom_button(__("Mark In Progress"), () => {
				frm.set_value("status", "In Progress");
				frm.save();
			}, __("Status"));
		}
		if (["Open", "In Progress", "Waiting on Customer"].includes(frm.doc.status)) {
			frm.add_custom_button(__("Resolve"), () => {
				frm.set_value("status", "Resolved");
				frm.save();
			}, __("Status"));
		}
	},
	project(frm) {
		if (!frm.doc.project || frm.doc.customer) return;
		frappe.db.get_value("Project", frm.doc.project, "customer").then((r) => {
			if (r.message && r.message.customer) {
				frm.set_value("customer", r.message.customer);
			}
		});
	},
});
