#!/usr/bin/env bash
# Hostinger / production update for Instacertify (ERPNext bench).
# Run as the bench user (e.g. frappe), from anywhere:
#   SITE=erp.yourdomain.com bash apps/instacertify/scripts/hostinger_update.sh
#
# Optional env:
#   SITE          Site name (required if more than one site)
#   BRANCH        Git branch to deploy (default: main)
#   SKIP_BACKUP   Set to 1 to skip bench backup
#   SKIP_BUILD    Set to 1 to skip bench build
#   RESTART=0     Skip supervisor restart

set -euo pipefail

BRANCH="${BRANCH:-main}"
SKIP_BACKUP="${SKIP_BACKUP:-0}"
SKIP_BUILD="${SKIP_BUILD:-0}"
RESTART="${RESTART:-1}"

# Resolve bench root (script lives in apps/instacertify/scripts/).
# Use pwd -L so a symlink apps/instacertify → ~/src/erppronxt/instacertify
# still yields BENCH_ROOT=~/frappe-bench (not ~/src/erppronxt).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -L)"
APP_DIR="$(cd "${SCRIPT_DIR}/.." && pwd -L)"
BENCH_ROOT="$(cd "${APP_DIR}/../.." && pwd -L)"

if [[ ! -d "${BENCH_ROOT}/sites" ]]; then
	if [[ -d "${PWD}/sites" ]]; then
		BENCH_ROOT="${PWD}"
	elif [[ -d "${HOME}/frappe-bench/sites" ]]; then
		BENCH_ROOT="${HOME}/frappe-bench"
	else
		echo "ERROR: Could not find bench root (expected sites/ under ${BENCH_ROOT})"
		echo "Run from ~/frappe-bench or: SITE=... bash ~/frappe-bench/apps/instacertify/scripts/hostinger_update.sh"
		exit 1
	fi
fi

cd "${BENCH_ROOT}"

if [[ -z "${SITE:-}" ]]; then
	# Prefer single non-assets site
	mapfile -t SITES < <(ls -1 sites 2>/dev/null | grep -vE '^(assets|common_site_config.json|apps.txt)$' || true)
	if [[ ${#SITES[@]} -eq 1 ]]; then
		SITE="${SITES[0]}"
	else
		echo "ERROR: Set SITE=your.site.name (found: ${SITES[*]:-none})"
		exit 1
	fi
fi

echo "==> Bench: ${BENCH_ROOT}"
echo "==> Site:  ${SITE}"
echo "==> Branch: ${BRANCH}"

# Frappe app path (may be a symlink to ~/src/erppronxt/instacertify)
APP_PATH=""
for cand in apps/instacertify apps/erppronxt/instacertify; do
	if [[ -f "${cand}/instacertify/hooks.py" ]]; then
		APP_PATH="$(cd "${cand}" && pwd -P)"
		break
	fi
done
if [[ -z "${APP_PATH}" ]]; then
	echo "ERROR: instacertify app not found under apps/"
	echo "Expected apps/instacertify/instacertify/hooks.py (symlink to ~/src/erppronxt/instacertify is OK)."
	exit 1
fi
echo "==> App:   ${APP_PATH}"

# Git root is the erppronxt clone (parent of nested instacertify/), not apps/ alone
GIT_ROOT="$(git -C "${APP_PATH}" rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${GIT_ROOT}" ]]; then
	echo "ERROR: ${APP_PATH} is not inside a git checkout."
	echo "Re-install with: clone ~/src/erppronxt and ln -sfn ~/src/erppronxt/instacertify apps/instacertify"
	exit 1
fi
echo "==> Git:   ${GIT_ROOT}"

if [[ "${SKIP_BACKUP}" != "1" ]]; then
	echo "==> Backup (with files)"
	bench --site "${SITE}" backup --with-files
fi

echo "==> git fetch / checkout / pull ${BRANCH}"
cd "${GIT_ROOT}"
git fetch origin
git checkout "${BRANCH}"
git pull origin "${BRANCH}"
GIT_SHA="$(git rev-parse --short HEAD)"
cd "${BENCH_ROOT}"
echo "==> Deploying SHA ${GIT_SHA}"

echo "==> migrate"
bench --site "${SITE}" migrate

if [[ "${SKIP_BUILD}" != "1" ]]; then
	echo "==> build --app instacertify"
	bench build --app instacertify
fi

echo "==> clear-cache + ensure_workspaces"
bench --site "${SITE}" clear-cache
bench --site "${SITE}" execute instacertify.setup.workspace_setup.ensure_workspaces

echo "==> smoke check"
bench --site "${SITE}" execute instacertify.setup.deploy_smoke.run || {
	echo "WARN: smoke check reported issues — review output above"
}

if [[ "${RESTART}" == "1" ]]; then
	if command -v supervisorctl >/dev/null 2>&1; then
		echo "==> supervisorctl restart all"
		sudo supervisorctl restart all || supervisorctl restart all || true
	else
		echo "==> (no supervisorctl — restart workers manually if needed)"
	fi
fi

echo ""
echo "OK — Instacertify ${GIT_SHA} deployed to ${SITE}"
echo "Open the site, hard-refresh the browser (Ctrl+Shift+R), and verify Home + Testing & Samples."
