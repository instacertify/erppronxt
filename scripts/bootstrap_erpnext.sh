#!/usr/bin/env bash
# Bootstrap Instacertify ERPNext 16.33 development environment
set -euo pipefail

export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
# shellcheck disable=SC1091
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 24 >/dev/null 2>&1 || nvm install 24
export PATH="$NVM_DIR/versions/node/$(node -v | tr -d v | xargs -I{} echo {})/bin:$HOME/.local/bin:$PATH" 2>/dev/null || true
export PATH="$HOME/.local/bin:$PATH"

BENCH_DIR="${BENCH_DIR:-$HOME/frappe-bench}"
SITE="${SITE:-instacertify.localhost}"
DB_ROOT_PASSWORD="${DB_ROOT_PASSWORD:-Instacertify@Root123}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin}"
REPO_APP_DIR="$(cd "$(dirname "$0")/.." && pwd)/instacertify"

echo "==> Ensuring uv + bench"
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
command -v bench >/dev/null || uv tool install frappe-bench --python python3.14
uv python install 3.14 >/dev/null 2>&1 || true

if [ ! -d "$BENCH_DIR/apps/frappe" ]; then
  echo "==> Initializing bench"
  UV_PYTHON=3.14 bench init "$BENCH_DIR" --frappe-branch version-16 --python python3.14 --skip-redis-config-generation
fi

cd "$BENCH_DIR"
bench set-config -g redis_cache "redis://127.0.0.1:6379" || true
bench set-config -g redis_queue "redis://127.0.0.1:6379" || true
bench set-config -g redis_socketio "redis://127.0.0.1:6379" || true

if [ ! -d apps/erpnext ]; then
  echo "==> Getting ERPNext v16.33.0"
  bench get-app erpnext --branch v16.33.0
fi

if [ ! -d apps/hrms ]; then
  echo "==> Getting HRMS version-16 (hiring → FnF)"
  bench get-app hrms --branch version-16
fi

if [ ! -d apps/india_compliance ]; then
  echo "==> Getting india_compliance version-16"
  bench get-app https://github.com/resilient-tech/india-compliance --branch version-16 || true
fi

if [ ! -d "sites/$SITE" ]; then
  echo "==> Creating site $SITE"
  bench new-site "$SITE" \
    --mariadb-root-password "$DB_ROOT_PASSWORD" \
    --admin-password "$ADMIN_PASSWORD" \
    --db-root-username root \
    --no-mariadb-socket \
    --set-default
  bench --site "$SITE" install-app erpnext
fi

# Link / install custom app from this repository
if [ ! -e apps/instacertify ]; then
  ln -s "$REPO_APP_DIR" apps/instacertify
fi
grep -q '^instacertify$' sites/apps.txt || echo instacertify >> sites/apps.txt
./env/bin/pip install -e apps/instacertify -q
./env/bin/pip install 'qrcode[pil]' -q

if ! bench --site "$SITE" list-apps | grep -q hrms; then
  bench --site "$SITE" install-app hrms || true
fi
if [ -d apps/india_compliance ] && ! bench --site "$SITE" list-apps | grep -q india_compliance; then
  bench --site "$SITE" install-app india_compliance || true
fi

if ! bench --site "$SITE" list-apps | grep -q instacertify; then
  bench --site "$SITE" install-app instacertify
else
  bench --site "$SITE" migrate
fi

echo "==> Done. Start with: cd $BENCH_DIR && bench start"
echo "    Site: http://127.0.0.1:8000  (Admin / $ADMIN_PASSWORD)"
echo "    Load demo: bench --site $SITE execute instacertify.setup.demo_data.execute"
