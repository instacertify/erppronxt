# Copyright (c) Instacertify
"""Turn Raven on for the people who already use the desk.

Raven itself is installed with scripts/install_raven.sh. This only opens the
chat to existing desk users and puts Chat in the side menu.
"""

from __future__ import annotations

import frappe


def configure():
	"""Let every enabled desk user open /raven, and show Chat in the menu."""
	if "raven" not in frappe.get_installed_apps():
		return {"ok": False, "reason": "Raven is not installed"}

	if frappe.db.exists("DocType", "Raven Settings"):
		frappe.db.set_single_value("Raven Settings", "auto_add_system_users", 1)

	added = []
	users = frappe.get_all(
		"User",
		filters={"enabled": 1, "user_type": "System User", "name": ["!=", "Guest"]},
		pluck="name",
	)
	for name in users:
		if name == "Administrator":
			continue
		if frappe.db.exists("Raven User", {"user": name}):
			continue
		user = frappe.get_doc("User", name)
		roles = {row.role for row in user.roles}
		if "Raven User" not in roles:
			user.append("roles", {"role": "Raven User"})
		user.flags.ignore_permissions = True
		user.save(ignore_permissions=True)
		added.append(name)

	frappe.db.commit()
	try:
		from instacertify.setup.workspace_setup import _ensure_instacertify_home_sidebar

		_ensure_instacertify_home_sidebar()
		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Raven sidebar")

	return {"ok": True, "users_added": added}
