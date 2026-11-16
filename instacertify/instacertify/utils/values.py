# Copyright (c) Instacertify
"""Small pure helpers (no Frappe import)."""


def pick_nonempty(existing, fallback):
	"""Return stripped existing value, else stripped fallback, else None."""
	existing = (existing or "").strip()
	if existing:
		return existing
	return (fallback or "").strip() or None
