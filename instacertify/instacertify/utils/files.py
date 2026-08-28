# Copyright (c) Instacertify
"""Ensure uploaded files are from ERPNext File storage (internal drive), not external URLs."""

from __future__ import annotations

import frappe
from frappe import _


def assert_internal_file(file_url: str | None, label: str = "File"):
	"""Accept only local File attachments under /files/ or /private/files/.

	Blocks Google Drive / Dropbox / arbitrary http(s) paste-URLs.
	"""
	if not file_url:
		frappe.throw(_("{0} is required — select from your device or File Library").format(_(label)))
	url = str(file_url).strip().split("?")[0]
	site = (frappe.utils.get_url() or "").rstrip("/")
	if url.startswith("http://") or url.startswith("https://"):
		if url.startswith(site + "/files/") or url.startswith(site + "/private/files/"):
			url = url[len(site) :]
		else:
			frappe.throw(
				_(
					"External drive / web links are not allowed. "
					"Upload from your device or pick a file from the Instacertify File Library."
				)
			)

	if not (url.startswith("/files/") or url.startswith("/private/files/")):
		frappe.throw(
			_(
				"Invalid file. Use Attach → My Device or Library (internal drive), not a pasted URL."
			)
		)

	exists = frappe.db.exists("File", {"file_url": url}) or frappe.db.exists(
		"File", {"file_url": file_url}
	)
	if not exists:
		fname = url.rsplit("/", 1)[-1]
		exists = frappe.db.exists("File", {"file_name": fname})
	if not exists:
		frappe.throw(_("Uploaded file not found in File Library. Please upload again."))
	return url
