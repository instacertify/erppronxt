# Copyright (c) Instacertify
"""Print format HTML for Instacertify documents."""

from __future__ import annotations

import frappe

QUOTATION_HTML = """
<style>
  .ic-quote { font-family: 'Segoe UI', Tahoma, sans-serif; color: #1a1a1a; font-size: 11px; }
  .ic-header { background: linear-gradient(135deg, #065175 0%, #0a7aa8 100%); color: #fff; padding: 18px 22px; border-radius: 8px 8px 0 0; }
  .ic-header h1 { margin: 0; font-size: 22px; letter-spacing: 0.5px; }
  .ic-header .tagline { opacity: 0.9; font-size: 11px; margin-top: 4px; }
  .ic-accent { color: #EC6820; }
  .ic-meta { display: flex; justify-content: space-between; padding: 14px 8px; border-bottom: 2px solid #065175; margin-bottom: 12px; }
  .ic-box { border: 1px solid #d9e6ee; border-radius: 8px; padding: 10px 12px; margin-bottom: 12px; }
  .ic-box h3 { margin: 0 0 8px 0; color: #065175; font-size: 13px; border-bottom: 1px solid #ecf3f7; padding-bottom: 4px; }
  table.ic-table { width: 100%; border-collapse: collapse; margin-top: 6px; }
  table.ic-table th { background: #065175; color: #fff; padding: 6px 8px; text-align: left; font-size: 10px; }
  table.ic-table td { border-bottom: 1px solid #e5eef3; padding: 6px 8px; }
  .badge-pass { background: #fff3e8; color: #EC6820; padding: 2px 6px; border-radius: 10px; font-size: 9px; }
  .badge-rev { background: #e8f4fa; color: #065175; padding: 2px 6px; border-radius: 10px; font-size: 9px; }
  .ic-footer { position: relative; margin-top: 24px; padding-top: 12px; border-top: 1px solid #d9e6ee; min-height: 90px; }
  .ic-qr { position: absolute; right: 0; bottom: 0; text-align: center; }
  .ic-qr img { width: 72px; height: 72px; }
  .ic-sign { margin-top: 28px; }
</style>
<div class="ic-quote">
  <div class="ic-header">
    <h1>INSTACERTIFY</h1>
    <div class="tagline">Global Certification · Compliance · Consulting · Testing</div>
  </div>
  <div class="ic-meta">
    <div>
      <div><b>Quotation:</b> {{ doc.name }}</div>
      <div><b>Revision:</b> {{ doc.ic_revision_number or 0 }}</div>
      <div><b>Date:</b> {{ frappe.utils.formatdate(doc.transaction_date) }}</div>
      <div><b>Type:</b> {{ doc.ic_quotation_type or '' }}</div>
    </div>
    <div style="text-align:right;">
      <div><b>Currency:</b> {{ doc.currency }}</div>
      <div><span class="badge-rev">{{ doc.ic_workflow_status or doc.status }}</span></div>
    </div>
  </div>

  <div class="ic-box">
    <h3>Customer Details</h3>
    <div><b>{{ doc.customer_name or doc.party_name }}</b></div>
    <div>{{ doc.address_display or '' }}</div>
  </div>

  {% if doc.ic_service_name or doc.ic_scope_of_work %}
  <div class="ic-box">
    <h3>Service Scope</h3>
    <div><b>Service:</b> {{ doc.ic_service_name or '' }}</div>
    <div><b>Certification Type:</b> {{ doc.ic_certification_type or '' }}</div>
    <div><b>Standard:</b> {{ doc.ic_applicable_standard or '' }}</div>
    <div><b>Timeline:</b> {{ doc.ic_estimated_timeline or '' }}</div>
    <div style="margin-top:8px;">{{ doc.ic_scope_of_work or '' }}</div>
    {% if doc.ic_deliverables %}<div style="margin-top:8px;"><b>Deliverables</b>{{ doc.ic_deliverables }}</div>{% endif %}
  </div>
  {% endif %}

  {% if doc.ic_test_items %}
  <div class="ic-box">
    <h3>Testing Details</h3>
    <table class="ic-table">
      <thead><tr>
        <th>Product</th><th>Test</th><th>Standard</th><th>Samples</th><th>Laboratory</th><th>Charges</th>
      </tr></thead>
      <tbody>
      {% for row in doc.ic_test_items %}
        <tr>
          <td>{{ row.product_name }}</td>
          <td>{{ row.test_name }}</td>
          <td>{{ row.applicable_standard or '' }}</td>
          <td>{{ row.number_of_samples or '' }}</td>
          <td>{{ row.laboratory or '' }}</td>
          <td>{{ frappe.utils.fmt_money(row.testing_charges, currency=doc.currency) }}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% endif %}

  {% if doc.ic_cost_items %}
  <div class="ic-box">
    <h3>Cost Breakdown</h3>
    <table class="ic-table">
      <thead><tr>
        <th>Component</th><th>Description</th><th>Destination</th><th>Amount</th>
      </tr></thead>
      <tbody>
      {% for row in doc.ic_cost_items %}
        <tr>
          <td>{{ row.cost_component }}</td>
          <td>{{ row.description or '' }} {% if row.is_passthrough %}<span class="badge-pass">Pass-through</span>{% endif %}</td>
          <td>{{ row.payment_destination }}</td>
          <td>{{ frappe.utils.fmt_money(row.amount, currency=doc.currency) }}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
    <div style="margin-top:10px;">
      <div><b>Instacertify Commercial Value:</b> {{ frappe.utils.fmt_money(doc.ic_commercial_value, currency=doc.currency) }}</div>
      <div><b>Pass-Through Charges:</b> {{ frappe.utils.fmt_money(doc.ic_passthrough_value, currency=doc.currency) }}</div>
      <div><b>Total Quoted Value:</b> {{ frappe.utils.fmt_money(doc.ic_total_quoted_value or doc.grand_total, currency=doc.currency) }}</div>
    </div>
  </div>
  {% endif %}

  {% if doc.items %}
  <div class="ic-box">
    <h3>Line Items</h3>
    <table class="ic-table">
      <thead><tr><th>Item</th><th>Qty</th><th>Rate</th><th>Amount</th></tr></thead>
      <tbody>
      {% for row in doc.items %}
        <tr>
          <td>{{ row.item_name or row.item_code }}</td>
          <td>{{ row.qty }}</td>
          <td>{{ frappe.utils.fmt_money(row.rate, currency=doc.currency) }}</td>
          <td>{{ frappe.utils.fmt_money(row.amount, currency=doc.currency) }}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% endif %}

  <div class="ic-box">
    <h3>Terms and Conditions</h3>
    {{ doc.ic_terms_and_conditions or doc.terms or '' }}
  </div>
  <div class="ic-box">
    <h3>Force Majeure</h3>
    {{ doc.ic_force_majeure or '' }}
  </div>

  <div class="ic-sign">
    <div>Authorized Signatory</div>
    <div style="margin-top:36px;"><b>Instacertify</b></div>
  </div>

  <div class="ic-footer">
    <div style="max-width:70%; color:#667;">This document was generated from ERPNext · Quotation {{ doc.name }} · Rev {{ doc.ic_revision_number or 0 }}</div>
    <div class="ic-qr">
      {% if doc.ic_qr_code %}
        <img src="{{ doc.ic_qr_code }}" alt="QR"/>
      {% else %}
        <img src="{{ get_qr_code_data_uri(frappe.utils.get_url() + '/ic-verify/Quotation/' + doc.name) }}" alt="QR"/>
      {% endif %}
      <div style="font-size:8px;">Scan to verify</div>
    </div>
  </div>
</div>
"""

INVOICE_HTML = """
<style>
  .ic-inv { font-family: 'Segoe UI', Tahoma, sans-serif; font-size: 11px; }
  .ic-header { background: #065175; color:#fff; padding:16px 20px; border-radius:8px; }
  .ic-header h1 { margin:0; }
  .accent { color:#EC6820; }
  table { width:100%; border-collapse: collapse; margin-top:12px; }
  th { background:#065175; color:#fff; padding:6px; text-align:left; }
  td { border-bottom:1px solid #e5eef3; padding:6px; }
  .qr { text-align:right; margin-top:20px; }
  .qr img { width:72px; height:72px; }
</style>
<div class="ic-inv">
  <div class="ic-header"><h1>INSTACERTIFY</h1><div>Tax Invoice</div></div>
  <p><b>Invoice:</b> {{ doc.name }} &nbsp;|&nbsp; <b>Date:</b> {{ frappe.utils.formatdate(doc.posting_date) }}</p>
  <p><b>Customer:</b> {{ doc.customer_name }}</p>
  <table>
    <thead><tr><th>Item</th><th>Qty</th><th>Rate</th><th>Amount</th></tr></thead>
    <tbody>
    {% for row in doc.items %}
      <tr>
        <td>{{ row.item_name }}</td>
        <td>{{ row.qty }}</td>
        <td>{{ frappe.utils.fmt_money(row.rate, currency=doc.currency) }}</td>
        <td>{{ frappe.utils.fmt_money(row.amount, currency=doc.currency) }}</td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
  <p style="text-align:right; margin-top:12px;"><b>Grand Total:</b> {{ frappe.utils.fmt_money(doc.grand_total, currency=doc.currency) }}</p>
  <div class="qr">
    <img src="{{ get_qr_code_data_uri(frappe.utils.get_url() + '/ic-verify/Sales Invoice/' + doc.name) }}" alt="QR"/>
  </div>
</div>
"""

SAMPLE_HTML = """
<style>
  .ic { font-family: 'Segoe UI', Tahoma, sans-serif; }
  .head { background:#065175; color:#fff; padding:12px 16px; border-radius:8px; }
  .qr img { width:90px; height:90px; }
</style>
<div class="ic">
  <div class="head"><h2 style="margin:0;">Sample Tracking Label</h2></div>
  <p><b>Tracking No:</b> {{ doc.tracking_number }}</p>
  <p><b>Customer:</b> {{ doc.customer }}</p>
  <p><b>Description:</b> {{ doc.sample_description }}</p>
  <p><b>Status:</b> {{ doc.status }}</p>
  <p><b>Qty:</b> {{ doc.quantity }} &nbsp; <b>Condition:</b> {{ doc.sample_condition or '' }}</p>
  <div class="qr">
    {% if doc.qr_code %}<img src="{{ doc.qr_code }}" alt="QR"/>{% else %}
    <img src="{{ get_qr_code_data_uri(frappe.utils.get_url() + '/ic-verify/IC Sample Tracking/' + doc.name) }}" alt="QR"/>{% endif %}
  </div>
</div>
"""

TESTING_HTML = """
<style>
  .ic { font-family: 'Segoe UI', Tahoma, sans-serif; font-size:11px; }
  .head { background:#065175; color:#fff; padding:12px 16px; border-radius:8px; }
</style>
<div class="ic">
  <div class="head"><h2 style="margin:0;">Testing Request</h2></div>
  <p><b>{{ doc.name }}</b> — {{ doc.title }}</p>
  <p><b>Customer:</b> {{ doc.customer }} | <b>Project:</b> {{ doc.project or '' }}</p>
  <p><b>Product:</b> {{ doc.product }} | <b>Test:</b> {{ doc.test_name }}</p>
  <p><b>Standard:</b> {{ doc.applicable_standard or '' }}</p>
  <p><b>Laboratory:</b> {{ doc.laboratory or '' }} ({{ doc.laboratory_location or '' }})</p>
  <p><b>Samples:</b> {{ doc.number_of_samples }} | <b>Status:</b> {{ doc.status }}</p>
  <img style="width:72px;height:72px;" src="{{ get_qr_code_data_uri(frappe.utils.get_url() + '/ic-verify/IC Testing Request/' + doc.name) }}" alt="QR"/>
</div>
"""

JOINING_HTML = """
<style>
  .ic { font-family: Georgia, 'Times New Roman', serif; }
  .head { color:#065175; border-bottom:3px solid #EC6820; padding-bottom:8px; }
  .qr { text-align:right; }
  .qr img { width:72px; height:72px; }
</style>
<div class="ic">
  <div class="head"><h1>INSTACERTIFY</h1><h3>Joining Letter</h3></div>
  <p>Date: {{ frappe.utils.formatdate(doc.joining_date) }}</p>
  <p>Dear <b>{{ doc.employee_name }}</b>,</p>
  {{ doc.letter_content or '<p>We are pleased to welcome you to Instacertify.</p>' }}
  <p>Designation: {{ doc.designation or '' }}<br/>Department: {{ doc.department or '' }}</p>
  <div class="qr">
    <img src="{{ get_qr_code_data_uri(frappe.utils.get_url() + '/ic-verify/IC Joining Letter/' + doc.name) }}" alt="QR"/>
    <div>Verification: {{ doc.verification_code or doc.name }}</div>
  </div>
</div>
"""


def ensure_print_formats():
	formats = [
		("Instacertify Quotation", "Quotation", QUOTATION_HTML),
		("Instacertify Sales Invoice", "Sales Invoice", INVOICE_HTML),
		("Instacertify Sample Label", "IC Sample Tracking", SAMPLE_HTML),
		("Instacertify Testing Request", "IC Testing Request", TESTING_HTML),
		("Instacertify Joining Letter", "IC Joining Letter", JOINING_HTML),
	]
	for name, dt, html in formats:
		if frappe.db.exists("Print Format", name):
			frappe.db.set_value("Print Format", name, {
				"html": html,
				"module": "Instacertify",
				"standard": "No",
				"custom_format": 1,
				"print_format_type": "Jinja",
			})
			continue
		try:
			frappe.get_doc(
				{
					"doctype": "Print Format",
					"name": name,
					"doc_type": dt,
					"module": "Instacertify",
					"standard": "No",
					"custom_format": 1,
					"print_format_type": "Jinja",
					"html": html,
				}
			).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Print Format {name}")
