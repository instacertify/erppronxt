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


def render_sample_sticker_50x25_png(tracking_number: str, payload: str | None = None) -> bytes:
	"""Render a 50mm × 25mm sample sticker PNG (QR + tracking + website).

	Output is 300 DPI (≈591 × 295 px).
	"""
	from PIL import Image, ImageDraw, ImageFont

	tracking_number = (tracking_number or "").strip() or "SAMPLE"
	payload = payload or tracking_number
	website_line1 = "For more information visit"
	website_line2 = "www.instacertify.com"

	dpi = 300
	width_mm, height_mm = 50.0, 25.0
	width_px = int(round(width_mm / 25.4 * dpi))
	height_px = int(round(height_mm / 25.4 * dpi))
	margin = max(4, int(round(1.2 / 25.4 * dpi)))
	gap = max(6, int(round(1.6 / 25.4 * dpi)))
	qr_size = int(round(18.0 / 25.4 * dpi))

	qr_img = generate_qr_image(payload, box_size=8, border=1)
	qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.NEAREST)

	label_font = _sticker_font(max(11, int(round(2.1 / 25.4 * dpi))))
	trk_font = _sticker_font(max(16, int(round(3.2 / 25.4 * dpi))))
	info_font = _sticker_font(max(10, int(round(1.9 / 25.4 * dpi))))

	canvas = Image.new("RGB", (width_px, height_px), "white")
	qr_y = max(margin, (height_px - qr_size) // 2)
	canvas.paste(qr_img, (margin, qr_y))

	draw = ImageDraw.Draw(canvas)
	text_x = margin + qr_size + gap
	text_right = width_px - margin
	max_text_w = max(40, text_right - text_x)

	# Vertical stack: SAMPLE label, tracking number, website lines
	y = margin + 2
	draw.text((text_x, y), "SAMPLE", fill="#333333", font=label_font)
	y += int(label_font.size * 1.35) + 2

	# Wrap tracking number if needed
	trk = tracking_number
	bbox = draw.textbbox((0, 0), trk, font=trk_font)
	if (bbox[2] - bbox[0]) > max_text_w and len(trk) > 12:
		# shrink font slightly for long numbers
		trk_font = _sticker_font(max(12, int(trk_font.size * 0.85)))
	draw.text((text_x, y), trk, fill="black", font=trk_font)
	y += int(trk_font.size * 1.35) + 4

	draw.text((text_x, y), website_line1, fill="#222222", font=info_font)
	y += int(info_font.size * 1.3) + 1
	draw.text((text_x, y), website_line2, fill="black", font=info_font)

	buf = io.BytesIO()
	canvas.save(buf, format="PNG", dpi=(dpi, dpi))
	return buf.getvalue()


# Back-compat alias
def render_sample_sticker_8mm_png(tracking_number: str, payload: str | None = None) -> bytes:
	return render_sample_sticker_50x25_png(tracking_number, payload)


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

