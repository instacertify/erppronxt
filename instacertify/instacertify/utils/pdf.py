# Copyright (c) Instacertify
"""Reliable PDF generation for Instacertify print formats.

Desk PDF fails on this environment because wkhtmltopdf resolves
`instacertify.localhost` (HostNotFoundError). Prefer Chrome; fall back to
wkhtmltopdf after inlining local /assets and /files as data URIs.
"""

from __future__ import annotations

import base64
import mimetypes
import re
from pathlib import Path

import frappe
from frappe import _


def inline_local_assets(html: str) -> str:
	"""Embed local site assets so PDF engines need no network DNS."""
	if not html:
		return html or ""

	assets_root = Path(frappe.utils.get_bench_path()) / "sites" / "assets"
	public_files = Path(frappe.get_site_path("public", "files"))
	private_files = Path(frappe.get_site_path("private", "files"))

	def file_for(url: str) -> Path | None:
		url = (url or "").split("?", 1)[0]
		if not url or url.startswith("data:"):
			return None
		# scrub_urls may have expanded to http://host/...
		for marker, root in (
			("/assets/", assets_root),
			("/private/files/", private_files),
			("/files/", public_files),
		):
			if marker in url:
				rel = url.split(marker, 1)[1]
				path = root / rel
				if path.exists() and path.is_file():
					return path
		return None

	def to_data_uri(path: Path) -> str:
		mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
		b64 = base64.b64encode(path.read_bytes()).decode()
		return f"data:{mime};base64,{b64}"

	def repl_src(match: re.Match) -> str:
		url = match.group(1)
		path = file_for(url)
		if path:
			return f'src="{to_data_uri(path)}"'
		# Drop remote JS bundles that only cause HostNotFound during PDF
		if url.endswith(".js") or "/print.bundle" in url:
			return 'src=""'
		return match.group(0)

	def repl_css_url(match: re.Match) -> str:
		prefix, url, suffix = match.group(1), match.group(2), match.group(3)
		path = file_for(url)
		if path:
			return f"{prefix}{to_data_uri(path)}{suffix}"
		return match.group(0)

	html = re.sub(r"<script\b[^>]*>[\s\S]*?</script>", "", html, flags=re.I)
	html = re.sub(r'src=["\']([^"\']+)["\']', repl_src, html)
	html = re.sub(r"""(url\(["']?)([^"')]+)(["']?\))""", repl_css_url, html)
	return html


def quotation_print_format(doc) -> str | None:
	"""Pick the Instacertify print format for a quotation."""
	qtype = (getattr(doc, "ic_quotation_type", None) or "").strip()
	if qtype == "Testing" and frappe.db.exists("Print Format", "Instacertify Testing Quotation"):
		return "Instacertify Testing Quotation"
	if qtype in ("Consulting", "Renewal", "Service", "Other") and frappe.db.exists(
		"Print Format", "Instacertify Consulting Quotation"
	):
		return "Instacertify Consulting Quotation"
	if frappe.db.exists("Print Format", "Instacertify Quotation"):
		return "Instacertify Quotation"
	return None


def even_print_margins() -> dict:
	"""Even A4 margins so printed PDFs align cleanly on all sides."""
	return {
		"page-size": "A4",
		"margin-top": "12mm",
		"margin-right": "12mm",
		"margin-bottom": "12mm",
		"margin-left": "12mm",
	}


def make_pdf(html: str, options: dict | None = None) -> bytes:
	"""Generate PDF bytes: try Chrome on the HTML, then inlined wkhtmltopdf."""
	options = dict(options or {})
	options.update(even_print_margins())
	options.setdefault("disable-javascript", "")
	options.setdefault("load-error-handling", "ignore")
	options.setdefault("load-media-error-handling", "ignore")

	safe_html = inline_local_assets(html)
	# Ensure CSS page box matches engine margins (even 12mm).
	if "@page" not in safe_html:
		safe_html = (
			"<style>@page{size:A4;margin:12mm}.print-format{padding:0!important;margin:0!important}</style>"
			+ safe_html
		)

	try:
		from frappe.utils.pdf import get_chrome_pdf

		frappe.local.form_dict.pdf_generator = "chrome"
		# Pass a real print format name so Browser can resolve print_designer flag
		fmt_name = (
			"Instacertify Quotation"
			if frappe.db.exists("Print Format", "Instacertify Quotation")
			else None
		)
		pdf = get_chrome_pdf(
			print_format=fmt_name,
			html=safe_html,
			options=options,
			output=None,
			pdf_generator="chrome",
		)
		if pdf:
			return pdf
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Instacertify Chrome PDF")

	from frappe.utils.pdf import get_pdf

	return get_pdf(safe_html, options=options)


def get_quotation_pdf_bytes(name: str, print_format: str | None = None, no_letterhead: int = 1) -> bytes:
	"""Build quotation PDF with resilient generators and even print margins."""
	doc = frappe.get_doc("Quotation", name)
	fmt = print_format or quotation_print_format(doc)

	# Prefer HTML → make_pdf so even margins are applied consistently.
	try:
		html = frappe.get_print("Quotation", name, print_format=fmt, no_letterhead=no_letterhead)
		pdf = make_pdf(html)
		if pdf:
			return pdf
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Quotation make_pdf")

	# Last resort: Frappe chrome get_print pipeline
	try:
		pdf = frappe.get_print(
			"Quotation",
			name,
			print_format=fmt,
			as_pdf=True,
			no_letterhead=no_letterhead,
			pdf_generator="chrome",
		)
		if pdf:
			return pdf
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Quotation Chrome get_print")
		raise


@frappe.whitelist()
def download_quotation_pdf(name: str, print_format: str | None = None):
	"""Desk-safe Quotation PDF download that avoids raw server errors."""
	if not name:
		frappe.throw(_("Quotation name is required"))
	doc = frappe.get_doc("Quotation", name)
	doc.check_permission("read")

	try:
		pdf = get_quotation_pdf_bytes(name, print_format=print_format or None, no_letterhead=1)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Quotation PDF download")
		frappe.throw(
			_("PDF could not be generated right now. Please try again in a moment."),
			title=_("PDF generation failed"),
		)

	frappe.local.response.filename = f"{name.replace(' ', '-')}.pdf"
	frappe.local.response.filecontent = pdf
	frappe.local.response.type = "pdf"


@frappe.whitelist()
@frappe.concurrent_limit()
def download_pdf(
	doctype: str,
	name: str,
	format: str | None = None,
	doc=None,
	no_letterhead: bool | int = 0,
	language: str | None = None,
	letterhead: str | None = None,
	pdf_generator: str | None = None,
):
	"""Override Frappe download_pdf for Instacertify Quotation reliability.

	Guests must use token-gated download_quotation_pdf — this endpoint requires login.
	"""
	if frappe.session.user == "Guest":
		frappe.throw(_("Login required to download this PDF"), frappe.PermissionError)

	# Non-quotation: keep core behaviour
	if doctype != "Quotation":
		from frappe.utils.print_format import download_pdf as core_download_pdf

		return core_download_pdf(
			doctype=doctype,
			name=name,
			format=format,
			doc=doc,
			no_letterhead=no_letterhead,
			language=language,
			letterhead=letterhead,
			pdf_generator=pdf_generator or "chrome",
		)

	from frappe.translate import print_language
	from frappe.www.printview import validate_print_permission

	doc = doc or frappe.get_doc(doctype, name)
	validate_print_permission(doc)

	fmt = format or quotation_print_format(doc)
	generator = pdf_generator or "chrome"

	try:
		with print_language(language):
			try:
				pdf_file = frappe.get_print(
					doctype,
					name,
					fmt,
					doc=doc,
					as_pdf=True,
					letterhead=letterhead,
					no_letterhead=no_letterhead if no_letterhead is not None else 1,
					pdf_generator=generator,
				)
			except Exception:
				# Hard fallback: resilient helper (chrome → inlined wkhtml)
				pdf_file = get_quotation_pdf_bytes(
					name,
					print_format=fmt,
					no_letterhead=1 if no_letterhead is None else int(no_letterhead),
				)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Quotation desk PDF")
		frappe.throw(
			_("PDF could not be generated right now. Please try again in a moment."),
			title=_("PDF generation failed"),
		)

	frappe.local.response.filename = "{name}.pdf".format(name=name.replace(" ", "-").replace("/", "-"))
	frappe.local.response.filecontent = pdf_file
	frappe.local.response.type = "pdf"
