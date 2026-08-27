# Copyright (c) Instacertify
"""Populate realistic Instacertify demo data."""

from __future__ import annotations

import secrets

import frappe
from frappe.utils import add_days, today


def execute():
	frappe.only_for(("System Manager", "Administrator"))
	_ensure_company()
	users = _create_users()
	_create_consultants()
	_create_templates()
	_create_checklists()
	labs = _create_laboratories()
	customers = _create_customers()
	_create_leads(users)
	quotations = _create_quotations(customers, users, labs)
	projects = _create_projects(customers, quotations, users)
	_create_testing(customers, projects, labs, users)
	_create_document_requests(customers, projects, users)
	_create_employees_and_assets(users)
	_seed_workdesk_and_hr(users, projects)
	_seed_helpdesk_tickets(customers, projects, users)
	frappe.db.commit()
	return {"ok": True, "customers": len(customers), "projects": len(projects)}


def _ensure_company():
	if not frappe.db.exists("Company", "Instacertify"):
		try:
			frappe.get_doc(
				{
					"doctype": "Company",
					"company_name": "Instacertify",
					"abbr": "IC",
					"default_currency": "INR",
					"country": "India",
					"chart_of_accounts": "Standard",
				}
			).insert(ignore_permissions=True)
		except Exception:
			# fallback: use existing first company
			pass
	company = frappe.db.get_value("Company", {"company_name": "Instacertify"}, "name") or frappe.db.get_single_value(
		"Global Defaults", "default_company"
	)
	if not company:
		company = frappe.db.get_value("Company", {}, "name")
	frappe.flags.ic_company = company
	return company


def _create_users():
	defs = [
		("admin.ops@instacertify.com", "Priya Sharma", ["IC Admin", "System Manager"]),
		("sales@instacertify.com", "Nikhil Verma", ["IC Sales Person", "Sales User", "Sales Manager"]),
		("ops@instacertify.com", "Ananya Reddy", ["IC Operations Manager", "Projects User"]),
		("ops.head@instacertify.com", "Rahul Mehta", ["IC Senior Operations", "Projects Manager"]),
	]
	created = {}
	for email, full_name, roles in defs:
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": full_name.split()[0],
					"last_name": " ".join(full_name.split()[1:]),
					"send_welcome_email": 0,
					"user_type": "System User",
					"new_password": "Instacertify@123",
				}
			)
			user.insert(ignore_permissions=True)
			for role in roles:
				user.add_roles(role)
		created[email] = email
	return created


def _create_consultants():
	consultants = [
		("Amit Khanna", "amit.khanna@referrals.in", "Mumbai"),
		("Sarah Williams", "sarah.w@globalrefs.com", "London"),
		("Vikram Patel", "vikram@indiamart-partner.in", "Ahmedabad"),
	]
	for name, email, city in consultants:
		if frappe.db.exists("Consultant Referral", {"consultant_name": name}):
			continue
		frappe.get_doc(
			{
				"doctype": "Consultant Referral",
				"consultant_name": name,
				"email": email,
				"city": city,
				"status": "Active",
			}
		).insert(ignore_permissions=True)


def _create_templates():
	templates = [
		{
			"template_name": "BIS Certification",
			"quotation_type": "Service",
			"service_name": "BIS Certification",
			"certification_type": "BIS CRS",
			"applicable_standard": "IS 616 / IS 13252",
			"estimated_timeline": "6-8 weeks",
			"scope_of_work": "<p>End-to-end BIS CRS certification support including documentation, testing coordination and portal filings.</p>",
			"deliverables": "<p>Application dossier, test coordination, grant of registration support.</p>",
			"cost_items": [
				{"cost_component": "Consulting Charges", "amount": 75000, "payment_destination": "Payable to Instacertify"},
				{"cost_component": "Government Fees", "amount": 32000, "payment_destination": "Payable Directly to Government", "is_passthrough": 1},
				{"cost_component": "Testing Charges", "amount": 45000, "payment_destination": "Payable to Instacertify"},
			],
		},
		{
			"template_name": "BIS Renewal",
			"quotation_type": "Service",
			"service_name": "BIS Renewal",
			"certification_type": "BIS Renewal",
			"applicable_standard": "Existing BIS Licence",
			"estimated_timeline": "3-4 weeks",
			"scope_of_work": "<p>Renewal documentation and authority liaison.</p>",
			"deliverables": "<p>Renewed registration support package.</p>",
			"cost_items": [
				{"cost_component": "Consulting Charges", "amount": 35000, "payment_destination": "Payable to Instacertify"},
				{"cost_component": "Government Fees", "amount": 15000, "payment_destination": "Payable Directly to Government", "is_passthrough": 1},
			],
		},
		{
			"template_name": "BIS Changeover",
			"quotation_type": "Service",
			"service_name": "BIS Standard Changeover",
			"certification_type": "BIS Changeover",
			"applicable_standard": "Updated IS Standard",
			"estimated_timeline": "5-7 weeks",
			"scope_of_work": "<p>Changeover assessment and re-testing coordination.</p>",
			"deliverables": "<p>Changeover completion pack.</p>",
			"cost_items": [
				{"cost_component": "Consulting Charges", "amount": 55000, "payment_destination": "Payable to Instacertify"},
			],
		},
		{
			"template_name": "Product Testing",
			"quotation_type": "Testing",
			"service_name": "Product Testing",
			"applicable_standard": "As applicable",
			"estimated_timeline": "2-4 weeks",
			"scope_of_work": "<p>Laboratory testing coordination and report delivery.</p>",
			"test_items": [
				{
					"product_name": "Sample Product",
					"test_name": "Safety Testing",
					"applicable_standard": "IEC 62368-1",
					"number_of_samples": 2,
					"testing_charges": 40000,
				}
			],
			"cost_items": [
				{"cost_component": "Testing Charges", "amount": 40000, "payment_destination": "Payable to Instacertify"},
				{"cost_component": "Laboratory Charges", "amount": 25000, "payment_destination": "Payable Directly to Laboratory", "is_passthrough": 1},
			],
		},
		{
			"template_name": "IEC Testing",
			"quotation_type": "Testing",
			"service_name": "IEC Testing",
			"applicable_standard": "IEC 62368-1",
			"estimated_timeline": "3-5 weeks",
			"scope_of_work": "<p>IEC safety testing package.</p>",
			"cost_items": [
				{"cost_component": "Testing Charges", "amount": 65000, "payment_destination": "Payable to Instacertify"},
			],
		},
		{
			"template_name": "CE Compliance",
			"quotation_type": "Service",
			"service_name": "CE Compliance",
			"certification_type": "CE",
			"applicable_standard": "EMC / LVD",
			"estimated_timeline": "4-6 weeks",
			"scope_of_work": "<p>CE technical file and compliance consulting.</p>",
			"cost_items": [
				{"cost_component": "Consulting Charges", "amount": 90000, "payment_destination": "Payable to Instacertify"},
			],
		},
		{
			"template_name": "Factory Inspection",
			"quotation_type": "Service",
			"service_name": "Factory Inspection",
			"estimated_timeline": "2 weeks",
			"scope_of_work": "<p>Factory audit preparation and inspection coordination.</p>",
			"cost_items": [
				{"cost_component": "Consulting Charges", "amount": 48000, "payment_destination": "Payable to Instacertify"},
			],
		},
		{
			"template_name": "Consulting Services",
			"quotation_type": "Service",
			"service_name": "Consulting Services",
			"estimated_timeline": "As scoped",
			"scope_of_work": "<p>Regulatory consulting retainer.</p>",
			"cost_items": [
				{"cost_component": "Consulting Charges", "amount": 25000, "payment_destination": "Payable to Instacertify"},
			],
		},
	]
	for t in templates:
		if frappe.db.exists("IC Quotation Template", t["template_name"]):
			continue
		cost_items = t.pop("cost_items", [])
		test_items = t.pop("test_items", [])
		doc = frappe.get_doc({"doctype": "IC Quotation Template", **t, "is_active": 1})
		for c in cost_items:
			doc.append("cost_items", c)
		for ti in test_items:
			doc.append("test_items", ti)
		doc.terms_and_conditions = frappe.db.get_single_value("IC Settings", "default_terms") or "<p>Standard terms apply.</p>"
		doc.force_majeure = frappe.db.get_single_value("IC Settings", "default_force_majeure") or "<p>Force majeure applies.</p>"
		doc.insert(ignore_permissions=True)


def _create_checklists():
	if frappe.db.exists("IC Document Checklist Template", "BIS Certification Documents"):
		return
	doc = frappe.get_doc(
		{
			"doctype": "IC Document Checklist Template",
			"template_name": "BIS Certification Documents",
			"service_name": "BIS Certification",
			"items": [
				{"document_name": "Company Registration", "category": "Customer Documents", "is_mandatory": 1},
				{"document_name": "Factory Details", "category": "Customer Documents", "is_mandatory": 1},
				{"document_name": "Product Specifications", "category": "Technical Documents", "is_mandatory": 1},
				{"document_name": "Technical Documents", "category": "Technical Documents", "is_mandatory": 1},
				{"document_name": "Authorization Letter", "category": "Applications", "is_mandatory": 1},
				{"document_name": "Test Reports", "category": "Test Reports", "is_mandatory": 0},
			],
		}
	)
	doc.insert(ignore_permissions=True)


def _create_laboratories():
	labs_data = [
		("NABL Tech Labs", "Gurugram", "India", "Haryana", [("Safety Testing", "IEC 62368-1", 28000, 42000), ("EMC Testing", "CISPR 32", 35000, 52000)]),
		("ElectroSafe Laboratories", "Bengaluru", "India", "Karnataka", [("IEC Testing", "IEC 60950", 30000, 48000), ("RF Testing", "ETSI EN 300", 40000, 65000)]),
		("Pacific Compliance Lab", "Singapore", "Singapore", "", [("CE EMC", "EN 55032", 1200, 1800), ("LVD Testing", "EN 62368", 900, 1400)]),
		("EuroTest GmbH", "Munich", "Germany", "", [("CE Compliance Pack", "EMC/LVD", 1500, 2300)]),
		("QualityMark Testing", "Pune", "India", "Maharashtra", [("Product Testing", "IS 616", 22000, 36000), ("Environmental", "IEC 60068", 18000, 29000)]),
	]
	labs = []
	for name, location, country, state, scopes in labs_data:
		existing = frappe.db.get_value("IC Laboratory", {"laboratory_name": name}, "name")
		if existing:
			labs.append(existing)
			continue
		doc = frappe.get_doc(
			{
				"doctype": "IC Laboratory",
				"laboratory_name": name,
				"location": location,
				"city": location,
				"country": country if frappe.db.exists("Country", country) else None,
				"state": state,
				"status": "Active",
				"address": f"{location} Industrial Area",
				"contact_person": "Lab Manager",
				"email": f"info@{name.lower().replace(' ', '')}.com",
				"phone": "+91-9876500000",
				"accreditation_details": "<p>ISO/IEC 17025 accredited laboratory.</p>",
				"accreditation_scope": "<p>Electrical safety, EMC and product testing as listed.</p>",
			}
		)
		for test_name, standard, purchase, selling in scopes:
			currency = "USD" if country != "India" else "INR"
			doc.append(
				"test_scopes",
				{
					"test_name": test_name,
					"applicable_standard": standard,
					"purchase_price": purchase,
					"selling_price": selling,
					"margin": selling - purchase,
					"currency": currency,
					"is_active": 1,
				},
			)
		doc.insert(ignore_permissions=True)
		labs.append(doc.name)
	return labs


def _create_customers():
	customers = [
		("ABC Electronics Pvt. Ltd.", "India", "Maharashtra", "INR", "27AABCU9603R1ZM"),
		("Shakti Appliances India", "India", "Gujarat", "INR", "24AADCS1234A1Z5"),
		("Nova Circuits Pvt Ltd", "India", "Karnataka", "INR", "29AABCN9988B1Z2"),
		("BrightLite Manufacturing", "India", "Tamil Nadu", "INR", "33AABCB5566C1Z9"),
		("Hindustan Power Gadgets", "India", "Delhi", "INR", "07AABCH7788D1Z1"),
		("GlobalTech Imports LLC", "United States", "California", "USD", None),
		("Nordic Home Devices AB", "Sweden", "", "USD", None),
		("Orient Trading Co.", "United Arab Emirates", "Dubai", "USD", None),
		("Pacific Brands Ltd", "Singapore", "", "USD", None),
		("Aurora Consumer Tech", "India", "Telangana", "INR", "36AABCA1122E1Z3"),
	]
	names = []
	for name, country, state, currency, gst in customers:
		if frappe.db.exists("Customer", name):
			names.append(name)
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": name,
				"customer_type": "Company",
				"customer_group": "Commercial",
				"territory": "All Territories" if frappe.db.exists("Territory", "All Territories") else frappe.db.get_value("Territory", {}, "name"),
				"default_currency": currency,
				"ic_country": country if frappe.db.exists("Country", country) else None,
				"ic_state": state,
				"ic_gst_number": gst,
				"ic_date_onboarded": add_days(today(), -60),
				"ic_company_size": "Medium",
				"ic_primary_currency": currency,
				"ic_factory_address": f"Factory Road, {state or country}",
			}
		)
		doc.insert(ignore_permissions=True)
		# Contact
		contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": name.split()[0],
				"last_name": "Contact",
				"email_id": f"contact@{name.lower().replace(' ', '').replace('.', '')[:20]}.com",
				"mobile_no": "+91-9800000000",
				"is_primary_contact": 1,
				"designation": "Purchase Manager",
				"links": [{"link_doctype": "Customer", "link_name": doc.name}],
			}
		)
		contact.insert(ignore_permissions=True)
		names.append(doc.name)
	return names


def _create_leads(users):
	leads = [
		("Ravi Kumar", "Pixel Power Systems", "Google", "Certification Request", "High", "India", "Karnataka"),
		("Meera Shah", "HomeSpark India", "IndiaMART", "Service Request", "Medium", "India", "Gujarat"),
		("John Carter", "Atlantic Gadgets Inc", "Direct Call", "Testing Request", "High", "United States", ""),
		("Chen Wei", "DragonByte Electronics", "Referral by Existing Customer", "Certification Request", "Medium", "Singapore", ""),
		("Sanjay Rao", "Deccan IoT Works", "Lead Generated", "Testing Request", "Low", "India", "Telangana"),
		("Fatima Al Hassan", "Gulf Import House", "Existing Customer", "Service Request", "High", "United Arab Emirates", "Dubai"),
		("Priya Nair", "Kerala Circuits", "Google", "Other", "Medium", "India", "Kerala"),
		("Thomas Berg", "Nordic Safety AB", "Referral by Existing Customer", "Certification Request", "High", "Sweden", ""),
		("Aisha Khan", "Metro Appliances", "Direct Call", "Service Request", "Medium", "India", "Delhi"),
		("Luis Ortega", "Andes Tech SA", "Other", "Testing Request", "Low", "United States", ""),
		("Neha Gupta", "SmartNest Pvt Ltd", "IndiaMART", "Certification Request", "Urgent", "India", "Uttar Pradesh"),
		("Omar Farouk", "Desert Brands", "Google", "Service Request", "Medium", "United Arab Emirates", ""),
		("Yuki Tanaka", "Sakura Imports", "Lead Generated", "Testing Request", "Medium", "Singapore", ""),
	]
	for person, company, source, category, priority, country, state in leads:
		if frappe.db.exists("Lead", {"company_name": company, "lead_name": person}):
			continue
		frappe.get_doc(
			{
				"doctype": "Lead",
				"lead_name": person,
				"company_name": company,
				"email_id": f"{person.lower().replace(' ', '.')}@example.com",
				"mobile_no": "+91-9811100000",
				"ic_alternate_phone": "+91-9811100001",
				"status": "Lead",
				"ic_lead_source_detail": source,
				"ic_request_category": category,
				"ic_priority": priority,
				"country": country if frappe.db.exists("Country", country) else None,
				"ic_state": state,
				"ic_company_size": "Small",
				"ic_expected_timeline": "4-6 weeks",
				"ic_estimated_value": 85000 if country == "India" else 2500,
				"ic_assigned_salesperson": users.get("sales@instacertify.com"),
				"ic_assigned_operations_manager": users.get("ops@instacertify.com"),
				"ic_remarks": f"Inbound enquiry for {category}",
			}
		).insert(ignore_permissions=True)


def _create_quotations(customers, users, labs):
	company = frappe.flags.ic_company
	# Ensure a selling item
	item = frappe.db.get_value("Item", {"item_name": "BIS Certification"}, "name") or frappe.db.get_value(
		"Item", {"is_sales_item": 1}, "name"
	)
	if not item:
		item_doc = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": "CONSULTING-SVC",
				"item_name": "Consulting Service",
				"item_group": "Services" if frappe.db.exists("Item Group", "Services") else "All Item Groups",
				"stock_uom": "Nos",
				"is_stock_item": 0,
				"is_sales_item": 1,
			}
		)
		item_doc.insert(ignore_permissions=True)
		item = item_doc.name

	defs = [
		(customers[0], "Service", "BIS Certification", "Accepted", "INR", 75000),
		(customers[1], "Service", "BIS Renewal", "Shared with Customer", "INR", 35000),
		(customers[2], "Testing", "IEC Testing", "Customer Review", "INR", 65000),
		(customers[5], "Service", "CE Compliance", "Accepted", "USD", 2200),
		(customers[6], "Testing", "Product Testing", "Ready to Share", "USD", 1800),
		(customers[3], "Multiple Products / Multiple Services", "BIS Certification", "Draft", "INR", 120000),
		(customers[7], "Service", "Consulting Services", "Changes Requested", "USD", 900),
		(customers[8], "Service", "Factory Inspection", "Internal Review", "USD", 1500),
		(customers[4], "Service", "BIS Standard Changeover", "Accepted", "INR", 55000),
	]
	created = []
	for customer, qtype, service, status, currency, amount in defs:
		title_key = f"{customer}-{service}-{status}"
		existing = frappe.db.get_value("Quotation", {"party_name": customer, "ic_service_name": service, "ic_workflow_status": status}, "name")
		if existing:
			created.append(existing)
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Quotation",
				"quotation_to": "Customer",
				"party_name": customer,
				"company": company,
				"transaction_date": today(),
				"valid_till": add_days(today(), 30),
				"order_type": "Sales",
				"currency": currency,
				"conversion_rate": 1 if currency == "INR" else 83,
				"selling_price_list": frappe.db.get_value("Price List", {"selling": 1}, "name"),
				"ic_quotation_type": qtype,
				"ic_service_name": service,
				"ic_certification_type": service,
				"ic_applicable_standard": "IS / IEC as applicable",
				"ic_estimated_timeline": "6-8 weeks",
				"ic_workflow_status": status,
				"ic_revision_number": 0,
				"ic_scope_of_work": f"<p>Scope for {service} for {customer}.</p>",
				"ic_deliverables": "<p>Final certificate / test report / consulting deliverable.</p>",
				"ic_terms_and_conditions": "<p>Payment 50% advance, 50% on completion. Validity 30 days.</p>",
				"ic_force_majeure": "<p>Standard force majeure clause applies.</p>",
				"items": [
					{
						"item_code": item,
						"item_name": service,
						"qty": 1,
						"rate": amount,
						"uom": "Nos",
					}
				],
			}
		)
		doc.append(
			"ic_cost_items",
			{
				"cost_component": "Consulting Charges",
				"description": service,
				"amount": amount * 0.6,
				"payment_destination": "Payable to Instacertify",
			},
		)
		doc.append(
			"ic_cost_items",
			{
				"cost_component": "Government Fees",
				"description": "Authority fees",
				"amount": amount * 0.25,
				"payment_destination": "Payable Directly to Government",
				"is_passthrough": 1,
			},
		)
		doc.append(
			"ic_cost_items",
			{
				"cost_component": "Testing Charges",
				"description": "Lab testing via Instacertify",
				"amount": amount * 0.15,
				"payment_destination": "Payable to Instacertify",
			},
		)
		if qtype in ("Testing", "Multiple Products / Multiple Services"):
			doc.append(
				"ic_test_items",
				{
					"product_name": "Smart Power Adapter" if customer == customers[0] else "Wireless Device",
					"test_name": "Safety Testing",
					"applicable_standard": "IEC 62368-1",
					"number_of_samples": 2,
					"sample_type": "Finished Goods",
					"laboratory": labs[0] if labs else None,
					"testing_timeline": "2-3 weeks",
					"testing_charges": amount * 0.15,
				},
			)
		if qtype == "Multiple Products / Multiple Services":
			doc.append(
				"ic_products",
				{
					"product_name": "Smart Power Adapter",
					"services": "BIS Certification, IEC Testing, Consulting",
					"applicable_standards": "IS 616, IEC 62368-1",
					"estimated_value": amount * 0.55,
				},
			)
			doc.append(
				"ic_products",
				{
					"product_name": "Wireless Device",
					"services": "BIS Certification, RF Testing, Consulting",
					"applicable_standards": "IS 13252, ETSI",
					"estimated_value": amount * 0.45,
				},
			)
		if status in ("Shared with Customer", "Customer Review", "Accepted", "Changes Requested"):
			doc.ic_share_token = secrets.token_urlsafe(16)
			doc.ic_shared_on = frappe.utils.now_datetime()
		if status == "Changes Requested":
			doc.ic_customer_remarks = "Please revise testing timeline and split government fees clearly."
		doc.insert(ignore_permissions=True)
		if status in ("Shared with Customer", "Customer Review", "Accepted", "Changes Requested"):
			try:
				doc.submit()
			except Exception:
				pass
		created.append(doc.name)
	return created


def _create_projects(customers, quotations, users):
	company = frappe.flags.ic_company
	defs = [
		("BIS Certification – Smart Power Adapter", customers[0], "Testing in Progress", 65, "High", "Laboratory Test Report", 19),
		("BIS Renewal – Kitchen Mixer", customers[1], "Customer Documents Pending", 15, "Medium", "Company Registration upload", 25),
		("IEC Testing – LED Driver", customers[2], "Application Submitted", 35, "High", "Authority acknowledgement", 12),
		("CE Compliance – Smart Plug", customers[5], "Report Available", 80, "High", "Share report with customer", 8),
		("BIS Changeover – Power Bank", customers[4], "Certificate Available", 92, "Medium", "Dispatch certificate", 5),
		("Factory Inspection – OEM Plant", customers[3], "Documents Under Review", 25, "Urgent", "Clarify factory layout", 10),
		("Product Testing – Wireless Earbuds", customers[8], "Sample Awaited", 40, "Medium", "Await sample courier", 14),
	]
	created = []
	for name, customer, stage, progress, priority, pending, days in defs:
		if frappe.db.exists("Project", {"project_name": name}):
			created.append(frappe.db.get_value("Project", {"project_name": name}, "name"))
			continue
		quotation = frappe.db.get_value("Quotation", {"party_name": customer}, "name")
		doc = frappe.get_doc(
			{
				"doctype": "Project",
				"project_name": name,
				"customer": customer,
				"company": company,
				"expected_start_date": add_days(today(), -20),
				"expected_end_date": add_days(today(), days),
				"priority": "High" if priority in ("High", "Urgent") else ("Low" if priority == "Low" else "Medium"),
				"status": "Open",
				"percent_complete": progress,
				"ic_project_stage": stage,
				"ic_priority": priority,
				"ic_progress_percentage": progress,
				"ic_pending_action": pending,
				"ic_deadline": add_days(today(), days),
				"ic_assigned_employee": users.get("ops@instacertify.com"),
				"ic_quotation": quotation,
				"ic_products_services": name.split("–")[0].strip(),
				"ic_deliverables": "Certificate / Test Report",
				"ic_testing_requirements": "As per quotation",
			}
		)
		doc.insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Task",
				"subject": pending,
				"project": doc.name,
				"status": "Working",
				"priority": "High" if priority in ("High", "Urgent") else ("Low" if priority == "Low" else "Medium"),
				"exp_end_date": add_days(today(), days),
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "IC Project Update",
				"project": doc.name,
				"subject": f"Progress update – {stage}",
				"project_stage": stage,
				"progress_percentage": progress,
				"pending_action": pending,
				"remarks": f"<p>Project is currently at <b>{stage}</b>.</p>",
				"working_hours": 3.5,
				"updated_by": users.get("ops@instacertify.com"),
			}
		).insert(ignore_permissions=True)
		created.append(doc.name)
	return created


def _create_testing(customers, projects, labs, users):
	defs = [
		(customers[0], projects[0] if projects else None, "Smart Power Adapter", "Safety Testing", "Testing in Progress"),
		(customers[2], projects[2] if len(projects) > 2 else None, "LED Driver", "IEC Testing", "Sample Received"),
		(customers[5], projects[3] if len(projects) > 3 else None, "Smart Plug", "EMC Testing", "Report Available"),
		(customers[8], projects[6] if len(projects) > 6 else None, "Wireless Earbuds", "RF Testing", "Sample Awaited"),
		(customers[4], projects[4] if len(projects) > 4 else None, "Power Bank", "Product Testing", "Report Shared with Customer"),
	]
	for customer, project, product, test, status in defs:
		title = f"{test} – {product}"
		if frappe.db.exists("IC Testing Request", {"title": title}):
			continue
		tr = frappe.get_doc(
			{
				"doctype": "IC Testing Request",
				"title": title,
				"customer": customer,
				"project": project,
				"product": product,
				"test_name": test,
				"applicable_standard": "IEC 62368-1",
				"number_of_samples": 2,
				"laboratory": labs[0] if labs else None,
				"testing_timeline": "2-3 weeks",
				"assigned_person": users.get("ops@instacertify.com"),
				"priority": "High",
				"status": status,
				"expected_completion": add_days(today(), 10),
			}
		)
		tr.insert(ignore_permissions=True)
		sample = frappe.get_doc(
			{
				"doctype": "IC Sample Tracking",
				"customer": customer,
				"project": project,
				"testing_request": tr.name,
				"laboratory": labs[0] if labs else None,
				"sample_description": f"{product} engineering samples",
				"quantity": 2,
				"sample_condition": "Good",
				"status": status if status.startswith("Sample") or status.startswith("Testing") or status.startswith("Report") else "Sample Awaited",
				"received_by": users.get("ops@instacertify.com"),
				"sample_received_date": today() if status != "Sample Awaited" else None,
			}
		)
		sample.insert(ignore_permissions=True)


def _create_document_requests(customers, projects, users):
	if frappe.db.exists("IC Document Request", {"title": "BIS Docs – ABC Electronics"}):
		return
	doc = frappe.get_doc(
		{
			"doctype": "IC Document Request",
			"title": "BIS Docs – ABC Electronics",
			"customer": customers[0],
			"project": projects[0] if projects else None,
			"checklist_template": "BIS Certification Documents"
			if frappe.db.exists("IC Document Checklist Template", "BIS Certification Documents")
			else None,
			"assigned_to": users.get("ops@instacertify.com"),
			"status": "Sent to Customer",
			"share_token": secrets.token_urlsafe(16),
			"sent_on": frappe.utils.now_datetime(),
			"items": [
				{"document_name": "Company Registration", "category": "Customer Documents", "is_mandatory": 1, "status": "Uploaded"},
				{"document_name": "Factory Details", "category": "Customer Documents", "is_mandatory": 1, "status": "Pending"},
				{"document_name": "Product Specifications", "category": "Technical Documents", "is_mandatory": 1, "status": "Pending"},
				{"document_name": "Authorization Letter", "category": "Applications", "is_mandatory": 1, "status": "Pending"},
			],
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.get_doc(
		{
			"doctype": "IC Project Record",
			"subject": "Customer committed to courier samples by Friday",
			"record_type": "Important Commitment",
			"customer": customers[0],
			"project": projects[0] if projects else None,
			"content": "<p>Customer confirmed sample dispatch.</p>",
			"recorded_by": users.get("ops@instacertify.com"),
		}
	).insert(ignore_permissions=True)


def _create_employees_and_assets(users):
	company = frappe.flags.ic_company
	# Department / Designation
	if not frappe.db.exists("Department", {"department_name": "Operations", "company": company}):
		try:
			frappe.get_doc(
				{"doctype": "Department", "department_name": "Operations", "company": company}
			).insert(ignore_permissions=True)
		except Exception:
			pass
	if not frappe.db.exists("Designation", "Operations Manager"):
		try:
			frappe.get_doc({"doctype": "Designation", "designation_name": "Operations Manager"}).insert(
				ignore_permissions=True
			)
		except Exception:
			pass

	emp_defs = [
		("EMP-IC-0001", "Nikhil Verma", users.get("sales@instacertify.com"), "Sales Person"),
		("EMP-IC-0002", "Ananya Reddy", users.get("ops@instacertify.com"), "Operations Manager"),
		("EMP-IC-0003", "Rahul Mehta", users.get("ops.head@instacertify.com"), "Senior Operations"),
		("EMP-IC-0004", "Priya Sharma", users.get("admin.ops@instacertify.com"), "Admin"),
	]
	for emp_number, emp_name, user_id, designation in emp_defs:
		if frappe.db.exists("Employee", {"employee_name": emp_name}):
			continue
		# Employee naming may vary
		try:
			emp = frappe.get_doc(
				{
					"doctype": "Employee",
					"first_name": emp_name.split()[0],
					"last_name": " ".join(emp_name.split()[1:]),
					"employee_name": emp_name,
					"status": "Active",
					"company": company,
					"date_of_joining": add_days(today(), -365),
					"user_id": user_id,
					"designation": "Operations Manager"
					if frappe.db.exists("Designation", "Operations Manager")
					else None,
					"gender": "Female" if emp_name.split()[0] in ("Ananya", "Priya") else "Male",
					"date_of_birth": "1992-01-15",
				}
			)
			emp.insert(ignore_permissions=True)
			# Joining letter
			jl = frappe.get_doc(
				{
					"doctype": "IC Joining Letter",
					"employee": emp.name,
					"joining_date": emp.date_of_joining,
					"letter_content": f"<p>Dear {emp_name},</p><p>Welcome to Instacertify. We are pleased to appoint you as {designation}.</p>",
					"verification_code": secrets.token_hex(4).upper(),
				}
			)
			jl.insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Employee {emp_name}")

	# Holiday list
	if not frappe.db.exists("Holiday List", "Instacertify 2026"):
		try:
			hl = frappe.get_doc(
				{
					"doctype": "Holiday List",
					"holiday_list_name": "Instacertify 2026",
					"from_date": "2026-01-01",
					"to_date": "2026-12-31",
					"holidays": [
						{"holiday_date": "2026-01-26", "description": "Republic Day"},
						{"holiday_date": "2026-08-15", "description": "Independence Day"},
						{"holiday_date": "2026-10-02", "description": "Gandhi Jayanti"},
					],
				}
			)
			hl.insert(ignore_permissions=True)
		except Exception:
			pass

	# Assets
	if frappe.db.exists("DocType", "Asset") and not frappe.db.exists("Asset", {"asset_name": "Dell Latitude Laptop – Ops"}):
		try:
			# Need item and asset category
			if not frappe.db.exists("Asset Category", "IT Equipment"):
				frappe.get_doc(
					{
						"doctype": "Asset Category",
						"asset_category_name": "IT Equipment",
						"accounts": [
							{
								"company_name": company,
								"fixed_asset_account": frappe.db.get_value(
									"Account", {"account_type": "Fixed Asset", "company": company, "is_group": 0}, "name"
								),
							}
						],
					}
				).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Asset demo")


def _seed_workdesk_and_hr(users, projects=None):
	"""Tasks, calendar events, salary slips & employment docs for the home workdesk."""
	from frappe.utils import get_datetime

	# Link Administrator to a preview employee so Home HR panel works in desk
	emp_name = frappe.db.get_value("Employee", {"user_id": "Administrator", "status": "Active"}, "name")
	if not emp_name:
		try:
			if not frappe.db.exists("Employee", {"employee_name": "Admin Preview"}):
				company = frappe.flags.ic_company
				preview = frappe.get_doc(
					{
						"doctype": "Employee",
						"first_name": "Admin",
						"last_name": "Preview",
						"employee_name": "Admin Preview",
						"status": "Active",
						"company": company,
						"date_of_joining": add_days(today(), -400),
						"user_id": "Administrator",
						"gender": "Male",
						"date_of_birth": "1990-05-01",
						"designation": "Operations Manager"
						if frappe.db.exists("Designation", "Operations Manager")
						else None,
					}
				)
				preview.insert(ignore_permissions=True)
				emp_name = preview.name
			else:
				emp_name = frappe.db.get_value("Employee", {"employee_name": "Admin Preview"}, "name")
				frappe.db.set_value("Employee", emp_name, "user_id", "Administrator")
		except Exception:
			frappe.log_error(frappe.get_traceback(), "link Administrator employee")
			emp_name = frappe.db.get_value("Employee", {"status": "Active"}, "name")
	if not emp_name:
		return

	# Ensure joining letter for the preview employee
	if frappe.db.exists("DocType", "IC Joining Letter") and not frappe.db.exists(
		"IC Joining Letter", {"employee": emp_name}
	):
		try:
			e = frappe.get_doc("Employee", emp_name)
			frappe.get_doc(
				{
					"doctype": "IC Joining Letter",
					"employee": emp_name,
					"joining_date": e.date_of_joining or today(),
					"designation": e.designation,
					"department": e.department,
					"letter_content": f"<p>Dear {e.employee_name},</p><p>Welcome to Instacertify.</p>",
					"verification_code": secrets.token_hex(4).upper(),
				}
			).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "joining letter seed")

	# Salary slips + employment documents
	if frappe.db.exists("DocType", "IC Employee Document"):
		doc_defs = [
			("Salary Slip", "Salary Slip – July 2026", add_days(today(), -30)),
			("Salary Slip", "Salary Slip – August 2026", today()),
			("Offer Letter", "Offer Letter", add_days(today(), -400)),
			("Contract", "Employment Contract", add_days(today(), -400)),
			("ID Proof", "Aadhaar / ID copy", add_days(today(), -390)),
		]
		for dtype, title, issue in doc_defs:
			if frappe.db.exists("IC Employee Document", {"employee": emp_name, "document_title": title}):
				continue
			try:
				frappe.get_doc(
					{
						"doctype": "IC Employee Document",
						"employee": emp_name,
						"document_title": title,
						"document_type": dtype,
						"issue_date": issue,
					}
				).insert(ignore_permissions=True)
			except Exception:
				frappe.log_error(frappe.get_traceback(), f"employee doc {title}")

	owner = "Administrator"

	# Open tasks for workdesk
	task_defs = [
		("Follow up lead contact calls", "High", add_days(today(), -1), "Open"),
		("Prepare quotation revision for customer", "Medium", today(), "Working"),
		("Upload pending project documents", "Medium", add_days(today(), 3), "Open"),
		("Review lab testing turnaround", "Low", add_days(today(), 7), "Open"),
	]
	for subject, priority, due, status in task_defs:
		if frappe.db.exists("Task", {"subject": subject}):
			continue
		try:
			doc = frappe.get_doc(
				{
					"doctype": "Task",
					"subject": subject,
					"status": status,
					"priority": priority,
					"exp_end_date": due,
				}
			)
			doc.insert(ignore_permissions=True)
			frappe.db.set_value("Task", doc.name, "owner", owner)
			# Assign so _assign filter matches
			try:
				from frappe.desk.form.assign_to import add as assign_add

				assign_add({"assign_to": [owner], "doctype": "Task", "name": doc.name, "description": subject})
			except Exception:
				pass
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"task seed {subject}")

	# Calendar events (next 14 days)
	event_defs = [
		("Weekly sales stand-up", 1, 10),
		("Customer site visit – BIS consult", 2, 14),
		("Lab handover review", 5, 11),
		("HR document verification", 8, 15),
	]
	for subject, day_offset, hour in event_defs:
		if frappe.db.exists("Event", {"subject": subject}):
			continue
		try:
			starts = get_datetime(f"{add_days(today(), day_offset)} {hour:02d}:00:00")
			ends = get_datetime(f"{add_days(today(), day_offset)} {hour+1:02d}:00:00")
			ev = frappe.get_doc(
				{
					"doctype": "Event",
					"subject": subject,
					"event_type": "Public",
					"starts_on": starts,
					"ends_on": ends,
					"status": "Open",
					"send_reminder": 0,
					"event_participants": [
						{"reference_doctype": "User", "reference_docname": owner},
					],
				}
			)
			ev.insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"event seed {subject}")

	# Ensure a few leads are owned by Administrator for My Leads panel
	try:
		leads = frappe.get_all(
			"Lead",
			filters={"status": ["not in", ["Converted", "Do Not Contact"]]},
			fields=["name"],
			limit_page_length=3,
			order_by="modified desc",
		)
		for lead in leads:
			frappe.db.set_value("Lead", lead.name, "lead_owner", owner, update_modified=False)
	except Exception:
		pass


def _seed_helpdesk_tickets(customers, projects=None, users=None):
	"""Sample complaints and queries for Helpdesk."""
	if not frappe.db.exists("DocType", "Helpdesk Ticket"):
		return
	customer_name = None
	if customers:
		customer_name = customers[0] if isinstance(customers[0], str) else customers[0].get("name")
	if not customer_name:
		customer_name = frappe.db.get_value("Customer", {}, "name")
	project_name = None
	if projects:
		project_name = projects[0] if isinstance(projects[0], str) else getattr(projects[0], "name", None) or (
			projects[0].get("name") if isinstance(projects[0], dict) else None
		)
	if not project_name:
		project_name = frappe.db.get_value("Project", {"customer": customer_name}, "name") if customer_name else None

	defs = [
		{
			"subject": "Delay in certificate dispatch",
			"ticket_type": "Certification Delay",
			"priority": "High",
			"status": "Open",
			"description": "<p>Customer reports certificate not received after project completion.</p>",
		},
		{
			"subject": "Wrong GST on invoice",
			"ticket_type": "Billing",
			"priority": "Urgent",
			"status": "In Progress",
			"description": "<p>Invoice shows CGST+SGST instead of IGST for interstate supply.</p>",
		},
		{
			"subject": "Sample status unclear",
			"ticket_type": "Sample / Lab",
			"priority": "Medium",
			"status": "Waiting on Customer",
			"description": "<p>Need POD copy for sample courier dispatched last week.</p>",
		},
		{
			"subject": "General query on BIS timeline",
			"ticket_type": "Query",
			"priority": "Low",
			"status": "Open",
			"description": "<p>Customer asked for typical BIS certification turnaround.</p>",
		},
	]
	for d in defs:
		if frappe.db.exists("Helpdesk Ticket", {"subject": d["subject"]}):
			continue
		try:
			doc = frappe.get_doc(
				{
					"doctype": "Helpdesk Ticket",
					**d,
					"customer": customer_name,
					"project": project_name if d["ticket_type"] != "Billing" else None,
					"channel": "Phone",
					"raised_by": "Administrator",
					"assigned_to": "Administrator",
				}
			)
			doc.insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"helpdesk seed {d['subject']}")
