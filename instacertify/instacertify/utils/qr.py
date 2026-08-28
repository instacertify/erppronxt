# Copyright (c) Instacertify
"""QR code utilities."""

from __future__ import annotations

import base64
import io

import frappe


def get_qr_code_data_uri(data: str, box_size: int = 4, border: int = 2) -> str:
	"""Return a data URI PNG for the given payload."""
	try:
		import qrcode
	except ImportError:
		return ""

	qr = qrcode.QRCode(version=1, box_size=box_size, border=border)
	qr.add_data(data)
	qr.make(fit=True)
	img = qr.make_image(fill_color="black", back_color="white")
	buf = io.BytesIO()
	img.save(buf, format="PNG")
	b64 = base64.b64encode(buf.getvalue()).decode()
	return f"data:image/png;base64,{b64}"


def generate_and_attach_qr(doctype: str, name: str, fieldname: str, payload: str) -> str | None:
	"""Generate QR image and attach to document field. Returns file URL."""
	try:
		import qrcode
	except ImportError:
		frappe.msgprint("qrcode package not installed")
		return None

	qr = qrcode.QRCode(version=1, box_size=6, border=2)
	qr.add_data(payload)
	qr.make(fit=True)
	img = qr.make_image(fill_color="black", back_color="white")
	buf = io.BytesIO()
	img.save(buf, format="PNG")
	filename = f"{doctype.replace(' ', '-')}-{name}-qr.png".replace("/", "-")

	file_doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": filename,
			"content": buf.getvalue(),
			"is_private": 0,
			"attached_to_doctype": doctype,
			"attached_to_name": name,
			"attached_to_field": fieldname,
		}
	)
	file_doc.save(ignore_permissions=True)
	frappe.db.set_value(doctype, name, fieldname, file_doc.file_url, update_modified=False)
	return file_doc.file_url


def verification_url(doctype: str, name: str) -> str:
	base = frappe.utils.get_url()
	return f"{base}/ic-verify/{doctype}/{name}"
