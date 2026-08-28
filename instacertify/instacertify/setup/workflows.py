# Copyright (c) Instacertify
"""Quotation workflow setup."""

from __future__ import annotations

import frappe

STATES = [
	("IC Draft", "Primary"),
	("IC Internal Review", "Warning"),
	("IC Ready to Share", "Info"),
	("IC Shared with Customer", "Info"),
	("IC Customer Review", "Warning"),
	("IC Accepted", "Success"),
	("IC Changes Requested", "Warning"),
	("IC Rejected / Lost", "Danger"),
]

ACTIONS = [
	"IC Submit for Review",
	"IC Approve for Sharing",
	"IC Share with Customer",
	"IC Mark Accepted",
	"IC Request Changes",
	"IC Revise",
	"IC Reject",
]


def ensure_quotation_workflow():
	for state, style in STATES:
		if not frappe.db.exists("Workflow State", state):
			frappe.get_doc(
				{"doctype": "Workflow State", "workflow_state_name": state, "style": style}
			).insert(ignore_permissions=True)

	for action in ACTIONS:
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc(
				{"doctype": "Workflow Action Master", "workflow_action_name": action}
			).insert(ignore_permissions=True)

	name = "IC Quotation Workflow"
	if frappe.db.exists("Workflow", name):
		return

	doc = frappe.get_doc(
		{
			"doctype": "Workflow",
			"workflow_name": name,
			"document_type": "Quotation",
			"is_active": 1,
			"override_status": 0,
			"send_email_alert": 0,
			"workflow_state_field": "workflow_state",
			"states": [
				{"state": "IC Draft", "doc_status": "0", "allow_edit": "IC Sales Person"},
				{"state": "IC Draft", "doc_status": "0", "allow_edit": "IC Admin"},
				{"state": "IC Internal Review", "doc_status": "0", "allow_edit": "IC Senior Operations"},
				{"state": "IC Internal Review", "doc_status": "0", "allow_edit": "IC Admin"},
				{"state": "IC Ready to Share", "doc_status": "0", "allow_edit": "IC Sales Person"},
				{"state": "IC Ready to Share", "doc_status": "0", "allow_edit": "IC Admin"},
				{"state": "IC Shared with Customer", "doc_status": "1", "allow_edit": "IC Admin"},
				{"state": "IC Customer Review", "doc_status": "1", "allow_edit": "IC Admin"},
				{"state": "IC Accepted", "doc_status": "1", "allow_edit": "IC Admin"},
				{"state": "IC Changes Requested", "doc_status": "1", "allow_edit": "IC Sales Person"},
				{"state": "IC Changes Requested", "doc_status": "1", "allow_edit": "IC Admin"},
				{"state": "IC Rejected / Lost", "doc_status": "1", "allow_edit": "IC Admin"},
			],
			"transitions": [
				{
					"state": "IC Draft",
					"action": "IC Submit for Review",
					"next_state": "IC Internal Review",
					"allowed": "IC Sales Person",
				},
				{
					"state": "IC Draft",
					"action": "IC Submit for Review",
					"next_state": "IC Internal Review",
					"allowed": "IC Admin",
				},
				{
					"state": "IC Internal Review",
					"action": "IC Approve for Sharing",
					"next_state": "IC Ready to Share",
					"allowed": "IC Senior Operations",
				},
				{
					"state": "IC Internal Review",
					"action": "IC Approve for Sharing",
					"next_state": "IC Ready to Share",
					"allowed": "IC Admin",
				},
				{
					"state": "IC Ready to Share",
					"action": "IC Share with Customer",
					"next_state": "IC Shared with Customer",
					"allowed": "IC Sales Person",
				},
				{
					"state": "IC Ready to Share",
					"action": "IC Share with Customer",
					"next_state": "IC Shared with Customer",
					"allowed": "IC Admin",
				},
				{
					"state": "IC Shared with Customer",
					"action": "IC Mark Accepted",
					"next_state": "IC Accepted",
					"allowed": "IC Admin",
				},
				{
					"state": "IC Shared with Customer",
					"action": "IC Request Changes",
					"next_state": "IC Changes Requested",
					"allowed": "IC Admin",
				},
				{
					"state": "IC Changes Requested",
					"action": "IC Revise",
					"next_state": "IC Draft",
					"allowed": "IC Sales Person",
				},
				{
					"state": "IC Shared with Customer",
					"action": "IC Reject",
					"next_state": "IC Rejected / Lost",
					"allowed": "IC Admin",
				},
			],
		}
	)
	try:
		doc.insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "IC Quotation Workflow")
