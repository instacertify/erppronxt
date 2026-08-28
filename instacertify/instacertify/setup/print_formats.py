# Copyright (c) Instacertify
"""Print format HTML for Instacertify documents."""

from __future__ import annotations

import frappe

QUOTATION_HTML = """
{%- set s = frappe.get_cached_doc('IC Settings') -%}
{%- set legal = s.legal_name or 'INSTACERTIFY LABS PRIVATE LIMITED' -%}
{%- set phone = s.phone or '+91 9999118039' -%}
{%- set email = s.email or 'contact@instacertify.com' -%}
{%- set website = s.website or 'www.instacertify.com' -%}
{%- set cin = s.cin or 'U74999UP2022PTC170291' -%}
{%- set gstin = s.gstin or '09AAGCI8396C1Z7' -%}
{%- set address = (s.address_line or 'PK 01 SECTOR 63A NOIDA, GAUTAM BUDDHA NAGAR, UTTAR PRADESH-201301, INDIA').replace('\\n', '<br>') -%}
{%- set logo = s.header_image or s.logo or '/assets/instacertify/images/instacertify_logo.png' -%}
<style>
  @page { size: A4; margin: 12mm; }
  .print-format { padding: 0 !important; margin: 0 !important; }
  .ic-quote { font-family: Arial, Helvetica, 'Segoe UI', sans-serif; color: #1a1a1a; font-size: 11px; }
  .ic-lh { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; padding-bottom:8px; border-bottom:1.5px solid #EC6820; margin-bottom:12px; }
  .ic-lh-logo img { max-height:58px; max-width:320px; }
  .ic-lh-co { text-align:right; color:#222; font-size:10px; line-height:1.4; }
  .ic-lh-co .name { color:#EC6820; font-weight:700; font-size:12.5px; text-transform:uppercase; margin-bottom:2px; }
  .ic-accent { color: #EC6820; }
  .ic-meta { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #065175; margin-bottom: 12px; }
  .ic-box { border: 1px solid #d9e6ee; border-radius: 8px; padding: 10px 12px; margin-bottom: 12px; }
  .ic-box h3 { margin: 0 0 8px 0; color: #065175; font-size: 13px; border-bottom: 1px solid #ecf3f7; padding-bottom: 4px; }
  table.ic-table { width: 100%; border-collapse: collapse; margin-top: 6px; }
  table.ic-table th { background: #065175; color: #fff; padding: 6px 8px; text-align: left; font-size: 10px; }
  table.ic-table td { border-bottom: 1px solid #e5eef3; padding: 6px 8px; }
  .badge-pass { background: #fff3e8; color: #EC6820; padding: 2px 6px; border-radius: 10px; font-size: 9px; }
  .badge-rev { background: #e8f4fa; color: #065175; padding: 2px 6px; border-radius: 10px; font-size: 9px; }
  .ic-footer { margin-top: 24px; padding-top: 12px; border-top: 1px solid #d9e6ee; overflow: auto; page-break-inside: avoid; }
  .ic-qr { float: right; margin: 0 0 8px 16px; text-align: center; }
  .ic-qr img { width: 72px; height: 72px; }
  .ic-qr .cap { font-size: 8px; color: #555; }
  .ic-sign { margin-top: 28px; page-break-inside: avoid; }
  .ic-footer-bar {
    background: linear-gradient(90deg, #d85a16 0%, #EC6820 50%, #d85a16 100%);
    color:#fff; text-align:center; padding:5px 12px; margin-top:20px;
    font-size:10px; font-weight:500; letter-spacing:0.14em; text-transform:lowercase;
    border:none; line-height:1.2;
  }
</style>
<div class="ic-quote">
  <div class="ic-lh">
    <div class="ic-lh-logo"><img src="{{ logo }}" alt="Instacertify"/></div>
    <div class="ic-lh-co">
      <div class="name">{{ legal }}</div>
      <div>{{ address }}</div>
      <div>☎ {{ phone }}</div>
      <div>✉ {{ email }}</div>
      <div>{{ website }}</div>
      <div><b>CIN :</b> {{ cin }}</div>
      <div><b>GSTIN :</b> {{ gstin }}</div>
    </div>
  </div>
  <div style="text-align:center;font-size:18px;font-weight:700;margin:8px 0 12px;">Quotation</div>
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
    <div style="margin-top:36px;"><b>For Instacertify Labs Private Limited</b></div>
  </div>

  <div class="ic-footer">
    <div style="max-width:70%; color:#667;">Quotation {{ doc.name }} · Rev {{ doc.ic_revision_number or 0 }}</div>
    <div class="ic-qr">
      {% if doc.ic_qr_code %}
        <img src="{{ doc.ic_qr_code }}" alt="QR"/>
      {% else %}
        <img src="{{ get_qr_code_data_uri(frappe.utils.get_url() + '/ic-verify/Quotation/' + doc.name) }}" alt="QR"/>
      {% endif %}
      <div style="font-size:8px;">Scan to verify</div>
    </div>
  </div>
  <div class="ic-footer-bar">www.instacertify.com</div>
</div>
"""

INVOICE_HTML = """
{%- set s = frappe.get_cached_doc('IC Settings') -%}
{%- set legal = s.legal_name or 'INSTACERTIFY LABS PRIVATE LIMITED' -%}
{%- set phone = s.phone or '+91 9999118039' -%}
{%- set email = s.email or 'contact@instacertify.com' -%}
{%- set website = s.website or 'www.instacertify.com' -%}
{%- set cin = s.cin or 'U74999UP2022PTC170291' -%}
{%- set gstin = s.gstin or '09AAGCI8396C1Z7' -%}
{%- set address = (s.address_line or 'PK 01 SECTOR 63A NOIDA, GAUTAM BUDDHA NAGAR, UTTAR PRADESH-201301, INDIA').replace('\\n', '<br>') -%}
{%- set logo = s.header_image or s.logo or '/assets/instacertify/images/instacertify_logo.png' -%}
<style>
  @page { size: A4; margin: 12mm; }
  .print-format { padding:0 !important; margin:0 !important; }
  .ic-inv { font-family: Arial, Helvetica, 'Segoe UI', sans-serif; font-size: 11px; }
  .ic-lh { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; padding-bottom:8px; border-bottom:1.5px solid #EC6820; margin-bottom:12px; }
  .ic-lh-logo img { max-height:58px; max-width:320px; }
  .ic-lh-co { text-align:right; color:#222; font-size:10px; line-height:1.4; }
  .ic-lh-co .name { color:#EC6820; font-weight:700; font-size:12.5px; text-transform:uppercase; margin-bottom:2px; }
  table { width:100%; border-collapse: collapse; margin-top:12px; }
  th { background:#065175; color:#fff; padding:6px; text-align:left; }
  td { border-bottom:1px solid #e5eef3; padding:6px; }
  .qr { text-align:right; margin-top:20px; }
  .qr img { width:72px; height:72px; }
  .ic-footer-bar {
    background: linear-gradient(90deg, #d85a16 0%, #EC6820 50%, #d85a16 100%);
    color:#fff; text-align:center; padding:5px 12px; margin-top:20px;
    font-size:10px; font-weight:500; letter-spacing:0.14em; text-transform:lowercase;
    border:none; line-height:1.2;
  }
</style>
<div class="ic-inv">
  <div class="ic-lh">
    <div class="ic-lh-logo"><img src="{{ logo }}" alt="Instacertify"/></div>
    <div class="ic-lh-co">
      <div class="name">{{ legal }}</div>
      <div>{{ address }}</div>
      <div>☎ {{ phone }}</div>
      <div>✉ {{ email }}</div>
      <div>{{ website }}</div>
      <div><b>CIN :</b> {{ cin }}</div>
      <div><b>GSTIN :</b> {{ gstin }}</div>
    </div>
  </div>
  <div style="text-align:center;font-size:18px;font-weight:700;margin:8px 0 12px;">Tax Invoice</div>
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
  <div class="ic-footer-bar">www.instacertify.com</div>
</div>
"""

SAMPLE_HTML = """
{%- set s = frappe.get_cached_doc('IC Settings') -%}
{%- set legal = s.legal_name or 'INSTACERTIFY LABS PRIVATE LIMITED' -%}
{%- set phone = s.phone or '+91 9999118039' -%}
{%- set email = s.email or 'contact@instacertify.com' -%}
{%- set website = s.website or 'www.instacertify.com' -%}
{%- set cin = s.cin or 'U74999UP2022PTC170291' -%}
{%- set gstin = s.gstin or '09AAGCI8396C1Z7' -%}
{%- set address = (s.address_line or 'PK 01 SECTOR 63A NOIDA, GAUTAM BUDDHA NAGAR, UTTAR PRADESH-201301, INDIA').replace('\\n', '<br>') -%}
{%- set logo = s.header_image or s.logo or '/assets/instacertify/images/instacertify_logo.png' -%}
<style>
  @page { size: A4; margin: 12mm; }
  .print-format { padding:0 !important; margin:0 !important; }
  .ic { font-family: Arial, Helvetica, 'Segoe UI', sans-serif; font-size:11px; }
  .ic-lh { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; padding-bottom:8px; border-bottom:1.5px solid #EC6820; margin-bottom:12px; }
  .ic-lh-logo img { max-height:48px; max-width:280px; }
  .ic-lh-co { text-align:right; color:#222; font-size:9.5px; line-height:1.35; }
  .ic-lh-co .name { color:#EC6820; font-weight:700; font-size:11px; text-transform:uppercase; }
  .qr img { width:90px; height:90px; }
  .ic-footer-bar {
    background: linear-gradient(90deg, #d85a16 0%, #EC6820 50%, #d85a16 100%);
    color:#fff; text-align:center; padding:5px 12px; margin-top:20px;
    font-size:10px; font-weight:500; letter-spacing:0.14em; text-transform:lowercase;
    border:none; line-height:1.2;
  }
</style>
<div class="ic">
  <div class="ic-lh">
    <div class="ic-lh-logo"><img src="{{ logo }}" alt="Instacertify"/></div>
    <div class="ic-lh-co">
      <div class="name">{{ legal }}</div>
      <div>{{ address }}</div>
      <div>☎ {{ phone }} · ✉ {{ email }}</div>
      <div><b>CIN :</b> {{ cin }} · <b>GSTIN :</b> {{ gstin }}</div>
    </div>
  </div>
  <h2 style="margin:0 0 10px; color:#065175;">Sample Tracking Label</h2>
  <p><b>Tracking No:</b> {{ doc.tracking_number }}</p>
  <p><b>Customer:</b> {{ doc.customer }}</p>
  <p><b>Description:</b> {{ doc.sample_description }}</p>
  <p><b>Status:</b> {{ doc.status }}</p>
  <p><b>Qty:</b> {{ doc.quantity }} &nbsp; <b>Condition:</b> {{ doc.sample_condition or '' }}</p>
  <div class="qr">
    {% if doc.qr_code %}<img src="{{ doc.qr_code }}" alt="QR"/>{% else %}
    <img src="{{ get_qr_code_data_uri(frappe.utils.get_url() + '/ic-verify/IC Sample Tracking/' + doc.name) }}" alt="QR"/>{% endif %}
  </div>
  <div class="ic-footer-bar">www.instacertify.com</div>
</div>
"""

TESTING_HTML = """
{%- set s = frappe.get_cached_doc('IC Settings') -%}
{%- set legal = s.legal_name or 'INSTACERTIFY LABS PRIVATE LIMITED' -%}
{%- set phone = s.phone or '+91 9999118039' -%}
{%- set email = s.email or 'contact@instacertify.com' -%}
{%- set website = s.website or 'www.instacertify.com' -%}
{%- set cin = s.cin or 'U74999UP2022PTC170291' -%}
{%- set gstin = s.gstin or '09AAGCI8396C1Z7' -%}
{%- set address = (s.address_line or 'PK 01 SECTOR 63A NOIDA, GAUTAM BUDDHA NAGAR, UTTAR PRADESH-201301, INDIA').replace('\\n', '<br>') -%}
{%- set logo = s.header_image or s.logo or '/assets/instacertify/images/instacertify_logo.png' -%}
<style>
  @page { size: A4; margin: 12mm; }
  .print-format { padding:0 !important; margin:0 !important; }
  .ic { font-family: Arial, Helvetica, 'Segoe UI', sans-serif; font-size:11px; }
  .ic-lh { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; padding-bottom:8px; border-bottom:1.5px solid #EC6820; margin-bottom:12px; }
  .ic-lh-logo img { max-height:48px; max-width:280px; }
  .ic-lh-co { text-align:right; color:#222; font-size:9.5px; line-height:1.35; }
  .ic-lh-co .name { color:#EC6820; font-weight:700; font-size:11px; text-transform:uppercase; }
  .ic-footer-bar {
    background: linear-gradient(90deg, #d85a16 0%, #EC6820 50%, #d85a16 100%);
    color:#fff; text-align:center; padding:5px 12px; margin-top:20px;
    font-size:10px; font-weight:500; letter-spacing:0.14em; text-transform:lowercase;
    border:none; line-height:1.2;
  }
</style>
<div class="ic">
  <div class="ic-lh">
    <div class="ic-lh-logo"><img src="{{ logo }}" alt="Instacertify"/></div>
    <div class="ic-lh-co">
      <div class="name">{{ legal }}</div>
      <div>{{ address }}</div>
      <div>☎ {{ phone }} · ✉ {{ email }}</div>
      <div><b>CIN :</b> {{ cin }} · <b>GSTIN :</b> {{ gstin }}</div>
    </div>
  </div>
  <h2 style="margin:0 0 10px; color:#065175;">Testing Request</h2>
  <p><b>{{ doc.name }}</b> — {{ doc.title }}</p>
  <p><b>Customer:</b> {{ doc.customer }} | <b>Project:</b> {{ doc.project or '' }}</p>
  <p><b>Product:</b> {{ doc.product }} | <b>Test:</b> {{ doc.test_name }}</p>
  <p><b>Standard:</b> {{ doc.applicable_standard or '' }}</p>
  <p><b>Laboratory:</b> {{ doc.laboratory or '' }} ({{ doc.laboratory_location or '' }})</p>
  <p><b>Samples:</b> {{ doc.number_of_samples }} | <b>Status:</b> {{ doc.status }}</p>
  <img style="width:72px;height:72px;" src="{{ get_qr_code_data_uri(frappe.utils.get_url() + '/ic-verify/IC Testing Request/' + doc.name) }}" alt="QR"/>
  <div class="ic-footer-bar">www.instacertify.com</div>
</div>
"""

JOINING_HTML = """
{%- set s = frappe.get_cached_doc('IC Settings') -%}
{%- set legal = s.legal_name or 'INSTACERTIFY LABS PRIVATE LIMITED' -%}
{%- set phone = s.phone or '+91 9999118039' -%}
{%- set email = s.email or 'contact@instacertify.com' -%}
{%- set website = s.website or 'www.instacertify.com' -%}
{%- set cin = s.cin or 'U74999UP2022PTC170291' -%}
{%- set gstin = s.gstin or '09AAGCI8396C1Z7' -%}
{%- set address = (s.address_line or 'PK 01 SECTOR 63A NOIDA, GAUTAM BUDDHA NAGAR, UTTAR PRADESH-201301, INDIA').replace('\\n', '<br>') -%}
{%- set logo = s.header_image or s.logo or '/assets/instacertify/images/instacertify_logo.png' -%}
<style>
  @page { size: A4; margin: 12mm; }
  .print-format { padding:0 !important; margin:0 !important; }
  .ic { font-family: Georgia, 'Times New Roman', serif; font-size:12px; }
  .ic-lh { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; padding-bottom:8px; border-bottom:3px solid #EC6820; margin-bottom:14px; }
  .ic-lh-logo img { max-height:52px; max-width:300px; }
  .ic-lh-co { text-align:right; font-family: Arial, Helvetica, sans-serif; color:#222; font-size:10px; line-height:1.4; }
  .ic-lh-co .name { color:#EC6820; font-weight:700; font-size:12px; text-transform:uppercase; }
  .qr { text-align:right; }
  .qr img { width:72px; height:72px; }
  .ic-footer-bar {
    background: linear-gradient(90deg, #d85a16 0%, #EC6820 50%, #d85a16 100%);
    color:#fff; text-align:center; padding:5px 12px; margin-top:20px;
    font-size:10px; font-weight:500; letter-spacing:0.14em; text-transform:lowercase;
    border:none; line-height:1.2;
  }
</style>
<div class="ic">
  <div class="ic-lh">
    <div class="ic-lh-logo"><img src="{{ logo }}" alt="Instacertify"/></div>
    <div class="ic-lh-co">
      <div class="name">{{ legal }}</div>
      <div>{{ address }}</div>
      <div>☎ {{ phone }}</div>
      <div>✉ {{ email }}</div>
      <div>{{ website }}</div>
      <div><b>CIN :</b> {{ cin }}</div>
      <div><b>GSTIN :</b> {{ gstin }}</div>
    </div>
  </div>
  <h3 style="color:#065175;">Joining Letter</h3>
  <p>Date: {{ frappe.utils.formatdate(doc.joining_date) }}</p>
  <p>Dear <b>{{ doc.employee_name }}</b>,</p>
  {{ doc.letter_content or '<p>We are pleased to welcome you to Instacertify.</p>' }}
  <p>Designation: {{ doc.designation or '' }}<br/>Department: {{ doc.department or '' }}</p>
  <div class="qr">
    <img src="{{ get_qr_code_data_uri(frappe.utils.get_url() + '/ic-verify/IC Joining Letter/' + doc.name) }}" alt="QR"/>
    <div>Verification: {{ doc.verification_code or doc.name }}</div>
  </div>
  <p style="margin-top:28px;"><b>For Instacertify Labs Private Limited</b></p>
  <div class="ic-footer-bar">www.instacertify.com</div>
</div>
"""

# Matches uploaded Instacertify Labs testing quotation template (A4)
# Source: public/templates/testing_quotation_template.pdf
TESTING_QUOTATION_HTML = """
{%- macro inr(amount) -%}
{%- if (doc.currency or 'INR') == 'INR' -%}₹{{ '{:,.0f}'.format(amount or 0) }}/-
{%- else -%}{{ frappe.utils.fmt_money(amount or 0, currency=doc.currency) }}/-
{%- endif -%}
{%- endmacro -%}
{%- set s = frappe.get_cached_doc('IC Settings') -%}
{%- set legal = s.legal_name or 'INSTACERTIFY LABS PRIVATE LIMITED' -%}
{%- set phone = s.phone or '+91 9999118039' -%}
{%- set email = s.email or 'contact@instacertify.com' -%}
{%- set website = s.website or 'www.instacertify.com' -%}
{%- set cin = s.cin or 'U74999UP2022PTC170291' -%}
{%- set gstin = s.gstin or '09AAGCI8396C1Z7' -%}
{%- set address = (s.address_line or 'PK 01 SECTOR 63A NOIDA, GAUTAM BUDDHA NAGAR, UTTAR PRADESH-201301, INDIA').replace('\\n', '<br>') -%}
{%- set logo = s.header_image or s.logo or '/assets/instacertify/images/instacertify_logo.png' -%}
{%- set stamp = s.stamp_image or '/assets/instacertify/images/instacertify_stamp.png' -%}
{%- set quote_no = doc.ic_quote_number or doc.name -%}
{%- set curr = doc.currency or 'INR' -%}
<style>
  @page { size: A4; margin: 12mm; }
  .tq { font-family: Arial, Helvetica, 'Segoe UI', sans-serif; color:#222; font-size:10.5px; line-height:1.45; }
  .tq * { box-sizing: border-box; }
  .tq-head { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; padding-bottom:8px; border-bottom:1.5px solid #EC6820; margin-bottom:12px; }
  .tq-logo img { max-height:58px; max-width:320px; }
  .tq-co { text-align:right; color:#222; font-size:10px; line-height:1.4; }
  .tq-co .name { color:#EC6820; font-weight:700; font-size:12.5px; letter-spacing:0.2px; margin-bottom:2px; text-transform:uppercase; }
  .tq-meta { display:flex; justify-content:space-between; margin:12px 0 4px; font-size:11px; font-weight:700; }
  .tq-title { text-align:center; font-size:22px; font-weight:700; margin:10px 0 16px; color:#111; }
  table.tq-grid { width:100%; border-collapse:collapse; table-layout:fixed; margin-bottom:0; page-break-inside:auto; }
  table.tq-grid > tbody > tr { page-break-inside:avoid; }
  table.tq-grid > tbody > tr > td { border:1px solid #333; vertical-align:top; padding:0; }
  .tq-label { width:17%; background:#efefef; font-weight:700; padding:10px 8px; color:#111; font-size:10.5px; }
  .tq-value { width:83%; padding:10px 12px; }
  .tq-value ul { margin:6px 0 0 18px; padding:0; }
  .tq-value ol { margin:6px 0 0 18px; padding:0; }
  .tq-value li { margin-bottom:4px; }
  .tq-h { font-weight:700; margin:0 0 6px; }
  table.tq-comm { width:100%; border-collapse:collapse; margin-top:4px; }
  table.tq-comm th { background:#f5f5f5; border:1px solid #555; padding:7px 5px; font-size:9.5px; text-align:center; font-weight:700; }
  table.tq-comm td { border:1px solid #555; padding:7px 5px; font-size:10px; vertical-align:top; }
  table.tq-comm td.num, table.tq-comm th.num { text-align:center; }
  table.tq-comm td.amt { text-align:center; white-space:nowrap; font-weight:600; }
  .tq-note { margin-top:8px; font-size:10px; }
  table.tq-bank { width:100%; border-collapse:collapse; margin-top:6px; }
  table.tq-bank td { border:1px solid #555; padding:7px 8px; }
  table.tq-bank td.k { width:34%; background:#f5f5f5; font-weight:600; }
  .tq-close { margin-top:28px; page-break-inside:avoid; }
  .tq-close p { margin:6px 0; }
  .tq-stamp { margin-top:18px; margin-bottom:6px; }
  .tq-stamp img { max-height:110px; max-width:140px; }
  .tq-sign { margin-top:8px; font-weight:700; }
  .tq-footer-bar {
    background: linear-gradient(90deg, #d85a16 0%, #EC6820 50%, #d85a16 100%);
    color:#fff; text-align:center; padding:5px 12px; margin-top:24px;
    font-size:10px; font-weight:500; letter-spacing:0.14em; text-transform:lowercase;
    border:none; line-height:1.2;
  }
  .tq-qr { float:right; margin:8px 0 0 12px; text-align:center; }
  .tq-qr img { width:72px; height:72px; }
  .tq-qr .cap { font-size:8px; color:#555; }
  .print-format { padding:0 !important; margin:0 !important; }
</style>
<div class="tq">
  <div class="tq-head">
    <div class="tq-logo">
      <img src="{{ logo }}" alt="Instacertify"/>
    </div>
    <div class="tq-co">
      <div class="name">{{ legal }}</div>
      <div>{{ address }}</div>
      <div>☎ {{ phone }}</div>
      <div>✉ {{ email }}</div>
      <div>{{ website }}</div>
      <div><b>CIN :</b> {{ cin }}</div>
      <div><b>GSTIN :</b> {{ gstin }}</div>
    </div>
  </div>

  <div class="tq-meta">
    <div>No: {{ quote_no }}</div>
    <div>Date: {{ frappe.utils.formatdate(doc.transaction_date, 'dd-MM-yyyy') }}</div>
  </div>
  <div class="tq-title">Quotation</div>

  <table class="tq-grid">
    <tr>
      <td class="tq-label">Subject</td>
      <td class="tq-value"><b>{{ doc.ic_subject or 'Testing' }}</b></td>
    </tr>
    <tr>
      <td class="tq-label">ABOUT</td>
      <td class="tq-value">
        {% if doc.ic_about_testing %}
          {{ doc.ic_about_testing }}
        {% else %}
          {{ doc.ic_scope_of_work or '' }}
        {% endif %}
      </td>
    </tr>
    <tr>
      <td class="tq-label">Applicable Standards</td>
      <td class="tq-value">
        {% if doc.ic_applicable_standards_text %}
          {{ doc.ic_applicable_standards_text }}
        {% else %}
          <div>The following standards are applicable for the proposed testing:</div>
          <ul>
          {% for row in doc.ic_test_items or [] %}
            <li><b>{{ row.applicable_standard }}</b>{% if row.test_name %} – {{ row.test_name }}{% endif %}</li>
          {% endfor %}
          </ul>
        {% endif %}
      </td>
    </tr>
    <tr>
      <td class="tq-label">Samples Requirements</td>
      <td class="tq-value">
        <div class="tq-h">Sample Required</div>
        {% for row in doc.ic_test_items or [] %}
          <div style="margin-bottom:8px;">
            <b>{{ row.applicable_standard }}:</b>
            {{ row.sample_requirement or ((row.number_of_samples or 1)|string + ' complete functional product sample, including all necessary accessories, cables, and power supply components.') }}
          </div>
        {% endfor %}
        <div class="tq-note"><b>Note:</b> {{ (doc.ic_samples_note or 'Additional samples may be requested by the laboratory depending on the product configuration and applicable test requirements.')|replace('Note: ','') }}</div>
      </td>
    </tr>
  </table>

  <table class="tq-grid" style="margin-top:-1px;">
    <tr>
      <td class="tq-label">Commercials</td>
      <td class="tq-value">
        <div class="tq-h">Commercials</div>
        <table class="tq-comm">
          <thead>
            <tr>
              <th class="num" style="width:8%">S. No.</th>
              <th style="width:18%">Applicable Standard</th>
              <th style="width:28%">Testing</th>
              <th class="num" style="width:10%">Units</th>
              <th style="width:18%">Per Unit Charges ({{ curr }})</th>
              <th style="width:18%">Total Charges ({{ curr }})</th>
            </tr>
          </thead>
          <tbody>
          {% for row in doc.ic_test_items or [] %}
            {%- set units = row.number_of_samples or 1 -%}
            {%- set per = row.per_unit_charges or (row.testing_charges / units if units and row.testing_charges else 0) -%}
            {%- set total = row.testing_charges or (per * units) -%}
            <tr>
              <td class="num">{{ loop.index }}</td>
              <td>{{ row.applicable_standard or '' }}</td>
              <td>{{ row.test_name or '' }}</td>
              <td class="num">{{ units }}</td>
              <td class="amt">{{ inr(per) }}</td>
              <td class="amt">{{ inr(total) }}</td>
            </tr>
          {% endfor %}
          </tbody>
        </table>
        <div class="tq-note"><b>{{ doc.ic_gst_note or 'Note: GST @ 18% shall be charged additionally on the above testing charges.' }}</b></div>
      </td>
    </tr>
    <tr>
      <td class="tq-label">Deliverable</td>
      <td class="tq-value">
        <div class="tq-h">Deliverables</div>
        {% if doc.ic_deliverables %}
          {{ doc.ic_deliverables }}
        {% else %}
          <ul>
            <li><b>Test Report</b> covering the applicable standards and tests performed.</li>
            <li><b>Test Results</b> with observations and measured parameters.</li>
            <li><b>Certificate/Report of Compliance</b>, wherever applicable.</li>
          </ul>
        {% endif %}
      </td>
    </tr>
    <tr>
      <td class="tq-label">Timeline</td>
      <td class="tq-value">
        <div class="tq-h">Timeline</div>
        <ul>
          <li><b>Estimated Testing Timeline:</b> {{ doc.ic_estimated_timeline or '5–7 working days' }}.</li>
          <li>The timeline shall commence upon receipt of the required sample and confirmation of payment.</li>
          <li>The timeline may vary depending on laboratory scheduling, sample condition, test requirements, and any additional testing, if applicable.</li>
        </ul>
      </td>
    </tr>
    <tr>
      <td class="tq-label">Payment Term</td>
      <td class="tq-value">
        <div class="tq-h">Payment Terms</div>
        {% if doc.ic_payment_terms %}
          {{ doc.ic_payment_terms }}
        {% else %}
          <ul>
            <li><b>100% Advance Payment</b> is required to initiate the testing process.</li>
            <li>Testing will commence upon receipt of the payment and sample.</li>
            <li>Any additional testing or charges, if applicable, shall be communicated separately.</li>
          </ul>
        {% endif %}
      </td>
    </tr>
    <tr>
      <td class="tq-label">Sample handling &amp; disposal policy</td>
      <td class="tq-value">
        {% if doc.ic_sample_handling_policy %}
          {{ doc.ic_sample_handling_policy }}
        {% else %}
          <ol>
            <li>Samples may be subjected to destructive and/or non-destructive testing as required by the applicable standard or test protocol.</li>
            <li>After completion of testing and receipt of the samples from the laboratory, Instacertify Labs Pvt. Ltd. shall retain the remaining samples for a maximum period of <b>15 days</b>.</li>
            <li>Clients wishing to recover their samples must arrange collection or request return shipment within the 15-day retention period.</li>
            <li>All sample shipping, return shipping, handling, storage, customs duties, taxes, and related logistics costs shall be borne solely by the Client.</li>
            <li>For samples returned within India through a reputed courier service arranged by Instacertify Labs Pvt. Ltd., return shipping charges shall be <b>₹450 per kg + applicable GST</b>.</li>
            <li>For samples returned outside India, return shipping charges shall be <b>USD 90 per kg</b>, exclusive of customs duties, taxes, import/export charges, and other applicable logistics costs, which shall be borne by the Client.</li>
            <li>Samples not claimed, or for which return arrangements are not confirmed within 15 days, shall be considered abandoned and may be disposed of at the sole discretion of Instacertify Labs Pvt. Ltd., without further notice or liability.</li>
            <li>Instacertify Labs Pvt. Ltd. shall not be responsible for any loss, damage, delay, or deterioration of samples during transit through third-party courier or logistics providers.</li>
          </ol>
        {% endif %}
      </td>
    </tr>
    <tr>
      <td class="tq-label">Our Banking Details</td>
      <td class="tq-value">
        <div class="tq-h">Bank Details for Payment</div>
        <table class="tq-bank">
          <tr><td class="k">Particulars</td><td><b>Details</b></td></tr>
          <tr><td class="k">Beneficiary Name</td><td>{{ s.beneficiary_name or 'Instacertify Labs Private Limited' }}</td></tr>
          <tr><td class="k">Bank Name</td><td>{{ s.bank_name or 'YES BANK' }}</td></tr>
          <tr><td class="k">Account Number</td><td>{{ s.account_number or '026485800001318' }}</td></tr>
          <tr><td class="k">IFSC Code</td><td>{{ s.ifsc_code or 'YESB0000264' }}</td></tr>
          <tr><td class="k">SWIFT Code</td><td>{{ s.swift_code or 'YESBINBBDEL (For International USD Transfers)' }}</td></tr>
          <tr><td class="k">GSTIN</td><td>{{ s.gstin or '09AAGCI8396C1Z7' }}</td></tr>
          <tr><td class="k">Branch Address</td><td>{{ s.bank_branch_address or 'Ground, Mezzanine & First Floor, Plot No. 6, Basant Lok, Vasant Vihar, New Delhi, Delhi – 110057, India' }}</td></tr>
        </table>
        <div class="tq-note" style="margin-top:8px;"><b>Kindly share the payment transaction details/remittance advice after making the payment for our records and further processing.</b></div>
      </td>
    </tr>
    <tr>
      <td class="tq-label">CANCELLATION AND REFUND POLICY</td>
      <td class="tq-value">
        {% if doc.ic_cancellation_policy %}
          {{ doc.ic_cancellation_policy }}
        {% else %}
          Testing fees are payable in advance and are non-refundable once samples have been submitted or testing has commenced. Government fees may be refunded only if they have not been deposited with the relevant authority. Consultancy fees are charged based on the work completed and are non-refundable once services have been rendered. Any eligible refund request must be submitted to Instacertify in writing within 7 working days of payment.
        {% endif %}
      </td>
    </tr>
    <tr>
      <td class="tq-label">FORCE MAJEURE</td>
      <td class="tq-value">
        {% if doc.ic_force_majeure %}
          {{ doc.ic_force_majeure }}
        {% else %}
          Instacertify Labs Pvt. Ltd. shall not be liable for any delay or failure in performing its obligations due to circumstances beyond its reasonable control, including but not limited to natural disasters, acts of government, regulatory changes, strikes, pandemics, war, civil unrest, transportation disruptions, laboratory delays, or certification authority actions. Any affected timelines shall be extended accordingly, and both parties shall make reasonable efforts to minimize the impact of such events
        {% endif %}
      </td>
    </tr>
    <tr>
      <td class="tq-label">CONFIDENTIALITY &amp; DATA PROTECTION</td>
      <td class="tq-value">
        {% if doc.ic_confidentiality %}
          {{ doc.ic_confidentiality }}
        {% else %}
          Instacertify Labs Pvt. Ltd. shall maintain strict confidentiality of all documents, technical information, business data, and records shared by the Client. Such information will be used solely for the purpose of providing the agreed services and will not be disclosed to any third party except where required by law, regulatory authorities, laboratories, or certification bodies. Reasonable measures shall be implemented to ensure data security and protection
        {% endif %}
      </td>
    </tr>
  </table>

  <div class="tq-close">
    <div class="tq-qr">
      {% if doc.ic_qr_code %}
        <img src="{{ doc.ic_qr_code }}" alt="QR"/>
      {% else %}
        <img src="{{ get_qr_code_data_uri(frappe.utils.get_url() + '/ic-verify/Quotation/' + doc.name) }}" alt="QR"/>
      {% endif %}
      <div class="cap">Scan to verify</div>
    </div>
    <p>For other Product Certification and Compliance, please visit us at {{ website }} for more details.</p>
    <p><b>Thanking You,</b></p>
    <div class="tq-stamp"><img src="{{ stamp }}" alt="Company Stamp"/></div>
    <div class="tq-sign">For Instacertify Labs Private Limited</div>
  </div>

  <div style="clear:both;"></div>
  <div class="tq-footer-bar">www.instacertify.com</div>
</div>
"""


# Matches uploaded Instacertify Labs consulting quotation template (A4)
# Source: public/templates/consulting_quotation_template.pdf
CONSULTING_QUOTATION_HTML = """
{%- macro inr(amount) -%}
{%- if (doc.currency or 'INR') == 'INR' -%}₹ {{ '{:,.0f}'.format(amount or 0) }}/-
{%- else -%}{{ frappe.utils.fmt_money(amount or 0, currency=doc.currency) }}/-
{%- endif -%}
{%- endmacro -%}
{%- set s = frappe.get_cached_doc('IC Settings') -%}
{%- set legal = s.legal_name or 'INSTACERTIFY LABS PRIVATE LIMITED' -%}
{%- set phone = s.phone or '+91 9999118039' -%}
{%- set email = s.email or 'contact@instacertify.com' -%}
{%- set website = s.website or 'www.instacertify.com' -%}
{%- set cin = s.cin or 'U74999UP2022PTC170291' -%}
{%- set gstin = s.gstin or '09AAGCI8396C1Z7' -%}
{%- set address = (s.address_line or 'PK 01 SECTOR 63A NOIDA, GAUTAM BUDDHA NAGAR, UTTAR PRADESH-201301, INDIA').replace('\\n', '<br>') -%}
{%- set logo = s.header_image or s.logo or '/assets/instacertify/images/instacertify_logo.png' -%}
{%- set stamp = s.stamp_image or '/assets/instacertify/images/instacertify_stamp.png' -%}
{%- set quote_no = doc.ic_quote_number or doc.name -%}
{%- set title = doc.ic_service_name or 'Consultancy' -%}
{%- set short = (doc.ic_certification_type or title) -%}
<style>
  @page { size: A4; margin: 12mm; }
  .cq { font-family: Arial, Helvetica, 'Segoe UI', sans-serif; color:#222; font-size:10.5px; line-height:1.5; }
  .cq * { box-sizing: border-box; }
  .cq-head { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; padding-bottom:8px; border-bottom:1.5px solid #EC6820; margin-bottom:12px; }
  .cq-logo img { max-height:58px; max-width:320px; }
  .cq-co { text-align:right; color:#222; font-size:10px; line-height:1.4; }
  .cq-co .name { color:#EC6820; font-weight:700; font-size:12.5px; letter-spacing:0.2px; margin-bottom:2px; text-transform:uppercase; }
  .cq-meta { display:flex; justify-content:space-between; margin:12px 0 4px; font-size:11px; font-weight:700; }
  .cq-title { text-align:center; font-size:22px; font-weight:700; margin:10px 0 14px; color:#111; }
  .cq-service { text-align:center; font-size:14px; font-weight:700; margin:0 0 14px; }
  .cq-box { border:1px solid #333; margin-bottom:0; }
  .cq-sec { border-top:1px solid #333; }
  .cq-sec:first-child { border-top:none; }
  .cq-bar { background:#efefef; font-weight:700; padding:8px 12px; border-bottom:1px solid #333; font-size:11px; text-transform:uppercase; letter-spacing:0.2px; }
  .cq-body { padding:12px 14px; }
  .cq-body ul, .cq-body ol { margin:6px 0 0 18px; padding:0; }
  .cq-body li { margin-bottom:4px; }
  .cq-h { font-weight:700; margin:0 0 6px; }
  table.cq-comm { width:100%; border-collapse:collapse; margin-top:6px; }
  table.cq-comm th { background:#f5f5f5; border:1px solid #555; padding:8px; text-align:left; }
  table.cq-comm td { border:1px solid #555; padding:8px; vertical-align:top; }
  table.cq-comm td.amt { text-align:right; white-space:nowrap; font-weight:600; width:32%; }
  table.cq-bank { width:100%; border-collapse:collapse; margin-top:6px; }
  table.cq-bank td { border:1px solid #555; padding:7px 8px; }
  table.cq-bank td.k { width:34%; background:#f5f5f5; font-weight:600; }
  .cq-close { margin-top:28px; page-break-inside:avoid; }
  .cq-stamp img { max-height:110px; max-width:140px; margin-top:16px; }
  .cq-sign { margin-top:8px; font-weight:700; }
  .cq-footer-bar {
    background: linear-gradient(90deg, #d85a16 0%, #EC6820 50%, #d85a16 100%);
    color:#fff; text-align:center; padding:5px 12px; margin-top:24px;
    font-size:10px; font-weight:500; letter-spacing:0.14em; text-transform:lowercase;
    border:none; line-height:1.2;
  }
  .cq-qr { float:right; margin:8px 0 0 12px; text-align:center; }
  .cq-qr img { width:72px; height:72px; }
  .cq-qr .cap { font-size:8px; color:#555; }
  .print-format { padding:0 !important; margin:0 !important; }
</style>
<div class="cq">
  <div class="cq-head">
    <div class="cq-logo"><img src="{{ logo }}" alt="Instacertify"/></div>
    <div class="cq-co">
      <div class="name">{{ legal }}</div>
      <div>{{ address }}</div>
      <div>☎ {{ phone }}</div>
      <div>✉ {{ email }}</div>
      <div>{{ website }}</div>
      <div><b>CIN :</b> {{ cin }}</div>
      <div><b>GSTIN :</b> {{ gstin }}</div>
    </div>
  </div>

  <div class="cq-meta">
    <div>No: {{ quote_no }}</div>
    <div>Date: {{ frappe.utils.formatdate(doc.transaction_date, 'dd-MM-yyyy') }}</div>
  </div>
  <div class="cq-title">Quotation</div>
  <div class="cq-service">{{ title }}</div>

  <div class="cq-box">
    <div class="cq-sec">
      <div class="cq-bar">ABOUT {{ short }}</div>
      <div class="cq-body">
        {% if doc.ic_about_service %}{{ doc.ic_about_service }}
        {% else %}{{ doc.ic_scope_of_work or '' }}{% endif %}
      </div>
    </div>

    <div class="cq-sec">
      <div class="cq-bar">STANDARD APPLICABLE FOR {{ short }}</div>
      <div class="cq-body">
        {% if doc.ic_standard_narrative %}
          {{ doc.ic_standard_narrative }}
        {% else %}
          <p><b>Standard Applicable:</b> {{ doc.ic_applicable_standard or '' }}</p>
        {% endif %}
      </div>
    </div>

    <div class="cq-sec">
      <div class="cq-bar">Process for {{ short }}</div>
      <div class="cq-body">
        {% if doc.ic_process_steps %}{{ doc.ic_process_steps }}
        {% else %}<p></p>{% endif %}
      </div>
    </div>

    <div class="cq-sec">
      <div class="cq-bar">Validity of {{ short }}</div>
      <div class="cq-body">
        {% if doc.ic_validity_text %}{{ doc.ic_validity_text }}
        {% else %}<p></p>{% endif %}
      </div>
    </div>

    <div class="cq-sec">
      <div class="cq-bar">Commercials for {{ short }}</div>
      <div class="cq-body">
        <div class="cq-h">Commercials – {{ title }}</div>
        {% if doc.ic_applicable_standard %}
          <div style="margin-bottom:8px;"><b>Applicable Standard:</b> {{ doc.ic_applicable_standard }}</div>
        {% endif %}
        <table class="cq-comm">
          <thead><tr><th>Particulars</th><th style="text-align:right;">Charges ({{ doc.currency or 'INR' }})</th></tr></thead>
          <tbody>
          {% for row in doc.ic_cost_items or [] %}
            <tr>
              <td>{{ row.particulars or row.description or row.cost_component }}</td>
              <td class="amt">
                {% if row.charges_display %}{{ row.charges_display }}
                {% else %}{{ inr(row.amount) }}{% endif %}
              </td>
            </tr>
          {% endfor %}
          </tbody>
        </table>
        {% if doc.ic_commercials_notes %}
          <div style="margin-top:10px;">{{ doc.ic_commercials_notes }}</div>
        {% endif %}
      </div>
    </div>

    <div class="cq-sec">
      <div class="cq-bar">PAYMENT TERMS FOR {{ short }}</div>
      <div class="cq-body">
        <div class="cq-h">Payment Terms &amp; Conditions</div>
        {% if doc.ic_payment_terms %}{{ doc.ic_payment_terms }}
        {% else %}
          <ul>
            <li>Professional Consultancy Charges shall be payable upon confirmation of the project and commencement of consultancy services.</li>
            <li>Government Fees and Product Testing Charges shall be payable in advance.</li>
            <li>GST @ 18% shall be applicable on Professional Consultancy Charges as per prevailing Government taxation regulations.</li>
            <li>This quotation is valid for {{ doc.ic_validity_days or 90 }} days from the date of issuance unless otherwise specified.</li>
          </ul>
        {% endif %}
      </div>
    </div>

    <div class="cq-sec">
      <div class="cq-bar">Timelines for {{ short }}</div>
      <div class="cq-body">
        {% if doc.ic_timeline_details %}{{ doc.ic_timeline_details }}
        {% elif doc.ic_estimated_timeline %}
          <p><b>Estimated Timeline:</b> {{ doc.ic_estimated_timeline }}</p>
        {% endif %}
      </div>
    </div>

    <div class="cq-sec">
      <div class="cq-bar">SAMPLE REQUIRED FOR {{ short }}</div>
      <div class="cq-body">
        <div class="cq-h">Sample Required</div>
        {% if doc.ic_sample_required %}{{ doc.ic_sample_required }}
        {% else %}
          <p>One (01) product sample with complete accessories, packaging, technical specifications, and user manual shall be required for testing at a BIS-recognized laboratory. Additional samples, if required, shall be provided by the applicant.</p>
        {% endif %}
      </div>
    </div>

    <div class="cq-sec">
      <div class="cq-bar">DOCUMENTS REQUIRED FOR {{ short }}</div>
      <div class="cq-body">
        {% if doc.ic_documents_required %}{{ doc.ic_documents_required }}
        {% else %}<p></p>{% endif %}
      </div>
    </div>

    <div class="cq-sec">
      <div class="cq-bar">OUR BANKING DETAILS FOR {{ short }}</div>
      <div class="cq-body">
        <div class="cq-h">Bank Details for Payment</div>
        <table class="cq-bank">
          <tr><td class="k">Particulars</td><td><b>Details</b></td></tr>
          <tr><td class="k">Beneficiary Name</td><td>{{ s.beneficiary_name or 'Instacertify Labs Private Limited' }}</td></tr>
          <tr><td class="k">Bank Name</td><td>{{ s.bank_name or 'YES BANK' }}</td></tr>
          <tr><td class="k">Account Number</td><td>{{ s.account_number or '026485800001318' }}</td></tr>
          <tr><td class="k">IFSC Code</td><td>{{ s.ifsc_code or 'YESB0000264' }}</td></tr>
          <tr><td class="k">SWIFT Code</td><td>{{ s.swift_code or 'YESBINBBDEL (For International USD Transfers)' }}</td></tr>
          <tr><td class="k">GSTIN</td><td>{{ s.gstin or '09AAGCI8396C1Z7' }}</td></tr>
          <tr><td class="k">Branch Address</td><td>{{ s.bank_branch_address or 'Ground, Mezzanine & First Floor, Plot No. 6, Basant Lok, Vasant Vihar, New Delhi, Delhi – 110057, India' }}</td></tr>
        </table>
        <div style="margin-top:8px;"><b>Kindly share the payment transaction details/remittance advice after making the payment for our records and further processing.</b></div>
      </div>
    </div>

    <div class="cq-sec">
      <div class="cq-bar">CANCELLATION &amp; REFUND POLICY FOR {{ short }}</div>
      <div class="cq-body">
        <div class="cq-h">Cancellation &amp; Refund Policy</div>
        {% if doc.ic_cancellation_policy %}{{ doc.ic_cancellation_policy }}
        {% else %}
          Testing fees are payable in advance and are non-refundable once samples have been submitted or testing has commenced. Government fees may be refunded only if they have not been deposited with the relevant authority. Consultancy fees are charged based on the work completed and are non-refundable once services have been rendered. Any eligible refund request must be submitted to Instacertify in writing within 7 working days of payment.
        {% endif %}
      </div>
    </div>

    <div class="cq-sec">
      <div class="cq-bar">FORCE MAJEURE FOR {{ short }}</div>
      <div class="cq-body">
        {% if doc.ic_force_majeure %}{{ doc.ic_force_majeure }}
        {% else %}
          Instacertify Labs Pvt. Ltd. shall not be liable for any delay or failure in performing its obligations due to circumstances beyond its reasonable control, including but not limited to natural disasters, acts of government, regulatory changes, strikes, pandemics, war, civil unrest, transportation disruptions, laboratory delays, or certification authority actions. Any affected timelines shall be extended accordingly, and both parties shall make reasonable efforts to minimize the impact of such events
        {% endif %}
      </div>
    </div>

    <div class="cq-sec">
      <div class="cq-bar">CONFIDENTIALITY &amp; DATA PROTECTION FOR {{ short }}</div>
      <div class="cq-body">
        {% if doc.ic_confidentiality %}{{ doc.ic_confidentiality }}
        {% else %}
          Instacertify Labs Pvt. Ltd. shall maintain strict confidentiality of all documents, technical information, business data, and records shared by the Client. Such information will be used solely for the purpose of providing the agreed services and will not be disclosed to any third party except where required by law, regulatory authorities, laboratories, or certification bodies. Reasonable measures shall be implemented to ensure data security and protection
        {% endif %}
      </div>
    </div>
  </div>

  <div class="cq-close">
    <div class="cq-qr">
      {% if doc.ic_qr_code %}
        <img src="{{ doc.ic_qr_code }}" alt="QR"/>
      {% else %}
        <img src="{{ get_qr_code_data_uri(frappe.utils.get_url() + '/ic-verify/Quotation/' + doc.name) }}" alt="QR"/>
      {% endif %}
      <div class="cap">Scan to verify</div>
    </div>
    <p>For other Product Certification and Compliance, please visit us at {{ website }} for more details.</p>
    <p><b>Thanking You,</b></p>
    <div class="cq-stamp"><img src="{{ stamp }}" alt="Company Stamp"/></div>
    <div class="cq-sign">For Instacertify Labs Private Limited</div>
  </div>
  <div style="clear:both;"></div>
  <div class="cq-footer-bar">www.instacertify.com</div>
</div>
"""


def ensure_print_formats():
	formats = [
		("Instacertify Quotation", "Quotation", QUOTATION_HTML),
		("Instacertify Consulting Quotation", "Quotation", CONSULTING_QUOTATION_HTML),
		("Instacertify Testing Quotation", "Quotation", TESTING_QUOTATION_HTML),
		("Instacertify Sales Invoice", "Sales Invoice", INVOICE_HTML),
		("Instacertify Sample Label", "IC Sample Tracking", SAMPLE_HTML),
		("Instacertify Testing Request", "IC Testing Request", TESTING_HTML),
		("Instacertify Joining Letter", "IC Joining Letter", JOINING_HTML),
	]
	for name, dt, html in formats:
		values = {
			"html": html,
			"module": "Instacertify",
			"standard": "No",
			"custom_format": 1,
			"print_format_type": "Jinja",
			"doc_type": dt,
			# Chrome avoids wkhtmltopdf HostNotFound on .localhost asset URLs
			"pdf_generator": "chrome",
		}
		try:
			if frappe.db.exists("Print Format", name):
				# pdf_generator field exists on Frappe 16 Print Format
				frappe.db.set_value("Print Format", name, values, update_modified=False)
			else:
				frappe.get_doc({"doctype": "Print Format", "name": name, **values}).insert(
					ignore_permissions=True
				)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Print Format {name}")

	# Prefer Instacertify Quotation as the Quotation default print format
	_ensure_default_print_format("Quotation", "Instacertify Quotation")
	_ensure_default_print_format("Sales Invoice", "Instacertify Sales Invoice")
	_ensure_default_print_format("IC Sample Tracking", "Instacertify Sample Label")
	_ensure_default_print_format("IC Testing Request", "Instacertify Testing Request")
	_ensure_default_print_format("IC Joining Letter", "Instacertify Joining Letter")

	# Prefer Chrome system-wide when Print Settings supports it
	try:
		if frappe.get_meta("Print Settings").has_field("pdf_generator"):
			frappe.db.set_single_value("Print Settings", "pdf_generator", "chrome")
	except Exception:
		pass


def _ensure_default_print_format(doctype: str, print_format: str):
	"""Set DocType default_print_format via Property Setter when missing/outdated."""
	if not frappe.db.exists("Print Format", print_format):
		return
	ps_name = f"{doctype}-main-default_print_format"
	try:
		if frappe.db.exists("Property Setter", ps_name):
			frappe.db.set_value("Property Setter", ps_name, "value", print_format, update_modified=False)
		else:
			frappe.get_doc(
				{
					"doctype": "Property Setter",
					"doctype_or_field": "DocType",
					"doc_type": doctype,
					"property": "default_print_format",
					"property_type": "Data",
					"value": print_format,
					"name": ps_name,
				}
			).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"Default print format {doctype}")