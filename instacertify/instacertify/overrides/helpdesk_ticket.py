# Copyright (c) Instacertify
"""Helpdesk Ticket Connections.

The ticket points at its project through its own ``project`` field. Without this
the Connections box looked for a ``project`` column on Project, which does not
exist, and every ticket opened with a server error.
"""

from __future__ import annotations


def get_dashboard_data(data):
	data = data or {}
	data.setdefault("internal_links", {})
	data["internal_links"]["Project"] = "project"
	return data
