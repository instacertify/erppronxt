/*! Instacertify Desk JS */
frappe.provide("instacertify");

instacertify.brand = {
	primary: "#0D47A1",
	accent: "#F26D21",
	surface: "#E7F1FC",
	white: "#FFFFFF",
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
		instacertify.enable_full_width_desk();
	} catch (e) {
		/* ignore */
	}
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

/** Stretch desk content next to the sidebar — correct Frappe localStorage key is container_fullwidth. */
instacertify.enable_full_width_desk = function () {
	try {
		localStorage.setItem("container_fullwidth", "true");
		localStorage.container_fullwidth = "true";
	} catch (e) {
		/* ignore */
	}
	if (document.body) {
		document.body.classList.add("full-width");
	}
	$(document.body).addClass("full-width");
	try {
		if (frappe.ui && frappe.ui.toolbar && frappe.ui.toolbar.set_fullwidth_if_enabled) {
			frappe.ui.toolbar.set_fullwidth_if_enabled();
		}
	} catch (e) {
		/* ignore */
	}
	// Keep home content flush beside the desk sidebar (tiny pad only)
	const pad = "4px";
	$(".page-body.container, .container.page-body").css({
		maxWidth: "100%",
		width: "100%",
		paddingLeft: 0,
		paddingRight: 0,
		marginLeft: 0,
		marginRight: 0,
	});
	$("[data-page-route='Workspaces'] .layout-main, [data-page-route='instacertify-home'] .layout-main").css({
		maxWidth: "none",
		width: "100%",
		marginLeft: 0,
		marginRight: 0,
	});
	$(".layout-main-section-wrapper, .layout-main-section").css({
		maxWidth: "none",
		width: "100%",
		paddingLeft: pad,
		paddingRight: pad,
	});
};

/** Never leave users on the generic ERPNext Home workspace (wrong landing / empty). */
$(document).on("page-change", function () {
	try {
		instacertify.enable_full_width_desk();
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
				options: "Consulting\nTesting\nRenewal\nOther",
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
					"Select PDF/DOCX from My Device or File Library. For bulk create, use CSV/Excel import on Quote Format Library."
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
		`<span class="ic-dl-quote-tpl-wrap" style="margin-right:auto;display:inline-flex;gap:6px;">
			<button type="button" class="btn btn-default btn-sm ic-dl-quote-xlsx">${__("Excel Template")}</button>
			<button type="button" class="btn btn-default btn-sm ic-dl-quote-csv">${__("CSV Template")}</button>
		</span>`
	);
	function dl(fmt) {
		frappe.call({
			method: "instacertify.setup.library_upload.download_quote_format_upload_template",
			args: { fmt },
			callback(r) {
				const m = r.message || {};
				if (m.file_url) window.open(m.file_url, "_blank");
			},
		});
	}
	d.$wrapper.find(".ic-dl-quote-xlsx").on("click", () => dl("xlsx"));
	d.$wrapper.find(".ic-dl-quote-csv").on("click", () => dl("csv"));
	d.show();
	instacertify.add_file_manager_hint(d, "file");
};

/** Upload dialog → create/update IC Laboratory with name + scope file / spreadsheet. */
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
				fieldname: "status",
				fieldtype: "Select",
				label: __("Status"),
				options: "Active\nInactive",
				default: opts.status || "Active",
			},
			{
				fieldname: "location",
				fieldtype: "Data",
				label: __("Location"),
				default: opts.location || "",
			},
			{
				fieldname: "city",
				fieldtype: "Data",
				label: __("City"),
				default: opts.city || "",
			},
			{
				fieldname: "address",
				fieldtype: "Small Text",
				label: __("Address"),
				default: opts.address || "",
			},
			{
				fieldname: "accreditation_scope",
				fieldtype: "Small Text",
				label: __("Accreditation Scope (text)"),
				description: __("Describe tests / standards covered — editable later on the form"),
				default: opts.accreditation_scope || "",
			},
			{
				fieldname: "accreditation_details",
				fieldtype: "Small Text",
				label: __("Accreditation Details"),
				default: opts.accreditation_details || "",
			},
			{
				fieldname: "scope_file",
				fieldtype: "Attach",
				label: __("Scope Sheet / PDF / CSV / Excel"),
				description: __(
					"PDF attaches as scope sheet. CSV/Excel also fills the pricing table (test rows)."
				),
				options: instacertify.attach_options,
			},
			{
				fieldname: "import_scopes_from_file",
				fieldtype: "Check",
				label: __("Import scope rows from CSV/Excel"),
				default: 1,
			},
			{
				fieldname: "contact_person",
				fieldtype: "Data",
				label: __("Contact Person"),
				default: opts.contact_person || "",
			},
			{
				fieldname: "email",
				fieldtype: "Data",
				label: __("Email"),
				options: "Email",
				default: opts.email || "",
			},
			{
				fieldname: "phone",
				fieldtype: "Data",
				label: __("Phone"),
				options: "Phone",
				default: opts.phone || "",
			},
			{
				fieldname: "website",
				fieldtype: "Data",
				label: __("Website"),
				options: "URL",
				default: opts.website || "",
			},
		],
		primary_action_label: __("Save to Library"),
		primary_action(values) {
			// Attach fields can lag — read from the control directly
			const scope_file =
				(d.get_value && d.get_value("scope_file")) ||
				(values && values.scope_file) ||
				"";
			values = Object.assign({}, values, { scope_file });
			if (!values.accreditation_scope && !values.scope_file) {
				frappe.msgprint(__("Add scope text or upload a scope file (PDF / CSV / Excel)."));
				return;
			}
			frappe.call({
				method: "instacertify.setup.library_upload.create_laboratory_from_upload",
				args: values,
				freeze: true,
				freeze_message: __("Saving laboratory…"),
				callback(r) {
					d.hide();
					const m = r.message || {};
					let msg = __("Laboratory saved: {0}", [m.laboratory_name]);
					if (m.scopes_imported || m.scopes_updated) {
						msg +=
							" — " +
							__("scopes +{0} / updated {1}", [
								m.scopes_imported || 0,
								m.scopes_updated || 0,
							]);
					}
					frappe.show_alert({ message: msg, indicator: "green" });
					if (opts.on_done) opts.on_done(m.laboratory);
					else frappe.set_route("Form", "IC Laboratory", m.laboratory);
				},
			});
		},
	});
	d.$wrapper.find(".modal-footer").prepend(
		`<span style="margin-right:auto;display:flex;gap:6px;">
			<button type="button" class="btn btn-default btn-sm ic-dl-lab-xlsx">${__("Excel Template")}</button>
			<button type="button" class="btn btn-default btn-sm ic-dl-lab-csv">${__("CSV Template")}</button>
		</span>`
	);
	const dl = (fmt) => {
		frappe.call({
			method: "instacertify.setup.library_upload.download_lab_scope_template",
			args: { fmt },
			callback(r) {
				const m = r.message || {};
				if (m.file_url) window.open(m.file_url, "_blank");
			},
		});
	};
	d.$wrapper.find(".ic-dl-lab-xlsx").on("click", () => dl("xlsx"));
	d.$wrapper.find(".ic-dl-lab-csv").on("click", () => dl("csv"));
	d.show();
	instacertify.add_file_manager_hint(d, "scope_file");
};

instacertify.open_lab_scope_csv_import = function (frm) {
	const d = new frappe.ui.Dialog({
		title: __("Import Laboratory Scope (CSV / Excel)"),
		fields: [
			{
				fieldname: "help",
				fieldtype: "HTML",
				options: `<p class="text-muted">${__(
					"Headers: test_name, applicable_standard, category, selling_price, purchase_price, currency, is_active. Matching test + standard updates the row."
				)}</p>`,
			},
			{
				fieldname: "file",
				fieldtype: "Attach",
				label: __("CSV or Excel File"),
				reqd: 1,
				description: __("Select from My Device or File Library (internal drive)."),
				options: instacertify.attach_options,
			},
		],
		primary_action_label: __("Import"),
		primary_action(values) {
			const file_url =
				(d.get_value && d.get_value("file")) || (values && values.file) || "";
			if (!file_url) {
				frappe.msgprint(__("Please attach a CSV or Excel file first."));
				return;
			}
			frappe.call({
				method: "instacertify.setup.library_upload.import_laboratory_scopes_csv",
				args: { laboratory: frm.doc.name, file_url },
				freeze: true,
				callback(r) {
					d.hide();
					const m = r.message || {};
					frappe.show_alert({
						message: __("Scopes: +{0} added, {1} updated", [
							m.added || 0,
							m.updated || 0,
						]),
						indicator: "green",
					});
					frm.reload_doc();
				},
			});
		},
	});
	d.$wrapper.find(".modal-footer").prepend(
		`<span style="margin-right:auto;display:flex;gap:6px;">
			<button type="button" class="btn btn-default btn-sm ic-dl-scope-xlsx">${__("Excel Template")}</button>
			<button type="button" class="btn btn-default btn-sm ic-dl-scope-csv">${__("CSV Template")}</button>
		</span>`
	);
	const dl = (fmt) => {
		frappe.call({
			method: "instacertify.setup.library_upload.download_lab_scope_template",
			args: { fmt },
			callback(r) {
				const m = r.message || {};
				if (m.file_url) window.open(m.file_url, "_blank");
			},
		});
	};
	d.$wrapper.find(".ic-dl-scope-xlsx").on("click", () => dl("xlsx"));
	d.$wrapper.find(".ic-dl-scope-csv").on("click", () => dl("csv"));
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

/** Show Workspace Shortcut icons inside tiles (Frappe stores icon but does not render it). */
(function patchShortcutIcons() {
	function paint() {
		if (!window.frappe || !frappe.utils || !frappe.utils.icon) return;
		document.querySelectorAll(".widget.shortcut-widget-box").forEach((el) => {
			const title = el.querySelector(".widget-title");
			if (!title || title.querySelector(".ic-shortcut-icon")) return;
			const name = (el.getAttribute("data-widget-name") || "").trim();
			let iconName = "file";
			try {
				const page = frappe.workspace && (frappe.workspace.page || frappe.workspace);
				const items =
					(page && page.shortcuts) ||
					(frappe.workspace && frappe.workspace.current_page && frappe.workspace.current_page.shortcuts) ||
					[];
				const hit = (items || []).find(
					(s) => (s.label || s.name || "") === name || __(s.label || "") === name
				);
				if (hit && hit.icon) iconName = hit.icon;
			} catch (e) {
				/* ignore */
			}
			// Fallback: map common labels
			const map = {
				Leads: "users",
				Customers: "building",
				Quotations: "file-text",
				Projects: "briefcase",
				"Project Board": "layout-grid",
				"Team Collaboration": "message-circle",
				"Team Calendar": "calendar",
				"Testing Requests": "flask-conical",
				Laboratories: "microscope",
				"Quote Format Library": "book-open",
				Samples: "package",
				"Documents Collection Sheets": "clipboard-list",
				"Sample Dispatch Sheets": "truck",
				Helpdesk: "headset",
				"Sales Invoice": "receipt",
				"Purchase Invoice": "shopping-cart",
				Asset: "boxes",
				"GSTR-1": "badge-indian-rupee",
				"GSTR-3B": "calculator",
				"GST Settings": "settings",
				"HRMS Lifecycle": "id-card",
				"File Expense": "wallet",
				"Lead Reminders": "phone",
				"Job Applicant": "user-plus",
				"Job Offer": "file-check",
				Employee: "square-user-round",
				"Employee Onboarding": "user-star",
				"Joining Letters": "mail",
				Attendance: "calendar-check",
				"Leave Application": "plane",
				"Salary Slip": "banknote",
				"Payroll Entry": "circle-dollar-sign",
				"Expense Claim": "wallet",
				"Employee Separation": "log-out",
				"Full and Final": "scale",
			};
			if (map[name]) iconName = map[name];
			const wrap = document.createElement("span");
			wrap.className = "ic-shortcut-icon";
			wrap.setAttribute("aria-hidden", "true");
			wrap.innerHTML = frappe.utils.icon(iconName, "md");
			title.prepend(wrap);
		});
	}
	const run = () => {
		try {
			paint();
		} catch (e) {
			/* ignore */
		}
	};
	$(document).on("page-change", () => setTimeout(run, 120));
	$(document).ready(() => setTimeout(run, 400));
	setTimeout(run, 800);
})();

/**
 * Desk-wide line icons for Previous / Next / Back / Print / Save and other actions.
 * Frappe already icons some controls; this fills gaps and keeps styling consistent.
 */
(function icActionButtonIcons() {
	const LABEL_ICONS = {
		Save: "save",
		Submit: "circle-check",
		Update: "pencil",
		Edit: "pencil",
		Amend: "rotate-ccw",
		Cancel: "x",
		Close: "x",
		Delete: "trash-2",
		Print: "printer",
		PDF: "file-text",
		Email: "mail",
		Reload: "refresh-cw",
		Rename: "text-cursor-input",
		Duplicate: "copy",
		New: "plus",
		Add: "plus",
		Back: "arrow-left",
		Previous: "chevron-left",
		Next: "chevron-right",
		"Previous Document": "chevron-left",
		"Next Document": "chevron-right",
		Refresh: "refresh-cw",
		Filter: "filter",
		Filters: "filter",
		Export: "download",
		Import: "upload",
		Download: "download",
		Upload: "upload",
		Share: "share-2",
		Assign: "user-plus",
		Comment: "message-circle",
		Attachments: "paperclip",
		Links: "link",
		"Show Links": "link",
		"Jump to field": "search",
		"Remind Me": "bell",
		Follow: "eye",
		Unfollow: "eye-off",
		"Copy to Clipboard": "clipboard",
		"Toggle Sidebar": "panel-left",
		Discard: "ban",
		Menu: "menu",
		Actions: "ellipsis",
		Help: "circle-question-mark",
		Settings: "settings",
		Create: "plus",
		Yes: "check",
		No: "x",
		Continue: "arrow-right",
		Confirm: "check",
		Apply: "check",
		Clear: "eraser",
		Reset: "rotate-ccw",
		Search: "search",
		"List View": "list",
		Report: "chart-bar",
		Dashboard: "layout-dashboard",
	};

	function normalizeLabel(raw) {
		if (!raw) return "";
		return String(raw)
			.replace(/\s+/g, " ")
			.trim()
			.replace(/^Add\s+.+$/i, "Add");
	}

	function iconForLabel(label) {
		const n = normalizeLabel(label);
		if (LABEL_ICONS[n]) return LABEL_ICONS[n];
		const lower = n.toLowerCase();
		for (const [k, v] of Object.entries(LABEL_ICONS)) {
			if (k.toLowerCase() === lower) return v;
		}
		if (/^add\b/i.test(n)) return "plus";
		if (/print/i.test(n)) return "printer";
		if (/email|mail/i.test(n)) return "mail";
		if (/save/i.test(n)) return "save";
		if (/submit/i.test(n)) return "circle-check";
		if (/cancel|close|discard/i.test(n)) return "x";
		if (/delete|trash/i.test(n)) return "trash-2";
		if (/reload|refresh/i.test(n)) return "refresh-cw";
		if (/previous|prev\b/i.test(n)) return "chevron-left";
		if (/^next\b/i.test(n)) return "chevron-right";
		if (/^back\b/i.test(n)) return "arrow-left";
		return null;
	}

	function ensureIconOnButton($btn) {
		if (!$btn || !$btn.length) return;
		if ($btn.find(".ic-action-icon, .icon, svg.icon, svg.es-icon").length) return;
		const label =
			$btn.attr("data-label") ||
			$btn.attr("aria-label") ||
			$btn.attr("title") ||
			$btn.text();
		const iconName = iconForLabel(label);
		if (!iconName || !frappe.utils || !frappe.utils.icon) return;
		const $icon = $(
			`<span class="ic-action-icon" aria-hidden="true">${frappe.utils.icon(
				iconName,
				"sm",
				"",
				"",
				"",
				true
			)}</span>`
		);
		const $span = $btn.children("span.hidden-xs, span:not(.ic-action-icon)").first();
		if ($span.length) {
			$icon.prependTo($btn);
		} else {
			const text = ($btn.text() || "").trim();
			$btn.empty().append($icon);
			if (text) $btn.append(` <span class="ic-action-label">${frappe.utils.escape_html(text)}</span>`);
		}
		$btn.addClass("ic-has-action-icon");
	}

	function ensureIconOnMenuItem($a) {
		if (!$a || !$a.length) return;
		if ($a.find(".menu-item-icon, .ic-action-icon").length) return;
		const label = ($a.find(".menu-item-label").text() || $a.text() || "").trim();
		const iconName = iconForLabel(label);
		if (!iconName || !frappe.utils || !frappe.utils.icon) return;
		$a.prepend(
			`<span class="menu-item-icon ic-action-icon flex align-items-center">${frappe.utils.icon(
				iconName,
				"sm",
				"",
				"",
				"",
				true
			)}</span>`
		);
	}

	function ensurePrintActionIcon(page) {
		if (!page || !page.add_action_icon) return;
		const $group = page.icon_group || (page.page_actions && page.page_actions.find(".page-icon-group"));
		if (!$group || !$group.length) return;
		if ($group.find(".ic-print-action").length) return;
		// Only on form / print contexts where printing is allowed
		const frm = cur_frm;
		if (!frm || !frappe.model.can_print_doc || !frappe.model.can_print_doc(frm)) return;
		if (frm.is_new && frm.is_new()) return;
		const $btn = page.add_action_icon(
			"printer",
			() => {
				if (cur_frm) cur_frm.print_doc();
			},
			"ic-print-action",
			__("Print")
		);
		if ($btn && $btn.addClass) $btn.addClass("ic-print-action");
	}

	function decoratePage(page) {
		if (!page) return;
		try {
			ensureIconOnButton(page.btn_primary);
			ensureIconOnButton(page.btn_secondary);
			(page.page_actions || $()).find(".btn").each(function () {
				ensureIconOnButton($(this));
			});
			(page.menu || $()).find("a.dropdown-item, a.grey-link").each(function () {
				ensureIconOnMenuItem($(this));
			});
			(page.actions || $()).find("a.dropdown-item, a.grey-link").each(function () {
				ensureIconOnMenuItem($(this));
			});
			// Style existing prev/next icon buttons
			(page.icon_group || $()).find(".icon-btn").addClass("ic-line-icon-btn");
			ensurePrintActionIcon(page);
		} catch (e) {
			/* ignore */
		}
	}

	function decorateAll() {
		if (!window.frappe) return;
		// Current page
		if (frappe.container && frappe.container.page && frappe.container.page.page) {
			decoratePage(frappe.container.page.page);
		}
		if (cur_page && cur_page.page) decoratePage(cur_page.page);
		if (cur_frm && cur_frm.page) decoratePage(cur_frm.page);
		// Dialogs
		$(".modal.show .btn, .modal.in .btn").each(function () {
			ensureIconOnButton($(this));
		});
		// List / report toolbars
		$(".page-head .page-actions .btn, .standard-actions .btn").each(function () {
			ensureIconOnButton($(this));
		});
		$(".page-head .dropdown-menu a.dropdown-item, .page-head .dropdown-menu a.grey-link").each(
			function () {
				ensureIconOnMenuItem($(this));
			}
		);
	}

	const schedule = () => setTimeout(decorateAll, 80);

	$(document).on("page-change", schedule);
	$(document).on("form-refresh", schedule);
	$(document).on("shown.bs.modal", schedule);
	$(document).ready(schedule);
	setTimeout(schedule, 500);
	setTimeout(schedule, 1500);

	// Keep icons after Frappe rebuilds the toolbar
	frappe.after_ajax && frappe.after_ajax(schedule);
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
		if (frm.fields_dict.ic_assignees) {
			frm.add_custom_button(__("Assign Me"), () => {
				instacertify.add_me_as_assignee(frm, "ic_assignees");
			}, __("Actions"));
		}
		frm.add_custom_button(__("Upload Quote Format"), () => {
			instacertify.open_quote_format_upload({
				quotation_type: frm.doc.ic_quotation_type || "Consulting",
			});
		}, __("Library"));
		frm.add_custom_button(__("Quote Format Library"), () => {
			frappe.set_route("quote-format-library");
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
								<p>${__("Customer can open this link to read, download PDF, approve, or ask for revision:")}</p>
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

			frm.add_custom_button(__("Print / PDF Options"), () => {
				// Opens Frappe print view: format picker, letter head, page options, PDF
				frm.print_doc();
			}, __("Actions"));

			frm.add_custom_button(__("Download PDF"), () => {
				const fmt =
					frm.meta.default_print_format
					|| (frm.doc.ic_quotation_type === "Testing"
						? "Instacertify Testing Quotation"
						: frm.doc.ic_quotation_type
							? "Instacertify Consulting Quotation"
							: "Instacertify Quotation");
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
				frappe.route_options = {
					quotation_type: frm.doc.ic_quotation_type || undefined,
				};
				frappe.set_route("quote-format-library");
			}, __("Actions"));

			if (frm.doc.ic_quotation_template) {
				frm.add_custom_button(__("Edit Template"), () => {
					frappe.set_route("Form", "IC Quotation Template", frm.doc.ic_quotation_template);
				}, __("Actions"));
			}

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
		frm.layout && frm.$wrapper && frm.$wrapper.addClass("ic-quotation-form");
	},

	ic_quotation_type(frm) {
		instacertify.toggle_quotation_sections(frm);
		instacertify.setup_quotation_template_filter(frm);
		instacertify.render_quotation_entry_guide(frm);
		instacertify.apply_quotation_naming_series(frm);
		if (frm.doc.ic_quotation_template && !frm._ic_skip_template_apply) {
			frm.set_value("ic_quotation_template", "");
		}
	},

	ic_quotation_template(frm) {
		instacertify.render_quotation_entry_guide(frm);
		if (!frm.doc.ic_quotation_template) return;
		if (frm._ic_skip_template_apply) return;
		instacertify.apply_quote_format_to_form(frm, frm.doc.ic_quotation_template);
	},
});

instacertify.apply_quote_format_to_form = function (frm, template) {
	if (!template) return;
	frappe.call({
		method: "instacertify.quotation.events.get_quotation_template_payload",
		args: { template },
		freeze: true,
		freeze_message: __("Loading quote format…"),
		callback(r) {
			const payload = r.message || {};
			instacertify.fill_quotation_from_format_payload(frm, payload);
			frappe.show_alert({
				message: payload.message || __("Format applied — edit headings and values as needed"),
				indicator: "green",
			});
		},
	});
};

instacertify.fill_quotation_from_format_payload = function (frm, payload) {
	payload = payload || {};
	const fields = payload.fields || {};
	frm._ic_skip_template_apply = true;
	const chain = Promise.resolve();
	let p = chain;
	Object.keys(fields).forEach((key) => {
		const val = fields[key];
		if (val === undefined || val === null || val === "") {
			if (key === "ic_subject") return;
		}
		p = p.then(() => frm.set_value(key, val));
	});
	return p
		.then(() => {
			frm.clear_table("ic_cost_items");
			(payload.cost_items || []).forEach((row) => {
				frm.add_child("ic_cost_items", row);
			});
			frm.clear_table("ic_test_items");
			(payload.test_items || []).forEach((row) => {
				frm.add_child("ic_test_items", row);
			});
			frm.refresh_field("ic_cost_items");
			frm.refresh_field("ic_test_items");
			instacertify.toggle_quotation_sections(frm);
			instacertify.apply_quotation_naming_series(frm);
			instacertify.render_quotation_entry_guide(frm);
		})
		.finally(() => {
			frm._ic_skip_template_apply = false;
		});
};

instacertify.QUOTATION_TYPE_HELP = {
	Consulting: {
		title: "Consulting / Certification",
		steps: [
			"Quote type + library format are chosen first — edit title, standards, and headings below",
			"Enter commercials in Cost Items",
			"Review payment terms → Share with Customer",
		],
	},
	Service: {
		title: "Service",
		steps: [
			"Confirm the library format title, timeline, and cost lines (all editable)",
			"Adjust commercials as needed",
			"Share with Customer when ready",
		],
	},
	Testing: {
		title: "Testing",
		steps: [
			"Format may prefill testing notes — open Test Lines for Laboratory & Lab Test Scope",
			"Charges fill from the lab library; adjust samples if needed",
			"Share with Customer when ready",
		],
	},
	Renewal: {
		title: "Renewal",
		steps: [
			"Confirm renewal format headings from the library",
			"Update validity / commercial lines",
			"Share with Customer",
		],
	},
	Other: {
		title: "Other",
		steps: ["Edit service basics from the format (or fill blank)", "Add cost lines", "Share when ready"],
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
		["Other", "Custom"],
	]
		.map(([key, hint]) => {
			const active = t === key ? "active" : "";
			const slug = ({ Consulting: "consulting", Testing: "testing", Renewal: "renewal", Other: "other" })[key] || "other";
			return `<button type="button" class="ic-quote-type-chip cat-${slug} ${active}" data-type="${frappe.utils.escape_html(key)}">
				<span class="ic-quote-type-swatch" aria-hidden="true"></span>
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

// Prompt: type first → then Quote Format Library dropdown → editable form
frappe.ui.form.on("Quotation", {
	onload(frm) {
		instacertify.setup_quotation_template_filter(frm);
		frm.$wrapper && frm.$wrapper.addClass("ic-quotation-form");
		instacertify.maybe_prompt_or_apply_quote_format(frm);
	},
	refresh(frm) {
		if (frm.is_new()) {
			instacertify.maybe_prompt_or_apply_quote_format(frm);
		}
	},
});

instacertify.maybe_prompt_or_apply_quote_format = function (frm) {
	if (!frm || !frm.is_new()) return;

	// Pending payload from list-view "New Quotation" picker
	const pending = instacertify._pending_quote_format;
	if (pending && !frm._ic_format_applied_on_load) {
		frm._ic_format_applied_on_load = true;
		frm._ic_type_format_prompted = true;
		instacertify._pending_quote_format = null;
		setTimeout(() => {
			if (pending.skip) {
				frm.set_value("ic_quotation_type", pending.quotation_type || "Consulting");
				instacertify.apply_quotation_naming_series(frm);
				instacertify.toggle_quotation_sections(frm);
				instacertify.render_quotation_entry_guide(frm);
				return;
			}
			instacertify
				.fill_quotation_from_format_payload(frm, pending.payload || {})
				.then(() => {
					frappe.show_alert({
						message: __(
							"Format applied. Edit headings, values, and commercials on the form as needed."
						),
						indicator: "green",
					});
				});
		}, 200);
		return;
	}

	if (frm.doc.ic_quotation_template && frm.doc.ic_quotation_type) {
		if (!frm._ic_format_applied_on_load) {
			frm._ic_format_applied_on_load = true;
			frm._ic_type_format_prompted = true;
			setTimeout(() => {
				instacertify.apply_quote_format_to_form(frm, frm.doc.ic_quotation_template);
			}, 300);
		}
		return;
	}

	if (!frm.doc.ic_quotation_type && !frm._ic_type_format_prompted) {
		frm._ic_type_format_prompted = true;
		setTimeout(() => instacertify.open_new_quotation_type_format_dialog(frm), 150);
	}
};

/** Open type → format picker, then create a new Quotation (preferred entry from list). */
instacertify.start_new_quotation = function () {
	instacertify.open_new_quotation_type_format_dialog(null);
};

instacertify.open_new_quotation_type_format_dialog = function (frm) {
	// Four major library categories — each can have many templates
	const TYPE_OPTIONS = [
		{ value: "Consulting", label: __("Consulting"), hint: __("Certification & consultancy packs") },
		{ value: "Testing", label: __("Testing"), hint: __("Lab tests & commercials") },
		{ value: "Renewal", label: __("Renewal"), hint: __("Certificate / licence renewals") },
		{ value: "Other", label: __("Other"), hint: __("Custom / miscellaneous quotes") },
	];

	let format_map = {};
	const standalone = !frm;

	const d = new frappe.ui.Dialog({
		title: __("New Quotation"),
		size: "large",
		static: true,
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "help",
				options: `<div class="ic-quote-dialog-help">
					<div class="ic-quote-dialog-step"><strong>${__("1.")}</strong> ${__(
						"Select major category: Consulting, Testing, Renewal, or Other"
					)}</div>
					<div class="ic-quote-dialog-step"><strong>${__("2.")}</strong> ${__(
						"Choose a template already in the library for that category"
					)}</div>
					<div class="ic-quote-dialog-step text-muted">${__(
						"After start, edit headings and mark cost lines as Counted Revenue or Do Not Count Revenue (pass-through)."
					)}</div>
				</div>`,
			},
			{
				fieldname: "ic_quotation_type",
				fieldtype: "Select",
				label: __("Major Category"),
				options: TYPE_OPTIONS.map((t) => t.value).join("\n"),
				reqd: 1,
				default: "Consulting",
				description: __("Required first — loads templates from the Quote Format Library"),
			},
			{
				fieldtype: "HTML",
				fieldname: "type_chips",
				options: `<div class="ic-new-quote-type-chips">${TYPE_OPTIONS.map(
					(t) => {
						const slug = ({
							Consulting: "consulting",
							Testing: "testing",
							Renewal: "renewal",
							Other: "other",
						})[t.value] || "other";
						return `<button type="button" class="ic-new-quote-type-chip cat-${slug}" data-type="${frappe.utils.escape_html(
							t.value
						)}">
							<span class="ic-new-quote-type-swatch" aria-hidden="true"></span>
							<span class="ic-new-quote-type-name">${frappe.utils.escape_html(t.label)}</span>
							<span class="ic-new-quote-type-hint">${frappe.utils.escape_html(t.hint)}</span>
						</button>`;
					}
				).join("")}</div>`,
			},
			{
				fieldname: "ic_quotation_template",
				fieldtype: "Select",
				label: __("Template (from library)"),
				options: "",
				reqd: 1,
				description: __(
					"Templates for this category. Admins / Ops can add more via Quote Format Library upload."
				),
			},
			{
				fieldtype: "HTML",
				fieldname: "format_hint",
				options: `<div class="ic-new-quote-format-hint text-muted"></div>`,
			},
			{
				fieldname: "skip_format",
				fieldtype: "Check",
				label: __("Continue without a library format (blank quote)"),
				default: 0,
			},
		],
		primary_action_label: __("Start Quotation"),
		primary_action(values) {
			const skip = cint(values.skip_format);
			if (!skip && !values.ic_quotation_template) {
				frappe.msgprint(
					__("Select a quote format from the library, or check Continue without a library format.")
				);
				return;
			}
			const qtype = values.ic_quotation_type;

			const finish_standalone = (pending) => {
				instacertify._pending_quote_format = pending;
				d.hide();
				frappe.new_doc("Quotation", {
					ic_quotation_type: qtype,
					ic_quotation_template: skip ? "" : values.ic_quotation_template || "",
				});
			};

			if (standalone) {
				if (skip || !values.ic_quotation_template) {
					finish_standalone({ skip: 1, quotation_type: qtype });
					return;
				}
				frappe.call({
					method: "instacertify.quotation.events.get_quotation_template_payload",
					args: { template: values.ic_quotation_template },
					freeze: true,
					freeze_message: __("Loading quote format…"),
					callback(r) {
						finish_standalone({
							skip: 0,
							quotation_type: qtype,
							payload: r.message || {},
						});
					},
				});
				return;
			}

			frm._ic_skip_template_apply = true;
			frm.set_value("ic_quotation_type", qtype).then(() => {
				instacertify.apply_quotation_naming_series(frm);
				instacertify.toggle_quotation_sections(frm);
				if (skip || !values.ic_quotation_template) {
					frm._ic_skip_template_apply = false;
					d.hide();
					setTimeout(() => {
						instacertify.render_quotation_entry_guide(frm);
						frm.scroll_to_field("ic_quotation_type");
					}, 200);
					return;
				}
				frappe.call({
					method: "instacertify.quotation.events.get_quotation_template_payload",
					args: { template: values.ic_quotation_template },
					freeze: true,
					freeze_message: __("Loading quote format…"),
					callback(r) {
						const payload = r.message || {};
						instacertify
							.fill_quotation_from_format_payload(frm, payload)
							.finally(() => {
								frm._ic_skip_template_apply = false;
								d.hide();
								frappe.show_alert({
									message: __(
										"Format applied. Edit headings, values, and commercials on the form as needed."
									),
									indicator: "green",
								});
								setTimeout(() => {
									instacertify.render_quotation_entry_guide(frm);
									frm.scroll_to_field("ic_service_name") ||
										frm.scroll_to_field("ic_subject") ||
										frm.scroll_to_field("ic_quotation_type");
								}, 250);
							});
					},
					error() {
						frm._ic_skip_template_apply = false;
					},
				});
			});
		},
	});

	function set_chip_active(type) {
		d.$wrapper.find(".ic-new-quote-type-chip").each(function () {
			$(this).toggleClass("active", $(this).data("type") === type);
		});
	}

	function load_formats(type) {
		const $hint = d.$wrapper.find(".ic-new-quote-format-hint");
		$hint.text(__("Loading formats…"));
		frappe.call({
			method: "instacertify.quotation.events.list_quote_formats_for_type",
			args: { quotation_type: type },
			callback(r) {
				const formats = (r.message && r.message.formats) || [];
				format_map = {};
				formats.forEach((f) => {
					format_map[f.name] = f;
				});
				const $sel = d.fields_dict.ic_quotation_template.$input;
				if ($sel && $sel.length) {
					$sel.empty();
					if (formats.length) {
						$sel.append(`<option value="">${__("— Select a format —")}</option>`);
						formats.forEach((f) => {
							$sel.append(
								`<option value="${frappe.utils.escape_html(f.name)}">${frappe.utils.escape_html(
									f.label
								)}</option>`
							);
						});
						$hint.html(
							__(
								"{0} format(s) in library for this type. Select one to prefill headings — you can edit everything after.",
								[`<strong>${formats.length}</strong>`]
							)
						);
					} else {
						$sel.append(`<option value="">${__("No formats for this type")}</option>`);
						$hint.html(
							__(
								"No active formats for this type yet. Open Quote Format Library to add one, or continue without a format."
							)
						);
					}
				}
				d.set_value("ic_quotation_template", "");
			},
		});
	}

	d.fields_dict.ic_quotation_type.df.onchange = () => {
		const t = d.get_value("ic_quotation_type");
		set_chip_active(t);
		d.set_value("ic_quotation_template", "");
		load_formats(t);
	};

	d.fields_dict.ic_quotation_template.df.onchange = () => {
		const name = d.get_value("ic_quotation_template");
		const f = format_map[name];
		const $hint = d.$wrapper.find(".ic-new-quote-format-hint");
		if (f) {
			const note = f.template_notes
				? frappe.utils.escape_html(String(f.template_notes).slice(0, 180))
				: "";
			$hint.html(
				`<strong>${frappe.utils.escape_html(f.template_name || f.name)}</strong>` +
					(f.service_family ? ` · ${frappe.utils.escape_html(f.service_family)}` : "") +
					(note ? `<div class="text-muted" style="margin-top:4px;">${note}</div>` : "")
			);
		}
	};

	d.fields_dict.skip_format.df.onchange = () => {
		const skip = cint(d.get_value("skip_format"));
		d.set_df_property("ic_quotation_template", "reqd", skip ? 0 : 1);
	};

	d.show();
	setTimeout(() => {
		d.$wrapper.find(".ic-new-quote-type-chip").on("click", function () {
			const type = $(this).data("type");
			d.set_value("ic_quotation_type", type);
		});
		set_chip_active(d.get_value("ic_quotation_type") || "Consulting");
		load_formats(d.get_value("ic_quotation_type") || "Consulting");
	}, 50);
};

// List: primary New Quotation opens type → format picker first
frappe.listview_settings["Quotation"] = frappe.listview_settings["Quotation"] || {};
(function () {
	const prev_onload = frappe.listview_settings["Quotation"].onload;
	frappe.listview_settings["Quotation"].onload = function (listview) {
		if (prev_onload) prev_onload(listview);
		listview.page.set_primary_action(__("New Quotation"), () => {
			instacertify.start_new_quotation();
		});
		listview.page.add_inner_button(__("New (type & format)"), () => {
			instacertify.start_new_quotation();
		});
	};
})();

// Customer Related Data tab — full per-customer history + completed project files
frappe.ui.form.on("Customer", {
	refresh(frm) {
		if (!frm.doc.name || frm.is_new()) return;
		if (frm.fields_dict.ic_section_files) {
			frm.set_df_property("ic_section_files", "label", __("Customer Data Drive"));
		}
		instacertify.load_customer_related(frm);
		instacertify.add_helpdesk_buttons(frm, {
			customer: frm.doc.name,
			contact_person: frm.doc.customer_name,
			channel: "Internal",
		});
		if (!frm.__ic_drive_btn) {
			frm.__ic_drive_btn = 1;
			frm.add_custom_button(__("Open Data Drive"), () => {
				frm.scroll_to_field("ic_customer_files_html");
			});
			frm.add_custom_button(__("Sync Team Access"), () => {
				frappe.call({
					method: "instacertify.crm.customer_permissions.sync_customer_team",
					args: { customer: frm.doc.name },
					freeze: true,
					callback(r) {
						frm.reload_doc();
						const users = (r.message && r.message.users) || [];
						frappe.msgprint({
							title: __("Customer Team Access"),
							message: __(
								"Team members who can see all Customer Data: {0}",
								[users.join(", ") || __("none")]
							),
							indicator: "green",
						});
					},
				});
			});
		}
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
	const phone = frm.doc.mobile_no || frm.doc.phone || frm.doc.ic_alternate_phone || "";
	let withUser = frm.doc.ic_assigned_salesperson || frm.doc.lead_owner || "";
	try {
		if (withUser && frappe.user_info) {
			const info = frappe.user_info(withUser);
			if (info && info.fullname) withUser = info.fullname;
		}
	} catch (e) {
		/* keep id */
	}

	const intro = `
		<div class="ic-lead-form-reminder ${urgency === "red" ? "overdue" : urgency === "orange" ? "today" : ""}">
			<div class="ic-lead-form-reminder-title">${__("Lead reminder")} · ${frappe.utils.escape_html(when)}</div>
			<div class="ic-lead-form-reminder-line">
				${frappe.utils.escape_html(person)}
				${phone ? " · " + frappe.utils.escape_html(phone) : ""}
				${withUser ? " · " + frappe.utils.escape_html(withUser) : ""}
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
	const drive = d.data_drive || {};
	const files = drive.files || [];
	const counts = drive.counts || {};
	const total = drive.total || files.length || 0;
	const categories = drive.categories || [
		"Uploaded",
		"Collected Data",
		"Projects",
		"Quotes",
		"Invoices",
		"Testing",
		"Samples",
		"Documents",
		"Contracts",
		"Support",
		"Records",
	];

	const chips = [
		`<button type="button" class="ic-drive-chip active" data-cat="all">${__("All")} (${total})</button>`,
	]
		.concat(
			categories
				.filter((c) => counts[c])
				.map(
					(c) =>
						`<button type="button" class="ic-drive-chip" data-cat="${frappe.utils.escape_html(
							c
						)}">${frappe.utils.escape_html(c)} (${counts[c]})</button>`
				)
		)
		.join("");

	const rows = files
		.map((f) => {
			const cat = f.category || "Other";
			const srcDt = f.source_doctype || f.source || "";
			const srcName = f.source_name || f.project || "";
			const srcLink =
				srcDt && srcName && srcDt !== "Customer"
					? ic_doc_link(srcDt, srcName)
					: srcDt === "Customer"
						? __("Saved on customer")
						: ic_esc(srcDt || "—");
			const date = (f.creation || "").toString().slice(0, 10) || "—";
			const url = frappe.utils.escape_html(f.file_url || "#");
			const label = ic_esc(f.label || f.file_name || f.name);
			const shareCell = ic_drive_share_cell(f);
			return `<tr class="ic-drive-row" data-cat="${frappe.utils.escape_html(cat)}"
				data-file-url="${frappe.utils.escape_html(f.file_url || "")}"
				data-file-name="${frappe.utils.escape_html(f.file_name || f.label || "")}"
				data-source-doctype="${frappe.utils.escape_html(srcDt)}"
				data-source-name="${frappe.utils.escape_html(srcName)}"
				data-title="${frappe.utils.escape_html(f.label || f.file_name || "")}">
				<td class="ic-drive-file"><a href="${url}" target="_blank" rel="noopener">${label}</a></td>
				<td><span class="ic-drive-cat">${ic_esc(cat)}</span></td>
				<td>${srcLink}</td>
				<td>${ic_esc(date)}</td>
				<td class="ic-drive-share">${shareCell}</td>
			</tr>`;
		})
		.join("");

	const table = files.length
		? `<div class="ic-related-table-wrap ic-drive-table-wrap"><table class="ic-related-table ic-drive-table">
			<thead><tr>
				<th>${__("File")}</th><th>${__("Folder")}</th><th>${__("Source")}</th><th>${__("Date")}</th><th>${__("Share Report")}</th>
			</tr></thead>
			<tbody>${rows}</tbody>
		</table></div>`
		: `<div class="ic-drive-empty">${__(
				"No files yet. Upload here or sync from related quotes, projects, invoices, and documents."
			)}</div>`;

	return `
		<div class="ic-customer-drive" data-customer="${frappe.utils.escape_html(frm.doc.name)}">
			<div class="ic-drive-header">
				<div>
					<div class="ic-drive-title">${__("Customer Data Drive")}</div>
					<div class="ic-drive-sub">${__(
						"All data collected from this customer — portal uploads, data collection sheets, sample dispatch, contracts, projects, and invoices — in one place."
					)}</div>
				</div>
				<div class="ic-drive-actions">
					<button type="button" class="btn btn-primary btn-sm ic-drive-upload">${__("Upload to Drive")}</button>
					<button type="button" class="btn btn-default btn-sm ic-drive-sync">${__("Sync related files")}</button>
				</div>
			</div>
			<div class="ic-drive-chips">${chips}</div>
			${table}
		</div>
	`;
}

function ic_drive_share_cell(f) {
	if (!f.shareable) {
		return `<span class="text-muted">—</span>`;
	}
	if (f.share_url && f.access_code) {
		return `
			<div class="ic-report-share-meta">
				<button type="button" class="btn btn-xs btn-default ic-copy-share-link" data-url="${frappe.utils.escape_html(
					f.share_url
				)}">${__("Copy link")}</button>
				<span class="ic-report-code" title="${__("Customer access code")}">${__("Code")}: <b>${ic_esc(
			f.access_code
		)}</b></span>
				<button type="button" class="btn btn-xs btn-link ic-reshare-report">${__("New code")}</button>
			</div>`;
	}
	return `<button type="button" class="btn btn-xs btn-primary ic-share-report">${__(
		"Share report"
	)}</button>`;
}

function ic_bind_customer_file_actions(frm) {
	const $wrap = frm.fields_dict.ic_customer_files_html
		? $(frm.fields_dict.ic_customer_files_html.wrapper)
		: $();

	$wrap.find(".ic-drive-chip").off("click").on("click", function () {
		const cat = $(this).data("cat");
		$wrap.find(".ic-drive-chip").removeClass("active");
		$(this).addClass("active");
		$wrap.find(".ic-drive-row").each(function () {
			const rowCat = $(this).data("cat");
			$(this).toggle(cat === "all" || rowCat === cat);
		});
	});

	$wrap.find(".ic-drive-sync").off("click").on("click", () => {
		frappe.confirm(
			__(
				"Save all related files (projects, quotes, invoices, testing, documents, support) onto this customer's Data Drive? Duplicates are skipped."
			),
			() => {
				frappe.call({
					method: "instacertify.crm.events.sync_customer_data_drive",
					args: { customer: frm.doc.name },
					freeze: true,
					freeze_message: __("Syncing Data Drive…"),
					callback(r) {
						const m = r.message || {};
						frappe.show_alert({
							message: __(
								"Data Drive: saved {0} file(s), skipped {1}. Indexed {2}.",
								[m.copied || 0, m.skipped || 0, m.total_indexed || 0]
							),
							indicator: m.copied ? "green" : "orange",
						});
						instacertify.load_customer_related(frm);
					},
				});
			}
		);
	});

	// Back-compat buttons if old markup still cached
	$wrap.find(".ic-import-project-files").off("click").on("click", () => {
		$wrap.find(".ic-drive-sync").trigger("click");
	});

	$wrap.find(".ic-drive-upload, .ic-upload-customer-file").off("click").on("click", () => {
		frappe.call({
			method: "instacertify.crm.events.ensure_customer_drive_folder",
			args: { customer: frm.doc.name },
			callback(r) {
				const folder = (r.message || "Home/Attachments");
				new frappe.ui.FileUploader({
					doctype: frm.doctype,
					docname: frm.doc.name,
					frm: frm,
					folder: folder,
					allow_web_link: false,
					allow_google_drive: false,
					upload_notes: instacertify.get_attach_upload_notes
						? instacertify.get_attach_upload_notes()
						: __("Upload from this device or File Library (internal drive)."),
					on_success() {
						frappe.show_alert({ message: __("Saved to Customer Data Drive"), indicator: "green" });
						instacertify.load_customer_related(frm);
					},
				});
			},
		});
	});

	const share_report = ($row, rotate) => {
		const file_url = $row.data("file-url");
		if (!file_url) {
			frappe.msgprint(__("No file URL on this row"));
			return;
		}
		frappe.call({
			method: "instacertify.crm.report_share.create_customer_report_share",
			args: {
				customer: frm.doc.name,
				file_url,
				file_name: $row.data("file-name") || "",
				source_doctype: $row.data("source-doctype") || "",
				source_name: $row.data("source-name") || "",
				title: $row.data("title") || "",
				rotate_code: rotate ? 1 : 0,
			},
			freeze: true,
			callback(r) {
				const m = r.message || {};
				frappe.msgprint({
					title: __("Report shared with customer"),
					indicator: "green",
					message: `
						<p>${__("Send both the link and the 8-digit code to the customer.")}</p>
						<p><b>${__("Share link")}</b><br>
							<a href="${frappe.utils.escape_html(m.share_url || "#")}" target="_blank" rel="noopener">${frappe.utils.escape_html(
						m.share_url || ""
					)}</a>
							<button class="btn btn-xs btn-default ic-msg-copy-link" style="margin-left:8px">${__("Copy")}</button>
						</p>
						<p><b>${__("Access code")}</b>: <code style="font-size:1.2em;letter-spacing:0.12em">${frappe.utils.escape_html(
							m.access_code || ""
						)}</code>
							<button class="btn btn-xs btn-default ic-msg-copy-code" style="margin-left:8px">${__("Copy")}</button>
						</p>
						<p class="text-muted">${__(
							"The customer opens the link, enters this code, then can view or download the PDF."
						)}</p>`,
				});
				setTimeout(() => {
					$(".ic-msg-copy-link")
						.off("click")
						.on("click", () => {
							if (m.share_url && navigator.clipboard) navigator.clipboard.writeText(m.share_url);
							frappe.show_alert({ message: __("Link copied"), indicator: "green" });
						});
					$(".ic-msg-copy-code")
						.off("click")
						.on("click", () => {
							if (m.access_code && navigator.clipboard) navigator.clipboard.writeText(m.access_code);
							frappe.show_alert({ message: __("Code copied"), indicator: "green" });
						});
				}, 50);
				instacertify.load_customer_related(frm);
			},
		});
	};

	$wrap.find(".ic-share-report").off("click").on("click", function () {
		share_report($(this).closest("tr"), false);
	});
	$wrap.find(".ic-reshare-report").off("click").on("click", function () {
		frappe.confirm(__("Generate a new 8-digit code and share link for this report?"), () => {
			share_report($(this).closest("tr"), true);
		});
	});
	$wrap.find(".ic-copy-share-link").off("click").on("click", function () {
		const url = $(this).data("url");
		if (url && navigator.clipboard) {
			navigator.clipboard.writeText(url);
			frappe.show_alert({ message: __("Share link copied"), indicator: "green" });
		}
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
		ic_esc(doc.company_legal_name || doc.product_name || doc.gstin || "—"),
	]);
	const dispatch_rows = (d.sample_dispatches || []).map((s) => [
		ic_doc_link("IC Sample Dispatch Collection", s.name),
		ic_status_pill(s.status),
		ic_esc(s.tracking_number || s.courier_name || "—"),
		ic_esc((s.submitted_on || s.modified || "").toString().slice(0, 16) || "—"),
	]);
	const contract_rows = (d.contracts || []).map((c) => [
		ic_doc_link("IC Contract", c.name, c.title || c.name),
		ic_status_pill(c.status),
		ic_esc(c.customer_signed_name || "—"),
		ic_esc((c.accepted_on || "").toString().slice(0, 16) || "—"),
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
				ic_table([__("Document Request"), __("Status"), __("Collected")], doc_rows),
				__("No document requests")
			)}
			${ic_related_section(
				__("Sample Dispatch Sheets"),
				ic_table([__("Sheet"), __("Status"), __("Tracking / Courier"), __("Submitted")], dispatch_rows),
				__("No sample dispatch collections")
			)}
			${ic_related_section(
				__("Contracts"),
				ic_table([__("Contract"), __("Status"), __("Signed by"), __("Accepted")], contract_rows),
				__("No contracts")
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

/** Shared multi-person assignee helpers (Quotation / Testing / Task). */
instacertify.add_me_as_assignee = function (frm, tableField) {
	const me = frappe.session.user;
	const rows = frm.doc[tableField] || [];
	if (rows.some((r) => r.user === me)) {
		frappe.show_alert({ message: __("You are already assigned"), indicator: "blue" });
		return;
	}
	frm.add_child(tableField, {
		user: me,
		full_name: (frappe.boot.user && frappe.boot.user.full_name) || me,
		role: rows.length ? "Member" : "Primary",
	});
	frm.refresh_field(tableField);
	frappe.show_alert({ message: __("Added — save to confirm"), indicator: "green" });
};

frappe.ui.form.on("IC Assignee", {
	user(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.user) return;
		frappe.db.get_value("User", row.user, "full_name", (r) => {
			if (r && r.full_name) frappe.model.set_value(cdt, cdn, "full_name", r.full_name);
		});
	},
	role(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.role !== "Primary") return;
		(frm.doc.ic_assignees || []).forEach((r) => {
			if (r.name !== cdn && r.role === "Primary") {
				frappe.model.set_value(r.doctype, r.name, "role", "Member");
			}
		});
	},
});

frappe.ui.form.on("Task", {
	refresh(frm) {
		if (frm.fields_dict.ic_assignees) {
			frm.add_custom_button(__("Assign Me"), () => {
				instacertify.add_me_as_assignee(frm, "ic_assignees");
			}, __("Actions"));
		}
	},
});

frappe.ui.form.on("IC Testing Request", {
	onload(frm) {
		instacertify.load_testing_request_library_options(frm);
	},
	refresh(frm) {
		frm.set_query("laboratory", () => ({ filters: { status: "Active" } }));
		instacertify.load_testing_request_library_options(frm);
		instacertify.bind_testing_request_library_pickers(frm);
		if (frm.doc.applicable_standard || frm.doc.test_name) {
			instacertify.load_testing_request_lab_offers(frm);
		}
		if (frm.fields_dict.ic_assignees) {
			frm.add_custom_button(__("Assign Me"), () => {
				instacertify.add_me_as_assignee(frm, "ic_assignees");
			}, __("Actions"));
		}
		if (frm.doc.laboratory) {
			instacertify.load_testing_request_scope_options(frm);
		}
		frm.add_custom_button(__("Compare Labs"), () => {
			if (!frm.doc.applicable_standard && !frm.doc.test_name) {
				frappe.msgprint(
					__("Select a Test name or Applicable Standard first (from the lab library dropdown).")
				);
				return;
			}
			instacertify.load_testing_request_lab_offers(frm, { open_picker: true });
		}, __("Actions"));
		if (!frm.is_new() && frm.doc.test_report) {
			frm.add_custom_button(__("Share with Customer"), () => {
				frappe.call({
					method: "instacertify.testing.events.share_report_with_customer",
					args: { testing_request: frm.doc.name },
					callback(r) {
						const m = r.message || {};
						frappe.msgprint({
							title: __("Report shared with customer"),
							indicator: "green",
							message: `
								<p>${__("Send both the link and the 8-digit code to the customer.")}</p>
								<p><b>${__("Share link")}</b><br>
									<a href="${frappe.utils.escape_html(m.url || "#")}" target="_blank" rel="noopener">${frappe.utils.escape_html(
								m.url || ""
							)}</a>
								</p>
								<p><b>${__("Access code")}</b>: <code style="font-size:1.2em;letter-spacing:0.12em">${frappe.utils.escape_html(
									m.access_code || ""
								)}</code></p>`,
						});
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
						amount: frm.doc.library_buying_price || frm.doc.suggested_selling_price,
					},
					freeze: true,
					callback(r) {
						frappe.set_route("Form", "Purchase Invoice", r.message.name);
					},
				});
			}, __("Billing"));
		}
	},
	test_name(frm) {
		if (frm._ic_skip_lab_picker) return;
		frm.set_value("lab_offer", "");
		instacertify.load_testing_request_lab_offers(frm, { open_picker: true });
	},
	applicable_standard(frm) {
		if (frm._ic_skip_lab_picker) return;
		frm.set_value("lab_offer", "");
		instacertify.load_testing_request_lab_offers(frm, { open_picker: true });
	},
	lab_offer(frm) {
		if (frm._ic_skip_lab_picker) return;
		instacertify.apply_testing_request_lab_offer(frm);
	},
	laboratory(frm) {
		frm.set_value("lab_test_scope", "");
		frm.set_value("lab_scope_row", "");
		frm.set_value("suggested_selling_price", 0);
		if (frm.fields_dict.library_buying_price) {
			frm.set_value("library_buying_price", 0);
		}
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
				if (frm.fields_dict.library_buying_price) {
					frm.set_value("library_buying_price", s.purchase_price);
				}
				if (s.label && frm.doc.lab_test_scope !== s.label) {
					frm.set_value("lab_test_scope", s.label);
				}
			},
		});
	},
});

instacertify.load_testing_request_library_options = function (frm) {
	frappe.call({
		method: "instacertify.laboratory.api.get_test_name_options",
		callback(r) {
			const values = (r.message || []).map((o) => o.value || o);
			frm.set_df_property("test_name", "options", values.join("\n"));
			const ctrl = frm.fields_dict.test_name;
			if (ctrl && ctrl.set_data) {
				ctrl.set_data(values);
			} else if (ctrl && ctrl.awesomplete) {
				ctrl.awesomplete.list = values;
			}
		},
	});
	frappe.call({
		method: "instacertify.laboratory.api.get_standard_options",
		callback(r) {
			const values = (r.message || []).map((o) => o.value || o);
			frm.set_df_property("applicable_standard", "options", values.join("\n"));
			const ctrl = frm.fields_dict.applicable_standard;
			if (ctrl && ctrl.set_data) {
				ctrl.set_data(values);
			} else if (ctrl && ctrl.awesomplete) {
				ctrl.awesomplete.list = values;
			}
		},
	});
};

instacertify.bind_testing_request_library_pickers = function (frm) {
	const bind = (fieldname) => {
		const ctrl = frm.fields_dict[fieldname];
		if (!ctrl || !ctrl.$input || ctrl._ic_lab_bound) return;
		ctrl._ic_lab_bound = true;
		ctrl.$input.on("awesomplete-selectcomplete.ic_lab", () => {
			if (frm._ic_skip_lab_picker) return;
			setTimeout(() => {
				frm.set_value("lab_offer", "");
				instacertify.load_testing_request_lab_offers(frm, { open_picker: true });
			}, 50);
		});
		ctrl.$input.on("change.ic_lab", () => {
			if (frm._ic_skip_lab_picker) return;
			if (!frm.doc[fieldname]) return;
			setTimeout(() => {
				instacertify.load_testing_request_lab_offers(frm, { open_picker: true });
			}, 80);
		});
	};
	bind("test_name");
	bind("applicable_standard");

	const offer = frm.fields_dict.lab_offer;
	if (offer && offer.$input && !offer._ic_lab_bound) {
		offer._ic_lab_bound = true;
		offer.$input.on("focus.ic_lab", () => {
			if (frm.doc.applicable_standard || frm.doc.test_name) {
				instacertify.load_testing_request_lab_offers(frm);
			}
		});
		offer.$wrapper.find(".control-label").css("cursor", "pointer");
		offer.$wrapper.on("click.ic_lab_compare", ".control-label, .help-box", () => {
			if (frm.doc.applicable_standard || frm.doc.test_name) {
				instacertify.load_testing_request_lab_offers(frm, { open_picker: true });
			} else {
				frappe.show_alert({
					message: __("Pick a Test or Applicable Standard first"),
					indicator: "orange",
				});
			}
		});
	}
};

instacertify.load_testing_request_lab_offers = function (frm, opts) {
	opts = opts || {};
	if (!frm.doc.applicable_standard && !frm.doc.test_name) {
		frm.set_df_property("lab_offer", "options", "");
		return;
	}
	frappe.call({
		method: "instacertify.laboratory.api.get_labs_for_standard",
		args: {
			applicable_standard: frm.doc.applicable_standard || "",
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
					message: __(
						"No Active labs list this test/standard yet. Check the Laboratory Library."
					),
					indicator: "orange",
				});
			}
		},
	});
};

instacertify.open_testing_request_lab_picker = function (frm, offers) {
	const rows_html = offers
		.map((o, idx) => {
			const buy = format_currency(o.purchase_price || 0, o.currency || "INR");
			const sell = format_currency(o.selling_price || 0, o.currency || "INR");
			return `<tr data-idx="${idx}" class="ic-lab-offer-row" style="cursor:pointer">
				<td><b>${frappe.utils.escape_html(o.laboratory_name || "")}</b></td>
				<td>${frappe.utils.escape_html(o.location || "—")}</td>
				<td>${frappe.utils.escape_html(o.test_name || "")}</td>
				<td>${frappe.utils.escape_html(o.applicable_standard || "—")}</td>
				<td style="text-align:right;font-weight:700;color:#EC6820">${frappe.utils.escape_html(buy)}</td>
				<td style="text-align:right">${frappe.utils.escape_html(sell)}</td>
			</tr>`;
		})
		.join("");
	const d = new frappe.ui.Dialog({
		title: __("Choose lab — compare buying rates"),
		size: "extra-large",
		fields: [
			{
				fieldtype: "HTML",
				options: `<div class="text-muted" style="margin-bottom:8px">
					${__("Labs in the library that offer this test / standard. Pick one using the buying rate:")}
				</div>
				<table class="table table-bordered table-hover" style="margin:0">
					<thead><tr>
						<th>${__("Laboratory")}</th><th>${__("Location")}</th>
						<th>${__("Test")}</th><th>${__("Standard")}</th>
						<th style="text-align:right">${__("Buying")}</th>
						<th style="text-align:right">${__("Selling")}</th>
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
		frm._ic_skip_lab_picker = true;
		const done = () => {
			frm._ic_skip_lab_picker = false;
		};
		Promise.resolve()
			.then(() => frm.set_value("laboratory", s.laboratory))
			.then(() => frm.set_value("lab_scope_row", s.scope_row))
			.then(() => (s.test_name ? frm.set_value("test_name", s.test_name) : null))
			.then(() =>
				s.applicable_standard ? frm.set_value("applicable_standard", s.applicable_standard) : null
			)
			.then(() => frm.set_value("suggested_selling_price", s.selling_price))
			.then(() =>
				frm.fields_dict.library_buying_price
					? frm.set_value("library_buying_price", s.purchase_price)
					: null
			)
			.then(() => (s.scope_label ? frm.set_value("lab_test_scope", s.scope_label) : null))
			.then(() => {
				instacertify.load_testing_request_scope_options(frm);
				frappe.show_alert({
					message: __(
						"Selected {0} — buying {1}",
						[
							s.laboratory_name || s.laboratory,
							format_currency(s.purchase_price || 0, s.currency || "INR"),
						]
					),
					indicator: "green",
				});
			})
			.finally(done);
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
			test_name: frm.doc.test_name,
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
					"Laboratory Library — enter Laboratory Name, Accreditation Scope, and upload Scope Sheet / Scope PDF / CSV / Excel. Add each accredited test with buying & selling prices — all columns are editable."
				),
				"blue"
			);
		} else {
			frm.set_intro(
				__(
					"Edit any field below anytime. Upload CSV/Excel from Library to fill scope rows, or edit the pricing table directly."
				),
				"blue"
			);
		}
		// Ensure master + attach fields stay editable (never locked after upload)
		[
			"laboratory_name",
			"status",
			"location",
			"city",
			"state",
			"country",
			"address",
			"contact_person",
			"email",
			"phone",
			"website",
			"accreditation_details",
			"accreditation_scope",
			"scope_sheet",
			"accreditation_certificate",
			"accreditation_scope_pdf",
			"remarks",
			"test_scopes",
			"supplier",
		].forEach((f) => {
			if (frm.fields_dict[f]) frm.set_df_property(f, "read_only", 0);
		});
		frm.add_custom_button(__("Upload Lab / Scope"), () => {
			const strip = (v) =>
				$("<div>")
					.html(v || "")
					.text()
					.trim();
			instacertify.open_laboratory_upload({
				laboratory_name: frm.doc.laboratory_name,
				location: frm.doc.location,
				city: frm.doc.city,
				address: frm.doc.address,
				status: frm.doc.status,
				accreditation_scope: strip(frm.doc.accreditation_scope),
				accreditation_details: strip(frm.doc.accreditation_details),
				contact_person: frm.doc.contact_person,
				email: frm.doc.email,
				phone: frm.doc.phone,
				website: frm.doc.website,
				on_done(name) {
					if (name === frm.doc.name) frm.reload_doc();
					else frappe.set_route("Form", "IC Laboratory", name);
				},
			});
		}, __("Library"));
		if (!frm.is_new()) {
			frm.add_custom_button(__("Import Scope CSV / Excel"), () => {
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
		frappe.model.set_value(
			cdt,
			cdn,
			"margin",
			(flt(row.selling_price) || 0) - (flt(row.purchase_price) || 0)
		);
	},
	selling_price(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		frappe.model.set_value(
			cdt,
			cdn,
			"margin",
			(flt(row.selling_price) || 0) - (flt(row.purchase_price) || 0)
		);
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
	// Prefer full-width desk so square tiles spread across the viewing screen
	instacertify.enable_full_width_desk();

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
			frm.add_custom_button(__("Lead Reminders"), () => {
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

// Quote Format + Laboratory libraries — list upload actions + category chips
frappe.listview_settings["IC Quotation Template"] = {
	add_fields: ["quotation_type", "service_family", "is_active", "uploaded_format", "template_notes"],
	filters: [["is_active", "=", 1]],
	get_indicator(doc) {
		const t = doc.quotation_type || "Other";
		const colors = {
			Consulting: "blue",
			Testing: "orange",
			Renewal: "green",
			Service: "cyan",
			Other: "gray",
			"Multiple Products / Multiple Services": "purple",
		};
		return [__(t), colors[t] || "blue", "quotation_type,=," + t];
	},
	formatters: {
		template_notes(value) {
			if (!value) return "";
			const m = String(value).match(/\[Tags:\s*([^\]]*)\]/i);
			if (!m) return "";
			return (m[1] || "")
				.split(",")
				.map((t) => t.trim())
				.filter(Boolean)
				.map((t) => `<span class="indicator-pill gray">${frappe.utils.escape_html(t)}</span>`)
				.join(" ");
		},
	},
	onload(listview) {
		listview.page.set_title(__("Quotation Templates — Edit formats & pricing"));
		listview.page.add_inner_button(__("Category Catalog"), () => {
			frappe.set_route("quote-format-library");
		});
		listview.page.add_inner_button(__("New Template"), () => {
			frappe.new_doc("IC Quotation Template", { is_active: 1, quotation_type: "Consulting" });
		});
		listview.page.add_inner_button(__("Upload Format File"), () => {
			instacertify.open_quote_format_upload();
		});
		listview.page.add_inner_button(__("Excel Template"), () => {
			frappe.call({
				method: "instacertify.setup.library_upload.download_quote_format_upload_template",
				args: { fmt: "xlsx" },
				callback(r) {
					const m = r.message || {};
					if (m.file_url) window.open(m.file_url, "_blank");
				},
			});
		});
		listview.page.add_inner_button(__("CSV Template"), () => {
			frappe.call({
				method: "instacertify.setup.library_upload.download_quote_format_upload_template",
				args: { fmt: "csv" },
				callback(r) {
					const m = r.message || {};
					if (m.file_url) window.open(m.file_url, "_blank");
				},
			});
		});
		listview.page.add_inner_button(__("Import Spreadsheet"), () => {
			const d = new frappe.ui.Dialog({
				title: __("Import Quote Formats (CSV / Excel)"),
				fields: [
					{
						fieldname: "file",
						fieldtype: "Attach",
						label: __("Spreadsheet File"),
						reqd: 1,
						description: __("Upload filled .csv or .xlsx template"),
						options: instacertify.attach_options,
					},
				],
				primary_action_label: __("Import"),
				primary_action(values) {
					frappe.call({
						method: "instacertify.setup.library_upload.import_quote_templates_from_spreadsheet",
						args: { file_url: values.file },
						freeze: true,
						callback(r) {
							d.hide();
							const m = r.message || {};
							frappe.show_alert({
								message:
									m.message ||
									__("{0} created, {1} updated", [m.created_count || 0, m.updated_count || 0]),
								indicator: "green",
							});
							listview.refresh();
						},
					});
				},
			});
			d.show();
		});

		const cats = ["", "Consulting", "Testing", "Renewal", "Other"];
		const $bar = $(`<div class="ic-quote-lib-list-cats"></div>`);
		const slugOf = {
			Consulting: "consulting",
			Testing: "testing",
			Renewal: "renewal",
			Other: "other",
		};
		cats.forEach((c) => {
			const label = c || __("All");
			const slug = c ? slugOf[c] || "other" : "all";
			const $btn = $(
				`<button type="button" class="btn btn-xs ic-list-cat-btn cat-${slug}">${frappe.utils.escape_html(
					label
				)}</button>`
			);
			$btn.on("click", () => {
				if (!c) {
					listview.filter_area.clear();
					listview.filter_area.add([[listview.doctype, "is_active", "=", 1]]);
				} else {
					listview.filter_area.clear();
					listview.filter_area.add([
						[listview.doctype, "quotation_type", "=", c],
						[listview.doctype, "is_active", "=", 1],
					]);
				}
				listview.refresh();
			});
			$bar.append($btn);
		});
		listview.$result.parent().find(".ic-quote-lib-list-cats").remove();
		listview.$result.before($bar);
	},
};

frappe.listview_settings["IC Laboratory"] = {
	onload(listview) {
		listview.page.add_inner_button(__("Upload Lab / Scope"), () => {
			instacertify.open_laboratory_upload();
		});
		listview.page.add_inner_button(__("Excel Template"), () => {
			frappe.call({
				method: "instacertify.setup.library_upload.download_lab_scope_template",
				args: { fmt: "xlsx" },
				callback(r) {
					const m = r.message || {};
					if (m.file_url) window.open(m.file_url, "_blank");
				},
			});
		}, __("Templates"));
		listview.page.add_inner_button(__("CSV Template"), () => {
			frappe.call({
				method: "instacertify.setup.library_upload.download_lab_scope_template",
				args: { fmt: "csv" },
				callback(r) {
					const m = r.message || {};
					if (m.file_url) window.open(m.file_url, "_blank");
				},
			});
		}, __("Templates"));
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
			"Report Available": "yellow",
			"Report Uploaded": "green",
			"Report Shared with Customer": "blue",
		};
		const label = doc.status === "Report Available" || doc.status === "Report Uploaded" || doc.status === "Report Shared with Customer"
			? doc.status
			: (doc.sample_location || doc.status || "");
		return [__(label || "Unset"), colors[label] || colors[loc] || "gray", "status,=," + (doc.status || "")];
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

instacertify.render_sample_sticker_preview = function (frm, fileUrl) {
	if (!frm.fields_dict.sticker_preview) return;
	const trk = frm.doc.tracking_number || frm.doc.name || "";
	const qr = frm.doc.qr_code || "";
	const stickerImg = fileUrl
		? `<img src="${frappe.utils.escape_html(fileUrl)}" alt="8mm sticker" style="height:48px;image-rendering:pixelated;border:1px solid #ddd;background:#fff;"/>`
		: "";
	const qrImg = qr
		? `<img src="${frappe.utils.escape_html(qr)}" alt="QR" style="height:64px;width:64px;image-rendering:pixelated;border:1px solid #ddd;"/>`
		: "";
	frm.fields_dict.sticker_preview.$wrapper.html(`
		<div class="ic-sample-sticker-preview" style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;padding:8px 0;">
			<div style="display:flex;align-items:center;gap:8px;padding:4px 8px;border:1px dashed #90a4ae;border-radius:4px;background:#fff;">
				${qrImg}
				<div style="font-family:ui-monospace,monospace;font-weight:700;font-size:13px;line-height:1.1;">
					<div style="font-size:10px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:#607d8b;">Sample</div>
					${frappe.utils.escape_html(trk)}
				</div>
			</div>
			${stickerImg}
			<div class="text-muted" style="font-size:12px;max-width:280px;">
				${__("8mm thermal sticker layout: QR + unique sample tracking number, side-by-side. Use Label → Print 8mm Sticker or Download 8mm PNG.")}
			</div>
		</div>
	`);
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
		if (frm.doc.status === "Report Available" && !frm.doc.test_report && !frm.is_new()) {
			frappe.show_alert({
				message: __("Upload the test report PDF from the Report section"),
				indicator: "orange",
			});
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
		if (!frm.is_new()) {
			instacertify.render_sample_sticker_preview(frm);
			frm.add_custom_button(__("Print 8mm Sticker"), () => {
				frm.print_doc("Instacertify Sample Sticker 8mm");
			}, __("Label"));
			frm.add_custom_button(__("Download 8mm PNG"), () => {
				frappe.call({
					method: "instacertify.testing.events.download_sample_sticker_8mm",
					args: { sample: frm.doc.name },
					freeze: true,
					freeze_message: __("Rendering 8mm sticker…"),
					callback(r) {
						const m = r.message || {};
						if (m.file_url) {
							window.open(m.file_url, "_blank");
							frappe.show_alert({
								message: __("Sticker ready: {0}", [m.tracking_number || ""]),
								indicator: "green",
							});
							instacertify.render_sample_sticker_preview(frm, m.file_url);
						}
					},
				});
			}, __("Label"));
			frm.add_custom_button(__("Regenerate QR"), () => {
				frappe.call({
					method: "instacertify.testing.events.regenerate_sample_qr",
					args: { sample: frm.doc.name },
					freeze: true,
					callback() {
						frm.reload_doc();
						frappe.show_alert({
							message: __("QR updated with sample tracking number"),
							indicator: "green",
						});
					},
				});
			}, __("Label"));
		}
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

		if (frm.is_new()) return;

		// Mark Report Available when testing is done
		if (
			["Testing in Progress", "At Laboratory", "Sample Dispatched to Laboratory"].includes(
				frm.doc.status
			)
		) {
			frm.add_custom_button(__("Mark Report Available"), () => {
				frappe.call({
					method: "instacertify.testing.events.mark_sample_report_available",
					args: { sample: frm.doc.name },
					freeze: true,
					callback() {
						frm.reload_doc().then(() => {
							frappe.show_alert({
								message: __("Status set to Report Available — upload the PDF report"),
								indicator: "blue",
							});
							instacertify.open_sample_report_upload(frm);
						});
					},
				});
			}, __("Report"));
		}

		// Upload / replace / delete PDF once Report Available
		if (
			["Report Available", "Report Uploaded", "Report Shared with Customer"].includes(
				frm.doc.status
			)
		) {
			frm.set_intro(
				frm.doc.test_report
					? __(
							"Test report PDF is on file. Use Report → Replace or Delete to modify it. Visible in Customer records."
					  )
					: __(
							"Status is Report Available — upload the lab test report as a PDF (Report → Upload Test Report PDF)."
					  ),
				frm.doc.test_report ? "green" : "orange"
			);

			frm.add_custom_button(
				frm.doc.test_report ? __("Replace Test Report PDF") : __("Upload Test Report PDF"),
				() => instacertify.open_sample_report_upload(frm),
				__("Report")
			);

			if (frm.doc.test_report) {
				frm.add_custom_button(__("View Report PDF"), () => {
					window.open(frm.doc.test_report, "_blank");
				}, __("Report"));
				frm.add_custom_button(__("Delete Test Report"), () => {
					frappe.confirm(
						__("Delete the uploaded PDF report? You can upload a new one after."),
						() => {
							frappe.call({
								method: "instacertify.testing.events.delete_sample_report",
								args: { sample: frm.doc.name },
								freeze: true,
								callback() {
									frm.reload_doc();
									frappe.show_alert({
										message: __("Report deleted — status back to Report Available"),
										indicator: "orange",
									});
								},
							});
						}
					);
				}, __("Report"));
			}

			// Auto-prompt upload when landing on Report Available with no file
			if (frm.doc.status === "Report Available" && !frm.doc.test_report && !frm._ic_report_prompted) {
				frm._ic_report_prompted = true;
				setTimeout(() => instacertify.open_sample_report_upload(frm), 400);
			}
		}

		instacertify.render_sample_report_actions(frm);

		if (frm.doc.test_report) {
			frm.dashboard.add_comment(
				__(
					"Test report PDF on file{0}. Visible in Customer → Data Drive / Project Records.",
					[
						frm.doc.report_uploaded_on
							? ` (${frm.doc.report_uploaded_on})`
							: "",
					]
				),
				"blue",
				true
			);
		}
	},
	test_report(frm) {
		// Direct attach on the form also stamps + ingests via DocType validate/on_update
		if (!frm.doc.test_report || frm.is_new()) return;
		const name = String(frm.doc.test_report).split("?")[0].toLowerCase();
		if (!name.endsWith(".pdf")) {
			frappe.msgprint(__("Please upload a PDF file for the test report."));
			frm.set_value("test_report", "");
			return;
		}
		if (frm.doc.status === "Report Available") {
			frappe.show_alert({
				message: __("Save to stamp date/time and push report to customer records"),
				indicator: "blue",
			});
		}
	},
});

instacertify.pdf_attach_options = Object.assign({}, instacertify.attach_options || {}, {
	restrictions: {
		allowed_file_types: [".pdf", "application/pdf"],
	},
});

instacertify.open_sample_report_upload = function (frm) {
	const d = new frappe.ui.Dialog({
		title: frm.doc.test_report
			? __("Replace Test Report PDF")
			: __("Upload Test Report PDF"),
		fields: [
			{
				fieldname: "help",
				fieldtype: "HTML",
				options: `<p class="text-muted">${__(
					"Attach the lab test report as a <b>PDF</b> only. It will be saved to Customer records with date & time. You can replace or delete it later."
				)}</p>`,
			},
			{
				fieldname: "test_report",
				fieldtype: "Attach",
				label: __("Test Report PDF"),
				reqd: 1,
				description: __("PDF only — My Device or File Library."),
				options: instacertify.pdf_attach_options,
			},
		],
		primary_action_label: frm.doc.test_report ? __("Replace") : __("Upload"),
		primary_action(values) {
			const file_url =
				(d.get_value && d.get_value("test_report")) ||
				(values && values.test_report) ||
				"";
			if (!file_url) {
				frappe.msgprint(__("Please attach a PDF file first."));
				return;
			}
			if (!String(file_url).split("?")[0].toLowerCase().endsWith(".pdf")) {
				frappe.msgprint(__("Test report must be a PDF file (.pdf)."));
				return;
			}
			frappe.call({
				method: "instacertify.testing.events.upload_sample_report",
				args: { sample: frm.doc.name, file_url },
				freeze: true,
				freeze_message: __("Saving PDF report to customer records…"),
				callback(r) {
					d.hide();
					const m = r.message || {};
					frappe.msgprint({
						title: __("Report uploaded"),
						indicator: "green",
						message: __(
							"PDF report saved on {0}. Available in Customer records. Use Report → Replace or Delete to modify.",
							[m.report_uploaded_on || __("now")]
						),
					});
					frm.reload_doc();
				},
			});
		},
	});
	d.show();
	if (instacertify.add_file_manager_hint) {
		instacertify.add_file_manager_hint(d, "test_report");
	}
};

instacertify.render_sample_report_actions = function (frm) {
	if (!frm.fields_dict.report_actions_html) return;
	const url = frm.doc.test_report;
	const status = frm.doc.status;
	if (
		!["Report Available", "Report Uploaded", "Report Shared with Customer"].includes(status) &&
		!url
	) {
		frm.fields_dict.report_actions_html.$wrapper.empty();
		return;
	}
	const buttons = [];
	if (!url) {
		buttons.push(
			`<button type="button" class="btn btn-primary btn-sm ic-upload-report-pdf">${__(
				"Upload Test Report PDF"
			)}</button>`
		);
	} else {
		buttons.push(
			`<a class="btn btn-default btn-sm" href="${frappe.utils.escape_html(
				url
			)}" target="_blank" rel="noopener">${__("Open PDF")}</a>`
		);
		buttons.push(
			`<button type="button" class="btn btn-default btn-sm ic-replace-report-pdf">${__(
				"Replace PDF"
			)}</button>`
		);
		buttons.push(
			`<button type="button" class="btn btn-danger btn-sm ic-delete-report-pdf">${__(
				"Delete PDF"
			)}</button>`
		);
	}
	const meta = url
		? `<div class="text-muted" style="margin-top:6px;font-size:12px;">${__(
				"Uploaded on {0} by {1}",
				[
					frappe.datetime.str_to_user(frm.doc.report_uploaded_on) || "—",
					frm.doc.report_uploaded_by || "—",
				]
		  )}</div>`
		: `<div class="text-muted" style="margin-top:6px;font-size:12px;">${__(
				"No report yet — PDF required"
		  )}</div>`;
	frm.fields_dict.report_actions_html.$wrapper.html(
		`<div class="ic-report-actions" style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">${buttons.join(
			""
		)}</div>${meta}`
	);
	frm.fields_dict.report_actions_html.$wrapper
		.find(".ic-upload-report-pdf, .ic-replace-report-pdf")
		.on("click", () => instacertify.open_sample_report_upload(frm));
	frm.fields_dict.report_actions_html.$wrapper.find(".ic-delete-report-pdf").on("click", () => {
		frappe.confirm(__("Delete the uploaded PDF report?"), () => {
			frappe.call({
				method: "instacertify.testing.events.delete_sample_report",
				args: { sample: frm.doc.name },
				freeze: true,
				callback() {
					frm.reload_doc();
				},
			});
		});
	});
};

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
