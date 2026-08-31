frappe.pages["document-collection-library"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Document Collection Library"),
		single_column: true,
	});

	frappe.breadcrumbs.add({
		label: __("Documents Collection Sheets"),
		route: "/app/ic-document-request",
	});

	page.set_title(__("Document Collection Library"));
	page.main.addClass("ic-doclib-page");

	const CATEGORIES = [
		{ key: "", label: __("All") },
		{ key: "General", label: __("General") },
		{ key: "BIS / CRS", label: __("BIS / CRS") },
		{ key: "TEC", label: __("TEC") },
		{ key: "WPC", label: __("WPC") },
		{ key: "Testing", label: __("Testing") },
		{ key: "Renewal", label: __("Renewal") },
		{ key: "Custom", label: __("Custom") },
	];

	page.main.html(`
		<div class="ic-doclib">
			<div class="ic-doclib-head">
				<div>
					<div class="ic-doclib-kicker">${__("Templates")}</div>
					<div class="ic-doclib-title">${__("Document Collection Sheet Library")}</div>
					<div class="ic-doclib-sub">${__(
						"Customise format fields (check/uncheck optional built-ins) and rows: Name, Remark, Mandatory, Collect As. Use a template to create a customer request with a sharable upload link."
					)}</div>
				</div>
				<div class="ic-doclib-tools">
					<input type="search" class="form-control" id="ic-doclib-search"
						placeholder="${__("Search templates…")}" />
					<button type="button" class="btn btn-default btn-sm" id="ic-doclib-sheets">${__("Open Sheets")}</button>
					<button type="button" class="btn btn-primary btn-sm" id="ic-doclib-new">${__("New Template")}</button>
					<button type="button" class="btn btn-primary btn-sm" id="ic-doclib-new-req">${__("New Request")}</button>
				</div>
			</div>
			<div class="ic-doclib-cats" id="ic-doclib-cats" role="tablist"></div>
			<div class="ic-doclib-panel">
				<div class="ic-doclib-panel-head">
					<div>
						<div class="ic-doclib-panel-title" id="ic-doclib-panel-title">${__("All templates")}</div>
						<div class="ic-doclib-panel-sub" id="ic-doclib-panel-sub"></div>
					</div>
					<label class="ic-doclib-active-only">
						<input type="checkbox" id="ic-doclib-active" checked />
						${__("Active only")}
					</label>
				</div>
				<div class="ic-doclib-grid" id="ic-doclib-grid" aria-live="polite"></div>
			</div>
		</div>
	`);

	const state = {
		category: "",
		search: "",
		active_only: 1,
		rows: [],
	};

	function render_cats() {
		const el = page.main.find("#ic-doclib-cats");
		el.empty();
		CATEGORIES.forEach((c) => {
			const btn = $(
				`<button type="button" class="ic-doclib-cat ${state.category === c.key ? "is-active" : ""}" data-cat="${frappe.utils.escape_html(c.key)}">${frappe.utils.escape_html(c.label)}</button>`
			);
			btn.on("click", () => {
				state.category = c.key;
				render_cats();
				load();
			});
			el.append(btn);
		});
	}

	function filtered() {
		const q = (state.search || "").toLowerCase().trim();
		return (state.rows || []).filter((r) => {
			if (state.category && (r.category || "General") !== state.category) return false;
			if (!q) return true;
			const hay = [r.display_name, r.template_name, r.service_name, r.category, r.notes]
				.concat((r.items || []).map((i) => i.document_name))
				.join(" ")
				.toLowerCase();
			return hay.includes(q);
		});
	}

	function render_grid() {
		const rows = filtered();
		page.main.find("#ic-doclib-panel-title").text(
			state.category ? state.category : __("All templates")
		);
		page.main
			.find("#ic-doclib-panel-sub")
			.text(__("{0} template(s)", [rows.length]));
		const grid = page.main.find("#ic-doclib-grid");
		grid.empty();
		if (!rows.length) {
			grid.html(
				`<div class="ic-doclib-empty">${__("No templates yet. Create one, or save an existing sheet as a template.")}</div>`
			);
			return;
		}
		rows.forEach((r) => {
			const shown = r.display_name || r.template_name || r.name;
			const preview = (r.items || [])
				.slice(0, 4)
				.map((i) => {
					const badge =
						i.entry_type === "Fill Field"
							? __("Fill")
							: __("Upload");
					return `<li><span class="ic-doclib-badge">${frappe.utils.escape_html(badge)}</span> ${frappe.utils.escape_html(i.document_name || "")}${i.is_mandatory ? " *" : ""}</li>`;
				})
				.join("");
			const more =
				(r.items || []).length > 4
					? `<div class="text-muted">${__("+{0} more", [(r.items || []).length - 4])}</div>`
					: "";
			const idHint =
				r.template_name && shown !== r.template_name
					? `<div class="text-muted" style="font-size:11px;">${__("ID")}: ${frappe.utils.escape_html(r.template_name)}</div>`
					: "";
			const card = $(`
				<article class="ic-doclib-card" data-name="${frappe.utils.escape_html(r.name)}">
					<div class="ic-doclib-card-top">
						<div>
							<div class="ic-doclib-card-cat">${frappe.utils.escape_html(r.category || "General")}</div>
							<div class="ic-doclib-card-title">${frappe.utils.escape_html(shown)}</div>
							${idHint}
							<div class="ic-doclib-card-meta">${frappe.utils.escape_html(r.service_name || "")}</div>
						</div>
						<div class="ic-doclib-card-counts">
							<span>${__("{0} upload", [r.upload_count || 0])}</span>
							<span>${__("{0} fill", [r.fill_count || 0])}</span>
						</div>
					</div>
					<ul class="ic-doclib-preview">${preview}</ul>
					${more}
					<div class="ic-doclib-card-actions">
						<button type="button" class="btn btn-default btn-sm" data-act="edit">${__("Edit")}</button>
						<button type="button" class="btn btn-default btn-sm" data-act="rename">${__("Rename")}</button>
						<button type="button" class="btn btn-primary btn-sm" data-act="use">${__("Use for Customer")}</button>
					</div>
				</article>
			`);
			card.find('[data-act="edit"]').on("click", () => {
				frappe.set_route("Form", "IC Document Checklist Template", r.name);
			});
			card.find('[data-act="rename"]').on("click", () => rename_template(r));
			card.find('[data-act="use"]').on("click", () => use_template(r));
			grid.append(card);
		});
	}

	function rename_template(row) {
		if (!row || !row.name) return;
		frappe.prompt(
			[
				{
					fieldname: "display_name",
					fieldtype: "Data",
					label: __("Display Name"),
					reqd: 1,
					default: row.display_name || row.template_name || "",
				},
			],
			(values) => {
				frappe.call({
					method: "instacertify.documents.api.rename_checklist_template_display_name",
					args: { template: row.name, display_name: values.display_name },
					freeze: true,
					callback() {
						frappe.show_alert({
							message: __("Display name updated (Template ID unchanged)"),
							indicator: "green",
						});
						load();
					},
				});
			},
			__("Rename Template"),
			__("Save")
		);
	}

	function use_template(row) {
		const shown = row.display_name || row.template_name || row.name;
		const d = new frappe.ui.Dialog({
			title: __("Create Document Collection Request"),
			fields: [
				{
					fieldtype: "HTML",
					options: `<p class="text-muted">${__("Template")}: <b>${frappe.utils.escape_html(shown)}</b>. ${__("Customer is mandatory. After create you get a sharable upload link.")}</p>`,
				},
				{
					fieldname: "customer",
					fieldtype: "Link",
					options: "Customer",
					label: __("Customer"),
					reqd: 1,
				},
				{
					fieldname: "title",
					fieldtype: "Data",
					label: __("Sheet Title"),
					default: __("Documents — {0}", [shown]),
				},
				{
					fieldname: "project",
					fieldtype: "Link",
					options: "Project",
					label: __("Project (optional)"),
					get_query() {
						const c = d.get_value("customer");
						return c ? { filters: { customer: c } } : {};
					},
				},
				{
					fieldname: "share",
					fieldtype: "Check",
					label: __("Generate customer share link now"),
					default: 1,
				},
			],
			primary_action_label: __("Create & Open"),
			primary_action(values) {
				if (!values.customer) {
					frappe.msgprint(__("Customer is mandatory"));
					return;
				}
				frappe.call({
					method: "instacertify.documents.api.create_document_request_for_customer",
					args: {
						customer: values.customer,
						title: values.title,
						template: row.name,
						project: values.project,
						share: values.share ? 1 : 0,
					},
					freeze: true,
					freeze_message: __("Creating collection sheet…"),
					callback(r) {
						d.hide();
						const m = r.message || {};
						const url = m.url;
						if (url) {
							frappe.msgprint({
								title: __("Customer share link"),
								indicator: "green",
								message: `<p>${__("Share this link so the customer can upload files and fill fields:")}</p>
									<p><a href="${frappe.utils.escape_html(url)}" target="_blank" rel="noopener">${frappe.utils.escape_html(url)}</a></p>
									<p class="text-muted">${__("Link copied to clipboard when supported.")}</p>`,
							});
							if (navigator.clipboard) {
								navigator.clipboard.writeText(url).catch(() => {});
							}
						}
						if (m.document_request) {
							frappe.set_route("Form", "IC Document Request", m.document_request);
						}
					},
				});
			},
		});
		d.show();
	}

	function new_request_dialog() {
		const d = new frappe.ui.Dialog({
			title: __("New Document Collection Request"),
			fields: [
				{
					fieldname: "customer",
					fieldtype: "Link",
					options: "Customer",
					label: __("Customer"),
					reqd: 1,
				},
				{
					fieldname: "template",
					fieldtype: "Link",
					options: "IC Document Checklist Template",
					label: __("Template"),
					get_query() {
						return { filters: { is_active: 1 } };
					},
				},
				{
					fieldname: "title",
					fieldtype: "Data",
					label: __("Sheet Title"),
				},
				{
					fieldname: "share",
					fieldtype: "Check",
					label: __("Generate customer share link now"),
					default: 1,
				},
			],
			primary_action_label: __("Create"),
			primary_action(values) {
				if (!values.customer) {
					frappe.msgprint(__("Customer is mandatory"));
					return;
				}
				frappe.call({
					method: "instacertify.documents.api.create_document_request_for_customer",
					args: {
						customer: values.customer,
						title: values.title,
						template: values.template,
						share: values.share ? 1 : 0,
					},
					freeze: true,
					callback(r) {
						d.hide();
						const m = r.message || {};
						if (m.url) {
							frappe.msgprint({
								title: __("Customer share link"),
								indicator: "green",
								message: `<p><a href="${frappe.utils.escape_html(m.url)}" target="_blank" rel="noopener">${frappe.utils.escape_html(m.url)}</a></p>`,
							});
							if (navigator.clipboard) {
								navigator.clipboard.writeText(m.url).catch(() => {});
							}
						}
						if (m.document_request) {
							frappe.set_route("Form", "IC Document Request", m.document_request);
						}
					},
				});
			},
		});
		d.show();
	}

	function load() {
		frappe.call({
			method: "instacertify.documents.api.get_document_collection_library",
			args: {
				active_only: state.active_only ? 1 : 0,
				category: state.category || null,
			},
			callback(r) {
				state.rows = r.message || [];
				render_grid();
			},
		});
	}

	page.main.find("#ic-doclib-search").on("input", function () {
		state.search = this.value || "";
		render_grid();
	});
	page.main.find("#ic-doclib-active").on("change", function () {
		state.active_only = this.checked ? 1 : 0;
		load();
	});
	page.main.find("#ic-doclib-new").on("click", () => {
		frappe.new_doc("IC Document Checklist Template");
	});
	page.main.find("#ic-doclib-sheets").on("click", () => {
		frappe.set_route("List", "IC Document Request");
	});
	page.main.find("#ic-doclib-new-req").on("click", () => new_request_dialog());

	render_cats();
	load();
};
