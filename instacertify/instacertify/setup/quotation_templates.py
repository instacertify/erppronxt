# Copyright (c) Instacertify
"""Seed editable quotation templates from Instacertify Labs quote formats."""

from __future__ import annotations

import frappe


BIS_ABOUT = """<p>BIS CRS (Compulsory Registration Scheme) is a mandatory certification issued by the Bureau of Indian
Standards for specified electronic and IT products sold in India. Manufacturers must test products in BIS-recognized
laboratories and register them with BIS before sale. CRS ensures product safety, quality, and compliance with
Indian standards, allowing the use of the Standard Mark on certified products.</p>"""

BIS_STANDARD = """<p><b>Standard Applicable:</b> IS 10322 (Part 5/Sec 2):2026, as specified under the applicable requirements of the BIS
Compulsory Registration Scheme (CRS) for the relevant product category.</p>"""

BIS_PROCESS = """<p><b>Process for BIS CRS Registration</b></p>
<p><b>Step 1 – Documentation Review &amp; Application Preparation</b><br>
Collection, verification, and preparation of all required documents as per BIS CRS requirements.</p>
<p><b>Step 2 – BIS Portal Registration</b><br>
Creation of manufacturer profile and application setup on the BIS online portal.</p>
<p><b>Step 3 – Product Testing</b><br>
Testing of the product at a BIS-recognized laboratory and obtaining the test report as per the applicable Indian Standard.</p>
<p><b>Step 4 – Application Submission</b><br>
Submission of the BIS CRS application along with supporting documents and test reports through the BIS portal.</p>
<p><b>Step 5 – BIS Scrutiny &amp; Evaluation</b><br>
Review and examination of the application by BIS officials for compliance with the applicable requirements.</p>
<p><b>Step 6 – Grant of Registration</b><br>
Issuance of BIS CRS Registration Certificate upon successful verification and approval by BIS.</p>"""

BIS_VALIDITY = """<p><b>Validity of BIS CRS Registration</b></p>
<p>The BIS CRS Registration is generally granted with a validity period of 1 (One) years from the date of issuance and
may be renewed for subsequent periods of 1 (One) years, subject to compliance with the applicable BIS
requirements and payment of prescribed renewal fees.</p>"""

BIS_COMMERCIALS_NOTES = """<p><b>Notes:</b></p>
<ul>
<li>The above charges are applicable for BIS CRS registration under IS 10322 (Part 5/Sec 2):2026.</li>
<li>BIS government fees, sample transportation charges, and any additional laboratory charges, if applicable, shall be charged extra at actuals.</li>
<li>GST @ 18% shall be applicable as per prevailing Government taxation norms.</li>
</ul>"""

BIS_PAYMENT = """<ul>
<li>Professional Consultancy Charges shall be payable upon confirmation of the project and commencement of consultancy services.</li>
<li>BIS Government Fees and Product Testing Charges shall be payable in advance and may be deposited directly with the respective authorities/laboratories or through InstaCertify, as applicable.</li>
<li>Any additional expenses arising due to changes in BIS regulations, product modifications, additional testing requirements, document revisions, or expansion of project scope shall be communicated and charged separately upon mutual consent.</li>
<li>GST @ 18% shall be applicable on Professional Consultancy Charges as per prevailing Government taxation regulations.</li>
<li>BIS Government Fees and Laboratory Testing Charges are subject to revision by the concerned authorities and shall be charged on an actual basis.</li>
<li>The timelines for registration are subject to the submission of complete and accurate documentation by the applicant and the processing time of BIS and the testing laboratory.</li>
<li>Grant of BIS CRS Registration is solely at the discretion of the Bureau of Indian Standards (BIS) and subject to successful compliance with all applicable regulatory requirements.</li>
<li>This quotation is valid for 90 days from the date of issuance unless otherwise specified.</li>
</ul>"""

BIS_TIMELINE = """<p><b>Estimated Timeline for BIS CRS Registration</b></p>
<p><b>Stage 1 – Documentation, Portal Registration &amp; Product Testing (Steps 1 to 3)</b><br>
Estimated Timeline: 10–15 Working Days</p>
<p><b>Stage 2 – Application Submission, BIS Scrutiny &amp; Grant of Registration (Steps 4 to 6)</b><br>
Estimated Timeline: 10–15 Working Days</p>
<p><b>Overall Project Duration</b><br>
The complete BIS CRS Registration process is generally completed within 20–25 Working Days, subject to timely
submission of documents, successful product testing, and approval by BIS.</p>
<p><b>Note:</b></p>
<ul>
<li>The above timeline is indicative and may vary depending on the product category, laboratory testing schedule, and BIS processing time.</li>
<li>Timelines for applications involving manufacturers located in China may differ significantly due to additional regulatory requirements and approval procedures; therefore, the above timeline should not be considered applicable for such cases.</li>
</ul>"""

BIS_SAMPLE = """<p>One (01) product sample with complete accessories, packaging, technical specifications, and user manual shall be
required for testing at a BIS-recognized laboratory. Additional samples, if required, shall be provided by the applicant.</p>"""

BIS_DOCUMENTS = """<p><b>Documents Required for BIS CRS Registration</b></p>
<ol>
<li>Manufacturer’s company profile, contact details, and authorized person’s information.</li>
<li>Technical Data Sheet (TDS) of the product.</li>
<li>Manufacturer’s Business Registration Certificate, Certificate of Incorporation, Trade Licence, MSME/Udyam Certificate, or equivalent document for verification of company name, address, and business activities.</li>
<li>Product Technical Specification Sheet and/or User Manual.</li>
<li>Additional technical certification reports, if available (e.g., UL, CE, RoHS, CB Report, etc.). Submission of such reports is optional but may facilitate the testing and evaluation process.</li>
<li>Product Marking Label/Nameplate artwork showing model number, brand name, ratings, and other applicable marking details.</li>
<li>Trademark Registration Certificate or Trademark Application Number (if the product is marketed under a registered brand/trademark).</li>
<li>Importer’s Company Registration Documents (Certificate of Incorporation, MSME/Udyam Certificate, GST Registration, etc.), where applicable.</li>
<li>Identity Proof and Address Proof of the Brand Owner, Authorized Indian Representative (AIR), or Indian Importer.</li>
<li>MSME/Udyam Registration Certificate (for Indian Manufacturers, if applicable).</li>
<li>Authorization Letter/Agreement in favor of the Authorized Indian Representative (AIR), wherever required.</li>
</ol>
<p><b>Note:</b><br>
In cases where the foreign manufacturer does not have a representative or office in India, InstaCertify can assist in
providing Authorized Indian Representative (AIR) services, subject to applicable terms and conditions.</p>"""

BIS_CANCEL = """<p>Testing fees are payable in advance and are non-refundable once samples have been submitted or testing has
commenced. Government fees may be refunded only if they have not been deposited with the relevant authority.
Consultancy fees are charged based on the work completed and are non-refundable once services have been
rendered. Any eligible refund request must be submitted to Instacertify in writing within 7 working days of payment.</p>"""

BIS_FORCE = """<p>Instacertify Labs Pvt. Ltd. shall not be liable for any delay or failure in performing its obligations due to
circumstances beyond its reasonable control, including but not limited to natural disasters, acts of government,
regulatory changes, strikes, pandemics, war, civil unrest, transportation disruptions, laboratory delays, or
certification authority actions. Any affected timelines shall be extended accordingly, and both parties shall make
reasonable efforts to minimize the impact of such events</p>"""

BIS_CONF = """<p>Instacertify Labs Pvt. Ltd. shall maintain strict confidentiality of all documents, technical information, business data,
and records shared by the Client. Such information will be used solely for the purpose of providing the agreed
services and will not be disclosed to any third party except where required by law, regulatory authorities,
laboratories, or certification bodies. Reasonable measures shall be implemented to ensure data security and protection</p>"""


def ensure_quotation_templates():
	_ensure_bis_crs_template()
	_ensure_starter_templates()
	_ensure_five_per_major_category()
	_migrate_legacy_service_type()


def _revenue_row(particulars: str, amount: float, display: str | None = None) -> dict:
	return {
		"cost_component": "Consulting Charges",
		"particulars": particulars,
		"amount": amount,
		"charges_display": display or f"₹ {amount:,.0f}/-",
		"payment_destination": "Payable to Instacertify",
		"is_passthrough": 0,
	}


def _passthrough_row(
	component: str,
	particulars: str,
	amount: float,
	destination: str = "Payable Directly to Government",
	display: str | None = None,
) -> dict:
	return {
		"cost_component": component,
		"particulars": particulars,
		"amount": amount,
		"charges_display": display or "At actuals",
		"payment_destination": destination,
		"is_passthrough": 1,
	}


def _ensure_five_per_major_category():
	"""Guarantee ≥5 active templates in each major category for create-quote dropdowns."""
	catalog = {
		"Consulting": [
			(
				"CDSCO Medical Device Consultancy",
				{
					"service_family": "CDSCO",
					"service_name": "CDSCO Medical Device Consultancy",
					"certification_type": "CDSCO",
					"applicable_standard": "MDR 2017",
					"estimated_timeline": "6–10 weeks",
					"validity_days": 90,
					"about_service": "<p>CDSCO medical device registration consultancy covering classification, documentation, and portal filings.</p>",
				},
				[
					_revenue_row("Consultancy Charges", 45000),
					_passthrough_row("Government Fees", "CDSCO / Authority Fees", 15000),
				],
			),
			(
				"BEE Star Label Consultancy",
				{
					"service_family": "BEE",
					"service_name": "BEE Star Label Consultancy",
					"certification_type": "BEE",
					"applicable_standard": "BEE Star Label",
					"estimated_timeline": "4–6 weeks",
					"validity_days": 90,
					"about_service": "<p>Bureau of Energy Efficiency star labelling consultancy for covered appliances.</p>",
				},
				[
					_revenue_row("Consultancy Charges", 28000),
					_passthrough_row("Government Fees", "BEE Fees", 8000),
				],
			),
		],
		"Testing": [
			(
				"RF / Wireless Testing Package",
				{
					"service_family": "RF",
					"service_name": "RF / Wireless Testing",
					"subject": "Testing",
					"applicable_standard": "ETSI / FCC RF",
					"estimated_timeline": "5–8 working days",
					"validity_days": 30,
					"about_testing": "<p>RF conducted and radiated testing package for wireless products.</p>",
				},
				[
					_revenue_row("Testing Coordination Charges", 12000, "₹ 12,000/-"),
					_passthrough_row(
						"Laboratory Charges",
						"Lab Testing Fees",
						85000,
						"Payable Directly to Laboratory",
						"₹ 85,000/-",
					),
				],
				[
					{
						"product_name": "Wireless Product",
						"test_name": "RF Conducted Spurious",
						"applicable_standard": "ETSI EN 300 328",
						"number_of_samples": 2,
						"per_unit_charges": 25000,
						"testing_charges": 50000,
					}
				],
			),
			(
				"RoHS Chemical Testing",
				{
					"service_family": "RoHS",
					"service_name": "RoHS Chemical Testing",
					"subject": "Testing",
					"applicable_standard": "RoHS Directive",
					"estimated_timeline": "4–6 working days",
					"validity_days": 30,
					"about_testing": "<p>Restricted substances screening for RoHS compliance.</p>",
				},
				[
					_passthrough_row(
						"Laboratory Charges",
						"RoHS Lab Fees",
						18000,
						"Payable Directly to Laboratory",
						"₹ 18,000/-",
					),
				],
				[
					{
						"product_name": "Product Sample",
						"test_name": "RoHS Screening",
						"applicable_standard": "RoHS",
						"number_of_samples": 1,
						"per_unit_charges": 18000,
						"testing_charges": 18000,
					}
				],
			),
		],
		"Renewal": [
			(
				"TEC Renewal Consultancy",
				{
					"service_family": "TEC Renewal",
					"service_name": "TEC Approval Renewal",
					"certification_type": "TEC Renewal",
					"estimated_timeline": "3–5 weeks",
					"validity_days": 90,
					"about_service": "<p>Renewal support for TEC / MTCTE approvals nearing expiry.</p>",
				},
				[
					_revenue_row("Renewal Consultancy Charges", 18000),
					_passthrough_row("Government Fees", "TEC Renewal Fees", 7000),
				],
			),
			(
				"WPC ETA Renewal",
				{
					"service_family": "WPC Renewal",
					"service_name": "WPC ETA Renewal",
					"certification_type": "WPC ETA Renewal",
					"estimated_timeline": "2–4 weeks",
					"validity_days": 90,
					"about_service": "<p>WPC ETA renewal filings and liaison.</p>",
				},
				[
					_revenue_row("Renewal Consultancy Charges", 12000),
					_passthrough_row("Government Fees", "WPC Fees", 4000),
				],
			),
			(
				"EPR Registration Renewal",
				{
					"service_family": "EPR Renewal",
					"service_name": "EPR Registration Renewal",
					"certification_type": "EPR Renewal",
					"estimated_timeline": "2–3 weeks",
					"validity_days": 90,
					"about_service": "<p>EPR registration renewal and annual return support.</p>",
				},
				[
					_revenue_row("Renewal Consultancy Charges", 22000),
					_passthrough_row("Government Fees", "EPR Authority Fees", 6000),
				],
			),
		],
		"Other": [
			(
				"General Professional Services",
				{
					"service_family": "General",
					"service_name": "General Professional Services",
					"certification_type": "Other",
					"estimated_timeline": "As agreed",
					"validity_days": 60,
					"about_service": "<p>Flexible professional services quotation for scoped advisory work.</p>",
				},
				[_revenue_row("Professional Charges", 25000)],
			),
			(
				"Documentation & Training Pack",
				{
					"service_family": "Training",
					"service_name": "Documentation & Training Pack",
					"certification_type": "Other",
					"estimated_timeline": "1–2 weeks",
					"validity_days": 60,
					"about_service": "<p>Compliance documentation packs and team training sessions.</p>",
				},
				[_revenue_row("Training & Documentation Charges", 35000)],
			),
			(
				"Gap Assessment Audit",
				{
					"service_family": "Audit",
					"service_name": "Gap Assessment Audit",
					"certification_type": "Other",
					"estimated_timeline": "1–3 weeks",
					"validity_days": 45,
					"about_service": "<p>On-site or remote gap assessment against target standards.</p>",
				},
				[_revenue_row("Audit / Assessment Charges", 40000)],
			),
			(
				"Sample Logistics Coordination",
				{
					"service_family": "Logistics",
					"service_name": "Sample Logistics Coordination",
					"certification_type": "Other",
					"estimated_timeline": "As required",
					"validity_days": 30,
					"about_service": "<p>Coordination of sample pickup, packing, and lab dispatch.</p>",
				},
				[
					_revenue_row("Coordination Charges", 5000),
					_passthrough_row(
						"Other Charges",
						"Courier / Freight (actuals)",
						3000,
						"Payable to Third Party",
						"At actuals",
					),
				],
			),
			(
				"Custom Compliance Scope",
				{
					"service_family": "Custom",
					"service_name": "Custom Compliance Scope",
					"certification_type": "Other",
					"estimated_timeline": "Scoped per SOW",
					"validity_days": 90,
					"about_service": "<p>Blank-slate template for custom multi-scope compliance engagements.</p>",
				},
				[
					_revenue_row("Professional Charges", 50000),
					_passthrough_row("Government Fees", "Authority Fees (if any)", 10000),
				],
			),
		],
	}

	for qtype, entries in catalog.items():
		for entry in entries:
			name = entry[0]
			values = dict(entry[1])
			values.update({"quotation_type": qtype, "is_active": 1})
			cost_rows = entry[2] if len(entry) > 2 else None
			test_rows = entry[3] if len(entry) > 3 else None
			_upsert_template(name, values, cost_rows, test_rows)

	# Top-up: if a category still has <5, clone numbered generics
	for qtype in ("Consulting", "Testing", "Renewal", "Other"):
		count = frappe.db.count("IC Quotation Template", {"quotation_type": qtype, "is_active": 1})
		n = 1
		while count < 5 and n <= 10:
			name = f"{qtype} Library Template {n}"
			if not frappe.db.exists("IC Quotation Template", name):
				values = {
					"quotation_type": qtype,
					"service_family": qtype,
					"is_active": 1,
					"service_name": name,
					"estimated_timeline": "As agreed",
					"validity_days": 60,
					"about_service": f"<p>Starter {qtype} template — edit headings and commercials after selection.</p>",
				}
				if qtype == "Testing":
					values["about_testing"] = (
						f"<p>Starter {qtype} testing narrative — edit as needed.</p>"
					)
					values["subject"] = "Testing"
				_upsert_template(
					name,
					values,
					[
						_revenue_row(f"{qtype} Professional Charges", 15000 + n * 1000),
						_passthrough_row(
							"Laboratory Charges" if qtype == "Testing" else "Government Fees",
							"External fees (pass-through)",
							5000,
							"Payable Directly to Laboratory"
							if qtype == "Testing"
							else "Payable Directly to Government",
						),
					],
				)
				count += 1
			n += 1


def _migrate_legacy_service_type():
	"""Map old Service / Multi templates into the four major categories."""
	frappe.db.sql(
		"""
		UPDATE `tabIC Quotation Template`
		SET quotation_type = 'Consulting'
		WHERE quotation_type IN ('Service', 'Multiple Products / Multiple Services')
		  AND IFNULL(service_family, '') NOT LIKE '%%Renewal%%'
		  AND IFNULL(template_name, '') NOT LIKE '%%Renewal%%'
		  AND IFNULL(template_name, '') NOT LIKE '%%Test%%'
		"""
	)
	frappe.db.sql(
		"""
		UPDATE `tabIC Quotation Template`
		SET quotation_type = 'Renewal'
		WHERE quotation_type IN ('Service', 'Consulting', 'Other')
		  AND (
		    IFNULL(service_family, '') LIKE '%%Renewal%%'
		    OR IFNULL(template_name, '') LIKE '%%Renewal%%'
		  )
		"""
	)
	frappe.db.sql(
		"""
		UPDATE `tabIC Quotation Template`
		SET quotation_type = 'Other'
		WHERE quotation_type = 'Multiple Products / Multiple Services'
		"""
	)


def _upsert_template(name: str, values: dict, cost_rows: list | None = None, test_rows: list | None = None):
	if frappe.db.exists("IC Quotation Template", name):
		doc = frappe.get_doc("IC Quotation Template", name)
		doc.update(values)
		doc.set("cost_items", [])
		for row in cost_rows or []:
			doc.append("cost_items", row)
		doc.set("test_items", [])
		for row in test_rows or []:
			doc.append("test_items", row)
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc({"doctype": "IC Quotation Template", "template_name": name, **values})
		for row in cost_rows or []:
			doc.append("cost_items", row)
		for row in test_rows or []:
			doc.append("test_items", row)
		doc.insert(ignore_permissions=True)


def _ensure_starter_templates():
	"""Multiple consulting / testing / renewal starter templates."""
	# Consulting
	_upsert_template(
		"TEC Approval Consultancy",
		{
			"quotation_type": "Consulting",
			"service_family": "TEC",
			"is_active": 1,
			"service_name": "TEC Approval Consultancy",
			"certification_type": "TEC",
			"applicable_standard": "TEC MTCTE",
			"estimated_timeline": "4–6 weeks",
			"validity_days": 90,
			"about_service": "<p>TEC / MTCTE consultancy covering documentation, testing coordination, and portal filings for telecom products.</p>",
			"payment_terms": "<ul><li>Consultancy charges payable on confirmation.</li><li>Government / lab fees payable in advance at actuals.</li></ul>",
		},
		[
			{
				"cost_component": "Consulting Charges",
				"particulars": "Consultancy Charges",
				"amount": 25000,
				"charges_display": "₹ 25,000/-",
				"payment_destination": "Payable to Instacertify",
			},
			{
				"cost_component": "Government Fees",
				"particulars": "Government / Authority Fees",
				"amount": 10000,
				"charges_display": "At actuals",
				"payment_destination": "Payable Directly to Government",
				"is_passthrough": 1,
			},
		],
	)
	_upsert_template(
		"WPC ETA Consultancy",
		{
			"quotation_type": "Consulting",
			"service_family": "WPC",
			"is_active": 1,
			"service_name": "WPC ETA Consultancy",
			"certification_type": "WPC ETA",
			"applicable_standard": "WPC Guidelines",
			"estimated_timeline": "3–5 weeks",
			"validity_days": 90,
			"about_service": "<p>Wireless Planning & Coordination (WPC) ETA consultancy for RF / wireless products.</p>",
		},
		[
			{
				"cost_component": "Consulting Charges",
				"particulars": "Consultancy Charges",
				"amount": 20000,
				"charges_display": "₹ 20,000/-",
				"payment_destination": "Payable to Instacertify",
			}
		],
	)
	_upsert_template(
		"EPR Compliance Consultancy",
		{
			"quotation_type": "Consulting",
			"service_family": "EPR",
			"is_active": 1,
			"service_name": "EPR Compliance Consultancy",
			"certification_type": "EPR",
			"applicable_standard": "EPR Rules",
			"estimated_timeline": "2–4 weeks",
			"validity_days": 90,
			"about_service": "<p>Extended Producer Responsibility (EPR) registration and compliance support.</p>",
		},
		[
			{
				"cost_component": "Consulting Charges",
				"particulars": "Consultancy Charges",
				"amount": 30000,
				"charges_display": "₹ 30,000/-",
				"payment_destination": "Payable to Instacertify",
			}
		],
	)

	# Testing
	_upsert_template(
		"EMC Testing Package",
		{
			"quotation_type": "Testing",
			"service_family": "EMC",
			"is_active": 1,
			"service_name": "EMC Testing",
			"subject": "Testing",
			"applicable_standard": "IEC 61000 series",
			"estimated_timeline": "5–7 working days",
			"validity_days": 30,
			"about_testing": "<p>EMC immunity and emission testing package as per applicable IEC 61000 standards.</p>",
			"gst_note": "Note: GST @ 18% shall be charged additionally on the above testing charges.",
		},
		None,
		[
			{
				"product_name": "Product Under Test",
				"test_name": "Surge Immunity Test",
				"applicable_standard": "IEC 61000-4-5",
				"number_of_samples": 4,
				"per_unit_charges": 20000,
				"testing_charges": 80000,
				"sample_requirement": "4 complete functional product samples with accessories.",
			},
			{
				"product_name": "Product Under Test",
				"test_name": "Voltage Dips & Interruptions",
				"applicable_standard": "IEC 61000-4-11",
				"number_of_samples": 4,
				"per_unit_charges": 20000,
				"testing_charges": 80000,
			},
		],
	)
	_upsert_template(
		"Safety Testing Package",
		{
			"quotation_type": "Testing",
			"service_family": "Safety",
			"is_active": 1,
			"service_name": "Safety Testing",
			"subject": "Testing",
			"applicable_standard": "IS/IEC 62368-1",
			"estimated_timeline": "7–10 working days",
			"validity_days": 30,
			"about_testing": "<p>Safety testing as per IS/IEC 62368-1 for AV/ICT equipment.</p>",
		},
		None,
		[
			{
				"product_name": "Product Under Test",
				"test_name": "Safety Requirements for AV/ICT Equipment",
				"applicable_standard": "IS/IEC 62368-1",
				"number_of_samples": 4,
				"per_unit_charges": 40000,
				"testing_charges": 160000,
			}
		],
	)
	_upsert_template(
		"IP65 Ingress Protection Testing",
		{
			"quotation_type": "Testing",
			"service_family": "IP",
			"is_active": 1,
			"service_name": "IP65 Testing",
			"subject": "Testing",
			"applicable_standard": "IP65",
			"estimated_timeline": "3–5 working days",
			"validity_days": 30,
			"about_testing": "<p>Ingress protection testing against dust and water jets (IP65).</p>",
		},
		None,
		[
			{
				"product_name": "Enclosure / Product",
				"test_name": "Ingress Protection Test",
				"applicable_standard": "IP65",
				"number_of_samples": 4,
				"per_unit_charges": 6000,
				"testing_charges": 24000,
			}
		],
	)

	# Renewal
	_upsert_template(
		"BIS CRS Renewal",
		{
			"quotation_type": "Renewal",
			"service_family": "BIS CRS Renewal",
			"is_active": 1,
			"service_name": "BIS CRS Renewal Consultancy",
			"certification_type": "BIS CRS Renewal",
			"applicable_standard": "Existing BIS CRS Registration",
			"estimated_timeline": "10–15 working days",
			"validity_days": 90,
			"about_service": "<p>Renewal support for existing BIS CRS registrations, including documentation review, portal filings, and authority liaison.</p>",
			"process_steps": "<p><b>Renewal Process</b></p><ol><li>Review existing registration and validity.</li><li>Prepare renewal documentation.</li><li>Submit renewal on BIS portal.</li><li>Follow-up until grant of renewed registration.</li></ol>",
			"payment_terms": "<ul><li>Consultancy charges payable on confirmation.</li><li>BIS renewal fees payable in advance at actuals.</li></ul>",
		},
		[
			{
				"cost_component": "Consulting Charges",
				"particulars": "Renewal Consultancy Charges",
				"amount": 8000,
				"charges_display": "₹ 8,000/-",
				"payment_destination": "Payable to Instacertify",
			},
			{
				"cost_component": "Government Fees",
				"particulars": "BIS Renewal Fees (Including GST)",
				"amount": 5000,
				"charges_display": "At actuals",
				"payment_destination": "Payable Directly to Government",
				"is_passthrough": 1,
			},
		],
	)
	_upsert_template(
		"Licence / Certificate Renewal",
		{
			"quotation_type": "Renewal",
			"service_family": "General Renewal",
			"is_active": 1,
			"service_name": "Licence / Certificate Renewal",
			"certification_type": "Renewal",
			"estimated_timeline": "2–4 weeks",
			"validity_days": 90,
			"about_service": "<p>General renewal consultancy for product certifications and licences nearing expiry.</p>",
		},
		[
			{
				"cost_component": "Consulting Charges",
				"particulars": "Renewal Consultancy Charges",
				"amount": 15000,
				"charges_display": "₹ 15,000/-",
				"payment_destination": "Payable to Instacertify",
			}
		],
	)


def _ensure_bis_crs_template():
	name = "BIS CRS Consultancy"
	cost_rows = [
		{
			"cost_component": "Government Fees",
			"particulars": "Government Fees ( Including GST)",
			"description": "Government Fees ( Including GST)",
			"amount": 8290,
			"charges_display": "₹ 8,290/-",
			"payment_destination": "Payable Directly to Government",
			"is_passthrough": 1,
		},
		{
			"cost_component": "Consulting Charges",
			"particulars": "Consultancy Charges",
			"description": "Consultancy Charges",
			"amount": 8000,
			"charges_display": "₹ 8,000/-",
			"payment_destination": "Payable to Instacertify",
			"is_passthrough": 0,
		},
		{
			"cost_component": "Testing Charges",
			"particulars": "Testing Charges",
			"description": "Testing Charges",
			"amount": 25000,
			"charges_display": "₹ 25,000/- per Test Report",
			"payment_destination": "Payable Directly to Laboratory",
			"is_passthrough": 1,
		},
	]
	values = {
		"quotation_type": "Consulting",
		"service_family": "BIS CRS",
		"is_active": 1,
		"service_name": "BIS CRS Consultancy",
		"certification_type": "BIS CRS",
		"applicable_standard": "IS 10322 (Part 5/Sec 2):2026",
		"estimated_timeline": "20–25 Working Days",
		"validity_days": 90,
		"about_service": BIS_ABOUT,
		"standard_narrative": BIS_STANDARD,
		"process_steps": BIS_PROCESS,
		"validity_text": BIS_VALIDITY,
		"timeline_details": BIS_TIMELINE,
		"sample_required": BIS_SAMPLE,
		"documents_required": BIS_DOCUMENTS,
		"commercials_notes": BIS_COMMERCIALS_NOTES,
		"payment_terms": BIS_PAYMENT,
		"cancellation_policy": BIS_CANCEL,
		"confidentiality": BIS_CONF,
		"force_majeure": BIS_FORCE,
	}
	if frappe.db.exists("IC Quotation Template", name):
		doc = frappe.get_doc("IC Quotation Template", name)
		doc.update(values)
		doc.set("cost_items", [])
		for row in cost_rows:
			doc.append("cost_items", row)
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc({"doctype": "IC Quotation Template", "template_name": name, **values})
		for row in cost_rows:
			doc.append("cost_items", row)
		doc.insert(ignore_permissions=True)


def ensure_sample_consulting_quotation():
	"""Create/update a sample consulting quotation matching the Labs PDF."""
	customer = frappe.db.get_value("Customer", {"customer_name": ["like", "%"]}, "name")
	if not customer:
		return
	# Prefer an existing Service quotation or create one
	existing = frappe.db.get_value(
		"Quotation", {"ic_quote_number": "ILPL/C/2026-2027/130"}, "name"
	) or frappe.db.get_value(
		"Quotation", {"ic_service_name": "BIS CRS Consultancy", "docstatus": 0}, "name"
	)
	tmpl = "BIS CRS Consultancy"
	if not frappe.db.exists("IC Quotation Template", tmpl):
		_ensure_bis_crs_template()

	if existing:
		from instacertify.quotation.events import apply_quotation_template

		frappe.db.set_value("Quotation", existing, {
			"ic_quote_number": "ILPL/C/2026-2027/130",
			"transaction_date": "2026-08-26",
		})
		apply_quotation_template(existing, tmpl)
		return existing

	# Create minimal quotation if company/customer available
	company = "Instacertify" if frappe.db.exists("Company", "Instacertify") else (
		frappe.db.get_single_value("Global Defaults", "default_company") or "Instacertify"
	)
	if not frappe.db.exists("Company", company):
		return
	item_code = (
		frappe.db.get_value("Item", {"item_name": ["like", "%Consult%"]}, "name")
		or frappe.db.get_value("Item", {}, "name")
	)
	if not item_code:
		return
	qt = frappe.get_doc(
		{
			"doctype": "Quotation",
			"quotation_to": "Customer",
			"party_name": customer,
			"company": company,
			"transaction_date": frappe.utils.today(),
			"order_type": "Sales",
			"ic_quotation_type": "Service",
			"ic_quote_number": "ILPL/C/2026-2027/130",
			"ic_quotation_template": tmpl,
			"items": [{"item_code": item_code, "qty": 1, "rate": 8000}],
		}
	)
	qt.insert(ignore_permissions=True)
	from instacertify.quotation.events import apply_quotation_template

	apply_quotation_template(qt.name, tmpl)
	frappe.db.set_value(
		"Quotation",
		qt.name,
		{"ic_quote_number": "ILPL/C/2026-2027/130", "transaction_date": "2026-08-26"},
	)
	return qt.name
