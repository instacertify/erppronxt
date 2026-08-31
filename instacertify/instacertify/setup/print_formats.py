# Copyright (c) Instacertify
"""Print format HTML for Instacertify documents."""

from __future__ import annotations

import frappe

# Shared bank details block (expects `s` = IC Settings in Jinja context).
# UPI ID is shown as text only — no QR image on quotation/invoice prints.
BANK_UPI_PAYMENT_HTML = """
{%- set upi_id = s.upi_id or 'yespay.bizsbiz31008@yesbankltd' -%}
<table class="ic-bank-tbl" style="width:100%;border-collapse:collapse;margin-top:6px;">
  <tr><td class="k" style="width:34%;background:#f5f5f5;font-weight:600;border:1px solid #555;padding:7px 8px;">Particulars</td><td style="border:1px solid #555;padding:7px 8px;"><b>Details</b></td></tr>
  <tr><td class="k" style="width:34%;background:#f5f5f5;font-weight:600;border:1px solid #555;padding:7px 8px;">Beneficiary Name</td><td style="border:1px solid #555;padding:7px 8px;">{{ s.beneficiary_name or 'Instacertify Labs Private Limited' }}</td></tr>
  <tr><td class="k" style="width:34%;background:#f5f5f5;font-weight:600;border:1px solid #555;padding:7px 8px;">Bank Name</td><td style="border:1px solid #555;padding:7px 8px;">{{ s.bank_name or 'YES BANK' }}</td></tr>
  <tr><td class="k" style="width:34%;background:#f5f5f5;font-weight:600;border:1px solid #555;padding:7px 8px;">Account Number</td><td style="border:1px solid #555;padding:7px 8px;">{{ s.account_number or '026485800001318' }}</td></tr>
  <tr><td class="k" style="width:34%;background:#f5f5f5;font-weight:600;border:1px solid #555;padding:7px 8px;">IFSC Code</td><td style="border:1px solid #555;padding:7px 8px;">{{ s.ifsc_code or 'YESB0000264' }}</td></tr>
  <tr><td class="k" style="width:34%;background:#f5f5f5;font-weight:600;border:1px solid #555;padding:7px 8px;">UPI ID</td><td style="border:1px solid #555;padding:7px 8px;"><b>{{ upi_id }}</b></td></tr>
  <tr><td class="k" style="width:34%;background:#f5f5f5;font-weight:600;border:1px solid #555;padding:7px 8px;">SWIFT Code</td><td style="border:1px solid #555;padding:7px 8px;">{{ s.swift_code or 'YESBINBBDEL (For International USD Transfers)' }}</td></tr>
  <tr><td class="k" style="width:34%;background:#f5f5f5;font-weight:600;border:1px solid #555;padding:7px 8px;">GSTIN</td><td style="border:1px solid #555;padding:7px 8px;">{{ s.gstin or '09AAGCI8396C1Z7' }}</td></tr>
  <tr><td class="k" style="width:34%;background:#f5f5f5;font-weight:600;border:1px solid #555;padding:7px 8px;">Branch Address</td><td style="border:1px solid #555;padding:7px 8px;">{{ s.bank_branch_address or 'Ground, Mezzanine & First Floor, Plot No. 6, Basant Lok, Vasant Vihar, New Delhi, Delhi – 110057, India' }}</td></tr>
</table>
<div style="margin-top:8px;"><b>Kindly share the payment transaction details/remittance advice after making the payment for our records and further processing.</b></div>
"""

# Instacertify Aptos Display / Aptos print typography (quotations + printable docs)
# Hierarchy: Display for titles/headings; Aptos for body/tables/terms.
# Quote print look: black text with grey-highlighted section/step bars.
IC_PRINT_TYPOGRAPHY_CSS = """
  @font-face {
    font-family: 'Aptos Display';
    src: url('/assets/instacertify/fonts/aptos/Aptos-Display.ttf') format('truetype');
    font-weight: 400;
    font-style: normal;
    font-display: swap;
  }
  @font-face {
    font-family: 'Aptos Display';
    src: url('/assets/instacertify/fonts/aptos/Aptos-Display-Bold.ttf') format('truetype');
    font-weight: 600 700;
    font-style: normal;
    font-display: swap;
  }
  @font-face {
    font-family: 'Aptos';
    src: url('/assets/instacertify/fonts/aptos/Aptos.ttf') format('truetype');
    font-weight: 400;
    font-style: normal;
    font-display: swap;
  }
  @font-face {
    font-family: 'Aptos';
    src: url('/assets/instacertify/fonts/aptos/Aptos-Bold.ttf') format('truetype');
    font-weight: 600 700;
    font-style: normal;
    font-display: swap;
  }
  :root {
    --ic-navy: #111111;
    --ic-orange: #EC691F;
    --ic-ink: #111111;
    --ic-soft: #E8E8E8;
    --ic-soft-mid: #D9D9D9;
    --ic-white: #FFFFFF;
  }
  .ic-font-body, .ic-quote, .ic-inv, .tq, .cq, .ic, .ic-sheet {
    font-family: 'Aptos', 'Segoe UI', Calibri, Arial, sans-serif;
    color: var(--ic-ink);
    font-size: 10px;
    line-height: 1.45;
    font-weight: 400;
  }
  .ic-doc-title, .tq-title, .cq-title {
    font-family: 'Aptos Display', 'Aptos', 'Segoe UI', sans-serif !important;
    font-weight: 700 !important;
    font-size: 16pt !important;
    color: #111111 !important;
    letter-spacing: 0.01em;
    text-transform: none !important;
    text-align: center;
    margin: 8px 0 10px !important;
    line-height: 1.2;
  }
  .ic-doc-subtitle, .cq-service {
    font-family: 'Aptos Display', 'Aptos', 'Segoe UI', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14pt !important;
    color: #111111 !important;
    text-transform: none !important;
    text-align: center;
    margin: 0 0 12px !important;
    line-height: 1.25;
  }
  .ic-section-heading, .tq-label, .cq-bar, .ic-box > h3, .tq-h, .cq-h {
    font-family: 'Aptos Display', 'Aptos', 'Segoe UI', sans-serif !important;
    font-weight: 600 !important;
    font-size: 11pt !important;
    color: #111111 !important;
    letter-spacing: 0.01em;
    text-transform: none !important;
  }
  /* Grey-highlighted step / section bars — normal case, not ALL CAPS */
  .tq-label, .cq-bar {
    font-size: 10.5pt !important;
    background: #E8E8E8 !important;
    color: #111111 !important;
    text-transform: none !important;
  }
  .ic-subheading {
    font-family: 'Aptos', 'Segoe UI', sans-serif !important;
    font-weight: 500 !important;
    font-size: 12pt !important;
    color: #111111 !important;
  }
  .ic-quote-no, .tq-meta, .cq-meta {
    font-family: 'Aptos', 'Segoe UI', sans-serif !important;
    font-weight: 600 !important;
    font-size: 9.5pt !important;
    color: #111111 !important;
  }
  .ic-lh-co .name, .tq-co .name, .cq-co .name {
    font-family: 'Aptos Display', 'Aptos', sans-serif !important;
    font-weight: 600 !important;
    font-size: 12.5px !important;
    color: #111111 !important;
    text-transform: none !important;
  }
  .ic-lh, .tq-head, .cq-head {
    border-bottom-color: var(--ic-orange) !important;
    background: transparent;
  }
  #header-html {
    width: 100%;
    box-sizing: border-box;
  }
  #header-html .ic-lh,
  #header-html .tq-head,
  #header-html .cq-head {
    margin-bottom: 0 !important;
  }
  table.ic-table th, table.tq-comm th, table.cq-comm th, .ic-inv th {
    font-family: 'Aptos', 'Segoe UI', sans-serif !important;
    font-weight: 600 !important;
    font-size: 9.5pt !important;
    background: #D0D0D0 !important;
    color: #111111 !important;
  }
  table.ic-table td, table.tq-comm td, table.cq-comm td, .ic-inv td {
    font-family: 'Aptos', 'Segoe UI', sans-serif !important;
    font-weight: 400 !important;
    color: #111111 !important;
  }
  /* Numbered / bulleted process steps — black on light grey wash */
  .cq-body ol li, .cq-body ul li, .tq-value ol li, .tq-value ul li,
  .ic-box ol li, .ic-box ul li {
    color: #111111 !important;
  }
  .cq-body ol > li, .tq-value ol > li, .ic-process-steps ol > li {
    background: #F3F3F3;
    border-left: 3px solid #C8C8C8;
    padding: 4px 8px;
    margin-bottom: 6px !important;
    list-style-position: inside;
  }

  .ic-terms, .tq-note, .cq-body .ic-terms {
    font-family: 'Aptos', 'Segoe UI', sans-serif !important;
    font-weight: 400 !important;
    font-size: 8.75pt !important;
    color: #111111 !important;
  }
  .ic-footer-bar, .tq-footer-bar, .cq-footer-bar {
    font-family: 'Aptos', 'Segoe UI', sans-serif !important;
    font-weight: 400 !important;
    font-size: 8.5pt !important;
    background: linear-gradient(90deg, #d85a16 0%, var(--ic-orange) 50%, #d85a16 100%) !important;
  }
  .ic-accent-text { color: var(--ic-orange) !important; }
  .ic-soft-block { background: var(--ic-soft) !important; }
  table.tq-comm td.amt, table.cq-comm td.amt, .ic-grand-total {
    color: #111111 !important;
  }
"""

# Visible letterhead block for quotation / invoice print bodies.
# Prefer body placement over `#header-html` alone — Chrome/wkhtmltopdf often
# strip or fail to inject `#header-html`, which made the header look "missing".
# Expects Jinja vars: logo, legal, address, phone, email, website, cin, gstin.
LETTERHEAD_BLOCK_HTML = """
<div class="ic-lh" style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;padding:0 0 10px;border-bottom:1.5px solid #EC691F;width:100%;box-sizing:border-box;background:#fff;margin:0 0 14px 0;">
  <div class="ic-lh-logo"><img src="{{ logo }}" alt="Instacertify" style="max-height:58px;max-width:320px;"/></div>
  <div class="ic-lh-co" style="text-align:right;color:#111;font-size:10px;line-height:1.4;font-family:'Aptos','Segoe UI',sans-serif;">
    <div class="name" style="color:#111;font-family:'Aptos Display','Aptos',sans-serif;font-weight:600;font-size:12.5px;text-transform:none;margin-bottom:2px;">{{ legal }}</div>
    <div>{{ address }}</div>
    <div>Phone: {{ phone }}</div>
    <div>Email: {{ email }}</div>
    {% if website %}<div>{{ website }}</div>{% endif %}
    {% if cin %}<div><b>CIN:</b> {{ cin }}</div>{% endif %}
    {% if gstin %}<div><b>GSTIN:</b> {{ gstin }}</div>{% endif %}
  </div>
</div>
"""

# Shared Jinja to load IC Settings + absolute logo URL (PDF engines need full URLs).
LETTERHEAD_CONTEXT_JINJA = """
{%- set s = frappe.get_cached_doc('IC Settings') -%}
{%- set legal = s.legal_name or 'Instacertify Labs Private Limited' -%}
{%- set phone = s.phone or '+91 9999118039' -%}
{%- set email = s.email or 'contact@instacertify.com' -%}
{%- set website = s.website or 'www.instacertify.com' -%}
{%- set cin = s.cin or 'U74999UP2022PTC170291' -%}
{%- set gstin = s.gstin or '09AAGCI8396C1Z7' -%}
{%- set address = (s.address_line or 'PK 01 SECTOR 63A NOIDA, GAUTAM BUDDHA NAGAR, UTTAR PRADESH-201301, INDIA').replace('\\n', '<br>') -%}
{%- set logo_raw = s.header_image or s.logo or '/assets/instacertify/images/instacertify_letterhead.png' -%}
{%- if logo_raw and (logo_raw.startswith('http://') or logo_raw.startswith('https://') or logo_raw.startswith('data:')) -%}
{%- set logo = logo_raw -%}
{%- else -%}
{%- set logo = frappe.utils.get_url(logo_raw) -%}
{%- endif -%}
"""

# Kept for callers that still compose with the old name — body letterhead (not header-only).
QUOTE_LETTERHEAD_HTML = LETTERHEAD_BLOCK_HTML

QUOTATION_HTML = """
""" + LETTERHEAD_CONTEXT_JINJA + """
<style>
""" + IC_PRINT_TYPOGRAPHY_CSS + """
  @page { size: A4; margin: 14mm 12mm 14mm 12mm; }
  .print-format { padding: 0 !important; margin: 0 !important; }
  .ic-quote { font-family: 'Aptos', 'Segoe UI', Calibri, Arial, sans-serif; color: var(--ic-ink); font-size: 10px; }
  .ic-lh { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; padding-bottom:8px; border-bottom:1.5px solid var(--ic-orange); margin-bottom:12px; }
  .ic-lh-logo img { max-height:58px; max-width:320px; }
  .ic-lh-co { text-align:right; color:var(--ic-ink); font-size:10px; line-height:1.4; font-family:'Aptos',sans-serif; }
  .ic-lh-co .name { color:var(--ic-navy); font-family:'Aptos Display',sans-serif; font-weight:600; font-size:12.5px; text-transform:none; margin-bottom:2px; }
  .ic-accent { color: var(--ic-orange); }
  .ic-meta { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--ic-navy); margin-bottom: 12px; font-family:'Aptos',sans-serif; font-weight:600; font-size:9.5pt; }
  .ic-box { border: 1px solid #d9e6ee; border-radius: 8px; padding: 10px 12px; margin-bottom: 12px; }
  .ic-box h3 { margin: 0 0 8px 0; color: var(--ic-navy); font-family:'Aptos Display',sans-serif; font-weight:600; font-size:15pt; border-bottom: 1px solid #ecf3f7; padding-bottom: 4px; }
  table.ic-table { width: 100%; border-collapse: collapse; margin-top: 6px; }
  table.ic-table th { background: #D0D0D0; color: #111; padding: 6px 8px; text-align: left; font-family:'Aptos',sans-serif; font-weight:600; font-size: 9.5pt; }
  table.ic-table td { border-bottom: 1px solid #e5eef3; padding: 6px 8px; font-family:'Aptos',sans-serif; font-size:9.5pt; }
  .badge-pass { background: #fff3e8; color: var(--ic-orange); padding: 2px 6px; border-radius: 10px; font-size: 9px; font-family:'Aptos',sans-serif; font-weight:600; }
  .badge-rev { background: var(--ic-soft); color: var(--ic-navy); padding: 2px 6px; border-radius: 10px; font-size: 9px; font-family:'Aptos',sans-serif; font-weight:600; }
  .ic-footer { margin-top: 24px; padding-top: 12px; border-top: 1px solid #d9e6ee; overflow: auto; page-break-inside: avoid; font-family:'Aptos',sans-serif; font-size:8.5pt; }
  .ic-qr { float: right; margin: 0 0 8px 16px; text-align: center; }
  .ic-qr img { width: 72px; height: 72px; }
  .ic-qr .cap { font-size: 8px; color: #555; font-family:'Aptos',sans-serif; }
  .ic-sign { margin-top: 28px; page-break-inside: avoid; font-family:'Aptos',sans-serif; }
  .ic-footer-bar {
    background: linear-gradient(90deg, #d85a16 0%, var(--ic-orange) 50%, #d85a16 100%);
    color:#fff; text-align:center; padding:5px 12px; margin-top:20px;
    font-family:'Aptos',sans-serif; font-size:8.5pt; font-weight:400; letter-spacing:0.14em; text-transform:lowercase;
    border:none; line-height:1.2;
  }
  .ic-grand-total { font-family:'Aptos Display',sans-serif; font-weight:700; font-size:18pt; color:var(--ic-navy); }
</style>
""" + LETTERHEAD_BLOCK_HTML + """
<div class="ic-quote">
  <div class="ic-doc-title">Quotation</div>
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
        <th>Test Name</th><th>Standard</th><th>Description</th><th>Qty</th><th>Price</th><th>Amount</th>
      </tr></thead>
      <tbody>
      {% for row in doc.ic_test_items %}
        {%- set units = row.number_of_samples or 1 -%}
        {%- set per = row.suggested_selling_price or row.per_unit_charges or (row.testing_charges / units if units and row.testing_charges else 0) -%}
        {%- set total = row.testing_charges or (per * units) -%}
        <tr>
          <td>{{ row.test_name or '' }}</td>
          <td>{{ row.applicable_standard or '' }}</td>
          <td>{{ row.description or '' }}</td>
          <td>{{ units }}</td>
          <td>{{ frappe.utils.fmt_money(per, currency=doc.currency) }}</td>
          <td>{{ frappe.utils.fmt_money(total, currency=doc.currency) }}</td>
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
      <div class="ic-grand-total">Total Quoted Value: {{ frappe.utils.fmt_money(doc.ic_total_quoted_value or doc.grand_total, currency=doc.currency) }}</div>
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

  <div class="ic-box ic-terms">
    <h3>Terms and Conditions</h3>
    {{ doc.ic_terms_and_conditions or doc.terms or '' }}
  </div>
  <div class="ic-box">
    <h3>Bank Details &amp; UPI Payment</h3>
""" + BANK_UPI_PAYMENT_HTML + """
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
""" + LETTERHEAD_CONTEXT_JINJA + """
<style>
""" + IC_PRINT_TYPOGRAPHY_CSS + """
  @page { size: A4; margin: 14mm 12mm 14mm 12mm; }
  .print-format { padding:0 !important; margin:0 !important; }
  .ic-inv { font-family: 'Aptos', 'Segoe UI', Calibri, Arial, sans-serif; font-size: 10px; color: var(--ic-ink); }
  .ic-lh { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; padding-bottom:8px; border-bottom:1.5px solid var(--ic-orange); margin-bottom:12px; }
  .ic-lh-logo img { max-height:58px; max-width:320px; }
  .ic-lh-co { text-align:right; color:var(--ic-ink); font-size:10px; line-height:1.4; font-family:'Aptos',sans-serif; }
  .ic-lh-co .name { color:var(--ic-navy); font-family:'Aptos Display',sans-serif; font-weight:600; font-size:12.5px; text-transform:none; margin-bottom:2px; }
  table { width:100%; border-collapse: collapse; margin-top:12px; }
  th { background:var(--ic-navy); color:#fff; padding:6px; text-align:left; font-family:'Aptos',sans-serif; font-weight:600; font-size:9.5pt; }
  td { border-bottom:1px solid #e5eef3; padding:6px; font-family:'Aptos',sans-serif; font-size:9.5pt; }
  .qr { text-align:right; margin-top:20px; }
  .qr img { width:72px; height:72px; }
  .ic-footer-bar {
    background: linear-gradient(90deg, #d85a16 0%, var(--ic-orange) 50%, #d85a16 100%);
    color:#fff; text-align:center; padding:5px 12px; margin-top:20px;
    font-family:'Aptos',sans-serif; font-size:8.5pt; font-weight:400; letter-spacing:0.14em; text-transform:lowercase;
    border:none; line-height:1.2;
  }
</style>
""" + LETTERHEAD_BLOCK_HTML + """
<div class="ic-inv">
  <div class="ic-doc-title">Tax Invoice</div>
  <p class="ic-quote-no"><b>Invoice:</b> {{ doc.name }} &nbsp;|&nbsp; <b>Date:</b> {{ frappe.utils.formatdate(doc.posting_date) }}</p>
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
  <p class="ic-grand-total" style="text-align:right; margin-top:12px;">Grand Total: {{ frappe.utils.fmt_money(doc.grand_total, currency=doc.currency) }}</p>
  <div style="margin-top:16px;padding:10px 12px;border:1px solid #d9e6ee;border-radius:6px;">
    <div style="font-weight:700;color:#065175;margin-bottom:8px;font-size:12px;">Bank Details &amp; UPI Payment</div>
""" + BANK_UPI_PAYMENT_HTML + """
  </div>
  <div class="qr">
    <img src="{{ get_qr_code_data_uri(frappe.utils.get_url() + '/ic-verify/Sales Invoice/' + doc.name) }}" alt="QR"/>
  </div>
  <div class="ic-footer-bar">www.instacertify.com</div>
</div>
"""

SAMPLE_HTML = """
{%- set s = frappe.get_cached_doc('IC Settings') -%}
{%- set legal = s.legal_name or 'Instacertify Labs Private Limited' -%}
{%- set phone = s.phone or '+91 9999118039' -%}
{%- set email = s.email or 'contact@instacertify.com' -%}
{%- set website = s.website or 'www.instacertify.com' -%}
{%- set cin = s.cin or 'U74999UP2022PTC170291' -%}
{%- set gstin = s.gstin or '09AAGCI8396C1Z7' -%}
{%- set address = (s.address_line or 'PK 01 SECTOR 63A NOIDA, GAUTAM BUDDHA NAGAR, UTTAR PRADESH-201301, INDIA').replace('\\n', '<br>') -%}
{%- set logo = s.header_image or s.logo or '/assets/instacertify/images/instacertify_letterhead.png' -%}
{%- set trk = doc.tracking_number or doc.name -%}
{%- set qr_payload = trk + '\\n' + (frappe.utils.get_url()|string).rstrip('/') + '/ic-verify/sample/' + trk -%}
<style>
""" + IC_PRINT_TYPOGRAPHY_CSS + """
  @page { size: A4; margin: 12mm; }
  .print-format { padding:0 !important; margin:0 !important; }
  .ic { font-family: Arial, Helvetica, 'Segoe UI', sans-serif; font-size:11px; }
  .ic-lh { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; padding-bottom:8px; border-bottom:1.5px solid #EC691F; margin-bottom:12px; }
  .ic-lh-logo img { max-height:48px; max-width:280px; }
  .ic-lh-co { text-align:right; color:#222; font-size:9.5px; line-height:1.35; }
  .ic-lh-co .name { color:#EC691F; font-weight:700; font-size:11px; text-transform:uppercase; }
  .qr-block { display:flex; align-items:center; gap:14px; margin-top:12px; }
  .qr-block img { width:90px; height:90px; image-rendering: pixelated; }
  .qr-block .trk { font-family: 'DejaVu Sans Mono', Consolas, monospace; font-size:14px; font-weight:700; color:#065175; letter-spacing:0.02em; }
  .ic-footer-bar {
    background: linear-gradient(90deg, #d85a16 0%, #EC691F 50%, #d85a16 100%);
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
      <div>{{ phone }} · {{ email }}</div>
      <div><b>CIN :</b> {{ cin }} · <b>GSTIN :</b> {{ gstin }}</div>
    </div>
  </div>
  <h2 style="margin:0 0 10px; color:#065175;">Sample Tracking Label</h2>
  <p><b>Sample Tracking No:</b> <span style="font-family:monospace;font-size:13px;">{{ trk }}</span></p>
  <p><b>Customer:</b> {{ doc.customer }}</p>
  <p><b>Description:</b> {{ doc.sample_description }}</p>
  <p><b>Status:</b> {{ doc.status }}</p>
  <p><b>Qty:</b> {{ doc.quantity }} &nbsp; <b>Condition:</b> {{ doc.sample_condition or '' }}</p>
  <div class="qr-block">
    <img src="{{ get_qr_code_data_uri(qr_payload, 5, 1) }}" alt="QR {{ trk }}"/>
    <div>
      <div style="font-size:10px;color:#666;">Scan / Sample No.</div>
      <div class="trk">{{ trk }}</div>
    </div>
  </div>
  <div class="ic-footer-bar">www.instacertify.com</div>
</div>
"""

# 50mm × 25mm sample sticker: QR + tracking number + website line
SAMPLE_STICKER_50X25_HTML = """
{%- set trk = doc.tracking_number or doc.name -%}
{%- set qr_payload = trk + '\\n' + (frappe.utils.get_url()|string).rstrip('/') + '/ic-verify/sample/' + trk -%}
<style>
  @page {
    size: 50mm 25mm;
    margin: 0;
  }
  html, body {
    margin: 0 !important;
    padding: 0 !important;
    width: 50mm;
    height: 25mm;
    overflow: hidden;
    background: #fff;
  }
  .print-format, .print-format-gutter {
    padding: 0 !important;
    margin: 0 !important;
    background: #fff !important;
  }
  .sticker {
    box-sizing: border-box;
    width: 50mm;
    height: 25mm;
    padding: 1.2mm 1.4mm 1mm 1.4mm;
    display: flex;
    flex-direction: row;
    align-items: stretch;
    justify-content: flex-start;
    gap: 1.6mm;
    font-family: 'DejaVu Sans', Arial, Helvetica, sans-serif;
    color: #000;
    background: #fff;
    overflow: hidden;
  }
  .sticker img.qr {
    width: 18mm;
    height: 18mm;
    flex: 0 0 18mm;
    align-self: center;
    image-rendering: pixelated;
    image-rendering: crisp-edges;
  }
  .sticker .meta {
    flex: 1 1 auto;
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-width: 0;
    gap: 0.6mm;
  }
  .sticker .lbl {
    font-size: 2.1mm;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #333;
    line-height: 1;
  }
  .sticker .trk {
    font-family: 'DejaVu Sans Mono', 'Courier New', monospace;
    font-size: 3.1mm;
    font-weight: 700;
    line-height: 1.1;
    letter-spacing: -0.01em;
    word-break: break-all;
    color: #000;
  }
  .sticker .info {
    margin-top: 0.4mm;
    font-size: 1.85mm;
    font-weight: 500;
    line-height: 1.25;
    color: #222;
  }
  .sticker .info b {
    font-weight: 700;
    letter-spacing: 0.01em;
  }
</style>
<div class="sticker">
  <img class="qr" src="{{ get_qr_code_data_uri(qr_payload, 6, 1) }}" alt="{{ trk }}"/>
  <div class="meta">
    <div class="lbl">Sample</div>
    <div class="trk">{{ trk }}</div>
    <div class="info">For more information visit<br><b>www.instacertify.com</b></div>
  </div>
</div>
"""

# Back-compat alias used by older references
SAMPLE_STICKER_8MM_HTML = SAMPLE_STICKER_50X25_HTML

TESTING_HTML = """
{%- set s = frappe.get_cached_doc('IC Settings') -%}
{%- set legal = s.legal_name or 'Instacertify Labs Private Limited' -%}
{%- set phone = s.phone or '+91 9999118039' -%}
{%- set email = s.email or 'contact@instacertify.com' -%}
{%- set website = s.website or 'www.instacertify.com' -%}
{%- set cin = s.cin or 'U74999UP2022PTC170291' -%}
{%- set gstin = s.gstin or '09AAGCI8396C1Z7' -%}
{%- set address = (s.address_line or 'PK 01 SECTOR 63A NOIDA, GAUTAM BUDDHA NAGAR, UTTAR PRADESH-201301, INDIA').replace('\\n', '<br>') -%}
{%- set logo = s.header_image or s.logo or '/assets/instacertify/images/instacertify_letterhead.png' -%}
<style>
""" + IC_PRINT_TYPOGRAPHY_CSS + """
  @page { size: A4; margin: 12mm; }
  .print-format { padding:0 !important; margin:0 !important; }
  .ic { font-family: Arial, Helvetica, 'Segoe UI', sans-serif; font-size:11px; }
  .ic-lh { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; padding-bottom:8px; border-bottom:1.5px solid #EC691F; margin-bottom:12px; }
  .ic-lh-logo img { max-height:48px; max-width:280px; }
  .ic-lh-co { text-align:right; color:#222; font-size:9.5px; line-height:1.35; }
  .ic-lh-co .name { color:#EC691F; font-weight:700; font-size:11px; text-transform:uppercase; }
  .ic-footer-bar {
    background: linear-gradient(90deg, #d85a16 0%, #EC691F 50%, #d85a16 100%);
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
{%- set legal = s.legal_name or 'Instacertify Labs Private Limited' -%}
{%- set phone = s.phone or '+91 9999118039' -%}
{%- set email = s.email or 'contact@instacertify.com' -%}
{%- set website = s.website or 'www.instacertify.com' -%}
{%- set cin = s.cin or 'U74999UP2022PTC170291' -%}
{%- set gstin = s.gstin or '09AAGCI8396C1Z7' -%}
{%- set address = (s.address_line or 'PK 01 SECTOR 63A NOIDA, GAUTAM BUDDHA NAGAR, UTTAR PRADESH-201301, INDIA').replace('\\n', '<br>') -%}
{%- set logo = s.header_image or s.logo or '/assets/instacertify/images/instacertify_letterhead.png' -%}
<style>
""" + IC_PRINT_TYPOGRAPHY_CSS + """
  @page { size: A4; margin: 12mm; }
  .print-format { padding:0 !important; margin:0 !important; }
  .ic { font-family: Georgia, 'Times New Roman', serif; font-size:12px; }
  .ic-lh { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; padding-bottom:8px; border-bottom:3px solid #EC691F; margin-bottom:14px; }
  .ic-lh-logo img { max-height:52px; max-width:300px; }
  .ic-lh-co { text-align:right; font-family: Arial, Helvetica, sans-serif; color:#222; font-size:10px; line-height:1.4; }
  .ic-lh-co .name { color:#EC691F; font-weight:700; font-size:12px; text-transform:uppercase; }
  .qr { text-align:right; }
  .qr img { width:72px; height:72px; }
  .ic-footer-bar {
    background: linear-gradient(90deg, #d85a16 0%, #EC691F 50%, #d85a16 100%);
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
""" + LETTERHEAD_CONTEXT_JINJA + """
{%- set stamp = s.stamp_image or '/assets/instacertify/images/instacertify_stamp.png' -%}
{%- if stamp and not (stamp.startswith('http://') or stamp.startswith('https://') or stamp.startswith('data:')) -%}
{%- set stamp = frappe.utils.get_url(stamp) -%}
{%- endif -%}
{%- set quote_no = doc.ic_quote_number or doc.name -%}
{%- set curr = doc.currency or 'INR' -%}
<style>
""" + IC_PRINT_TYPOGRAPHY_CSS + """
  @page { size: A4; margin: 14mm 12mm 14mm 12mm; }
  .tq { font-family: 'Aptos', 'Segoe UI', Calibri, Arial, sans-serif; color:var(--ic-ink); font-size:10px; line-height:1.45; }
  .tq * { box-sizing: border-box; }
  .tq-head { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; padding-bottom:8px; border-bottom:1.5px solid var(--ic-orange); margin-bottom:12px; }
  .tq-logo img { max-height:58px; max-width:320px; }
  .tq-co { text-align:right; color:var(--ic-ink); font-size:10px; line-height:1.4; font-family:'Aptos',sans-serif; }
  .tq-co .name { color:var(--ic-navy); font-family:'Aptos Display',sans-serif; font-weight:600; font-size:12.5px; letter-spacing:0.2px; margin-bottom:2px; text-transform:none; }
  .tq-meta { display:flex; justify-content:space-between; margin:12px 0 4px; font-family:'Aptos',sans-serif; font-size:9.5pt; font-weight:600; color:var(--ic-ink); }
  .tq-title { text-align:center; font-family:'Aptos Display',sans-serif; font-size:16pt; font-weight:700; margin:8px 0 12px; color:var(--ic-navy); letter-spacing:0.01em; line-height:1.2; text-transform:none; }
  table.tq-grid { width:100%; border-collapse:collapse; table-layout:fixed; margin-bottom:0; page-break-inside:auto; }
  table.tq-grid > tbody > tr { page-break-inside:avoid; }
  table.tq-grid > tbody > tr > td { border:1px solid #333; vertical-align:top; padding:0; }
  .tq-label { width:17%; background:#E8E8E8; font-family:'Aptos Display',sans-serif; font-weight:600; padding:10px 8px; color:#111; font-size:11pt; }
  .tq-value { width:83%; padding:10px 12px; font-family:'Aptos',sans-serif; font-size:10px; color:var(--ic-ink); }
  .tq-value ul { margin:6px 0 0 18px; padding:0; }
  .tq-value ol { margin:6px 0 0 18px; padding:0; }
  .tq-value li { margin-bottom:4px; }
  .tq-h { font-family:'Aptos Display',sans-serif; font-weight:600; font-size:15pt; color:var(--ic-navy); margin:0 0 6px; }
  table.tq-comm { width:100%; border-collapse:collapse; margin-top:4px; }
  table.tq-comm th { background:#D0D0D0; color:#111; border:1px solid #555; padding:7px 5px; font-family:'Aptos',sans-serif; font-size:9.5pt; text-align:center; font-weight:600; }
  table.tq-comm td { border:1px solid #555; padding:7px 5px; font-family:'Aptos',sans-serif; font-size:9.5pt; vertical-align:top; color:var(--ic-ink); }
  table.tq-comm td.num, table.tq-comm th.num { text-align:center; }
  table.tq-comm td.amt { text-align:center; white-space:nowrap; font-family:'Aptos',sans-serif; font-weight:600; font-size:10.5pt; color:var(--ic-navy); }
  .tq-note { margin-top:8px; font-family:'Aptos',sans-serif; font-size:8.75pt; color:var(--ic-ink); }
  table.tq-bank { width:100%; border-collapse:collapse; margin-top:6px; }
  table.tq-bank td { border:1px solid #555; padding:7px 8px; font-family:'Aptos',sans-serif; font-size:9.5pt; }
  table.tq-bank td.k { width:34%; background:var(--ic-soft); font-weight:600; }
  .tq-close { margin-top:28px; page-break-inside:avoid; font-family:'Aptos',sans-serif; }
  .tq-close p { margin:6px 0; }
  .tq-stamp { margin-top:18px; margin-bottom:6px; }
  .tq-stamp img { max-height:110px; max-width:140px; }
  .tq-sign { margin-top:8px; font-family:'Aptos',sans-serif; font-weight:600; }
  .tq-footer-bar {
    background: linear-gradient(90deg, #d85a16 0%, var(--ic-orange) 50%, #d85a16 100%);
    color:#fff; text-align:center; padding:5px 12px; margin-top:24px;
    font-family:'Aptos',sans-serif; font-size:8.5pt; font-weight:400; letter-spacing:0.14em; text-transform:lowercase;
    border:none; line-height:1.2;
  }
  .tq-qr { float:right; margin:8px 0 0 12px; text-align:center; }
  .tq-qr img { width:72px; height:72px; }
  .tq-qr .cap { font-size:8px; color:#555; font-family:'Aptos',sans-serif; }
  .print-format { padding:0 !important; margin:0 !important; }
</style>
""" + QUOTE_LETTERHEAD_HTML + """
<div class="tq">
<div class="tq-meta">
    <div>No: {{ quote_no }}</div>
    <div>Date: {{ frappe.utils.formatdate(doc.transaction_date, 'dd-MM-yyyy') }}</div>
  </div>
  <div class="tq-title">Quotation</div>

  <table class="tq-grid">
    <tr>
      <td class="tq-label">{{ doc.ic_label_subject or 'Subject' }}</td>
      <td class="tq-value"><b>{{ doc.ic_subject or 'Testing' }}</b></td>
    </tr>
    <tr>
      <td class="tq-label">{{ doc.ic_label_about_testing or 'ABOUT' }}</td>
      <td class="tq-value">
        {% if doc.ic_about_testing %}
          {{ doc.ic_about_testing }}
        {% else %}
          {{ doc.ic_scope_of_work or '' }}
        {% endif %}
      </td>
    </tr>
    <tr>
      <td class="tq-label">{{ doc.ic_label_applicable_standards or 'Applicable Standards' }}</td>
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
      <td class="tq-label">{{ doc.ic_label_samples_requirements or 'Samples Requirements' }}</td>
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
      <td class="tq-label">{{ doc.ic_label_commercials or 'Commercials' }}</td>
      <td class="tq-value">
        <div class="tq-h">{{ doc.ic_label_commercials or 'Commercials' }}</div>
        <table class="tq-comm">
          <thead>
            <tr>
              <th class="num" style="width:6%">S. No.</th>
              <th style="width:18%">Test Name</th>
              <th style="width:16%">Standard</th>
              <th style="width:22%">Description</th>
              <th class="num" style="width:8%">Qty</th>
              <th style="width:15%">Price ({{ curr }})</th>
              <th style="width:15%">Amount ({{ curr }})</th>
            </tr>
          </thead>
          <tbody>
          {% for row in doc.ic_test_items or [] %}
            {%- set units = row.number_of_samples or 1 -%}
            {%- set per = row.suggested_selling_price or row.per_unit_charges or (row.testing_charges / units if units and row.testing_charges else 0) -%}
            {%- set total = row.testing_charges or (per * units) -%}
            <tr>
              <td class="num">{{ loop.index }}</td>
              <td>{{ row.test_name or '' }}</td>
              <td>{{ row.applicable_standard or '' }}</td>
              <td>{{ row.description or '' }}</td>
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
      <td class="tq-label">{{ doc.ic_label_deliverable or 'Deliverable' }}</td>
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
      <td class="tq-label">{{ doc.ic_label_timeline or 'Timeline' }}</td>
      <td class="tq-value">
        <div class="tq-h">{{ doc.ic_label_timeline or 'Timeline' }}</div>
        <ul>
          <li><b>Estimated Testing Timeline:</b> {{ doc.ic_estimated_timeline or '5–7 working days' }}.</li>
          <li>The timeline shall commence upon receipt of the required sample and confirmation of payment.</li>
          <li>The timeline may vary depending on laboratory scheduling, sample condition, test requirements, and any additional testing, if applicable.</li>
        </ul>
      </td>
    </tr>
    <tr>
      <td class="tq-label">{{ doc.ic_label_payment_term or 'Payment Term' }}</td>
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
      <td class="tq-label">{{ doc.ic_label_sample_handling or 'Sample handling & disposal policy' }}</td>
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
      <td class="tq-label">{{ doc.ic_label_banking or 'Our Banking Details' }}</td>
      <td class="tq-value">
        <div class="tq-h">Bank Details for Payment</div>
""" + BANK_UPI_PAYMENT_HTML + """
      </td>
    </tr>
    <tr>
      <td class="tq-label">{{ doc.ic_label_cancellation or 'CANCELLATION AND REFUND POLICY' }}</td>
      <td class="tq-value">
        {% if doc.ic_cancellation_policy %}
          {{ doc.ic_cancellation_policy }}
        {% else %}
          Testing fees are payable in advance and are non-refundable once samples have been submitted or testing has commenced. Government fees may be refunded only if they have not been deposited with the relevant authority. Consultancy fees are charged based on the work completed and are non-refundable once services have been rendered. Any eligible refund request must be submitted to Instacertify in writing within 7 working days of payment.
        {% endif %}
      </td>
    </tr>
    <tr>
      <td class="tq-label">{{ doc.ic_label_force_majeure or 'FORCE MAJEURE' }}</td>
      <td class="tq-value">
        {% if doc.ic_force_majeure %}
          {{ doc.ic_force_majeure }}
        {% else %}
          Instacertify Labs Pvt. Ltd. shall not be liable for any delay or failure in performing its obligations due to circumstances beyond its reasonable control, including but not limited to natural disasters, acts of government, regulatory changes, strikes, pandemics, war, civil unrest, transportation disruptions, laboratory delays, or certification authority actions. Any affected timelines shall be extended accordingly, and both parties shall make reasonable efforts to minimize the impact of such events
        {% endif %}
      </td>
    </tr>
    <tr>
      <td class="tq-label">{{ doc.ic_label_confidentiality or 'CONFIDENTIALITY & DATA PROTECTION' }}</td>
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
""" + LETTERHEAD_CONTEXT_JINJA + """
{%- set stamp = s.stamp_image or '/assets/instacertify/images/instacertify_stamp.png' -%}
{%- if stamp and not (stamp.startswith('http://') or stamp.startswith('https://') or stamp.startswith('data:')) -%}
{%- set stamp = frappe.utils.get_url(stamp) -%}
{%- endif -%}
{%- set quote_no = doc.ic_quote_number or doc.name -%}
{%- set title = doc.ic_service_name or 'Consultancy' -%}
{%- set short = (doc.ic_certification_type or title) -%}
<style>
""" + IC_PRINT_TYPOGRAPHY_CSS + """
  @page { size: A4; margin: 14mm 12mm 14mm 12mm; }
  .cq { font-family: 'Aptos', 'Segoe UI', Calibri, Arial, sans-serif; color:var(--ic-ink); font-size:10px; line-height:1.5; }
  .cq * { box-sizing: border-box; }
  .cq-head { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; padding-bottom:8px; border-bottom:1.5px solid var(--ic-orange); margin-bottom:12px; }
  .cq-logo img { max-height:58px; max-width:320px; }
  .cq-co { text-align:right; color:var(--ic-ink); font-size:10px; line-height:1.4; font-family:'Aptos',sans-serif; }
  .cq-co .name { color:var(--ic-navy); font-family:'Aptos Display',sans-serif; font-weight:600; font-size:12.5px; letter-spacing:0.2px; margin-bottom:2px; text-transform:none; }
  .cq-meta { display:flex; justify-content:space-between; margin:12px 0 4px; font-family:'Aptos',sans-serif; font-size:9.5pt; font-weight:600; color:var(--ic-ink); }
  .cq-title { text-align:center; font-family:'Aptos Display',sans-serif; font-size:16pt; font-weight:700; margin:8px 0 10px; color:var(--ic-navy); letter-spacing:0.01em; line-height:1.2; text-transform:none; }
  .cq-service { text-align:center; font-family:'Aptos Display',sans-serif; font-size:14pt; font-weight:600; margin:0 0 12px; color:var(--ic-navy); line-height:1.25; text-transform:none; }
  .cq-box { border:1px solid #333; margin-bottom:0; }
  .cq-sec { border-top:1px solid #333; }
  .cq-sec:first-child { border-top:none; }
  .cq-bar { background:#E8E8E8; font-family:'Aptos Display',sans-serif; font-weight:600; padding:8px 12px; border-bottom:1px solid #333; font-size:10.5pt; text-transform:none; letter-spacing:0.01em; color:#111; }
  .cq-body { padding:12px 14px; font-family:'Aptos',sans-serif; font-size:10px; color:var(--ic-ink); }
  .cq-body ul, .cq-body ol { margin:6px 0 0 18px; padding:0; }
  .cq-body li { margin-bottom:4px; }
  .cq-h { font-family:'Aptos Display',sans-serif; font-weight:600; font-size:15pt; color:var(--ic-navy); margin:0 0 6px; }
  table.cq-comm { width:100%; border-collapse:collapse; margin-top:6px; }
  table.cq-comm th { background:#D0D0D0; color:#111; border:1px solid #555; padding:8px; text-align:left; font-family:'Aptos',sans-serif; font-weight:600; font-size:9.5pt; }
  table.cq-comm td { border:1px solid #555; padding:8px; vertical-align:top; font-family:'Aptos',sans-serif; font-size:9.5pt; color:var(--ic-ink); }
  table.cq-comm td.amt { text-align:right; white-space:nowrap; font-family:'Aptos',sans-serif; font-weight:600; font-size:10.5pt; color:var(--ic-navy); width:32%; }
  table.cq-bank { width:100%; border-collapse:collapse; margin-top:6px; }
  table.cq-bank td { border:1px solid #555; padding:7px 8px; font-family:'Aptos',sans-serif; font-size:9.5pt; }
  table.cq-bank td.k { width:34%; background:var(--ic-soft); font-weight:600; }
  .cq-close { margin-top:28px; page-break-inside:avoid; font-family:'Aptos',sans-serif; }
  .cq-stamp img { max-height:110px; max-width:140px; margin-top:16px; }
  .cq-sign { margin-top:8px; font-family:'Aptos',sans-serif; font-weight:600; }
  .cq-footer-bar {
    background: linear-gradient(90deg, #d85a16 0%, var(--ic-orange) 50%, #d85a16 100%);
    color:#fff; text-align:center; padding:5px 12px; margin-top:24px;
    font-family:'Aptos',sans-serif; font-size:8.5pt; font-weight:400; letter-spacing:0.14em; text-transform:lowercase;
    border:none; line-height:1.2;
  }
  .cq-qr { float:right; margin:8px 0 0 12px; text-align:center; }
  .cq-qr img { width:72px; height:72px; }
  .cq-qr .cap { font-size:8px; color:#555; font-family:'Aptos',sans-serif; }
  .print-format { padding:0 !important; margin:0 !important; }
</style>
""" + QUOTE_LETTERHEAD_HTML + """
<div class="cq">
<div class="cq-meta">
    <div>No: {{ quote_no }}</div>
    <div>Date: {{ frappe.utils.formatdate(doc.transaction_date, 'dd-MM-yyyy') }}</div>
  </div>
  <div class="cq-title">Quotation</div>
  <div class="cq-service">{{ title }}</div>

  <div class="cq-box">
    <div class="cq-sec">
      <div class="cq-bar">{{ doc.ic_label_about or ('ABOUT ' ~ short) }}</div>
      <div class="cq-body">
        {% if doc.ic_about_service %}{{ doc.ic_about_service }}
        {% else %}{{ doc.ic_scope_of_work or '' }}{% endif %}
      </div>
    </div>

    <div class="cq-sec">
      <div class="cq-bar">{{ doc.ic_label_standard or ('STANDARD APPLICABLE FOR ' ~ short) }}</div>
      <div class="cq-body">
        {% if doc.ic_standard_narrative %}
          {{ doc.ic_standard_narrative }}
        {% else %}
          <p><b>Standard Applicable:</b> {{ doc.ic_applicable_standard or '' }}</p>
        {% endif %}
      </div>
    </div>

    <div class="cq-sec">
      <div class="cq-bar">{{ doc.ic_label_process or ('Process for ' ~ short) }}</div>
      <div class="cq-body">
        {% if doc.ic_process_steps %}{{ doc.ic_process_steps }}
        {% else %}<p></p>{% endif %}
      </div>
    </div>

    <div class="cq-sec">
      <div class="cq-bar">{{ doc.ic_label_validity or ('Validity of ' ~ short) }}</div>
      <div class="cq-body">
        {% if doc.ic_validity_text %}{{ doc.ic_validity_text }}
        {% else %}<p></p>{% endif %}
      </div>
    </div>

    <div class="cq-sec">
      <div class="cq-bar">{{ doc.ic_label_commercials or ('Commercials for ' ~ short) }}</div>
      <div class="cq-body">
        <div class="cq-h">{{ doc.ic_label_commercials or ('Commercials – ' ~ title) }}</div>
        {% if doc.ic_applicable_standard %}
          <div style="margin-bottom:8px;"><b>Applicable Standard:</b> {{ doc.ic_applicable_standard }}</div>
        {% endif %}
        <table class="cq-comm">
          <thead><tr><th>{{ doc.ic_label_particulars_col or 'Particulars' }}</th><th style="text-align:right;">{{ doc.ic_label_charges_col or 'Charges' }} ({{ doc.currency or 'INR' }})</th></tr></thead>
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
      <div class="cq-bar">{{ doc.ic_label_payment_terms or ('PAYMENT TERMS FOR ' ~ short) }}</div>
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
      <div class="cq-bar">{{ doc.ic_label_timelines or ('Timelines for ' ~ short) }}</div>
      <div class="cq-body">
        {% if doc.ic_timeline_details %}{{ doc.ic_timeline_details }}
        {% elif doc.ic_estimated_timeline %}
          <p><b>Estimated Timeline:</b> {{ doc.ic_estimated_timeline }}</p>
        {% endif %}
      </div>
    </div>

    <div class="cq-sec">
      <div class="cq-bar">{{ doc.ic_label_sample_required or ('SAMPLE REQUIRED FOR ' ~ short) }}</div>
      <div class="cq-body">
        <div class="cq-h">Sample Required</div>
        {% if doc.ic_sample_required %}{{ doc.ic_sample_required }}
        {% else %}
          <p>One (01) product sample with complete accessories, packaging, technical specifications, and user manual shall be required for testing at a BIS-recognized laboratory. Additional samples, if required, shall be provided by the applicant.</p>
        {% endif %}
      </div>
    </div>

    <div class="cq-sec">
      <div class="cq-bar">{{ doc.ic_label_documents_required or ('DOCUMENTS REQUIRED FOR ' ~ short) }}</div>
      <div class="cq-body">
        {% if doc.ic_documents_required %}{{ doc.ic_documents_required }}
        {% else %}<p></p>{% endif %}
      </div>
    </div>

    <div class="cq-sec">
      <div class="cq-bar">{{ doc.ic_label_banking or ('OUR BANKING DETAILS FOR ' ~ short) }}</div>
      <div class="cq-body">
        <div class="cq-h">Bank Details for Payment</div>
""" + BANK_UPI_PAYMENT_HTML + """
      </div>
    </div>

    <div class="cq-sec">
      <div class="cq-bar">{{ doc.ic_label_cancellation or ('CANCELLATION & REFUND POLICY FOR ' ~ short) }}</div>
      <div class="cq-body">
        <div class="cq-h">Cancellation &amp; Refund Policy</div>
        {% if doc.ic_cancellation_policy %}{{ doc.ic_cancellation_policy }}
        {% else %}
          Testing fees are payable in advance and are non-refundable once samples have been submitted or testing has commenced. Government fees may be refunded only if they have not been deposited with the relevant authority. Consultancy fees are charged based on the work completed and are non-refundable once services have been rendered. Any eligible refund request must be submitted to Instacertify in writing within 7 working days of payment.
        {% endif %}
      </div>
    </div>

    <div class="cq-sec">
      <div class="cq-bar">{{ doc.ic_label_force_majeure or ('FORCE MAJEURE FOR ' ~ short) }}</div>
      <div class="cq-body">
        {% if doc.ic_force_majeure %}{{ doc.ic_force_majeure }}
        {% else %}
          Instacertify Labs Pvt. Ltd. shall not be liable for any delay or failure in performing its obligations due to circumstances beyond its reasonable control, including but not limited to natural disasters, acts of government, regulatory changes, strikes, pandemics, war, civil unrest, transportation disruptions, laboratory delays, or certification authority actions. Any affected timelines shall be extended accordingly, and both parties shall make reasonable efforts to minimize the impact of such events
        {% endif %}
      </div>
    </div>

    <div class="cq-sec">
      <div class="cq-bar">{{ doc.ic_label_confidentiality or ('CONFIDENTIALITY & DATA PROTECTION FOR ' ~ short) }}</div>
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


DOCUMENTS_COLLECTION_HTML = """
{%- set s = frappe.get_cached_doc('IC Settings') -%}
{%- set legal = s.legal_name or 'Instacertify Labs Private Limited' -%}
{%- set logo = s.header_image or s.logo or '/assets/instacertify/images/instacertify_letterhead.png' -%}
<style>
""" + IC_PRINT_TYPOGRAPHY_CSS + """
  @page { size: A4; margin: 12mm; }
  .print-format { padding: 0 !important; margin: 0 !important; }
  .ic-sheet { font-family: Arial, Helvetica, sans-serif; color:#1a1a1a; font-size:11px; }
  .ic-lh { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; padding-bottom:8px; border-bottom:1.5px solid #EC691F; margin-bottom:12px; }
  .ic-lh-logo img { max-height:58px; max-width:320px; }
  .ic-title { color:#065175; font-size:16px; font-weight:700; margin:8px 0 4px; }
  .ic-sub { color:#555; margin-bottom:12px; }
  .ic-box { border:1px solid #d9e6ee; border-radius:8px; padding:10px 12px; margin-bottom:12px; }
  .ic-box h3 { margin:0 0 8px; color:#065175; font-size:13px; border-bottom:1px solid #ecf3f7; padding-bottom:4px; }
  table.ic-table { width:100%; border-collapse:collapse; margin-top:6px; }
  table.ic-table th { background:#065175; color:#fff; padding:6px 8px; text-align:left; font-size:10px; }
  table.ic-table td { border-bottom:1px solid #e5eef3; padding:6px 8px; }
  .ic-meta { margin-bottom:10px; }
  .ic-footer-bar { background:linear-gradient(90deg,#d85a16 0%,#EC691F 50%,#d85a16 100%); color:#fff; text-align:center; padding:5px 12px; margin-top:20px; font-size:10px; letter-spacing:0.14em; }
</style>
<div class="ic-sheet">
  <div class="ic-lh">
    <div class="ic-lh-logo"><img src="{{ logo }}" alt="Instacertify"/></div>
    <div style="text-align:right;font-size:10px;line-height:1.4;">{{ legal }}</div>
  </div>
  <div class="ic-title">Documents Collection Sheet</div>
  <div class="ic-sub">List of Documents + Data Collection Sheet</div>
  <div class="ic-meta">
    <b>Sheet:</b> {{ doc.name }} &nbsp;|&nbsp; <b>Title:</b> {{ doc.title }} &nbsp;|&nbsp; <b>Status:</b> {{ doc.status }}<br/>
    <b>Customer:</b> {{ doc.customer }} &nbsp;|&nbsp; <b>Project:</b> {{ doc.project or '—' }}
  </div>
  <div class="ic-box">
    <h3>1. List of Documents</h3>
    <table class="ic-table">
      <thead><tr><th>#</th><th>Document</th><th>Category</th><th>Mandatory</th><th>Status</th></tr></thead>
      <tbody>
      {% for row in doc.items %}
        <tr>
          <td>{{ row.idx }}</td>
          <td>{{ row.document_name }}</td>
          <td>{{ row.category or '' }}</td>
          <td>{{ 'Yes' if row.is_mandatory else 'No' }}</td>
          <td>{{ row.status }}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  <div class="ic-box">
    <h3>2. Data Collection Sheet</h3>
    <table class="ic-table">
      <tbody>
        <tr><td><b>Company Legal Name</b></td><td>{{ doc.company_legal_name or '' }}</td></tr>
        <tr><td><b>GSTIN</b></td><td>{{ doc.gstin or '' }}</td></tr>
        {% if doc.include_company_address is none or doc.include_company_address %}
        <tr><td><b>Company Address</b></td><td>{{ doc.company_address or '' }}</td></tr>
        {% endif %}
        <tr><td><b>Contact Person</b></td><td>{{ doc.data_contact_person or '' }}</td></tr>
        <tr><td><b>Phone</b></td><td>{{ doc.data_contact_phone or '' }}</td></tr>
        <tr><td><b>Email</b></td><td>{{ doc.data_contact_email or '' }}</td></tr>
        {% if (doc.include_product_name is none or doc.include_product_name)
              or (doc.include_product_model is none or doc.include_product_model)
              or (doc.include_product_brand is none or doc.include_product_brand) %}
        <tr><td><b>Product</b></td><td>
          {%- if doc.include_product_name is none or doc.include_product_name -%}{{ doc.product_name or '' }}{%- endif -%}
          {%- if doc.include_product_model is none or doc.include_product_model -%}{% if doc.include_product_name is none or doc.include_product_name %} / {% endif %}{{ doc.product_model or '' }}{%- endif -%}
          {%- if doc.include_product_brand is none or doc.include_product_brand -%}{% if (doc.include_product_name is none or doc.include_product_name) or (doc.include_product_model is none or doc.include_product_model) %} / {% endif %}{{ doc.product_brand or '' }}{%- endif -%}
        </td></tr>
        {% endif %}
        {% if doc.include_data_collection_remarks is none or doc.include_data_collection_remarks %}
        <tr><td><b>Remarks</b></td><td>{{ doc.data_collection_remarks or '' }}</td></tr>
        {% endif %}
      </tbody>
    </table>
    {% if (doc.include_data_fields is none or doc.include_data_fields) and doc.data_fields %}
    <table class="ic-table" style="margin-top:10px;">
      <thead><tr><th>#</th><th>Field</th><th>Value</th><th>Mandatory</th></tr></thead>
      <tbody>
      {% for row in doc.data_fields %}
        <tr>
          <td>{{ row.idx }}</td>
          <td>{{ row.field_label }}</td>
          <td>{{ row.field_value or '' }}</td>
          <td>{{ 'Yes' if row.is_mandatory else 'No' }}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
    {% endif %}
  </div>
  {% if doc.include_remarks is none or doc.include_remarks %}
  {% if doc.remarks %}
  <div class="ic-box">
    <h3>Notes</h3>
    <div>{{ doc.remarks }}</div>
  </div>
  {% endif %}
  {% endif %}
  <div class="ic-footer-bar">instacertify · documents collection sheet</div>
</div>
"""


TRF_HTML = """
{%- set s = frappe.get_cached_doc('IC Settings') -%}
{%- set legal = s.legal_name or 'Instacertify Labs Private Limited' -%}
{%- set logo = s.header_image or s.logo or '/assets/instacertify/images/instacertify_letterhead.png' -%}
{%- set qr_src = doc.sample_qr_code or '' -%}
{%- if not qr_src and doc.sample_tracking_number -%}
  {%- set qr_src = get_qr_code_data_uri((doc.sample_tracking_number or '') + '\n' + frappe.utils.get_url() + '/ic-verify/sample/' + (doc.sample_tracking_number or ''), 6, 1) -%}
{%- endif -%}
<style>
""" + IC_PRINT_TYPOGRAPHY_CSS + """
  @page { size: A4; margin: 12mm; }
  .print-format { padding: 0 !important; margin: 0 !important; }
  .ic-sheet { font-family: Arial, Helvetica, sans-serif; color:#1a1a1a; font-size:11px; }
  .ic-lh { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; padding-bottom:8px; border-bottom:1.5px solid #EC691F; margin-bottom:12px; }
  .ic-lh-logo img { max-height:58px; max-width:320px; }
  .ic-title { color:#065175; font-size:16px; font-weight:700; margin:8px 0 4px; }
  .ic-sub { color:#555; margin-bottom:12px; }
  .ic-box { border:1.5px solid #8eafc0; border-radius:8px; padding:10px 12px; margin-bottom:12px; }
  .ic-box h3 { margin:0 0 8px; color:#065175; font-size:13px; border-bottom:1px solid #ecf3f7; padding-bottom:4px; }
  table.ic-table { width:100%; border-collapse:collapse; margin-top:6px; }
  table.ic-table td, table.ic-table th { border:1px solid #8eafc0; padding:7px 8px; vertical-align:top; }
  table.ic-table td:first-child { width:34%; color:#065175; font-weight:600; background:#f5fafc; }
  .ic-meta { margin-bottom:10px; }
  .ic-qr-row { display:flex; gap:16px; align-items:center; }
  .ic-qr-row img { width:28mm; height:28mm; border:1px solid #cfd8dc; }
  .ic-footer-bar { background:linear-gradient(90deg,#d85a16 0%,#EC691F 50%,#d85a16 100%); color:#fff; text-align:center; padding:5px 12px; margin-top:20px; font-size:10px; letter-spacing:0.14em; }
</style>
<div class="ic-sheet">
  <div class="ic-lh">
    <div class="ic-lh-logo"><img src="{{ logo }}" alt="Instacertify"/></div>
    <div style="text-align:right;font-size:10px;line-height:1.4;">{{ legal }}</div>
  </div>
  <div class="ic-title">Test Request Form (TRF)</div>
  <div class="ic-sub">Filled sheet for lab / records · match sample QR on intake</div>
  <div class="ic-meta">
    <b>TRF:</b> {{ doc.name }}
    {% if doc.testing_request %}
      &nbsp;|&nbsp; <b>Testing Request:</b>
      <a href="{{ frappe.utils.get_url('/app/ic-testing-request/' + doc.testing_request) }}">{{ doc.testing_request }}</a>
    {% endif %}
    {% if doc.share_url %}
      &nbsp;|&nbsp; <b>Form link:</b> <a href="{{ doc.share_url }}">{{ doc.share_url }}</a>
    {% endif %}
    {% if doc.project %}
      <br/><b>Project:</b> {{ doc.project }}
    {% endif %}
  </div>
  <div class="ic-box">
    <h3>Sample QR (same as product sample)</h3>
    <div class="ic-qr-row">
      {% if qr_src %}<img src="{{ qr_src }}" alt="Sample QR"/>{% endif %}
      <div>
        <div><b>Tracking #:</b> {{ doc.sample_tracking_number or '—' }}</div>
        <div><b>Sample:</b> {{ doc.sample_tracking or '—' }}</div>
        <div style="margin-top:4px;color:#555;">QR matches the sample sticker to avoid confusion.</div>
      </div>
    </div>
  </div>
  <div class="ic-box">
    <h3>Sample &amp; Brand</h3>
    <table class="ic-table">
      <tr><td>Sample Name</td><td>{{ doc.sample_name or '' }}</td></tr>
      <tr><td>Sample Quantity</td><td>{{ doc.sample_quantity or '' }}</td></tr>
      <tr><td>Brand Name</td><td>{{ doc.brand_name or '' }}</td></tr>
      <tr><td>Model No</td><td>{{ doc.model_no or '' }}</td></tr>
      <tr><td>Brand Logo</td><td>{% if doc.brand_logo %}<img src="{{ doc.brand_logo }}" style="max-height:28px;"/>{% else %}—{% endif %}</td></tr>
    </table>
  </div>
  <div class="ic-box">
    <h3>Product / Testing</h3>
    <table class="ic-table">
      <tr><td>Product Name</td><td>{{ doc.product_name or '' }}</td></tr>
      <tr><td>Rated Input / Specification</td><td>{{ doc.rated_input or '' }}</td></tr>
      <tr><td>Testing Requested</td><td>{{ doc.testing_requested or '' }}</td></tr>
      <tr><td>Standard Applicable</td><td>{{ doc.applicable_standard or '' }}</td></tr>
      <tr><td>Description</td><td>{{ doc.description or '' }}</td></tr>
      <tr><td>Other Remarks</td><td>{{ doc.other_remarks or '' }}</td></tr>
    </table>
  </div>
  <div class="ic-footer-bar">instacertify · test request form (TRF)</div>
</div>
"""


SAMPLE_DISPATCH_COLLECTION_HTML = """
{%- set s = frappe.get_cached_doc('IC Settings') -%}
{%- set legal = s.legal_name or 'Instacertify Labs Private Limited' -%}
{%- set logo = s.header_image or s.logo or '/assets/instacertify/images/instacertify_letterhead.png' -%}
<style>
""" + IC_PRINT_TYPOGRAPHY_CSS + """
  @page { size: A4; margin: 12mm; }
  .print-format { padding: 0 !important; margin: 0 !important; }
  .ic-sheet { font-family: Arial, Helvetica, sans-serif; color:#1a1a1a; font-size:11px; }
  .ic-lh { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; padding-bottom:8px; border-bottom:1.5px solid #EC691F; margin-bottom:12px; }
  .ic-lh-logo img { max-height:58px; max-width:320px; }
  .ic-title { color:#065175; font-size:16px; font-weight:700; margin:8px 0 4px; }
  .ic-sub { color:#555; margin-bottom:12px; }
  .ic-box { border:1px solid #d9e6ee; border-radius:8px; padding:10px 12px; margin-bottom:12px; }
  .ic-box h3 { margin:0 0 8px; color:#065175; font-size:13px; border-bottom:1px solid #ecf3f7; padding-bottom:4px; }
  table.ic-table { width:100%; border-collapse:collapse; margin-top:6px; }
  table.ic-table td { border-bottom:1px solid #e5eef3; padding:6px 8px; vertical-align:top; }
  table.ic-table td:first-child { width:32%; color:#065175; font-weight:600; }
  .ic-meta { margin-bottom:10px; }
  .ic-footer-bar { background:linear-gradient(90deg,#d85a16 0%,#EC691F 50%,#d85a16 100%); color:#fff; text-align:center; padding:5px 12px; margin-top:20px; font-size:10px; letter-spacing:0.14em; }
</style>
<div class="ic-sheet">
  <div class="ic-lh">
    <div class="ic-lh-logo"><img src="{{ logo }}" alt="Instacertify"/></div>
    <div style="text-align:right;font-size:10px;line-height:1.4;">{{ legal }}</div>
  </div>
  <div class="ic-title">Sample Dispatch Data Collection Sheet</div>
  <div class="ic-sub">Customer courier / AWB / POD collection</div>
  <div class="ic-meta">
    <b>Sheet:</b> {{ doc.name }} &nbsp;|&nbsp; <b>Title:</b> {{ doc.title }} &nbsp;|&nbsp; <b>Status:</b> {{ doc.status }}<br/>
    <b>Customer:</b> {{ doc.customer }} &nbsp;|&nbsp; <b>Project:</b> {{ doc.project or '—' }}
  </div>
  <div class="ic-box">
    <h3>Contact</h3>
    <table class="ic-table">
      <tr><td>Contact Person</td><td>{{ doc.contact_person or '' }}</td></tr>
      <tr><td>Phone</td><td>{{ doc.contact_phone or '' }}</td></tr>
      <tr><td>Email</td><td>{{ doc.contact_email or '' }}</td></tr>
      <tr><td>Dispatch From Address</td><td>{{ doc.dispatch_from_address or '' }}</td></tr>
    </table>
  </div>
  <div class="ic-box">
    <h3>Sample Details</h3>
    <table class="ic-table">
      <tr><td>Description</td><td>{{ doc.sample_description or '' }}</td></tr>
      <tr><td>Quantity</td><td>{{ doc.sample_quantity or '' }}</td></tr>
      <tr><td>Condition</td><td>{{ doc.sample_condition or '' }}</td></tr>
      <tr><td>Packaging</td><td>{{ doc.packaging_details or '' }}</td></tr>
    </table>
  </div>
  <div class="ic-box">
    <h3>Courier / Dispatch</h3>
    <table class="ic-table">
      <tr><td>Courier</td><td>{{ doc.courier_name or '' }}</td></tr>
      <tr><td>Tracking / AWB</td><td>{{ doc.tracking_number or '' }}</td></tr>
      <tr><td>Dispatch Date</td><td>{{ doc.dispatch_date or '' }}</td></tr>
      <tr><td>Expected Delivery</td><td>{{ doc.expected_delivery or '' }}</td></tr>
      <tr><td>POD Attached</td><td>{{ 'Yes' if doc.pod_attachment else 'No' }}</td></tr>
      <tr><td>Customer Remarks</td><td>{{ doc.customer_remarks or '' }}</td></tr>
    </table>
  </div>
  <div class="ic-footer-bar">instacertify · sample dispatch data collection</div>
</div>
"""


def _ensure_aptos_fonts():
	"""Install Aptos Display / Aptos into the system font cache for Chrome PDF."""
	import os
	import shutil
	from pathlib import Path

	try:
		app_fonts = Path(frappe.get_app_path("instacertify")) / "public" / "fonts" / "aptos"
		if not app_fonts.is_dir():
			return
		dest = Path("/usr/local/share/fonts/aptos")
		try:
			dest.mkdir(parents=True, exist_ok=True)
		except PermissionError:
			dest = Path.home() / ".local" / "share" / "fonts" / "aptos"
			dest.mkdir(parents=True, exist_ok=True)
		copied = False
		for ttf in app_fonts.glob("*.ttf"):
			target = dest / ttf.name
			if not target.exists() or target.stat().st_size != ttf.stat().st_size:
				try:
					shutil.copy2(ttf, target)
					copied = True
				except Exception:
					pass
		if copied:
			os.system("fc-cache -f >/dev/null 2>&1")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Aptos font install")


def _ensure_instacertify_letter_head():
	"""Create/update Letter Head so Print / PDF Options shows Instacertify branding.

	Instacertify Quotation / Invoice Jinja formats embed the letterhead in the
	print body (logo + company details from IC Settings). The Letter Head record
	is still kept as default for other DocTypes / print dialog selection.
	"""
	name = "Instacertify"
	try:
		s = frappe.get_cached_doc("IC Settings")
	except Exception:
		s = None
	logo = (
		(getattr(s, "header_image", None) if s else None)
		or (getattr(s, "logo", None) if s else None)
		or "/assets/instacertify/images/instacertify_letterhead.png"
	)
	if logo and not str(logo).startswith(("http://", "https://", "data:")):
		logo = frappe.utils.get_url(logo)
	legal = (getattr(s, "legal_name", None) if s else None) or "Instacertify Labs Private Limited"
	address = (getattr(s, "address_line", None) if s else None) or (
		"PK 01 SECTOR 63A NOIDA, GAUTAM BUDDHA NAGAR, UTTAR PRADESH-201301, INDIA"
	)
	phone = (getattr(s, "phone", None) if s else None) or "+91 9999118039"
	email = (getattr(s, "email", None) if s else None) or "contact@instacertify.com"
	website = (getattr(s, "website", None) if s else None) or "www.instacertify.com"
	cin = (getattr(s, "cin", None) if s else None) or "U74999UP2022PTC170291"
	gstin = (getattr(s, "gstin", None) if s else None) or "09AAGCI8396C1Z7"
	addr_html = (address or "").replace("\n", "<br>")
	content = f"""
<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;padding:0 0 8px;border-bottom:1.5px solid #EC691F;width:100%;box-sizing:border-box;background:#fff;">
  <div><img src="{logo}" alt="Instacertify" style="max-height:58px;max-width:320px;"/></div>
  <div style="text-align:right;color:#111;font-size:10px;line-height:1.4;font-family:Aptos,Segoe UI,sans-serif;">
    <div style="font-weight:600;font-size:12.5px;text-transform:none;margin-bottom:2px;">{legal}</div>
    <div>{addr_html}</div>
    <div>Phone: {phone}</div>
    <div>Email: {email}</div>
    <div>{website}</div>
    <div><b>CIN:</b> {cin}</div>
    <div><b>GSTIN:</b> {gstin}</div>
  </div>
</div>
"""
	try:
		if frappe.db.exists("Letter Head", name):
			doc = frappe.get_doc("Letter Head", name)
			doc.source = "HTML"
			doc.content = content
			doc.disabled = 0
			doc.is_default = 1
			doc.save(ignore_permissions=True)
		else:
			frappe.get_doc(
				{
					"doctype": "Letter Head",
					"letter_head_name": name,
					"source": "HTML",
					"content": content,
					"disabled": 0,
					"is_default": 1,
				}
			).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Instacertify Letter Head")


def ensure_print_formats():
	_ensure_aptos_fonts()
	_ensure_instacertify_letter_head()
	formats = [
		("Instacertify Quotation", "Quotation", QUOTATION_HTML),
		("Instacertify Consulting Quotation", "Quotation", CONSULTING_QUOTATION_HTML),
		("Instacertify Testing Quotation", "Quotation", TESTING_QUOTATION_HTML),
		("Instacertify Sales Invoice", "Sales Invoice", INVOICE_HTML),
		("Instacertify Sample Label", "IC Sample Tracking", SAMPLE_HTML),
		("Instacertify Sample Sticker 50x25mm", "IC Sample Tracking", SAMPLE_STICKER_50X25_HTML),
		("Instacertify Sample Sticker 8mm", "IC Sample Tracking", SAMPLE_STICKER_50X25_HTML),
		("Instacertify Testing Request", "IC Testing Request", TESTING_HTML),
		("Instacertify Joining Letter", "IC Joining Letter", JOINING_HTML),
		("Instacertify Documents Collection Sheet", "IC Document Request", DOCUMENTS_COLLECTION_HTML),
		("Instacertify Sample Dispatch Collection", "IC Sample Dispatch Collection", SAMPLE_DISPATCH_COLLECTION_HTML),
		("Instacertify Test Request Form", "IC Test Request Form", TRF_HTML),
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
	_ensure_default_print_format("IC Document Request", "Instacertify Documents Collection Sheet")
	_ensure_default_print_format("IC Sample Dispatch Collection", "Instacertify Sample Dispatch Collection")

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