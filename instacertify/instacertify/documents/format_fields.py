# Copyright (c) Instacertify
"""Optional built-in fields on Documents / Data Collection Sheet format."""

from __future__ import annotations

from frappe.utils import cint

# (include_flag, label, desk fieldnames controlled by the flag)
OPTIONAL_FORMAT_FIELDS: list[tuple[str, str, list[str]]] = [
	("include_company_address", "Company Address", ["company_address"]),
	("include_product_name", "Product Name", ["product_name"]),
	("include_product_model", "Model / Variant", ["product_model"]),
	("include_product_brand", "Brand", ["product_brand"]),
	(
		"include_data_collection_remarks",
		"Data Collection Remarks",
		["data_collection_remarks"],
	),
	(
		"include_data_fields",
		"Additional Data Fields",
		["section_data_fields", "data_fields"],
	),
	(
		"include_sample_dispatch",
		"Sample Dispatch (legacy)",
		[
			"section_sample",
			"courier_name",
			"tracking_number",
			"column_break_sample",
			"dispatch_date",
			"pod_attachment",
			"sample_dispatch_remarks",
		],
	),
	("include_remarks", "Notes / Remarks", ["section_notes", "remarks"]),
]

# Product section stays visible if any of these product/address flags are on
PRODUCT_SECTION_FLAGS = (
	"include_company_address",
	"include_product_name",
	"include_product_model",
	"include_product_brand",
	"include_data_collection_remarks",
)

INCLUDE_FIELDNAMES = [flag for flag, _label, _fields in OPTIONAL_FORMAT_FIELDS]


def is_format_field_included(doc, include_flag: str) -> bool:
	"""Missing flag / null → included (backward compatible). Explicit 0 → hidden."""
	meta = getattr(doc, "meta", None)
	if meta is not None and not meta.has_field(include_flag):
		return True
	val = doc.get(include_flag) if hasattr(doc, "get") else getattr(doc, include_flag, None)
	if val is None or val == "":
		return True
	return cint(val) == 1


def format_field_flags(doc) -> dict[str, int]:
	"""API / portal payload: 1 = show, 0 = hide."""
	return {flag: 1 if is_format_field_included(doc, flag) else 0 for flag in INCLUDE_FIELDNAMES}


def copy_format_field_flags(source, target) -> None:
	"""Copy include_* checks from template → request (or request → template)."""
	for flag in INCLUDE_FIELDNAMES:
		src_meta = getattr(source, "meta", None)
		tgt_meta = getattr(target, "meta", None)
		if src_meta is not None and not src_meta.has_field(flag):
			continue
		if tgt_meta is not None and not tgt_meta.has_field(flag):
			continue
		target.set(flag, 1 if is_format_field_included(source, flag) else 0)


def doctype_include_fields() -> list[dict]:
	"""DocField dicts for Template / Request JSON (Check, default included)."""
	fields: list[dict] = [
		{
			"doctype": "DocField",
			"fieldname": "section_format_fields",
			"fieldtype": "Section Break",
			"label": "Format Fields (optional)",
			"collapsible": 1,
			"description": (
				"Uncheck to hide non-mandatory built-in fields from this sheet "
				"(desk, customer portal, and print). Checklist rows are controlled below."
			),
		},
		{
			"doctype": "DocField",
			"fieldname": "format_fields_help",
			"fieldtype": "HTML",
			"options": (
				'<p class="text-muted">These are the built-in Data Collection fields. '
				"Uncheck any field you do not need on this format. "
				"Mandatory checklist / fill rows stay in <b>Collection Sheet Rows</b>.</p>"
			),
		},
	]
	# Two columns of checks
	mid = (len(OPTIONAL_FORMAT_FIELDS) + 1) // 2
	for i, (flag, label, _fields) in enumerate(OPTIONAL_FORMAT_FIELDS):
		if i == mid:
			fields.append(
				{
					"doctype": "DocField",
					"fieldname": "column_break_format_fields",
					"fieldtype": "Column Break",
				}
			)
		fields.append(
			{
				"doctype": "DocField",
				"fieldname": flag,
				"fieldtype": "Check",
				"label": label,
				"default": "1",
			}
		)
	return fields
