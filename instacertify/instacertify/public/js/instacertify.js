/*! Instacertify Desk JS */
frappe.provide("instacertify");

instacertify.brand = {
	primary: "#065175",
	accent: "#EC6820",
	logo: "/assets/instacertify/images/instacertify_logo.png",
	icon: "/assets/instacertify/images/instacertify_icon.png",
	app_logo: "/assets/instacertify/images/instacertify_app_logo.png",
	favicon: "/assets/instacertify/images/favicon-32.png",
};

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
			frm.add_custom_button(__("Share with Customer"), () => {
				frappe.call({
					method: "instacertify.quotation.events.share_with_customer",
					args: { quotation: frm.doc.name },
					freeze: true,
					callback(r) {
						frm.reload_doc();
						frappe.msgprint({
							title: __("Customer Link"),
							message: `__("Secure link"): <a href="${r.message.url}" target="_blank">${r.message.url}</a>`,
							indicator: "green",
						});
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

			if (frm.doc.ic_workflow_status === "Accepted") {
				frm.add_custom_button(__("Start Project"), () => {
					frappe.call({
						method: "instacertify.quotation.events.start_project_from_quotation",
						args: { quotation: frm.doc.name },
						freeze: true,
						callback(r) {
							frappe.set_route("Form", "Project", r.message.project);
						},
					});
				}, __("Instacertify"));
			}
		}

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
		if (frm.is_new() && !frm.doc.ic_quotation_type) return;
	},

	ic_quotation_template(frm) {
		if (!frm.doc.ic_quotation_template || (frm.is_new() && !frm.doc.name)) {
			if (!frm.doc.ic_quotation_template) return;
		}
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
	if (row.per_unit_charges) {
		frappe.model.set_value(cdt, cdn, "testing_charges", flt(row.per_unit_charges) * units);
	}
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

// Customer history
frappe.ui.form.on("Customer", {
	refresh(frm) {
		if (frm.doc.name) {
			frappe.call({
				method: "instacertify.crm.events.get_customer_history",
				args: { customer: frm.doc.name },
				callback(r) {
					const d = r.message || {};
					const html = `
						<div class="ic-summary-grid">
							<div class="ic-summary-card"><div class="label">Leads</div><div class="value">${(d.leads||[]).length}</div></div>
							<div class="ic-summary-card"><div class="label">Quotations</div><div class="value">${(d.quotations||[]).length}</div></div>
							<div class="ic-summary-card accent"><div class="label">Accepted</div><div class="value">${(d.accepted_quotations||[]).length}</div></div>
							<div class="ic-summary-card"><div class="label">Active Projects</div><div class="value">${(d.active_projects||[]).length}</div></div>
							<div class="ic-summary-card"><div class="label">Testing</div><div class="value">${(d.testing_requests||[]).length}</div></div>
							<div class="ic-summary-card"><div class="label">Invoices</div><div class="value">${(d.invoices||[]).length}</div></div>
							<div class="ic-summary-card accent"><div class="label">Outstanding</div><div class="value" style="font-size:1.1rem;">${format_currency(d.outstanding_amount||0)}</div></div>
						</div>
						<div class="text-muted">Contacts: ${(d.contacts||[]).length} · Documents: ${(d.documents||[]).length} · Records: ${(d.records||[]).length}</div>
					`;
					frm.set_df_property("ic_history_html", "options", html);
				},
			});
		}
	},
});

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
	},
});

frappe.ui.form.on("IC Testing Request", {
	refresh(frm) {
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
	},
});

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
		// Margin calculation hint for admin
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
