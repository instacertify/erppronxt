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

	qr = qrcode.QRCode(
		version=None,
		error_correction=qrcode.constants.ERROR_CORRECT_M,
		box_size=box_size,
		border=border,
	)
	qr.add_data(data)
	qr.make(fit=True)
	img = qr.make_image(fill_color="black", back_color="white")
	buf = io.BytesIO()
	img.save(buf, format="PNG")
	b64 = base64.b64encode(buf.getvalue()).decode()
	return f"data:image/png;base64,{b64}"


def generate_qr_image(payload: str, box_size: int = 6, border: int = 1):
	"""Return a PIL image for the QR payload (tight border for stickers)."""
	import qrcode

	qr = qrcode.QRCode(
		version=None,
		error_correction=qrcode.constants.ERROR_CORRECT_M,
		box_size=box_size,
		border=border,
	)
	qr.add_data(payload)
	qr.make(fit=True)
	return qr.make_image(fill_color="black", back_color="white").convert("RGB")


def generate_and_attach_qr(
	doctype: str,
	name: str,
	fieldname: str,
	payload: str,
	*,
	box_size: int = 6,
	border: int = 2,
) -> str | None:
	"""Generate QR image and attach to document field. Returns file URL."""
	try:
		img = generate_qr_image(payload, box_size=box_size, border=border)
	except ImportError:
		frappe.msgprint("qrcode package not installed")
		return None
	except Exception:
		frappe.log_error(frappe.get_traceback(), "generate_and_attach_qr")
		return None

	buf = io.BytesIO()
	img.save(buf, format="PNG")
	filename = f"{doctype.replace(' ', '-')}-{name}-qr.png".replace("/", "-")

	# Replace previous QR file for this field when regenerating
	existing = frappe.get_all(
		"File",
		filters={
			"attached_to_doctype": doctype,
			"attached_to_name": name,
			"attached_to_field": fieldname,
		},
		pluck="name",
	)
	for fname in existing:
		try:
			frappe.delete_doc("File", fname, ignore_permissions=True, force=True)
		except Exception:
			pass

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


def sample_qr_payload(tracking_number: str, docname: str | None = None) -> str:
	"""Compact QR payload: unique sample tracking number + verify URL.

	Scanners that read plain text get the tracking number; phone cameras open verify.
	"""
	tracking_number = (tracking_number or "").strip()
	base = frappe.utils.get_url().rstrip("/")
	# Prefer tracking-number route when available (shorter, human-meaningful)
	if tracking_number:
		return f"{tracking_number}\n{base}/ic-verify/sample/{tracking_number}"
	if docname:
		return verification_url("IC Sample Tracking", docname)
	return tracking_number


def render_sample_sticker_8mm_png(tracking_number: str, payload: str | None = None) -> bytes:
	"""Render a thermal sticker PNG: QR + tracking number aligned for 8mm tape height.

	Output is 300 DPI, height = 8mm (~94px), width sized to fit QR + sample number.
	"""
	from PIL import Image, ImageDraw, ImageFont

	tracking_number = (tracking_number or "").strip() or "SAMPLE"
	payload = payload or tracking_number

	# 8mm @ 300 DPI
	dpi = 300
	height_mm = 8.0
	height_px = max(int(round(height_mm / 25.4 * dpi)), 72)
	margin = max(2, int(round(0.3 / 25.4 * dpi)))
	qr_size = height_px - (2 * margin)

	qr_img = generate_qr_image(payload, box_size=8, border=1)
	qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.NEAREST)

	# Text beside QR — monospace-ish, fits 8mm height
	font = _sticker_font(max(10, int(height_px * 0.42)))
	# Measure text
	tmp = Image.new("RGB", (10, 10), "white")
	draw = ImageDraw.Draw(tmp)
	bbox = draw.textbbox((0, 0), tracking_number, font=font)
	text_w = bbox[2] - bbox[0]
	text_h = bbox[3] - bbox[1]
	gap = max(3, margin)
	width_px = margin + qr_size + gap + text_w + margin

	canvas = Image.new("RGB", (width_px, height_px), "white")
	canvas.paste(qr_img, (margin, margin))
	draw = ImageDraw.Draw(canvas)
	text_x = margin + qr_size + gap
	text_y = max(0, (height_px - text_h) // 2 - 1)
	draw.text((text_x, text_y), tracking_number, fill="black", font=font)

	buf = io.BytesIO()
	canvas.save(buf, format="PNG", dpi=(dpi, dpi))
	return buf.getvalue()


def _sticker_font(size: int):
	from PIL import ImageFont

	candidates = [
		"/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
		"/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
		"/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
		"/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf",
	]
	for path in candidates:
		try:
			return ImageFont.truetype(path, size=size)
		except Exception:
			continue
	return ImageFont.load_default()

