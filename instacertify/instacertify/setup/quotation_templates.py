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
		"quotation_type": "Service",
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
