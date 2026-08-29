frappe.ui.form.on("IC Contract", {
	refresh(frm) {
		if (frm.is_new()) return;

		frm.add_custom_button(__("Open Quotation"), () => {
			if (frm.doc.quotation) {
				frappe.set_route("Form", "Quotation", frm.doc.quotation);
			} else {
				frappe.msgprint(__("No quotation linked."));
			}
		}, __("Links"));

		if (frm.doc.lead) {
			frm.add_custom_button(__("Open Lead"), () => {
				frappe.set_route("Form", "Lead", frm.doc.lead);
			}, __("Links"));
		}
		if (frm.doc.customer) {
			frm.add_custom_button(__("Open Customer"), () => {
				frappe.set_route("Form", "Customer", frm.doc.customer);
			}, __("Links"));
		}

		if (frm.doc.status !== "Cancelled") {
			frm.add_custom_button(__("Share with Customer"), () => {
				frappe.call({
					method: "instacertify.contract.events.share_contract",
					args: { contract: frm.doc.name },
					freeze: true,
					callback(r) {
						frm.reload_doc();
						const url = r.message && r.message.url;
						frappe.msgprint({
							title: __("Contract Share Link"),
							message: `
								<p>${__("Customer can open this link to read, download, and accept the contract by typing their name:")}</p>
								<p><a href="${frappe.utils.escape_html(url)}" target="_blank" rel="noopener">${frappe.utils.escape_html(url)}</a></p>
							`,
							indicator: "green",
						});
						if (url && navigator.clipboard) {
							navigator.clipboard.writeText(url).catch(() => {});
						}
					},
				});
			}, __("Actions"));
		}

		if (frm.doc.status === "Shared with Customer" || frm.doc.status === "Accepted") {
			frm.add_custom_button(__("Open for Edit / Re-share"), () => {
				frappe.call({
					method: "instacertify.contract.events.open_contract_for_edit",
					args: { contract: frm.doc.name },
					freeze: true,
					callback() {
						frm.reload_doc();
						frappe.show_alert({ message: __("Contract opened for editing"), indicator: "blue" });
					},
				});
			}, __("Actions"));
		}
	},
});
