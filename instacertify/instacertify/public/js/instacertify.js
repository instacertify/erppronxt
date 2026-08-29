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

/** Prefer ERPNext File Library (internal drive) over pasted URLs / Google Drive. */
instacertify.attach_options = {
	allow_web_link: false,
	allow_google_drive: false,
};

instacertify.get_attach_upload_notes = function () {
	return __(
		"Use My Device or Library (internal drive). Web links and Google Drive are disabled."
	);
};

instacertify.open_file_manager = function () {
	frappe.set_route("List", "File");
};

/** Append a File Manager shortcut under Attach fields in dialogs. */
instacertify.add_file_manager_hint = function (dialog, fieldname) {
	try {
		const field = dialog.fields_dict && dialog.fields_dict[fieldname];
		if (!field || !field.$wrapper) return;
		if (field.$wrapper.find(".ic-open-file-manager").length) return;
		const $hint = $(
			`<div class="ic-open-file-manager text-muted" style="margin-top:6px;font-size:12px;">
				<a href="#" class="ic-file-mgr-link">${__("Open File Manager")}</a>
				— ${__("browse or upload once, then pick from Library")}
			</div>`
		);
		field.$wrapper.append($hint);
		$hint.find(".ic-file-mgr-link").on("click", (e) => {
			e.preventDefault();
			dialog.hide();
			instacertify.open_file_manager();
		});
	} catch (e) {
		/* ignore */
	}
};

instacertify.patch_file_uploader_for_internal_drive = function () {
	if (frappe.ui.form.ControlAttach && !frappe.ui.form.ControlAttach.prototype.__ic_internal_drive) {
		const orig = frappe.ui.form.ControlAttach.prototype.set_upload_options;
		frappe.ui.form.ControlAttach.prototype.set_upload_options = function () {
			orig.apply(this, arguments);
			this.upload_options = this.upload_options || {};
			this.upload_options.allow_web_link = false;
			this.upload_options.allow_google_drive = false;
			if (!this.upload_options.upload_notes) {
				this.upload_options.upload_notes = instacertify.get_attach_upload_notes();
			}
		};
		frappe.ui.form.ControlAttach.prototype.__ic_internal_drive = true;
	}
	if (frappe.ui.form.ControlAttachImage && !frappe.ui.form.ControlAttachImage.prototype.__ic_internal_drive) {
		const origImg = frappe.ui.form.ControlAttachImage.prototype.set_upload_options;
		frappe.ui.form.ControlAttachImage.prototype.set_upload_options = function () {
			origImg.apply(this, arguments);
			this.upload_options = this.upload_options || {};
			this.upload_options.allow_web_link = false;
			this.upload_options.allow_google_drive = false;
		};
		frappe.ui.form.ControlAttachImage.prototype.__ic_internal_drive = true;
	}
};

/** Quotation naming: Service/Consulting → QTN-SRV, Testing → QTN-TST, else QTN-OTH */
instacertify.quotation_series_for_type = function (quotation_type) {
	const t = (quotation_type || "").trim();
	if (t === "Testing") return "QTN-TST-.#####";
	if (t === "Service" || t === "Consulting") return "QTN-SRV-.#####";
	return "QTN-OTH-.#####";
};

instacertify.apply_quotation_naming_series = function (frm) {
	if (!frm || !frm.is_new || !frm.is_new()) return;
	const wanted = instacertify.quotation_series_for_type(frm.doc.ic_quotation_type);
	if (frm.doc.naming_series !== wanted) {
		frm.set_value("naming_series", wanted);
	}
};

/** Find a node in the light DOM or inside open shadow roots (Custom HTML Blocks). */
instacertify.query_deep = function (selector, root) {
	const scope = root || document;
	try {
		const hit = scope.querySelector(selector);
		if (hit) return hit;
	} catch (e) {
		/* ignore */
	}
	const walk = scope.querySelectorAll ? scope.querySelectorAll("*") : [];
	for (let i = 0; i < walk.length; i++) {
		const sr = walk[i].shadowRoot;
		if (!sr) continue;
		const nested = instacertify.query_deep(selector, sr);
		if (nested) return nested;
	}
	return null;
};

instacertify.has_home_root = function () {
	return !!instacertify.query_deep("#ic-home-root");
};

/** Frappe 16 desk URL for Instacertify Home (slug path, not /Workspaces/...). */
instacertify.home_desk_path = function () {
	const home =
		(frappe.boot.instacertify && frappe.boot.instacertify.default_workspace) || "Instacertify Home";
	const slug = frappe.router && frappe.router.slug ? frappe.router.slug(home) : "instacertify-home";
	return "/desk/" + slug;
};

instacertify.go_home = function () {
	const home =
		(frappe.boot.instacertify && frappe.boot.instacertify.default_workspace) || "Instacertify Home";
	localStorage.setItem("current_page", home);
	localStorage.setItem("is_current_page_public", "true");
	const slug =
		frappe.router && frappe.router.slug ? frappe.router.slug(home) : "instacertify-home";
	// Use slug so /desk/instacertify-home resolves via frappe.workspaces — never Page "workspace"
	if (frappe.workspaces && frappe.workspaces[slug]) {
		frappe.set_route(slug);
	} else {
		frappe.set_route(slug);
	}
};

/** Land every user on Instacertify Home dashboard after login / desk boot. */
$(document).on("app_ready", function () {
	try {
		instacertify.patch_file_uploader_for_internal_drive();
	} catch (e) {
		/* ignore */
	}
	try {
		const home =
			(frappe.boot.instacertify && frappe.boot.instacertify.default_workspace) || "Instacertify Home";
		const route = frappe.get_route_str ? frappe.get_route_str() : "";
		const isDeskRoot =
			!route ||
			route === "Workspaces" ||
			route === "workspace" ||
			route === "workspaces" ||
			route === "desktop" ||
			route === "Home" ||
			route === "Workspaces/Home" ||
			route === "Welcome Workspace" ||
			route === "Workspaces/Welcome Workspace";
		// Also recover from boot.home_page mistakenly set to legacy "workspace"
		if (isDeskRoot || (frappe.boot && frappe.boot.home_page === "workspace")) {
			instacertify.go_home();
		} else if (!localStorage.getItem("current_page")) {
			localStorage.setItem("current_page", home);
		}
	} catch (e) {
		/* ignore */
	}
});

/** Never leave users on the generic ERPNext Home workspace (wrong landing / empty). */
$(document).on("page-change", function () {
	try {
		const route = frappe.get_route ? frappe.get_route() : [];
		if (
			(route[0] === "Workspaces" && (route[1] === "Home" || route[1] === "Welcome Workspace")) ||
			(route[0] === "workspace" && (!route[1] || route[1] === "Home")) ||
			route[0] === "workspace" ||
			route[0] === "workspaces" ||
			route[0] === "desktop"
		) {
			instacertify.go_home();
		}
	} catch (e) {
		/* ignore */
	}
});

/** Quick lead capture — name + phone, optional need/source, save in seconds. */
instacertify.open_quick_lead = function (opts) {
	opts = opts || {};
	const tomorrow = frappe.datetime.add_days(frappe.datetime.get_today(), 1);
	const d = new frappe.ui.Dialog({
		title: __("Capture a Lead"),
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "ic_zippy_hint",
				options:
					'<div class="ic-quick-lead-hint">Name is enough to start. Phone helps you call back. Save and keep moving.</div>',
			},
			{
				fieldname: "ic_party_name",
				fieldtype: "Data",
				label: __("Name / company"),
				reqd: 1,
				default: opts.ic_party_name || "",
			},
			{
				fieldname: "mobile_no",
				fieldtype: "Data",
				label: __("Mobile"),
				options: "Phone",
				default: opts.mobile_no || "",
			},
			{
				fieldname: "email_id",
				fieldtype: "Data",
				label: __("Email (optional)"),
				options: "Email",
				default: opts.email_id || "",
			},
			{
				fieldname: "ic_lead_source_detail",
				fieldtype: "Link",
				label: __("Source"),
				options: "IC Lead Source",
				default: opts.ic_lead_source_detail || "",
			},
			{
				fieldname: "ic_project_type",
				fieldtype: "Link",
				label: __("Project type"),
				options: "IC Project Type",
				default: opts.ic_project_type || "",
			},
			{
				fieldname: "ic_call_remarks",
				fieldtype: "Small Text",
				label: __("What they need"),
				default: opts.ic_call_remarks || "",
			},
			{
				fieldname: "ic_next_contact_date",
				fieldtype: "Date",
				label: __("Call back on"),
				default: opts.ic_next_contact_date || tomorrow,
			},
			{
				fieldname: "assign_to_me",
				fieldtype: "Check",
				label: __("Assign to me"),
				default: 1,
			},
		],
		primary_action_label: __("Save Lead"),
		secondary_action_label: __("Save & another"),
		primary_action(values) {
			instacertify._save_quick_lead(d, values, { another: false, on_done: opts.on_done });
		},
	});
	d.$wrapper.addClass("ic-quick-lead-dialog");
	d.set_secondary_action(() => {
		const values = d.get_values();
		if (!values) return;
		instacertify._save_quick_lead(d, values, {
			another: true,
			on_done: opts.on_done,
		});
	});
	d.$wrapper.find(".modal-footer").prepend(
		`<button type="button" class="btn btn-default btn-sm ic-open-full-lead" style="margin-right:auto;">${__("Full form")}</button>`
	);
	d.$wrapper.find(".ic-open-full-lead").on("click", () => {
		d.hide();
		frappe.new_doc("Lead");
	});
	d.show();
	setTimeout(() => {
		d.get_field("ic_party_name") && d.get_field("ic_party_name").$input.focus();
	}, 200);
};

instacertify._save_quick_lead = function (dialog, values, opts) {
	opts = opts || {};
	frappe.call({
		method: "instacertify.crm.events.create_quick_lead",
		args: values,
		freeze: true,
		freeze_message: __("Saving lead…"),
		callback(r) {
			const name = r.message && r.message.name;
			frappe.show_alert({
				message: __("Lead saved{0}", [name ? ": " + name : " — nice!"]),
				indicator: "green",
			});
			if (opts.on_done) opts.on_done(name);
			if (opts.another) {
				dialog.set_values({
					ic_party_name: "",
					mobile_no: "",
					email_id: "",
					ic_call_remarks: "",
					ic_next_contact_date: frappe.datetime.add_days(frappe.datetime.get_today(), 1),
					assign_to_me: 1,
				});
				setTimeout(() => {
					dialog.get_field("ic_party_name") && dialog.get_field("ic_party_name").$input.focus();
				}, 100);
				return;
			}
			dialog.hide();
			if (name) frappe.set_route("Form", "Lead", name);
		},
	});
};

/** Open a new Helpdesk Ticket with CRM context defaults. */
instacertify.raise_helpdesk_ticket = function (defaults) {
	defaults = defaults || {};
	frappe.new_doc("Helpdesk Ticket", defaults);
};

/** Quick expense filing dialog — travel / petty / office for every user. */
instacertify.open_expense_file = function (opts) {
	opts = opts || {};
	const d = new frappe.ui.Dialog({
		title: __("File an Expense"),
		fields: [
			{
				fieldname: "title",
				fieldtype: "Data",
				label: __("Title"),
				reqd: 1,
				default: opts.title || "",
			},
			{
				fieldname: "category",
				fieldtype: "Select",
				label: __("Category"),
				options: "Travel\nPetty Cash\nOffice\nConveyance\nLodging\nMeals\nCommunication\nOther",
				reqd: 1,
				default: opts.category || "Travel",
			},
			{
				fieldname: "expense_date",
				fieldtype: "Date",
				label: __("Expense Date"),
				reqd: 1,
				default: frappe.datetime.get_today(),
			},
			{
				fieldname: "amount",
				fieldtype: "Currency",
				label: __("Amount"),
				reqd: 1,
			},
			{
				fieldname: "payment_mode",
				fieldtype: "Select",
				label: __("Paid By"),
				options: "Self\nCompany Card\nAdvance\nOther",
				default: "Self",
			},
			{
				fieldname: "description",
				fieldtype: "Small Text",
				label: __("Description"),
				reqd: 1,
			},
			{
				fieldname: "receipt",
				fieldtype: "Attach",
				label: __("Receipt / Bill"),
				description: __(
					"Select from My Device or File Library (internal drive). No web / Drive URLs."
				),
				options: instacertify.attach_options,
			},
			{
				fieldname: "project",
				fieldtype: "Link",
				label: __("Project (optional)"),
				options: "Project",
			},
		],
		primary_action_label: __("Save Expense"),
		primary_action(values) {
			frappe.call({
				method: "instacertify.expenses.api.create_expense_claim",
				args: values,
				freeze: true,
				freeze_message: __("Saving expense…"),
				callback(r) {
					d.hide();
					const name = r.message && r.message.name;
					frappe.show_alert({
						message: __("Expense saved: {0}", [name || ""]),
						indicator: "green",
					});
					if (opts.on_done) opts.on_done(name);
					else if (name) frappe.set_route("Form", "IC Expense Claim", name);
				},
			});
		},
	});
	d.$wrapper.find(".modal-footer").prepend(
		`<button type="button" class="btn btn-default btn-sm ic-open-expense-list" style="margin-right:auto;">${__("My Expenses")}</button>`
	);
	d.$wrapper.find(".ic-open-expense-list").on("click", () => {
		d.hide();
		frappe.set_route("List", "IC Expense Claim");
	});
	d.show();
	instacertify.add_file_manager_hint(d, "receipt");
};

/** Upload dialog → create/update IC Quotation Template with format file. */
instacertify.open_quote_format_upload = function (opts) {
	opts = opts || {};
	const d = new frappe.ui.Dialog({
		title: __("Upload Quote Format / Template"),
		fields: [
			{
				fieldname: "template_name",
				fieldtype: "Data",
				label: __("Template Name"),
				reqd: 1,
				default: opts.template_name || "",
			},
			{
				fieldname: "quotation_type",
				fieldtype: "Select",
				label: __("Quote Type"),
				options: "Consulting\nTesting\nRenewal\nService\nOther\nMultiple Products / Multiple Services",
				reqd: 1,
				default: opts.quotation_type || "Consulting",
			},
			{
				fieldname: "service_family",
				fieldtype: "Data",
				label: __("Service Family / Subtype"),
				description: __("e.g. BIS CRS, TEC, EMC"),
			},
			{
				fieldname: "file",
				fieldtype: "Attach",
				label: __("Quote Format File"),
				reqd: 1,
				description: __(
					"Select PDF/DOCX/HTML from My Device or File Library (internal drive)."
				),
				options: instacertify.attach_options,
			},
			{
				fieldname: "template_notes",
				fieldtype: "Small Text",
				label: __("Notes"),
			},
		],
		primary_action_label: __("Save to Library"),
		primary_action(values) {
			frappe.call({
				method: "instacertify.setup.library_upload.create_quote_format_from_upload",
				args: {
					template_name: values.template_name,
					quotation_type: values.quotation_type,
					file_url: values.file,
					service_family: values.service_family,
					template_notes: values.template_notes,
				},
				freeze: true,
				freeze_message: __("Saving quote format…"),
				callback(r) {
					d.hide();
					frappe.show_alert({
						message: __("Quote format saved: {0}", [r.message.template]),
						indicator: "green",
					});
					if (opts.on_done) opts.on_done(r.message.template);
					else frappe.set_route("Form", "IC Quotation Template", r.message.template);
				},
			});
		},
	});
	d.$wrapper.find(".modal-footer").prepend(
		`<button type="button" class="btn btn-default btn-sm ic-dl-quote-tpl" style="margin-right:auto;">${__("Download Upload Template")}</button>`
	);
	d.$wrapper.find(".ic-dl-quote-tpl").on("click", () => {
		frappe.call({
			method: "instacertify.setup.library_upload.download_quote_format_upload_template",
			callback(r) {
				const m = r.message || {};
				if (m.file_url) window.open(m.file_url, "_blank");
			},
		});
	});
	d.show();
	instacertify.add_file_manager_hint(d, "file");
};

/** Upload dialog → create/update IC Laboratory with name + scope file. */
instacertify.open_laboratory_upload = function (opts) {
	opts = opts || {};
	const d = new frappe.ui.Dialog({
		title: __("Upload Laboratory / Scope"),
		fields: [
			{
				fieldname: "laboratory_name",
				fieldtype: "Data",
				label: __("Laboratory Name"),
				reqd: 1,
				default: opts.laboratory_name || "",
			},
			{
				fieldname: "location",
				fieldtype: "Data",
				label: __("Location"),
				default: opts.location || "",
			},
			{
				fieldname: "accreditation_scope",
				fieldtype: "Text",
				label: __("Accreditation Scope (text)"),
				description: __("Describe tests / standards covered"),
			},
			{
				fieldname: "scope_file",
				fieldtype: "Attach",
				label: __("Scope Sheet / PDF"),
				description: __(
					"Select from My Device or File Library (internal drive). No web / Drive URLs."
				),
				options: instacertify.attach_options,
			},
			{
				fieldname: "contact_person",
				fieldtype: "Data",
				label: __("Contact Person"),
			},
			{
				fieldname: "email",
				fieldtype: "Data",
				label: __("Email"),
				options: "Email",
			},
			{
				fieldname: "phone",
				fieldtype: "Data",
				label: __("Phone"),
				options: "Phone",
			},
		],
		primary_action_label: __("Save to Library"),
		primary_action(values) {
			if (!values.accreditation_scope && !values.scope_file) {
				frappe.msgprint(__("Add scope text or upload a scope file."));
				return;
			}
			frappe.call({
				method: "instacertify.setup.library_upload.create_laboratory_from_upload",
				args: values,
				freeze: true,
				freeze_message: __("Saving laboratory…"),
				callback(r) {
					d.hide();
					frappe.show_alert({
						message: __("Laboratory saved: {0}", [r.message.laboratory_name]),
						indicator: "green",
					});
					if (opts.on_done) opts.on_done(r.message.laboratory);
					else frappe.set_route("Form", "IC Laboratory", r.message.laboratory);
				},
			});
		},
	});
	d.show();
	instacertify.add_file_manager_hint(d, "scope_file");
};

instacertify.open_lab_scope_csv_import = function (frm) {
	const d = new frappe.ui.Dialog({
		title: __("Import Laboratory Scope CSV"),
		fields: [
			{
				fieldname: "help",
				fieldtype: "HTML",
				options: `<p class="text-muted">${__(
					"CSV headers: test_name, applicable_standard, category, selling_price, purchase_price"
				)}</p>`,
			},
			{
				fieldname: "file",
				fieldtype: "Attach",
				label: __("CSV File"),
				reqd: 1,
				description: __(
					"Select CSV from My Device or File Library (internal drive)."
				),
				options: instacertify.attach_options,
			},
		],
		primary_action_label: __("Import"),
		primary_action(values) {
			frappe.call({
				method: "instacertify.setup.library_upload.import_laboratory_scopes_csv",
				args: { laboratory: frm.doc.name, file_url: values.file },
				freeze: true,
				callback(r) {
					d.hide();
					frappe.show_alert({
						message: __("Added {0} scope rows", [r.message.added]),
						indicator: "green",
					});
					frm.reload_doc();
				},
			});
		},
	});
	d.$wrapper.find(".modal-footer").prepend(
		`<button type="button" class="btn btn-default btn-sm ic-dl-scope-tpl" style="margin-right:auto;">${__("Download CSV Template")}</button>`
	);
	d.$wrapper.find(".ic-dl-scope-tpl").on("click", () => {
		frappe.call({
			method: "instacertify.setup.library_upload.download_lab_scope_template",
			callback(r) {
				const m = r.message || {};
				if (m.file_url) window.open(m.file_url, "_blank");
			},
		});
	});
	d.show();
	instacertify.add_file_manager_hint(d, "file");
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
	// Prefer the Custom HTML Block home dashboard when present (incl. shadow DOM).
	if (!wrapper || wrapper.find("#ic-home-root, .ic-greeting").length || instacertify.has_home_root()) {
		instacertify.bind_summary_card_clicks(document);
		return;
	}
	const html = `
		<div class="ic-greeting">
			<div class="ic-greeting-brand">Insta<span>certify</span></div>
			<h2>${frappe.utils.escape_html(instacertify.greeting())}</h2>
			<div class="ic-datetime">
				<span class="ic-date">${moment().format("dddd, D MMMM YYYY")}</span>
				&nbsp;·&nbsp;
				<span class="ic-time">${moment().format("h:mm A")}</span>
			</div>
		</div>
		<div class="ic-summary-grid" id="ic-summary-grid"></div>
		<div class="ic-project-section-head">
			<h3>${__("Ongoing Projects")}</h3>
			<a class="ic-view-all" href="/app/project-board">${__("Open tile board")}</a>
		</div>
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

/** KPI tile → filtered list. Used by Home summary cards and workspace HTML. */
instacertify.kpi_routes = function () {
	const today = frappe.datetime.get_today();
	const week_start = frappe.datetime.add_days(today, -6);
	const month_start = moment(today).startOf("month").format("YYYY-MM-DD");
	const deadline_end = frappe.datetime.add_days(today, 14);
	const amc_end = frappe.datetime.add_days(today, 31);
	return {
		"New Leads": { doctype: "Lead", filters: { status: "Lead" } },
		"Active Leads": {
			doctype: "Lead",
			filters: { status: ["in", ["Open", "Replied", "Opportunity"]] },
		},
		"Leads to Contact": {
			doctype: "Lead",
			filters: {
				status: ["not in", ["Converted", "Do Not Contact"]],
				ic_next_contact_date: ["<=", today],
			},
		},
		"Leads This Week": { doctype: "Lead", filters: { creation: [">=", week_start] } },
		"Leads This Month": { doctype: "Lead", filters: { creation: [">=", month_start] } },
		"This Week": { doctype: "Lead", filters: { creation: [">=", week_start] } },
		"Last 7 Days": { doctype: "Lead", filters: { creation: [">=", week_start] } },
		"This Month": { doctype: "Lead", filters: { creation: [">=", month_start] } },
		"Last 30 Days": {
			doctype: "Lead",
			filters: { creation: [">=", frappe.datetime.add_days(today, -29)] },
		},
		"Quotations Sent": {
			doctype: "Quotation",
			filters: {
				ic_workflow_status: ["in", ["Shared with Customer", "Customer Review"]],
			},
		},
		"Awaiting Response": {
			doctype: "Quotation",
			filters: {
				ic_workflow_status: ["in", ["Shared with Customer", "Customer Review"]],
			},
		},
		"Quotations Accepted": {
			doctype: "Quotation",
			filters: { ic_workflow_status: "Accepted" },
		},
		"Active Projects": {
			doctype: "Project",
			filters: { status: ["not in", ["Completed", "Cancelled"]] },
		},
		"Pending Tasks": {
			doctype: "Task",
			filters: { status: ["in", ["Open", "Working"]] },
		},
		"Open Tickets": {
			doctype: "Helpdesk Ticket",
			filters: { status: ["in", ["Open", "In Progress", "Waiting on Customer"]] },
		},
		"Open Complaints": {
			doctype: "Helpdesk Ticket",
			filters: {
				status: ["in", ["Open", "In Progress", "Waiting on Customer"]],
				ticket_type: "Complaint",
			},
		},
		"Pending Documents": {
			doctype: "IC Document Request",
			filters: { status: ["in", ["Sent to Customer", "Partially Uploaded"]] },
		},
		"Testing Requests": {
			doctype: "IC Testing Request",
			filters: { status: ["not in", ["Report Shared with Customer"]] },
		},
		"Upcoming Deadlines": {
			doctype: "Project",
			filters: {
				status: ["not in", ["Completed", "Cancelled"]],
				ic_deadline: ["<=", deadline_end],
			},
		},
		"AMC Due Soon": {
			doctype: "Project",
			filters: {
				ic_requires_amc: 1,
				ic_amc_status: ["in", ["Scheduled", "Reminded"]],
				ic_amc_contact_date: ["<=", amc_end],
			},
		},
		"Samples Transit to Office": {
			doctype: "IC Sample Tracking",
			filters: { sample_location: "In Transit to Office" },
		},
		"Samples At Office": {
			doctype: "IC Sample Tracking",
			filters: { sample_location: "At Instacertify Office" },
		},
		"Samples Transit to Lab": {
			doctype: "IC Sample Tracking",
			filters: { sample_location: "In Transit to Lab" },
		},
		"Samples At Laboratory": {
			doctype: "IC Sample Tracking",
			filters: { sample_location: "At Laboratory" },
		},
		"Samples In Storage": {
			doctype: "IC Sample Tracking",
			filters: { sample_location: "At Instacertify Storage" },
		},
		"Samples Discarded": {
			doctype: "IC Sample Tracking",
			filters: { sample_location: "Discarded" },
		},
	};
};

instacertify.open_kpi = function (label) {
	const route = (instacertify.kpi_routes() || {})[label];
	if (!route || !route.doctype) {
		frappe.show_alert({ message: __("No list linked for {0}", [label]), indicator: "orange" });
		return;
	}
	if (!frappe.model.can_read(route.doctype)) {
		frappe.show_alert({
			message: __("You do not have permission to open {0}", [route.doctype]),
			indicator: "red",
		});
		return;
	}
	frappe.route_options = route.filters || {};
	frappe.set_route("List", route.doctype);
};

instacertify.bind_summary_card_clicks = function (root) {
	const bindIn = (scope) => {
		if (!scope || !scope.querySelectorAll) return;
		scope.querySelectorAll(".ic-summary-card[data-kpi]").forEach((el) => {
			el.style.cursor = "pointer";
			el.onclick = function (e) {
				if (e.target && e.target.closest && e.target.closest("a")) return;
				e.preventDefault();
				const label = el.getAttribute("data-kpi");
				if (label) instacertify.open_kpi(label);
			};
		});
		scope.querySelectorAll("*").forEach((node) => {
			if (node.shadowRoot) bindIn(node.shadowRoot);
		});
	};
	bindIn(root && root.nodeType ? root : document);
};

// Global delegation (light DOM). Shadow blocks bind via onclick in their own script.
$(document).on("click.icKpiGlobal", ".ic-summary-card[data-kpi]", function (e) {
	if ($(e.target).closest("a").length) return;
	e.preventDefault();
	const label = $(this).attr("data-kpi");
	if (label) instacertify.open_kpi(label);
});

instacertify.load_summary_cards = function () {
	frappe.call({
		method: "instacertify.project.events.get_dashboard_counts",
		callback(r) {
			const d = r.message || {};
			const items = [
				["New Leads", d.new_leads],
				["Active Leads", d.active_leads],
				["Leads to Contact", d.leads_to_contact, true],
				["Quotations Sent", d.quotations_sent],
				["Awaiting Response", d.quotations_awaiting],
				["Quotations Accepted", d.quotations_accepted, true],
				["Active Projects", d.active_projects],
				["Pending Tasks", d.pending_tasks],
				["Open Tickets", d.open_tickets, true],
				["Pending Documents", d.pending_documents],
				["Testing Requests", d.testing_requests],
				["Upcoming Deadlines", d.upcoming_deadlines, true],
				["AMC Due Soon", d.amc_due_soon, true],
			];
			const $grid = $("#ic-summary-grid");
			if (!$grid.length) return;
			$grid.empty();
			items.forEach(([label, value, accent]) => {
				$grid.append(`
					<div class="ic-summary-card is-clickable ${accent ? "accent" : ""}" data-kpi="${frappe.utils.escape_html(label)}" title="${__("Click to open list")}">
						<div class="label">${__(label)}</div>
						<div class="value">${value ?? 0}</div>
					</div>
				`);
			});
			instacertify.bind_summary_card_clicks($grid);
		},
	});
};

instacertify.load_project_cards = function () {
	frappe.call({
		method: "instacertify.project.events.get_ongoing_project_cards",
		args: { limit: 12 },
		callback(r) {
			const $grid = $("#ic-project-grid");
			if (!$grid.length) return;
			const rows = r.message || [];
			if (!rows.length) {
				$grid.html(
					`<div class="ic-project-empty">${__("No ongoing projects yet.")} <a href="/app/project/new">${__("Create one")}</a></div>`
				);
				return;
			}
			$grid.html(rows.map((p) => instacertify.project_tile_html(p)).join(""));
			$grid.find(".ic-project-tile").on("click", function () {
				frappe.set_route("Form", "Project", $(this).data("name"));
			});
		},
	});
};

instacertify.project_tile_html = function (p) {
	const esc = frappe.utils.escape_html;
	const priority = p.priority || p.ic_priority || "Medium";
	const progress = Math.round(p.progress || 0);
	const urgency = p.urgency || "ok";
	const stage = p.stage || p.ic_project_stage || p.status || "Active";
	const deadline = p.deadline_label
		? p.deadline_label
		: p.deadline
			? frappe.datetime.str_to_user(p.deadline)
			: "No deadline";
	let due_txt = deadline;
	if (p.days_left != null) {
		if (p.days_left < 0) due_txt = __("{0}d overdue", [Math.abs(p.days_left)]);
		else if (p.days_left === 0) due_txt = __("Due today");
		else due_txt = __("{0}d left", [p.days_left]);
	}
	const pending = p.ic_pending_action || "";
	const assigned = p.assigned_name || "Unassigned";
	const count = p.assignee_count || (p.assignees || []).length || 0;
	const team_title = (p.assignees || [])
		.map((a) => `${a.full_name || a.user}${a.role_on_project === "Primary" ? " (Primary)" : ""}`)
		.join(", ");
	const initials = p.initials || "?";
	const avatars = (p.assignees || [])
		.slice(0, 4)
		.map((a, i) => {
			const name = a.full_name || a.user || "?";
			const ini = name
				.split(/\s+/)
				.filter(Boolean)
				.slice(0, 2)
				.map((w) => w[0])
				.join("")
				.toUpperCase();
			return `<span class="ic-project-avatar" style="z-index:${4 - i}" title="${esc(name)}">${esc(ini || "?")}</span>`;
		})
		.join("");
	const more =
		count > 4 ? `<span class="ic-project-avatar more">+${count - 4}</span>` : "";
	return `
		<article class="ic-project-tile priority-${esc(priority)} urgency-${esc(urgency)}" data-name="${esc(p.name)}" tabindex="0" role="button">
			<div class="ic-project-tile-glow"></div>
			<div class="ic-project-tile-top">
				<div class="ic-project-tile-mark">${esc(initials)}</div>
				<div class="ic-project-tile-badges">
					<span class="ic-badge ${esc(String(priority).toLowerCase())}">${esc(priority)}</span>
					<span class="ic-project-stage">${esc(stage)}</span>
				</div>
			</div>
			<h4 class="ic-project-tile-title">${esc(p.project_name || p.name)}</h4>
			<div class="ic-project-tile-customer">${esc(p.customer_name || p.customer || "No customer")}</div>
			<div class="ic-project-tile-progress">
				<div class="ic-project-ring" style="--ic-prog:${progress}">
					<span>${progress}%</span>
				</div>
				<div class="ic-project-tile-progress-meta">
					<div class="ic-project-tile-progress-label">${__("Progress")}</div>
					<div class="ic-progress"><span style="width:${progress}%"></span></div>
					${pending ? `<div class="ic-project-pending">${esc(pending)}</div>` : `<div class="ic-project-pending muted">${__("On track")}</div>`}
				</div>
			</div>
			<div class="ic-project-tile-foot">
				<div class="ic-project-tile-person" title="${esc(team_title || assigned)}">
					<span class="ic-project-avatars">${avatars}${more}</span>
					<span class="ic-project-person-label">${esc(assigned)}</span>
				</div>
				<div class="ic-project-tile-due urgency-${esc(urgency)}">${esc(due_txt)}</div>
			</div>
		</article>
	`;
};


// Inject greeting on Instacertify Home workspace
$(document).on("page-change", function () {
	const route = frappe.get_route();
	if (route[0] === "Workspaces" && (route[1] || "").includes("Instacertify")) {
		const bindOrInject = (attempt) => {
			// Home Dashboard custom block owns KPI tiles — only bind clicks.
			if (instacertify.has_home_root() || document.getElementById("ic-home-root")) {
				instacertify.bind_summary_card_clicks(document);
				return;
			}
			if (attempt < 6) {
				setTimeout(() => bindOrInject(attempt + 1), 250);
				return;
			}
			const $page = $(".workspace-body, .workspace-page, .page-body").first();
			instacertify.render_home_banner($page);
		};
		setTimeout(() => bindOrInject(0), 200);
	}
});

// Quotation form enhancements
frappe.ui.form.on("Quotation", {
	refresh(frm) {
		instacertify.apply_quotation_naming_series(frm);
		frm.add_custom_button(__("Upload Quote Format"), () => {
			instacertify.open_quote_format_upload({
				quotation_type: frm.doc.ic_quotation_type || "Consulting",
			});
		}, __("Library"));
		frm.add_custom_button(__("Quote Format Library"), () => {
			frappe.set_route("List", "IC Quotation Template");
		}, __("Library"));
		frm.add_custom_button(__("Upload Lab / Scope"), () => {
			instacertify.open_laboratory_upload();
		}, __("Library"));

		if (!frm.is_new()) {
			instacertify.add_helpdesk_buttons(frm, {
				quotation: frm.doc.name,
				customer: frm.doc.quotation_to === "Customer" ? frm.doc.party_name : null,
				lead: frm.doc.quotation_to === "Lead" ? frm.doc.party_name : null,
				channel: "Internal",
				subject: `Quotation ${frm.doc.name}`,
			});
			instacertify.load_quotation_links(frm);
			if (frm.doc.quotation_to === "Lead" && frm.doc.party_name) {
				frm.add_custom_button(__("Open Lead"), () => {
					frappe.set_route("Form", "Lead", frm.doc.party_name);
				}, __("Links"));
			}
			if (frm.doc.quotation_to === "Customer" && frm.doc.party_name) {
				frm.add_custom_button(__("Open Customer"), () => {
					frappe.set_route("Form", "Customer", frm.doc.party_name);
				}, __("Links"));
			}
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
			}, __("Actions"));

			frm.add_custom_button(__("Download PDF"), () => {
				const fmt = frm.meta.default_print_format || "Instacertify Quotation";
				const url = frappe.urllib.get_full_url(
					"/api/method/instacertify.utils.pdf.download_quotation_pdf?" +
						$.param({ name: frm.doc.name, print_format: fmt })
				);
				window.open(url, "_blank");
			}, __("Actions"));

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
			}, __("Actions"));

			frm.add_custom_button(__("Manage Templates"), () => {
				frappe.set_route("List", "IC Quotation Template", {
					quotation_type: frm.doc.ic_quotation_type || undefined,
				});
			}, __("Actions"));

			frm.add_custom_button(__("New Template"), () => {
				frappe.new_doc("IC Quotation Template", {
					quotation_type:
						frm.doc.ic_quotation_type === "Service"
							? "Consulting"
							: frm.doc.ic_quotation_type || "Consulting",
					service_family: frm.doc.ic_service_family,
					service_name: frm.doc.ic_service_name,
				});
			}, __("Actions"));

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
				}, __("Actions"));
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
				}, __("Actions"));

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
				}, __("Actions"));

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
					}, __("Actions"));
				}

				// Make Invoice the primary action after acceptance
				frm.page.set_inner_btn_group_as_primary(__("Actions"));
			}

			// Hide Sales Order — Instacertify bills from Quotation directly
			instacertify.hide_sales_order_button(frm);
		}

		instacertify.setup_quotation_lab_queries(frm);
		instacertify.render_quotation_entry_guide(frm);
		if (frm.doc.ic_quotation_type) {
			instacertify.toggle_quotation_sections(frm);
		}
		instacertify.setup_quotation_template_filter(frm);
		frm.layout && frm.wrapper && frm.wrapper.addClass("ic-quotation-form");
	},

	ic_quotation_type(frm) {
		instacertify.toggle_quotation_sections(frm);
		instacertify.setup_quotation_template_filter(frm);
		instacertify.render_quotation_entry_guide(frm);
		instacertify.apply_quotation_naming_series(frm);
		if (frm.doc.ic_quotation_template) {
			frm.set_value("ic_quotation_template", "");
		}
	},

	ic_quotation_template(frm) {
		instacertify.render_quotation_entry_guide(frm);
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

instacertify.QUOTATION_TYPE_HELP = {
	Consulting: {
		title: "Consulting / Certification",
		steps: [
			"Select a Quotation Template (right) or fill title & standards below",
			"Enter commercials in Cost Items",
			"Review payment terms → Share with Customer",
		],
	},
	Service: {
		title: "Service",
		steps: [
			"Pick a Service/Consulting template",
			"Confirm title, timeline, and cost lines",
			"Share with Customer when ready",
		],
	},
	Testing: {
		title: "Testing",
		steps: [
			"Open Test Lines — pick Laboratory, then Lab Test Scope",
			"Charges fill from the lab library; adjust samples if needed",
			"Share with Customer when ready",
		],
	},
	Renewal: {
		title: "Renewal",
		steps: [
			"Choose a Renewal template if available",
			"Update validity / commercial lines",
			"Share with Customer",
		],
	},
	Other: {
		title: "Other",
		steps: ["Fill service basics", "Add cost lines", "Share when ready"],
	},
	"Multiple Products / Multiple Services": {
		title: "Multiple Products / Services",
		steps: [
			"Fill consulting and/or testing sections as needed",
			"Add product rows under Multi-Product lines",
			"Share when ready",
		],
	},
};

instacertify.render_quotation_entry_guide = function (frm) {
	const wrap = frm.fields_dict.ic_entry_guide && frm.fields_dict.ic_entry_guide.$wrapper;
	if (!wrap || !wrap.length) return;
	const t = frm.doc.ic_quotation_type;
	const help = instacertify.QUOTATION_TYPE_HELP[t];
	const type_chips = [
		["Consulting", "Certification / consulting quote"],
		["Testing", "Lab tests & commercials"],
		["Renewal", "Certificate renewal"],
		["Service", "Service delivery quote"],
		["Multiple Products / Multiple Services", "Mixed lines"],
		["Other", "Custom"],
	]
		.map(([key, hint]) => {
			const active = t === key ? "active" : "";
			return `<button type="button" class="ic-quote-type-chip ${active}" data-type="${frappe.utils.escape_html(key)}">
				<span class="ic-quote-type-name">${frappe.utils.escape_html(key)}</span>
				<span class="ic-quote-type-hint">${frappe.utils.escape_html(hint)}</span>
			</button>`;
		})
		.join("");

	const steps = help
		? `<ol class="ic-quote-steps">${help.steps
				.map((s) => `<li>${frappe.utils.escape_html(s)}</li>`)
				.join("")}</ol>`
		: `<p class="ic-quote-guide-empty">${__("Select a Quotation Type to see the entry steps.")}</p>`;

	wrap.html(`
		<div class="ic-quote-entry">
			<div class="ic-quote-entry-head">
				<div>
					<div class="ic-quote-entry-kicker">${__("Data entry")}</div>
					<div class="ic-quote-entry-title">${
						help ? frappe.utils.escape_html(help.title) : __("Choose quotation type")
					}</div>
					<div class="ic-quote-entry-sub">${__(
						"Type and template are the first two fields — everything else opens from there."
					)}</div>
				</div>
			</div>
			<div class="ic-quote-type-grid">${type_chips}</div>
			${steps}
		</div>
	`);

	wrap.find(".ic-quote-type-chip").on("click", function () {
		const type = $(this).data("type");
		if (!type || type === frm.doc.ic_quotation_type) return;
		frm.set_value("ic_quotation_type", type);
	});
};

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
	const isConsulting = consultingLike.includes(t);
	const isTesting = ["Testing", "Multiple Products / Multiple Services"].includes(t);
	[
		"ic_section_service",
		"ic_section_about",
		"ic_section_docs_timeline",
		"ic_section_scope",
	].forEach((f) => frm.toggle_display(f, isConsulting));
	["ic_section_testing", "ic_section_test_lines"].forEach((f) => frm.toggle_display(f, isTesting));
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
		instacertify.load_standard_options(frm);
		instacertify.load_lab_scope_options(frm, cdt, cdn);
		instacertify.load_lab_offers_for_row(frm, cdt, cdn);
	},
	applicable_standard(frm, cdt, cdn) {
		frappe.model.set_value(cdt, cdn, "lab_offer", "");
		instacertify.load_lab_offers_for_row(frm, cdt, cdn, { open_picker: true });
	},
	lab_offer(frm, cdt, cdn) {
		instacertify.apply_lab_offer(frm, cdt, cdn);
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

instacertify.set_lab_offer_autocomplete = function (frm, options) {
	const grid = frm.fields_dict.ic_test_items && frm.fields_dict.ic_test_items.grid;
	if (!grid) return;
	const opt_str = (options || []).map((o) => o.value || o).join("\n");
	grid.update_docfield_property("lab_offer", "options", opt_str);
};

instacertify.load_standard_options = function (frm) {
	frappe.call({
		method: "instacertify.laboratory.api.get_standard_options",
		callback(r) {
			const opts = (r.message || []).map((o) => o.value || o);
			const opt_str = opts.join("\n");
			const grid = frm.fields_dict.ic_test_items && frm.fields_dict.ic_test_items.grid;
			if (grid) {
				grid.update_docfield_property("applicable_standard", "options", opt_str);
			}
			frm._ic_standard_options = opts;
		},
	});
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

instacertify.load_lab_offers_for_row = function (frm, cdt, cdn, opts) {
	opts = opts || {};
	const row = locals[cdt][cdn];
	if (!row || !row.applicable_standard) {
		instacertify.set_lab_offer_autocomplete(frm, []);
		return;
	}
	frappe.call({
		method: "instacertify.laboratory.api.get_labs_for_standard",
		args: {
			applicable_standard: row.applicable_standard,
			test_name: row.test_name || "",
		},
		callback(r) {
			const offers = r.message || [];
			frm._ic_lab_offers = frm._ic_lab_offers || {};
			frm._ic_lab_offers[cdn] = offers;
			instacertify.set_lab_offer_autocomplete(frm, offers);
			if (opts.open_picker && offers.length) {
				instacertify.open_lab_offer_picker(frm, cdt, cdn, offers);
			} else if (!offers.length) {
				frappe.show_alert({
					message: __("No Active labs list this standard yet. Add it under Laboratory → Test / Pricing."),
					indicator: "orange",
				});
			}
		},
	});
};

instacertify.open_lab_offer_picker = function (frm, cdt, cdn, offers) {
	if (!offers || !offers.length) return;
	const rows_html = offers
		.map((o, idx) => {
			const price = format_currency(o.selling_price || 0, o.currency || "INR");
			return `<tr data-idx="${idx}" class="ic-lab-offer-row" style="cursor:pointer">
				<td><b>${frappe.utils.escape_html(o.laboratory_name || "")}</b></td>
				<td>${frappe.utils.escape_html(o.location || "—")}</td>
				<td>${frappe.utils.escape_html(o.test_name || "")}</td>
				<td style="text-align:right;font-weight:700;color:#033447">${frappe.utils.escape_html(price)}</td>
			</tr>`;
		})
		.join("");
	const d = new frappe.ui.Dialog({
		title: __("Select lab for this standard"),
		size: "large",
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "help",
				options: `<div class="text-muted" style="margin-bottom:8px">
					${__("Same standard is available from multiple labs at different prices. Pick one:")}
				</div>
				<table class="table table-bordered table-hover" style="margin:0">
					<thead><tr>
						<th>${__("Laboratory")}</th>
						<th>${__("Location")}</th>
						<th>${__("Test")}</th>
						<th style="text-align:right">${__("Selling")}</th>
					</tr></thead>
					<tbody>${rows_html}</tbody>
				</table>`,
			},
		],
	});
	d.$body.find(".ic-lab-offer-row").on("click", function () {
		const idx = cint($(this).data("idx"));
		const offer = offers[idx];
		if (!offer) return;
		frappe.model.set_value(cdt, cdn, "lab_offer", offer.value).then(() => {
			instacertify.apply_lab_offer(frm, cdt, cdn, offer);
		});
		d.hide();
	});
	d.show();
};

instacertify.apply_lab_offer = function (frm, cdt, cdn, offer) {
	const row = locals[cdt][cdn];
	const apply = (s) => {
		if (!s) {
			frappe.show_alert({
				message: __("Could not resolve that lab offer. Try again."),
				indicator: "orange",
			});
			return;
		}
		frappe.model.set_value(cdt, cdn, "laboratory", s.laboratory);
		frappe.model.set_value(cdt, cdn, "lab_scope_row", s.scope_row);
		frappe.model.set_value(cdt, cdn, "test_name", s.test_name);
		if (s.applicable_standard) {
			frappe.model.set_value(cdt, cdn, "applicable_standard", s.applicable_standard);
		}
		frappe.model.set_value(cdt, cdn, "suggested_selling_price", s.selling_price);
		frappe.model.set_value(cdt, cdn, "per_unit_charges", s.selling_price).then(() => {
			instacertify.recalc_test_row(frm, cdt, cdn);
		});
		if (s.currency) {
			frappe.model.set_value(cdt, cdn, "currency", s.currency);
		}
		if (s.scope_label) {
			frappe.model.set_value(cdt, cdn, "lab_test_scope", s.scope_label);
		}
		if (s.value && row.lab_offer !== s.value) {
			frappe.model.set_value(cdt, cdn, "lab_offer", s.value);
		}
		frappe.call({
			method: "instacertify.laboratory.api.get_laboratory_summary",
			args: { laboratory: s.laboratory },
			callback(r) {
				const d = r.message || {};
				if (d.accreditation_summary) {
					frappe.model.set_value(cdt, cdn, "laboratory_accreditation", d.accreditation_summary);
				}
			},
		});
		instacertify.load_lab_scope_options(frm, cdt, cdn);
	};

	if (offer) {
		apply(offer);
		return;
	}
	if (!row.lab_offer) return;
	frappe.call({
		method: "instacertify.laboratory.api.get_lab_offer_details",
		args: {
			lab_offer: row.lab_offer,
			applicable_standard: row.applicable_standard,
			laboratory: row.laboratory,
			scope_row: row.lab_scope_row,
		},
		callback(r) {
			apply(r.message);
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

// Prompt for quotation type on new — clearer type + template selection
frappe.ui.form.on("Quotation", {
	onload(frm) {
		instacertify.setup_quotation_template_filter(frm);
		instacertify.load_standard_options(frm);
		frm.wrapper && frm.wrapper.addClass("ic-quotation-form");
		if (frm.is_new() && !frm.doc.ic_quotation_type) {
			const d = new frappe.ui.Dialog({
				title: __("New Quotation — choose type"),
				size: "large",
				fields: [
					{
						fieldtype: "HTML",
						fieldname: "help",
						options: `<div class="ic-quote-dialog-help">
							<strong>${__("Step 1")}</strong> ${__("Pick the quotation type")}<br>
							<strong>${__("Step 2")}</strong> ${__("Optionally pick a template (filtered by type)")}<br>
							<span class="text-muted">${__("You can change both later on the form.")}</span>
						</div>`,
					},
					{
						fieldname: "ic_quotation_type",
						fieldtype: "Select",
						label: __("Quotation Type"),
						options:
							"Consulting\nTesting\nRenewal\nService\nOther\nMultiple Products / Multiple Services",
						reqd: 1,
						default: "Consulting",
						description: __(
							"Consulting/Service = certification · Testing = lab lines · Renewal = renewals"
						),
					},
					{
						fieldname: "ic_quotation_template",
						fieldtype: "Link",
						label: __("Quotation Template (optional)"),
						options: "IC Quotation Template",
						get_query() {
							const t = d.get_value("ic_quotation_type");
							const filters = { is_active: 1 };
							if (t === "Consulting" || t === "Service") {
								filters.quotation_type = ["in", ["Consulting", "Service"]];
							} else if (t) {
								filters.quotation_type = t;
							}
							return { filters };
						},
					},
				],
				primary_action_label: __("Continue to form"),
				primary_action(values) {
					frm.set_value("ic_quotation_type", values.ic_quotation_type);
					instacertify.apply_quotation_naming_series(frm);
					if (values.ic_quotation_template) {
						frm.set_value("ic_quotation_template", values.ic_quotation_template);
					}
					d.hide();
					setTimeout(() => {
						frm.scroll_to_field("ic_quotation_type");
						instacertify.render_quotation_entry_guide(frm);
					}, 200);
				},
			});
			d.fields_dict.ic_quotation_type.df.onchange = () => {
				d.set_value("ic_quotation_template", "");
			};
			d.show();
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

instacertify.render_lead_reminder_banner = function (frm) {
	if (!frm || !frm.doc || frm.is_new()) {
		try {
			frm.dashboard && frm.dashboard.clear_headline();
		} catch (e) {
			/* ignore */
		}
		return;
	}

	// Avoid stacking duplicate headlines when multiple refresh handlers fire.
	if (frm.__ic_lead_reminder_painting) return;
	frm.__ic_lead_reminder_painting = true;

	const due = frm.doc.ic_next_contact_date;
	const today = frappe.datetime.get_today();
	let urgency = "blue";
	let when = __("No next contact date set");
	if (due) {
		if (due < today) {
			urgency = "red";
			when = __("Overdue — was {0}", [frappe.datetime.str_to_user(due)]);
		} else if (due === today) {
			urgency = "orange";
			when = __("Call today");
		} else {
			urgency = "blue";
			when = __("Next contact {0}", [frappe.datetime.str_to_user(due)]);
		}
	}

	const person = frm.doc.ic_party_name || frm.doc.lead_name || frm.doc.company_name || frm.doc.name;
	const phone = frm.doc.mobile_no || frm.doc.phone || frm.doc.ic_alternate_phone || "—";
	let withUser = frm.doc.ic_assigned_salesperson || frm.doc.lead_owner || __("Unassigned");
	try {
		if (withUser && frappe.user_info) {
			const info = frappe.user_info(withUser);
			if (info && info.fullname) withUser = info.fullname;
		}
	} catch (e) {
		/* keep id */
	}
	const remarks = (frm.doc.ic_call_remarks || "").trim() || __("No customer remarks yet — capture what they said after the call.");
	const connected = frm.doc.ic_lead_connected ? __("Connected") : __("Not connected yet");

	const intro = `
		<div class="ic-lead-form-reminder ${urgency === "red" ? "overdue" : urgency === "orange" ? "today" : ""}">
			<div class="ic-lead-form-reminder-title">${__("Lead reminder")} · ${frappe.utils.escape_html(when)}</div>
			<div class="ic-lead-form-reminder-grid">
				<div><strong>${__("Whom to call")}</strong>${frappe.utils.escape_html(person)}</div>
				<div><strong>${__("Phone")}</strong>${frappe.utils.escape_html(phone)}</div>
				<div><strong>${__("Connect with")}</strong>${frappe.utils.escape_html(withUser)}</div>
				<div><strong>${__("Status")}</strong>${frappe.utils.escape_html(connected)}</div>
				<div style="grid-column:1/-1"><strong>${__("Customer remarks")}</strong>${frappe.utils.escape_html(remarks)}</div>
			</div>
		</div>
	`;

	try {
		if (frm.dashboard) {
			frm.dashboard.clear_headline();
			frm.dashboard.set_headline(intro, urgency, true);
		} else if (frm.set_intro) {
			frm.set_intro(intro, urgency);
		}
	} catch (e) {
		console.warn("ic lead reminder", e);
	} finally {
		setTimeout(() => {
			frm.__ic_lead_reminder_painting = false;
		}, 400);
	}
};

instacertify.load_lead_related = function (frm) {
	if (!frm.fields_dict.ic_history_html) return;
	frappe.call({
		method: "instacertify.crm.events.get_lead_history",
		args: { lead: frm.doc.name },
		callback(r) {
			frm.set_df_property("ic_history_html", "options", ic_render_lead_related(r.message || {}));
		},
	});
};

instacertify.load_quotation_links = function (frm) {
	if (!frm.fields_dict.ic_links_html) return;
	frappe.call({
		method: "instacertify.crm.events.get_quotation_links",
		args: { quotation: frm.doc.name },
		callback(r) {
			frm.set_df_property("ic_links_html", "options", ic_render_quotation_links(r.message || {}));
		},
	});
};

function ic_render_lead_related(d) {
	const lead = (d.lead && d.lead.name) || "";
	const cards = `
		<div class="ic-summary-grid">
			<div class="ic-summary-card"><div class="label">${__("Quotations")}</div><div class="value">${(d.quotations || []).length}</div></div>
			<div class="ic-summary-card accent"><div class="label">${__("Open Quotes")}</div><div class="value">${(d.open_quotations || []).length}</div></div>
			<div class="ic-summary-card"><div class="label">${__("Accepted")}</div><div class="value">${(d.accepted_quotations || []).length}</div></div>
			<div class="ic-summary-card"><div class="label">${__("Opportunities")}</div><div class="value">${(d.opportunities || []).length}</div></div>
			<div class="ic-summary-card"><div class="label">${__("Projects")}</div><div class="value">${(d.projects || []).length}</div></div>
			<div class="ic-summary-card accent"><div class="label">${__("Tickets")}</div><div class="value">${(d.tickets || []).length}</div></div>
		</div>
		<p class="ic-related-hint text-muted">${__("Quotations created from this lead, plus customer journey after conversion.")}</p>
	`;
	const quote_rows = (d.quotations || []).map((q) => [
		ic_doc_link("Quotation", q.name),
		ic_status_pill(q.ic_workflow_status || q.status),
		ic_esc(q.ic_quotation_type || "—"),
		ic_fmt_money(q.grand_total, q.currency),
		ic_esc(q.transaction_date || "—"),
	]);
	const opp_rows = (d.opportunities || []).map((o) => [
		ic_doc_link("Opportunity", o.name, o.title || o.name),
		ic_status_pill(o.status),
		ic_fmt_money(o.opportunity_amount, o.currency),
		ic_esc(o.transaction_date || "—"),
	]);
	const project_rows = (d.projects || []).map((p) => [
		ic_doc_link("Project", p.name, p.project_name || p.name),
		ic_status_pill(p.status),
		ic_esc(p.ic_project_stage || "—"),
		p.ic_quotation ? ic_doc_link("Quotation", p.ic_quotation) : "—",
	]);
	const customer_block = d.customer
		? `<p>${__("Converted Customer")}: ${ic_doc_link("Customer", d.customer.name, d.customer.customer_name || d.customer.name)}</p>`
		: `<p class="text-muted">${__("Not converted to Customer yet.")}</p>`;

	return `
		<div class="ic-customer-related">
			${cards}
			${customer_block}
			${ic_related_section(
				__("Quotations"),
				ic_table([__("Quotation"), __("Status"), __("Type"), __("Amount"), __("Date")], quote_rows),
				__("No quotations yet — use Create → Create Quotation"),
				lead ? ic_list_link("Quotation", null, __("View all"), { party_name: lead, quotation_to: "Lead" }) : ""
			)}
			${ic_related_section(
				__("Opportunities"),
				ic_table([__("Opportunity"), __("Status"), __("Amount"), __("Date")], opp_rows),
				__("No opportunities")
			)}
			${ic_related_section(
				__("Projects (after conversion)"),
				ic_table([__("Project"), __("Status"), __("Stage"), __("Quotation")], project_rows),
				__("No projects yet")
			)}
		</div>
	`;
}

function ic_render_quotation_links(d) {
	const q = d.quotation || {};
	const partyBits = [];
	if (d.lead) {
		partyBits.push(
			`${__("Lead")}: ${ic_doc_link("Lead", d.lead.name, d.lead.ic_party_name || d.lead.company_name || d.lead.name)} ${ic_status_pill(d.lead.ic_pipeline_stage || d.lead.status)}`
		);
	}
	if (d.customer) {
		partyBits.push(
			`${__("Customer")}: ${ic_doc_link("Customer", d.customer.name, d.customer.customer_name || d.customer.name)}`
		);
	}
	if (d.opportunity) {
		partyBits.push(`${__("Opportunity")}: ${ic_doc_link("Opportunity", d.opportunity)}`);
	}
	if (d.parent_quotation) {
		partyBits.push(`${__("Revision of")}: ${ic_doc_link("Quotation", d.parent_quotation)}`);
	}

	const cards = `
		<div class="ic-summary-grid">
			<div class="ic-summary-card"><div class="label">${__("Projects")}</div><div class="value">${(d.projects || []).length}</div></div>
			<div class="ic-summary-card"><div class="label">${__("Invoices")}</div><div class="value">${(d.invoices || []).length}</div></div>
			<div class="ic-summary-card accent"><div class="label">${__("Testing")}</div><div class="value">${(d.testing_requests || []).length}</div></div>
			<div class="ic-summary-card"><div class="label">${__("Documents")}</div><div class="value">${(d.documents || []).length}</div></div>
		</div>
		<div class="ic-related-party">${partyBits.join(" · ") || `<span class="text-muted">${__("No party linked")}</span>`}</div>
	`;

	const project_rows = (d.projects || []).map((p) => [
		ic_doc_link("Project", p.name, p.project_name || p.name),
		ic_status_pill(p.status),
		ic_esc(p.ic_project_stage || "—"),
		ic_esc(p.ic_deadline || "—"),
	]);
	const invoice_rows = (d.invoices || []).map((i) => [
		ic_doc_link("Sales Invoice", i.name),
		ic_status_pill(i.status),
		ic_fmt_money(i.grand_total, i.currency),
		ic_esc(i.posting_date || "—"),
	]);
	const testing_rows = (d.testing_requests || []).map((t) => [
		ic_doc_link("IC Testing Request", t.name, t.title || t.name),
		ic_status_pill(t.status),
		t.project ? ic_doc_link("Project", t.project) : "—",
		ic_esc(t.product || "—"),
	]);
	const doc_rows = (d.documents || []).map((x) => [
		ic_doc_link("IC Document Request", x.name, x.title || x.name),
		ic_status_pill(x.status),
		x.project ? ic_doc_link("Project", x.project) : "—",
	]);

	return `
		<div class="ic-customer-related">
			${cards}
			${ic_related_section(__("Projects"), ic_table([__("Project"), __("Status"), __("Stage"), __("Deadline")], project_rows), __("No projects from this quotation yet"))}
			${ic_related_section(__("Sales Invoices"), ic_table([__("Invoice"), __("Status"), __("Amount"), __("Date")], invoice_rows), __("No invoices yet"))}
			${ic_related_section(__("Testing Requests"), ic_table([__("Request"), __("Status"), __("Project"), __("Product")], testing_rows), __("No testing requests"))}
			${ic_related_section(__("Document Requests"), ic_table([__("Request"), __("Status"), __("Project")], doc_rows), __("No document requests"))}
		</div>
	`;
}

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
			allow_web_link: false,
			allow_google_drive: false,
			upload_notes: instacertify.get_attach_upload_notes(),
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

		if (frm.doc.ic_quotation) {
			frm.add_custom_button(__("Open Quotation"), () => {
				frappe.set_route("Form", "Quotation", frm.doc.ic_quotation);
			}, __("Links"));
		}
		if (frm.doc.customer) {
			frm.add_custom_button(__("Open Customer"), () => {
				frappe.set_route("Form", "Customer", frm.doc.customer);
			}, __("Links"));
		}

		frm.add_custom_button(__("Add Project Update"), () => {
			frappe.new_doc("IC Project Update", { project: frm.doc.name, progress_percentage: frm.doc.ic_progress_percentage, project_stage: frm.doc.ic_project_stage });
		}, __("Actions"));
		frm.add_custom_button(__("Generate / Share Document List"), () => {
			instacertify.open_project_document_share_dialog(frm);
		}, __("Actions"));
		frm.add_custom_button(__("Share Sample Dispatch Sheet"), () => {
			frappe.call({
				method: "instacertify.sample_dispatch.api.create_sample_dispatch_for_project",
				args: { project: frm.doc.name },
				freeze: true,
				callback(r) {
					const url = r.message && r.message.url;
					frappe.msgprint({
						title: __("Sample Dispatch Data Collection — customer link"),
						message: `
							<p>${__("Share this link so the customer can submit courier, AWB, POD, and sample dispatch details:")}</p>
							<p><a href="${frappe.utils.escape_html(url)}" target="_blank" rel="noopener">${frappe.utils.escape_html(url)}</a></p>
						`,
						indicator: "green",
					});
					if (url && navigator.clipboard) {
						navigator.clipboard.writeText(url).catch(() => {});
					}
					if (r.message && r.message.name) {
						frappe.set_route("Form", "IC Sample Dispatch Collection", r.message.name);
					}
				},
			});
		}, __("Actions"));
		frm.add_custom_button(__("Open Team Chat"), () => {
			instacertify.open_project_chat(frm);
		}, __("Actions"));
		frm.add_custom_button(__("Collaboration Hub"), () => {
			frappe.route_options = { project: frm.doc.name };
			frappe.set_route("team-collaboration");
		}, __("Actions"));
		instacertify.add_helpdesk_buttons(frm, {
			project: frm.doc.name,
			customer: frm.doc.customer,
			channel: "Internal",
			subject: frm.doc.project_name ? `Project: ${frm.doc.project_name}` : "",
		});
		instacertify.render_project_chat_panel(frm);
		frm.add_custom_button(__("Add Me to Team"), () => {
			const me = frappe.session.user;
			const exists = (frm.doc.ic_team_members || []).some((r) => r.user === me);
			if (exists) {
				frappe.show_alert({ message: __("You are already on this team"), indicator: "blue" });
				return;
			}
			frm.add_child("ic_team_members", {
				user: me,
				full_name: frappe.boot.user.full_name || me,
				role_on_project: (frm.doc.ic_team_members || []).length ? "Member" : "Primary",
			});
			frm.refresh_field("ic_team_members");
			frappe.show_alert({ message: __("Added — save the project to confirm"), indicator: "green" });
		}, __("Actions"));
	},
});

frappe.ui.form.on("Project Team Member", {
	user(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.user) return;
		frappe.db.get_value("User", row.user, "full_name", (r) => {
			if (r && r.full_name) frappe.model.set_value(cdt, cdn, "full_name", r.full_name);
		});
	},
	role_on_project(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.role_on_project !== "Primary") return;
		(frm.doc.ic_team_members || []).forEach((r) => {
			if (r.name !== cdn && r.role_on_project === "Primary") {
				frappe.model.set_value(r.doctype, r.name, "role_on_project", "Member");
			}
		});
	},
});

frappe.ui.form.on("IC Testing Request", {
	refresh(frm) {
		frm.set_query("laboratory", () => ({ filters: { status: "Active" } }));
		instacertify.load_testing_request_standard_options(frm);
		if (frm.doc.applicable_standard) {
			instacertify.load_testing_request_lab_offers(frm);
		}
		if (frm.doc.laboratory) {
			instacertify.load_testing_request_scope_options(frm);
		}
		if (!frm.is_new() && frm.doc.applicable_standard) {
			frm.add_custom_button(__("Compare Labs for Standard"), () => {
				instacertify.load_testing_request_lab_offers(frm, { open_picker: true });
			}, __("Actions"));
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
			}, __("Actions"));
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
	applicable_standard(frm) {
		frm.set_value("lab_offer", "");
		instacertify.load_testing_request_lab_offers(frm, { open_picker: true });
	},
	lab_offer(frm) {
		instacertify.apply_testing_request_lab_offer(frm);
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

instacertify.load_testing_request_standard_options = function (frm) {
	frappe.call({
		method: "instacertify.laboratory.api.get_standard_options",
		callback(r) {
			const opt_str = (r.message || []).map((o) => o.value || o).join("\n");
			frm.set_df_property("applicable_standard", "options", opt_str);
		},
	});
};

instacertify.load_testing_request_lab_offers = function (frm, opts) {
	opts = opts || {};
	if (!frm.doc.applicable_standard) {
		frm.set_df_property("lab_offer", "options", "");
		return;
	}
	frappe.call({
		method: "instacertify.laboratory.api.get_labs_for_standard",
		args: {
			applicable_standard: frm.doc.applicable_standard,
			test_name: frm.doc.test_name || "",
		},
		callback(r) {
			const offers = r.message || [];
			frm._ic_lab_offers = offers;
			frm.set_df_property("lab_offer", "options", offers.map((o) => o.value).join("\n"));
			if (opts.open_picker && offers.length) {
				instacertify.open_testing_request_lab_picker(frm, offers);
			} else if (opts.open_picker && !offers.length) {
				frappe.show_alert({
					message: __("No Active labs list this standard yet."),
					indicator: "orange",
				});
			}
		},
	});
};

instacertify.open_testing_request_lab_picker = function (frm, offers) {
	const rows_html = offers
		.map((o, idx) => {
			const price = format_currency(o.selling_price || 0, o.currency || "INR");
			return `<tr data-idx="${idx}" class="ic-lab-offer-row" style="cursor:pointer">
				<td><b>${frappe.utils.escape_html(o.laboratory_name || "")}</b></td>
				<td>${frappe.utils.escape_html(o.location || "—")}</td>
				<td>${frappe.utils.escape_html(o.test_name || "")}</td>
				<td style="text-align:right;font-weight:700">${frappe.utils.escape_html(price)}</td>
			</tr>`;
		})
		.join("");
	const d = new frappe.ui.Dialog({
		title: __("Select lab for this standard"),
		size: "large",
		fields: [
			{
				fieldtype: "HTML",
				options: `<div class="text-muted" style="margin-bottom:8px">
					${__("Compare labs offering this standard at different prices:")}
				</div>
				<table class="table table-bordered table-hover" style="margin:0">
					<thead><tr>
						<th>${__("Laboratory")}</th><th>${__("Location")}</th>
						<th>${__("Test")}</th><th style="text-align:right">${__("Selling")}</th>
					</tr></thead>
					<tbody>${rows_html}</tbody>
				</table>`,
			},
		],
	});
	d.$body.find(".ic-lab-offer-row").on("click", function () {
		const offer = offers[cint($(this).data("idx"))];
		if (!offer) return;
		frm.set_value("lab_offer", offer.value).then(() => {
			instacertify.apply_testing_request_lab_offer(frm, offer);
		});
		d.hide();
	});
	d.show();
};

instacertify.apply_testing_request_lab_offer = function (frm, offer) {
	const apply = (s) => {
		if (!s) return;
		frm.set_value("laboratory", s.laboratory);
		frm.set_value("lab_scope_row", s.scope_row);
		frm.set_value("test_name", s.test_name);
		if (s.applicable_standard) frm.set_value("applicable_standard", s.applicable_standard);
		frm.set_value("suggested_selling_price", s.selling_price);
		if (s.scope_label) frm.set_value("lab_test_scope", s.scope_label);
		instacertify.load_testing_request_scope_options(frm);
	};
	if (offer) {
		apply(offer);
		return;
	}
	if (!frm.doc.lab_offer) return;
	frappe.call({
		method: "instacertify.laboratory.api.get_lab_offer_details",
		args: {
			lab_offer: frm.doc.lab_offer,
			applicable_standard: frm.doc.applicable_standard,
			laboratory: frm.doc.laboratory,
			scope_row: frm.doc.lab_scope_row,
		},
		callback(r) {
			apply(r.message);
		},
	});
};

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
						const url = r.message && r.message.url;
						frappe.msgprint({
							title: __("Documents Collection Sheet — customer link"),
							message: `<p><a href="${frappe.utils.escape_html(url)}" target="_blank" rel="noopener">${frappe.utils.escape_html(url)}</a></p>
								<p class="text-muted">${__("Customer can upload the document list and fill the Data Collection Sheet.")}</p>`,
							indicator: "green",
						});
						if (url && navigator.clipboard) {
							navigator.clipboard.writeText(url).catch(() => {});
						}
						frm.reload_doc();
					},
				});
			}, __("Actions"));

			(frm.doc.items || []).forEach((row) => {
				if (!row.name) return;
				if (row.uploaded_file) {
					frm.add_custom_button(__("Clear: {0}", [row.document_name]), () => {
						frappe.confirm(__("Delete this customer upload? They can upload again."), () => {
							frappe.call({
								method: "instacertify.documents.api.clear_document_item",
								args: { document_request: frm.doc.name, item_name: row.name },
								callback() { frm.reload_doc(); },
							});
						});
					}, __("Manage Uploads"));
				}
				if (["Uploaded", "Under Review", "Replacement Requested"].includes(row.status) || row.uploaded_file) {
					frm.add_custom_button(__("Approve: {0}", [row.document_name]), () => {
						frappe.call({
							method: "instacertify.documents.api.review_document_item",
							args: { document_request: frm.doc.name, item_name: row.name, action: "approve" },
							callback() { frm.reload_doc(); },
						});
					}, __("Review"));
					frm.add_custom_button(__("Reject: {0}", [row.document_name]), () => {
						frappe.prompt(
							[{ fieldname: "remarks", fieldtype: "Small Text", label: __("Remarks"), reqd: 1 }],
							(v) => {
								frappe.call({
									method: "instacertify.documents.api.review_document_item",
									args: {
										document_request: frm.doc.name,
										item_name: row.name,
										action: "reject",
										remarks: v.remarks,
									},
									callback() { frm.reload_doc(); },
								});
							},
							__("Reject document"),
							__("Reject")
						);
					}, __("Review"));
				}
			});
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

frappe.ui.form.on("IC Sample Dispatch Collection", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("Generate / Share Customer Link"), () => {
			frappe.call({
				method: "instacertify.sample_dispatch.api.share_sample_dispatch_collection",
				args: { name: frm.doc.name },
				freeze: true,
				callback(r) {
					const url = r.message && r.message.url;
					frappe.msgprint({
						title: __("Sample Dispatch Data Collection — customer link"),
						message: `<p>${__("Share this link with the customer to collect courier, AWB, POD, and sample details:")}</p>
							<p><a href="${frappe.utils.escape_html(url)}" target="_blank" rel="noopener">${frappe.utils.escape_html(url)}</a></p>`,
						indicator: "green",
					});
					if (url && navigator.clipboard) {
						navigator.clipboard.writeText(url).catch(() => {});
					}
					frm.reload_doc();
				},
			});
		}, __("Actions"));
	},
});

frappe.ui.form.on("IC Laboratory", {
	refresh(frm) {
		if (frm.is_new()) {
			frm.set_intro(
				__(
					"Laboratory Library — enter Laboratory Name, Accreditation Scope, and upload Scope Sheet / Scope PDF. Add each accredited test with buying & selling prices."
				),
				"blue"
			);
		} else {
			frm.set_intro(
				__(
					"Laboratory Library — buy lab services via Purchase Invoice (non-stock). Upload scope files and import CSV scope rows from Library menu."
				),
				"blue"
			);
		}
		frm.add_custom_button(__("Upload Lab / Scope"), () => {
			instacertify.open_laboratory_upload({
				laboratory_name: frm.doc.laboratory_name,
				location: frm.doc.location,
				on_done(name) {
					if (name === frm.doc.name) frm.reload_doc();
					else frappe.set_route("Form", "IC Laboratory", name);
				},
			});
		}, __("Library"));
		if (!frm.is_new()) {
			frm.add_custom_button(__("Import Scope CSV"), () => {
				instacertify.open_lab_scope_csv_import(frm);
			}, __("Library"));
		}
		frm.add_custom_button(__("New Testing Quotation"), () => {
			frappe.new_doc("Quotation", {
				ic_quotation_type: "Testing",
				quotation_to: "Customer",
			});
		}, __("Actions"));
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
		if (frm.is_new()) {
			const wanted = cint(frm.doc.is_return) ? "INV-RET-.#####" : "INV-.#####";
			if (!frm.doc.naming_series || String(frm.doc.naming_series).indexOf("SINV") >= 0) {
				frm.set_value("naming_series", wanted);
			}
		}
		frm.set_intro(
			__("Consulting billing: sell services to customers as non-stock items — warehouse is not required. Series: INV-00001 …"),
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
		if (!(route || "").includes("Instacertify")) return;
		if (instacertify.has_home_root()) {
			instacertify.bind_summary_card_clicks(document);
			return;
		}
		const $page = $(".workspace-body, .workspace-sidebar + .layout-main-section, .page-body, .workspace-page").first();
		if ($page.length && !$page.find(".ic-greeting").length) {
			instacertify.render_home_banner($page);
		}
	};
	setTimeout(tryInject, 800);
	setTimeout(tryInject, 2000);
});

// --- Lead capture: zippy new form + quick dialog entry ---
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
		frm.set_df_property("ic_party_name", "label", __("Name / company"));
		frm.set_df_property("ic_party_name", "description", __("Person or firm — enough to get started"));
		frm.set_df_property("ic_call_remarks", "label", __("What they need"));
		frm.set_df_property("ic_call_remarks", "description", __("One line is fine"));
		frm.set_df_property("ic_next_contact_date", "label", __("Call back on"));
		if (!frm.doc.country && frm.is_new()) {
			frm.set_value("country", "India");
		}
		if (!frm.doc.ic_party_name) {
			const party = frm.doc.company_name || frm.doc.lead_name || frm.doc.first_name;
			if (party) frm.set_value("ic_party_name", party);
		}
		if (frm.is_new()) {
			instacertify.apply_zippy_lead_capture(frm);
			if (!frm.doc.ic_next_contact_date) {
				frm.set_value("ic_next_contact_date", frappe.datetime.add_days(frappe.datetime.get_today(), 1));
			}
			if (!frm.doc.ic_assigned_salesperson && frappe.session.user !== "Guest") {
				frm.set_value("ic_assigned_salesperson", frappe.session.user);
			}
			frm.page.set_primary_action(__("Save Lead"), () => frm.save());
		} else {
			instacertify.clear_zippy_lead_capture(frm);
			instacertify.add_helpdesk_buttons(frm, {
				lead: frm.doc.name,
				contact_person: frm.doc.lead_name || frm.doc.ic_party_name || frm.doc.company_name,
				contact_email: frm.doc.email_id,
				contact_phone: frm.doc.mobile_no || frm.doc.phone,
				channel: "Internal",
			});
			instacertify.load_lead_related(frm);
			instacertify.render_lead_reminder_banner(frm);
			frm.add_custom_button(__("Create Quotation"), () => {
				frappe.model.open_mapped_doc({
					method: "erpnext.crm.doctype.lead.lead.make_quotation",
					frm: frm,
				});
			}, __("Create"));
			frm.add_custom_button(__("Open Dashboard"), () => {
				instacertify.go_home();
			}, __("View"));
			frm.add_custom_button(__("Lead Reminder Hub"), () => {
				instacertify.go_home();
			}, __("View"));
		}
	},
	ic_next_contact_date(frm) {
		instacertify.render_lead_reminder_banner(frm);
	},
	ic_call_remarks(frm) {
		instacertify.render_lead_reminder_banner(frm);
	},
	ic_lead_connected(frm) {
		instacertify.render_lead_reminder_banner(frm);
	},
	ic_assigned_salesperson(frm) {
		instacertify.render_lead_reminder_banner(frm);
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
		if (frm.is_new() && !frm.__ic_lead_show_all) {
			const need = src === "Consultant" || src === "Reference";
			frm.toggle_display("ic_consultant_referral", need);
		}
	},
});

instacertify.ZIPPY_LEAD_HIDE = [
	"salutation",
	"first_name",
	"middle_name",
	"last_name",
	"job_title",
	"gender",
	"source",
	"company_name",
	"website",
	"industry",
	"market_segment",
	"territory",
	"campaign_name",
	"fax",
	"whatsapp_no",
	"phone_ext",
	"annual_revenue",
	"no_of_employees",
	"image",
	"language",
	"disabled",
	"ic_company_size",
	"ic_section_company_extra",
	"ic_factory_address",
	"ic_gst_number",
	"ic_state",
	"ic_request_category",
	"ic_expected_timeline",
	"ic_estimated_value",
	"ic_priority",
	"ic_assigned_operations_manager",
	"ic_remarks",
	"ic_last_contacted",
	"ic_lead_connected",
	"ic_section_pipeline",
	"ic_pipeline_stage",
	"qualification_status",
	"company",
];

instacertify.apply_zippy_lead_capture = function (frm) {
	if (!frm.layout) return;
	if (frm.set_intro) {
		frm.set_intro(
			__(
				"Quick capture — name, phone, and what they need. Save now; add GST, factory, and pipeline later."
			),
			"blue"
		);
	}
	const hide = !frm.__ic_lead_show_all;
	(instacertify.ZIPPY_LEAD_HIDE || []).forEach((f) => {
		if (frm.fields_dict[f]) frm.toggle_display(f, !hide);
	});
	if (frm.fields_dict.ic_consultant_referral) {
		const src = frm.doc.ic_lead_source_detail;
		const need = src === "Consultant" || src === "Reference";
		frm.toggle_display("ic_consultant_referral", hide ? true : need);
	}
	const btnLabel = hide ? __("Show all fields") : __("Simple view");
	frm.remove_custom_button(__("Show all fields"));
	frm.remove_custom_button(__("Simple view"));
	frm.add_custom_button(btnLabel, () => {
		frm.__ic_lead_show_all = hide;
		instacertify.apply_zippy_lead_capture(frm);
	});
};

instacertify.clear_zippy_lead_capture = function (frm) {
	if (frm.set_intro) frm.set_intro(null);
	(instacertify.ZIPPY_LEAD_HIDE || []).forEach((f) => {
		if (frm.fields_dict[f]) frm.toggle_display(f, true);
	});
	frm.remove_custom_button(__("Show all fields"));
	frm.remove_custom_button(__("Simple view"));
};

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

frappe.listview_settings["IC Expense Claim"] = {
	add_fields: ["status", "category", "amount", "expense_date"],
	get_indicator(doc) {
		const map = {
			Draft: ["Draft", "gray", "status,=,Draft"],
			Submitted: ["Submitted", "orange", "status,=,Submitted"],
			Approved: ["Approved", "green", "status,=,Approved"],
			Rejected: ["Rejected", "red", "status,=,Rejected"],
			Reimbursed: ["Reimbursed", "blue", "status,=,Reimbursed"],
		};
		return map[doc.status] || [__(doc.status || "Draft"), "gray", "status,=," + (doc.status || "Draft")];
	},
	onload(listview) {
		listview.page.add_inner_button(__("File New Expense"), () => {
			if (window.instacertify && instacertify.open_expense_file) {
				instacertify.open_expense_file();
			} else {
				frappe.new_doc("IC Expense Claim");
			}
		});
	},
};

// Quote Format + Laboratory libraries — list upload actions
frappe.listview_settings["IC Quotation Template"] = {
	onload(listview) {
		listview.page.add_inner_button(__("Upload Quote Format"), () => {
			instacertify.open_quote_format_upload();
		});
		listview.page.add_inner_button(__("Download Upload Template"), () => {
			frappe.call({
				method: "instacertify.setup.library_upload.download_quote_format_upload_template",
				callback(r) {
					const m = r.message || {};
					if (m.file_url) window.open(m.file_url, "_blank");
				},
			});
		});
	},
};

frappe.listview_settings["IC Laboratory"] = {
	onload(listview) {
		listview.page.add_inner_button(__("Upload Lab / Scope"), () => {
			instacertify.open_laboratory_upload();
		});
		listview.page.add_inner_button(__("Download Scope CSV Template"), () => {
			frappe.call({
				method: "instacertify.setup.library_upload.download_lab_scope_template",
				callback(r) {
					const m = r.message || {};
					if (m.file_url) window.open(m.file_url, "_blank");
				},
			});
		});
	},
};

// Project list — tile board entry + indicators
frappe.listview_settings["Project"] = {
	add_fields: [
		"status",
		"percent_complete",
		"ic_project_stage",
		"ic_priority",
		"ic_deadline",
		"ic_assigned_employee",
		"customer",
	],
	get_indicator(doc) {
		const priority = doc.ic_priority || "Medium";
		const colors = { Urgent: "red", High: "orange", Medium: "blue", Low: "gray" };
		const stage = doc.ic_project_stage || doc.status || "";
		return [__(stage || priority), colors[priority] || "blue", "status,=," + (doc.status || "")];
	},
	onload(listview) {
		listview.page.add_inner_button(__("Tile Board"), () => {
			frappe.set_route("project-board");
		});
		listview.page.add_inner_button(__("New Project"), () => {
			frappe.new_doc("Project");
		});
	},
};

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

// --- Project team chat / collaboration ---
instacertify.render_project_chat_panel = function (frm) {
	if (frm.is_new() || !frm.fields_dict.ic_progress_html) return;
	const wrap_id = "ic-project-chat-inline";
	let host = frm.fields_dict.ic_progress_html.$wrapper;
	if (!host || !host.length) return;
	if (!host.find("#" + wrap_id).length) {
		host.append(`
			<div id="${wrap_id}" class="ic-project-chat">
				<div class="ic-project-chat-head">
					<div>
						<strong>${__("Team chat")}</strong>
						<span class="text-muted"> · ${__("Discuss this project with teammates")}</span>
					</div>
					<a href="/app/team-collaboration" class="btn btn-xs btn-default">${__("All project chats")}</a>
				</div>
				<div class="ic-project-chat-log" id="ic-project-chat-log-${frm.doc.name}"></div>
				<div class="ic-project-chat-compose">
					<textarea class="form-control" rows="2" placeholder="${__("Write a message…")}"></textarea>
					<button class="btn btn-primary btn-sm ic-chat-send">${__("Send")}</button>
				</div>
			</div>
		`);
		host.find(".ic-chat-send").on("click", () => {
			const $ta = host.find("textarea");
			const message = ($ta.val() || "").trim();
			if (!message) return;
			frappe.call({
				method: "instacertify.collaboration.api.post_project_message",
				args: { project: frm.doc.name, message },
				freeze: true,
				callback() {
					$ta.val("");
					instacertify.load_project_chat(frm);
				},
			});
		});
	}
	instacertify.load_project_chat(frm);
};

instacertify.load_project_chat = function (frm) {
	const $log = $(`#ic-project-chat-log-${frm.doc.name}`);
	if (!$log.length) return;
	frappe.call({
		method: "instacertify.collaboration.api.get_project_messages",
		args: { project: frm.doc.name, limit: 60 },
		callback(r) {
			const rows = (r.message && r.message.messages) || [];
			if (!rows.length) {
				$log.html(`<div class="text-muted">${__("No messages yet — start the conversation.")}</div>`);
				return;
			}
			$log.html(
				rows
					.map((m) => {
						const mine = m.is_mine ? "mine" : "";
						const attach = m.attachment
							? ` <a href="${frappe.utils.escape_html(m.attachment)}" target="_blank">${__("Attachment")}</a>`
							: "";
						return `<div class="ic-chat-bubble ${mine}">
							<div class="ic-chat-meta">${frappe.utils.escape_html(m.sender_name || m.sender || "")} · ${frappe.utils.escape_html(m.time_label || "")}</div>
							<div class="ic-chat-body">${m.message || frappe.utils.escape_html(m.plain || "")}${attach}</div>
						</div>`;
					})
					.join("")
			);
			$log.scrollTop($log[0].scrollHeight);
		},
	});
};

instacertify.open_project_document_share_dialog = function (frm) {
	if (!frm.doc.customer) {
		frappe.msgprint({
			title: __("Customer required"),
			message: __("Set a Customer on this project before sharing a document list."),
			indicator: "orange",
		});
		return;
	}

	const d = new frappe.ui.Dialog({
		title: __("Generate / Share Document List with Customer"),
		size: "large",
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "intro",
				options: `<p class="text-muted">${__(
					"Pick a document checklist from the dropdown (or leave blank for the default list). This generates the share link for the customer."
				)}</p>`,
			},
			{
				fieldname: "title",
				fieldtype: "Data",
				label: __("List title"),
				default: __("Documents for {0}", [frm.doc.project_name || frm.doc.name]),
			},
			{
				fieldname: "template",
				fieldtype: "Link",
				label: __("Document checklist (dropdown)"),
				options: "IC Document Checklist Template",
				get_query() {
					return { filters: { is_active: 1 } };
				},
				description: __("Select from saved document lists — e.g. BIS Certification Documents"),
			},
			{
				fieldname: "preview_html",
				fieldtype: "HTML",
				label: __("Documents in selected list"),
			},
			{
				fieldname: "force_new",
				fieldtype: "Check",
				label: __("Always create a new document request"),
				default: 0,
			},
			{
				fieldname: "replace_items",
				fieldtype: "Check",
				label: __("Replace document list with selected checklist"),
				default: 1,
			},
		],
		primary_action_label: __("Generate & Share Link"),
		primary_action(values) {
			frappe.call({
				method: "instacertify.documents.api.create_document_request_for_project",
				args: {
					project: frm.doc.name,
					title: values.title,
					template: values.template || null,
					force_new: values.force_new ? 1 : 0,
					replace_items: values.replace_items ? 1 : 0,
				},
				freeze: true,
				freeze_message: __("Generating document list…"),
				callback(r) {
					const m = r.message || {};
					const url = m.url;
					const docs = m.documents || [];
					const rows = docs
						.map(
							(x, i) =>
								`<tr><td>${i + 1}</td><td>${frappe.utils.escape_html(
									x.document_name || ""
								)}</td><td>${frappe.utils.escape_html(
									x.category || ""
								)}</td><td>${x.is_mandatory ? __("Yes") : __("No")}</td></tr>`
						)
						.join("");
					d.hide();
					frappe.msgprint({
						title: __("Document list shared with customer"),
						message: `
							<p>${__("Share this link so the customer can upload the documents:")}</p>
							<p><a href="${frappe.utils.escape_html(url)}" target="_blank" rel="noopener"><b>${frappe.utils.escape_html(
							url
						)}</b></a></p>
							<p class="text-muted">${__("Request")}: ${frappe.utils.escape_html(m.document_request || "")}</p>
							<table class="table table-bordered" style="margin-top:12px;">
								<thead><tr><th>#</th><th>${__("Document")}</th><th>${__("Category")}</th><th>${__(
							"Mandatory"
						)}</th></tr></thead>
								<tbody>${rows || `<tr><td colspan="4">${__("No documents")}</td></tr>`}</tbody>
							</table>
						`,
						indicator: "green",
					});
					if (url && navigator.clipboard) {
						navigator.clipboard.writeText(url).catch(() => {});
						frappe.show_alert({ message: __("Link copied"), indicator: "green" });
					}
					if (m.document_request) {
						frappe.set_route("Form", "IC Document Request", m.document_request);
					}
				},
			});
		},
	});

	const render_preview = (template) => {
		const $wrap = $(d.fields_dict.preview_html.wrapper);
		if (!template) {
			$wrap.html(
				`<p class="text-muted">${__(
					"No checklist selected — a default document list will be used."
				)}</p>`
			);
			return;
		}
		$wrap.html(`<p class="text-muted">${__("Loading…")}</p>`);
		frappe.call({
			method: "instacertify.documents.api.preview_checklist_template",
			args: { template },
			callback(r) {
				const items = (r.message && r.message.items) || [];
				if (!items.length) {
					$wrap.html(`<p class="text-muted">${__("This checklist has no documents.")}</p>`);
					return;
				}
				const rows = items
					.map(
						(x, i) =>
							`<tr><td>${i + 1}</td><td>${frappe.utils.escape_html(
								x.document_name || ""
							)}</td><td>${frappe.utils.escape_html(x.category || "")}</td><td>${
								x.is_mandatory ? __("Yes") : __("No")
							}</td></tr>`
					)
					.join("");
				$wrap.html(`
					<table class="table table-bordered table-condensed" style="margin:0;">
						<thead><tr><th>#</th><th>${__("Document")}</th><th>${__("Category")}</th><th>${__(
					"Mandatory"
				)}</th></tr></thead>
						<tbody>${rows}</tbody>
					</table>
				`);
			},
		});
	};

	d.fields_dict.template.df.onchange = () => {
		render_preview(d.get_value("template"));
	};
	d.show();
	render_preview(null);
};

instacertify.open_project_chat = function (frm) {
	const d = new frappe.ui.Dialog({
		title: __("Team chat — {0}", [frm.doc.project_name || frm.doc.name]),
		size: "large",
		fields: [{ fieldtype: "HTML", fieldname: "chat_html" }],
	});
	d.show();
	const $body = $(d.fields_dict.chat_html.wrapper);
	$body.html(`
		<div class="ic-project-chat dialog">
			<div class="ic-project-chat-log" id="ic-chat-dialog-log"></div>
			<div class="ic-project-chat-compose">
				<textarea class="form-control" rows="3" placeholder="${__("Write a message…")}"></textarea>
				<button class="btn btn-primary btn-sm" id="ic-chat-dialog-send">${__("Send")}</button>
			</div>
		</div>
	`);
	const refresh = () => {
		frappe.call({
			method: "instacertify.collaboration.api.get_project_messages",
			args: { project: frm.doc.name, limit: 100 },
			callback(r) {
				const $log = $body.find("#ic-chat-dialog-log");
				const rows = (r.message && r.message.messages) || [];
				$log.html(
					rows.length
						? rows
								.map((m) => {
									const mine = m.is_mine ? "mine" : "";
									return `<div class="ic-chat-bubble ${mine}">
										<div class="ic-chat-meta">${frappe.utils.escape_html(m.sender_name || m.sender || "")} · ${frappe.utils.escape_html(m.time_label || "")}</div>
										<div class="ic-chat-body">${m.message || frappe.utils.escape_html(m.plain || "")}</div>
									</div>`;
								})
								.join("")
						: `<div class="text-muted">${__("No messages yet.")}</div>`
				);
				$log.scrollTop($log[0].scrollHeight);
			},
		});
	};
	$body.find("#ic-chat-dialog-send").on("click", () => {
		const message = ($body.find("textarea").val() || "").trim();
		if (!message) return;
		frappe.call({
			method: "instacertify.collaboration.api.post_project_message",
			args: { project: frm.doc.name, message },
			callback() {
				$body.find("textarea").val("");
				refresh();
				instacertify.load_project_chat(frm);
			},
		});
	});
	refresh();
};

// --- Team calendar / Event sessions ---
frappe.ui.form.on("Event", {
	refresh(frm) {
		if (frm.is_new()) {
			if (!frm.doc.event_category) frm.set_value("event_category", "Meeting");
			if (frm.doc.send_reminder == null) frm.set_value("send_reminder", 1);
			if (frm.fields_dict.ic_notify_minutes && !frm.doc.ic_notify_minutes) {
				frm.set_value("ic_notify_minutes", 30);
			}
		}
		frm.add_custom_button(__("Add Team Members"), () => {
			instacertify.pick_team_participants(frm);
		}, __("Participants"));
		frm.add_custom_button(__("Open Calendar View"), () => {
			frappe.set_route("List", "Event", "Calendar");
		}, __("View"));
	},
});

instacertify.pick_team_participants = function (frm) {
	frappe.call({
		method: "instacertify.calendar.events.get_team_users",
		callback(r) {
			const users = r.message || [];
			const d = new frappe.ui.Dialog({
				title: __("Add teammates to this session"),
				fields: [
					{
						fieldname: "users",
						fieldtype: "MultiCheck",
						label: __("Team members"),
						options: users.map((u) => ({
							label: `${u.full_name || u.name} (${u.name})`,
							value: u.name,
							checked: false,
						})),
						columns: 1,
					},
				],
				primary_action_label: __("Add"),
				primary_action(values) {
					const selected = values.users || [];
					const existing = new Set(
						(frm.doc.event_participants || [])
							.filter((p) => p.reference_doctype === "User")
							.map((p) => p.reference_docname)
					);
					selected.forEach((user) => {
						if (existing.has(user)) return;
						frm.add_child("event_participants", {
							reference_doctype: "User",
							reference_docname: user,
							email: user,
						});
					});
					frm.refresh_field("event_participants");
					d.hide();
					frappe.show_alert({ message: __("Participants added — save to notify them"), indicator: "green" });
				},
			});
			d.show();
		},
	});
};

instacertify.schedule_team_session = function () {
	frappe.call({
		method: "instacertify.calendar.events.get_team_users",
		callback(r) {
			const users = r.message || [];
			const start = moment().add(1, "hour").startOf("hour");
			const d = new frappe.ui.Dialog({
				title: __("Schedule team session"),
				fields: [
					{ fieldname: "subject", fieldtype: "Data", label: __("Subject"), reqd: 1 },
					{ fieldname: "starts_on", fieldtype: "Datetime", label: __("Starts on"), reqd: 1, default: start.format("YYYY-MM-DD HH:mm:ss") },
					{ fieldname: "ends_on", fieldtype: "Datetime", label: __("Ends on"), default: start.clone().add(1, "hour").format("YYYY-MM-DD HH:mm:ss") },
					{ fieldname: "location", fieldtype: "Data", label: __("Location / Meet link") },
					{
						fieldname: "event_type",
						fieldtype: "Select",
						label: __("Visibility"),
						options: "Public\nPrivate",
						default: "Public",
						description: __("Public = visible on team calendar. Private = participants only."),
					},
					{
						fieldname: "participants",
						fieldtype: "MultiCheck",
						label: __("Book for teammates"),
						options: users.map((u) => ({
							label: `${u.full_name || u.name}`,
							value: u.name,
							checked: false,
						})),
						columns: 1,
					},
					{ fieldname: "description", fieldtype: "Small Text", label: __("Notes") },
				],
				primary_action_label: __("Book session"),
				primary_action(values) {
					frappe.call({
						method: "instacertify.calendar.events.create_team_session",
						args: {
							subject: values.subject,
							starts_on: values.starts_on,
							ends_on: values.ends_on,
							location: values.location,
							event_type: values.event_type,
							description: values.description,
							participants: values.participants || [],
						},
						freeze: true,
						freeze_message: __("Booking session…"),
						callback(res) {
							d.hide();
							const name = res.message && res.message.name;
							frappe.show_alert({
								message: __("Session booked. Participants get a 30‑minute reminder before start."),
								indicator: "green",
							});
							if (name) frappe.set_route("Form", "Event", name);
						},
					});
				},
			});
			d.show();
		},
	});
};

// Home dashboard: Schedule session link
$(document).on("click", "a.ic-schedule-session", function (e) {
	e.preventDefault();
	if (instacertify.schedule_team_session) {
		instacertify.schedule_team_session();
	} else {
		frappe.new_doc("Event");
	}
});
