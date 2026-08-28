# Copyright (c) Instacertify
"""QC: Project Generate / Share Document List with template dropdown."""

from __future__ import annotations

import json

import frappe


def run_project_document_share_qc() -> dict:
	report = {"ok": [], "warn": [], "fail": []}

	def ok(m):
		report["ok"].append(m)

	def fail(m):
		report["fail"].append(m)

	def warn(m):
		report["warn"].append(m)

	frappe.set_user("Administrator")
	from instacertify.documents.api import (
		create_document_request_for_project,
		get_document_checklist_templates,
		preview_checklist_template,
	)

	templates = get_document_checklist_templates()
	(ok if isinstance(templates, list) else fail)(f"templates list len={len(templates or [])}")
	tmpl_name = None
	if templates:
		tmpl_name = templates[0]["name"]
		ok(f"template option {tmpl_name} items={templates[0].get('item_count')}")
		prev = preview_checklist_template(tmpl_name)
		(ok if prev.get("items") else fail)(f"preview items={len(prev.get('items') or [])}")
	else:
		warn("No active checklist templates — will use default list")

	project = frappe.db.get_value("Project", {"customer": ["is", "set"]}, "name", order_by="modified desc")
	if not project:
		fail("No Project with customer")
		report["summary"] = {"ok": len(report["ok"]), "fail": len(report["fail"]), "passed": False}
		print(json.dumps(report, indent=2, default=str))
		return report

	res = create_document_request_for_project(
		project=project,
		title="QC Document List Share",
		template=tmpl_name,
		force_new=1,
		replace_items=1,
	)
	if res.get("url") and "/ic-documents/" in res["url"]:
		ok(f"share url ok {res.get('document_request')}")
	else:
		fail(f"bad share: {res}")
	docs = res.get("documents") or []
	(ok if docs else fail)(f"documents generated={len(docs)}")
	for row in docs[:5]:
		ok(f"doc: {row.get('document_name')}")

	# Reuse path without force_new
	res2 = create_document_request_for_project(project=project, template=tmpl_name, replace_items=1)
	(ok if res2.get("document_request") else fail)(f"reuse {res2.get('document_request')}")

	report["summary"] = {
		"ok": len(report["ok"]),
		"warn": len(report["warn"]),
		"fail": len(report["fail"]),
		"passed": len(report["fail"]) == 0,
		"url": res.get("url"),
		"document_request": res.get("document_request"),
	}
	print(json.dumps(report, indent=2, default=str))
	return report
