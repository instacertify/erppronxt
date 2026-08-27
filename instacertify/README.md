# Instacertify

Custom Frappe app for Instacertify on ERPNext 16.33 — certification, compliance, consulting and testing operations.

## Required apps

- `erpnext`
- `india_compliance` (Indian GST / GSTR) — install with:
  `bench get-app https://github.com/resilient-tech/india-compliance --branch version-16`
  `bench --site <site> install-app india_compliance`

## GST & billing currency

- Company GSTIN / address configured for **Instacertify Labs** (Uttar Pradesh).
- India customers default to **INR** with GST templates (CGST+SGST in-state / IGST out-state).
- Customers with country other than India default to **USD** and GST category **Overseas**.
- Users can manually change currency (INR or any other) anytime; set **Currency Manually Set** to keep the choice when country changes.

## POS billing

POS billing is **disabled**. Use standard Sales Invoice only. The Include Payment (POS) option and all POS menu entries are removed on migrate.

## Theme

Desk uses a **light cool-teal hue** background (Instacertify brand soft blues), not flat white or dark mode. Cards and forms stay white for readability.
