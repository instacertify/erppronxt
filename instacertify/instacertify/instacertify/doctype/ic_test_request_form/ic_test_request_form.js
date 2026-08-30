# Copyright (c) Instacertify
frappe.ui.form.on("IC Test Request Form", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("Share with Customer"), () => {
			frappe.call({
				method: "instacertify.trf.api.share_trf",
				args: { name: frm.doc.name },
				freeze: true,
				callback(r) {
					const m = r.message || {};
					frm.reload_doc();
					frappe.msgprint({
						title: __("TRF customer fill link"),
						message: `<p>${__("Send this link to the customer to fill the Test Request Form:")}</p>
							<p><a href="${frappe.utils.escape_html(m.url)}" target="_blank">${frappe.utils.escape_html(
								m.url
							)}</a></p>
							<p class="text-muted">${__(
								"Customer can submit only once. Use Allow Edit if a correction is needed."
							)}</p>`,
						indicator: "green",
					});
				},
			});
		});

		const locked = ["Submitted by Customer", "Under Review", "PDF Generated", "Completed"].includes(
			frm.doc.status
		);
		if (locked) {
			frm.add_custom_button(__("Allow Edit"), () => {
				frappe.confirm(
					__(
						"Reopen this TRF so the customer (or you) can correct details? After they submit again, it will lock."
					),
					() => {
						frappe.call({
							method: "instacertify.trf.api.reopen_trf_for_edit",
							args: { name: frm.doc.name },
							freeze: true,
							callback(r) {
								const m = r.message || {};
								frm.reload_doc();
								frappe.msgprint({
									title: __("TRF reopened for edit"),
									message: `<p>${frappe.utils.escape_html(
										m.message || __("TRF reopened for edit")
									)}</p>
									${
										m.share_url
											? `<p><a href="${frappe.utils.escape_html(
													m.share_url
											  )}" target="_blank">${frappe.utils.escape_html(m.share_url)}</a></p>`
											: ""
									}`,
									indicator: "green",
								});
							},
						});
					}
				);
			});
		}

		const can_pdf =
			["Submitted by Customer", "Under Review", "Reopened for Edit", "PDF Generated", "Completed"].includes(
				frm.doc.status
			) || (frm.doc.sample_name && frm.doc.brand_name);
		if (can_pdf) {
			frm.add_custom_button(__("Generate TRF PDF"), () => {
				frappe.call({
					method: "instacertify.trf.api.generate_trf_pdf",
					args: { name: frm.doc.name },
					freeze: true,
					freeze_message: __("Generating TRF PDF…"),
					callback(r) {
						const m = r.message || {};
						frm.reload_doc();
						if (m.file_url) {
							window.open(m.file_url, "_blank");
						}
						frappe.show_alert({ message: __("TRF PDF ready"), indicator: "green" });
					},
				});
			});
		}
		if (frm.doc.pdf_file) {
			frm.add_custom_button(__("Open PDF"), () => window.open(frm.doc.pdf_file, "_blank"));
		}
		if (frm.doc.share_url) {
			frm.add_custom_button(__("Copy Customer Link"), () => {
				frappe.utils.copy_to_clipboard(frm.doc.share_url);
				frappe.show_alert({ message: __("Link copied"), indicator: "green" });
			});
		}
	},
});
