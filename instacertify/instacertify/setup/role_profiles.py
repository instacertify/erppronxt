# Copyright (c) Instacertify
"""Instacertify Role Profiles — Manager / Executive access by function.

Profiles (assign on User → Role Profile):
  • IC Admin — settings, mappings, full control, Excel/CSV download
  • IC Ops Manager / IC Ops Executive — formats, lab scopes, customer data (no Excel/CSV)
  • IC Sales Manager / IC Sales Executive — sales, quotes, testing records
  • IC Projects Manager / IC Projects Executive — projects + test requests
  • IC HR Manager / IC HR Executive — attendance, salary, expenses
  • IC Finance Manager / IC Finance Executive — billing & billing requests

Calendar (Event) is available to every Instacertify profile.
Only Admin may export Excel/CSV of customer / commercial / lab data.
"""

from __future__ import annotations

import frappe

# Desk roles created for Instacertify (names stay stable for permissions code)
IC_ROLES = (
	"IC Admin",
	# Ops
	"IC Operations Manager",  # legacy + Ops Manager
	"IC Ops Executive",
	"IC Senior Operations",  # legacy senior ops (treated as Ops Manager tier)
	# Sales
	"IC Sales Manager",
	"IC Sales Executive",
	"IC Sales Person",  # legacy → Sales Executive tier
	# Projects
	"IC Projects Manager",
	"IC Projects Executive",
	# HR
	"IC HR Manager",
	"IC HR Executive",
	# Finance
	"IC Finance Manager",
	"IC Finance Executive",
)

# Role Profile name → bundled Role names (ERPNext/HRMS + IC)
ROLE_PROFILES: dict[str, list[str]] = {
	"IC Admin": [
		"IC Admin",
		"System Manager",
		"Sales Manager",
		"Projects Manager",
		"HR Manager",
		"Accounts Manager",
		"Employee",
	],
	"IC Ops Manager": [
		"IC Operations Manager",
		"IC Senior Operations",
		"Projects Manager",
		"Sales User",
		"Employee",
	],
	"IC Ops Executive": [
		"IC Ops Executive",
		"IC Operations Manager",
		"Projects User",
		"Employee",
	],
	"IC Sales Manager": [
		"IC Sales Manager",
		"IC Sales Person",
		"Sales Manager",
		"Sales User",
		"Employee",
	],
	"IC Sales Executive": [
		"IC Sales Executive",
		"IC Sales Person",
		"Sales User",
		"Employee",
	],
	"IC Projects Manager": [
		"IC Projects Manager",
		"Projects Manager",
		"Projects User",
		"Employee",
	],
	"IC Projects Executive": [
		"IC Projects Executive",
		"Projects User",
		"Employee",
	],
	"IC HR Manager": [
		"IC HR Manager",
		"HR Manager",
		"HR User",
		"Employee",
	],
	"IC HR Executive": [
		"IC HR Executive",
		"HR User",
		"Employee",
	],
	"IC Finance Manager": [
		"IC Finance Manager",
		"Accounts Manager",
		"Accounts User",
		"Employee",
	],
	"IC Finance Executive": [
		"IC Finance Executive",
		"Accounts User",
		"Employee",
	],
}

# Who may download Excel / CSV of operational & customer data
EXPORT_ROLES = frozenset({"Administrator", "System Manager", "IC Admin"})

# Ops may view sensitive masters but never export
OPS_ROLES = frozenset(
	{
		"IC Operations Manager",
		"IC Ops Executive",
		"IC Senior Operations",
	}
)

# DocTypes where Ops gets read (formats, labs, customers) without export
OPS_VIEW_DOCTYPES = (
	"Customer",
	"Contact",
	"Address",
	"Lead",
	"Opportunity",
	"Quotation",
	"IC Quotation Template",
	"IC Laboratory",
	"IC Settings",
	"IC Document Checklist Template",
	"IC Testing Request",
	"IC Sample Tracking",
	"IC Test Request Form",
	"IC Document Request",
	"IC Sample Dispatch Collection",
	"IC Contract",
	"IC Report Share",
	"Project",
	"Task",
	"File",
)

# Sales — quotes, leads, testing records
SALES_WRITE_DOCTYPES = (
	"Lead",
	"Opportunity",
	"Customer",
	"Contact",
	"Address",
	"Quotation",
	"IC Testing Request",
	"IC Sample Tracking",
	"IC Test Request Form",
	"IC Document Request",
	"IC Sample Dispatch Collection",
	"Project",
	"Task",
	"IC Project Update",
	"IC Project Record",
	"IC Report Share",
	"Helpdesk Ticket",
)

# Projects — projects + generate testing requests
PROJECTS_WRITE_DOCTYPES = (
	"Project",
	"Task",
	"Timesheet",
	"IC Testing Request",
	"IC Sample Tracking",
	"IC Test Request Form",
	"IC Document Request",
	"IC Project Update",
	"IC Project Record",
	"IC Sample Dispatch Collection",
	"Customer",
	"Quotation",
)

# HR
HR_DOCTYPES = (
	"Employee",
	"Attendance",
	"Attendance Request",
	"Leave Application",
	"Leave Allocation",
	"Salary Slip",
	"Payroll Entry",
	"Expense Claim",
	"IC Expense Claim",
	"IC Employee Document",
	"IC Joining Letter",
	"Employee Checkin",
	"Shift Assignment",
)

# Finance / billing
FINANCE_DOCTYPES = (
	"Sales Invoice",
	"Purchase Invoice",
	"Payment Entry",
	"Journal Entry",
	"Payment Request",
	"Sales Order",
	"Purchase Order",
	"GL Entry",
	"Account",
	"Cost Center",
	"GSTR-1",
	"GSTR 3B Report",
	"GST Return Log",
	"GST Settings",
)

# Calendar — every IC profile
CALENDAR_DOCTYPES = ("Event",)

# Settings / mappings — Admin only write
ADMIN_SETTINGS_DOCTYPES = (
	"IC Settings",
	"IC Lead Source",
	"IC Project Type",
	"IC Quotation Template",
	"IC Laboratory",
	"IC Document Checklist Template",
	"Website Settings",
	"Navbar Settings",
	"Print Format",
	"Letter Head",
	"Workflow",
	"Role",
	"Role Profile",
	"Module Profile",
	"Custom Field",
	"Property Setter",
)


def ensure_role_profiles():
	"""Create roles, Role Profiles, and DocType permissions for Instacertify teams."""
	_ensure_roles()
	_ensure_profiles()
	_apply_permissions()
	_ensure_calendar_for_all()
	frappe.clear_cache()


def _ensure_roles():
	for role in IC_ROLES:
		if frappe.db.exists("Role", role):
			# Keep desk access on
			frappe.db.set_value("Role", role, "desk_access", 1, update_modified=False)
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Role",
				"role_name": role,
				"desk_access": 1,
				"is_custom": 1,
			}
		)
		doc.insert(ignore_permissions=True)


def _ensure_profiles():
	if not frappe.db.exists("DocType", "Role Profile"):
		return
	for profile_name, roles in ROLE_PROFILES.items():
		_upsert_role_profile(profile_name, roles)


def _upsert_role_profile(name: str, roles: list[str]):
	# Only keep roles that exist on this site (HRMS/ERPNext may vary)
	valid = [r for r in roles if frappe.db.exists("Role", r)]
	if not valid:
		return
	if frappe.db.exists("Role Profile", name):
		doc = frappe.get_doc("Role Profile", name)
		_save_role_profile(doc, valid)
		return
	doc = frappe.get_doc(
		{
			"doctype": "Role Profile",
			"role_profile": name,
			"roles": [{"role": r} for r in valid],
		}
	)
	doc.insert(ignore_permissions=True)


def _save_role_profile(doc, roles: list[str]):
	"""Save Role Profile, clearing stale document locks from failed installs / migrate."""
	import time

	doc.set("roles", [])
	for r in roles:
		doc.append("roles", {"role": r})
	doc.flags.ignore_permissions = True
	last_err = None
	for attempt in range(5):
		try:
			doc.unlock()
		except Exception:
			pass
		try:
			doc.save(ignore_permissions=True)
			return
		except frappe.DocumentLockedError as e:
			last_err = e
			time.sleep(0.5 * (attempt + 1))
			doc.reload()
			doc.set("roles", [])
			for r in roles:
				doc.append("roles", {"role": r})
	if last_err:
		raise last_err


def _apply_permissions():
	# —— Admin: full on IC + settings + export ——
	for dt in _existing(
		list(OPS_VIEW_DOCTYPES)
		+ list(SALES_WRITE_DOCTYPES)
		+ list(PROJECTS_WRITE_DOCTYPES)
		+ list(HR_DOCTYPES)
		+ list(FINANCE_DOCTYPES)
		+ list(ADMIN_SETTINGS_DOCTYPES)
		+ list(CALENDAR_DOCTYPES)
	):
		_set_perm(
			dt,
			"IC Admin",
			read=1,
			write=1,
			create=1,
			delete=1,
			submit=1,
			cancel=1,
			report=1,
			export=1,
			print=1,
			select=1,
			force_export=True,
		)

	# —— Ops Manager: view formats / labs / customers — NO export ——
	for dt in _existing(OPS_VIEW_DOCTYPES):
		write = 1 if dt not in ("IC Settings", "Website Settings", "Navbar Settings") else 0
		for role in ("IC Operations Manager", "IC Senior Operations"):
			_set_perm(
				dt,
				role,
				read=1,
				write=write,
				create=write,
				delete=0,
				report=1,
				export=0,
				print=1,
				select=1,
				force_export=True,
			)

	# —— Ops Executive: read + limited write, no export ——
	for dt in _existing(OPS_VIEW_DOCTYPES):
		_set_perm(
			dt,
			"IC Ops Executive",
			read=1,
			write=1 if dt in ("IC Testing Request", "IC Sample Tracking", "IC Document Request", "Task", "Project") else 0,
			create=1 if dt in ("IC Testing Request", "IC Sample Tracking", "Task") else 0,
			delete=0,
			report=1,
			export=0,
			print=1,
			select=1,
			force_export=True,
		)

	# —— Sales Manager / Executive ——
	for dt in _existing(SALES_WRITE_DOCTYPES):
		_set_perm(
			dt,
			"IC Sales Manager",
			read=1,
			write=1,
			create=1,
			delete=0,
			submit=1 if dt == "Quotation" else 0,
			report=1,
			export=0,
			print=1,
			select=1,
			force_export=True,
		)
		_set_perm(
			dt,
			"IC Sales Executive",
			read=1,
			write=1,
			create=1,
			delete=0,
			report=1,
			export=0,
			print=1,
			select=1,
			force_export=True,
		)
		# Legacy sales person same as executive
		_set_perm(
			dt,
			"IC Sales Person",
			read=1,
			write=1,
			create=1,
			delete=0,
			report=1,
			export=0,
			print=1,
			select=1,
			force_export=True,
		)

	# Sales can read lab scopes / quote formats (no export, no settings write)
	for dt in _existing(("IC Laboratory", "IC Quotation Template", "IC Document Checklist Template")):
		for role in ("IC Sales Manager", "IC Sales Executive", "IC Sales Person"):
			_set_perm(dt, role, read=1, write=0, create=0, delete=0, report=1, export=0, print=1, select=1, force_export=True)

	# —— Projects Manager / Executive ——
	for dt in _existing(PROJECTS_WRITE_DOCTYPES):
		_set_perm(
			dt,
			"IC Projects Manager",
			read=1,
			write=1,
			create=1,
			delete=0,
			report=1,
			export=0,
			print=1,
			select=1,
			force_export=True,
		)
		_set_perm(
			dt,
			"IC Projects Executive",
			read=1,
			write=1,
			create=1,
			delete=0,
			report=1,
			export=0,
			print=1,
			select=1,
			force_export=True,
		)

	# —— HR Manager / Executive ——
	for dt in _existing(HR_DOCTYPES):
		_set_perm(
			dt,
			"IC HR Manager",
			read=1,
			write=1,
			create=1,
			delete=0,
			submit=1,
			cancel=1,
			report=1,
			export=1,  # HR may export payroll/attendance for processing
			print=1,
			select=1,
			force_export=True,
		)
		_set_perm(
			dt,
			"IC HR Executive",
			read=1,
			write=1,
			create=1,
			delete=0,
			submit=0,
			report=1,
			export=0,
			print=1,
			select=1,
			force_export=True,
		)

	# —— Finance Manager / Executive ——
	for dt in _existing(FINANCE_DOCTYPES):
		is_settings = dt == "GST Settings"
		_set_perm(
			dt,
			"IC Finance Manager",
			read=1,
			write=0 if is_settings else 1,
			create=0 if is_settings else 1,
			delete=0,
			submit=0 if is_settings else 1,
			cancel=0 if is_settings else 1,
			report=1,
			export=1,  # Finance may export billing data
			print=1,
			select=1,
			force_export=True,
		)
		_set_perm(
			dt,
			"IC Finance Executive",
			read=1,
			write=0 if is_settings else 1,
			create=0 if is_settings else 1,
			delete=0,
			submit=0,
			report=1,
			export=0,
			print=1,
			select=1,
			force_export=True,
		)


def _ensure_calendar_for_all():
	"""Every Instacertify role can use Team Calendar (Event)."""
	if not frappe.db.exists("DocType", "Event"):
		return
	for role in IC_ROLES:
		_set_perm(
			"Event",
			role,
			read=1,
			write=1,
			create=1,
			delete=0,
			report=1,
			export=0,
			print=1,
			select=1,
			force_export=True,
		)
	# Admin may export calendar if needed
	_set_perm(
		"Event",
		"IC Admin",
		read=1,
		write=1,
		create=1,
		delete=1,
		report=1,
		export=1,
		print=1,
		select=1,
		force_export=True,
	)


def _existing(names) -> list[str]:
	return [n for n in names if n and frappe.db.exists("DocType", n)]


def _set_perm(
	dt: str,
	role: str,
	*,
	read=0,
	write=0,
	create=0,
	delete=0,
	submit=0,
	cancel=0,
	report=0,
	export=0,
	print=0,
	select=0,
	force_export=False,
):
	if not frappe.db.exists("Role", role):
		return
	existing = frappe.db.exists("Custom DocPerm", {"parent": dt, "role": role, "permlevel": 0})
	values = {
		"read": int(read),
		"write": int(write),
		"create": int(create),
		"delete": int(delete),
		"submit": int(submit),
		"cancel": int(cancel),
		"amend": 0,
		"report": int(report),
		"export": int(export),
		"import": 1 if role == "IC Admin" and export else 0,
		"share": 0,
		"print": int(print),
		"email": 1 if write else 0,
		"select": int(select or read),
	}
	if existing:
		if not force_export:
			# Preserve stronger export if not forcing
			cur_export = frappe.db.get_value("Custom DocPerm", existing, "export")
			if cint(cur_export) and not values["export"]:
				values.pop("export", None)
		# Upscale other flags; never silently drop read if we intend read
		frappe.db.set_value("Custom DocPerm", existing, values, update_modified=False)
		return
	row = {"doctype": "Custom DocPerm", "parent": dt, "parenttype": "DocType", "parentfield": "permissions", "role": role, "permlevel": 0}
	row.update(values)
	try:
		frappe.get_doc(row).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"role_profiles perm {dt}/{role}")


def cint(v):
	try:
		return int(v or 0)
	except Exception:
		return 0


def user_can_export(user: str | None = None) -> bool:
	"""True if user may download Excel/CSV of operational data."""
	user = user or frappe.session.user
	if user in ("Administrator", "Guest"):
		return user == "Administrator"
	roles = set(frappe.get_roles(user))
	return bool(roles & EXPORT_ROLES)


def assert_can_export(user: str | None = None):
	"""Raise PermissionError when Ops / non-admin tries Excel/CSV export."""
	if user_can_export(user):
		return
	frappe.throw(
		"Excel / CSV download is limited to Admin. Ops Manager can view data but cannot export.",
		frappe.PermissionError,
	)


@frappe.whitelist()
def export_query():
	"""Gate list Excel/CSV export — Admin only for operational data; Ops blocked."""
	# Allow Admin / System Manager; block Ops and other non-export profiles
	doctype = frappe.form_dict.get("doctype") or frappe.form_dict.get("doc_type")
	sensitive = {
		"Customer",
		"Lead",
		"Quotation",
		"IC Laboratory",
		"IC Quotation Template",
		"IC Testing Request",
		"IC Sample Tracking",
		"IC Document Request",
		"Contact",
		"Address",
		"Opportunity",
		"Project",
		"Sales Invoice",
		"Payment Entry",
	}
	if doctype in sensitive or (doctype and str(doctype).startswith("IC ")):
		roles = set(frappe.get_roles())
		# Finance may export billing doctypes; HR may export HR doctypes; Admin always
		if not (roles & EXPORT_ROLES):
			finance_ok = doctype in FINANCE_DOCTYPES and (roles & {"IC Finance Manager", "Accounts Manager"})
			hr_ok = doctype in HR_DOCTYPES and (roles & {"IC HR Manager", "HR Manager"})
			if not finance_ok and not hr_ok:
				assert_can_export()
	from frappe.desk.reportview import export_query as _frappe_export_query

	return _frappe_export_query()
