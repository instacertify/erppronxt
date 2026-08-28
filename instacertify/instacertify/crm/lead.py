# Copyright (c) Instacertify
"""Lead class override — sync mandatory person/firm name before ERPNext checks."""

from __future__ import annotations

from erpnext.crm.doctype.lead.lead import Lead

from instacertify.crm.events import _ensure_mandatory_name, _sync_party_name


class ICLead(Lead):
	def before_insert(self):
		_sync_party_name(self)
		super().before_insert()

	def validate(self):
		_sync_party_name(self)
		_ensure_mandatory_name(self)
		super().validate()
