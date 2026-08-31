# Copyright (c) Instacertify
"""Back-compat aliases for older desk JS that called instacertify.quotation_events.*.

Prefer instacertify.quotation.events — this module re-exports the same whitelisted APIs.
"""

from instacertify.quotation.events import (  # noqa: F401
	apply_quotation_template,
	duplicate_quotation_template,
	ensure_template_preview_quotation,
	get_quotation_template_payload,
	list_quote_formats_for_type,
	rename_quotation_template_display_name,
	save_quotation_as_template,
)
