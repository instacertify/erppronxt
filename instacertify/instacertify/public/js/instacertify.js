/*! Instacertify Desk JS */
frappe.provide("instacertify");

instacertify.brand = {
	primary: "#065175",
	accent: "#EC6820",
	surface: "#f3f8fb",
	logo: "/assets/instacertify/images/instacertify_logo.png",
	icon: "/assets/instacertify/images/instacertify_icon.png",
	app_logo: "/assets/instacertify/images/instacertify_app_logo.png",
	favicon: "/assets/instacertify/images/favicon-32.png",
};

/** Open a new Helpdesk Ticket with CRM context defaults. */
instacertify.raise_helpdesk_ticket = function (defaults) {
	defaults = defaults || {};
	frappe.new_doc("Helpdesk Ticket", defaults);
};

/** Add Raise Ticket / Raise Complaint buttons on CRM forms. */
instacertify.add_helpdesk_buttons = function (frm, defaults) {
	if (frm.is_new()) return;
	frm.add_custom_button(__("Raise Complaint"), () => {
		instacertify.raise_helpdesk_ticket(
			Object.assign({ ticket_type: "Complaint", priority: "High" }, defaults || {})
		);
	}, __("Helpdesk"));
	frm.add_custom_button(__("Raise Ticket"), () => {
		instacertify.raise_helpdesk_ticket(
			Object.assign({ ticket_type: "Query", priority: "Medium" }, defaults || {})
		);
	}, __("Helpdesk"));
	frm.add_custom_button(__("View Tickets"), () => {
		const filters = {};
		if (defaults && defaults.customer) filters.customer = defaults.customer;
		if (defaults && defaults.lead) filters.lead = defaults.lead;
		if (defaults && defaults.project) filters.project = defaults.project;
		frappe.set_route("List", "Helpdesk Ticket", filters);
	}, __("Helpdesk"));
};


// Prefer light theme with Instacertify soft hue (never force dark)
(function applyInstacertifyLightTheme() {
	try {
		document.documentElement.setAttribute("data-theme", "light");
		document.documentElement.setAttribute("data-ic-theme", "light-hue");
		if (window.localStorage) {
			localStorage.setItem("theme", "light");
			localStorage.setItem("desk_theme", "light");
		}
	} catch (e) {
		/* ignore */
	}
})();

// Ensure favicon is always the circular Instacertify mark
(function setInstacertifyFavicon() {
	const href = instacertify.brand.favicon;
	let link = document.querySelector("link[rel='icon']");
	if (!link) {
		link = document.createElement("link");
		link.rel = "icon";
		document.head.appendChild(link);
	}
	link.type = "image/png";
	link.href = href;
	let apple = document.querySelector("link[rel='apple-touch-icon']");
	if (!apple) {
		apple = document.createElement("link");
		apple.rel = "apple-touch-icon";
		document.head.appendChild(apple);
	}
	apple.href = "/assets/instacertify/images/apple-touch-icon.png";
})();

instacertify.greeting = function (fullName) {
	const hour = moment().hour();
	let greet = __("Good Evening");
	if (hour < 12) greet = __("Good Morning");
	else if (hour < 17) greet = __("Good Afternoon");
	return `${greet}, ${fullName || frappe.session.user_fullname}`;
};

instacertify.render_home_banner = function (wrapper) {
	if (!wrapper || wrapper.find(".ic-greeting").length) return;
	const html = `
		<div class="ic-greeting">
			<div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">
				<img src="${instacertify.brand.icon}" alt="Instacertify" style="width:42px;height:42px;object-fit:contain;"/>
				<span style="font-size:1.15rem;font-weight:700;letter-spacing:0.02em;">Instacertify</span>
			</div>
			<h2>${frappe.utils.escape_html(instacertify.greeting())}</h2>
			<div class="ic-datetime">
				<span class="ic-date">${moment().format("dddd, D MMMM YYYY")}</span>
				&nbsp;·&nbsp;
				<span class="ic-time">${moment().format("h:mm A")}</span>
			</div>
		</div>
		<div class="ic-summary-grid" id="ic-summary-grid"></div>
		<div class="ic-section-title" style="margin:8px 0 10px;color:#065175;font-weight:600;">Ongoing Projects</div>
		<div class="ic-project-grid" id="ic-project-grid"></div>
	`;
	wrapper.prepend(html);

	setInterval(() => {
		wrapper.find(".ic-time").text(moment().format("h:mm A"));
		wrapper.find(".ic-greeting h2").text(instacertify.greeting());
	}, 30000);

	instacertify.load_summary_cards();
	instacertify.load_project_cards();
};

instacertify.load_summary_cards = function () {
	frappe.call({
		method: "instacertify.project.events.get_dashboard_counts",
		callback(r) {
			const d = r.message || {};
			const items = [
				["New Leads", d.new_leads],
				["Active Leads", d.active_leads],
				["Quotations Sent", d.quotations_sent],
				["Awaiting Response", d.quotations_awaiting],
				["Quotations Accepted", d.quotations_accepted, true],
				["Active Projects", d.active_projects],
				["Pending Tasks", d.pending_tasks],
				["Pending Documents", d.pending_documents],
				["Testing Requests", d.testing_requests],
				["Upcoming Deadlines", d.upcoming_deadlines, true],
			];
			const $grid = $("#ic-summary-grid");
			if (!$grid.length) return;
			$grid.empty();
			items.forEach(([label, value, accent]) => {
				$grid.append(`
					<div class="ic-summary-card ${accent ? "accent" : ""}">
						<div class="label">${label}</div>
						<div class="value">${value ?? 0}</div>
					</div>
				`);
			});
		},
	});
};

instacertify.load_project_cards = function () {
	frappe.call({
		method: "instacertify.project.events.get_ongoing_project_cards",
		args: { limit: 8 },
		callback(r) {
			const $grid = $("#ic-project-grid");
			if (!$grid.length) return;
			$grid.empty();
			(r.message || []).forEach((p) => {
				const priority = p.ic_priority || "Medium";
				const progress = Math.round(p.progress || 0);
				const badgeClass = priority.toLowerCase();
				$grid.append(`
					<div class="ic-project-card priority-${frappe.utils.escape_html(priority)}" data-name="${p.name}">
						<h4>${frappe.utils.escape_html(p.project_name || p.name)}</h4>
						<div class="meta"><b>Customer:</b> ${frappe.utils.escape_html(p.customer_name || p.customer || "-")}</div>
						<div class="meta"><b>Priority:</b> <span class="ic-badge ${badgeClass}">${frappe.utils.escape_html(priority)}</span></div>
						<div class="meta"><b>Status:</b> ${frappe.utils.escape_html(p.ic_project_stage || p.status || "-")}</div>
						<div class="ic-progress"><span style="width:${progress}%"></span></div>
						<div class="meta"><b>Progress:</b> ${progress}%</div>
						<div class="meta"><b>Pending:</b> ${frappe.utils.escape_html(p.ic_pending_action || "-")}</div>
						<div class="meta"><b>Assigned:</b> ${frappe.utils.escape_html(p.ic_assigned_employee || "-")}</div>
						<div class="meta"><b>Deadline:</b> ${p.deadline ? frappe.datetime.str_to_user(p.deadline) : "-"}</div>
					</div>
				`);
			});
			$grid.find(".ic-project-card").on("click", function () {
				frappe.set_route("Form", "Project", $(this).data("name"));
			});
		},
	});
};

// Inject greeting on Instacertify Home workspace
$(document).on("page-change", function () {
	const route = frappe.get_route();
	if (route[0] === "Workspaces" && (route[1] || "").includes("Instacertify")) {
		setTimeout(() => {
			const $page = $(".workspace-body, .workspace-page, .page-body").first();
			instacertify.render_home_banner($page);
		}, 400);
	}
});

// Quotation form enhancements
frappe.ui.form.on("Quotation", {
	refresh(frm) {
		if (!frm.is_new()) {
			instacertify.add_helpdesk_buttons(frm, {
				quotation: frm.doc.name,
				customer: frm.doc.quotation_to === "Customer" ? frm.doc.party_name : null,
				lead: frm.doc.quotation_to === "Lead" ? frm.doc.party_name : null,
				channel: "Internal",
				subject: `Quotation ${frm.doc.name}`,
			});
			frm.add_custom_button(__("Share with Customer"), () => {
				frappe.call({
					method: "instacertify.quotation.events.share_with_customer",
					args: { quotation: frm.doc.name },
					freeze: true,
					callback(r) {
						frm.reload_doc();
						const url = r.message && r.message.url;
						frappe.msgprint({
							title: __("Customer Share Link"),
							message: `
								<p>${__("Customer can open this link to read, download PDF, approve, reject, or ask for revision:")}</p>
								<p><a href="${frappe.utils.escape_html(url)}" target="_blank" rel="noopener">${frappe.utils.escape_html(url)}</a></p>
								<p class="text-muted">${__("Copy and send this open link to the customer (email / WhatsApp).")}</p>
							`,
							indicator: "green",
						});
						if (url && navigator.clipboard) {
							navigator.clipboard.writeText(url).then(() => {
								frappe.show_alert({ message: __("Link copied"), indicator: "green" });
							}).catch(() => {});
						}
					},
				});
			}, __("Instacertify"));

			frm.add_custom_button(__("Save as Template"), () => {
				frappe.prompt(
					[
						{
							fieldname: "template_name",
							fieldtype: "Data",
							label: "Template Name",
							reqd: 1,
							default:
								frm.doc.ic_quotation_template ||
								frm.doc.ic_service_name ||
								frm.doc.ic_subject ||
								frm.doc.name,
						},
						{
							fieldname: "overwrite",
							fieldtype: "Check",
							label: "Overwrite if exists",
							default: 0,
						},
					],
					(values) => {
						frappe.call({
							method: "instacertify.quotation.events.save_quotation_as_template",
							args: {
								quotation: frm.doc.name,
								template_name: values.template_name,
								overwrite: values.overwrite ? 1 : 0,
							},
							freeze: true,
							callback(r) {
								frm.reload_doc();
								frappe.show_alert({
									message: __("Saved template: {0}", [r.message.template]),
									indicator: "green",
								});
							},
						});
					},
					__("Save Quotation as Template"),
					__("Save")
				);
			}, __("Instacertify"));

			frm.add_custom_button(__("Manage Templates"), () => {
				frappe.set_route("List", "IC Quotation Template", {
					quotation_type: frm.doc.ic_quotation_type || undefined,
				});
			}, __("Instacertify"));

			frm.add_custom_button(__("New Template"), () => {
				frappe.new_doc("IC Quotation Template", {
					quotation_type:
						frm.doc.ic_quotation_type === "Service"
							? "Consulting"
							: frm.doc.ic_quotation_type || "Consulting",
					service_family: frm.doc.ic_service_family,
					service_name: frm.doc.ic_service_name,
				});
			}, __("Instacertify"));

			if (["Changes Requested", "Rejected / Lost"].includes(frm.doc.ic_workflow_status)) {
				if (frm.doc.ic_customer_remarks) {
					frm.set_intro(
						__("Customer remarks: {0}", [frm.doc.ic_customer_remarks]),
						"orange"
					);
				}
				frm.add_custom_button(__("Open for Revision"), () => {
					frappe.confirm(
						__(
							"Bump revision number and reopen this quotation for editing? Only the owner, managers, or admin can revise."
						),
						() => {
							frappe.call({
								method: "instacertify.quotation.events.open_quotation_for_revision",
								args: { quotation: frm.doc.name },
								freeze: true,
								callback(r) {
									frm.reload_doc();
									frappe.show_alert({
										message: __("Revision {0} ready to edit — then Share with Customer again", [
											r.message.ic_revision_number,
										]),
										indicator: "green",
									});
								},
							});
						}
					);
				}, __("Instacertify"));
			}

			if (frm.doc.ic_workflow_status === "Accepted") {
				frm.add_custom_button(__("Create Invoice"), () => {
					frappe.confirm(
						__(
							"Create Sales Invoice from this confirmed quotation as per payment terms? (No Sales Order will be created.)"
						),
						() => {
							frappe.call({
								method: "instacertify.quotation.events.create_invoice_from_quotation",
								args: { quotation: frm.doc.name, submit: 0 },
								freeze: true,
								freeze_message: __("Creating Invoice..."),
								callback(r) {
									if (!r.message || !r.message.invoice) return;
									frappe.show_alert({
										message: r.message.created
											? __("Invoice {0} created", [r.message.invoice])
											: __("Invoice {0} already exists", [r.message.invoice]),
										indicator: "green",
									});
									frappe.set_route("Form", "Sales Invoice", r.message.invoice);
								},
							});
						}
					);
				}, __("Instacertify"));

				frm.add_custom_button(__("Start Project"), () => {
					frappe.call({
						method: "instacertify.quotation.events.start_project_from_quotation",
						args: { quotation: frm.doc.name },
						freeze: true,
						callback(r) {
							const created = (r.message && r.message.testing_requests) || [];
							if (created.length) {
								frappe.show_alert({
									message: __("Created {0} testing request(s) from lab library lines", [
										created.length,
									]),
									indicator: "green",
								});
							}
							frappe.set_route("Form", "Project", r.message.project);
						},
					});
				}, __("Instacertify"));

				if ((frm.doc.ic_test_items || []).length) {
					frm.add_custom_button(__("Create Testing Requests"), () => {
						frappe.call({
							method: "instacertify.testing.events.create_testing_requests_from_quotation",
							args: { quotation: frm.doc.name },
							freeze: true,
							callback(r) {
								const created = (r.message && r.message.created) || [];
								const existing = (r.message && r.message.existing) || [];
								frappe.msgprint({
									title: __("Testing Requests"),
									message: __(
										"Created: {0}<br>Already linked: {1}",
										[created.join(", ") || "—", existing.join(", ") || "—"]
									),
									indicator: "green",
								});
								if (created[0]) {
									frappe.set_route("Form", "IC Testing Request", created[0]);
								}
							},
						});
					}, __("Instacertify"));
				}

				// Make Invoice the primary action after acceptance
				frm.page.set_inner_btn_group_as_primary(__("Instacertify"));
			}

			// Hide Sales Order — Instacertify bills from Quotation directly
			instacertify.hide_sales_order_button(frm);
		}

		instacertify.setup_quotation_lab_queries(frm);

		if (frm.doc.ic_quotation_type) {
			instacertify.toggle_quotation_sections(frm);
		}
		instacertify.setup_quotation_template_filter(frm);
	},

	ic_quotation_type(frm) {
		instacertify.toggle_quotation_sections(frm);
		instacertify.setup_quotation_template_filter(frm);
		if (frm.doc.ic_quotation_template) {
			frm.set_value("ic_quotation_template", "");
		}
	},

	ic_quotation_template(frm) {
		if (!frm.doc.ic_quotation_template) return;
		if (!frm.doc.name) {
			frappe.show_alert(__("Save the quotation first to apply a template"));
			return;
		}
		frappe.call({
			method: "instacertify.quotation.events.apply_quotation_template",
			args: { quotation: frm.doc.name, template: frm.doc.ic_quotation_template },
			freeze: true,
			callback() {
				frm.reload_doc();
			},
		});
	},
});

instacertify.setup_quotation_lab_queries = function (frm) {
	frm.set_query("laboratory", "ic_test_items", () => ({
		filters: { status: "Active" },
	}));
};

instacertify.setup_quotation_template_filter = function (frm) {
	frm.set_query("ic_quotation_template", () => {
		const t = frm.doc.ic_quotation_type;
		const filters = { is_active: 1 };
		if (t === "Consulting" || t === "Service") {
			filters.quotation_type = ["in", ["Consulting", "Service"]];
		} else if (t) {
			filters.quotation_type = t;
		}
		return { filters };
	});
};

instacertify.hide_sales_order_button = function (frm) {
	const hide = () => {
		frm.remove_custom_button(__("Sales Order"), __("Create"));
		// Also remove from inner button group if present
		frm.page &&
			frm.page.btn_secondary &&
			frm.page.btn_secondary.find('.inner-group-button:contains("Sales Order")').remove();
	};
	hide();
	setTimeout(hide, 300);
	setTimeout(hide, 800);
};

instacertify.toggle_quotation_sections = function (frm) {
	const t = frm.doc.ic_quotation_type;
	const consultingLike = ["Consulting", "Renewal", "Service", "Other", "Multiple Products / Multiple Services"];
	frm.toggle_display("ic_section_service", consultingLike.includes(t));
	frm.toggle_display("ic_section_testing", ["Testing", "Multiple Products / Multiple Services"].includes(t));
	frm.toggle_display("ic_section_products", t === "Multiple Products / Multiple Services");
	if (t === "Testing") {
		frm.meta.default_print_format = "Instacertify Testing Quotation";
		frm.set_df_property("ic_subject", "reqd", 1);
	} else if (["Consulting", "Renewal", "Service", "Other"].includes(t)) {
		frm.meta.default_print_format = "Instacertify Consulting Quotation";
		frm.set_df_property("ic_subject", "reqd", 0);
	} else {
		frm.meta.default_print_format = "Instacertify Quotation";
		frm.set_df_property("ic_subject", "reqd", 0);
	}
};

frappe.ui.form.on("IC Quotation Test Item", {
	form_render(frm, cdt, cdn) {
		instacertify.load_lab_scope_options(frm, cdt, cdn);
	},
	laboratory(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "lab_test_scope", "");
		frappe.model.set_value(cdt, cdn, "lab_scope_row", "");
		frappe.model.set_value(cdt, cdn, "suggested_selling_price", 0);
		frappe.model.set_value(cdt, cdn, "laboratory_accreditation", "");
		if (!row.laboratory) {
			instacertify.set_lab_scope_autocomplete(frm, []);
			return;
		}
		frappe.call({
			method: "instacertify.laboratory.api.get_laboratory_summary",
			args: { laboratory: row.laboratory },
			callback(r) {
				const d = r.message || {};
				if (d.accreditation_summary) {
					frappe.model.set_value(cdt, cdn, "laboratory_accreditation", d.accreditation_summary);
				}
			},
		});
		instacertify.load_lab_scope_options(frm, cdt, cdn);
	},
	lab_test_scope(frm, cdt, cdn) {
		instacertify.apply_lab_test_scope(frm, cdt, cdn);
	},
	number_of_samples(frm, cdt, cdn) {
		instacertify.recalc_test_row(frm, cdt, cdn);
	},
	per_unit_charges(frm, cdt, cdn) {
		instacertify.recalc_test_row(frm, cdt, cdn);
	},
});

instacertify.recalc_test_row = function (frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	const units = row.number_of_samples || 1;
	if (row.per_unit_charges != null && row.per_unit_charges !== "") {
		frappe.model.set_value(cdt, cdn, "testing_charges", flt(row.per_unit_charges) * units);
	}
};

instacertify.set_lab_scope_autocomplete = function (frm, options) {
	const grid = frm.fields_dict.ic_test_items && frm.fields_dict.ic_test_items.grid;
	if (!grid) return;
	const opt_str = (options || []).map((o) => o.value || o).join("\n");
	grid.update_docfield_property("lab_test_scope", "options", opt_str);
};

instacertify.load_lab_scope_options = function (frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (!row || !row.laboratory) {
		instacertify.set_lab_scope_autocomplete(frm, []);
		return;
	}
	frappe.call({
		method: "instacertify.laboratory.api.get_lab_test_scope_options",
		args: { laboratory: row.laboratory },
		callback(r) {
			const opts = r.message || [];
			frm._ic_lab_scopes = frm._ic_lab_scopes || {};
			frm._ic_lab_scopes[row.laboratory] = opts;
			instacertify.set_lab_scope_autocomplete(frm, opts);
		},
	});
};

instacertify.apply_lab_test_scope = function (frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (!row.laboratory || !row.lab_test_scope) return;
	frappe.call({
		method: "instacertify.laboratory.api.get_lab_test_scope_details",
		args: {
			laboratory: row.laboratory,
			scope_key: row.lab_test_scope,
			scope_row: row.lab_scope_row,
		},
		callback(r) {
			const s = r.message;
			if (!s) {
				frappe.show_alert({
					message: __("No matching test in this lab library. Check Lab Test / Pricing."),
					indicator: "orange",
				});
				return;
			}
			frappe.model.set_value(cdt, cdn, "lab_scope_row", s.name);
			frappe.model.set_value(cdt, cdn, "test_name", s.test_name);
			if (s.applicable_standard) {
				frappe.model.set_value(cdt, cdn, "applicable_standard", s.applicable_standard);
			}
			frappe.model.set_value(cdt, cdn, "suggested_selling_price", s.selling_price);
			// Prefill editable selling price from library (user may change)
			frappe.model.set_value(cdt, cdn, "per_unit_charges", s.selling_price).then(() => {
				instacertify.recalc_test_row(frm, cdt, cdn);
			});
			if (s.currency) {
				frappe.model.set_value(cdt, cdn, "currency", s.currency);
			}
			if (s.label && row.lab_test_scope !== s.label) {
				frappe.model.set_value(cdt, cdn, "lab_test_scope", s.label);
			}
		},
	});
};

// Prompt for quotation type on new
frappe.ui.form.on("Quotation", {
	onload(frm) {
		instacertify.setup_quotation_template_filter(frm);
		if (frm.is_new() && !frm.doc.ic_quotation_type) {
			frappe.prompt(
				[
					{
						fieldname: "ic_quotation_type",
						fieldtype: "Select",
						label: "Quotation Type",
						options: "Consulting\nTesting\nRenewal\nOther\nMultiple Products / Multiple Services",
						reqd: 1,
						default: "Consulting",
					},
					{
						fieldname: "ic_quotation_template",
						fieldtype: "Link",
						label: "Quotation Template",
						options: "IC Quotation Template",
						get_query() {
							// evaluated in prompt via options only; filter applied after type set
							return {};
						},
					},
				],
				(values) => {
					frm.set_value("ic_quotation_type", values.ic_quotation_type);
					if (values.ic_quotation_template) {
						frm.set_value("ic_quotation_template", values.ic_quotation_template);
					}
				},
				__("Create Quotation"),
				__("Continue")
			);
		}
	},
});

// Customer Related Data tab — full per-customer history + completed project files
frappe.ui.form.on("Customer", {
	refresh(frm) {
		if (!frm.doc.name || frm.is_new()) return;
		instacertify.load_customer_related(frm);
		instacertify.add_helpdesk_buttons(frm, {
			customer: frm.doc.name,
			contact_person: frm.doc.customer_name,
			channel: "Internal",
		});
	},
});

instacertify.load_customer_related = function (frm) {
	frappe.call({
		method: "instacertify.crm.events.get_customer_history",
		args: { customer: frm.doc.name },
		callback(r) {
			const d = r.message || {};
			frm.set_df_property("ic_history_html", "options", ic_render_customer_related(d));
			if (frm.fields_dict.ic_customer_files_html) {
				frm.set_df_property(
					"ic_customer_files_html",
					"options",
					ic_render_customer_files(frm, d)
				);
				ic_bind_customer_file_actions(frm);
			}
		},
	});
};

function ic_file_rows(files) {
	return (files || []).map((f) => [
		`<a href="${frappe.utils.escape_html(f.file_url || "#")}" target="_blank" rel="noopener">${ic_esc(
			f.file_name || f.name
		)}</a>`,
		ic_esc(f.source || f.project || f.attached_to_name || "—"),
		ic_esc((f.creation || "").toString().slice(0, 10) || "—"),
	]);
}

function ic_render_customer_files(frm, d) {
	const saved = ic_table(
		[__("File"), __("Source"), __("Date")],
		(d.customer_files || []).map((f) => [
			`<a href="${frappe.utils.escape_html(f.file_url || "#")}" target="_blank" rel="noopener">${ic_esc(
				f.file_name || f.name
			)}</a>`,
			__("Saved on Customer"),
			ic_esc((f.creation || "").toString().slice(0, 10) || "—"),
		])
	);
	const from_projects = ic_table(
		[__("File"), __("Project / Record"), __("Date")],
		ic_file_rows(d.project_files)
	);
	const completed_count = (d.completed_project_names || []).length;
	const pending_count = (d.project_files || []).length;

	return `
		<div class="ic-customer-files">
			<p class="text-muted" style="margin-bottom:12px;">
				${__(
					"Save certificates, reports, and other files from completed projects onto this customer. You can also upload files directly."
				)}
			</p>
			<div class="ic-file-actions" style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px;">
				<button type="button" class="btn btn-primary btn-sm ic-import-project-files">
					${__("Save files from completed projects")}
					${pending_count ? ` (${pending_count})` : ""}
				</button>
				<button type="button" class="btn btn-default btn-sm ic-upload-customer-file">
					${__("Upload file to customer")}
				</button>
			</div>
			<p class="text-muted" style="font-size:12px;margin-bottom:8px;">
				${__("Completed projects")}: ${completed_count}
			</p>
			${ic_related_section(
				__("Saved on this Customer"),
				saved,
				__("No files saved on this customer yet")
			)}
			${ic_related_section(
				__("Available from Completed Projects"),
				from_projects,
				__("No files on completed projects yet")
			)}
		</div>
	`;
}

function ic_bind_customer_file_actions(frm) {
	const $wrap = frm.fields_dict.ic_customer_files_html
		? $(frm.fields_dict.ic_customer_files_html.wrapper)
		: $();

	$wrap.find(".ic-import-project-files").off("click").on("click", () => {
		frappe.confirm(
			__(
				"Copy files from completed projects onto this customer? Existing files with the same name or content are skipped."
			),
			() => {
				frappe.call({
					method: "instacertify.crm.events.import_completed_project_files",
					args: { customer: frm.doc.name },
					freeze: true,
					freeze_message: __("Saving project files…"),
					callback(r) {
						const m = r.message || {};
						frappe.show_alert({
							message: __(
								"Saved {0} file(s); skipped {1} (already on customer). From {2} completed project(s).",
								[m.copied || 0, m.skipped || 0, m.projects || 0]
							),
							indicator: m.copied ? "green" : "orange",
						});
						frm.reload_doc();
					},
				});
			}
		);
	});

	$wrap.find(".ic-upload-customer-file").off("click").on("click", () => {
		new frappe.ui.FileUploader({
			doctype: frm.doctype,
			docname: frm.doc.name,
			frm: frm,
			folder: "Home/Attachments",
			on_success() {
				frappe.show_alert({ message: __("File uploaded"), indicator: "green" });
				instacertify.load_customer_related(frm);
			},
		});
	});
}

function ic_esc(v) {
	return frappe.utils.escape_html(v == null ? "" : String(v));
}

function ic_fmt_money(amount, currency) {
	try {
		return format_currency(amount || 0, currency);
	} catch (e) {
		return String(amount || 0);
	}
}

function ic_doc_link(doctype, name, label) {
	const route = `/app/${frappe.router.slug(doctype)}/${encodeURIComponent(name)}`;
	return `<a href="${route}" class="ic-doc-link">${ic_esc(label || name)}</a>`;
}

function ic_list_link(doctype, customer, label, extra_params) {
	const params = new URLSearchParams(extra_params || { customer });
	const route = `/app/${frappe.router.slug(doctype)}?${params.toString()}`;
	return `<a href="${route}" class="ic-view-all">${ic_esc(label || __("View all"))}</a>`;
}

function ic_status_pill(status) {
	if (!status) return '<span class="text-muted">—</span>';
	return `<span class="ic-status-pill">${ic_esc(status)}</span>`;
}

function ic_related_section(title, rows_html, empty_msg, view_all_html) {
	return `
		<section class="ic-related-section">
			<div class="ic-related-header">
				<h4>${ic_esc(title)}</h4>
				${view_all_html || ""}
			</div>
			${rows_html || `<div class="ic-related-empty">${ic_esc(empty_msg || __("No records"))}</div>`}
		</section>
	`;
}

function ic_table(headers, body_rows) {
	if (!body_rows || !body_rows.length) return "";
	const th = headers.map((h) => `<th>${ic_esc(h)}</th>`).join("");
	const tr = body_rows.map((cols) => `<tr>${cols.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("");
	return `<div class="ic-related-table-wrap"><table class="ic-related-table"><thead><tr>${th}</tr></thead><tbody>${tr}</tbody></table></div>`;
}

function ic_render_customer_related(d) {
	const customer = d.customer || "";
	const cards = `
		<div class="ic-summary-grid">
			<div class="ic-summary-card"><div class="label">${__("Quotations")}</div><div class="value">${(d.quotations || []).length}</div></div>
			<div class="ic-summary-card accent"><div class="label">${__("Shared / Accepted")}</div><div class="value">${(d.shared_quotations || []).length}</div></div>
			<div class="ic-summary-card"><div class="label">${__("Projects")}</div><div class="value">${(d.projects || []).length}</div></div>
			<div class="ic-summary-card"><div class="label">${__("Active Projects")}</div><div class="value">${(d.active_projects || []).length}</div></div>
			<div class="ic-summary-card"><div class="label">${__("Invoices")}</div><div class="value">${(d.invoices || []).length}</div></div>
			<div class="ic-summary-card"><div class="label">${__("Payments")}</div><div class="value">${(d.payments || []).length}</div></div>
			<div class="ic-summary-card accent"><div class="label">${__("Outstanding")}</div><div class="value" style="font-size:1.1rem;">${ic_fmt_money(d.outstanding_amount || 0)}</div></div>
			<div class="ic-summary-card"><div class="label">${__("Testing")}</div><div class="value">${(d.testing_requests || []).length}</div></div>
			<div class="ic-summary-card accent"><div class="label">${__("Open Tickets")}</div><div class="value">${(d.open_tickets || []).length}</div></div>
		</div>
		<p class="ic-related-hint text-muted">${__("All quotations, projects, invoices, payments, and Instacertify records for this customer. Open a row or use Connections for filtered lists.")}</p>
	`;

	const quote_rows = (d.quotations || []).map((q) => [
		ic_doc_link("Quotation", q.name),
		ic_status_pill(q.ic_workflow_status || q.status),
		ic_fmt_money(q.grand_total, q.currency),
		ic_esc(q.transaction_date || "—"),
	]);
	const project_rows = (d.projects || []).map((p) => [
		ic_doc_link("Project", p.name, p.project_name || p.name),
		ic_status_pill(p.status),
		ic_esc(p.ic_project_stage || "—"),
		`${ic_esc(p.ic_progress_percentage || 0)}%`,
		ic_esc(p.ic_deadline || p.expected_end_date || "—"),
	]);
	const invoice_rows = (d.invoices || []).map((i) => [
		ic_doc_link("Sales Invoice", i.name),
		ic_status_pill(i.status),
		ic_fmt_money(i.grand_total, i.currency),
		ic_fmt_money(i.outstanding_amount, i.currency),
		ic_esc(i.posting_date || "—"),
		i.ic_quotation ? ic_doc_link("Quotation", i.ic_quotation) : "—",
	]);
	const payment_rows = (d.payments || []).map((p) => [
		ic_doc_link("Payment Entry", p.name),
		ic_status_pill(p.status || (cint(p.docstatus) === 1 ? "Submitted" : "Draft")),
		ic_esc(p.payment_type || "—"),
		ic_fmt_money(p.received_amount || p.paid_amount, p.currency),
		ic_esc(p.mode_of_payment || "—"),
		ic_esc(p.posting_date || "—"),
	]);
	const opportunity_rows = (d.opportunities || []).map((o) => [
		ic_doc_link("Opportunity", o.name, o.title || o.name),
		ic_status_pill(o.status),
		ic_fmt_money(o.opportunity_amount, o.currency),
		ic_esc(o.transaction_date || "—"),
	]);
	const testing_rows = (d.testing_requests || []).map((t) => [
		ic_doc_link("IC Testing Request", t.name, t.title || t.name),
		ic_status_pill(t.status),
		ic_esc(t.product || t.test_name || "—"),
	]);
	const doc_rows = (d.documents || []).map((doc) => [
		ic_doc_link("IC Document Request", doc.name, doc.title || doc.name),
		ic_status_pill(doc.status),
	]);
	const ticket_rows = (d.tickets || []).map((t) => [
		ic_doc_link("Helpdesk Ticket", t.name, t.subject || t.name),
		ic_status_pill(t.status),
		ic_esc(t.ticket_type || "—"),
		ic_esc(t.priority || "—"),
	]);
	const sample_rows = (d.samples || []).map((s) => [
		ic_doc_link("IC Sample Tracking", s.name, s.tracking_number || s.name),
		ic_status_pill(s.status),
		ic_esc(s.sample_description || "—"),
	]);
	const record_rows = (d.records || []).map((rec) => [
		ic_doc_link("IC Project Record", rec.name, rec.subject || rec.name),
		ic_esc(rec.record_type || "—"),
		ic_esc(rec.category || "—"),
	]);
	const contact_rows = (d.contacts || []).map((c) => {
		const full = [c.first_name, c.last_name].filter(Boolean).join(" ") || c.name;
		return [
			ic_doc_link("Contact", c.name, full),
			ic_esc(c.email_id || "—"),
			ic_esc(c.mobile_no || "—"),
			c.is_primary_contact ? __("Primary") : "",
		];
	});
	const lead_rows = (d.leads || []).map((l) => [
		ic_doc_link("Lead", l.name),
		ic_status_pill(l.status),
		ic_esc(l.ic_request_category || l.source || "—"),
	]);

	return `
		<div class="ic-customer-related">
			${cards}
			${ic_related_section(
				__("Quotations Shared"),
				ic_table([__("Quotation"), __("Status"), __("Amount"), __("Date")], quote_rows),
				__("No quotations for this customer"),
				customer
					? ic_list_link("Quotation", customer, null, {
							party_name: customer,
							quotation_to: "Customer",
					  })
					: ""
			)}
			${ic_related_section(
				__("Customer Projects"),
				ic_table([__("Project"), __("Status"), __("Stage"), __("Progress"), __("Deadline")], project_rows),
				__("No projects for this customer"),
				customer ? ic_list_link("Project", customer) : ""
			)}
			${ic_related_section(
				__("Invoices"),
				ic_table([__("Invoice"), __("Status"), __("Amount"), __("Outstanding"), __("Date"), __("Quotation")], invoice_rows),
				__("No invoices for this customer"),
				customer ? ic_list_link("Sales Invoice", customer) : ""
			)}
			${ic_related_section(
				__("Payments"),
				ic_table([__("Payment"), __("Status"), __("Type"), __("Amount"), __("Mode"), __("Date")], payment_rows),
				__("No payments for this customer"),
				customer
					? ic_list_link("Payment Entry", customer, null, {
							party: customer,
							party_type: "Customer",
					  })
					: ""
			)}
			${ic_related_section(
				__("Opportunities"),
				ic_table([__("Opportunity"), __("Status"), __("Amount"), __("Date")], opportunity_rows),
				__("No opportunities for this customer"),
				customer
					? ic_list_link("Opportunity", customer, null, {
							party_name: customer,
							opportunity_from: "Customer",
					  })
					: ""
			)}
			${ic_related_section(
				__("Testing Requests"),
				ic_table([__("Request"), __("Status"), __("Product / Test")], testing_rows),
				__("No testing requests"),
				customer ? ic_list_link("IC Testing Request", customer) : ""
			)}
			${ic_related_section(
				__("Document Requests"),
				ic_table([__("Document Request"), __("Status")], doc_rows),
				__("No document requests")
			)}
			${ic_related_section(
				__("Helpdesk Tickets"),
				ic_table([__("Ticket"), __("Status"), __("Type"), __("Priority")], ticket_rows),
				__("No helpdesk tickets"),
				customer ? ic_list_link("Helpdesk Ticket", customer) : ""
			)}
			${ic_related_section(
				__("Samples"),
				ic_table([__("Sample"), __("Status"), __("Description")], sample_rows),
				__("No samples")
			)}
			${ic_related_section(
				__("Project Records"),
				ic_table([__("Record"), __("Type"), __("Category")], record_rows),
				__("No project records")
			)}
			${ic_related_section(
				__("Contacts"),
				ic_table([__("Contact"), __("Email"), __("Mobile"), __("Role")], contact_rows),
				__("No contacts linked")
			)}
			${ic_related_section(
				__("Leads"),
				ic_table([__("Lead"), __("Status"), __("Category / Source")], lead_rows),
				__("No matching leads")
			)}
		</div>
	`;
}

// Project progress HTML
frappe.ui.form.on("Project", {
	refresh(frm) {
		const stages = [
			"Project Initiated","Customer Documents Pending","Documents Under Review","Application Submitted",
			"Sample Awaited","Sample Received","Sample Dispatched to Laboratory","Testing in Progress",
			"Report Awaited","Report Available","Certification in Progress","Certificate Available",
			"Delivered to Customer","Project Completed"
		];
		const current = frm.doc.ic_project_stage;
		const idx = stages.indexOf(current);
		let html = '<div class="ic-stage-tracker">';
		stages.forEach((s, i) => {
			let cls = "stage";
			if (i < idx) cls += " done";
			if (i === idx) cls += " active";
			html += `<span class="${cls}">${s}</span>`;
		});
		html += "</div>";
		html += `<div class="ic-progress" style="margin-top:12px;"><span style="width:${frm.doc.ic_progress_percentage||0}%"></span></div>`;
		frm.set_df_property("ic_progress_html", "options", html);

		frm.add_custom_button(__("Add Project Update"), () => {
			frappe.new_doc("IC Project Update", { project: frm.doc.name, progress_percentage: frm.doc.ic_progress_percentage, project_stage: frm.doc.ic_project_stage });
		}, __("Instacertify"));
		instacertify.add_helpdesk_buttons(frm, {
			project: frm.doc.name,
			customer: frm.doc.customer,
			channel: "Internal",
			subject: frm.doc.project_name ? `Project: ${frm.doc.project_name}` : "",
		});
	},
});

frappe.ui.form.on("IC Testing Request", {
	refresh(frm) {
		frm.set_query("laboratory", () => ({ filters: { status: "Active" } }));
		if (frm.doc.laboratory) {
			instacertify.load_testing_request_scope_options(frm);
		}
		if (!frm.is_new() && frm.doc.test_report) {
			frm.add_custom_button(__("Share with Customer"), () => {
				frappe.call({
					method: "instacertify.testing.events.share_report_with_customer",
					args: { testing_request: frm.doc.name },
					callback(r) {
						frappe.msgprint(`Report link: <a href="${r.message.url}" target="_blank">${r.message.url}</a>`);
						frm.reload_doc();
					},
				});
			}, __("Instacertify"));
		}
		if (!frm.is_new() && frm.doc.laboratory) {
			frm.add_custom_button(__("Buy Lab Service (PI)"), () => {
				frappe.call({
					method: "instacertify.accounting.consulting_billing.create_lab_purchase_invoice",
					args: {
						laboratory: frm.doc.laboratory,
						testing_request: frm.doc.name,
						project: frm.doc.project,
						amount: frm.doc.suggested_selling_price,
					},
					freeze: true,
					callback(r) {
						frappe.set_route("Form", "Purchase Invoice", r.message.name);
					},
				});
			}, __("Billing"));
		}
	},
	laboratory(frm) {
		frm.set_value("lab_test_scope", "");
		frm.set_value("lab_scope_row", "");
		frm.set_value("suggested_selling_price", 0);
		instacertify.load_testing_request_scope_options(frm);
	},
	lab_test_scope(frm) {
		if (!frm.doc.laboratory || !frm.doc.lab_test_scope) return;
		frappe.call({
			method: "instacertify.laboratory.api.get_lab_test_scope_details",
			args: {
				laboratory: frm.doc.laboratory,
				scope_key: frm.doc.lab_test_scope,
				scope_row: frm.doc.lab_scope_row,
			},
			callback(r) {
				const s = r.message;
				if (!s) return;
				frm.set_value("lab_scope_row", s.name);
				frm.set_value("test_name", s.test_name);
				if (s.applicable_standard) {
					frm.set_value("applicable_standard", s.applicable_standard);
				}
				frm.set_value("suggested_selling_price", s.selling_price);
				if (s.label && frm.doc.lab_test_scope !== s.label) {
					frm.set_value("lab_test_scope", s.label);
				}
			},
		});
	},
});

instacertify.load_testing_request_scope_options = function (frm) {
	if (!frm.doc.laboratory) {
		frm.set_df_property("lab_test_scope", "options", "");
		return;
	}
	frappe.call({
		method: "instacertify.laboratory.api.get_lab_test_scope_options",
		args: { laboratory: frm.doc.laboratory },
		callback(r) {
			const opt_str = (r.message || []).map((o) => o.value).join("\n");
			frm.set_df_property("lab_test_scope", "options", opt_str);
		},
	});
};

frappe.ui.form.on("IC Document Request", {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Send to Customer"), () => {
				frappe.call({
					method: "instacertify.documents.api.share_document_request",
					args: { document_request: frm.doc.name },
					callback(r) {
						frappe.msgprint(`Customer link: <a href="${r.message.url}" target="_blank">${r.message.url}</a>`);
						frm.reload_doc();
					},
				});
			}, __("Instacertify"));
		}
	},
	checklist_template(frm) {
		if (!frm.doc.checklist_template) return;
		frappe.call({
			method: "instacertify.documents.api.apply_checklist_template",
			args: { document_request: frm.doc.name, template: frm.doc.checklist_template },
			callback() { frm.reload_doc(); },
		});
	},
});

frappe.ui.form.on("IC Laboratory", {
	refresh(frm) {
		if (frm.is_new()) {
			frm.set_intro(
				__(
					"Register the lab, attach accreditation documents, and add each accredited test with Buying Price and Suggested Selling Price. These prices appear as a dropdown on Testing quotations."
				),
				"blue"
			);
		} else {
			frm.set_intro(
				__(
					"Laboratory Library — buy lab services via Purchase Invoice (non-stock, no warehouse). Link a Supplier, then create PI."
				),
				"blue"
			);
		}
		frm.add_custom_button(__("New Testing Quotation"), () => {
			frappe.new_doc("Quotation", {
				ic_quotation_type: "Testing",
				quotation_to: "Customer",
			});
		}, __("Instacertify"));
		if (!frm.is_new()) {
			frm.add_custom_button(__("Link / Create Supplier"), () => {
				frappe.call({
					method: "instacertify.accounting.consulting_billing.ensure_supplier_for_laboratory",
					args: { laboratory: frm.doc.name },
					freeze: true,
					callback(r) {
						frappe.show_alert({
							message: r.message.created
								? __("Supplier {0} created and linked", [r.message.supplier])
								: __("Supplier {0} linked", [r.message.supplier]),
							indicator: "green",
						});
						frm.reload_doc();
					},
				});
			}, __("Billing"));
			frm.add_custom_button(__("Buy Lab Service (Purchase Invoice)"), () => {
				frappe.prompt(
					[
						{
							fieldname: "amount",
							label: __("Amount"),
							fieldtype: "Currency",
							reqd: 1,
						},
						{
							fieldname: "description",
							label: __("Description"),
							fieldtype: "Small Text",
						},
					],
					(values) => {
						frappe.call({
							method: "instacertify.accounting.consulting_billing.create_lab_purchase_invoice",
							args: {
								laboratory: frm.doc.name,
								amount: values.amount,
								description: values.description,
							},
							freeze: true,
							callback(r) {
								frappe.set_route("Form", "Purchase Invoice", r.message.name);
							},
						});
					},
					__("Buy laboratory service"),
					__("Create Purchase Invoice")
				);
			}, __("Billing"));
		}
	},
});

frappe.ui.form.on("IC Laboratory Test Scope", {
	purchase_price(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		row.margin = (row.selling_price || 0) - (row.purchase_price || 0);
		frm.refresh_field("test_scopes");
	},
	selling_price(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		row.margin = (row.selling_price || 0) - (row.purchase_price || 0);
		frm.refresh_field("test_scopes");
	},
});

// --- Indian GST billing currency: India → INR, other country → USD (overridable) ---
instacertify.apply_billing_currency = function (frm, customer, opts) {
	opts = opts || {};
	if (!customer) return;
	if (frm.doc.ic_currency_manual && !opts.force) return;

	frappe.call({
		method: "instacertify.accounting.billing.get_billing_defaults",
		args: { customer },
		callback(r) {
			const d = r.message || {};
			if (!d.currency) return;
			const currencyField = opts.currency_field || "currency";
			if (frm.doc[currencyField] !== d.currency) {
				instacertify._auto_setting_currency = true;
				frm.set_value(currencyField, d.currency).then(() => {
					instacertify._auto_setting_currency = false;
				});
				frappe.show_alert({
					message: d.is_export
						? __("Export customer ({0}) — billing currency set to {1}. Change anytime if needed.", [
								d.country || __("Overseas"),
								d.currency,
							])
						: __("India customer — billing currency set to {0}.", [d.currency]),
					indicator: "blue",
				});
			}
			if (opts.on_defaults) opts.on_defaults(d);
		},
	});
};

frappe.ui.form.on("Customer", {
	ic_country(frm) {
		if (!frm.doc.ic_country) return;
		if (frm.doc.ic_currency_manual) return;
		const isIndia = frm.doc.ic_country === "India";
		const currency = isIndia ? "INR" : "USD";
		instacertify._auto_setting_currency = true;
		frm.set_value("default_currency", currency);
		frm.set_value("ic_primary_currency", currency).then(() => {
			instacertify._auto_setting_currency = false;
		});
		if (frm.doc.gst_category !== undefined) {
			if (!isIndia) {
				frm.set_value("gst_category", "Overseas");
			} else if (frm.doc.gst_category === "Overseas") {
				frm.set_value(
					"gst_category",
					frm.doc.gstin || frm.doc.ic_gst_number ? "Registered Regular" : "Unregistered"
				);
			}
		}
		frappe.show_alert({
			message: isIndia
				? __("Country India — default billing currency INR (GST as per Indian rules).")
				: __(
						"Country outside India — default billing currency USD. You can change to INR or another currency."
					),
			indicator: "blue",
		});
	},
	default_currency(frm) {
		if (instacertify._auto_setting_currency) return;
		if (frm.doc.default_currency) {
			frm.set_value("ic_currency_manual", 1);
		}
	},
	ic_primary_currency(frm) {
		if (instacertify._auto_setting_currency) return;
		if (frm.doc.ic_primary_currency && frm.doc.default_currency !== frm.doc.ic_primary_currency) {
			frm.set_value("default_currency", frm.doc.ic_primary_currency);
		}
	},
	ic_gst_number(frm) {
		if (frm.doc.ic_gst_number && frm.fields_dict.gstin) {
			frm.set_value("gstin", (frm.doc.ic_gst_number || "").toUpperCase());
		}
	},
	gstin(frm) {
		if (frm.doc.gstin && frm.fields_dict.ic_gst_number) {
			frm.set_value("ic_gst_number", (frm.doc.gstin || "").toUpperCase());
		}
	},
});

frappe.ui.form.on("Quotation", {
	party_name(frm) {
		if (frm.doc.quotation_to !== "Customer" || !frm.doc.party_name) return;
		instacertify.apply_billing_currency(frm, frm.doc.party_name);
	},
	currency(frm) {
		if (!frm.doc.currency || instacertify._auto_setting_currency) return;
		if (!frm.doc.ic_currency_manual) {
			frm.set_value("ic_currency_manual", 1);
		}
	},
	taxes_and_charges(frm) {
		if (instacertify._auto_setting_currency) return;
		if (frm.doc.taxes_and_charges && !frm.doc.ic_tax_manual) {
			frm.set_value("ic_tax_manual", 1);
		}
	},
});

frappe.ui.form.on("Sales Invoice", {
	setup(frm) {
		instacertify.hide_pos_on_sales_invoice(frm);
	},
	refresh(frm) {
		instacertify.hide_pos_on_sales_invoice(frm);
		instacertify.apply_consulting_no_warehouse(frm);
		frm.set_intro(
			__("Consulting billing: sell services to customers as non-stock items — warehouse is not required."),
			"blue"
		);
		if (!frm.is_new()) {
			instacertify.add_helpdesk_buttons(frm, {
				sales_invoice: frm.doc.name,
				customer: frm.doc.customer,
				project: frm.doc.project,
				channel: "Internal",
				ticket_type: "Billing",
				subject: `Invoice ${frm.doc.name}`,
			});
		}
	},
	customer(frm) {
		if (!frm.doc.customer) return;
		instacertify.apply_billing_currency(frm, frm.doc.customer);
	},
	currency(frm) {
		if (!frm.doc.currency || instacertify._auto_setting_currency) return;
		if (!frm.doc.ic_currency_manual) {
			frm.set_value("ic_currency_manual", 1);
		}
	},
	taxes_and_charges(frm) {
		if (frm.doc.taxes_and_charges && !frm.doc.ic_tax_manual) {
			frm.set_value("ic_tax_manual", 1);
		}
	},
	is_pos(frm) {
		// POS billing is disabled for Instacertify
		if (frm.doc.is_pos) {
			frm.set_value("is_pos", 0);
			frappe.show_alert({
				message: __("POS billing is disabled. Use standard Sales Invoice."),
				indicator: "orange",
			});
		}
	},
	update_stock(frm) {
		if (frm.doc.update_stock) {
			frm.set_value("update_stock", 0);
			frappe.show_alert({
				message: __("Stock update disabled for consulting service billing."),
				indicator: "orange",
			});
		}
	},
});

frappe.ui.form.on("Purchase Invoice", {
	refresh(frm) {
		instacertify.apply_consulting_no_warehouse(frm);
		frm.set_intro(
			__(
				"Buy lab/vendor services or organisational purchases as non-stock. Link Laboratory / Testing Request when buying lab work. Use Asset for company equipment."
			),
			"blue"
		);
		if (!frm.is_new()) {
			frm.add_custom_button(__("Create Asset"), () => {
				frappe.new_doc("Asset", {
					ic_purchase_invoice: frm.doc.name,
					supplier: frm.doc.supplier,
				});
			}, __("Billing"));
		}
	},
	update_stock(frm) {
		if (frm.doc.update_stock) {
			frm.set_value("update_stock", 0);
			frappe.show_alert({
				message: __("Stock update disabled — consulting purchases do not use warehouse."),
				indicator: "orange",
			});
		}
	},
	ic_laboratory(frm) {
		if (!frm.doc.ic_laboratory || frm.doc.supplier) return;
		frappe.call({
			method: "instacertify.accounting.consulting_billing.ensure_supplier_for_laboratory",
			args: { laboratory: frm.doc.ic_laboratory },
			callback(r) {
				if (r.message && r.message.supplier) {
					frm.set_value("supplier", r.message.supplier);
				}
			},
		});
	},
});

frappe.ui.form.on("Asset", {
	refresh(frm) {
		frm.set_intro(
			__("Organisational assets — purchase via Purchase Invoice, then record the asset here (not warehouse stock)."),
			"blue"
		);
	},
});

instacertify.apply_consulting_no_warehouse = function (frm) {
	if (frm.fields_dict.update_stock) {
		frm.set_df_property("update_stock", "hidden", 1);
		if (frm.doc.update_stock) {
			frm.set_value("update_stock", 0);
		}
	}
	(frm.doc.items || []).forEach((row) => {
		["warehouse", "target_warehouse", "from_warehouse"].forEach((f) => {
			if (row[f]) {
				frappe.model.set_value(row.doctype, row.name, f, null);
			}
		});
	});
};

instacertify.hide_pos_on_sales_invoice = function (frm) {
	["is_pos", "pos_profile"].forEach((f) => {
		if (frm.fields_dict[f]) {
			frm.set_df_property(f, "hidden", 1);
			frm.set_df_property(f, "read_only", 1);
		}
	});
	if (frm.doc.is_pos) {
		frm.set_value("is_pos", 0);
	}
};

// Also inject when workspace page is shown via frappe.pages
$(document).ready(function () {
	const tryInject = () => {
		const route = frappe.get_route_str ? frappe.get_route_str() : (frappe.get_route() || []).join("/");
		if ((route || "").includes("Instacertify")) {
			const $page = $(".workspace-body, .workspace-sidebar + .layout-main-section, .page-body, .workspace-page").first();
			if ($page.length && !$page.find(".ic-greeting").length) {
				instacertify.render_home_banner($page);
			}
		}
	};
	setTimeout(tryInject, 800);
	setTimeout(tryInject, 2000);
});

// --- Lead capture: mandatory name, India-first country, editable source/type ---
frappe.ui.form.on("Lead", {
	setup(frm) {
		frm.set_query("country", () => ({
			query: "instacertify.crm.dashboard.search_country_india_first",
		}));
		frm.set_query("ic_lead_source_detail", () => ({
			filters: { is_active: 1 },
		}));
		frm.set_query("ic_project_type", () => ({
			filters: { is_active: 1 },
		}));
	},
	refresh(frm) {
		frm.set_df_property("email_id", "reqd", 0);
		frm.set_df_property("mobile_no", "reqd", 0);
		frm.set_df_property("phone", "reqd", 0);
		frm.set_df_property("ic_party_name", "reqd", 1);
		if (!frm.doc.country && frm.is_new()) {
			frm.set_value("country", "India");
		}
		if (!frm.doc.ic_party_name) {
			const party = frm.doc.company_name || frm.doc.lead_name || frm.doc.first_name;
			if (party) frm.set_value("ic_party_name", party);
		}
		if (!frm.is_new()) {
			instacertify.add_helpdesk_buttons(frm, {
				lead: frm.doc.name,
				contact_person: frm.doc.lead_name || frm.doc.ic_party_name || frm.doc.company_name,
				contact_email: frm.doc.email_id,
				contact_phone: frm.doc.mobile_no || frm.doc.phone,
				channel: "Internal",
			});
		}
	},
	ic_party_name(frm) {
		const party = (frm.doc.ic_party_name || "").trim();
		if (!party) return;
		if (!frm.doc.company_name) {
			frm.set_value("company_name", party);
		}
		if (!frm.doc.first_name) {
			frm.set_value("first_name", party.split(/\s+/)[0]);
		}
	},
	ic_lead_source_detail(frm) {
		const src = frm.doc.ic_lead_source_detail;
		if (src !== "Consultant" && src !== "Reference") {
			frm.set_value("ic_consultant_referral", "");
		}
	},
});

// --- Project AMC on completion ---
frappe.ui.form.on("Project", {
	ic_project_stage(frm) {
		if (frm.doc.ic_project_stage !== "Project Completed") return;
		if (frm.doc.ic_requires_amc) return;
		frappe.confirm(
			__("Does this completed project require AMC / renewal follow-up?"),
			() => {
				frappe.prompt(
					[
						{
							fieldname: "contact_date",
							fieldtype: "Date",
							label: __("Next AMC Contact Date"),
							reqd: 1,
							default: frappe.datetime.add_months(frappe.datetime.get_today(), 12),
							description: __("Reminders go to Admin & Sales Manager 1 month before this date"),
						},
					],
					(values) => {
						frappe.call({
							method: "instacertify.project.events.schedule_project_amc",
							args: { project: frm.doc.name, contact_date: values.contact_date },
							freeze: true,
							callback(r) {
								frm.reload_doc();
								frappe.show_alert({
									message: __("AMC scheduled for {0} (reminder {1})", [
										r.message.contact_date,
										r.message.reminder_date,
									]),
									indicator: "green",
								});
							},
						});
					},
					__("Schedule AMC"),
					__("Save")
				);
			},
			() => {
				frm.set_value("ic_requires_amc", 0);
				frm.set_value("ic_amc_status", "Not Applicable");
			}
		);
	},
});

// Sample custody — location management + list indicators
frappe.listview_settings["IC Sample Tracking"] = {
	add_fields: ["sample_location", "status", "tracking_number", "customer"],
	get_indicator(doc) {
		const loc = doc.sample_location || doc.status || "";
		const colors = {
			"With Customer": "blue",
			"In Transit to Office": "orange",
			"At Instacertify Office": "green",
			"In Transit to Lab": "orange",
			"At Laboratory": "purple",
			"At Instacertify Storage": "teal",
			Discarded: "red",
			"Sample Awaited": "blue",
			"Sample Received": "green",
		};
		return [__(loc || "Unset"), colors[loc] || "gray", "sample_location,=," + (doc.sample_location || "")];
	},
	onload(listview) {
		const locs = [
			"In Transit to Office",
			"At Instacertify Office",
			"In Transit to Lab",
			"At Laboratory",
			"At Instacertify Storage",
			"Discarded",
		];
		locs.forEach((loc) => {
			listview.page.add_inner_button(__(loc), () => {
				frappe.set_route("List", "IC Sample Tracking", { sample_location: loc });
			}, __("Location"));
		});
	},
};

frappe.ui.form.on("IC Sample Tracking", {
	status(frm) {
		const map = {
			"Sample Awaited": "With Customer",
			"Sample Received": "At Instacertify Office",
			"In Transit to Office": "In Transit to Office",
			"At Instacertify Office": "At Instacertify Office",
			"In Transit to Lab": "In Transit to Lab",
			"At Laboratory": "At Laboratory",
			"Sample Dispatched to Laboratory": "In Transit to Lab",
			"At Instacertify Storage": "At Instacertify Storage",
			Discarded: "Discarded",
		};
		if (map[frm.doc.status] && frm.doc.sample_location !== map[frm.doc.status]) {
			frm.set_value("sample_location", map[frm.doc.status]);
		}
	},
	sample_location(frm) {
		const map = {
			"With Customer": "Sample Awaited",
			"In Transit to Office": "In Transit to Office",
			"At Instacertify Office": "Sample Received",
			"In Transit to Lab": "In Transit to Lab",
			"At Laboratory": "At Laboratory",
			"At Instacertify Storage": "At Instacertify Storage",
			Discarded: "Discarded",
		};
		if (map[frm.doc.sample_location] && frm.doc.status !== map[frm.doc.sample_location]) {
			frm.set_value("status", map[frm.doc.sample_location]);
		}
	},
	refresh(frm) {
		const locs = [
			"In Transit to Office",
			"At Instacertify Office",
			"In Transit to Lab",
			"At Laboratory",
			"At Instacertify Storage",
			"Discarded",
		];
		locs.forEach((label) => {
			frm.add_custom_button(__(label), () => {
				if (label === "Discarded") {
					frappe.prompt(
						[
							{
								fieldname: "discard_reason",
								fieldtype: "Small Text",
								label: __("Discard Reason"),
								reqd: 1,
							},
						],
						(values) => {
							frappe.call({
								method: "instacertify.testing.events.set_sample_location",
								args: {
									sample: frm.doc.name,
									location: label,
									discard_reason: values.discard_reason,
								},
								freeze: true,
								callback() {
									frm.reload_doc();
								},
							});
						},
						__("Discard Sample"),
						__("Discard")
					);
					return;
				}
				frappe.call({
					method: "instacertify.testing.events.set_sample_location",
					args: { sample: frm.doc.name, location: label },
					freeze: true,
					callback() {
						frm.reload_doc();
					},
				});
			}, __("Location"));
		});
	},
});

// Opportunity — raise ticket from deal context
frappe.ui.form.on("Opportunity", {
	refresh(frm) {
		if (frm.is_new()) return;
		instacertify.add_helpdesk_buttons(frm, {
			opportunity: frm.doc.name,
			customer: frm.doc.opportunity_from === "Customer" ? frm.doc.party_name : null,
			lead: frm.doc.opportunity_from === "Lead" ? frm.doc.party_name : null,
			channel: "Internal",
			subject: frm.doc.title || `Opportunity ${frm.doc.name}`,
		});
	},
});
