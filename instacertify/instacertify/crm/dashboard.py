# Copyright (c) Instacertify
"""CRM lead tracker stats for desk charts."""

from __future__ import annotations

import frappe
from frappe.utils import add_days, add_months, cint, get_first_day, getdate, nowdate


def _count_leads(from_date, to_date=None):
	filters = [["creation", ">=", str(from_date)]]
	if to_date:
		filters.append(["creation", "<", str(to_date)])
	try:
		return frappe.db.count("Lead", filters)
	except Exception:
		return 0


def _group_leads(fieldname: str, from_date, to_date=None, limit=12):
	"""Return [{label, count}] for pie / bar hierarchy charts."""
	if not frappe.db.has_column("Lead", fieldname) and fieldname not in (
		"status",
		"country",
		"source",
	):
		# Custom fields still use column names like ic_lead_source_detail
		pass
	conditions = ["creation >= %(from_date)s"]
	params = {"from_date": str(from_date)}
	if to_date:
		conditions.append("creation < %(to_date)s")
		params["to_date"] = str(to_date)

	# Safe field allow-list
	allowed = {
		"ic_lead_source_detail",
		"ic_project_type",
		"ic_company_size",
		"status",
		"country",
		"ic_request_category",
	}
	if fieldname not in allowed:
		return []

	sql = f"""
		select ifnull(`{fieldname}`, 'Not Set') as label, count(*) as count
		from `tabLead`
		where {' and '.join(conditions)}
		group by ifnull(`{fieldname}`, 'Not Set')
		order by count desc
		limit {int(limit)}
	"""
	try:
		rows = frappe.db.sql(sql, params, as_dict=True)
	except Exception:
		return []
	return [{"label": r.label or "Not Set", "count": int(r.count or 0)} for r in rows]


@frappe.whitelist()
def get_lead_tracker_stats():
	"""Week/month comparisons + hierarchy breakdowns for CRM charts."""
	today = getdate(nowdate())
	# Week windows (Mon–Sun style relative: last 7 days buckets)
	this_week_start = add_days(today, -6)  # inclusive rolling 7 days
	last_week_start = add_days(today, -13)
	last_week_end = add_days(today, -6)  # exclusive end = this_week_start

	this_month_start = get_first_day(today)
	last_month_start = get_first_day(add_months(today, -1))
	last_month_end = this_month_start

	day_30_start = add_days(today, -29)
	day_7_start = add_days(today, -6)

	this_week = _count_leads(this_week_start)
	last_week = _count_leads(last_week_start, last_week_end)
	this_month = _count_leads(this_month_start)
	last_month = _count_leads(last_month_start, last_month_end)
	last_7 = _count_leads(day_7_start)
	last_30 = _count_leads(day_30_start)

	def pct_change(current, previous):
		if not previous:
			return 100.0 if current else 0.0
		return round(((current - previous) / previous) * 100.0, 1)

	return {
		"this_week": this_week,
		"last_week": last_week,
		"week_change_pct": pct_change(this_week, last_week),
		"this_month": this_month,
		"last_month": last_month,
		"month_change_pct": pct_change(this_month, last_month),
		"last_7_days": last_7,
		"last_30_days": last_30,
		"week_compare": [
			{"label": "This Week", "count": this_week},
			{"label": "Last Week", "count": last_week},
		],
		"month_compare": [
			{"label": "This Month", "count": this_month},
			{"label": "Last Month", "count": last_month},
		],
		"by_source_7d": _group_leads("ic_lead_source_detail", day_7_start),
		"by_source_30d": _group_leads("ic_lead_source_detail", day_30_start),
		"by_project_type_7d": _group_leads("ic_project_type", day_7_start),
		"by_project_type_30d": _group_leads("ic_project_type", day_30_start),
		"by_status_30d": _group_leads("status", day_30_start),
		"by_size_30d": _group_leads("ic_company_size", day_30_start),
		"by_country_30d": _group_leads("country", day_30_start),
		"leads_to_contact": _leads_to_contact(),
		"amc_due": _amc_due_list(),
	}


def _leads_to_contact(limit=20, include_upcoming_days=7, mine_first=True):
	"""Leads due for contact (overdue/today) plus upcoming within N days.

	Returns reminder-hub rows: whom to call, phone, who to connect with, remarks.
	"""
	if not frappe.get_meta("Lead").has_field("ic_next_contact_date"):
		return []

	today = getdate(nowdate())
	horizon = add_days(today, include_upcoming_days)
	user = frappe.session.user

	fields = [
		"name",
		"lead_name",
		"company_name",
		"ic_party_name",
		"ic_next_contact_date",
		"ic_last_contacted",
		"ic_call_remarks",
		"ic_lead_connected",
		"status",
		"mobile_no",
		"phone",
		"email_id",
		"lead_owner",
		"city",
	]
	meta = frappe.get_meta("Lead")
	for optional in (
		"ic_assigned_salesperson",
		"ic_assigned_operations_manager",
		"ic_remarks",
		"ic_priority",
		"ic_pipeline_stage",
		"ic_alternate_phone",
		"designation",
	):
		if meta.has_field(optional):
			fields.append(optional)

	filters = [
		["status", "not in", ["Converted", "Do Not Contact"]],
		["ic_next_contact_date", "is", "set"],
		["ic_next_contact_date", "<=", str(horizon)],
	]

	rows = frappe.get_all(
		"Lead",
		filters=filters,
		fields=fields,
		order_by="ic_next_contact_date asc",
		limit_page_length=max(limit * 3, 30),
	)

	# Resolve user display names once
	user_ids = set()
	for r in rows:
		for key in ("lead_owner", "ic_assigned_salesperson", "ic_assigned_operations_manager"):
			if r.get(key):
				user_ids.add(r.get(key))
	user_names = {}
	if user_ids:
		for u in frappe.get_all(
			"User",
			filters={"name": ["in", list(user_ids)]},
			fields=["name", "full_name"],
		):
			user_names[u.name] = u.full_name or u.name

	def _plain(html_or_text):
		if not html_or_text:
			return ""
		text = frappe.utils.strip_html(str(html_or_text))
		return " ".join(text.split())

	out = []
	for r in rows:
		due = getdate(r.ic_next_contact_date) if r.ic_next_contact_date else None
		if not due:
			continue
		days = (due - today).days
		if due < today:
			due_label = f"Overdue · {abs(days)}d"
			urgency = "overdue"
		elif due == today:
			due_label = "Call today"
			urgency = "today"
		else:
			due_label = f"Due {due.strftime('%d %b')}"
			urgency = "upcoming"

		contact_person = (r.get("ic_party_name") or r.get("lead_name") or "").strip()
		company = (r.get("company_name") or "").strip()
		title = contact_person or company or r.name
		phone = r.get("mobile_no") or r.get("phone") or r.get("ic_alternate_phone") or ""

		salesperson = r.get("ic_assigned_salesperson") or ""
		owner = r.get("lead_owner") or ""
		ops = r.get("ic_assigned_operations_manager") or ""
		# Who to dial with / coordinate with on this lead
		call_with_id = salesperson or owner
		call_with = user_names.get(call_with_id) if call_with_id else ""
		if not call_with and call_with_id:
			call_with = call_with_id
		ops_name = user_names.get(ops) if ops else ""

		remarks = _plain(r.get("ic_call_remarks")) or _plain(r.get("ic_remarks")) or ""

		mine = bool(
			user
			and user not in ("Guest", "Administrator")
			and user in {salesperson, owner, ops}
		) or (user == "Administrator")

		out.append(
			{
				**{k: r.get(k) for k in fields},
				"title": title,
				"contact_person": contact_person or title,
				"company": company,
				"phone": phone,
				"email": r.get("email_id") or "",
				"due_label": due_label,
				"urgency": urgency,
				"days_offset": days,
				"connected_label": "Connected" if r.get("ic_lead_connected") else "Not connected yet",
				"call_with": call_with or "Unassigned",
				"call_with_user": call_with_id or "",
				"ops_manager": ops_name,
				"remarks": remarks or "No customer remarks yet — add Call / Lead Remarks after the conversation.",
				"has_remarks": 1 if remarks else 0,
				"mine": 1 if mine else 0,
				"priority": r.get("ic_priority") or "",
				"pipeline_stage": r.get("ic_pipeline_stage") or r.get("status") or "",
			}
		)

	# Prefer my leads, then urgency (overdue → today → upcoming), then date
	urgency_rank = {"overdue": 0, "today": 1, "upcoming": 2}
	if mine_first and user not in ("Guest",):
		out.sort(
			key=lambda x: (
				0 if x.get("mine") else 1,
				urgency_rank.get(x.get("urgency"), 9),
				x.get("ic_next_contact_date") or "",
			)
		)
	else:
		out.sort(
			key=lambda x: (
				urgency_rank.get(x.get("urgency"), 9),
				x.get("ic_next_contact_date") or "",
			)
		)
	return out[:limit]


@frappe.whitelist()
def get_lead_contact_prompts(limit=12, mine_only=0):
	"""Reminder hub: whom to call, who to connect with, customer remarks, due when."""
	limit = int(limit or 12)
	rows = _leads_to_contact(limit=limit * 2 if cint(mine_only) else limit)
	if cint(mine_only):
		rows = [r for r in rows if r.get("mine")][:limit]
	due_now = [r for r in rows if r.get("urgency") in ("overdue", "today")]
	upcoming = [r for r in rows if r.get("urgency") == "upcoming"]
	return {
		"prompts": rows,
		"due_now": due_now,
		"upcoming": upcoming,
		"due_count": len(due_now),
		"upcoming_count": len(upcoming),
		"hub_title": "Lead reminders",
		"hub_sub": "Who to call next",
	}


@frappe.whitelist()
def get_lead_reminders_page(limit=200, filter=None):
	"""Dedicated Lead Reminders page payload (supports Show more paging in UI)."""
	limit = max(1, min(int(limit or 200), 500))
	data = get_lead_contact_prompts(limit=limit)
	rows = data.get("prompts") or []
	filt = (filter or "all").lower()
	if filt == "due":
		rows = [r for r in rows if r.get("urgency") in ("overdue", "today")]
	elif filt == "upcoming":
		rows = [r for r in rows if r.get("urgency") == "upcoming"]
	elif filt == "mine":
		rows = [r for r in rows if r.get("mine")]
	return {
		"prompts": rows,
		"due_count": data.get("due_count") or 0,
		"upcoming_count": data.get("upcoming_count") or 0,
		"total": len(rows),
		"filter": filt,
		"page_size": 20,
		"hub_title": "Lead Reminders",
		"hub_sub": "Who to call · phone · owner · remarks",
		"me": frappe.session.user,
	}


def _amc_due_list(limit=10):
	if not frappe.get_meta("Project").has_field("ic_requires_amc"):
		return []
	return frappe.get_all(
		"Project",
		filters={
			"ic_requires_amc": 1,
			"ic_amc_status": ["in", ["Scheduled", "Reminded"]],
			"ic_amc_contact_date": ["<=", add_days(nowdate(), 31)],
		},
		fields=["name", "project_name", "customer", "ic_amc_contact_date", "ic_amc_status"],
		order_by="ic_amc_contact_date asc",
		limit_page_length=limit,
	)


@frappe.whitelist()
def search_country_india_first(
	doctype=None, txt="", searchfield=None, start=0, page_len=20, filters=None
):
	"""Country Link query — India pinned at top, then alphabetical."""
	txt = (txt or "").strip()
	like = f"%{txt}%"
	start = int(start or 0)
	page_len = int(page_len or 20)

	# Always try to include India first on page 0 when it matches
	rows = []
	if start == 0 and (not txt or "india".startswith(txt.lower()) or "india" in txt.lower()):
		if frappe.db.exists("Country", "India"):
			rows.append(("India",))

	extra = frappe.db.sql(
		"""
		select name
		from tabCountry
		where name like %(txt)s
		  and name != 'India'
		order by name asc
		limit %(start)s, %(page_len)s
		""",
		{"txt": like, "start": start, "page_len": page_len},
	)
	for r in extra:
		if r[0] not in {x[0] for x in rows}:
			rows.append(r)
	return rows[:page_len]
