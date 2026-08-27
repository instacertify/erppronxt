# Copyright (c) Instacertify
frappe.ui.form.on("IC Expense Claim", {
	refresh(frm) {
		frm.set_intro(
			__(
				"File travel, petty cash, office, and other expenses. Attach the receipt and Submit for approval."
			),
			"blue"
		);
		if (frm.doc.docstatus === 1 && frm.doc.status === "Submitted") {
			if (frappe.user.has_role("System Manager") || frappe.user.has_role("IC Admin") || frappe.user.has_role("IC Senior Operations") || frappe.user.has_role("IC Operations Manager")) {
				frm.add_custom_button(__("Approve"), () => {
					frappe.call({
						method: "instacertify.expenses.api.set_expense_status",
						args: { name: frm.doc.name, status: "Approved" },
						freeze: true,
						callback() {
							frm.reload_doc();
						},
					});
				}, __("Actions"));
				frm.add_custom_button(__("Reject"), () => {
					frappe.prompt(
						[{ fieldname: "remarks", fieldtype: "Small Text", label: __("Remarks"), reqd: 1 }],
						(values) => {
							frappe.call({
								method: "instacertify.expenses.api.set_expense_status",
								args: {
									name: frm.doc.name,
									status: "Rejected",
									remarks: values.remarks,
								},
								freeze: true,
								callback() {
									frm.reload_doc();
								},
							});
						},
						__("Reject Expense"),
						__("Reject")
					);
				}, __("Actions"));
				frm.add_custom_button(__("Mark Reimbursed"), () => {
					frappe.call({
						method: "instacertify.expenses.api.set_expense_status",
						args: { name: frm.doc.name, status: "Reimbursed" },
						freeze: true,
						callback() {
							frm.reload_doc();
						},
					});
				}, __("Actions"));
			}
		}
	},
	onload(frm) {
		if (frm.is_new() && !frm.doc.employee) {
			frappe.db.get_value("Employee", { user_id: frappe.session.user }, "name").then((r) => {
				const emp = r && r.message && r.message.name;
				if (emp) frm.set_value("employee", emp);
			});
		}
	},
});
