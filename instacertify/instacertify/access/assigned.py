# Copyright (c) Instacertify
"""Let the people named on a record open that record.

Sharing is added. Nothing is hidden from anyone else, and no price, field,
workflow or DocType is changed. A person still needs their role for anything
the share does not cover.
"""

from __future__ import annotations

import json

import frappe

# Write on the records a person is responsible for. An invoice is read-only
# through the share; Finance still posts it, and a sales role that already
# has write is unchanged.
_WRITE = {"Lead", "Quotation", "Project", "Task"}

_FIELDS = {
	"Lead": ("lead_owner", "ic_assigned_salesperson", "ic_assigned_operations_manager", "owner"),
	"Quotation": ("ic_primary_assignee", "ic_assigned_salesperson", "owner"),
	"Project": ("ic_assigned_employee", "owner"),
	"Task": ("ic_primary_assignee", "owner"),
	"Sales Invoice": ("owner",),
}


def _add(users: list[str], seen: set[str], user):
	if not user or user in seen or user in ("Guest", "Administrator"):
		return
	if not frappe.db.exists("User", user):
		return
	seen.add(user)
	users.append(user)


def assigned_users(doc) -> list[str]:
	"""Users named on this record: owner, assignee fields, team rows and Assign To."""
	users: list[str] = []
	seen: set[str] = set()
	for field in _FIELDS.get(doc.doctype, ("owner",)):
		if field == "owner" or doc.meta.has_field(field):
			_add(users, seen, doc.get(field))
	try:
		from instacertify.team.assignees import get_assignee_users

		for user in get_assignee_users(doc):
			_add(users, seen, user)
	except Exception:
		pass
	raw = doc.get("_assign")
	if raw:
		try:
			parsed = json.loads(raw) if isinstance(raw, str) else raw
			for user in parsed or []:
				_add(users, seen, user)
		except Exception:
			pass
	if doc.doctype == "Sales Invoice" and doc.get("ic_quotation"):
		quote = doc.ic_quotation
		quote_meta = frappe.get_meta("Quotation")
		fields = ["owner"] + [
			field
			for field in ("ic_primary_assignee", "ic_assigned_salesperson")
			if quote_meta.has_field(field)
		]
		row = frappe.db.get_value("Quotation", quote, fields, as_dict=True)
		if row:
			for user in row.values():
				_add(users, seen, user)
		if frappe.db.exists("DocType", "IC Assignee"):
			for user in frappe.get_all(
				"IC Assignee",
				filters={"parent": quote, "parenttype": "Quotation"},
				pluck="user",
			):
				_add(users, seen, user)
	return users


def share_with_assignees(doc, method=None):
	"""Share this saved record with the people assigned to it."""
	if not doc or doc.doctype not in _FIELDS or not doc.name or doc.flags.get("ic_sharing_assignees"):
		return
	users = assigned_users(doc)
	if not users:
		return
	write = 1 if doc.doctype in _WRITE else 0
	doc.flags.ic_sharing_assignees = True
	for user in users:
		try:
			frappe.share.add_docshare(
				doc.doctype,
				doc.name,
				user,
				read=1,
				write=write,
				share=0,
				notify=0,
				flags={"ignore_share_permission": True},
			)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Share assigned {doc.doctype} {doc.name}")


def share_existing_assignments(limit: int = 2000):
	"""One pass so records assigned before this share existed can be opened."""
	shared = 0
	for doctype in _FIELDS:
		if not frappe.db.exists("DocType", doctype):
			continue
		for name in frappe.get_all(doctype, pluck="name", limit_page_length=int(limit)):
			try:
				share_with_assignees(frappe.get_doc(doctype, name))
				shared += 1
			except Exception:
				frappe.log_error(frappe.get_traceback(), f"Share existing {doctype} {name}")
	return {"shared": shared}
