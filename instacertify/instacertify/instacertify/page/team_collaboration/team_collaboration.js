frappe.pages["team-collaboration"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Team Collaboration"),
		single_column: true,
	});

	frappe.breadcrumbs.add({
		label: __("Home"),
		route: "/app/home",
	});

	page.set_title(__("Team Collaboration"));
	page.main.addClass("ic-collab-page");

	const state = {
		project: frappe.route_options && frappe.route_options.project,
		rooms: [],
		poll: null,
	};

	page.main.html(`
		<div class="ic-collab-shell">
			<aside class="ic-collab-sidebar">
				<div class="ic-collab-side-head">
					<div>
						<div class="ic-collab-kicker">${__("Internal chat")}</div>
						<div class="ic-collab-side-title">${__("Projects")}</div>
					</div>
					<button class="btn btn-default btn-xs" id="ic-collab-refresh">${__("Refresh")}</button>
				</div>
				<div class="ic-collab-search">
					<input type="search" class="form-control" id="ic-collab-search"
						placeholder="${__("Search projects…")}" />
				</div>
				<div class="ic-collab-room-list" id="ic-collab-rooms"></div>
			</aside>
			<section class="ic-collab-main">
				<div class="ic-collab-main-head" id="ic-collab-head">
					<div>
						<div class="ic-collab-kicker">${__("Select a project")}</div>
						<div class="ic-collab-main-title" id="ic-collab-title">${__("Team chat")}</div>
						<div class="ic-collab-main-sub" id="ic-collab-sub">${__("Discuss delivery, documents, testing, and handovers with your teammates.")}</div>
					</div>
					<div class="ic-collab-head-actions" id="ic-collab-actions"></div>
				</div>
				<div class="ic-collab-log" id="ic-collab-log">
					<div class="ic-collab-empty">${__("Pick a project on the left to open its chat room.")}</div>
				</div>
				<div class="ic-collab-compose" id="ic-collab-compose" style="display:none;">
					<textarea class="form-control" id="ic-collab-input" rows="2"
						placeholder="${__("Write a message to the project team…")}"></textarea>
					<button class="btn btn-primary" id="ic-collab-send">${__("Send")}</button>
				</div>
			</section>
		</div>
	`);

	const $rooms = page.main.find("#ic-collab-rooms");
	const $log = page.main.find("#ic-collab-log");
	const $compose = page.main.find("#ic-collab-compose");
	const $input = page.main.find("#ic-collab-input");

	function esc(v) {
		return frappe.utils.escape_html(v == null ? "" : String(v));
	}

	function render_rooms(filter) {
		const q = (filter || "").toLowerCase().trim();
		let rows = state.rooms || [];
		if (q) {
			rows = rows.filter(
				(r) =>
					(r.project_name || "").toLowerCase().includes(q) ||
					(r.project || "").toLowerCase().includes(q) ||
					(r.customer || "").toLowerCase().includes(q)
			);
		}
		if (!rows.length) {
			$rooms.html(`<div class="ic-collab-empty small">${__("No projects found.")}</div>`);
			return;
		}
		$rooms.html(
			rows
				.map((r) => {
					const active = state.project === r.project ? "active" : "";
					const preview = r.last_message
						? `${esc(r.last_sender)}: ${esc(r.last_message)}`
						: __("No messages yet");
					return `<button type="button" class="ic-collab-room ${active}" data-project="${esc(r.project)}">
						<div class="ic-collab-room-top">
							<span class="ic-collab-room-name">${esc(r.project_name)}</span>
							<span class="ic-collab-room-time">${esc(r.last_at_label || "")}</span>
						</div>
						<div class="ic-collab-room-meta">${esc(r.status || "")}${r.customer ? " · " + esc(r.customer) : ""}</div>
						<div class="ic-collab-room-preview">${preview}</div>
					</button>`;
				})
				.join("")
		);
	}

	function render_messages(payload) {
		const rows = (payload && payload.messages) || [];
		const meta = (payload && payload.project) || {};
		page.main.find("#ic-collab-title").text(meta.project_name || state.project || __("Team chat"));
		page.main.find("#ic-collab-sub").text(
			[meta.status, meta.customer, meta.name].filter(Boolean).join(" · ") ||
				__("Discuss this project with teammates")
		);
		page.main.find("#ic-collab-actions").html(
			state.project
				? `<a class="btn btn-default btn-sm" href="/app/project/${encodeURIComponent(state.project)}">${__("Open project")}</a>`
				: ""
		);
		$compose.show();
		if (!rows.length) {
			$log.html(`<div class="ic-collab-empty">${__("No messages yet — start the conversation.")}</div>`);
			return;
		}
		$log.html(
			rows
				.map((m) => {
					const mine = m.is_mine ? "mine" : "";
					const attach = m.attachment
						? ` <a href="${esc(m.attachment)}" target="_blank" rel="noopener">${__("Attachment")}</a>`
						: "";
					return `<div class="ic-chat-bubble ${mine}">
						<div class="ic-chat-meta">${esc(m.sender_name || m.sender || "")} · ${esc(m.time_label || "")}</div>
						<div class="ic-chat-body">${m.message || esc(m.plain || "")}${attach}</div>
					</div>`;
				})
				.join("")
		);
		$log.scrollTop($log[0].scrollHeight);
	}

	function load_rooms(cb) {
		frappe.call({
			method: "instacertify.collaboration.api.list_chat_rooms",
			args: { limit: 50 },
			callback(r) {
				state.rooms = (r.message && r.message.rooms) || [];
				render_rooms(page.main.find("#ic-collab-search").val());
				if (cb) cb();
			},
		});
	}

	function open_project(project) {
		if (!project) return;
		state.project = project;
		render_rooms(page.main.find("#ic-collab-search").val());
		frappe.call({
			method: "instacertify.collaboration.api.get_project_messages",
			args: { project, limit: 120 },
			callback(r) {
				render_messages(r.message || {});
			},
		});
	}

	function send_message() {
		const message = ($input.val() || "").trim();
		if (!message || !state.project) return;
		frappe.call({
			method: "instacertify.collaboration.api.post_project_message",
			args: { project: state.project, message },
			freeze: true,
			freeze_message: __("Sending…"),
			callback() {
				$input.val("");
				open_project(state.project);
				load_rooms();
			},
		});
	}

	$rooms.on("click", ".ic-collab-room", function () {
		open_project($(this).data("project"));
	});
	page.main.find("#ic-collab-send").on("click", send_message);
	$input.on("keydown", function (e) {
		if (e.key === "Enter" && !e.shiftKey) {
			e.preventDefault();
			send_message();
		}
	});
	page.main.find("#ic-collab-search").on("input", function () {
		render_rooms($(this).val());
	});
	page.main.find("#ic-collab-refresh").on("click", function () {
		load_rooms(() => {
			if (state.project) open_project(state.project);
		});
	});

	load_rooms(() => {
		if (state.project) {
			open_project(state.project);
		} else if (state.rooms.length) {
			const first_active = state.rooms.find((r) => r.has_activity) || state.rooms[0];
			if (first_active) open_project(first_active.project);
		}
	});

	// Light polling while page is open
	state.poll = setInterval(() => {
		if (!state.project || document.hidden) return;
		frappe.call({
			method: "instacertify.collaboration.api.get_project_messages",
			args: { project: state.project, limit: 120 },
			callback(r) {
				render_messages(r.message || {});
			},
		});
	}, 20000);

	$(wrapper).on("hide", () => {
		if (state.poll) clearInterval(state.poll);
	});
};

frappe.pages["team-collaboration"].on_page_show = function () {
	const project = frappe.route_options && frappe.route_options.project;
	if (project) {
		frappe.route_options = null;
		const $btn = $(`.ic-collab-room[data-project="${frappe.utils.escape_html(project)}"]`);
		if ($btn.length) $btn.trigger("click");
	}
};
