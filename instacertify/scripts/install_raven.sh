#!/usr/bin/env bash
# Install or update Raven chat (https://github.com/frappe/raven) on this bench.
# Run as the bench user:
#   SITE=next.instacertify.com bash apps/instacertify/scripts/install_raven.sh
#
# Raven opens at https://<site>/raven
# Optional: RAVEN_REF=v3.2.0  (a tag or branch)

set -euo pipefail

RAVEN_REF="${RAVEN_REF:-v3.2.0}"
RAVEN_REPO="${RAVEN_REPO:-https://github.com/frappe/raven}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -L)"
APP_DIR="$(cd "${SCRIPT_DIR}/.." && pwd -L)"
BENCH_ROOT="$(cd "${APP_DIR}/../.." && pwd -L)"
if [[ ! -d "${BENCH_ROOT}/sites" ]]; then
	if [[ -d "${HOME}/frappe-bench/sites" ]]; then
		BENCH_ROOT="${HOME}/frappe-bench"
	else
		echo "ERROR: Could not find the bench (sites/ folder)."
		exit 1
	fi
fi
cd "${BENCH_ROOT}"

if [[ -z "${SITE:-}" ]]; then
	mapfile -t SITES < <(ls -1 sites 2>/dev/null | grep -vE '^(assets|common_site_config.json|apps.txt)$' || true)
	if [[ ${#SITES[@]} -eq 1 ]]; then
		SITE="${SITES[0]}"
	else
		echo "ERROR: Set SITE=next.instacertify.com"
		exit 1
	fi
fi

echo "==> Bench: ${BENCH_ROOT}"
echo "==> Site:  ${SITE}"
echo "==> Raven: ${RAVEN_REF}"

if [[ ! -d apps/raven/.git ]]; then
	echo "==> Download Raven"
	bench get-app --branch "${RAVEN_REF}" "${RAVEN_REPO}"
else
	echo "==> Update Raven to ${RAVEN_REF}"
	git -C apps/raven fetch origin --tags
	git -C apps/raven checkout "${RAVEN_REF}"
	./env/bin/pip install -q -e apps/raven
fi

if ! bench --site "${SITE}" list-apps | awk '{print $1}' | grep -qx raven; then
	echo "==> Install Raven on ${SITE}"
	bench --site "${SITE}" install-app raven
else
	echo "==> Raven is already installed on ${SITE}"
	bench --site "${SITE}" migrate
fi

echo "==> Build Raven"
bench build --app raven
bench --site "${SITE}" clear-cache

if [[ -f apps/instacertify/instacertify/hooks.py ]]; then
	bench --site "${SITE}" execute instacertify.setup.raven_setup.configure || true
	bench --site "${SITE}" execute instacertify.setup.workspace_setup.ensure_workspaces || true
fi

echo ""
echo "Raven chat is ready at: /raven"
echo "Sign in, then open Chat in the left menu, or go straight to /raven."
