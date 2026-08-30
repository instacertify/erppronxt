# Copyright (c) Instacertify
"""Project Progress Tracker — saved editable log (IC Project Update)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, flt, get_datetime, now_datetime, strip_html


@frappe.whitelist()
def get_progress_log(project: str, limit: int = 100):
	"""Return saved Progress Tracker log entries for a project."""
	if not project:
		frappe.throw(_("Project is required"))
	frappe.has_permission("Project", doc=project, throw=True)

	limit = min(cint(limit) or 100, 200)
	rows = frappe.get_all(
		"IC Project Update",
		filters={"project": project},
		fields=[
			"name",
			"subject",
			"update_date",
			"progress_percentage",
			"project_stage",
			"pending_action",
			"remarks",
			"attachment",
			"working_hours",
			"updated_by",
			"creation",
			"modified",
			"owner",
		],
		order_by="update_date desc, creation desc",
		limit_page_length=limit,
	)

	out = []
	for r in rows:
		plain = strip_html(r.remarks or "") if r.remarks else ""
		user = r.updated_by or r.owner
		full_name = frappe.db.get_value("User", user, "full_name") if user else ""
		out.append(
			{
				"name": r.name,
				"subject": r.subject or "",
				"update_date": r.update_date or r.creation,
				"progress_percentage": flt(r.progress_percentage),
				"project_stage": r.project_stage or "",
				"pending_action": r.pending_action or "",
				"remarks": r.remarks or "",
				"plain": plain,
				"attachment": r.attachment or "",
				"working_hours": flt(r.working_hours),
				"updated_by": user,
				"updated_by_name": full_name or user or "",
			}
		)

	proj = frappe.db.get_value(
		"Project",
		project,
		[
			"ic_project_stage",
			"ic_progress_percentage",
			"ic_pending_action",
			"ic_products_services",
			"ic_deliverables",
			"ic_testing_requirements",
			"ic_timeline",
		],
		as_dict=True,
	) or {}

	return {"entries": out, "project": proj, "me": frappe.session.user}


@frappe.whitelist()
def save_progress_entry(
	project: str,
	subject: str,
	name: str | None = None,
	remarks: str | None = None,
	project_stage: str | None = None,
	progress_percentage: float | None = None,
	pending_action: str | None = None,
	update_date: str | None = None,
	attachment: str | None = None,
	working_hours: float | None = None,
	apply_to_project: int | bool = 1,
):
	"""Create or update a Progress Tracker log entry (IC Project Update)."""
	if not project:
		frappe.throw(_("Project is required"))
	if not frappe.db.exists("Project", project):
		frappe.throw(_("Project {0} not found").format(project))
	frappe.has_permission("Project", doc=project, throw=True)

	subject = (subject or "").strip()
	if not subject:
		frappe.throw(_("Subject is required"))

	apply_to_project = cint(apply_to_project)
	is_new = not name

	if name:
		if not frappe.db.exists("IC Project Update", name):
			frappe.throw(_("Progress log entry {0} not found").format(name))
		doc = frappe.get_doc("IC Project Update", name)
		if doc.project != project:
			frappe.throw(_("Entry does not belong to this project"))
		frappe.has_permission("IC Project Update", doc=doc, ptype="write", throw=True)
	else:
		frappe.has_permission("IC Project Update", ptype="create", throw=True)
		doc = frappe.new_doc("IC Project Update")
		doc.project = project

	doc.subject = subject
	doc.remarks = remarks or ""
	doc.project_stage = project_stage or doc.project_stage
	if progress_percentage is not None and progress_percentage != "":
		doc.progress_percentage = flt(progress_percentage)
	doc.pending_action = pending_action if pending_action is not None else doc.pending_action
	doc.update_date = get_datetime(update_date) if update_date else (doc.update_date or now_datetime())
	if attachment is not None:
		doc.attachment = attachment
	if working_hours is not None and working_hours != "":
		doc.working_hours = flt(working_hours)
	doc.updated_by = frappe.session.user
	# Avoid double project sync from doc_events when we apply below
	doc.flags.ic_skip_project_sync = True

	if is_new:
		doc.insert()
	else:
		doc.save()

	if apply_to_project:
		_apply_entry_to_project(project, doc)

	frappe.db.commit()
	return {"name": doc.name, "message": _("Progress log saved")}


@frappe.whitelist()
def delete_progress_entry(name: str):
	"""Delete a Progress Tracker log entry."""
	if not name or not frappe.db.exists("IC Project Update", name):
		frappe.throw(_("Progress log entry not found"))
	doc = frappe.get_doc("IC Project Update", name)
	frappe.has_permission("Project", doc=doc.project, throw=True)
	frappe.has_permission("IC Project Update", doc=doc, ptype="delete", throw=True)
	doc.delete()
	frappe.db.commit()
	return {"ok": 1}


def sync_project_from_update(doc, method=None):
	"""When an IC Project Update is saved outside the Progress UI, mirror stage/% onto Project."""
	if getattr(doc, "flags", None) and doc.flags.get("ic_skip_project_sync"):
		return
	if not doc.project:
		return
	# Only sync when stage or % explicitly set on the update
	if not doc.project_stage and doc.progress_percentage in (None, ""):
		return
	try:
		_apply_entry_to_project(doc.project, doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "IC Project Update → Project sync")


def _apply_entry_to_project(project: str, entry):
	proj = frappe.get_doc("Project", project)
	changed = False
	if entry.project_stage and proj.ic_project_stage != entry.project_stage:
		proj.ic_project_stage = entry.project_stage
		changed = True
	if entry.progress_percentage not in (None, "") and flt(proj.ic_progress_percentage) != flt(
		entry.progress_percentage
	):
		proj.ic_progress_percentage = flt(entry.progress_percentage)
		changed = True
	if entry.pending_action is not None and (proj.ic_pending_action or "") != (entry.pending_action or ""):
		proj.ic_pending_action = entry.pending_action
		changed = True
	if changed:
		# Prevent auto-creating another update from stage change
		proj.flags.ic_skip_auto_update = True
		proj.save(ignore_permissions=True)
