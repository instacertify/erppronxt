# Copyright (c) Instacertify
"""Cumulative QC for this Instacertify session — runs all suites + spot checks."""

from __future__ import annotations

import json
import os
import traceback

import frappe


def run_full_session_qc(session_target: int = 50, save_print_samples: int = 0) -> dict:
	"""Run interop, session bulk, print, guest portal, and feature spot checks."""
	out = {
		"suites": {},
		"spot": {"ok": [], "warn": [], "fail": []},
		"passed": False,
		"suite_fails": [],
	}

	def spot_ok(m):
		out["spot"]["ok"].append(m)

	def spot_warn(m):
		out["spot"]["warn"].append(m)

	def spot_fail(m):
		out["spot"]["fail"].append(m)

	frappe.set_user("Administrator")

	# --- Suite: interop ---
	try:
		from instacertify.setup.interop_qc import run as interop_run

		interop = interop_run()
		out["suites"]["interop"] = {
			"ok": interop.get("ok"),
			"warn": interop.get("warn"),
			"fail": interop.get("fail"),
			"failures": (interop.get("report") or {}).get("fail", [])[:20],
		}
		if (interop.get("fail") or 0) > 0:
			out["suite_fails"].append("interop")
	except Exception:
		out["suites"]["interop"] = {"error": traceback.format_exc()}
		out["suite_fails"].append("interop")

	# --- Suite: session bulk (idempotent) ---
	try:
		from instacertify.setup.session_bulk_qc import run_session_bulk_qc

		bulk = run_session_bulk_qc(target=session_target)
		created = bulk.get("created") or {}
		out["suites"]["session_bulk"] = {
			"ok": bulk.get("ok"),
			"created": created,
			"total_records": sum(created.values()) if isinstance(created, dict) else 0,
			"errors": (bulk.get("errors") or [])[:20],
			"interop": bulk.get("interop"),
		}
		if bulk.get("ok") is False or bulk.get("errors"):
			out["suite_fails"].append("session_bulk")
	except Exception:
		out["suites"]["session_bulk"] = {"ok": False, "error": traceback.format_exc()}
		out["suite_fails"].append("session_bulk")

	# --- Suite: print formats ---
	try:
		from instacertify.setup.print_format_qc import run_print_format_qc

		prints = run_print_format_qc(save_samples=save_print_samples)
		summary = prints.get("summary") or {}
		out["suites"]["print_formats"] = {
			"ok": summary.get("ok", len(prints.get("ok") or [])),
			"warn": summary.get("warn", len(prints.get("warn") or [])),
			"fail": summary.get("fail", len(prints.get("fail") or [])),
			"passed": summary.get("passed", len(prints.get("fail") or []) == 0),
			"failures": list(prints.get("fail") or [])[:20],
		}
		if not out["suites"]["print_formats"]["passed"]:
			out["suite_fails"].append("print_formats")
	except Exception:
		out["suites"]["print_formats"] = {"passed": False, "error": traceback.format_exc()}
		out["suite_fails"].append("print_formats")

	# --- Suite: guest portal ---
	try:
		from instacertify.setup.guest_portal_qc import run_guest_portal_qc

		guest = run_guest_portal_qc()
		summary = guest.get("summary") or {}
		out["suites"]["guest_portal"] = {
			"ok": summary.get("ok", len(guest.get("ok") or [])),
			"warn": summary.get("warn", len(guest.get("warn") or [])),
			"fail": summary.get("fail", len(guest.get("fail") or [])),
			"passed": summary.get("passed", len(guest.get("fail") or []) == 0),
			"failures": list(guest.get("fail") or [])[:20],
			"urls": guest.get("urls") or {},
		}
		if not out["suites"]["guest_portal"]["passed"]:
			out["suite_fails"].append("guest_portal")
	except Exception:
		out["suites"]["guest_portal"] = {"passed": False, "error": traceback.format_exc()}
		out["suite_fails"].append("guest_portal")

	# --- Spot checks ---
	_spot_libraries(spot_ok, spot_warn, spot_fail)
	_spot_explore(spot_ok, spot_warn, spot_fail)
	_spot_expenses(spot_ok, spot_warn, spot_fail)
	_spot_assets(spot_ok, spot_warn, spot_fail)
	_spot_portals(spot_ok, spot_warn, spot_fail)

	if out["spot"]["fail"]:
		out["suite_fails"].append("spot")

	out["passed"] = len(out["suite_fails"]) == 0
	out["totals"] = {
		"ok": sum(
			[
				out["suites"].get("interop", {}).get("ok") or 0,
				out["suites"].get("print_formats", {}).get("ok") or 0,
				out["suites"].get("guest_portal", {}).get("ok") or 0,
				len(out["spot"]["ok"]),
			]
		),
		"warn": sum(
			[
				out["suites"].get("interop", {}).get("warn") or 0,
				out["suites"].get("print_formats", {}).get("warn") or 0,
				out["suites"].get("guest_portal", {}).get("warn") or 0,
				len(out["spot"]["warn"]),
			]
		),
		"fail": sum(
			[
				out["suites"].get("interop", {}).get("fail") or 0,
				out["suites"].get("print_formats", {}).get("fail") or 0,
				out["suites"].get("guest_portal", {}).get("fail") or 0,
				len(out["spot"]["fail"]),
				len(out["suites"].get("session_bulk", {}).get("errors") or []),
			]
		),
		"session_records": out["suites"].get("session_bulk", {}).get("total_records") or 0,
	}

	print(json.dumps(out, indent=2, default=str))
	return out


def _spot_libraries(ok, warn, fail):
	try:
		from instacertify.setup.library_upload import get_library_summary
		from instacertify.setup import library_upload as lu

		summary = get_library_summary()
		ok(f"Library summary ok keys={list(summary.keys()) if isinstance(summary, dict) else type(summary)}")
		for dt in ("IC Quotation Template", "IC Laboratory", "IC Quote Format File"):
			(ok if frappe.db.exists("DocType", dt) else fail)(f"DocType {dt}")
		for fn in (
			"download_quote_format_upload_template",
			"download_lab_scope_template",
			"create_quote_format_from_upload",
			"create_laboratory_from_upload",
			"import_laboratory_scopes_csv",
		):
			(ok if hasattr(lu, fn) else fail)(f"library_upload.{fn}")
		# Smoke: template downloads return a file URL
		for fn in ("download_quote_format_upload_template", "download_lab_scope_template"):
			res = getattr(lu, fn)()
			if isinstance(res, dict) and (res.get("file_url") or res.get("file_name") or res.get("message")):
				ok(f"{fn} returned file")
			else:
				fail(f"{fn} bad response: {res!r}")
	except Exception as e:
		fail(f"Libraries: {e}")


def _spot_explore(ok, warn, fail):
	try:
		from instacertify.explore.dashboard import get_explore_prompts

		frappe.set_user("Administrator")
		prompts = get_explore_prompts()
		cards = prompts.get("cards") if isinstance(prompts, dict) else prompts
		if not cards:
			fail("Explore prompts empty")
			return
		ok(f"Explore prompts: {len(cards)} cards")
		blob = json.dumps(cards, default=str).lower()
		if "expense" in blob:
			ok("Explore includes expense prompt")
		else:
			warn("Explore may lack expense card (role-dependent)")
	except Exception as e:
		fail(f"Explore: {e}")


def _spot_expenses(ok, warn, fail):
	try:
		(ok if frappe.db.exists("DocType", "IC Expense Claim") else fail)("IC Expense Claim DocType")
		from instacertify.expenses import api as exp

		for fn in ("create_expense_claim", "set_expense_status"):
			(ok if hasattr(exp, fn) else fail)(f"expenses.api.{fn}")

		marker = "FULL-QC-EXPENSE"
		existing = frappe.db.get_value("IC Expense Claim", {"description": marker}, "name")
		if existing:
			ok(f"Expense claim exists {existing}")
		else:
			name = exp.create_expense_claim(
				title="Full QC Expense",
				category="Petty Cash",
				amount=10,
				expense_date=frappe.utils.nowdate(),
				description=marker,
			)
			ok(f"Created expense claim {name}")
		ok(f"Expense claims in DB: {frappe.db.count('IC Expense Claim')}")
	except Exception as e:
		fail(f"Expenses: {e}")


def _spot_assets(ok, warn, fail):
	app_path = frappe.get_app_path("instacertify")
	for rel in (
		"public/js/instacertify.js",
		"public/css/instacertify.css",
		"www/ic_quotation.py",
		"www/ic_documents.py",
		"www/ic_verify.py",
		"www/ic_report.py",
		"setup/library_upload.py",
		"explore/dashboard.py",
		"expenses/api.py",
	):
		path = os.path.join(app_path, rel)
		(ok if os.path.isfile(path) else fail)(f"Asset {rel}")


def _spot_portals(ok, warn, fail):
	try:
		for route in ("ic_quotation", "ic_documents", "ic_verify", "ic_report"):
			mod = f"instacertify.www.{route}"
			try:
				frappe.get_module(mod)
				ok(f"Portal module {mod}")
			except Exception as e:
				fail(f"Portal module {mod}: {e}")

		for fmt in (
			"Instacertify Quotation",
			"Instacertify Sales Invoice",
			"Instacertify Sample Label",
			"Instacertify Testing Request",
			"Instacertify Joining Letter",
		):
			(ok if frappe.db.exists("Print Format", fmt) else fail)(f"Print Format {fmt}")
	except Exception as e:
		fail(f"Portals: {e}")
