/* Instacertify desk experience layer.
   Presentation only: nothing here writes to a document, changes a price, a tax,
   a permission or a workflow. Every number shown is read live with the signed-in
   user's own permissions. */

frappe.provide("instacertify");
frappe.provide("instacertify.ux");

(function () {
	const ux = instacertify.ux;

	/* ------------------------------------------------------------------ */
	/* 1. One meaning per status colour                                    */
	/*    green = done, amber = waiting, red = overdue / lost,             */
	/*    blue = in progress, grey = draft / inactive.                     */
	/* ------------------------------------------------------------------ */
	ux.STATUS_TONE = {
		Draft: "gray",
		Cancelled: "gray",
		Closed: "gray",
		Expired: "gray",
		Disabled: "gray",
		Inactive: "gray",
		Lost: "red",
		Overdue: "red",
		Rejected: "red",
		Enabled: "green",
	};

	ux.patch_indicator = function () {
		if (!frappe.get_indicator || frappe.get_indicator.__ic) return;
		const original = frappe.get_indicator;
		const patched = function (doc, doctype) {
			const indicator = original.apply(this, arguments);
			try {
				if (!indicator || !Array.isArray(indicator)) return indicator;
				const filter = indicator[2] || "";
				let tone = null;
				if (filter === "docstatus,=,0" || filter === "docstatus,=,2") {
					tone = "gray";
				} else if (doc && doc.status && filter === "status,=," + doc.status) {
					tone = ux.STATUS_TONE[doc.status] || null;
				} else if (filter === "enabled,=,1" || filter === "disabled,=,0") {
					tone = "green";
				} else if (filter === "enabled,=,0" || filter === "disabled,=,1") {
					tone = "gray";
				}
				if (tone) indicator[1] = tone;
			} catch (e) {
				/* keep the standard colour */
			}
			return indicator;
		};
		patched.__ic = true;
		frappe.get_indicator = patched;
	};

	/* ------------------------------------------------------------------ */
	/* 2. Page header stays on one line                                    */
	/*    Buttons that do not fit beside the title move into "More".       */
	/*    The original buttons are only hidden, never moved, so every      */
	/*    action keeps working exactly as before.                          */
	/* ------------------------------------------------------------------ */
	const tidy_state = new WeakMap();

	function is_shown(el) {
		return !!(el && el.offsetParent !== null && el.getBoundingClientRect().width > 1);
	}

	function label_of(el) {
		const btn = el.matches("button, a") ? el : el.querySelector("button, a");
		const raw = (btn && btn.getAttribute("data-label")) || "";
		let text = "";
		try {
			text = raw ? decodeURIComponent(raw) : "";
		} catch (e) {
			text = raw;
		}
		if (!text) text = ((btn || el).textContent || "").trim().replace(/\s+/g, " ");
		return text;
	}

	function build_more(bar, folded) {
		const wrap = document.createElement("div");
		wrap.className = "ic-more-actions";
		wrap.innerHTML =
			`<button type="button" class="btn btn-default ic-more-btn" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">` +
			`<span>${__("More")}</span>${frappe.utils.icon("select", "xs")}</button>` +
			`<div role="menu" class="dropdown-menu dropdown-menu-right"></div>`;
		const menu = wrap.querySelector(".dropdown-menu");
		const add_item = (text, target, indent) => {
			const a = document.createElement("a");
			a.className = "dropdown-item" + (indent ? " ic-more-sub" : "");
			a.href = "#";
			a.setAttribute("role", "menuitem");
			a.textContent = text;
			a.addEventListener("click", (e) => {
				e.preventDefault();
				target.click();
			});
			menu.appendChild(a);
		};
		folded.forEach((el) => {
			if (el.classList.contains("inner-group-button") || el.querySelector(":scope > .dropdown-menu")) {
				const items = [...el.querySelectorAll(".dropdown-menu .dropdown-item, .dropdown-menu a")].filter(
					(a) => !a.classList.contains("hide") && (a.textContent || "").trim()
				);
				if (!items.length) return;
				const head = document.createElement("div");
				head.className = "dropdown-header ic-more-head";
				head.textContent = label_of(el);
				menu.appendChild(head);
				items.forEach((a) => add_item((a.textContent || "").trim().replace(/\s+/g, " "), a, true));
			} else {
				const btn = el.matches("button, a") ? el : el.querySelector("button, a");
				if (btn) add_item(label_of(el), btn, false);
			}
		});
		bar.appendChild(wrap);
		return wrap;
	}

	ux.tidy_header = function (head) {
		if (!head) return;
		const bar = head.querySelector(".page-actions .custom-actions");
		const content = head.querySelector(".page-head-content");
		if (!bar || !content) return;
		const state = tidy_state.get(head);
		if (state && state.busy) return;
		// rebuilding the menu while it is open would close it under the user's pointer
		if (bar.querySelector(":scope > .ic-more-actions.show, :scope > .ic-more-actions .dropdown-menu.show")) return;
		if (state) state.busy = true;
		try {
			bar.querySelectorAll(":scope > .ic-folded").forEach((el) => el.classList.remove("ic-folded"));
			const old = bar.querySelector(":scope > .ic-more-actions");
			if (old) old.remove();
			head.classList.add("ic-head-tidy");
			if (window.innerWidth < 768 || !is_shown(bar)) return;

			const items = [...bar.children].filter(
				(el) => is_shown(el) && !el.classList.contains("inner-page-message")
			);
			if (items.length < 2) return;

			const title = head.querySelector(".title-area");
			const standard = head.querySelector(".page-actions .standard-actions");
			const toggle = head.querySelector(".page-title .sidebar-toggle-btn");
			const total = content.clientWidth;
			// measure the title at its full width, not at the width it has been squeezed to
			head.classList.add("ic-head-measure");
			const title_natural = title ? title.getBoundingClientRect().width : 0;
			head.classList.remove("ic-head-measure");
			const title_need = Math.min(title_natural, Math.round(total * 0.45)) + 16;
			const fixed =
				(standard && is_shown(standard) ? standard.getBoundingClientRect().width : 0) +
				(toggle && is_shown(toggle) ? toggle.getBoundingClientRect().width + 12 : 0) +
				40;
			const available = total - title_need - fixed;
			const gap = 6;
			const widths = items.map((el) => el.getBoundingClientRect().width + gap);
			const sum = widths.reduce((a, b) => a + b, 0);
			if (sum <= available) return;

			const more_width = 84;
			let used = more_width;
			const folded = [];
			items.forEach((el, i) => {
				if (!folded.length && used + widths[i] <= available) {
					used += widths[i];
				} else {
					folded.push(el);
				}
			});
			if (!folded.length) return;
			folded.forEach((el) => el.classList.add("ic-folded"));
			build_more(bar, folded);
		} catch (e) {
			head.classList.remove("ic-head-tidy");
		} finally {
			if (state) {
				// let the observer drain the changes we just made before listening again
				Promise.resolve().then(() => {
					state.busy = false;
				});
			}
		}
	};

	ux.watch_headers = function () {
		document.querySelectorAll(".page-head").forEach((head) => {
			if (tidy_state.has(head)) return;
			const bar = head.querySelector(".page-actions .custom-actions");
			const content = head.querySelector(".page-head-content");
			if (!bar || !content) return;
			const state = { busy: false };
			tidy_state.set(head, state);
			const run = () => ux.tidy_header(head);
			new MutationObserver((changes) => {
				if (state.busy) return;
				// opening or closing our own menu is not a change to the buttons
				const own = changes.every((m) => m.target.closest && m.target.closest(".ic-more-actions"));
				if (!own) run();
			}).observe(bar, { childList: true, subtree: true, attributes: true, attributeFilter: ["class", "style"] });
			const title = head.querySelector(".title-area");
			if (title) {
				// the page name arrives after the buttons on a form, so the room has to be measured again
				new MutationObserver(() => {
					if (!state.busy) run();
				}).observe(title, { childList: true, subtree: true, characterData: true });
			}
			if (window.ResizeObserver) {
				new ResizeObserver(() => {
					if (!state.busy) run();
				}).observe(content);
			}
			run();
		});
	};

	/* ------------------------------------------------------------------ */
	/* 3. Status bar above a list (count and value per stage; click to     */
	/*    filter). Read-only: one small permission-checked count per stage.*/
	/* ------------------------------------------------------------------ */
	ux.STATUS_BARS = {
		Quotation: {
			amount: "base_grand_total",
			fields: ["docstatus", "status"],
			segments: [
				{ key: "draft", label: __("Draft"), hint: __("Not sent yet"), tone: "neutral", filters: [["docstatus", "=", 0]] },
				{
					key: "open",
					label: __("Awaiting reply"),
					hint: __("Sent, no decision yet"),
					tone: "info",
					filters: [["docstatus", "=", 1], ["status", "in", ["Open", "Replied"]]],
				},
				{
					key: "won",
					label: __("Ordered"),
					hint: __("Customer confirmed"),
					tone: "ok",
					filters: [["docstatus", "=", 1], ["status", "in", ["Ordered", "Partially Ordered"]]],
				},
				{
					key: "lost",
					label: __("Lost / expired"),
					hint: __("Closed without an order"),
					tone: "danger",
					filters: [["docstatus", "=", 1], ["status", "in", ["Lost", "Expired"]]],
				},
			],
		},
		"Sales Invoice": {
			amount: "base_grand_total",
			fields: ["docstatus", "status"],
			segments: [
				{ key: "draft", label: __("Draft"), hint: __("Not issued yet"), tone: "neutral", filters: [["docstatus", "=", 0]] },
				{
					key: "unpaid",
					label: __("Unpaid"),
					hint: __("Issued, not yet due"),
					tone: "warn",
					filters: [
						["docstatus", "=", 1],
						["status", "in", ["Unpaid", "Partly Paid", "Unpaid and Discounted", "Partly Paid and Discounted"]],
					],
				},
				{
					key: "overdue",
					label: __("Overdue"),
					hint: __("Past the due date"),
					tone: "danger",
					filters: [["docstatus", "=", 1], ["status", "in", ["Overdue", "Overdue and Discounted"]]],
				},
				{ key: "paid", label: __("Paid"), hint: __("Fully received"), tone: "ok", filters: [["docstatus", "=", 1], ["status", "=", "Paid"]] },
			],
		},
		Lead: {
			fields: ["status", "ic_next_contact_date"],
			segments: [
				{
					key: "due",
					label: __("Follow-up due"),
					hint: __("Contact date is today or earlier"),
					tone: "danger",
					needs: "ic_next_contact_date",
					filters: () => [
						["status", "not in", ["Converted", "Do Not Contact"]],
						// "between" leaves out leads that have no contact date at all;
						// a plain "<=" would count those as due.
						["ic_next_contact_date", "between", ["2000-01-01", frappe.datetime.get_today()]],
					],
				},
				{ key: "new", label: __("New"), hint: __("Not contacted yet"), tone: "info", filters: [["status", "=", "Lead"]] },
				{
					key: "talking",
					label: __("In conversation"),
					hint: __("Open, replied or interested"),
					tone: "warn",
					filters: [["status", "in", ["Open", "Replied", "Interested"]]],
				},
				{
					key: "quoted",
					label: __("Opportunity / quoted"),
					hint: __("Ready for or holding a quotation"),
					tone: "info",
					filters: [["status", "in", ["Opportunity", "Quotation"]]],
				},
				{ key: "won", label: __("Converted"), hint: __("Became a customer"), tone: "ok", filters: [["status", "=", "Converted"]] },
			],
		},
		Task: {
			fields: ["status"],
			segments: [
				{ key: "open", label: __("Open"), hint: __("Not started"), tone: "info", filters: [["status", "=", "Open"]] },
				{ key: "working", label: __("Working"), hint: __("In progress"), tone: "warn", filters: [["status", "in", ["Working", "Pending Review"]]] },
				{ key: "overdue", label: __("Overdue"), hint: __("Past the end date"), tone: "danger", filters: [["status", "=", "Overdue"]] },
				{ key: "done", label: __("Completed"), hint: __("Finished"), tone: "ok", filters: [["status", "=", "Completed"]] },
			],
		},
	};

	function seg_filters(seg) {
		return typeof seg.filters === "function" ? seg.filters() : seg.filters;
	}

	function money(value) {
		const currency = (frappe.boot.sysdefaults && frappe.boot.sysdefaults.currency) || "";
		try {
			return format_currency(value || 0, currency, 0);
		} catch (e) {
			return String(Math.round(value || 0));
		}
	}

	ux.render_status_bar = function (lv, frame_only) {
		const config = ux.STATUS_BARS[lv.doctype];
		if (!config || !lv.page || !lv.page.main) return;
		const main = lv.page.main[0] || lv.page.main;
		let bar = main.querySelector(":scope > .ic-statbar");
		const segments = config.segments.filter((s) => !s.needs || frappe.meta.has_field(lv.doctype, s.needs));
		if (!bar) {
			bar = document.createElement("div");
			bar.className = "ic-statbar";
			bar.setAttribute("role", "group");
			bar.setAttribute("aria-label", __("Filter by stage"));
			bar.innerHTML = segments
				.map(
					(s) =>
						`<button type="button" class="ic-stat ic-tone-${s.tone}" data-seg="${s.key}" aria-pressed="false" title="${frappe.utils.escape_html(s.hint || "")}">` +
						`<span class="ic-stat-label"><i class="ic-stat-dot" aria-hidden="true"></i>${frappe.utils.escape_html(s.label)}</span>` +
						`<span class="ic-stat-count">&ndash;</span>` +
						(config.amount ? `<span class="ic-stat-amount">&nbsp;</span>` : `<span class="ic-stat-amount">${frappe.utils.escape_html(s.hint || "")}</span>`) +
						`</button>`
				)
				.join("");
			const anchor = main.querySelector(":scope > .page-form");
			if (anchor && anchor.nextSibling) main.insertBefore(bar, anchor.nextSibling);
			else main.insertBefore(bar, main.firstChild);
			bar.addEventListener("click", (e) => {
				const btn = e.target.closest(".ic-stat");
				if (!btn) return;
				const seg = segments.find((s) => s.key === btn.getAttribute("data-seg"));
				if (seg) ux.apply_segment(lv, config, seg, btn.getAttribute("aria-pressed") === "true");
			});
		}
		ux.mark_active_segment(lv, config, segments, bar);
		if (frame_only) return;

		const now = Date.now();
		if (lv.__ic_stat_at && now - lv.__ic_stat_at < 8000) return;
		lv.__ic_stat_at = now;
		segments.forEach((seg) => {
			const fields = [{ COUNT: "name", as: "n" }];
			if (config.amount) fields.push({ SUM: config.amount, as: "total" });
			frappe.call({
				method: "frappe.client.get_list",
				args: { doctype: lv.doctype, filters: seg_filters(seg), fields: fields, limit_page_length: 1 },
				callback(r) {
					const row = (r.message && r.message[0]) || {};
					const btn = bar.querySelector(`[data-seg="${seg.key}"]`);
					if (!btn) return;
					const n = row.n || 0;
					btn.querySelector(".ic-stat-count").textContent = n;
					btn.classList.toggle("is-empty", !n);
					if (config.amount) btn.querySelector(".ic-stat-amount").textContent = money(row.total);
				},
				error() {
					const btn = bar.querySelector(`[data-seg="${seg.key}"]`);
					if (btn) btn.classList.add("is-empty");
				},
			});
		});
	};

	function same(a, b) {
		return JSON.stringify(a) === JSON.stringify(b);
	}

	ux.mark_active_segment = function (lv, config, segments, bar) {
		let current = [];
		try {
			current = (lv.filter_area ? lv.filter_area.get() : []).filter((f) => config.fields.includes(f[1]));
		} catch (e) {
			current = [];
		}
		const norm = (list) =>
			list
				.map((f) => (f.length > 3 ? [f[1], f[2], f[3]] : f))
				.map((f) => [f[0], String(f[1]).toLowerCase(), Array.isArray(f[2]) ? f[2].slice().sort() : String(f[2])])
				.sort((x, y) => (x[0] > y[0] ? 1 : -1));
		const cur = norm(current);
		segments.forEach((seg) => {
			const on = cur.length > 0 && same(cur, norm(seg_filters(seg)));
			const btn = bar.querySelector(`[data-seg="${seg.key}"]`);
			if (btn) {
				btn.classList.toggle("is-on", on);
				btn.setAttribute("aria-pressed", on ? "true" : "false");
			}
		});
	};

	ux.apply_segment = function (lv, config, seg, was_on) {
		if (!lv.filter_area) return;
		const keep = lv.filter_area.get().filter((f) => !config.fields.includes(f[1]));
		const next = was_on ? keep : keep.concat(
					// The filter row drops a bare 0, so numbers go in as text ("0" is draft).
					seg_filters(seg).map((f) => [lv.doctype, f[0], f[1], typeof f[2] === "number" ? String(f[2]) : f[2]])
			  );
		Promise.resolve(lv.filter_area.clear(false))
			.then(() => (next.length ? lv.filter_area.add(next, false) : null))
			.then(() => lv.refresh());
	};

	ux.patch_lists = function () {
		const ListView = frappe.views && frappe.views.ListView;
		if (!ListView || ListView.prototype.__ic_ux) return;
		ListView.prototype.__ic_ux = true;
		const render_list = ListView.prototype.render_list;
		ListView.prototype.render_list = function () {
			const result = render_list.apply(this, arguments);
			try {
				ux.render_status_bar(this);
			} catch (e) {
				/* never block a list from drawing */
			}
			return result;
		};
		// Frappe marks the page as a list only once the rows arrive; on a phone that
		// changed the side padding and moved the whole list 16px sideways. Mark it as
		// soon as the page exists.
		const setup_page = ListView.prototype.setup_page;
		ListView.prototype.setup_page = function () {
			const result = setup_page.apply(this, arguments);
			try {
				if (this.view_name === "List") this.parent.page.main.parent().addClass("list-view");
			} catch (e) {
				/* never block a list from drawing */
			}
			return result;
		};
		// Put the (still empty) bar in place while the list is being built, so the
		// rows are drawn below it once instead of being pushed down a moment later.
		const setup_view = ListView.prototype.setup_view;
		ListView.prototype.setup_view = function () {
			const result = setup_view.apply(this, arguments);
			try {
				ux.render_status_bar(this, true);
			} catch (e) {
				/* never block a list from drawing */
			}
			return result;
		};
		// A total on Home ("6 leads") asks for every record. Without this the list
		// opened with whatever filter this person last used and showed fewer rows.
		const before_refresh = ListView.prototype.before_refresh;
		ListView.prototype.before_refresh = function () {
			if (frappe.route_options && frappe.route_options.__ic_show_all && this.filter_area) {
				frappe.route_options = null;
				return this.filter_area.clear(false);
			}
			return before_refresh.apply(this, arguments);
		};
	};

	/* ------------------------------------------------------------------ */
	/* 4. Small-screen and home housekeeping                               */
	/* ------------------------------------------------------------------ */
	ux.rail_on_tablet = function () {
		try {
			const sidebar = frappe.app && frappe.app.sidebar;
			if (!sidebar || ux.__railed) return;
			if (window.innerWidth < 768 || window.innerWidth >= 1100) {
				ux.__railed = true;
				return;
			}
			// The menu is drawn a moment after the page; wait until it has its items.
			const ready = sidebar.wrapper && sidebar.wrapper.find(".sidebar-items").children().length > 0;
			if (!ready) {
				ux.__rail_tries = (ux.__rail_tries || 0) + 1;
				if (ux.__rail_tries < 20) setTimeout(ux.rail_on_tablet, 250);
				return;
			}
			ux.__railed = true;
			if (sidebar.sidebar_expanded) sidebar.toggle_width();
		} catch (e) {
			/* ignore */
		}
	};

	/** A section heading with nothing under it is hidden (home page only). */
	ux.hide_empty_headings = function () {
		const page = document.querySelector('.page-container[data-page-route="instacertify-home"], #page-instacertify-home');
		const scope = page || document;
		const blocks = [...scope.querySelectorAll(".codex-editor__redactor > .ce-block")];
		if (!blocks.length) return;
		let heading = null;
		let has_content = false;
		const close = () => {
			if (heading) heading.classList.toggle("ic-empty-heading", !has_content);
		};
		blocks.forEach((block) => {
			if (block.querySelector(".ce-header")) {
				close();
				heading = block;
				has_content = false;
			} else if (!block.querySelector(".widget.spacer") && block.getBoundingClientRect().height > 24) {
				has_content = true;
			}
		});
		close();
	};

	/**
	 * Two kinds of desk link reloaded the whole desk on every click, because
	 * Frappe's own link handler does not pick them up:
	 *   - links inside the Home blocks (they sit in a shadow root), and
	 *   - links written with the older "/app/..." address, which the server
	 *     redirects to "/desk/...".
	 * Both are handed to the router here, the same way Frappe treats its own links.
	 */
	ux.keep_block_links_in_app = function () {
		if (ux.__block_links) return;
		ux.__block_links = true;
		document.addEventListener("click", function (e) {
			if (e.defaultPrevented || e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
			const path = (e.composedPath && e.composedPath()) || [];
			const link = path.find((node) => node && node.tagName === "A" && node.getAttribute("href"));
			if (!link || !(frappe.router && frappe.router.is_app_route)) return;
			if (link.getAttribute("target") === "_blank" || link.getAttribute("onclick")) return;
			if (link.hasAttribute("download") || link.getAttribute("href") === "#") return;
			if (link.hostname !== window.location.hostname) return;
			const old_style = /^\/app(\/|$)/.test(link.pathname);
			const in_block = link.getRootNode() instanceof ShadowRoot;
			const desk_path = old_style ? link.pathname.replace(/^\/app/, "/desk") : link.pathname;
			// An ordinary "/desk/..." link is already handled by Frappe.
			if (!old_style && !in_block) return;
			if (!frappe.router.is_app_route(desk_path)) return;
			e.preventDefault();
			if (link.search) {
				frappe.route_options = {};
				new URLSearchParams(link.search).forEach((value, key) => {
					frappe.route_options[key] = value;
				});
			}
			if (link.hash) frappe.route_hash = link.hash;
			frappe.set_route(desk_path);
		});
	};

	/* ------------------------------------------------------------------ */
	/* Charts and totals open the records behind them                      */
	/* ------------------------------------------------------------------ */

	/** Open a list showing exactly `filters` ([[doctype, field, operator, value], ...]). */
	ux.open_records = function (doctype, filters) {
		if (!doctype) return;
		if (!frappe.model.can_read(doctype)) {
			frappe.show_alert({ message: __("You do not have permission to open {0}", [__(doctype)]), indicator: "red" });
			return;
		}
		const options = {};
		(filters || []).forEach((f) => {
			if (!Array.isArray(f) || f.length < 4 || (f[0] && f[0] !== doctype)) return;
			options[f[1]] = f[2] === "=" ? f[3] : [f[2], f[3]];
		});
		// With nothing to filter by, the list is asked to show everything instead of
		// the filter this person last used there.
		frappe.route_options = Object.keys(options).length ? options : { __ic_show_all: 1 };
		frappe.set_route("List", doctype, "List");
	};

	/** The label of the bar, slice or legend entry that was clicked, or null. */
	ux.chart_label_at = function (target, chart) {
		if (!target || !target.closest) return null;
		const svg = target.closest("svg");
		const hit = target.closest(
			".pie-path, .donut-path, .bar, .legend-dot, .legend-dataset-label, .legend-dataset-value"
		);
		if (!svg || !hit) return null;
		let index = -1;
		const circular = !!svg.querySelector(".pie-path, .donut-path");
		if (hit.matches(".pie-path, .donut-path")) {
			index = Array.from(svg.querySelectorAll(".pie-path, .donut-path")).indexOf(hit);
		} else if (hit.matches(".bar")) {
			const group = hit.closest(".dataset-units") || svg;
			index = Array.from(group.querySelectorAll(".bar")).indexOf(hit);
		} else {
			const legend = hit.closest(".chart-legend");
			const item = hit.closest("g");
			if (legend && item) index = Array.from(legend.children).indexOf(item);
		}
		if (index < 0 || !chart) return null;
		const labels = circular ? chart.state && chart.state.labels : chart.data && chart.data.labels;
		const label = labels && labels[index];
		return label == null ? null : String(label);
	};

	ux.TIMESPAN = {
		"Last Year": "last year",
		"Last Quarter": "last quarter",
		"Last Month": "last month",
		"Last Week": "last week",
	};

	/** Filters that describe what a dashboard chart (and the clicked part of it) counts. */
	ux.chart_widget_filters = function (widget, label) {
		const doc = widget.chart_doc || {};
		const doctype = doc.document_type;
		let filters = [];
		const chosen = widget.filters;
		if (Array.isArray(chosen)) {
			filters = chosen.map((f) => f.slice(0, 4));
		} else if (chosen && typeof chosen === "object") {
			filters = Object.keys(chosen).map((k) =>
				Array.isArray(chosen[k]) ? [doctype, k, chosen[k][0], chosen[k][1]] : [doctype, k, "=", chosen[k]]
			);
		} else {
			try {
				filters = (JSON.parse(doc.filters_json || "[]") || []).map((f) => f.slice(0, 4));
			} catch (e) {
				filters = [];
			}
		}
		if (doc.chart_type === "Group By" && doc.group_by_based_on) {
			if (label && label !== "Rest") {
				const unset = label === "Not Set" || label === __("Not Set");
				filters.push(
					unset
						? [doctype, doc.group_by_based_on, "is", "not set"]
						: [doctype, doc.group_by_based_on, "=", label]
				);
			}
		} else if (doc.timeseries && doc.based_on) {
			const settings = widget.chart_settings || {};
			const span = settings.timespan || doc.timespan;
			if (ux.TIMESPAN[span]) {
				filters.push([doctype, doc.based_on, "Timespan", ux.TIMESPAN[span]]);
			} else if ((settings.from_date || doc.from_date) && (settings.to_date || doc.to_date)) {
				filters.push([
					doctype,
					doc.based_on,
					"between",
					[settings.from_date || doc.from_date, settings.to_date || doc.to_date],
				]);
			}
		}
		return filters;
	};

	/** Pie and donut legends are drawn in fixed 150px slots, so a long name
	 *  such as "Shared with Customer" paints over the next name. Each name
	 *  gets its own row, and the chart grows to fit. */
	ux.stack_home_legends = function (root) {
		const visit = (node) => {
			if (!node || !node.querySelectorAll) return;
			node.querySelectorAll(".chart-legend").forEach(ux._stack_one_legend);
			node.querySelectorAll("*").forEach((el) => {
				if (el.shadowRoot) visit(el.shadowRoot);
			});
		};
		visit(root && root.querySelectorAll ? root : document);
	};

	ux._stack_one_legend = function (legend) {
		const items = [...legend.children].filter((el) => (el.tagName || "").toLowerCase() === "g");
		if (items.length < 2) return;
		const svg = legend.ownerSVGElement;
		if (!svg) return;
		const placed = legend.getAttribute("transform") || "";
		const pos = /translate\(\s*([-\d.]+)[,\s]+([-\d.]+)\s*\)/.exec(placed);
		const left = pos ? parseFloat(pos[1]) : 0;
		const top = pos ? parseFloat(pos[2]) : 0;
		const svgW = parseFloat(svg.getAttribute("width")) || svg.getBoundingClientRect().width || 320;
		const maxLabel = Math.max(120, svgW - left - 28);
		items.forEach((g) => {
			const label = g.querySelector(".legend-dataset-label");
			if (!label || label.getAttribute("data-ic-wrapped")) return;
			const words = (label.textContent || "").trim().split(/\s+/);
			if (words.length > 1) {
				let wide = false;
				try {
					wide = label.getBBox().width > maxLabel;
				} catch (e) {
					wide = false;
				}
				if (wide) {
					const x = label.getAttribute("x") || "0";
					const dx = label.getAttribute("dx") || "0";
					const lines = [];
					let line = [];
					words.forEach((word) => {
						const trial = line.concat(word).join(" ");
						label.textContent = trial;
						let w = 0;
						try {
							w = label.getBBox().width;
						} catch (e) {
							w = 0;
						}
						if (line.length && w > maxLabel) {
							lines.push(line.join(" "));
							line = [word];
						} else {
							line.push(word);
						}
					});
					if (line.length) lines.push(line.join(" "));
					label.textContent = "";
					lines.forEach((content, i) => {
						const span = document.createElementNS("http://www.w3.org/2000/svg", "tspan");
						span.setAttribute("x", x);
						span.setAttribute("dx", dx);
						span.setAttribute("dy", i === 0 ? "0" : "1.2em");
						span.textContent = content;
						label.appendChild(span);
					});
				}
			}
			label.setAttribute("data-ic-wrapped", "1");
			const value = g.querySelector(".legend-dataset-value");
			if (value) {
				let bottom = 18;
				try {
					const box = label.getBBox();
					bottom = box.y + box.height + 6;
				} catch (e) {
					/* keep the original value position */
				}
				value.setAttribute("y", String(Math.round(bottom)));
			}
		});
		let y = 0;
		items.forEach((g) => {
			g.setAttribute("transform", "translate(0, " + y + ")");
			let h = 42;
			try {
				h = Math.max(36, Math.ceil(g.getBBox().height) + 12);
			} catch (e) {
				/* a fixed step still separates the names */
			}
			y += h;
		});
		const needed = Math.ceil(top + y + 8);
		const current = parseFloat(svg.getAttribute("height")) || 0;
		if (needed > current) {
			svg.setAttribute("height", String(needed));
			svg.style.height = needed + "px";
			svg.style.overflow = "visible";
		}
		let box = svg.parentElement;
		while (box && !box.classList.contains("layout-main")) {
			if (box.classList.contains("widget") || box.classList.contains("widget-body") || box.classList.contains("chart-container")) {
				box.style.height = "auto";
				box.style.overflow = "visible";
			}
			box = box.parentElement;
		}
	};

	ux.patch_charts = function () {
		const Chart = frappe.widget && frappe.widget.widget_factory && frappe.widget.widget_factory.chart;
		if (!Chart || Chart.prototype.__ic_click) return;
		Chart.prototype.__ic_click = true;
		const chartArgs = Chart.prototype.get_chart_args;
		if (chartArgs) {
			Chart.prototype.get_chart_args = function () {
				const args = chartArgs.apply(this, arguments);
				const doc = this.chart_doc || {};
				const counting =
					doc.chart_type === "Count" ||
					(doc.chart_type === "Group By" && (doc.group_by_type || "Count") === "Count");
				if (counting && args) {
					args.tooltipOptions = Object.assign({}, args.tooltipOptions, {
						formatTooltipY: (value) => {
							const n = Number(value);
							return Number.isFinite(n) ? String(Math.round(n)) : String(value == null ? "" : value);
						},
					});
				}
				return args;
			};
		}
		const render = Chart.prototype.render;
		Chart.prototype.render = function () {
			const result = render.apply(this, arguments);
			const widget = this;
			try {
				const doc = widget.chart_doc || {};
				const from_records = ["Group By", "Count", "Sum", "Average"].includes(doc.chart_type);
				if (from_records && widget.chart_wrapper && !widget.__ic_bound) {
					widget.__ic_bound = true;
					widget.chart_wrapper
						.addClass("ic-chart-opens-list")
						.attr("title", __("Click a bar, slice or name to see those records"))
						.on("click", function (e) {
							if (!widget.chart_doc.document_type) return;
							const label = ux.chart_label_at(e.target, widget.dashboard_chart);
							ux.open_records(widget.chart_doc.document_type, ux.chart_widget_filters(widget, label));
						});
				}
			} catch (e) {
				/* the chart still shows; it just does not open a list */
			}
			const fix = () => {
				try {
					ux.stack_home_legends(widget.chart_wrapper && widget.chart_wrapper[0]);
				} catch (e) {
					/* the chart still shows with its original legend */
				}
			};
			if (result && typeof result.then === "function") result.then(fix);
			[80, 400, 1000, 1800].forEach((ms) => setTimeout(fix, ms));
			return result;
		};
	};

	/**
	 * For charts drawn inside the Home blocks. `spec` says what the chart counts:
	 * { doctype, field, base: [[doctype, field, op, value]], ranges: { label: [from, to] }, date_field }.
	 */
	ux.bind_block_chart = function (el, chart, spec) {
		if (!el || !spec || !spec.doctype) return;
		el.classList.add("ic-chart-opens-list");
		el.style.cursor = "pointer";
		el.title = __("Click a bar, slice or name to see those records");
		el.onclick = function (e) {
			const label = ux.chart_label_at(e.target, chart);
			let filters = (spec.base || []).slice();
			if (label && spec.ranges && spec.ranges[label]) {
				const range = spec.ranges[label];
				filters = [
					range[1]
						? [spec.doctype, spec.date_field || "creation", "between", [range[0], range[1]]]
						: [spec.doctype, spec.date_field || "creation", ">=", range[0]],
				];
			} else if (label && spec.field && label !== "Rest") {
				filters.push(
					label === "Not Set"
						? [spec.doctype, spec.field, "is", "not set"]
						: [spec.doctype, spec.field, "=", label]
				);
			}
			ux.open_records(spec.doctype, filters);
		};
	};

	/** Field notes stay behind an "i". Click it to read them. */
	ux.fold_field_help = function (root) {
		const scope = root && root.querySelectorAll ? root : document;
		scope.querySelectorAll(".help-box, .form-section-description").forEach((box) => {
			const text = (box.textContent || "").replace(/\s+/g, " ").trim();
			if (!text) return;
			const host = box.closest(".frappe-control, .form-section, .form-dashboard-section");
			const label =
				host &&
				host.querySelector(".control-label, .section-head, .form-section-heading, .label-area");
			if (!label) return;
			let button = label.querySelector(".ic-field-info");
			if (!button) {
				button = document.createElement("button");
				button.type = "button";
				button.className = "ic-field-info";
				button.setAttribute("aria-label", __("About this field"));
				button.textContent = "i";
				button.addEventListener("click", function (event) {
					event.preventDefault();
					event.stopPropagation();
					ux.show_help_pop(button, button.getAttribute("data-help") || "");
				});
				label.appendChild(button);
			}
			button.setAttribute("data-help", text);
			box.classList.add("ic-help-folded");
		});
	};

	ux.show_help_pop = function (button, text) {
		const open = document.querySelector(".ic-help-pop");
		if (open) open.remove();
		if (!text) return;
		if (button._ic_pop_open) {
			button._ic_pop_open = false;
			return;
		}
		const pop = document.createElement("div");
		pop.className = "ic-help-pop";
		pop.textContent = text;
		document.body.appendChild(pop);
		const rect = button.getBoundingClientRect();
		const width = Math.min(280, window.innerWidth - 24);
		let left = rect.left;
		if (left + width > window.innerWidth - 12) left = window.innerWidth - width - 12;
		pop.style.width = width + "px";
		pop.style.left = Math.max(12, left) + "px";
		pop.style.top = rect.bottom + 8 + "px";
		button._ic_pop_open = true;
		setTimeout(() => {
			const close = function (event) {
				if (pop.contains(event.target) || event.target === button) return;
				pop.remove();
				button._ic_pop_open = false;
				document.removeEventListener("click", close, true);
			};
			document.addEventListener("click", close, true);
		}, 0);
	};

	ux.watch_chart_legends = function () {
		if (ux._legend_watch) return;
		ux._legend_watch = true;
		const run = () => {
			const route = (document.body.getAttribute("data-route") || "");
			if (route.indexOf("Instacertify Home") === -1 && route.indexOf("Workspaces") === -1) return;
			try {
				ux.stack_home_legends(document);
			} catch (e) {
				/* leave the legend as drawn */
			}
		};
		const observer = new MutationObserver(() => {
			clearTimeout(ux._legend_timer);
			ux._legend_timer = setTimeout(run, 60);
		});
		observer.observe(document.body, { childList: true, subtree: true });
		run();
	};

	ux.watch_field_help = function () {
		if (ux._help_watch) return;
		ux._help_watch = true;
		const run = () => {
			try {
				ux.fold_field_help(document);
			} catch (e) {
				/* the form still works; the note stays where it was */
			}
		};
		run();
		ux._help_timer = null;
		const observer = new MutationObserver(() => {
			clearTimeout(ux._help_timer);
			ux._help_timer = setTimeout(run, 80);
		});
		observer.observe(document.body, { childList: true, subtree: true });
	};

	ux.on_page = function () {
		ux.keep_block_links_in_app();
		ux.watch_field_help();
		ux.patch_charts();
		ux.watch_chart_legends();
		ux.patch_indicator();
		ux.patch_lists();
		ux.watch_headers();
		ux.rail_on_tablet();
		const route = (frappe.get_route && frappe.get_route()) || [];
		if (route[0] === "Workspaces" || route[0] === "instacertify-home" || route.length === 0) {
			[400, 1500, 3500].forEach((ms) => {
				setTimeout(ux.hide_empty_headings, ms);
				setTimeout(() => ux.stack_home_legends(document), ms);
			});
		}
	};

	/**
	 * When the first page fails to open (a link to a record this person may not
	 * see), Frappe never announces a page change, so the usual side menu was not
	 * put in place and a different module's menu stayed. Try again shortly after.
	 */
	ux.keep_home_menu = function () {
		[600, 2000].forEach((ms) =>
			setTimeout(() => {
				try {
					const sidebar = frappe.app && frappe.app.sidebar;
					if (sidebar && !sidebar.__ic_pinned && window.instacertify && instacertify.pin_home_sidebar) {
						instacertify.pin_home_sidebar();
					}
				} catch (e) {
					/* keep whatever menu is showing */
				}
			}, ms)
		);
	};

	/**
	 * The app already keeps one side menu on every page, but it switched that on
	 * only after the desk had started. Reloading a record, or opening one from a
	 * link, therefore showed another module's menu for a moment (and that
	 * module's "Getting Started" panel) before the usual menu came back. The same
	 * rule is applied here before the first page is drawn.
	 */
	ux.pin_menu_early = function () {
		try {
			const Sidebar = frappe.ui && frappe.ui.Sidebar;
			if (!Sidebar || Sidebar.prototype.__ic_early || !frappe.boot) return;
			const home = (frappe.boot.instacertify && frappe.boot.instacertify.default_workspace) || "Instacertify Home";
			const known = frappe.boot.workspace_sidebar_item || {};
			if (!known[home.toLowerCase()]) return;
			Sidebar.prototype.__ic_early = true;
			Sidebar.prototype.resolve_sidebar = function () {
				return this.sidebar_title || home;
			};
			Sidebar.prototype.show_sidebar_for_module = function () {
				this.set_active_workspace_item();
			};
		} catch (e) {
			/* the menu is still pinned once the desk has started */
		}
	};
	ux.pin_menu_early();

	$(document).on("app_ready", function () {
		ux.on_page();
		ux.rail_on_tablet();
		ux.keep_home_menu();
	});
	$(document).on("page-change", function () {
		ux.on_page();
		setTimeout(ux.watch_headers, 300);
	});
	$(document).on("form-refresh", function () {
		ux.watch_headers();
	});
	ux.patch_indicator();
})();
