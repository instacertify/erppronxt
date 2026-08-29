# Instacertify

Custom Frappe app for Instacertify on ERPNext 16.33 — certification, compliance, consulting and testing operations.

## Required apps

- `erpnext`
- `india_compliance` (Indian GST / GSTR) — install with:
  `bench get-app https://github.com/resilient-tech/india-compliance --branch version-16`
  `bench --site <site> install-app india_compliance`
- `hrms` (Frappe HR — hiring → FnF) — install with:
  `bench get-app hrms --branch version-16`
  `bench --site <site> install-app hrms`
- `gameplan` (team discussions) — install with:
  `bench get-app gameplan --branch develop`
  `bench --site <site> install-app gameplan`
  Open from Desk icon, Instacertify Home sidebar, Explore tile, or `/g`

## Expenses & HRMS (last in navigation)

Expenses and HRMS are intentionally placed **last** on Instacertify Home and Explore.
Open workspace **HRMS & Expenses** for the full employee lifecycle:

1. Hiring — Job Applicant / Job Offer  
2. Onboarding — Employee / Employee Onboarding / Joining Letter  
3. Attendance & Leave  
4. Payroll — Salary Structure / Payroll Entry / Salary Slip  
5. Expenses — Instacertify expense claims + HRMS Expense Claim  
6. Performance — Appraisal / Goal  
7. Exit & Full and Final — Employee Separation / Full and Final Statement  


## GST & billing currency

- Company GSTIN / address configured for **Instacertify Labs** (Uttar Pradesh).
- India customers default to **INR** with GST templates (CGST+SGST in-state / IGST out-state).
- Customers with country other than India default to **USD** and GST category **Overseas**.
- Users can manually change currency (INR or any other) anytime; set **Currency Manually Set** to keep the choice when country changes.

## GST returns (GSTR-1 / GSTR-3B)

Instacertify Home → **GST & Invoicing** includes:
- Sales Invoice / Payment Entry
- **GSTR-1** (generate / upload / file)
- **GSTR-3B** (generate JSON/Excel/PDF and mark filed)
- GST Return Log, GST Settings, GSTR-3B Details report

Also available under the **GST India** workspace from india_compliance. Portal filing needs an India Compliance API secret in GST Settings.

## POS billing

POS billing is **disabled**. Use standard Sales Invoice only. The Include Payment (POS) option and all POS menu entries are removed on migrate.

## Laboratory Library (Testing pricing)

1. **Instacertify Home → Laboratory Library → Register / Manage Labs** (`IC Laboratory`)
2. Save accreditation details/scope PDFs and add **Scope of Accreditation & Pricing** rows:
   - Test name + standard
   - **Buying Price** (admin)
   - **Suggested Selling Price** (used on quotations)
3. On a **Testing** Quotation → Testing Items:
   - Choose **Laboratory** (Active labs)
   - Pick **Lab Test / Pricing** from the dropdown
   - **Selling Price / Unit** is prefilled from the library and remains editable
4. After Accept → **Start Project** (or **Create Testing Requests**) assigns lab-scoped testing projects.

## CRM Lead Tracker & Capture

**Instacertify Home → CRM Lead Tracker** shows:
- This week vs last week, this month vs last month (bar charts + % change)
- Last 7 / 30 days pie & donut charts by **Lead Source**, **Project Type**, and status

**Lead capture fields**
- **Name of Person / Firm** (mandatory)
- Phone & email optional
- **Country** dropdown with India on top (default India)
- **Company Size**: Micro / Small / Medium / Large
- **Lead Source**: Google Search, Google Ads, IndiaMART, Reference, Consultant (+ more) — edit under **IC Lead Source**
- **Project Type**: BIS, Testing, EPR, LMPC, SABER, GMARK, MSDS Authoring — edit under **IC Project Type**

## Customer Related Data

Open any **Customer** → **Related Data** tab to view that customer’s:
- Quotations shared / accepted
- Projects (stage & progress)
- Sales invoices & payments
- Opportunities, testing requests, document requests, samples, project records, contacts, leads

The **Connections** tab also shows counts and filtered lists (including Instacertify DocTypes).

## Theme

Desk uses a **light cool-teal hue** background (Instacertify brand soft blues), not flat white or dark mode. Cards and forms stay white for readability.
