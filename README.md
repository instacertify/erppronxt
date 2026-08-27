# Instacertify ERP (ERPNext 16.33)

Instacertify certification, compliance, consulting and testing operations — implemented **only** on ERPNext + Frappe.

## Stack

| Component | Version |
|-----------|---------|
| ERPNext | **16.33.0** |
| Frappe | version-16 (compatible) |
| Custom app | `instacertify` |
| Primary currency | INR (multi-currency via native ERPNext) |

No separate frontend, CRM, HRMS app, or alternate ERP platform is used. HR features reuse ERPNext native **Employee**, **Holiday List**, **Asset**, plus Instacertify DocTypes for joining letters / employee documents.

## Repository layout

```
instacertify/          # Custom Frappe app (install on ERPNext site)
scripts/bootstrap_erpnext.sh
README.md
```

## Quick start

```bash
# Prerequisites: MariaDB, Redis, Node.js 24+, Python 3.14 (via uv), yarn
chmod +x scripts/bootstrap_erpnext.sh
./scripts/bootstrap_erpnext.sh

cd ~/frappe-bench
bench start
# Desk: http://127.0.0.1:8000  (Administrator / admin)

# Optional realistic demo data
bench --site instacertify.localhost execute instacertify.setup.demo_data.execute
```

## What the custom app adds

**Extends native ERPNext**

- Lead, Customer, Quotation, Project, Sales Invoice, Asset custom fields
- Quotation workflow (Draft → Review → Share → Accept / Changes Requested)
- Multi-currency quotations & invoices (INR / USD)
- Workspace **Instacertify Home** with greeting, summary cards, project tiles, charts
- Print formats (Quotation, Invoice, Testing Request, Sample Label, Joining Letter) with QR
- Roles: IC Admin, IC Senior Operations, IC Sales Person, IC Operations Manager

**Custom DocTypes (only where native ERPNext is insufficient)**

- Consultant Referral
- IC Quotation Template (+ cost / test child tables)
- IC Laboratory (+ test scopes with Admin-only purchase price / margin)
- IC Testing Request, IC Sample Tracking
- IC Document Checklist Template / IC Document Request
- IC Project Record, IC Project Update
- IC Joining Letter, IC Employee Document
- IC Settings

**Customer-facing secure links (Frappe www)**

- `/ic-quotation/<token>` — view / accept / request changes
- `/ic-documents/<token>` — upload requested documents
- `/ic-report/<token>` — view shared test report
- `/ic-verify/<doctype>/<name>` — QR verification

## Branding

- Primary `#065175`
- Accent `#EC6820`

## Demo users (after demo data)

| User | Password | Roles |
|------|----------|-------|
| Administrator | admin | System Manager |
| sales@instacertify.com | Instacertify@123 | IC Sales Person |
| ops@instacertify.com | Instacertify@123 | IC Operations Manager |
| ops.head@instacertify.com | Instacertify@123 | IC Senior Operations |
| admin.ops@instacertify.com | Instacertify@123 | IC Admin |

## Upgrade-friendly principles

- No ERPNext core edits
- Customizations live in `instacertify`
- Prefer Custom Fields, Workflows, Print Formats, Reports, Workspaces
- Custom DocTypes only for Instacertify-specific processes
