frappe.pages["project-board"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Project Board"),
		single_column: true,
	});

	frappe.breadcrumbs.add({
		label: __("Projects"),
		route: "/app/project",
	});

	page.set_title(__("Project Board"));
	page.main.addClass("ic-project-board-page");

	page.main.html(`
		<div class="ic-project-board">
			<div class="ic-project-board-head">
				<div>
					<div class="ic-project-board-kicker">${__("Projects")}</div>
					<div class="ic-project-board-title">${__("Tile board")}</div>
					<div class="ic-project-board-sub">${__("Browse active work as tiles — click any tile to open the project.")}</div>
				</div>
				<div class="ic-project-board-tools">
					<input type="search" class="form-control" id="ic-board-search" placeholder="${__("Search projects…")}" />
					<select class="form-control" id="ic-board-priority">
						<option value="">${__("All priorities")}</option>
						<option>Urgent</option>
						<option>High</option>
						<option>Medium</option>
						<option>Low</option>
					</select>
					<button class="btn btn-default btn-sm" id="ic-board-refresh">${__("Refresh")}</button>
					<a class="btn btn-primary btn-sm" href="/app/project/new">${__("New Project")}</a>
				</div>
			</div>
			<div class="ic-project-grid ic-project-grid-board" id="ic-project-board-grid"></div>
		</div>
	`);

	const $grid = page.main.find("#ic-project-board-grid");

	function load() {
		frappe.call({
			method: "instacertify.project.events.get_project_board",
			args: {
				limit: 48,
				search: page.main.find("#ic-board-search").val(),
				priority: page.main.find("#ic-board-priority").val(),
			},
			freeze: true,
			callback(r) {
				const rows = (r.message && r.message.projects) || [];
				if (!rows.length) {
					$grid.html(`<div class="ic-project-empty">${__("No projects match this filter.")}</div>`);
					return;
				}
				$grid.html(rows.map((p) => instacertify.project_tile_html(p)).join(""));
				$grid.find(".ic-project-tile").on("click", function () {
					frappe.set_route("Form", "Project", $(this).data("name"));
				});
			},
		});
	}

	page.main.find("#ic-board-refresh").on("click", load);
	page.main.find("#ic-board-priority").on("change", load);
	let timer = null;
	page.main.find("#ic-board-search").on("input", function () {
		clearTimeout(timer);
		timer = setTimeout(load, 280);
	});

	load();
};
