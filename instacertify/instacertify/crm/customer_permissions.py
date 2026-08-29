# Copyright (c) Instacertify
"""Customer team membership — assigned members can see all Customer Data."""

from __future__ import annotations

import frappe
from frappe import _


FULL_ACCESS_ROLES = {
	"System Manager",
	"Administrator",
	"IC Admin",
	"Sales Manager",
	"Accounts Manager",
	"IC Senior Operations",
	"IC Operations Manager",
}


def user_has_full_customer_access(user: str | None = None) -> bool:
	user = user or frappe.session.user
	if not user or user in ("Guest",):
		return False
	if user == "Administrator":
		return True
	roles = set(frappe.get_roles(user))
	return bool(roles & FULL_ACCESS_ROLES)


def get_customer_team_users(customer: str | None) -> set[str]:
	"""Users explicitly assigned on the Customer (salesperson, AM, team table)."""
	users: set[str] = set()
	if not customer or not frappe.db.exists("Customer", customer):
		return users
	meta = frappe.get_meta("Customer")
	fields = ["owner"]
	for f in ("ic_assigned_salesperson", "ic_account_manager"):
		if meta.has_field(f):
			fields.append(f)
	row = frappe.db.get_value("Customer", customer, fields, as_dict=True) or {}
	for key in fields:
		u = row.get(key)
		if u and u not in ("Guest", "Administrator"):
			users.add(u)
	if frappe.db.exists("DocType", "IC Customer Team Member") and meta.has_field("ic_team_members"):
		for u in frappe.get_all(
			"IC Customer Team Member",
			filters={"parent": customer, "parenttype": "Customer"},
			pluck="user",
		):
			if u and u not in ("Guest",):
				users.add(u)
	return users


def get_users_assigned_to_customer(customer: str | None) -> set[str]:
	"""Union of Customer team + project teams linked to this customer + lead assignees."""
	users = get_customer_team_users(customer)
	if not customer:
		return users

	# Project teams
	projects = frappe.get_all("Project", filters={"customer": customer}, pluck="name")
	for project in projects[:100]:
		try:
			from instacertify.project.events import get_project_assignee_users

			users.update(get_project_assignee_users(project))
		except Exception:
			pass

	# Lead assignees for leads converted to this customer
	if frappe.db.has_column("Customer", "lead_name"):
		lead = frappe.db.get_value("Customer", customer, "lead_name")
		if lead and frappe.db.exists("Lead", lead):
			lead_row = frappe.db.get_value(
				"Lead",
				lead,
				["lead_owner", "ic_assigned_salesperson", "ic_assigned_operations_manager"],
				as_dict=True,
			) or {}
			for key in ("lead_owner", "ic_assigned_salesperson", "ic_assigned_operations_manager"):
				u = lead_row.get(key)
				if u and u not in ("Guest",):
					users.add(u)

	return {u for u in users if u and u not in ("Guest",)}


def is_user_assigned_to_customer(customer: str | None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	if not customer or not user or user == "Guest":
		return False
	if user_has_full_customer_access(user):
		return True
	return user in get_users_assigned_to_customer(customer)


def assert_can_read_customer_data(customer: str, user: str | None = None):
	"""Raise if the current user cannot view this customer's data.

	Assigned team members (Customer team, project team, lead assignees) always
	pass — even when they lack a broad Customer role — so they can open the
	Customer Data tab / drive. Managers and users with Customer read also pass.
	"""
	user = user or frappe.session.user
	if not customer or not user or user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if user_has_full_customer_access(user):
		return
	# Prefer explicit assignment first (covers users with no Customer role).
	if is_user_assigned_to_customer(customer, user):
		return
	# Fallback: standard Customer read (role / DocShare already granted).
	try:
		if frappe.has_permission("Customer", "read", customer, user=user):
			return
	except Exception:
		pass
	frappe.throw(
		_("You are not assigned to this customer, so Customer Data is not available."),
		frappe.PermissionError,
	)


def has_permission(doc, ptype=None, user=None, debug=False):
	"""Grant read (and report) to assigned team members."""
	user = user or frappe.session.user
	if ptype not in (None, "read", "report", "print", "email", "share"):
		return None
	if user_has_full_customer_access(user):
		return True
	name = doc if isinstance(doc, str) else getattr(doc, "name", None)
	if name and is_user_assigned_to_customer(name, user):
		return True
	return None


def get_permission_query_conditions(user: str | None = None) -> str:
	"""Ensure assigned customers appear in list for team members.

	Does not restrict managers. For other users, OR-assigns their customers with
	whatever their role already allows via Frappe's share/role logic by returning
	an inclusive subquery — Frappe ANDs this, so we only use it to *expand*
	visibility when combined carefully.

	Note: Frappe ANDs hook conditions. Returning assignee-only would hide other
	customers from Sales User. Therefore managers get no filter; others get a
	condition that is always true if they have broad Customer read via role.
	We rely on DocShare + has_permission for grants, and only add a soft filter
	when the user has no Customer read role at all.
	"""
	user = user or frappe.session.user
	if not user or user in ("Guest",):
		return "1=0"
	if user_has_full_customer_access(user):
		return ""

	# If the user already has Customer read via role (typical Sales User),
	# do not restrict the list — DocShare/has_permission handle assignees.
	try:
		meta = frappe.get_meta("Customer")
		# Rough check: can they read Customer doctype at all?
		if frappe.has_permission("Customer", "read", user=user):
			return ""
	except Exception:
		pass

	# No Customer role — show only assigned customers (DocShare + team)
	user_esc = frappe.db.escape(user)
	return f"""(
		`tabCustomer`.owner = {user_esc}
		OR `tabCustomer`.ic_assigned_salesperson = {user_esc}
		OR `tabCustomer`.ic_account_manager = {user_esc}
		OR EXISTS (
			SELECT 1 FROM `tabIC Customer Team Member` tm
			WHERE tm.parent = `tabCustomer`.name
			  AND tm.parenttype = 'Customer'
			  AND tm.user = {user_esc}
		)
		OR EXISTS (
			SELECT 1 FROM `tabProject` p
			INNER JOIN `tabProject Team Member` ptm
				ON ptm.parent = p.name AND ptm.parenttype = 'Project'
			WHERE p.customer = `tabCustomer`.name AND ptm.user = {user_esc}
		)
	)"""


def on_update_customer(doc, method=None):
	"""Keep DocShare in sync so assigned team can open Customer Data."""
	try:
		apply_customer_team_access(doc.name, rebuild_table=False)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "on_update_customer team access")


@frappe.whitelist()
def sync_customer_team(customer: str):
	"""Rebuild Customer team from projects + lead and share Customer Data access."""
	if not customer or not frappe.db.exists("Customer", customer):
		frappe.throw(_("Customer is required"))
	frappe.has_permission("Customer", "write", customer, throw=True)
	result = apply_customer_team_access(customer, rebuild_table=True)
	return result


def apply_customer_team_access(customer: str, rebuild_table: bool = False) -> dict:
	"""Persist team rows (optional) and DocShare read access for all assigned users."""
	if not customer or not frappe.db.exists("Customer", customer):
		return {"customer": customer, "users": [], "shared": 0}

	users = get_users_assigned_to_customer(customer)
	shared = 0

	if rebuild_table and frappe.get_meta("Customer").has_field("ic_team_members"):
		# Preserve manual rows; merge project/lead users
		doc = frappe.get_doc("Customer", customer)
		existing = {
			(row.user): row
			for row in (doc.get("ic_team_members") or [])
			if row.get("user")
		}
		# Seed salesperson / AM from lead if blank
		lead = doc.get("lead_name")
		if lead and frappe.db.exists("Lead", lead):
			lead_row = frappe.db.get_value(
				"Lead",
				lead,
				["ic_assigned_salesperson", "ic_assigned_operations_manager", "lead_owner"],
				as_dict=True,
			) or {}
			if not doc.get("ic_assigned_salesperson") and lead_row.get("ic_assigned_salesperson"):
				doc.ic_assigned_salesperson = lead_row.ic_assigned_salesperson
			if not doc.get("ic_account_manager") and lead_row.get("ic_assigned_operations_manager"):
				doc.ic_account_manager = lead_row.ic_assigned_operations_manager

		# Add missing users from projects/lead
		for user in sorted(users):
			if user in existing:
				continue
			if user in (doc.get("ic_assigned_salesperson"), doc.get("ic_account_manager")):
				role = "Sales" if user == doc.get("ic_assigned_salesperson") else "Account Owner"
			else:
				role = "Member"
			doc.append(
				"ic_team_members",
				{
					"user": user,
					"full_name": frappe.db.get_value("User", user, "full_name") or user,
					"role_on_customer": role,
					"source": "Project / Lead",
				},
			)
		doc.save(ignore_permissions=True)
		users = get_users_assigned_to_customer(customer)

	# DocShare read so team members can open Customer + see Customer Data
	for user in users:
		if user in ("Guest", "Administrator"):
			continue
		try:
			frappe.share.add(
				"Customer",
				customer,
				user,
				read=1,
				write=0,
				share=0,
				notify=0,
			)
			shared += 1
		except Exception:
			try:
				frappe.share.add_docshare(
					"Customer",
					customer,
					user,
					read=1,
					write=0,
					share=0,
					notify=0,
					flags={"ignore_share_permission": True},
				)
				shared += 1
			except Exception:
				frappe.log_error(frappe.get_traceback(), "Customer team DocShare")

	return {"customer": customer, "users": sorted(users), "shared": shared}
