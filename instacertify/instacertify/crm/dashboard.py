# Copyright (c) Instacertify
"""CRM lead tracker stats for desk charts."""

from __future__ import annotations

import frappe
from frappe.utils import add_days, add_months, get_first_day, getdate, nowdate


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


def _leads_to_contact(limit=20, include_upcoming_days=7):
	"""Leads due for contact (overdue/today) plus upcoming within N days.

	Returns rows with due_label, phone, remarks, connected flag for dashboard prompts.
	"""
	if not frappe.get_meta("Lead").has_field("ic_next_contact_date"):
		return []

	today = getdate(nowdate())
	horizon = add_days(today, include_upcoming_days)

	rows = frappe.get_all(
		"Lead",
		filters=[
			["status", "not in", ["Converted", "Do Not Contact"]],
			["ic_next_contact_date", "is", "set"],
			["ic_next_contact_date", "<=", str(horizon)],
		],
		fields=[
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
		],
		order_by="ic_next_contact_date asc",
		limit_page_length=limit,
	)

	out = []
	for r in rows:
		due = getdate(r.ic_next_contact_date) if r.ic_next_contact_date else None
		if not due:
			continue
		if due < today:
			due_label = "Overdue"
			urgency = "overdue"
		elif due == today:
			due_label = "Contact today"
			urgency = "today"
		else:
			due_label = f"Due {due.strftime('%d %b')}"
			urgency = "upcoming"
		out.append(
			{
				**r,
				"title": r.ic_party_name or r.company_name or r.lead_name or r.name,
				"phone": r.mobile_no or r.phone or "",
				"due_label": due_label,
				"urgency": urgency,
				"connected_label": "Connected" if r.ic_lead_connected else "Not connected",
			}
		)
	return out


@frappe.whitelist()
def get_lead_contact_prompts(limit=12):
	"""Dashboard prompts: when to contact, call remarks, connected status."""
	rows = _leads_to_contact(limit=limit)
	due_now = [r for r in rows if r.get("urgency") in ("overdue", "today")]
	return {
		"prompts": rows,
		"due_now": due_now,
		"due_count": len(due_now),
		"upcoming_count": len([r for r in rows if r.get("urgency") == "upcoming"]),
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
