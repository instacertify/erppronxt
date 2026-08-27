import frappe

def execute(filters=None):
	columns = [
		{"label": "Project", "fieldname": "name", "fieldtype": "Link", "options": "Project", "width": 140},
		{"label": "Project Name", "fieldname": "project_name", "fieldtype": "Data", "width": 220},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 160},
		{"label": "Stage", "fieldname": "ic_project_stage", "fieldtype": "Data", "width": 180},
		{"label": "Priority", "fieldname": "ic_priority", "fieldtype": "Data", "width": 90},
		{"label": "Progress %", "fieldname": "ic_progress_percentage", "fieldtype": "Percent", "width": 100},
		{"label": "Pending Action", "fieldname": "ic_pending_action", "fieldtype": "Data", "width": 180},
		{"label": "Deadline", "fieldname": "ic_deadline", "fieldtype": "Date", "width": 110},
		{"label": "Assigned", "fieldname": "ic_assigned_employee", "fieldtype": "Link", "options": "User", "width": 140},
	]
	data = frappe.get_all(
		"Project",
		filters={"status": ["not in", ["Cancelled"]]},
		fields=[c["fieldname"] for c in columns],
		order_by="ic_deadline asc",
	)
	return columns, data
