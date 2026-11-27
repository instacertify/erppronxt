# Copyright (c) Instacertify
"""Embed print images so the PDF does not depend on a website address."""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

import frappe

_MIME = {
	".png": "image/png",
	".jpg": "image/jpeg",
	".jpeg": "image/jpeg",
	".webp": "image/webp",
	".gif": "image/gif",
	".svg": "image/svg+xml",
}


def quote_image_data_uri(src: str | None) -> str:
	"""Return a data URI for a logo, stamp, or other print image.

	A path such as ``/assets/...`` is left as a website address by the old
	print HTML. Chrome's PDF pass does not load that address, so the picture
	comes out blank. The file bytes are placed in the page instead.
	"""
	raw = (src or "").strip()
	if not raw:
		return ""
	if raw.startswith("data:"):
		return raw
	path = _image_file(raw)
	if path is not None and path.is_file():
		mime = _MIME.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or "image/png"
		encoded = base64.b64encode(path.read_bytes()).decode()
		return f"data:{mime};base64,{encoded}"
	if raw.startswith(("http://", "https://")):
		return raw
	return frappe.utils.get_url(raw)


def _image_file(src: str) -> Path | None:
	if src.startswith("/assets/"):
		rest = src[len("/assets/") :]
		app, _, rel = rest.partition("/")
		if not app or not rel:
			return None
		try:
			package = Path(frappe.get_app_path(app))
		except Exception:
			return None
		candidates = (
			package / "public" / rel,
			package.parent / "public" / rel,
		)
		for candidate in candidates:
			if candidate.is_file():
				return candidate
		return candidates[0]
	name = src.rsplit("/", 1)[-1]
	if src.startswith("/private/files/"):
		return Path(frappe.get_site_path("private", "files", name))
	if src.startswith("/files/"):
		return Path(frappe.get_site_path("public", "files", name))
	return None
