# Copyright (c) Instacertify
"""QC: all Instacertify print formats — aligned, printable, shareable."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.utils.pdf import get_pdf

from instacertify.utils.pdf import (
	even_print_margins,
	get_quotation_pdf_bytes,
	inline_local_assets,
	make_pdf,
	quotation_print_format,
)


PRINT_MATRIX = [
	("Instacertify Quotation", "Quotation", "Consulting"),
	("Instacertify Consulting Quotation", "Quotation", "Consulting"),
	("Instacertify Testing Quotation", "Quotation", "Testing"),
	("Instacertify Sales Invoice", "Sales Invoice", None),
	("Instacertify Sample Label", "IC Sample Tracking", None),
	("Instacertify Testing Request", "IC Testing Request", None),
	("Instacertify Joining Letter", "IC Joining Letter", None),
]


def _pick_doc(doctype: str, quotation_type: str | None = None) -> str | None:
	if doctype == "Quotation" and quotation_type:
		name = frappe.db.get_value(
			"Quotation",
			{"ic_quotation_type": quotation_type},
			"name",
			order_by="modified desc",
		)
		if name:
			return name
	return frappe.db.get_value(doctype, {}, "name", order_by="modified desc")


def _pdf_info(pdf: bytes) -> dict:
	info = {
		"bytes": len(pdf or b""),
		"is_pdf": bool(pdf and pdf[:4] == b"%PDF"),
		"pages": None,
		"page_size": None,
	}
	if not info["is_pdf"]:
		return info
	try:
		from pypdf import PdfReader
		from io import BytesIO

		reader = PdfReader(BytesIO(pdf))
		info["pages"] = len(reader.pages)
		if reader.pages:
			box = reader.pages[0].mediabox
			# A4 points ≈ 595 x 842
			w, h = float(box.width), float(box.height)
			info["page_size"] = f"{w:.0f}x{h:.0f}pt"
			info["is_a4"] = 580 <= min(w, h) <= 610 and 820 <= max(w, h) <= 860
	except Exception as e:
		info["pdf_meta_error"] = str(e)
	return info


def _render_pdf(doctype: str, name: str, print_format: str) -> bytes:
	if doctype == "Quotation":
		return get_quotation_pdf_bytes(name, print_format=print_format, no_letterhead=1)

	html = frappe.get_print(doctype, name, print_format=print_format, no_letterhead=1)
	try:
		return make_pdf(html)
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"make_pdf {print_format}")
		# fallback core get_pdf with even margins + inlined assets
		return get_pdf(inline_local_assets(html), options=even_print_margins())


@frappe.whitelist()
def run_print_format_qc(save_samples: int = 1) -> dict:
	"""
	Ensure all Instacertify print formats exist, have even A4 margins,
	generate printable PDFs, and confirm shareability hooks for quotations.
	"""
	from instacertify.setup.print_formats import ensure_print_formats

	ensure_print_formats()
	frappe.clear_cache()

	report = {
		"ok": [],
		"warn": [],
		"fail": [],
		"formats": [],
		"share": {},
	}

	for fmt_name, doctype, qtype in PRINT_MATRIX:
		row = {"print_format": fmt_name, "doctype": doctype}
		if not frappe.db.exists("Print Format", fmt_name):
			report["fail"].append(f"Missing Print Format {fmt_name}")
			row["status"] = "missing"
			report["formats"].append(row)
			continue

		html = frappe.db.get_value("Print Format", fmt_name, "html") or ""
		generator = frappe.db.get_value("Print Format", fmt_name, "pdf_generator")
		row["pdf_generator"] = generator
		row["has_page_rule"] = "@page" in html and "12mm" in html
		row["has_zero_pad"] = "print-format" in html and "padding:0" in html.replace(" ", "")
		if not row["has_page_rule"]:
			report["fail"].append(f"{fmt_name}: missing @page 12mm")
		else:
			report["ok"].append(f"{fmt_name}: @page 12mm")
		if generator and str(generator).lower() != "chrome":
			report["warn"].append(f"{fmt_name}: pdf_generator={generator} (prefer chrome)")

		docname = _pick_doc(doctype, qtype)
		row["docname"] = docname
		if not docname:
			report["warn"].append(f"{fmt_name}: no {doctype} sample doc")
			row["status"] = "no_doc"
			report["formats"].append(row)
			continue

		try:
			pdf = _render_pdf(doctype, docname, fmt_name)
			meta = _pdf_info(pdf)
			row.update(meta)
			if not meta["is_pdf"]:
				report["fail"].append(f"{fmt_name}: invalid PDF for {docname}")
				row["status"] = "bad_pdf"
			else:
				report["ok"].append(
					f"{fmt_name}: PDF {docname} bytes={meta['bytes']} pages={meta['pages']} size={meta.get('page_size')}"
				)
				row["status"] = "ok"
				if meta.get("is_a4") is False:
					report["warn"].append(f"{fmt_name}: page size not A4-like ({meta.get('page_size')})")
				if int(save_samples or 0):
					out = Path("/opt/cursor/artifacts") / f"print_{fmt_name.replace(' ', '_').lower()}.pdf"
					out.parent.mkdir(parents=True, exist_ok=True)
					out.write_bytes(pdf)
					row["sample_path"] = str(out)
		except Exception as e:
			report["fail"].append(f"{fmt_name}: {e}")
			row["status"] = "error"
			row["error"] = str(e)

		report["formats"].append(row)

	# Shareability — quotation customer portal PDF
	try:
		qtn = frappe.db.get_value("Quotation", {}, "name", order_by="modified desc")
		if qtn:
			from instacertify.quotation.events import share_with_customer, download_quotation_pdf

			share = share_with_customer(qtn)
			report["share"] = {
				"quotation": qtn,
				"url": share.get("url"),
				"token": bool(share.get("token")),
				"pdf_endpoint": f"/api/method/instacertify.quotation.events.download_quotation_pdf?token={share.get('token')}",
			}
			# Generate via token path (as Guest would)
			token = share.get("token")
			name = frappe.db.get_value("Quotation", {"ic_share_token": token}, "name")
			pdf = get_quotation_pdf_bytes(name)
			meta = _pdf_info(pdf)
			if meta["is_pdf"]:
				report["ok"].append(f"Shareable portal PDF ok bytes={meta['bytes']}")
			else:
				report["fail"].append("Shareable portal PDF invalid")
	except Exception as e:
		report["fail"].append(f"Shareability: {e}")

	# Defaults
	for dt, expected in (
		("Quotation", "Instacertify Quotation"),
		("Sales Invoice", "Instacertify Sales Invoice"),
		("IC Sample Tracking", "Instacertify Sample Label"),
		("IC Testing Request", "Instacertify Testing Request"),
		("IC Joining Letter", "Instacertify Joining Letter"),
	):
		ps = frappe.db.get_value(
			"Property Setter",
			{"doc_type": dt, "property": "default_print_format"},
			"value",
		)
		if ps == expected:
			report["ok"].append(f"Default print format {dt}={expected}")
		else:
			report["warn"].append(f"Default print format {dt}={ps!r} expected {expected}")

	report["summary"] = {
		"ok": len(report["ok"]),
		"warn": len(report["warn"]),
		"fail": len(report["fail"]),
		"passed": len(report["fail"]) == 0,
	}
	return report
