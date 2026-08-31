/*! Instacertify Desk JS */
frappe.provide("instacertify");

instacertify.brand = {
	primary: "#0D47A1",
	accent: "#EC691F",
	surface: "#E7F1FC",
	white: "#FFFFFF",
	logo: "/assets/instacertify/images/instacertify_logo.png",
	// Circular favicon mark — home icon logo, navbar, small UI
	icon: "/assets/instacertify/images/favicon-48.png",
	app_logo: "/assets/instacertify/images/favicon-48.png",
	favicon: "/assets/instacertify/images/favicon-32.png",
};

/**
 * Desk-wide contrast guard: dark fills get white labels; soft fills get dark ink.
 * Uniform highlight brightness. Runs early so buttons stay readable without hover.
 */
instacertify.ensure_contrast_guard = function () {
	const ID = "ic-contrast-guard-style";
	let s = document.getElementById(ID);
	if (!s) {
		s = document.createElement("style");
		s.id = ID;
		(document.head || document.documentElement).appendChild(s);
	}
	s.textContent = `
:root {
  --btn-primary-color: #ffffff !important;
  --text-on-primary: #ffffff;
  --icon-stroke: #0B1820 !important;
  --text-muted: #3A5563 !important;
  --ic-line-ink: #0B1820;
  --ic-hl-bg: rgba(6, 81, 117, 0.08);
  --ic-hl-bg-strong: rgba(6, 81, 117, 0.12);
  --ic-hl-edge: rgba(236, 105, 31, 0.55);
}
.btn-primary, .btn.btn-primary, a.btn-primary, button.btn-primary,
.btn-primary:hover, .btn-primary:focus, .btn-primary:active, .btn-primary:disabled,
.btn-warning, .btn-orange, .btn-accent, .btn.btn-accent, .btn-danger, .btn-success, .btn-info,
.ic-btn-primary, .ic-btn-accent, .ic-ts-btn-qr,
.ic-ts-tab-gen.is-active, .ic-ts-tab-manage.is-active, .ic-ts-step.is-current,
.ic-quote-lib-tag.active, .ic-doclib-cat.is-active, .primary-action,
.for-login .btn-primary, .for-login .btn-login, .for-login button[type="submit"],
.login-content .btn-primary, .login-content .btn-login, .page-card .btn-primary {
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
}
.for-login .btn-primary, .for-login .btn-login, .for-login button[type="submit"],
.login-content .btn-primary, .page-card .btn-primary {
  background: #065175 !important;
  border-color: #065175 !important;
}
.for-login label, .for-login .form-control, .login-content label, .login-content .form-control {
  color: #0B1820 !important;
  -webkit-text-fill-color: #0B1820 !important;
}
.btn-default, .btn-secondary, .btn-light, .ic-btn-ghost, .ic-list-cat-btn, .filter-button,
.btn-modal-close, .btn-modal-minimize, .btn[data-label="Cut"], .btn[aria-label="Cut"],
.btn[title="Cut"], .btn[data-label="Cancel"], .page-icon-group .icon-btn,
.page-head .inner-group-button > .btn-default,
.custom-actions .btn-default, .actions-btn-group .btn-default {
  color: #033447 !important;
  -webkit-text-fill-color: #033447 !important;
}
/* Dark line icons on light chrome.
   Lucide (.icon) = stroke; Espresso (.es-icon) = fill (Reload List uses es-line-reload). */
svg.icon:not(.es-icon),
.icon:not(.es-icon) use,
.page-icon-group .icon-btn svg.icon:not(.es-icon),
.page-icon-group button svg.icon:not(.es-icon),
.page-actions .btn-default svg.icon:not(.es-icon),
.standard-actions .btn-default svg.icon:not(.es-icon),
.menu-btn-group .dropdown-item svg.icon:not(.es-icon),
.menu-item-icon svg.icon:not(.es-icon), .ic-action-icon svg.icon:not(.es-icon),
.form-sidebar svg.icon:not(.es-icon),
.btn-modal-close svg.icon:not(.es-icon), .btn-modal-minimize svg.icon:not(.es-icon),
.modal-header .btn:not(.btn-primary) svg.icon:not(.es-icon), .section-head .icon:not(.es-icon),
.row-actions svg.icon:not(.es-icon), .btn-open-row svg.icon:not(.es-icon),
.ql-toolbar button svg, .ql-toolbar .ql-stroke,
.link-btn svg, .btn-search svg, .control-input .link-btn svg {
  stroke: #0B1820 !important;
  color: #0B1820 !important;
  --icon-stroke: #0B1820 !important;
  opacity: 1 !important;
  visibility: visible !important;
}
svg.es-icon,
.es-icon use,
.page-icon-group .icon-btn svg.es-icon,
.page-icon-group button svg.es-icon,
.page-actions .btn-default svg.es-icon,
.standard-actions .btn-default svg.es-icon,
.menu-item-icon svg.es-icon, .ic-action-icon svg.es-icon,
.btn-modal-close svg.es-icon, .btn-modal-minimize svg.es-icon {
  fill: #0B1820 !important;
  stroke: none !important;
  stroke-width: 0 !important;
  color: #0B1820 !important;
  --icon-stroke: #0B1820 !important;
  opacity: 1 !important;
  visibility: visible !important;
}
.page-icon-group .icon-btn,
.page-icon-group .icon-btn.text-muted,
.page-icon-group button.text-muted {
  color: #0B1820 !important;
  -webkit-text-fill-color: #0B1820 !important;
  opacity: 1 !important;
}
.page-icon-group .icon-btn svg.icon:not(.es-icon),
.page-icon-group button svg.icon:not(.es-icon),
.ic-action-icon svg.icon:not(.es-icon),
.btn-modal-close svg.icon:not(.es-icon),
.btn[data-label="Cut"] svg.icon:not(.es-icon),
.btn[title="Cut"] svg.icon:not(.es-icon) {
  stroke-width: 2 !important;
  fill: none !important;
}
.ql-toolbar .ql-stroke { stroke: #0B1820 !important; stroke-width: 1.7 !important; }
.ql-toolbar .ql-fill { fill: #0B1820 !important; }
.ql-toolbar button, .ql-toolbar .ql-picker {
  color: #0B1820 !important;
  opacity: 1 !important;
}
/* Filled buttons: white glyphs last so they win over dark line-icon rules */
.btn-primary, a.btn-primary, .btn-warning, .btn-accent, .btn-danger,
.btn-success, .ic-btn-primary, .primary-action,
.for-login .btn-primary, .for-login .btn-login, .for-login button[type="submit"],
.login-content .btn-primary {
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
}
.btn-primary .ic-action-label, .btn-primary .hidden-xs, .btn-primary span:not(.ic-action-icon),
.primary-action span:not(.ic-action-icon),
.ic-ts-tab-gen.is-active .ic-ts-tab-label, .ic-ts-tab-manage.is-active .ic-ts-tab-label,
.ic-ts-tab-gen.is-active .ic-ts-tab-hint, .ic-ts-tab-manage.is-active .ic-ts-tab-hint,
.ic-quote-lib-tag.active, .ic-doclib-cat.is-active {
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
}
.btn-primary svg.icon:not(.es-icon), .btn-primary .icon:not(.es-icon),
.btn-primary .ic-action-icon svg.icon:not(.es-icon),
.btn-warning svg.icon:not(.es-icon), .btn-accent svg.icon:not(.es-icon),
.btn-danger svg.icon:not(.es-icon), .btn-success svg.icon:not(.es-icon),
.ic-btn-primary svg.icon:not(.es-icon), .primary-action svg.icon:not(.es-icon) {
  color: #ffffff !important;
  stroke: #ffffff !important;
  --icon-stroke: #ffffff !important;
  fill: none !important;
  opacity: 1 !important;
}
.btn-primary svg.es-icon, .btn-primary .es-icon use,
.btn-primary .ic-action-icon svg.es-icon,
.btn-warning svg.es-icon, .btn-accent svg.es-icon,
.btn-danger svg.es-icon, .btn-success svg.es-icon,
.ic-btn-primary svg.es-icon, .primary-action svg.es-icon {
  color: #ffffff !important;
  fill: #ffffff !important;
  stroke: none !important;
  --icon-stroke: #ffffff !important;
  opacity: 1 !important;
}
.ic-list-cat-btn.btn-primary {
  background: #e4f1f8 !important;
  border-color: #065175 !important;
  color: #033447 !important;
  -webkit-text-fill-color: #033447 !important;
  box-shadow: none !important;
}
.ic-list-cat-btn.btn-primary *,
.ic-list-cat-btn.btn-primary svg.icon:not(.es-icon) {
  color: #033447 !important;
  -webkit-text-fill-color: #033447 !important;
  stroke: #033447 !important;
  --icon-stroke: #033447 !important;
  fill: none !important;
}
.ic-list-cat-btn.btn-primary svg.es-icon {
  color: #033447 !important;
  fill: #033447 !important;
  stroke: none !important;
  --icon-stroke: #033447 !important;
}
.ic-ts-tab.is-active .ic-ts-tab-label, .ic-ts-tab.is-active .ic-ts-tab-hint {
  color: #ffffff !important;
}
.ic-explore-count, .ic-lead-prompt-when, .ic-lead-hub-counts,
.ic-lead-hub-chip.overdue, .ic-lead-hub-chip.upcoming, .ic-lead-hub-chip.today {
  color: #ffffff !important;
}
::selection, ::-moz-selection {
  background: rgba(6, 81, 117, 0.12) !important;
  color: #0B1820 !important;
}
mark, .highlight, .search-highlight, .frappe-list .highlight, .ql-editor mark, span.highlight, .awesomplete mark {
  background: rgba(6, 81, 117, 0.08) !important;
  color: #0B1820 !important;
  box-shadow: none !important;
  border-radius: 2px;
}
.list-row:hover, .list-row.list-row-highlight,
.grid-row:hover .data-row, .grid-row > .data-row.highlight,
.awesomplete > ul > li[aria-selected="true"], .awesomplete > ul > li:hover,
.dropdown-item.active, .dropdown-item:hover,
.ic-ts-table tbody tr:hover, .ic-ts-tr-row.is-open, .ic-ts-table tbody tr.is-selected {
  background: rgba(6, 81, 117, 0.08) !important;
  color: #0B1820 !important;
  box-shadow: inset 3px 0 0 rgba(236, 105, 31, 0.55);
}
.desk-sidebar .standard-sidebar-item.selected,
.workspace-sidebar .item-anchor.active {
  background: rgba(6, 81, 117, 0.12) !important;
  color: #033447 !important;
}
.indicator-pill.blue, .indicator.blue, .indicator-pill.green {
  background: #e4f1f8 !important;
  color: #033447 !important;
}
.indicator-pill.orange, .indicator.orange, .indicator-pill.yellow {
  background: #fff1e6 !important;
  color: #c44710 !important;
}
.modal .btn-primary, .page-actions .btn-primary, .standard-actions .btn-primary {
  background: #065175 !important;
  border-color: #065175 !important;
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
}
`;
};

try {
	instacertify.ensure_contrast_guard();
} catch (e) {
	/* ignore */
}
$(document).on("page-change", function () {
	try {
		instacertify.ensure_contrast_guard();
	} catch (e) {
		/* ignore */
	}
});

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

/**
 * Case-handler Edit Price dialog — buying, selling, currency.
 * Available from Testing Request, Manage TR, Sample, TRF, etc.
 */
instacertify.edit_testing_request_prices = function (testing_request, opts) {
	opts = opts || {};
	if (!testing_request) {
		frappe.msgprint({
			title: __("Edit Price"),
			message: __("No Testing Request selected."),
			indicator: "orange",
		});
		return;
	}

	const open_dialog = (defaults) => {
		const d = new frappe.ui.Dialog({
			title: __("Edit Price — {0}", [testing_request]),
			fields: [
				{
					fieldname: "library_buying_price",
					fieldtype: "Currency",
					label: __("Buying Price"),
					default: flt(defaults.library_buying_price) || 0,
					reqd: 1,
					description: __("What we buy the lab service for (Purchase Invoice)"),
				},
				{
					fieldname: "suggested_selling_price",
					fieldtype: "Currency",
					label: __("Selling Price"),
					default: flt(defaults.suggested_selling_price) || 0,
					reqd: 1,
					description: __("What we sell / bill the customer"),
				},
				{
					fieldname: "price_currency",
					fieldtype: "Link",
					options: "Currency",
					label: __("Currency"),
					default: defaults.price_currency || "INR",
					reqd: 1,
				},
			],
			primary_action_label: __("Save Prices"),
			primary_action(values) {
				frappe.call({
					method: "instacertify.testing.events.update_testing_request_prices",
					args: {
						testing_request,
						library_buying_price: values.library_buying_price,
						suggested_selling_price: values.suggested_selling_price,
						price_currency: values.price_currency,
					},
					freeze: true,
					callback(r) {
						d.hide();
						frappe.show_alert({
							message: __("Prices updated ({0})", [values.price_currency || "INR"]),
							indicator: "green",
						});
						if (typeof opts.on_save === "function") {
							opts.on_save(r.message || values);
						}
					},
				});
			},
		});
		d.show();
	};

	if (
		opts.library_buying_price != null ||
		opts.suggested_selling_price != null ||
		opts.price_currency
	) {
		open_dialog(opts);
		return;
	}

	frappe.db
		.get_value("IC Testing Request", testing_request, [
			"library_buying_price",
			"suggested_selling_price",
			"price_currency",
		])
		.then((r) => open_dialog((r && r.message) || {}));
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
				fieldname: "contact_designation",
				fieldtype: "Data",
				label: __("Designation"),
				description: __("e.g. Quality Manager, Lab In-charge"),
				default: opts.contact_designation || "",
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

/** Inline bar above Scope of Accreditation table — bulk Excel/CSV upload. */
instacertify.render_lab_scope_bulk_bar = function (frm) {
	if (!frm || !frm.fields_dict || !frm.fields_dict.test_scopes) return;
	const $wrap = frm.fields_dict.test_scopes.$wrapper;
	$wrap.find(".ic-lab-bulk-bar").remove();
	const $bar = $(`
		<div class="ic-lab-bulk-bar" style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 10px;padding:10px 12px;border:1.5px solid #8eafc0;border-radius:10px;background:#f5fafc;">
			<div style="flex:1;min-width:200px">
				<div style="font-weight:650;color:#065175;font-size:13px">${__("Bulk upload scope")}</div>
				<div class="text-muted" style="font-size:12px;line-height:1.35">${__(
					"Add many tests at once from an Excel sheet or CSV file (prices included)."
				)}</div>
			</div>
			<button type="button" class="btn btn-sm btn-default ic-lab-dl-xlsx">${__("Excel Template")}</button>
			<button type="button" class="btn btn-sm btn-default ic-lab-dl-csv">${__("CSV Template")}</button>
			<button type="button" class="btn btn-sm btn-primary ic-lab-bulk-upload">${__("Upload Excel / CSV")}</button>
		</div>
	`);
	$wrap.prepend($bar);
	$bar.find(".ic-lab-bulk-upload").on("click", () => {
		if (frm.is_new()) {
			frappe.msgprint(__("Save the Laboratory first, then bulk-upload scope rows."));
			return;
		}
		instacertify.open_lab_scope_bulk_upload({
			laboratory: frm.doc.name,
			laboratory_name: frm.doc.laboratory_name,
			on_done() {
				frm.reload_doc();
			},
		});
	});
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
	$bar.find(".ic-lab-dl-xlsx").on("click", () => dl("xlsx"));
	$bar.find(".ic-lab-dl-csv").on("click", () => dl("csv"));
};

instacertify.open_lab_scope_csv_import = function (frm) {
	instacertify.open_lab_scope_bulk_upload({
		laboratory: frm && frm.doc ? frm.doc.name : "",
		laboratory_name: frm && frm.doc ? frm.doc.laboratory_name : "",
		on_done() {
			if (frm && frm.reload_doc) frm.reload_doc();
		},
	});
};

/** Bulk upload lab scope rows from Excel/CSV — one lab or multi-lab via laboratory_name column. */
instacertify.open_lab_scope_bulk_upload = function (opts) {
	opts = opts || {};
	const fixed_lab = (opts.laboratory || "").trim();
	const d = new frappe.ui.Dialog({
		title: __("Bulk Upload Lab Scope (Excel / CSV)"),
		fields: [
			{
				fieldname: "help",
				fieldtype: "HTML",
				options: `<div class="ic-lab-bulk-help" style="margin-bottom:8px">
					<p style="margin:0 0 6px">${__(
						"Upload many accredited tests at once. Download the Excel or CSV template, fill rows, then import."
					)}</p>
					<p class="text-muted" style="margin:0;font-size:12px">${__(
						"Columns: laboratory_name (optional if one lab selected), test_name, applicable_standard, category, selling_price, purchase_price, currency, is_active. Matching test + standard updates the row."
					)}</p>
				</div>`,
			},
			{
				fieldname: "laboratory",
				fieldtype: "Link",
				label: __("Laboratory (optional)"),
				options: "IC Laboratory",
				default: fixed_lab || "",
				description: fixed_lab
					? __("All rows will import into this laboratory.")
					: __(
							"Leave empty to split rows by laboratory_name column (multi-lab bulk). Or pick one lab to force all rows into it."
					  ),
				read_only: fixed_lab ? 1 : 0,
			},
			{
				fieldname: "create_missing_labs",
				fieldtype: "Check",
				label: __("Create missing laboratories from laboratory_name"),
				default: 0,
				depends_on: `eval:!doc.laboratory`,
			},
			{
				fieldname: "file",
				fieldtype: "Attach",
				label: __("Excel or CSV File"),
				reqd: 1,
				description: __("Select from My Device or File Library (.xlsx / .xls / .csv)."),
				options: instacertify.attach_options,
			},
		],
		primary_action_label: __("Import Scope Rows"),
		primary_action(values) {
			const file_url =
				(d.get_value && d.get_value("file")) || (values && values.file) || "";
			if (!file_url) {
				frappe.msgprint(__("Please attach an Excel or CSV file first."));
				return;
			}
			const laboratory =
				fixed_lab ||
				(d.get_value && d.get_value("laboratory")) ||
				(values && values.laboratory) ||
				"";
			frappe.call({
				method: "instacertify.setup.library_upload.import_lab_scopes_bulk",
				args: {
					file_url,
					laboratory: laboratory || "",
					create_missing_labs: cint(
						(d.get_value && d.get_value("create_missing_labs")) ||
							(values && values.create_missing_labs) ||
							0
					),
				},
				freeze: true,
				freeze_message: __("Importing lab scope rows…"),
				callback(r) {
					d.hide();
					const m = r.message || {};
					let msg = __("Scopes: +{0} added, {1} updated", [
						m.added || 0,
						m.updated || 0,
					]);
					if (m.mode === "multi") {
						msg += " — " + __("{0} laboratories", [m.labs || 0]);
					}
					frappe.show_alert({ message: msg, indicator: "green" });
					if (opts.on_done) opts.on_done(m);
					else if (m.laboratory) {
						frappe.set_route("Form", "IC Laboratory", m.laboratory);
					} else if (m.results && m.results[0]) {
						frappe.set_route("Form", "IC Laboratory", m.results[0].laboratory);
					}
				},
			});
		},
	});
	d.$wrapper.find(".modal-footer").prepend(
		`<span style="margin-right:auto;display:flex;gap:6px;flex-wrap:wrap;">
			<button type="button" class="btn btn-default btn-sm ic-dl-scope-xlsx">${__("Download Excel Template")}</button>
			<button type="button" class="btn btn-default btn-sm ic-dl-scope-csv">${__("Download CSV Template")}</button>
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

// Ensure favicon + site identity is always the circular Instacertify mark
(function setInstacertifyFavicon() {
	const favicon = (instacertify.brand && instacertify.brand.favicon) ||
		"/assets/instacertify/images/favicon-32.png";
	const icon48 = (instacertify.brand && instacertify.brand.icon) ||
		"/assets/instacertify/images/favicon-48.png";
	const apple = "/assets/instacertify/images/apple-touch-icon.png";
	const ico = "/assets/instacertify/images/favicon.ico";

	function upsertLink(rel, href, attrs) {
		attrs = attrs || {};
		let link = document.querySelector(`link[rel='${rel}']${attrs.sizes ? `[sizes='${attrs.sizes}']` : ""}`);
		if (!link) {
			// also match shortcut icon / generic icon
			link = Array.from(document.querySelectorAll("link[rel]")).find((el) => {
				const r = (el.getAttribute("rel") || "").toLowerCase();
				return r === rel || r.split(/\s+/).includes(rel);
			});
		}
		if (!link) {
			link = document.createElement("link");
			link.rel = rel;
			document.head.appendChild(link);
		}
		link.href = href;
		if (attrs.type) link.type = attrs.type;
		if (attrs.sizes) link.setAttribute("sizes", attrs.sizes);
	}

	upsertLink("icon", favicon, { type: "image/png", sizes: "32x32" });
	upsertLink("shortcut icon", favicon, { type: "image/png" });
	upsertLink("apple-touch-icon", apple, { sizes: "180x180" });

	// Extra ico for older browsers
	let icoLink = document.querySelector("link[rel='icon'][sizes='any']");
	if (!icoLink) {
		icoLink = document.createElement("link");
		icoLink.rel = "icon";
		icoLink.setAttribute("sizes", "any");
		document.head.appendChild(icoLink);
	}
	icoLink.href = ico;

	// App name meta
	function upsertMeta(name, content, prop) {
		const sel = prop ? `meta[property='${prop}']` : `meta[name='${name}']`;
		let m = document.querySelector(sel);
		if (!m) {
			m = document.createElement("meta");
			if (prop) m.setAttribute("property", prop);
			else m.setAttribute("name", name);
			document.head.appendChild(m);
		}
		m.setAttribute("content", content);
	}
	upsertMeta("application-name", "Instacertify");
	upsertMeta("apple-mobile-web-app-title", "Instacertify");
	upsertMeta(null, "Instacertify", "og:site_name");
	upsertMeta(null, icon48, "og:image");

	if (document.title === "Frappe" || document.title === "ERPNext" || !document.title) {
		document.title = "Instacertify";
	}
})();

/** Home greeting + navbar: use circular favicon as icon logo. */
instacertify.apply_favicon_brand_icons = function (root) {
	const iconSrc = (instacertify.brand && (instacertify.brand.icon || instacertify.brand.favicon)) ||
		"/assets/instacertify/images/favicon-48.png";
	const scope = root || document;
	try {
		scope.querySelectorAll(".ic-greeting-brand").forEach((brand) => {
			if (brand.querySelector(".ic-home-brand-icon")) {
				const img = brand.querySelector(".ic-home-brand-icon");
				if (img && img.getAttribute("src") !== iconSrc) img.setAttribute("src", iconSrc);
				return;
			}
			const img = document.createElement("img");
			img.className = "ic-home-brand-icon";
			img.src = iconSrc;
			img.width = 48;
			img.height = 48;
			img.alt = "Instacertify";
			const text = Array.from(brand.childNodes).filter(
				(n) => !(n.nodeType === 1 && n.classList && n.classList.contains("ic-home-brand-icon"))
			);
			brand.innerHTML = "";
			brand.appendChild(img);
			const wrap = document.createElement("span");
			wrap.className = "ic-greeting-brand-text";
			text.forEach((n) => wrap.appendChild(n));
			if (!wrap.textContent.trim()) {
				wrap.innerHTML = 'Insta<span>certify</span>';
			}
			brand.appendChild(wrap);
		});
	} catch (e) {
		/* ignore */
	}
	try {
		document.querySelectorAll(
			".navbar .app-logo, .navbar .navbar-brand img, .navbar img.app-logo, .sidebar-logo img"
		).forEach((el) => {
			if (el && el.tagName === "IMG") {
				el.src = iconSrc;
			}
		});
	} catch (e) {
		/* ignore */
	}
};

(function bindFaviconBrandIcons() {
	const run = () => {
		try {
			instacertify.apply_favicon_brand_icons(document);
			const home = instacertify.query_deep && instacertify.query_deep("#ic-home-root");
			if (home && home.getRootNode && home.getRootNode() !== document) {
				instacertify.apply_favicon_brand_icons(home.getRootNode());
			}
		} catch (e) {
			/* ignore */
		}
	};
	$(document).ready(run);
	$(document).on("page-change", () => setTimeout(run, 80));
	setTimeout(run, 400);
	setTimeout(run, 1200);
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
				"Testing & Samples": "flask-conical",
				Laboratories: "microscope",
				"Quote Format Library": "book-open",
				"Documents Collection Sheets": "clipboard-list",
				"Document Collection Library": "folder-open",
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
		Cut: "scissors",
		Minimize: "minimize-2",
		Maximize: "maximize-2",
		Expand: "expand",
		Collapse: "collapse",
		"Move Forward": "chevron-right",
		Forward: "chevron-right",
		Delete: "trash-2",
		Print: "printer",
		PDF: "file-text",
		Email: "mail",
		Reload: "refresh-cw",
		"Reload List": "refresh-cw",
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
		if (/cancel|close|discard|cut\b/i.test(n)) return /cut/i.test(n) ? "scissors" : "x";
		if (/minimize/i.test(n)) return "minimize-2";
		if (/maximize|expand/i.test(n)) return "maximize-2";
		if (/move\s*forward|forward/i.test(n)) return "chevron-right";
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

		// List pages first (Quotation / Lead / Labs / etc. from home sidebar).
		// Prefer list over cur_frm — form context can linger after navigation.
		const listview = window.cur_list;
		if (listview && listview.doctype && listview.page === page) {
			const $btn = page.add_action_icon(
				"printer",
				() => {
					if (typeof listview.print_documents === "function") {
						listview.print_documents();
						return;
					}
					const names = (
						(listview.get_checked_items && listview.get_checked_items(true)) ||
						[]
					).filter(Boolean);
					if (!names.length) {
						frappe.show_alert({
							message: __("Select one or more rows to print"),
							indicator: "orange",
						});
						return;
					}
					try {
						if (frappe.BulkOperations) {
							new frappe.BulkOperations({ doctype: listview.doctype }).print(names);
							return;
						}
					} catch (e) {
						/* fall through */
					}
					frappe.set_route("print", listview.doctype, names[0]);
				},
				"ic-print-action",
				__("Print")
			);
			if ($btn && $btn.addClass) $btn.addClass("ic-print-action");
			return;
		}

		// Form print
		const frm = cur_frm;
		if (
			frm &&
			frm.page === page &&
			frappe.model.can_print_doc &&
			frappe.model.can_print_doc(frm) &&
			!(frm.is_new && frm.is_new())
		) {
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
	}

	function stylePageIconGroup(page) {
		const $group =
			(page && (page.icon_group || (page.page_actions && page.page_actions.find(".page-icon-group")))) ||
			$(".page-head .page-icon-group").first();
		if (!$group || !$group.length) return;
		$group.removeClass("hide").css({
			display: "inline-flex",
			visibility: "visible",
			opacity: 1,
		});
		$group.find(".icon-btn, button").each(function () {
			const $b = $(this);
			$b.removeClass("text-muted hide")
				.addClass("ic-line-icon-btn")
				.css({
					display: "inline-flex",
					visibility: "visible",
					opacity: 1,
					color: "#0B1820",
					border: "none",
					boxShadow: "none",
					outline: "none",
					background: "transparent",
				});
			$b.find("svg.es-icon, .es-icon, use").each(function () {
				const $el = $(this);
				if ($el.closest("svg").hasClass("es-icon") || $el.is("svg.es-icon") || $el.hasClass("es-icon")) {
					$el.css({
						fill: "#0B1820",
						stroke: "none",
						color: "#0B1820",
						opacity: 1,
						visibility: "visible",
					});
				}
			});
			$b.find("svg.es-icon, .es-icon").css({
				fill: "#0B1820",
				stroke: "none",
				color: "#0B1820",
				opacity: 1,
				visibility: "visible",
				width: "18px",
				height: "18px",
			});
			$b.find("svg.icon:not(.es-icon)").css({
				stroke: "#0B1820",
				color: "#0B1820",
				opacity: 1,
				visibility: "visible",
				width: "18px",
				height: "18px",
			});
		});
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
			stylePageIconGroup(page);
			ensurePrintActionIcon(page);
			stylePageIconGroup(page);
			// Form custom groups (Library / Actions / Test on Quotation Template, etc.)
			(page.page_actions || $()).find(".inner-group-button > .btn, .custom-actions .btn, .actions-btn-group .btn").each(
				function () {
					const $b = $(this);
					if ($b.hasClass("btn-primary") || $b.hasClass("btn-warning") || $b.hasClass("btn-danger")) return;
					$b.css({
						color: "#033447",
						border: "none",
						boxShadow: "none",
						background: "transparent",
						opacity: 1,
						visibility: "visible",
					});
					ensureIconOnButton($b);
				}
			);
			// Cut / Minimize on any open modal
			$(".modal.show .btn-modal-close, .modal.show .btn-modal-minimize, .modal.show .btn[data-label='Cut'], .modal.show button[title='Cut'], .modal.show button[aria-label='Cut']").each(
				function () {
					const $b = $(this);
					$b.css({
						display: "inline-flex",
						visibility: "visible",
						opacity: 1,
						color: "#0B1820",
						border: "none",
						background: "transparent",
					});
					$b.find("svg, .icon").css({ stroke: "#0B1820", color: "#0B1820", opacity: 1 });
					ensureIconOnButton($b);
				}
			);
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
		if (window.cur_list && cur_list.page) decoratePage(cur_list.page);
		// Global pass for list toolbars opened from home sidebar
		stylePageIconGroup(null);
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

	let _icDecorateTimer = null;
	const schedule = () => {
		if (_icDecorateTimer) clearTimeout(_icDecorateTimer);
		_icDecorateTimer = setTimeout(decorateAll, 80);
	};

	$(document).on("page-change", schedule);
	$(document).on("form-refresh", schedule);
	$(document).on("shown.bs.modal", schedule);
	$(document).on("list_view_rendered", schedule);
	$(document).ready(schedule);
	setTimeout(schedule, 500);
	setTimeout(schedule, 1500);

	// Keep icons after Frappe rebuilds the toolbar
	frappe.after_ajax && frappe.after_ajax(schedule);

	// Watch page-head for list Reload / Print icon injection
	try {
		if (window.MutationObserver) {
			const mo = new MutationObserver((mutations) => {
				for (let i = 0; i < mutations.length; i++) {
					const t = mutations[i].target;
					if (
						t &&
						(t.classList?.contains("page-icon-group") ||
							t.classList?.contains("page-actions") ||
							t.classList?.contains("page-head") ||
							(typeof t.closest === "function" &&
								t.closest(".page-head, .page-icon-group, .standard-actions")))
					) {
						schedule();
						return;
					}
				}
			});
			mo.observe(document.body, { childList: true, subtree: true });
		}
	} catch (e) {
		/* ignore */
	}
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
		try {
			instacertify.apply_favicon_brand_icons(document);
		} catch (e) {
			/* ignore */
		}
		return;
	}
	const icon = frappe.utils.escape_html(instacertify.brand.icon || instacertify.brand.favicon);
	const html = `
		<div class="ic-greeting">
			<div class="ic-greeting-brand">
				<img class="ic-home-brand-icon" src="${icon}" width="48" height="48" alt="Instacertify" />
				<span class="ic-greeting-brand-text">Insta<span>certify</span></span>
			</div>
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
		"Samples In Warehouse": {
			doctype: "IC Sample Tracking",
			filters: { sample_location: "At Instacertify Warehouse" },
		},
		"Samples In Storage": {
			doctype: "IC Sample Tracking",
			filters: { sample_location: ["in", ["At Instacertify Warehouse", "At Instacertify Storage"]] },
		},
		"Samples Returned to Client": {
			doctype: "IC Sample Tracking",
			filters: { sample_location: "Returned to Client" },
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
	onload(frm) {
		instacertify.ensure_party_address_contact_fields();
	},
	refresh(frm) {
		instacertify.ensure_party_address_contact_fields();
		instacertify.apply_service_quote_mandatory(frm);
		instacertify.apply_quotation_naming_series(frm);
		instacertify.add_change_currency_button(frm, { fieldname: "currency" });
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

instacertify.ensure_party_address_contact_fields = function () {
	if (instacertify._party_fields_ensuring) return;
	instacertify._party_fields_ensuring = true;
	frappe.call({
		method: "instacertify.setup.contact_billing.ensure_party_fields",
		callback() {
			instacertify._party_fields_ensuring = false;
			instacertify._party_fields_ready = true;
		},
		error() {
			instacertify._party_fields_ensuring = false;
		},
	});
};

instacertify.apply_service_quote_mandatory = function (frm) {
	// Service business: only Customer is mandatory — products/services are free text, not inventory
	frm.set_df_property("party_name", "reqd", 1);
	frm.set_df_property("quotation_to", "reqd", 0);
	frm.set_df_property("ic_quotation_type", "reqd", 0);
	frm.set_df_property("ic_quotation_template", "reqd", 0);
	frm.set_df_property("ic_subject", "reqd", 0);
	frm.set_df_property("order_type", "reqd", 0);
	[
		"shipping_rule",
		"taxes_and_charges",
		"tax_category",
		"payment_terms_template",
		"payment_schedule",
		"customer_address",
		"shipping_address_name",
		"company_address",
		"company_gstin",
		"place_of_supply",
		"gst_category",
		"billing_address_gstin",
		"contact_person",
		"contact_display",
		"contact_email",
		"contact_mobile",
		"customer_name",
		"address_display",
		"shipping_address",
		"company_contact_person",
		"tc_name",
		"ic_assignees",
		"ic_primary_assignee",
		"ic_payment_terms",
		"ic_quote_number",
		"naming_series",
	].forEach((f) => {
		if (frm.fields_dict[f]) frm.set_df_property(f, "reqd", 0);
	});
	if (frm.fields_dict.ic_quote_number) {
		frm.set_df_property("ic_quote_number", "read_only", 1);
		frm.set_df_property(
			"ic_quote_number",
			"description",
			__("Filled automatically from the naming series after save (e.g. QTN-SRV-00001).")
		);
		if (!frm.is_new() && frm.doc.name && !frm.doc.ic_quote_number) {
			frm.set_value("ic_quote_number", frm.doc.name);
		}
	}
	if (frm.fields_dict.items) {
		frm.set_df_property("items", "reqd", 0);
	}
	if (frm.fields_dict.ic_section_assignees) {
		frm.set_df_property("ic_section_assignees", "collapsible", 1);
	}
	if (!frm.doc.quotation_to) {
		frm.set_value("quotation_to", "Customer");
	}
	// Allow typing a free-text service name in Items (no Item master required)
	const grid = frm.fields_dict.items && frm.fields_dict.items.grid;
	if (grid) {
		grid.update_docfield_property("item_code", "reqd", 0);
		grid.update_docfield_property("item_name", "reqd", 0);
		grid.update_docfield_property(
			"item_name",
			"description",
			__("Free-text service / product — no inventory Item required. Price can be suggested from the lab library.")
		);
	}
};

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

// Free-text service lines on Quotation Items — suggest price from lab purchase/scope library
frappe.ui.form.on("Quotation Item", {
	item_name(frm, cdt, cdn) {
		instacertify.suggest_quote_item_service_price(frm, cdt, cdn);
	},
	description(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row && !row.item_code && !row.item_name && row.description) {
			frappe.model.set_value(cdt, cdn, "item_name", row.description);
		}
	},
});

instacertify.suggest_quote_item_service_price = function (frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (!row) return;
	const label = (row.item_name || row.description || "").trim();
	if (!label) return;
	// If an inventory item was picked, leave rate alone
	if (row.item_code && !String(row.item_code).startsWith("SVC-") && row.item_code !== "CUSTOMER-SERVICE") {
		return;
	}
	frappe.call({
		method: "instacertify.setup.service_quote.suggest_service_price",
		args: { label },
		callback(r) {
			const d = r.message || {};
			if (d.item_code) {
				frappe.model.set_value(cdt, cdn, "item_code", d.item_code);
			}
			if (!row.qty) frappe.model.set_value(cdt, cdn, "qty", 1);
			const offers = d.offers || [];
			if (offers.length > 1) {
				instacertify.open_quote_item_lab_price_picker(frm, cdt, cdn, offers, d);
			} else if (flt(d.suggested_selling_price) > 0) {
				frappe.model.set_value(cdt, cdn, "rate", d.suggested_selling_price);
				frappe.show_alert({
					message: __("Suggested price {0} from lab library", [
						format_currency(d.suggested_selling_price, d.currency || frm.doc.currency || "INR"),
					]),
					indicator: "green",
				});
			}
		},
	});
};

instacertify.open_quote_item_lab_price_picker = function (frm, cdt, cdn, offers, hint) {
	const rows_html = (offers || [])
		.map((o, idx) => {
			const buy = format_currency(o.purchase_price || 0, o.currency || "INR");
			const sell = format_currency(o.selling_price || 0, o.currency || "INR");
			return `<tr data-idx="${idx}" class="ic-lab-offer-row" style="cursor:pointer">
				<td><b>${frappe.utils.escape_html(o.laboratory_name || "")}</b></td>
				<td>${frappe.utils.escape_html(o.test_name || "")}</td>
				<td>${frappe.utils.escape_html(o.applicable_standard || "—")}</td>
				<td style="text-align:right;font-weight:700;color:#EC691F">${frappe.utils.escape_html(buy)}</td>
				<td style="text-align:right">${frappe.utils.escape_html(sell)}</td>
			</tr>`;
		})
		.join("");
	const d = new frappe.ui.Dialog({
		title: __("Suggest price from lab library"),
		size: "large",
		fields: [
			{
				fieldtype: "HTML",
				options: `<div class="text-muted" style="margin-bottom:8px">
					${__("Pick a lab scope offer — selling price is suggested onto this service line:")}
				</div>
				<table class="table table-bordered table-hover" style="margin:0">
					<thead><tr>
						<th>${__("Laboratory")}</th><th>${__("Test")}</th><th>${__("Standard")}</th>
						<th style="text-align:right">${__("Purchase")}</th>
						<th style="text-align:right">${__("Suggested Sell")}</th>
					</tr></thead>
					<tbody>${rows_html}</tbody>
				</table>`,
			},
		],
	});
	d.show();
	d.$wrapper.find(".ic-lab-offer-row").on("click", function () {
		const idx = cint($(this).data("idx"));
		const offer = offers[idx];
		if (!offer) return;
		d.hide();
		if (hint && hint.item_code) {
			frappe.model.set_value(cdt, cdn, "item_code", hint.item_code);
		}
		frappe.model.set_value(cdt, cdn, "rate", offer.selling_price || 0);
		frappe.show_alert({
			message: __("Suggested price {0} from {1}", [
				format_currency(offer.selling_price || 0, offer.currency || "INR"),
				offer.laboratory_name || __("lab library"),
			]),
			indicator: "green",
		});
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
						"Only Customer is required. Type, format, products, and services are optional free text (no inventory)."
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
	// Cost / commercials always available — on Testing quotes they sit under test lines
	["ic_section_costing", "ic_cost_items", "ic_section_cost_totals"].forEach((f) => {
		if (frm.fields_dict[f]) frm.toggle_display(f, true);
	});
	if (frm.fields_dict.ic_section_costing) {
		frm.set_df_property(
			"ic_section_costing",
			"label",
			isTesting
				? __("Consulting & Other Commercials (below Testing)")
				: __("7. Cost Breakdown / Commercials")
		);
	}
	if (frm.fields_dict.ic_cost_items) {
		frm.set_df_property(
			"ic_cost_items",
			"description",
			isTesting
				? __(
						"Add consulting fees, government fees, or other charges here. On the customer quote they appear in a table below Testing Prices."
				  )
				: __(
						"Particulars / Line Name = customer-facing name (rename freely). Cost Component = any label. Charges Display overrides Amount on print. Mark pass-through lines as Do Not Count as Revenue."
				  )
		);
	}
	if (t === "Testing") {
		frm.meta.default_print_format = "Instacertify Testing Quotation";
	} else if (["Consulting", "Renewal", "Service", "Other"].includes(t)) {
		frm.meta.default_print_format = "Instacertify Consulting Quotation";
	} else {
		frm.meta.default_print_format = "Instacertify Quotation";
	}
	frm.set_df_property("ic_subject", "reqd", 0);
};

frappe.ui.form.on("IC Quotation Test Item", {
	form_render(frm, cdt, cdn) {
		instacertify.load_quote_test_library_options(frm, cdt, cdn);
		instacertify.load_lab_scope_options(frm, cdt, cdn);
		instacertify.load_quote_test_lab_offers(frm, cdt, cdn);
	},
	product_name(frm, cdt, cdn) {
		// Free-text customer product — no Item master required
	},
	laboratory(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "lab_test_scope", "");
		frappe.model.set_value(cdt, cdn, "lab_scope_row", "");
		frappe.model.set_value(cdt, cdn, "lab_offer", "");
		frappe.model.set_value(cdt, cdn, "test_name", "");
		frappe.model.set_value(cdt, cdn, "applicable_standard", "");
		frappe.model.set_value(cdt, cdn, "description", "");
		frappe.model.set_value(cdt, cdn, "purchase_price", 0);
		frappe.model.set_value(cdt, cdn, "suggested_selling_price", 0);
		frappe.model.set_value(cdt, cdn, "per_unit_charges", 0);
		frappe.model.set_value(cdt, cdn, "testing_charges", 0);
		frappe.model.set_value(cdt, cdn, "laboratory_accreditation", "");
		if (!row.laboratory) {
			frappe.model.set_value(cdt, cdn, "lab_initials", "");
			instacertify.set_lab_scope_autocomplete(frm, []);
			instacertify.load_quote_test_library_options(frm, cdt, cdn);
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
		frappe.db.get_value("IC Laboratory", row.laboratory, ["lab_initials", "laboratory_name"], (v) => {
			if (v && v.lab_initials) {
				frappe.model.set_value(cdt, cdn, "lab_initials", v.lab_initials);
			}
		});
		instacertify.load_lab_scope_options(frm, cdt, cdn);
		instacertify.load_quote_test_library_options(frm, cdt, cdn);
	},
	test_name(frm, cdt, cdn) {
		frappe.model.set_value(cdt, cdn, "lab_offer", "");
		frappe.model.set_value(cdt, cdn, "applicable_standard", "");
		frappe.model.set_value(cdt, cdn, "purchase_price", 0);
		frappe.model.set_value(cdt, cdn, "suggested_selling_price", 0);
		frappe.model.set_value(cdt, cdn, "per_unit_charges", 0);
		instacertify.load_quote_test_library_options(frm, cdt, cdn);
		instacertify.maybe_autofill_single_standard(frm, cdt, cdn);
	},
	applicable_standard(frm, cdt, cdn) {
		frappe.model.set_value(cdt, cdn, "lab_offer", "");
		instacertify.apply_lab_scoped_pricing(frm, cdt, cdn);
	},
	lab_offer(frm, cdt, cdn) {
		instacertify.apply_quote_test_lab_offer(frm, cdt, cdn);
	},
	lab_test_scope(frm, cdt, cdn) {
		instacertify.apply_lab_test_scope(frm, cdt, cdn);
	},
	number_of_samples(frm, cdt, cdn) {
		instacertify.recalc_test_row(frm, cdt, cdn);
	},
	suggested_selling_price(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "per_unit_charges", row.suggested_selling_price || 0).then(() => {
			instacertify.recalc_test_row(frm, cdt, cdn);
		});
	},
	per_unit_charges(frm, cdt, cdn) {
		instacertify.recalc_test_row(frm, cdt, cdn);
	},
	purchase_price(frm, cdt, cdn) {
		/* editable internal cost — no total impact */
	},
});

instacertify.load_quote_test_library_options = function (frm, cdt, cdn) {
	const row = locals[cdt][cdn] || {};
	const grid = frm.fields_dict.ic_test_items && frm.fields_dict.ic_test_items.grid;
	if (!grid) return;
	const lab = row.laboratory || "";
	frappe.call({
		method: "instacertify.laboratory.api.get_test_name_options",
		args: {
			applicable_standard: "",
			laboratory: lab,
		},
		callback(r) {
			const opts = (r.message || []).map((o) => o.value || o).filter(Boolean);
			grid.update_docfield_property("test_name", "options", opts.join("\n"));
		},
	});
	frappe.call({
		method: "instacertify.laboratory.api.get_standard_options",
		args: {
			test_name: row.test_name || "",
			laboratory: lab,
		},
		callback(r) {
			const opts = (r.message || []).map((o) => o.value || o).filter(Boolean);
			grid.update_docfield_property("applicable_standard", "options", opts.join("\n"));
		},
	});
};

instacertify.maybe_autofill_single_standard = function (frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (!row || !row.laboratory || !row.test_name) return;
	frappe.call({
		method: "instacertify.laboratory.api.get_standards_for_test",
		args: {
			test_name: row.test_name,
			laboratory: row.laboratory,
		},
		callback(r) {
			const opts = (r.message || []).filter((o) => o && o.value && !o.is_other);
			if (opts.length === 1) {
				frappe.model.set_value(cdt, cdn, "applicable_standard", opts[0].value).then(() => {
					instacertify.apply_lab_scoped_pricing(frm, cdt, cdn);
				});
			}
		},
	});
};

instacertify.apply_lab_scoped_pricing = function (frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (!row || !row.laboratory || !row.test_name) return;
	frappe.call({
		method: "instacertify.laboratory.api.resolve_lab_test_pricing",
		args: {
			laboratory: row.laboratory,
			test_name: row.test_name,
			applicable_standard: row.applicable_standard || "",
		},
		callback(r) {
			const s = r.message;
			if (!s) {
				frappe.show_alert({
					message: __(
						"This test/standard is not in the selected lab's scope. Pick another from the lab library."
					),
					indicator: "orange",
				});
				return;
			}
			if (s.scope_row) frappe.model.set_value(cdt, cdn, "lab_scope_row", s.scope_row);
			if (s.lab_initials) frappe.model.set_value(cdt, cdn, "lab_initials", s.lab_initials);
			if (s.description && !row.description) {
				frappe.model.set_value(cdt, cdn, "description", s.description);
			}
			if (s.applicable_standard && !row.applicable_standard) {
				frappe.model.set_value(cdt, cdn, "applicable_standard", s.applicable_standard);
			}
			frappe.model.set_value(cdt, cdn, "purchase_price", s.purchase_price || 0);
			frappe.model.set_value(cdt, cdn, "suggested_selling_price", s.selling_price || 0);
			frappe.model.set_value(cdt, cdn, "per_unit_charges", s.selling_price || 0).then(() => {
				instacertify.recalc_test_row(frm, cdt, cdn);
			});
			if (s.currency) frappe.model.set_value(cdt, cdn, "currency", s.currency);
			if (s.label) frappe.model.set_value(cdt, cdn, "lab_test_scope", s.label);
			frappe.show_alert({
				message: __("Prices from {0}: buy {1} · sell {2}", [
					s.lab_initials || s.laboratory_name || row.laboratory,
					format_currency(s.purchase_price || 0, s.currency || "INR"),
					format_currency(s.selling_price || 0, s.currency || "INR"),
				]),
				indicator: "green",
			});
		},
	});
};

instacertify.load_quote_test_lab_offers = function (frm, cdt, cdn, opts) {
	opts = opts || {};
	const row = locals[cdt][cdn];
	if (!row) return;
	const grid = frm.fields_dict.ic_test_items && frm.fields_dict.ic_test_items.grid;
	if (!row.applicable_standard && !row.test_name) {
		if (grid) grid.update_docfield_property("lab_offer", "options", "");
		return;
	}
	frappe.call({
		method: "instacertify.laboratory.api.get_labs_for_standard",
		args: {
			applicable_standard: row.applicable_standard || "",
			test_name: row.test_name || "",
		},
		callback(r) {
			const offers = r.message || [];
			frm._ic_quote_lab_offers = frm._ic_quote_lab_offers || {};
			frm._ic_quote_lab_offers[cdn] = offers;
			if (grid) {
				grid.update_docfield_property(
					"lab_offer",
					"options",
					offers.map((o) => o.value).join("\n")
				);
			}
			if (opts.open_picker && offers.length) {
				instacertify.open_quote_test_lab_picker(frm, cdt, cdn, offers);
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

instacertify.open_quote_test_lab_picker = function (frm, cdt, cdn, offers) {
	const rows_html = offers
		.map((o, idx) => {
			const buy = format_currency(o.purchase_price || 0, o.currency || "INR");
			const sell = format_currency(o.selling_price || 0, o.currency || "INR");
			return `<tr data-idx="${idx}" class="ic-lab-offer-row" style="cursor:pointer">
				<td><b>${frappe.utils.escape_html(o.laboratory_name || "")}</b></td>
				<td>${frappe.utils.escape_html(o.location || "—")}</td>
				<td>${frappe.utils.escape_html(o.test_name || "")}</td>
				<td>${frappe.utils.escape_html(o.applicable_standard || "—")}</td>
				<td style="text-align:right;font-weight:700;color:#EC691F">${frappe.utils.escape_html(buy)}</td>
				<td style="text-align:right">${frappe.utils.escape_html(sell)}</td>
			</tr>`;
		})
		.join("");
	const d = new frappe.ui.Dialog({
		title: __("Choose lab — suggest price from lab library"),
		size: "extra-large",
		fields: [
			{
				fieldtype: "HTML",
				options: `<div class="text-muted" style="margin-bottom:8px">
					${__("Labs offering this standard/test. Selling price is suggested onto the quote line:")}
				</div>
				<table class="table table-bordered table-hover" style="margin:0">
					<thead><tr>
						<th>${__("Laboratory")}</th><th>${__("Location")}</th>
						<th>${__("Test")}</th><th>${__("Standard")}</th>
						<th style="text-align:right">${__("Lab Purchase")}</th>
						<th style="text-align:right">${__("Suggested Sell")}</th>
					</tr></thead>
					<tbody>${rows_html}</tbody>
				</table>`,
			},
		],
	});
	d.show();
	d.$wrapper.find(".ic-lab-offer-row").on("click", function () {
		const idx = cint($(this).data("idx"));
		const offer = offers[idx];
		if (!offer) return;
		d.hide();
		frappe.model.set_value(cdt, cdn, "lab_offer", offer.value).then(() => {
			instacertify.apply_quote_test_lab_offer(frm, cdt, cdn, offer);
		});
	});
};

instacertify.apply_quote_test_lab_offer = function (frm, cdt, cdn, offer) {
	const row = locals[cdt][cdn];
	if (!row) return;
	const apply = (s) => {
		if (!s) return;
		if (s.laboratory) frappe.model.set_value(cdt, cdn, "laboratory", s.laboratory);
		if (s.lab_initials) frappe.model.set_value(cdt, cdn, "lab_initials", s.lab_initials);
		if (s.test_name) frappe.model.set_value(cdt, cdn, "test_name", s.test_name);
		if (s.applicable_standard) {
			frappe.model.set_value(cdt, cdn, "applicable_standard", s.applicable_standard);
		}
		if (s.description) frappe.model.set_value(cdt, cdn, "description", s.description);
		if (s.scope_row) frappe.model.set_value(cdt, cdn, "lab_scope_row", s.scope_row);
		if (s.label || s.scope_label) {
			frappe.model.set_value(cdt, cdn, "lab_test_scope", s.label || s.scope_label);
		}
		frappe.model.set_value(cdt, cdn, "purchase_price", s.purchase_price || 0);
		frappe.model.set_value(cdt, cdn, "suggested_selling_price", s.selling_price || 0);
		frappe.model.set_value(cdt, cdn, "per_unit_charges", s.selling_price || 0).then(() => {
			instacertify.recalc_test_row(frm, cdt, cdn);
		});
		if (s.currency) frappe.model.set_value(cdt, cdn, "currency", s.currency);
		frappe.show_alert({
			message: __("Suggested selling price {0} from lab library", [
				format_currency(s.selling_price || 0, s.currency || "INR"),
			]),
			indicator: "green",
		});
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
			test_name: row.test_name,
			laboratory: row.laboratory,
			scope_row: row.lab_scope_row,
		},
		callback(r) {
			apply(r.message);
		},
	});
};

instacertify.recalc_test_row = function (frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	const units = row.number_of_samples || 1;
	let rate = row.suggested_selling_price;
	if (rate == null || rate === "") {
		rate = row.per_unit_charges;
	}
	if (rate != null && rate !== "") {
		if (flt(row.per_unit_charges) !== flt(rate)) {
			frappe.model.set_value(cdt, cdn, "per_unit_charges", rate);
		}
		frappe.model.set_value(cdt, cdn, "testing_charges", flt(rate) * units);
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
			if (s.description) {
				frappe.model.set_value(cdt, cdn, "description", s.description);
			}
			frappe.model.set_value(cdt, cdn, "purchase_price", s.purchase_price || 0);
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
		static: false,
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "help",
				options: `<div class="ic-quote-dialog-help">
					<div class="ic-quote-dialog-step"><strong>${__("Optional.")}</strong> ${__(
						"Only Customer is required to save a quote. Type, format, and product lines are optional."
					)}</div>
					<div class="ic-quote-dialog-step"><strong>${__("1.")}</strong> ${__(
						"Select major category: Consulting, Testing, Renewal, or Other (optional)"
					)}</div>
					<div class="ic-quote-dialog-step"><strong>${__("2.")}</strong> ${__(
						"Choose a template from the library, or continue blank"
					)}</div>
					<div class="ic-quote-dialog-step text-muted">${__(
						"Products and services are free-text (no inventory Item required)."
					)}</div>
				</div>`,
			},
			{
				fieldname: "ic_quotation_type",
				fieldtype: "Select",
				label: __("Major Category"),
				options: TYPE_OPTIONS.map((t) => t.value).join("\n"),
				reqd: 0,
				default: "Consulting",
				description: __("Optional — loads templates from the Quote Format Library"),
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
				reqd: 0,
				description: __(
					"Optional. Admins / Ops can add more via Quote Format Library upload."
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
				default: 1,
			},
		],
		primary_action_label: __("Start Quotation"),
		primary_action(values) {
			const skip = cint(values.skip_format) || !values.ic_quotation_template;
			const qtype = values.ic_quotation_type || "Consulting";

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
						frm.scroll_to_field("party_name");
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
									frm.scroll_to_field("party_name") ||
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
				`<strong>${frappe.utils.escape_html(f.display_name || f.template_name || f.name)}</strong>` +
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
		// Website Link + Login ID + Password must stay visible on Customer
		[
			"ic_section_login",
			"ic_website_link",
			"ic_customer_user_id",
			"ic_column_login",
			"ic_customer_password",
			"ic_login_notes",
			"ic_section_more_portals",
			"ic_portal_credentials",
		].forEach((fn) => {
			if (frm.fields_dict[fn]) frm.set_df_property(fn, "hidden", 0);
		});
		if (frm.fields_dict.ic_section_login) {
			frm.set_df_property("ic_section_login", "label", __("Customer Login Credentials"));
		}
		if (frm.fields_dict.ic_website_link) {
			frm.set_df_property("ic_website_link", "label", __("Website Link"));
		}
		if (frm.fields_dict.ic_customer_user_id) {
			frm.set_df_property("ic_customer_user_id", "label", __("Login ID"));
		}
		if (frm.fields_dict.ic_customer_password) {
			frm.set_df_property("ic_customer_password", "label", __("Password"));
		}
		if (!frm.__ic_login_btn) {
			frm.__ic_login_btn = 1;
			frm.add_custom_button(__("Login Credentials"), () => {
				frm.scroll_to_field(
					frm.fields_dict.ic_website_link ? "ic_website_link" : "ic_section_login"
				);
			});
		}
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
			frm.add_custom_button(__("Testing & Samples"), () => {
				frappe.route_options = { customer: frm.doc.name };
				frappe.set_route("testing-samples");
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
			const $hist = frm.fields_dict.ic_history_html && frm.fields_dict.ic_history_html.$wrapper;
			if ($hist) {
				$hist.find("[data-ic-ts-customer]").off("click.icTs").on("click.icTs", function (e) {
					e.preventDefault();
					frappe.route_options = { customer: $(this).attr("data-ic-ts-customer") };
					frappe.set_route("testing-samples");
				});
			}
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
			${ic_related_section(__("Document Collection / Customer Data Sheets"), ic_table([__("Sheet"), __("Status"), __("Project")], doc_rows), __("No document collection sheets"))}
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
			<div class="ic-summary-card accent"><div class="label">${__("Samples")}</div><div class="value">${(d.samples || []).length}</div></div>
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
		p.ic_quotation ? ic_doc_link("Quotation", p.ic_quotation) : "—",
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
	const testing_rows = (d.testing_requests || []).map((t) => {
		const testedFor = [t.product, t.test_name, t.applicable_standard]
			.filter(Boolean)
			.join(" / ");
		return [
			ic_doc_link("IC Testing Request", t.name, t.title || t.name),
			ic_status_pill(t.status),
			ic_esc(testedFor || t.product || t.test_name || "—"),
			t.laboratory
				? ic_doc_link("IC Laboratory", t.laboratory, t.laboratory_name || t.laboratory)
				: "—",
			t.project ? ic_doc_link("Project", t.project) : "—",
			t.quotation ? ic_doc_link("Quotation", t.quotation) : "—",
		];
	});
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
	const sample_rows = (d.samples || []).map((s) => {
		const testedFor =
			s.tested_for ||
			[s.product, s.test_name, s.applicable_standard].filter(Boolean).join(" / ") ||
			s.sample_description ||
			"—";
		const loc = s.sample_location || s.custody_label || "";
		const reportCell = s.test_report
			? `<a class="btn btn-xs btn-primary ic-sample-report-dl" href="${frappe.utils.escape_html(
					s.test_report
			  )}" target="_blank" rel="noopener" download>${__("Download Report")}</a>`
			: s.report_ready
				? `<span class="text-muted">${__("Awaiting upload")}</span>`
				: `<span class="text-muted">—</span>`;
		return [
			ic_doc_link("IC Sample Tracking", s.name, s.tracking_number || s.name),
			`<div class="ic-sample-tested-for">${ic_esc(testedFor)}</div>${
				s.testing_request
					? `<div class="text-muted" style="font-size:11px;margin-top:2px;">${ic_doc_link(
							"IC Testing Request",
							s.testing_request
					  )}</div>`
					: ""
			}`,
			ic_status_pill(s.status),
			`<span style="font-weight:600;color:${
				(instacertify._sample_custody_color &&
					instacertify._sample_custody_color(loc)) ||
				"#546e7a"
			}">${ic_esc(loc || "—")}</span>`,
			s.laboratory
				? ic_doc_link("IC Laboratory", s.laboratory, s.laboratory_name || s.laboratory)
				: "—",
			reportCell,
		];
	});
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
				ic_table(
					[__("Project"), __("Status"), __("Stage"), __("Progress"), __("Quotation"), __("Deadline")],
					project_rows
				),
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
				ic_table(
					[
						__("Request"),
						__("Status"),
						__("Being tested for"),
						__("Laboratory"),
						__("Project"),
						__("Quotation"),
					],
					testing_rows
				),
				__("No testing requests"),
				customer
					? `<a href="/app/testing-samples" class="ic-view-all" data-ic-ts-customer="${ic_esc(
							customer
					  )}">${ic_esc(__("Open Testing & Samples"))}</a>`
					: ""
			)}
			${ic_related_section(
				__("Samples — status & reports"),
				ic_table(
					[
						__("Sample"),
						__("Being tested for"),
						__("Status"),
						__("Location"),
						__("Laboratory"),
						__("Report"),
					],
					sample_rows
				),
				__("No samples"),
				customer
					? `<a href="/app/testing-samples" class="ic-view-all" data-ic-ts-customer="${ic_esc(
							customer
					  )}">${ic_esc(__("Open Testing & Samples"))}</a>`
					: ""
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

// Project progress HTML + saved editable Progress Log
frappe.ui.form.on("Project", {
	refresh(frm) {
		instacertify.render_project_progress_tracker(frm);

		// Optional Quotation map — filter to this customer's quotes
		frm.set_query("ic_quotation", () => {
			const filters = { docstatus: ["<", 2] };
			if (frm.doc.customer) {
				filters.party_name = frm.doc.customer;
				filters.quotation_to = "Customer";
			}
			return { filters };
		});

		if (frm.doc.ic_quotation) {
			frm.add_custom_button(__("Open Quotation"), () => {
				frappe.set_route("Form", "Quotation", frm.doc.ic_quotation);
			}, __("Links"));
		}
		if (frm.doc.customer) {
			frm.add_custom_button(__("Open Customer"), () => {
				frappe.set_route("Form", "Customer", frm.doc.customer);
			}, __("Links"));
			frm.add_custom_button(__("Customer Data Drive"), () => {
				frappe.set_route("Form", "Customer", frm.doc.customer);
			}, __("Links"));
		}
		if (!frm.is_new()) {
			frm.add_custom_button(__("Testing & Samples"), () => {
				frappe.route_options = {
					customer: frm.doc.customer,
					project: frm.doc.name,
				};
				frappe.set_route("testing-samples");
			}, __("Testing"));
			frm.add_custom_button(__("Testing Requests (list)"), () => {
				frappe.set_route("List", "IC Testing Request", { project: frm.doc.name });
			}, __("Testing"));
			frm.add_custom_button(__("Samples (list)"), () => {
				frappe.set_route("List", "IC Sample Tracking", { project: frm.doc.name });
			}, __("Testing"));
			instacertify.render_project_testing_panel(frm);
		}

		frm.add_custom_button(__("Add Progress Log Entry"), () => {
			instacertify.open_progress_log_dialog(frm);
		}, __("Actions"));
		frm.add_custom_button(__("Open Progress Log List"), () => {
			frappe.set_route("List", "IC Project Update", { project: frm.doc.name });
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

/**
 * Keep the form Save button visible and usable after field edits.
 * Frappe often clears/hides primary Save after toolbar refresh when the doc
 * looks "clean" — always re-apply, with short delayed retries.
 */
instacertify.ALWAYS_SAVE_DOCTYPES = [
	"IC Testing Request",
	"IC Sample Tracking",
	"IC Document Request",
	"IC Laboratory",
	"IC Quotation Template",
	"IC Document Checklist Template",
	"IC Test Request Form",
];

instacertify.ensure_form_save_button = function (frm) {
	if (!frm || !frm.page) return;
	const force = () => {
		try {
			if (typeof frm.enable_save === "function") {
				frm.enable_save();
			}
			frm.save_disabled = false;
			const page = frm.page;
			if (!page || typeof page.set_primary_action !== "function") return;

			// Always set primary = Save (do not wait for dirty state).
			page.set_primary_action(__("Save"), () => frm.save());

			const $btn = page.btn_primary;
			if ($btn && $btn.length) {
				$btn
					.addClass("ic-always-save-btn primary-action")
					.attr("data-label", "Save")
					.removeClass("hide hidden d-none disabled")
					.prop("disabled", false)
					.css({
						display: "inline-flex",
						visibility: "visible",
						opacity: 1,
						pointerEvents: "auto",
					});
				const labelText = ($btn.text() || "").replace(/\s+/g, " ").trim();
				if (!/save/i.test(labelText)) {
					if (!$btn.find(".ic-action-label").length) {
						$btn.append(` <span class="ic-action-label">${__("Save")}</span>`);
					} else {
						$btn.find(".ic-action-label").text(__("Save"));
					}
				}
			}
			instacertify._ensure_actions_save_fallback(frm);
		} catch (e) {
			/* ignore */
		}
	};

	force();
	clearTimeout(frm._ic_save_btn_t1);
	clearTimeout(frm._ic_save_btn_t2);
	clearTimeout(frm._ic_save_btn_t3);
	frm._ic_save_btn_t1 = setTimeout(force, 120);
	frm._ic_save_btn_t2 = setTimeout(force, 400);
	frm._ic_save_btn_t3 = setTimeout(force, 1000);
};

/** Fallback under Actions if page-head Save is crowded off-screen. */
instacertify._ensure_actions_save_fallback = function (frm) {
	try {
		if (frm._ic_actions_save_added) return;
		frm.add_custom_button(__("Save"), () => frm.save(), __("Actions"));
		frm._ic_actions_save_added = true;
	} catch (e) {
		/* ignore */
	}
};

// Desk-wide: keep Save on key Instacertify forms (toolbar can clear it after refresh).
$(document).on("form-refresh", function (_e, frm) {
	try {
		if (!frm || !frm.doctype) return;
		if ((instacertify.ALWAYS_SAVE_DOCTYPES || []).indexOf(frm.doctype) < 0) return;
		instacertify.ensure_form_save_button(frm);
	} catch (err) {
		/* ignore */
	}
});
$(document).on("form-dirty", function (_e, frm) {
	try {
		if (!frm || !frm.doctype) return;
		if ((instacertify.ALWAYS_SAVE_DOCTYPES || []).indexOf(frm.doctype) < 0) return;
		instacertify.ensure_form_save_button(frm);
	} catch (err) {
		/* ignore */
	}
});

frappe.ui.form.on("IC Testing Request", {
	onload(frm) {
		instacertify.load_testing_request_library_options(frm);
		instacertify.ensure_form_save_button(frm);
	},
	onload_post_render(frm) {
		instacertify.ensure_form_save_button(frm);
	},
	refresh(frm) {
		frm._ic_actions_save_added = false;
		instacertify.ensure_form_save_button(frm);
		frm.set_query("laboratory", () => ({ filters: { status: "Active" } }));
		instacertify.load_testing_request_library_options(frm);
		instacertify.bind_testing_request_library_pickers(frm);
		instacertify.add_change_currency_button(frm, {
			fieldname: "price_currency",
			force_button: true,
		});
		if (frm.doc.applicable_standard || frm.doc.test_name) {
			instacertify.load_testing_request_lab_offers(frm);
		}
		if (frm.fields_dict.ic_assignees) {
			frm.add_custom_button(__("Assign Me"), () => {
				instacertify.add_me_as_assignee(frm, "ic_assignees");
			}, __("Actions"));
		}
		frm.set_query("quotation", () => {
			const filters = { docstatus: ["<", 2] };
			if (frm.doc.customer) {
				filters.party_name = frm.doc.customer;
				filters.quotation_to = "Customer";
			}
			return { filters };
		});
		frm.set_query("project", () => {
			const filters = {};
			if (frm.doc.customer) filters.customer = frm.doc.customer;
			return { filters };
		});
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
		if (frm.doc.quotation) {
			frm.add_custom_button(__("Open Quotation"), () => {
				frappe.set_route("Form", "Quotation", frm.doc.quotation);
			}, __("Links"));
		}
		if (frm.doc.project) {
			frm.add_custom_button(__("Open Project"), () => {
				frappe.set_route("Form", "Project", frm.doc.project);
			}, __("Links"));
		}
		if (frm.doc.customer) {
			frm.add_custom_button(__("Open Customer"), () => {
				frappe.set_route("Form", "Customer", frm.doc.customer);
			}, __("Links"));
		}
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
						amount: frm.doc.library_buying_price || 0,
					},
					freeze: true,
					callback(r) {
						frappe.set_route("Form", "Purchase Invoice", r.message.name);
					},
				});
			}, __("Billing"));
		}
		if (!frm.is_new()) {
			frm.add_custom_button(__("Edit Price"), () => {
				instacertify.edit_testing_request_prices(frm.doc.name, {
					library_buying_price: frm.doc.library_buying_price,
					suggested_selling_price: frm.doc.suggested_selling_price,
					price_currency: frm.doc.price_currency || "INR",
					on_save() {
						frm.reload_doc().then(() => {
							instacertify.ensure_form_save_button(frm);
						});
					},
				});
			}, __("Actions"));
			// Keep prices visible in form dashboard
			const cur = frm.doc.price_currency || "INR";
			frm.dashboard.clear_headline();
			frm.dashboard.set_headline(
				__(
					"Buying {0} · Selling {1} · {2}",
					[
						format_currency(frm.doc.library_buying_price || 0, cur),
						format_currency(frm.doc.suggested_selling_price || 0, cur),
						cur,
					]
				)
			);
			frm.add_custom_button(__("Create / Share TRF"), () => {
				frappe.call({
					method: "instacertify.trf.api.create_or_get_trf",
					args: { testing_request: frm.doc.name, share: 1 },
					freeze: true,
					freeze_message: __("Preparing Test Request Form…"),
					callback(r) {
						const m = r.message || {};
						const url = m.url || m.share_url || "";
						frappe.msgprint({
							title: __("Test Request Form (TRF)"),
							message: `<p>${__(
								"Share this link so the customer can fill the TRF. Case handlers can also open and fill the same form."
							)}</p>
							<p><a href="${frappe.utils.escape_html(url)}" target="_blank">${frappe.utils.escape_html(
								url
							)}</a></p>
							<p><a href="/app/ic-test-request-form/${encodeURIComponent(
								m.name
							)}">${__("Open TRF (staff fill / PDF)")}</a></p>`,
							indicator: "green",
						});
					},
				});
			}, __("TRF"));
			frm.add_custom_button(__("Open TRF"), () => {
				frappe.call({
					method: "instacertify.trf.api.create_or_get_trf",
					args: { testing_request: frm.doc.name, share: 0 },
					freeze: true,
					callback(r) {
						frappe.set_route("Form", "IC Test Request Form", r.message.name);
					},
				});
			}, __("TRF"));
			frm.add_custom_button(__("Edit TRF"), () => {
				frappe.call({
					method: "instacertify.trf.api.create_or_get_trf",
					args: { testing_request: frm.doc.name, share: 0 },
					freeze: true,
					callback(r) {
						const name = (r.message || {}).name;
						if (!name) return;
						const locked = [
							"Submitted by Customer",
							"Under Review",
							"PDF Generated",
							"Completed",
						].includes((r.message || {}).status || "");
						const open = () => frappe.set_route("Form", "IC Test Request Form", name);
						if (locked) {
							frappe.call({
								method: "instacertify.trf.api.reopen_trf_for_edit",
								args: { name },
								freeze: true,
								callback() {
									frappe.show_alert({
										message: __("TRF reopened for edit"),
										indicator: "green",
									});
									open();
								},
							});
						} else {
							open();
						}
					},
				});
			}, __("TRF"));
			frm.add_custom_button(__("Print QR Labels"), () => {
				frappe.call({
					method: "instacertify.testing.events.get_testing_request_sample_labels",
					args: { testing_request: frm.doc.name },
					freeze: true,
					freeze_message: __("Preparing sample QR labels…"),
					callback(r) {
						if (
							window.instacertify &&
							typeof instacertify.show_testing_request_sample_qr_dialog === "function"
						) {
							instacertify.show_testing_request_sample_qr_dialog(r.message || {});
						} else {
							frappe.msgprint({
								title: __("QR labels"),
								message: __(
									"QR helper did not load. Hard-refresh the page (Ctrl+Shift+R), then try again."
								),
								indicator: "orange",
							});
						}
					},
				});
			});
			frm.add_custom_button(__("Create / Sync Samples"), () => {
				instacertify.ensure_testing_request_samples(frm, { force_sync: 1 });
			}, __("Samples"));
			frm.add_custom_button(__("Print Sample QR Labels"), () => {
				frappe.call({
					method: "instacertify.testing.events.get_testing_request_sample_labels",
					args: { testing_request: frm.doc.name },
					freeze: true,
					freeze_message: __("Preparing sample QR labels…"),
					callback(r) {
						instacertify.show_testing_request_sample_qr_dialog(r.message || {});
					},
				});
			}, __("Samples"));
			frm.add_custom_button(__("Open Sample List"), () => {
				frappe.set_route("List", "IC Sample Tracking", {
					testing_request: frm.doc.name,
				});
			}, __("Samples"));
			instacertify.render_testing_request_samples(frm);
		}
		instacertify.ensure_form_save_button(frm);
	},
	number_of_samples(frm) {
		if (frm.is_new() || frm._ic_skip_lab_picker) return;
		instacertify.ensure_testing_request_samples(frm);
	},
	status(frm) {
		frm.dirty();
		instacertify.ensure_form_save_button(frm);
	},
	priority(frm) {
		frm.dirty();
		instacertify.ensure_form_save_button(frm);
	},
	project(frm) {
		frm.dirty();
		instacertify.ensure_form_save_button(frm);
	},
	assigned_person(frm) {
		frm.dirty();
		instacertify.ensure_form_save_button(frm);
	},
	ic_assignees_add(frm) {
		frm.dirty();
		instacertify.ensure_form_save_button(frm);
	},
	ic_assignees_remove(frm) {
		frm.dirty();
		instacertify.ensure_form_save_button(frm);
	},
	test_report(frm) {
		frm.dirty();
		instacertify.ensure_form_save_button(frm);
	},
	test_name(frm) {
		if (frm._ic_skip_lab_picker) return;
		frm.set_value("lab_offer", "");
		instacertify.load_testing_request_standards_for_test(frm);
		instacertify._schedule_lab_offers_picker(frm);
	},
	applicable_standard(frm) {
		if (frm._ic_skip_lab_picker) return;
		frm.set_value("lab_offer", "");
		instacertify.load_testing_request_tests_for_standard(frm);
		instacertify._schedule_lab_offers_picker(frm);
	},
	lab_offer(frm) {
		if (frm._ic_skip_lab_picker) return;
		if (frm._ic_applying_lab_offer) return;
		instacertify.apply_testing_request_lab_offer(frm);
	},
	laboratory(frm) {
		if (frm._ic_skip_lab_picker) return;
		frm.set_value("lab_test_scope", "");
		frm.set_value("lab_scope_row", "");
		frm.set_value("suggested_selling_price", 0);
		if (frm.fields_dict.library_buying_price) {
			frm.set_value("library_buying_price", 0);
		}
		instacertify.load_testing_request_scope_options(frm);
		frm.dirty();
		instacertify.ensure_form_save_button(frm);
	},
	lab_test_scope(frm) {
		if (frm._ic_skip_lab_picker) return;
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
				frm._ic_skip_lab_picker = true;
				Promise.resolve()
					.then(() => frm.set_value("lab_scope_row", s.name))
					.then(() => frm.set_value("test_name", s.test_name))
					.then(() =>
						s.applicable_standard
							? frm.set_value("applicable_standard", s.applicable_standard)
							: null
					)
					.then(() => frm.set_value("suggested_selling_price", s.selling_price))
					.then(() =>
						frm.fields_dict.library_buying_price
							? frm.set_value("library_buying_price", s.purchase_price)
							: null
					)
					.then(() =>
						s.currency && frm.fields_dict.price_currency
							? frm.set_value("price_currency", s.currency)
							: null
					)
					.then(() => {
						if (s.label && frm.doc.lab_test_scope !== s.label) {
							return frm.set_value("lab_test_scope", s.label);
						}
					})
					.finally(() => {
						frm._ic_skip_lab_picker = false;
						frm.dirty();
						instacertify.ensure_form_save_button(frm);
					});
			},
		});
	},
});

instacertify._schedule_lab_offers_picker = function (frm) {
	if (frm._ic_skip_lab_picker) return;
	clearTimeout(frm._ic_lab_picker_timer);
	frm._ic_lab_picker_timer = setTimeout(() => {
		instacertify.load_testing_request_lab_offers(frm, { open_picker: true });
	}, 120);
};
instacertify._ic_is_other = function (v) {
	return String(v || "").trim().toLowerCase() === "other";
};

instacertify._set_autocomplete_list = function (frm, fieldname, values) {
	frm.set_df_property(fieldname, "options", (values || []).join("\n"));
	const ctrl = frm.fields_dict[fieldname];
	if (ctrl && ctrl.set_data) {
		ctrl.set_data(values);
	} else if (ctrl && ctrl.awesomplete) {
		ctrl.awesomplete.list = values;
	}
};

instacertify.load_testing_request_library_options = function (frm) {
	frappe.call({
		method: "instacertify.laboratory.api.get_test_name_options",
		args: {
			applicable_standard: frm.doc.applicable_standard || "",
		},
		callback(r) {
			const values = (r.message || []).map((o) => o.value || o);
			instacertify._set_autocomplete_list(frm, "test_name", values);
		},
	});
	frappe.call({
		method: "instacertify.laboratory.api.get_standard_options",
		args: {
			test_name: frm.doc.test_name || "",
		},
		callback(r) {
			const values = (r.message || []).map((o) => o.value || o);
			instacertify._set_autocomplete_list(frm, "applicable_standard", values);
		},
	});
};

instacertify.load_testing_request_standards_for_test = function (frm) {
	const test = frm.doc.test_name || "";
	frappe.call({
		method: "instacertify.laboratory.api.get_standards_for_test",
		args: { test_name: test },
		callback(r) {
			const rows = r.message || [];
			const values = rows.map((o) => o.value || o);
			instacertify._set_autocomplete_list(frm, "applicable_standard", values);
			// Auto-pick when exactly one real standard
			const real = values.filter((v) => !instacertify._ic_is_other(v));
			if (real.length === 1 && !frm.doc.applicable_standard) {
				frm.set_value("applicable_standard", real[0]);
			} else if (
				frm.doc.applicable_standard &&
				!instacertify._ic_is_other(frm.doc.applicable_standard) &&
				values.length &&
				!values.includes(frm.doc.applicable_standard)
			) {
				// Current standard no longer related — clear so user re-picks
				frm.set_value("applicable_standard", "");
			}
			// Hint labs that have each standard
			const tips = rows
				.filter((o) => !instacertify._ic_is_other(o.value) && o.lab_names)
				.slice(0, 6)
				.map((o) => `${o.value}: ${o.lab_names}`);
			if (frm.fields_dict.applicable_standard) {
				frm.set_df_property(
					"applicable_standard",
					"description",
					tips.length
						? __("Related to this test — labs: {0}. Pick Other if not listed.", [tips.join(" · ")])
						: __("Standards related to the selected Test Name — includes Other")
				);
			}
		},
	});
};

instacertify.load_testing_request_tests_for_standard = function (frm) {
	const std = frm.doc.applicable_standard || "";
	if (!std || instacertify._ic_is_other(std)) return;
	frappe.call({
		method: "instacertify.laboratory.api.get_test_name_options",
		args: { applicable_standard: std },
		callback(r) {
			const values = (r.message || []).map((o) => o.value || o);
			instacertify._set_autocomplete_list(frm, "test_name", values);
		},
	});
};

instacertify.bind_testing_request_library_pickers = function (frm) {
	// Form change handlers already open the picker (debounced). Only bind
	// focus/compare on lab_offer — avoid triple-firing awesomplete + change.
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
	if (frm._ic_lab_picker_dialog) {
		try {
			frm._ic_lab_picker_dialog.hide();
		} catch (e) {
			/* ignore */
		}
	}
	const rows_html = offers
		.map((o, idx) => {
			const buy = format_currency(o.purchase_price || 0, o.currency || "INR");
			const sell = format_currency(o.selling_price || 0, o.currency || "INR");
			return `<tr data-idx="${idx}" class="ic-lab-offer-row" style="cursor:pointer">
				<td><b>${frappe.utils.escape_html(o.laboratory_name || "")}</b></td>
				<td>${frappe.utils.escape_html(o.location || "—")}</td>
				<td>${frappe.utils.escape_html(o.test_name || "")}</td>
				<td>${frappe.utils.escape_html(o.applicable_standard || "—")}</td>
				<td style="text-align:right;font-weight:700;color:#EC691F">${frappe.utils.escape_html(buy)}</td>
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
					${__("Suggested labs that have this test / standard in the library. One test can appear under multiple standards and labs — pick by buying rate:")}
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
	frm._ic_lab_picker_dialog = d;
	d.show();
	// Bind after show (same pattern as quote picker) so rows are in the DOM
	d.$wrapper.off("click.ic_lab_pick").on("click.ic_lab_pick", ".ic-lab-offer-row", function () {
		const offer = offers[cint($(this).attr("data-idx"))];
		if (!offer) return;
		d.hide();
		instacertify.apply_testing_request_lab_offer(frm, offer);
	});
};

instacertify.apply_testing_request_lab_offer = function (frm, offer) {
	const apply = (s) => {
		if (!s) return;
		frm._ic_skip_lab_picker = true;
		frm._ic_applying_lab_offer = true;
		const done = () => {
			frm._ic_skip_lab_picker = false;
			frm._ic_applying_lab_offer = false;
			frm.dirty();
			instacertify.ensure_form_save_button(frm);
		};
		Promise.resolve()
			.then(() => frm.set_value("lab_offer", s.value || frm.doc.lab_offer || ""))
			.then(() => frm.set_value("laboratory", s.laboratory))
			.then(() => frm.set_value("lab_scope_row", s.scope_row))
			.then(() => (s.test_name ? frm.set_value("test_name", s.test_name) : null))
			.then(() =>
				s.applicable_standard ? frm.set_value("applicable_standard", s.applicable_standard) : null
			)
			.then(() =>
				s.currency && frm.fields_dict.price_currency
					? frm.set_value("price_currency", s.currency)
					: null
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
						"Selected {0} — buying {1}. Click Save to keep changes.",
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

instacertify.ensure_testing_request_samples = function (frm, opts) {
	opts = opts || {};
	if (!frm.doc.name || frm.is_new()) return;
	frappe.call({
		method: "instacertify.testing.events.ensure_samples_for_testing_request",
		args: {
			testing_request: frm.doc.name,
			force_sync: opts.force_sync ? 1 : 0,
		},
		freeze: true,
		freeze_message: __("Linking samples…"),
		callback(r) {
			const m = r.message || {};
			const created = (m.created || []).length;
			if (created) {
				frappe.show_alert({
					message: __("Created {0} sample tracking record(s)", [created]),
					indicator: "green",
				});
			}
			instacertify.render_testing_request_samples(frm, m.samples);
		},
	});
};

instacertify._sample_custody_color = function (loc) {
	const colors = {
		"With Customer": "#1976d2",
		"In Transit to Office": "#ef6c00",
		"At Instacertify Office": "#2e7d32",
		"In Transit to Lab": "#ef6c00",
		"At Laboratory": "#6a1b9a",
		"At Instacertify Warehouse": "#00838f",
		"At Instacertify Storage": "#00838f",
		"In Transit to Client": "#ef6c00",
		"Returned to Client": "#1565c0",
		Discarded: "#c62828",
	};
	return colors[loc] || "#546e7a";
};

instacertify.render_testing_request_samples = function (frm, samples) {
	const wrap = frm.fields_dict.sample_tracking_html;
	if (!wrap) return;

	const paint = (rows) => {
		rows = rows || [];
		if (!rows.length) {
			wrap.$wrapper.html(`
				<div class="ic-tr-samples ic-tr-samples--empty">
					<div class="ic-tr-samples-head">
						<div class="ic-tr-samples-title">${__("Sample Tracking")}</div>
						<p class="ic-tr-samples-sub">
							${__("No samples linked yet. Samples are created from Number of Samples using Product / Test / Laboratory from this request.")}
						</p>
					</div>
					<button type="button" class="btn btn-sm btn-primary ic-tr-ensure-samples">${__("Create Samples")}</button>
				</div>
			`);
			wrap.$wrapper.find(".ic-tr-ensure-samples").on("click", () => {
				instacertify.ensure_testing_request_samples(frm, { force_sync: 1 });
			});
			return;
		}
		const rows_html = rows
			.map((s) => {
				const loc = s.sample_location || s.status || "—";
				const color = instacertify._sample_custody_color(loc);
				const lab = s.laboratory_name || s.laboratory || "—";
				const city = s.laboratory_city
					? `<div class="ic-tr-samples-muted">${frappe.utils.escape_html(s.laboratory_city)}</div>`
					: "";
				return `<tr class="ic-tr-samples-row" data-name="${frappe.utils.escape_html(s.name)}">
					<td class="ic-tr-col-track">
						<a class="ic-tr-track-link" href="/app/ic-sample-tracking/${encodeURIComponent(s.name)}">
							${frappe.utils.escape_html(s.tracking_number || s.name)}
						</a>
					</td>
					<td class="ic-tr-col-desc">${frappe.utils.escape_html(s.sample_description || "—")}</td>
					<td class="ic-tr-col-loc">
						<span class="ic-tr-loc-badge" style="--ic-loc:${color};">${frappe.utils.escape_html(loc)}</span>
					</td>
					<td class="ic-tr-col-lab">${frappe.utils.escape_html(lab)}${city}</td>
					<td class="ic-tr-col-status">${frappe.utils.escape_html(s.status || "")}</td>
					<td class="ic-tr-col-act">
						<button type="button" class="btn btn-xs btn-default ic-open-sample" data-name="${frappe.utils.escape_html(s.name)}">${__("Open")}</button>
					</td>
				</tr>`;
			})
			.join("");
		wrap.$wrapper.html(`
			<div class="ic-tr-samples">
				<div class="ic-tr-samples-head">
					<div>
						<div class="ic-tr-samples-title">${__("Sample Tracking")}
							<span class="ic-tr-samples-count">${rows.length}</span>
						</div>
						<p class="ic-tr-samples-sub">
							${__("Where each sample is now — at lab, Instacertify warehouse, or returned to the client. Update location on the sample form after testing.")}
						</p>
					</div>
					<button type="button" class="btn btn-xs btn-default ic-tr-ensure-samples">${__("Sync from Lab / Count")}</button>
				</div>
				<div class="ic-tr-samples-table-wrap">
					<table class="ic-tr-samples-table">
						<thead>
							<tr>
								<th class="ic-tr-col-track">${__("Tracking #")}</th>
								<th class="ic-tr-col-desc">${__("Description")}</th>
								<th class="ic-tr-col-loc">${__("Location")}</th>
								<th class="ic-tr-col-lab">${__("Laboratory")}</th>
								<th class="ic-tr-col-status">${__("Status")}</th>
								<th class="ic-tr-col-act"></th>
							</tr>
						</thead>
						<tbody>${rows_html}</tbody>
					</table>
				</div>
			</div>
		`);
		wrap.$wrapper.find(".ic-tr-ensure-samples").on("click", () => {
			instacertify.ensure_testing_request_samples(frm, { force_sync: 1 });
		});
		wrap.$wrapper.find(".ic-open-sample, .ic-tr-samples-row").on("click", function (e) {
			if ($(e.target).closest("a, button").length && !$(e.target).closest(".ic-open-sample").length) {
				return;
			}
			const name = $(this).data("name") || $(this).closest("tr").data("name");
			if (name) frappe.set_route("Form", "IC Sample Tracking", name);
		});
	};

	if (samples) {
		paint(samples);
		return;
	}
	frappe.call({
		method: "instacertify.testing.events.get_samples_for_testing_request",
		args: { testing_request: frm.doc.name },
		callback(r) {
			paint(r.message || []);
		},
	});
};

instacertify.render_project_testing_panel = function (frm) {
	if (!frm.doc.name || frm.is_new()) return;
	frappe.call({
		method: "instacertify.testing.events.get_linked_testing_overview",
		args: { project: frm.doc.name },
		callback(r) {
			const d = r.message || {};
			const tests = d.testing_requests || [];
			const samples = d.samples || [];
			const counts = d.custody_counts || {};
			const custody_bits = Object.keys(counts)
				.map(
					(k) =>
						`<span style="margin-right:8px;"><b>${frappe.utils.escape_html(k)}</b>: ${counts[k]}</span>`
				)
				.join("");
			const test_rows = tests
				.slice(0, 8)
				.map((t) => {
					return `<tr>
						<td><a href="/app/ic-testing-request/${encodeURIComponent(t.name)}">${frappe.utils.escape_html(
							t.name
						)}</a></td>
						<td>${frappe.utils.escape_html(t.status || "")}</td>
						<td>${frappe.utils.escape_html(t.product || t.test_name || "—")}</td>
						<td>${frappe.utils.escape_html(t.laboratory_name || t.laboratory || "—")}</td>
					</tr>`;
				})
				.join("");
			const sample_rows = samples
				.slice(0, 10)
				.map((s) => {
					const loc = s.sample_location || "—";
					const color = instacertify._sample_custody_color(loc);
					return `<tr>
						<td><a href="/app/ic-sample-tracking/${encodeURIComponent(s.name)}">${frappe.utils.escape_html(
							s.tracking_number || s.name
						)}</a></td>
						<td><span style="color:${color};font-weight:600">${frappe.utils.escape_html(loc)}</span></td>
						<td>${frappe.utils.escape_html(s.laboratory_name || s.laboratory || "—")}</td>
						<td>${
							s.testing_request
								? `<a href="/app/ic-testing-request/${encodeURIComponent(s.testing_request)}">${frappe.utils.escape_html(
										s.testing_request
								  )}</a>`
								: "—"
						}</td>
					</tr>`;
				})
				.join("");

			const html = `
				<div class="ic-project-testing form-dashboard-section" style="margin:12px 0;padding:12px;border:1px solid #d7e6ef;border-radius:10px;background:#F5F9FD;">
					<div style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:4px;">
						<div style="font-weight:650;color:#0D47A1;">${__("Testing & Sample Custody")}</div>
						<button type="button" class="btn btn-xs btn-primary ic-open-testing-samples">${__("Open Testing & Samples")}</button>
					</div>
					<div class="text-muted" style="font-size:12px;margin-bottom:8px;">
						${__("Generate requests from lab pricing, then update where each sample is — lab, warehouse, or back with the client.")}
					</div>
					<div style="font-size:12px;margin-bottom:10px;">${custody_bits || `<span class="text-muted">${__("No samples yet")}</span>`}</div>
					<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
						<div>
							<div style="font-weight:600;margin-bottom:4px;">${__("Testing Requests")} (${tests.length})</div>
							${
								test_rows
									? `<table class="table table-bordered table-condensed" style="background:#fff;margin:0"><thead><tr>
										<th>${__("Request")}</th><th>${__("Status")}</th><th>${__("Product / Test")}</th><th>${__("Lab")}</th>
									</tr></thead><tbody>${test_rows}</tbody></table>`
									: `<div class="text-muted">${__("No testing requests on this project")}</div>`
							}
						</div>
						<div>
							<div style="font-weight:600;margin-bottom:4px;">${__("Samples")} (${samples.length})</div>
							${
								sample_rows
									? `<table class="table table-bordered table-condensed" style="background:#fff;margin:0"><thead><tr>
										<th>${__("Tracking")}</th><th>${__("Location")}</th><th>${__("Lab")}</th><th>${__("TR")}</th>
									</tr></thead><tbody>${sample_rows}</tbody></table>`
									: `<div class="text-muted">${__("No samples on this project")}</div>`
							}
						</div>
					</div>
				</div>
			`;
			// Prefer progress HTML area; else inject above form layout
			let $panel;
			if (frm.fields_dict.ic_progress_html && frm.fields_dict.ic_progress_html.$wrapper) {
				const $host = frm.fields_dict.ic_progress_html.$wrapper;
				$host.find(".ic-project-testing").remove();
				$host.append(html);
				$panel = $host.find(".ic-project-testing");
			} else if (frm.layout && frm.layout.wrapper) {
				const $body = $(frm.layout.wrapper).find(".form-layout").first();
				$body.find(".ic-project-testing").remove();
				$body.prepend(html);
				$panel = $body.find(".ic-project-testing");
			}
			if ($panel && $panel.length) {
				$panel.find(".ic-open-testing-samples").on("click", () => {
					frappe.route_options = {
						customer: frm.doc.customer,
						project: frm.doc.name,
					};
					frappe.set_route("testing-samples");
				});
			}
		},
	});
};

frappe.ui.form.on("IC Document Request", {
	refresh(frm) {
		frm._ic_actions_save_added = false;
		instacertify.ensure_form_save_button(frm);
		frm.add_custom_button(__("Open Library"), () => {
			frappe.set_route("document-collection-library");
		});
		if (!frm.is_new()) {
			frm.add_custom_button(__("Send to Customer"), () => {
				if (!frm.doc.customer) {
					frappe.msgprint({
						title: __("Customer required"),
						indicator: "orange",
						message: __("Map this sheet to a Customer before sharing."),
					});
					return;
				}
				frappe.call({
					method: "instacertify.documents.api.share_document_request",
					args: { document_request: frm.doc.name },
					callback(r) {
						const url = r.message && r.message.url;
						frappe.msgprint({
							title: __("Documents Collection Sheet — customer link"),
							message: `<p><a href="${frappe.utils.escape_html(url)}" target="_blank" rel="noopener">${frappe.utils.escape_html(url)}</a></p>
								<p class="text-muted">${__("Customer can upload files and fill fields on this link. Copied to clipboard when supported.")}</p>`,
							indicator: "green",
						});
						if (url && navigator.clipboard) {
							navigator.clipboard.writeText(url).catch(() => {});
						}
						frm.reload_doc();
					},
				});
			}, __("Actions"));

			frm.add_custom_button(__("Save as Template"), () => {
				frappe.prompt(
					[
						{
							fieldname: "template_name",
							fieldtype: "Data",
							label: __("Template Name"),
							reqd: 1,
						},
						{
							fieldname: "service_name",
							fieldtype: "Data",
							label: __("Service"),
						},
						{
							fieldname: "category",
							fieldtype: "Select",
							label: __("Category"),
							options: "General\nBIS / CRS\nTEC\nWPC\nTesting\nRenewal\nCustom",
							default: "Custom",
						},
					],
					(v) => {
						frappe.call({
							method: "instacertify.documents.api.save_document_request_as_template",
							args: {
								document_request: frm.doc.name,
								template_name: v.template_name,
								service_name: v.service_name,
								category: v.category,
							},
							freeze: true,
							callback(r) {
								const t = r.message && r.message.template;
								frappe.show_alert({
									message: __("Saved to Document Collection Library"),
									indicator: "green",
								});
								if (t) {
									frappe.set_route("Form", "IC Document Checklist Template", t);
								}
							},
						});
					},
					__("Save collection sheet as template"),
					__("Save")
				);
			}, __("Actions"));

			frm.add_custom_button(__("Push to Customer Data Sheet"), () => {
				if (!frm.doc.customer) {
					frappe.msgprint(__("Map this sheet to a Customer first."));
					return;
				}
				frappe.call({
					method: "instacertify.documents.api.push_document_request_to_customer",
					args: { document_request: frm.doc.name },
					freeze: true,
					callback() {
						frappe.show_alert({
							message: __("Collected data mapped to Customer Data Sheet"),
							indicator: "green",
						});
						frappe.set_route("Form", "Customer", frm.doc.customer);
					},
				});
			}, __("Actions"));

			frm.add_custom_button(__("Open Customer"), () => {
				if (!frm.doc.customer) {
					frappe.msgprint(__("No customer linked."));
					return;
				}
				frappe.set_route("Form", "Customer", frm.doc.customer);
			}, __("Links"));

			if (frm.doc.share_url || frm.doc.share_token) {
				frm.add_custom_button(__("Copy Share Link"), () => {
					const url =
						frm.doc.share_url ||
						(window.location.origin + "/ic-documents/" + frm.doc.share_token);
					if (navigator.clipboard) {
						navigator.clipboard.writeText(url).then(() => {
							frappe.show_alert({ message: __("Link copied"), indicator: "green" });
						});
					} else {
						frappe.msgprint(url);
					}
				}, __("Actions"));
			}

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
		const apply = () => {
			frappe.call({
				method: "instacertify.documents.api.apply_checklist_template",
				args: { document_request: frm.doc.name, template: frm.doc.checklist_template },
				freeze: true,
				freeze_message: __("Applying template…"),
				callback() {
					frm.reload_doc();
					frappe.show_alert({
						message: __("Template applied — upload rows and fill fields are ready"),
						indicator: "green",
					});
				},
			});
		};
		if (frm.is_new()) {
			frm.save().then(apply);
			return;
		}
		apply();
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
		frm._ic_actions_save_added = false;
		instacertify.ensure_form_save_button(frm);
		if (frm.is_new()) {
			frm.set_intro(
				__(
					"Laboratory Library — fill Laboratory Name, Contact Person, Designation, Phone, Accreditation Scope, and upload Scope Sheet / CSV. Add each accredited test with buying & selling prices in the scope table."
				),
				"blue"
			);
		} else {
			frm.set_intro(
				__(
					"All fields below stay editable: contact, designation, phone, accreditation scope, and the pricing table. Use Library → Upload / Import CSV anytime."
				),
				"blue"
			);
		}
		// Ensure master + attach + contact fields stay editable (never locked after upload)
		[
			"laboratory_name",
			"status",
			"location",
			"city",
			"state",
			"country",
			"address",
			"contact_person",
			"contact_designation",
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
			if (frm.fields_dict[f]) {
				frm.set_df_property(f, "read_only", 0);
				frm.set_df_property(f, "hidden", 0);
			}
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
				contact_designation: frm.doc.contact_designation,
				email: frm.doc.email,
				phone: frm.doc.phone,
				website: frm.doc.website,
				on_done(name) {
					if (name === frm.doc.name) frm.reload_doc();
					else frappe.set_route("Form", "IC Laboratory", name);
				},
			});
		}, __("Library"));
		// Primary, visible bulk upload (Excel/CSV) — not buried in a submenu
		frm.add_custom_button(__("Bulk Upload Scope (Excel/CSV)"), () => {
			if (frm.is_new()) {
				frappe.msgprint(__("Save the Laboratory first, then bulk-upload scope rows."));
				return;
			}
			instacertify.open_lab_scope_bulk_upload({
				laboratory: frm.doc.name,
				laboratory_name: frm.doc.laboratory_name,
				on_done() {
					frm.reload_doc();
				},
			});
		});
		if (!frm.is_new()) {
			frm.add_custom_button(__("Import Scope CSV / Excel"), () => {
				instacertify.open_lab_scope_csv_import(frm);
			}, __("Library"));
		}
		instacertify.render_lab_scope_bulk_bar(frm);
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

/** Visible Change Currency action for Quotation / Invoice / Testing finance screens. */
instacertify.add_change_currency_button = function (frm, opts) {
	opts = opts || {};
	const field = opts.fieldname || "currency";
	if (!frm.fields_dict[field] && !opts.force_button) return;
	if (frm.doc.docstatus === 1 && !opts.allow_submitted) return;
	const label = opts.label || __("Change Currency");
	frm.add_custom_button(label, () => instacertify.open_change_currency(frm, opts), __("Finance"));
};

instacertify.open_change_currency = function (frm, opts) {
	opts = opts || {};
	const field = opts.fieldname || "currency";
	const current = (frm.doc[field] || opts.default || "INR").toString();
	const quick = ["INR", "USD", "EUR", "AED", "GBP"];

	const d = new frappe.ui.Dialog({
		title: __("Change Currency"),
		fields: [
			{
				fieldtype: "HTML",
				options: `<p class="text-muted" style="margin:0 0 8px;">${__(
					"Current"
				)}: <b>${frappe.utils.escape_html(current)}</b>. ${__(
					"Pick INR / USD or any currency. Amounts stay the same numbers — only the currency label changes (edit rates if needed)."
				)}</p>`,
			},
			{
				fieldname: "quick",
				fieldtype: "Select",
				label: __("Quick pick"),
				options: "\n" + quick.join("\n"),
				default: quick.includes(current) ? current : "",
			},
			{
				fieldname: "currency",
				fieldtype: "Link",
				options: "Currency",
				label: __("Currency"),
				reqd: 1,
				default: current,
			},
		],
		primary_action_label: __("Apply"),
		primary_action(values) {
			const cur = (values.currency || values.quick || "").trim();
			if (!cur) {
				frappe.msgprint(__("Select a currency"));
				return;
			}
			d.hide();
			instacertify.apply_manual_currency(frm, cur, { fieldname: field });
		},
	});
	d.fields_dict.quick.$input.on("change", function () {
		const v = d.get_value("quick");
		if (v) d.set_value("currency", v);
	});
	d.show();
};

instacertify.apply_manual_currency = function (frm, currency, opts) {
	opts = opts || {};
	const field = opts.fieldname || "currency";
	if (!currency) return;
	const done = () => {
		frappe.show_alert({
			message: __("Currency set to {0}", [currency]),
			indicator: "green",
		});
		if (typeof opts.on_done === "function") opts.on_done(currency);
	};
	const set_manual = () => {
		if (frm.fields_dict.ic_currency_manual && !cint(frm.doc.ic_currency_manual)) {
			return frm.set_value("ic_currency_manual", 1);
		}
		return Promise.resolve();
	};
	instacertify._auto_setting_currency = true;
	Promise.resolve()
		.then(() => set_manual())
		.then(() => frm.set_value(field, currency))
		.then(() => {
			instacertify._auto_setting_currency = false;
			// Refresh ERPNext conversion / totals when present
			if (field === "currency" && frm.fields_dict.conversion_rate) {
				try {
					frm.trigger("currency");
				} catch (e) {
					/* ignore */
				}
			}
			done();
		})
		.catch(() => {
			instacertify._auto_setting_currency = false;
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
		instacertify.add_change_currency_button(frm, { fieldname: "currency" });
		if (frm.is_new()) {
			const wanted = cint(frm.doc.is_return) ? "INV-RET-.#####" : "INV-.#####";
			if (!frm.doc.naming_series || String(frm.doc.naming_series).indexOf("SINV") >= 0) {
				frm.set_value("naming_series", wanted);
			}
		}
		frm.set_intro(
			__("Consulting billing: sell services to customers as non-stock items — warehouse is not required. Series: INV-00001 … Use Finance → Change Currency anytime."),
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
		instacertify.add_change_currency_button(frm, { fieldname: "currency" });
		frm.set_intro(
			__(
				"Buy lab/vendor services or organisational purchases as non-stock. Link Laboratory / Testing Request when buying lab work. Use Asset for company equipment. Finance → Change Currency anytime."
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
		instacertify.enable_full_width_desk();
		if (frm.page && frm.page.wrapper) {
			frm.page.wrapper.addClass("ic-lead-form-page");
		}
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
			if (frm.doc.customer) {
				frm.add_custom_button(__("Testing & Samples"), () => {
					frappe.route_options = { customer: frm.doc.customer };
					frappe.set_route("testing-samples");
				}, __("Create"));
				frm.add_custom_button(__("Open Customer"), () => {
					frappe.set_route("Form", "Customer", frm.doc.customer);
				}, __("View"));
				frm.add_custom_button(__("Customer Testing / Samples"), () => {
					frappe.route_options = { customer: frm.doc.customer };
					frappe.set_route("testing-samples");
				}, __("View"));
			}
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
	add_fields: ["status", "location", "contact_person", "contact_designation", "phone"],
	onload(listview) {
		listview.page.add_inner_button(__("Bulk Upload Scope (Excel/CSV)"), () => {
			instacertify.open_lab_scope_bulk_upload({
				on_done() {
					listview.refresh();
				},
			});
		});
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
	get_indicator(doc) {
		if (doc.status === "Active") return [__("Active"), "green", "status,=,Active"];
		return [__("Inactive"), "gray", "status,=,Inactive"];
	},
	formatters: {
		contact_person(val, df, doc) {
			if (!val) return "";
			const desig = doc.contact_designation ? ` · ${frappe.utils.escape_html(doc.contact_designation)}` : "";
			return `${frappe.utils.escape_html(val)}${desig}`;
		},
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
	add_fields: ["sample_location", "status", "tracking_number", "customer", "testing_request"],
	get_indicator(doc) {
		const loc = doc.sample_location || doc.status || "";
		const colors = {
			"With Customer": "blue",
			"In Transit to Office": "orange",
			"At Instacertify Office": "green",
			"In Transit to Lab": "orange",
			"At Laboratory": "purple",
			"At Instacertify Warehouse": "teal",
			"At Instacertify Storage": "teal",
			"In Transit to Client": "orange",
			"Returned to Client": "blue",
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
			"At Instacertify Warehouse",
			"In Transit to Client",
			"Returned to Client",
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
		? `<img src="${frappe.utils.escape_html(fileUrl)}" alt="50x25mm sticker" style="height:72px;image-rendering:pixelated;border:1px solid #ddd;background:#fff;"/>`
		: "";
	const qrImg = qr
		? `<img src="${frappe.utils.escape_html(qr)}" alt="QR" style="height:64px;width:64px;image-rendering:pixelated;border:1px solid #ddd;"/>`
		: "";
	frm.fields_dict.sticker_preview.$wrapper.html(`
		<div class="ic-sample-sticker-preview" style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;padding:8px 0;">
			<div style="display:flex;align-items:center;gap:10px;padding:8px 10px;border:1px dashed #90a4ae;border-radius:4px;background:#fff;min-width:220px;">
				${qrImg}
				<div style="font-family:ui-monospace,monospace;font-weight:700;font-size:13px;line-height:1.15;">
					<div style="font-size:10px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:#607d8b;">Sample</div>
					${frappe.utils.escape_html(trk)}
					<div style="margin-top:6px;font-family:system-ui,sans-serif;font-size:11px;font-weight:500;color:#333;line-height:1.25;">
						${__("For more information visit")}<br>
						<b>www.instacertify.com</b>
					</div>
				</div>
			</div>
			${stickerImg}
			<div class="text-muted" style="font-size:12px;max-width:300px;">
				${__("50×25 mm sticker: QR + sample tracking number + www.instacertify.com. Use Label → Print 50×25 mm Sticker or Download PNG.")}
			</div>
		</div>
	`);
};

instacertify.download_png = function (src, filename) {
	if (!src) {
		frappe.msgprint({
			title: __("Download PNG"),
			message: __("No PNG available yet. Regenerate the sample sticker first."),
			indicator: "orange",
		});
		return Promise.resolve(false);
	}
	const fname = filename || "sample-qr.png";
	const trigger_blob = (blob) => {
		const url = URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = url;
		a.download = fname;
		a.rel = "noopener";
		document.body.appendChild(a);
		a.click();
		a.remove();
		setTimeout(() => URL.revokeObjectURL(url), 2500);
		return true;
	};
	const data_uri_to_blob = (dataUri) => {
		const parts = String(dataUri).split(",");
		const mime = (parts[0].match(/:(.*?);/) || [])[1] || "image/png";
		const bin = atob(parts[1] || "");
		const arr = new Uint8Array(bin.length);
		for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
		return new Blob([arr], { type: mime });
	};

	if (String(src).startsWith("data:")) {
		try {
			return Promise.resolve(trigger_blob(data_uri_to_blob(src)));
		} catch (e) {
			frappe.msgprint({
				title: __("Download PNG"),
				message: __("Could not prepare PNG download."),
				indicator: "orange",
			});
			return Promise.resolve(false);
		}
	}

	const url = String(src).startsWith("http") ? src : frappe.urllib.get_full_url(src);
	return fetch(url, { credentials: "same-origin" })
		.then((r) => {
			if (!r.ok) throw new Error("fetch failed");
			return r.blob();
		})
		.then((blob) => trigger_blob(blob))
		.catch(() => {
			// Last resort: open file URL
			window.open(url, "_blank");
			return false;
		});
};

/** Download 50×25 sample sticker PNG — prefers in-memory sticker, else regenerates via API. */
instacertify.download_sample_sticker_png = function (lab) {
	const sample = (lab && lab.name) || "";
	const trk = (lab && (lab.tracking_number || lab.name)) || "sample-qr";
	const fname = `${trk}.png`;
	const local =
		(lab && (lab.sticker_data_uri || lab.sticker_url || lab.qr_data_uri || lab.qr_code)) || "";

	const finish = (src) => {
		frappe.show_alert({ message: __("Downloading {0}", [fname]), indicator: "blue" });
		return instacertify.download_png(src, fname);
	};

	if (lab && lab.sticker_data_uri) {
		return finish(lab.sticker_data_uri);
	}
	if (!sample) {
		return finish(local);
	}
	return new Promise((resolve) => {
		frappe.call({
			method: "instacertify.testing.events.download_sample_sticker_50x25",
			args: { sample },
			freeze: true,
			freeze_message: __("Preparing PNG…"),
			callback(r) {
				const m = r.message || {};
				const src = m.file_url || local;
				resolve(finish(src));
			},
			error() {
				resolve(finish(local));
			},
		});
	});
};

instacertify.print_sample_qr_labels = function (labels) {
	if (!labels || !labels.length) {
		frappe.msgprint({
			title: __("Print QR"),
			message: __("No sample labels to print."),
			indicator: "orange",
		});
		return;
	}
	const sheets = labels
		.map((lab) => {
			const sticker = lab.sticker_data_uri || lab.sticker_url || "";
			const qr = lab.qr_data_uri || lab.qr_code || "";
			const trk = lab.tracking_number || lab.name || "";
			// Prefer full sticker image when available
			if (sticker) {
				return `<div class="sheet">
					<img class="full" src="${sticker.replace(/"/g, "&quot;")}" alt="50x25 ${frappe.utils.escape_html(trk)}"/>
				</div>`;
			}
			return `<div class="sheet">
				<div class="sticker">
					${qr ? `<img class="qr" src="${qr.replace(/"/g, "&quot;")}" alt="QR"/>` : ""}
					<div class="meta">
						<div class="lbl">SAMPLE</div>
						<div class="trk">${frappe.utils.escape_html(trk)}</div>
						<div class="info">For more information visit<br><b>www.instacertify.com</b></div>
					</div>
				</div>
			</div>`;
		})
		.join("");

	const html = `<!doctype html><html><head><title>Sample QR Labels</title>
		<style>
			@page { size: 50mm 25mm; margin: 0; }
			html, body { margin: 0; padding: 0; background: #fff; }
			.sheet { page-break-after: always; width: 50mm; height: 25mm; }
			.sheet:last-child { page-break-after: auto; }
			.sheet img.full { width: 50mm; height: 25mm; object-fit: contain; display: block; }
			.sticker {
				box-sizing: border-box; width: 50mm; height: 25mm;
				padding: 1.2mm 1.4mm; display: flex; align-items: center; gap: 1.6mm;
				font-family: Arial, Helvetica, sans-serif; color: #000;
			}
			.sticker img.qr { width: 18mm; height: 18mm; image-rendering: pixelated; }
			.sticker .meta { flex: 1; min-width: 0; }
			.sticker .lbl { font-size: 2.1mm; font-weight: 700; letter-spacing: .06em; color: #333; }
			.sticker .trk { font-family: monospace; font-size: 3.1mm; font-weight: 700; word-break: break-all; margin: 0.6mm 0; }
			.sticker .info { font-size: 1.85mm; line-height: 1.25; color: #222; }
			@media screen {
				body { padding: 16px; background: #eef2f5; }
				.sheet {
					page-break-after: auto; margin: 0 auto 12px; background: #fff;
					box-shadow: 0 2px 8px rgba(0,0,0,.12); border: 1px solid #cfd8dc;
				}
			}
		</style></head><body>${sheets}</body></html>`;

	// Prefer same-window iframe print (avoids popup blockers)
	let iframe = document.getElementById("ic-qr-print-frame");
	if (!iframe) {
		iframe = document.createElement("iframe");
		iframe.id = "ic-qr-print-frame";
		iframe.setAttribute("title", "Print QR");
		iframe.style.cssText =
			"position:fixed;right:0;bottom:0;width:0;height:0;border:0;opacity:0;pointer-events:none;";
		document.body.appendChild(iframe);
	}
	const idoc = iframe.contentDocument || iframe.contentWindow.document;
	idoc.open();
	idoc.write(html);
	idoc.close();
	const do_print = () => {
		try {
			iframe.contentWindow.focus();
			iframe.contentWindow.print();
		} catch (e) {
			const w = window.open("", "_blank");
			if (!w) {
				frappe.msgprint(__("Please allow pop-ups to print sample QR labels."));
				return;
			}
			w.document.write(html);
			w.document.close();
			setTimeout(() => w.print(), 250);
		}
	};
	// Wait for images in iframe to load
	const imgs = idoc.images || [];
	if (!imgs.length) {
		setTimeout(do_print, 200);
		return;
	}
	let pending = imgs.length;
	const done = () => {
		pending -= 1;
		if (pending <= 0) setTimeout(do_print, 100);
	};
	Array.from(imgs).forEach((img) => {
		if (img.complete) done();
		else {
			img.onload = done;
			img.onerror = done;
		}
	});
	setTimeout(do_print, 2500); // safety
};

instacertify.show_testing_request_sample_qr_dialog = function (payload) {
	const labels = (payload && payload.labels) || [];
	if (!labels.length) {
		frappe.msgprint({
			title: __("No sample QR"),
			message: __(
				"No sample tracking numbers were found for this Testing Request. Create samples first, then click QR again."
			),
			indicator: "orange",
		});
		return;
	}
	const by_name = {};
	labels.forEach((lab) => {
		if (lab && lab.name) by_name[lab.name] = lab;
	});

	const cards = labels
		.map((lab) => {
			const trk = lab.tracking_number || lab.name || "";
			const sticker = lab.sticker_data_uri || lab.sticker_url || "";
			const qr = lab.qr_data_uri || lab.qr_code || "";
			const main_img = sticker || qr;
			const sticker_block = main_img
				? `<img class="ic-ts-qr-sticker-50" src="${main_img.replace(/"/g, "&quot;")}" alt="50×25 mm ${frappe.utils.escape_html(
						trk
				  )}" onerror="this.onerror=null;this.style.display='none';"/>`
				: `<div class="ic-ts-qr-sticker-50 ic-ts-qr-missing">${__(
						"QR image missing — regenerate from Samples"
				  )}</div>`;
			return `<div class="ic-ts-qr-card" data-sample="${frappe.utils.escape_html(lab.name)}">
				<div class="ic-ts-qr-size-tag">${__("50 × 25 mm · unique sample QR")}</div>
				${sticker_block}
				${
					qr && sticker
						? `<div class="ic-ts-qr-only"><img src="${qr.replace(/"/g, "&quot;")}" alt="QR ${frappe.utils.escape_html(
								trk
						  )}"/></div>`
						: ""
				}
				<div class="ic-ts-qr-code-line">
					<span>${__("Sample code")}</span>
					<b>${frappe.utils.escape_html(trk)}</b>
				</div>
				<div class="ic-ts-qr-actions">
					<button type="button" class="btn btn-xs btn-primary ic-ts-print-one" data-sample="${frappe.utils.escape_html(
						lab.name
					)}">${__("Print QR")}</button>
					<button type="button" class="btn btn-xs btn-default ic-ts-dl-one" data-sample="${frappe.utils.escape_html(
						lab.name
					)}">${__("Download PNG")}</button>
					<a class="btn btn-xs btn-default ic-ts-open-sample" href="/app/ic-sample-tracking/${encodeURIComponent(
						lab.name
					)}">${__("Open")}</a>
				</div>
			</div>`;
		})
		.join("");

	const d = new frappe.ui.Dialog({
		title: __("Sample QR — {0}", [(payload && payload.testing_request) || ""]),
		size: "large",
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "labels",
				options: `
					<div class="ic-ts-qr-dialog">
						<div class="ic-ts-qr-intro">
							${__("Each Testing Request QR opens unique 50×25 mm labels — sample code +")}
							<b>www.instacertify.com</b>.
							${payload.test_name ? ` · ${frappe.utils.escape_html(payload.test_name)}` : ""}
						</div>
						<div class="ic-ts-qr-grid">${cards}</div>
					</div>
				`,
			},
		],
		primary_action_label: __("Print QR"),
		primary_action() {
			instacertify.print_sample_qr_labels(labels);
		},
		secondary_action_label: __("Close"),
		secondary_action() {
			d.hide();
		},
	});

	const bind = () => {
		d.$wrapper.off("click.icQrPrint").on("click.icQrPrint", ".ic-ts-print-one", function (e) {
			e.preventDefault();
			e.stopPropagation();
			const name = $(this).attr("data-sample");
			const lab = by_name[name] || labels.find((x) => x.name === name);
			if (lab) instacertify.print_sample_qr_labels([lab]);
			else frappe.msgprint(__("Sample label not found."));
		});
		d.$wrapper.off("click.icQrDl").on("click.icQrDl", ".ic-ts-dl-one", function (e) {
			e.preventDefault();
			e.stopPropagation();
			const name = $(this).attr("data-sample");
			const lab = by_name[name] || labels.find((x) => x.name === name) || { name };
			instacertify.download_sample_sticker_png(lab);
		});
	};

	d.show();
	bind();
	// Re-bind after dialog paints HTML field
	setTimeout(bind, 50);
};

frappe.ui.form.on("IC Sample Tracking", {
	refresh(frm) {
		frm._ic_actions_save_added = false;
		instacertify.ensure_form_save_button(frm);
	},
	status(frm) {
		const map = {
			"Sample Awaited": "With Customer",
			"Sample Received": "At Instacertify Office",
			"In Transit to Office": "In Transit to Office",
			"At Instacertify Office": "At Instacertify Office",
			"In Transit to Lab": "In Transit to Lab",
			"At Laboratory": "At Laboratory",
			"Sample Dispatched to Laboratory": "In Transit to Lab",
			"Testing in Progress": "At Laboratory",
			"At Instacertify Warehouse": "At Instacertify Warehouse",
			"At Instacertify Storage": "At Instacertify Warehouse",
			"In Transit to Client": "In Transit to Client",
			"Dispatched to Client": "In Transit to Client",
			"Returned to Client": "Returned to Client",
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
			"At Instacertify Warehouse": "At Instacertify Warehouse",
			"At Instacertify Storage": "At Instacertify Warehouse",
			"In Transit to Client": "In Transit to Client",
			"Returned to Client": "Returned to Client",
			Discarded: "Discarded",
		};
		if (map[frm.doc.sample_location] && frm.doc.status !== map[frm.doc.sample_location]) {
			frm.set_value("status", map[frm.doc.sample_location]);
		}
	},
	refresh(frm) {
		if (!frm.is_new()) {
			instacertify.render_sample_sticker_preview(frm);
			if (frm.doc.testing_request) {
				frm.add_custom_button(__("Edit Price"), () => {
					instacertify.edit_testing_request_prices(frm.doc.testing_request, {
						on_save() {
							frappe.show_alert({
								message: __("Testing Request prices updated"),
								indicator: "green",
							});
						},
					});
				}, __("Actions"));
			}
			frm.add_custom_button(__("Print 50×25 mm Sticker"), () => {
				const print_one = () => {
					frappe.call({
						method: "instacertify.testing.events.download_sample_sticker_50x25",
						args: { sample: frm.doc.name },
						freeze: true,
						callback(rr) {
							const m = rr.message || {};
							instacertify.print_sample_qr_labels([
								{
									name: frm.doc.name,
									tracking_number: frm.doc.tracking_number,
									sticker_url: m.file_url,
									sticker_data_uri: "",
									qr_code: frm.doc.qr_code,
								},
							]);
						},
					});
				};
				if (!frm.doc.testing_request) {
					print_one();
					return;
				}
				frappe.call({
					method: "instacertify.testing.events.get_testing_request_sample_labels",
					args: { testing_request: frm.doc.testing_request },
					freeze: true,
					callback(r) {
						const labels = ((r.message || {}).labels || []).filter(
							(x) => x.name === frm.doc.name
						);
						if (labels.length) {
							instacertify.print_sample_qr_labels(labels);
						} else {
							print_one();
						}
					},
				});
			}, __("Label"));
			frm.add_custom_button(__("Download 50×25 mm PNG"), () => {
				instacertify.download_sample_sticker_png({
					name: frm.doc.name,
					tracking_number: frm.doc.tracking_number,
					qr_code: frm.doc.qr_code,
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
			if (frm.doc.testing_request) {
				frm.add_custom_button(__("Open Testing Request"), () => {
					frappe.set_route("Form", "IC Testing Request", frm.doc.testing_request);
				}, __("Links"));
			}
			if (frm.doc.laboratory) {
				frm.add_custom_button(__("Open Laboratory"), () => {
					frappe.set_route("Form", "IC Laboratory", frm.doc.laboratory);
				}, __("Links"));
			}
		}
		const locs = [
			"In Transit to Office",
			"At Instacertify Office",
			"In Transit to Lab",
			"At Laboratory",
			"At Instacertify Warehouse",
			"In Transit to Client",
			"Returned to Client",
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
			) ||
			frm.doc.sample_location === "At Laboratory"
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

// --- Project Progress Tracker (saved editable log) ---
instacertify.PROJECT_STAGES = [
	"Project Initiated",
	"Customer Documents Pending",
	"Documents Under Review",
	"Application Submitted",
	"Sample Awaited",
	"Sample Received",
	"Sample Dispatched to Laboratory",
	"Testing in Progress",
	"Report Awaited",
	"Report Available",
	"Certification in Progress",
	"Certificate Available",
	"Delivered to Customer",
	"Project Completed",
];

instacertify.render_project_progress_tracker = function (frm) {
	if (!frm.fields_dict.ic_progress_html) return;

	const stages = instacertify.PROJECT_STAGES;
	const current = frm.doc.ic_project_stage;
	const idx = stages.indexOf(current);
	let stages_html = '<div class="ic-stage-tracker">';
	stages.forEach((s, i) => {
		let cls = "stage";
		if (i < idx) cls += " done";
		if (i === idx) cls += " active";
		stages_html += `<span class="${cls}">${frappe.utils.escape_html(s)}</span>`;
	});
	stages_html += "</div>";
	stages_html += `<div class="ic-progress" style="margin-top:12px;"><span style="width:${
		frm.doc.ic_progress_percentage || 0
	}%"></span></div>`;
	stages_html += `<div class="text-muted" style="font-size:12px;margin-top:4px;">${__(
		"Progress"
	)}: <b>${frappe.utils.escape_html(String(frm.doc.ic_progress_percentage || 0))}%</b>`;
	if (frm.doc.ic_pending_action) {
		stages_html += ` · ${__("Pending")}: ${frappe.utils.escape_html(frm.doc.ic_pending_action)}`;
	}
	stages_html += "</div>";

	const log_shell = frm.is_new()
		? `<div class="ic-progress-log"><div class="text-muted">${__(
				"Save the project to start the Progress Log."
		  )}</div></div>`
		: `<div class="ic-progress-log" id="ic-progress-log-${frappe.utils.escape_html(frm.doc.name)}">
			<div class="ic-progress-log-head">
				<div>
					<strong>${__("Progress Log")}</strong>
					<span class="text-muted"> · ${__("Saved history — add or edit entries anytime")}</span>
				</div>
				<button type="button" class="btn btn-xs btn-primary ic-progress-add">${__("Add entry")}</button>
			</div>
			<div class="ic-progress-log-body"><div class="text-muted">${__("Loading…")}</div></div>
		</div>`;

	frm.set_df_property("ic_progress_html", "options", stages_html + log_shell);

	if (frm.is_new()) return;

	const $host = frm.fields_dict.ic_progress_html.$wrapper;
	$host.find(".ic-progress-add").off("click").on("click", () => {
		instacertify.open_progress_log_dialog(frm);
	});
	instacertify.load_project_progress_log(frm);
};

instacertify.load_project_progress_log = function (frm) {
	const $body = $(`#ic-progress-log-${frm.doc.name} .ic-progress-log-body`);
	if (!$body.length) return;
	frappe.call({
		method: "instacertify.project.progress.get_progress_log",
		args: { project: frm.doc.name, limit: 80 },
		callback(r) {
			const entries = (r.message && r.message.entries) || [];
			if (!entries.length) {
				$body.html(
					`<div class="ic-progress-log-empty text-muted">${__(
						"No progress log yet. Click Add entry to record stage notes, blockers, or milestones."
					)}</div>`
				);
				return;
			}
			$body.html(
				entries
					.map((e) => {
						const pct =
							e.progress_percentage || e.progress_percentage === 0
								? `${frappe.utils.escape_html(String(e.progress_percentage))}%`
								: "";
						const stage = e.project_stage
							? `<span class="ic-progress-pill">${frappe.utils.escape_html(e.project_stage)}</span>`
							: "";
						const when = e.update_date
							? frappe.datetime.str_to_user(e.update_date)
							: "";
						const plain = frappe.utils.escape_html((e.plain || "").slice(0, 280));
						const pending = e.pending_action
							? `<div class="ic-progress-pending">${__("Pending")}: ${frappe.utils.escape_html(
									e.pending_action
							  )}</div>`
							: "";
						const attach = e.attachment
							? ` <a href="${frappe.utils.escape_html(
									e.attachment
							  )}" target="_blank" rel="noopener">${__("Attachment")}</a>`
							: "";
						return `<div class="ic-progress-entry" data-name="${frappe.utils.escape_html(e.name)}">
							<div class="ic-progress-entry-top">
								<div class="ic-progress-entry-title">${frappe.utils.escape_html(e.subject || e.name)}</div>
								<div class="ic-progress-entry-actions">
									<button type="button" class="btn btn-xs btn-default ic-progress-edit">${__("Edit")}</button>
									<button type="button" class="btn btn-xs btn-default ic-progress-open">${__("Open")}</button>
								</div>
							</div>
							<div class="ic-progress-entry-meta">
								${frappe.utils.escape_html(when)}
								${e.updated_by_name ? ` · ${frappe.utils.escape_html(e.updated_by_name)}` : ""}
								${pct ? ` · ${pct}` : ""}
								${stage}
							</div>
							${plain ? `<div class="ic-progress-entry-body">${plain}${attach}</div>` : attach ? `<div>${attach}</div>` : ""}
							${pending}
						</div>`;
					})
					.join("")
			);
			$body.find(".ic-progress-edit").on("click", function () {
				const name = $(this).closest(".ic-progress-entry").data("name");
				const entry = entries.find((x) => x.name === name);
				instacertify.open_progress_log_dialog(frm, entry);
			});
			$body.find(".ic-progress-open").on("click", function () {
				const name = $(this).closest(".ic-progress-entry").data("name");
				frappe.set_route("Form", "IC Project Update", name);
			});
		},
	});
};

instacertify.open_progress_log_dialog = function (frm, entry) {
	if (frm.is_new()) {
		frappe.msgprint(__("Save the project first."));
		return;
	}
	entry = entry || {};
	const is_edit = !!entry.name;
	const d = new frappe.ui.Dialog({
		title: is_edit ? __("Edit Progress Log Entry") : __("Add Progress Log Entry"),
		size: "large",
		fields: [
			{
				fieldname: "subject",
				fieldtype: "Data",
				label: __("Subject"),
				reqd: 1,
				default: entry.subject || "",
			},
			{
				fieldname: "update_date",
				fieldtype: "Datetime",
				label: __("Update Date"),
				default: entry.update_date || frappe.datetime.now_datetime(),
			},
			{ fieldtype: "Column Break" },
			{
				fieldname: "project_stage",
				fieldtype: "Select",
				label: __("Project Stage"),
				options: ["", ...instacertify.PROJECT_STAGES].join("\n"),
				default: entry.project_stage || frm.doc.ic_project_stage || "",
			},
			{
				fieldname: "progress_percentage",
				fieldtype: "Percent",
				label: __("Progress %"),
				default:
					entry.progress_percentage != null && entry.progress_percentage !== ""
						? entry.progress_percentage
						: frm.doc.ic_progress_percentage || 0,
			},
			{
				fieldname: "pending_action",
				fieldtype: "Data",
				label: __("Pending Action"),
				default: entry.pending_action || frm.doc.ic_pending_action || "",
			},
			{ fieldtype: "Section Break" },
			{
				fieldname: "remarks",
				fieldtype: "Text Editor",
				label: __("Notes / Narration"),
				default: entry.remarks || "",
			},
			{
				fieldname: "attachment",
				fieldtype: "Attach",
				label: __("Attachment"),
				default: entry.attachment || "",
			},
			{
				fieldname: "apply_to_project",
				fieldtype: "Check",
				label: __("Apply stage / progress / pending action to Project"),
				default: 1,
			},
		],
		primary_action_label: __("Save to Progress Log"),
		primary_action(values) {
			frappe.call({
				method: "instacertify.project.progress.save_progress_entry",
				args: {
					project: frm.doc.name,
					name: entry.name || null,
					subject: values.subject,
					remarks: values.remarks,
					project_stage: values.project_stage,
					progress_percentage: values.progress_percentage,
					pending_action: values.pending_action,
					update_date: values.update_date,
					attachment: values.attachment,
					apply_to_project: values.apply_to_project ? 1 : 0,
				},
				freeze: true,
				freeze_message: __("Saving progress log…"),
				callback() {
					d.hide();
					frappe.show_alert({ message: __("Progress log saved"), indicator: "green" });
					frm.reload_doc();
				},
			});
		},
	});
	if (is_edit && frappe.model.can_delete("IC Project Update")) {
		d.set_secondary_action(__("Delete"), () => {
			frappe.confirm(__("Delete this progress log entry?"), () => {
				frappe.call({
					method: "instacertify.project.progress.delete_progress_entry",
					args: { name: entry.name },
					freeze: true,
					callback() {
						d.hide();
						frappe.show_alert({ message: __("Entry deleted"), indicator: "orange" });
						instacertify.load_project_progress_log(frm);
					},
				});
			});
		});
	}
	d.show();
};

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

frappe.listview_settings["IC Testing Request"] = {
	add_fields: ["library_buying_price", "suggested_selling_price", "price_currency"],
	onload(listview) {
		listview.page.add_actions_menu_item(__("Edit Price"), () => {
			const selected = listview.get_checked_items();
			if (!selected.length) {
				frappe.msgprint(__("Select one Testing Request first."));
				return;
			}
			const row = selected[0];
			instacertify.edit_testing_request_prices(row.name, {
				library_buying_price: row.library_buying_price,
				suggested_selling_price: row.suggested_selling_price,
				price_currency: row.price_currency || "INR",
				on_save() {
					listview.refresh();
				},
			});
		});
	},
	button: {
		show(doc) {
			return true;
		},
		get_label() {
			return __("Edit Price");
		},
		get_description(doc) {
			return __("Edit buying / selling / currency");
		},
		action(doc) {
			instacertify.edit_testing_request_prices(doc.name, {
				library_buying_price: doc.library_buying_price,
				suggested_selling_price: doc.suggested_selling_price,
				price_currency: doc.price_currency || "INR",
			});
		},
	},
};
