# Copyright (c) Instacertify
"""One-shot interoperability + prompts QC."""

from __future__ import annotations

import json
import traceback

import frappe
from frappe.utils import add_to_date, now_datetime, nowdate


def run():
	report = {"ok": [], "warn": [], "fail": []}

	def ok(msg):
		report["ok"].append(msg)

	def warn(msg):
		report["warn"].append(msg)

	def fail(msg):
		report["fail"].append(msg)

	for dt in [
		"Lead",
		"Quotation",
		"Project",
		"Customer",
		"Event",
		"Task",
		"Helpdesk Ticket",
		"IC Testing Request",
		"IC Document Request",
		"IC Sample Tracking",
		"IC Expense Claim",
		"IC Quotation Template",
		"IC Laboratory",
		"IC Settings",
	]:
		(ok if frappe.db.exists("DocType", dt) else fail)(f"DocType {dt}")

	for dt, field in [
		("Quotation", "ic_workflow_status"),
		("Project", "ic_quotation"),
		("Sales Invoice", "ic_quotation"),
		("Lead", "ic_pipeline_stage"),
		("Lead", "ic_next_contact_date"),
		("Lead", "ic_history_html"),
		("Quotation", "ic_links_html"),
		("Event", "ic_notify_minutes"),
		("Event", "ic_prestart_notified"),
	]:
		try:
			(ok if frappe.get_meta(dt).has_field(field) else fail)(f"Field {dt}.{field}")
		except Exception as e:
			fail(f"Meta {dt}: {e}")

	lead = frappe.db.get_value("Lead", {}, "name", order_by="modified desc")
	qtn = frappe.db.get_value("Quotation", {}, "name", order_by="modified desc")
	cust = frappe.db.get_value("Customer", {}, "name", order_by="modified desc")

	apis = [
		("instacertify.project.events.get_dashboard_counts", {}),
		("instacertify.hr.dashboard.get_workdesk_insights", {"limit": 5}),
		("instacertify.crm.dashboard.get_lead_contact_prompts", {"limit": 5}),
		("instacertify.explore.dashboard.get_explore_prompts", {}),
		("instacertify.setup.library_upload.get_library_summary", {}),
		("instacertify.calendar.events.get_team_users", {}),
		("instacertify.crm.dashboard.get_lead_tracker_stats", {}),
	]
	if lead:
		apis.append(("instacertify.crm.events.get_lead_history", {"lead": lead}))
	if qtn:
		apis.append(("instacertify.crm.events.get_quotation_links", {"quotation": qtn}))
	if cust:
		apis.append(("instacertify.crm.events.get_customer_history", {"customer": cust}))

	for method, args in apis:
		try:
			r = frappe.call(method, **args)
			ok(f"API {method}")
		except Exception as e:
			fail(f"API {method}: {e}")

	# Lead contact prompts content
	try:
		prompts = frappe.call("instacertify.crm.dashboard.get_lead_contact_prompts", limit=10) or {}
		rows = prompts.get("prompts") or []
		ok(f"Lead prompts rows={len(rows)} keys={list(prompts.keys())}")
		if not rows:
			warn("Lead contact prompts empty — set ic_next_contact_date on leads")
	except Exception as e:
		fail(f"Lead prompts: {e}")

	# Workdesk prompts (tasks/calendar/leads)
	try:
		wd = frappe.call("instacertify.hr.dashboard.get_workdesk_insights", limit=5) or {}
		ok(
			f"Workdesk tasks={len(wd.get('tasks') or [])} events={len(wd.get('events') or [])} leads={len(wd.get('my_leads') or [])}"
		)
	except Exception as e:
		fail(f"Workdesk: {e}")

	# Dashboard counts
	try:
		counts = frappe.call("instacertify.project.events.get_dashboard_counts") or {}
		needed = [
			"new_leads",
			"active_leads",
			"quotations_sent",
			"active_projects",
			"pending_tasks",
			"leads_to_contact",
		]
		missing = [k for k in needed if k not in counts]
		if missing:
			fail(f"Dashboard counts missing {missing}")
		else:
			ok(f"Dashboard counts ok { {k: counts[k] for k in needed} }")
	except Exception as e:
		fail(f"Dashboard counts: {e}")

	# Explore prompts
	try:
		explore = frappe.call("instacertify.explore.dashboard.get_explore_prompts") or {}
		cards = explore.get("cards") or []
		ok(f"Explore cards={len(cards)} ids={[c.get('id') for c in cards[:8]]}")
		if len(cards) < 3:
			warn("Explore cards sparse for current user roles")
	except Exception as e:
		fail(f"Explore prompts: {e}")

	# Quotation PDF
	try:
		from instacertify.utils.pdf import get_quotation_pdf_bytes

		q = frappe.db.get_value("Quotation", {"ic_quotation_type": "Consulting"}, "name") or qtn
		pdf = get_quotation_pdf_bytes(q)
		if pdf and pdf[:4] == b"%PDF":
			ok(f"Quotation PDF {q} bytes={len(pdf)}")
		else:
			fail(f"Quotation PDF invalid {q}")
	except Exception as e:
		fail(f"Quotation PDF: {e}")

	# Calendar reminder
	try:
		from instacertify.calendar.events import create_team_session
		from instacertify.notifications.tasks import event_start_reminders

		start = add_to_date(now_datetime(), minutes=18)
		end = add_to_date(start, minutes=30)
		users = frappe.get_all(
			"User",
			filters={"enabled": 1, "user_type": "System User"},
			pluck="name",
			limit=2,
		)
		res = create_team_session(
			subject="Interop QC reminder session",
			starts_on=str(start),
			ends_on=str(end),
			participants=users,
			event_type="Public",
		)
		name = res["name"]
		if frappe.get_meta("Event").has_field("ic_prestart_notified"):
			frappe.db.set_value("Event", name, "ic_prestart_notified", 0, update_modified=False)
		before = frappe.db.count(
			"Notification Log", {"document_name": name, "subject": ["like", "Starting%"]}
		)
		event_start_reminders()
		after = frappe.db.count(
			"Notification Log", {"document_name": name, "subject": ["like", "Starting%"]}
		)
		flagged = frappe.db.get_value("Event", name, "ic_prestart_notified")
		if after > before or flagged:
			ok(f"Calendar 30m reminder Event={name} new_notifs={after - before} flagged={flagged}")
		else:
			fail(f"Calendar 30m reminder silent for {name}")
	except Exception as e:
		fail(f"Calendar reminder: {e}")

	# Default workspace
	ws = frappe.db.get_value("User", "Administrator", "default_workspace")
	(ok if ws == "Instacertify Home" else warn)(f"default_workspace={ws}")

	# Number card filters
	import json as _json

	bad = []
	for nc in frappe.get_all(
		"Number Card", filters={"module": "Instacertify"}, fields=["name", "filters_json"], limit=25
	):
		try:
			parsed = _json.loads(nc.filters_json or "[]")
			if not isinstance(parsed, list):
				bad.append(nc.name)
		except Exception:
			bad.append(nc.name)
	(ok if not bad else fail)(
		"Number Card filters list-ok" if not bad else f"Number Card bad filters {bad}"
	)

	# Project-Quotation links
	linked = frappe.db.sql(
		"""
		select count(*) from tabProject where ifnull(ic_quotation,'')!=''
		"""
	)[0][0]
	(ok if linked else warn)(f"Projects linked to Quotation={linked}")

	# Lead due prompts source
	due_leads = frappe.db.count(
		"Lead",
		{
			"status": ["not in", ["Converted", "Do Not Contact"]],
			"ic_next_contact_date": ["<=", nowdate()],
		},
	)
	ok(f"Leads due for contact={due_leads}")

	# Ensure some leads have contact dates so prompts work
	if due_leads == 0:
		sample = frappe.get_all(
			"Lead",
			filters={"status": ["not in", ["Converted", "Do Not Contact"]]},
			pluck="name",
			limit=3,
		)
		for n in sample:
			frappe.db.set_value(
				"Lead",
				n,
				{
					"ic_next_contact_date": nowdate(),
					"ic_call_remarks": "Interop QC: please call and update remarks",
					"ic_lead_connected": 0,
				},
				update_modified=False,
			)
		due_leads = len(sample)
		warn(f"Seeded ic_next_contact_date on {due_leads} leads for prompts")

	hooks = frappe.get_hooks("override_doctype_dashboards") or {}
	for dt in ["Lead", "Quotation", "Project", "Customer"]:
		(ok if dt in hooks else fail)(f"Dashboard override {dt}")

	sched = frappe.get_hooks("scheduler_events") or {}
	cron = sched.get("cron") if isinstance(sched, dict) else {}
	found = False
	if isinstance(cron, dict):
		for _k, v in cron.items():
			if any("event_start_reminders" in str(x) for x in (v or [])):
				found = True
	(ok if found else fail)("Cron event_start_reminders")

	# Pipeline advance path exists
	try:
		from instacertify.quotation import events as qe

		assert hasattr(qe, "_advance_linked_lead")
		ok("Quotation→Lead pipeline advance helper")
	except Exception as e:
		fail(f"Pipeline helper: {e}")

	frappe.db.commit()
	summary = {
		"ok": len(report["ok"]),
		"warn": len(report["warn"]),
		"fail": len(report["fail"]),
		"report": report,
	}
	print(json.dumps(summary, indent=2, default=str))
	return summary
