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

	ux.on_page = function () {
		ux.patch_indicator();
		ux.patch_lists();
		ux.watch_headers();
		ux.rail_on_tablet();
		const route = (frappe.get_route && frappe.get_route()) || [];
		if (route[0] === "Workspaces" || route[0] === "instacertify-home" || route.length === 0) {
			[400, 1500, 3500].forEach((ms) => setTimeout(ux.hide_empty_headings, ms));
		}
	};

	$(document).on("app_ready", function () {
		ux.on_page();
		ux.rail_on_tablet();
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
