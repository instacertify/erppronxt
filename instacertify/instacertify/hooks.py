app_name = "instacertify"
app_title = "Instacertify"
app_publisher = "Instacertify"
app_description = "Instacertify ERP customizations on ERPNext for certification, compliance, consulting and testing"
app_email = "admin@instacertify.com"
app_license = "mit"
app_version = "1.0.0"

# Apps
required_apps = ["erpnext", "india_compliance"]

# Includes in <head>
app_include_css = "/assets/instacertify/css/instacertify.css"
app_include_js = "/assets/instacertify/js/instacertify.js"
web_include_css = "/assets/instacertify/css/instacertify.css"
website_include_css = "/assets/instacertify/css/instacertify.css"

# Website / portal
website_route_rules = [
	{"from_route": "/ic-quotation/<path:name>", "to_route": "ic_quotation"},
	{"from_route": "/ic-documents/<path:name>", "to_route": "ic_documents"},
	{"from_route": "/ic-report/<path:name>", "to_route": "ic_report"},
	{"from_route": "/ic-verify/<path:doctype>/<path:name>", "to_route": "ic_verify"},
]

# Document Events
doc_events = {
	"Sales Invoice": {
		"validate": "instacertify.accounting.events.validate_sales_invoice",
	},
	"Purchase Invoice": {
		"validate": "instacertify.accounting.events.validate_purchase_invoice",
	},
	"Quotation": {
		"before_insert": "instacertify.quotation.events.before_insert_quotation",
		"validate": "instacertify.quotation.events.validate_quotation",
		"on_update_after_submit": "instacertify.quotation.events.on_update_after_submit",
		"on_submit": "instacertify.quotation.events.on_submit_quotation",
	},
	"Customer": {
		"validate": "instacertify.accounting.events.validate_customer",
	},
	"Project": {
		"validate": "instacertify.project.events.validate_project",
		"on_update": "instacertify.project.events.on_update_project",
	},
	"Lead": {
		"validate": "instacertify.crm.events.validate_lead",
		"before_validate": "instacertify.crm.events.before_validate_lead",
		"before_insert": "instacertify.crm.events.before_validate_lead",
	},
	"IC Sample Tracking": {
		"before_insert": "instacertify.testing.events.before_insert_sample",
		"validate": "instacertify.testing.events.validate_sample",
	},
	"IC Testing Request": {
		"on_update": "instacertify.testing.events.on_update_testing_request",
	},
	"Payment Entry": {
		"on_submit": "instacertify.accounting.payments.on_submit_payment_entry",
	},
	"Event": {
		"validate": "instacertify.calendar.events.validate_event",
		"on_update": "instacertify.calendar.events.on_update_event",
		"after_insert": "instacertify.calendar.events.after_insert_event",
	},
}

# Scheduled Tasks
scheduler_events = {
	"daily": [
		"instacertify.notifications.tasks.deadline_reminders",
	],
	"cron": {
		# Every 15 minutes — 30-min prior calendar session alerts
		"*/15 * * * *": [
			"instacertify.notifications.tasks.event_start_reminders",
		],
	},
}

# Fixtures
fixtures = [
	{
		"dt": "Role",
		"filters": [["name", "in", [
			"IC Admin",
			"IC Senior Operations",
			"IC Sales Person",
			"IC Operations Manager",
		]]],
	},
	{
		"dt": "Custom Field",
		"filters": [["module", "=", "Instacertify"]],
	},
	{
		"dt": "Property Setter",
		"filters": [["module", "=", "Instacertify"]],
	},
	{
		"dt": "Workspace",
		"filters": [["module", "=", "Instacertify"]],
	},
	{
		"dt": "Workflow",
		"filters": [["name", "like", "IC %"]],
	},
	{
		"dt": "Workflow State",
		"filters": [["name", "like", "IC %"]],
	},
	{
		"dt": "Workflow Action Master",
		"filters": [["name", "like", "IC %"]],
	},
	{
		"dt": "Print Format",
		"filters": [["module", "=", "Instacertify"]],
	},
	{
		"dt": "Notification",
		"filters": [["module", "=", "Instacertify"]],
	},
	{
		"dt": "Client Script",
		"filters": [["module", "=", "Instacertify"]],
	},
	{
		"dt": "Server Script",
		"filters": [["module", "=", "Instacertify"]],
	},
	{
		"dt": "Number Card",
		"filters": [["module", "=", "Instacertify"]],
	},
	{
		"dt": "Dashboard Chart",
		"filters": [["module", "=", "Instacertify"]],
	},
]

# Jinja
jinja = {
	"methods": [
		"instacertify.utils.qr.get_qr_code_data_uri",
	],
}

# Bootinfo / branding
boot_session = "instacertify.boot.boot_session"

# Form Connections dashboards
override_doctype_dashboards = {
	"Customer": "instacertify.overrides.customer.get_dashboard_data",
	"Quotation": "instacertify.overrides.quotation.get_dashboard_data",
	"Project": "instacertify.overrides.project.get_dashboard_data",
	"Lead": "instacertify.overrides.lead.get_dashboard_data",
}

override_doctype_class = {
	"Lead": "instacertify.crm.lead.ICLead",
}

# After migrate
after_migrate = [
	"instacertify.setup.install.after_migrate",
]

after_install = "instacertify.setup.install.after_install"

# Desk / login logo (circular mark for small navbar spaces)
app_logo_url = "/assets/instacertify/images/instacertify_app_logo.png"

# Website context extras
website_context = {
	"favicon": "/assets/instacertify/images/favicon-32.png",
	"splash_image": "/assets/instacertify/images/instacertify_logo.png",
}

# Reliable Quotation PDF (Chrome + inlined-asset fallback; no HostNotFound server error)
override_whitelisted_methods = {
	"frappe.utils.print_format.download_pdf": "instacertify.utils.pdf.download_pdf",
}
