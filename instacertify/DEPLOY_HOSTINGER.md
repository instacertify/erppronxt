# Deploy Instacertify (ERPNext) on Hostinger

This build is a **Frappe / ERPNext** app (`instacertify`). It needs a **Linux VPS** (Hostinger **KVM VPS** or Cloud VPS), **not** shared Web Hosting / hPanel PHP hosting.

**Repo:** `https://github.com/instacertify/erppronxt`  
**Branch to deploy:** `main`  
**App name:** `instacertify` (Python package + bench app)

---

## Pre-flight (verified)

Local bench checks against current `main`:

| Check | Result |
|-------|--------|
| `bench migrate` | Pass |
| `bench build --app instacertify` | Pass (~0.6s) |
| Installed apps | frappe, erpnext, instacertify, india_compliance, hrms, gameplan |
| Core DocTypes (TR, Sample, Lab, TRF, …) | Present |
| Instacertify Home workspace + Home Dashboard | Present |
| Customer history API | OK |

After every Hostinger update, run:

```bash
bench --site YOUR_SITE execute instacertify.setup.deploy_smoke.run
```

Or use the one-shot update script (Option B below).

---

## What you need on Hostinger

| Item | Recommendation |
|------|----------------|
| Plan | Hostinger **VPS** (Ubuntu **24.04** preferred) |
| RAM | **8 GB** preferred (4 GB minimum) |
| Disk | 40 GB+ SSD |
| Python | **3.14+** (matches `pyproject.toml` / ERPNext 16 in this repo) |
| Access | Root SSH |
| Domain | Point A record to the VPS public IP |

Shared hosting, WordPress, or “upload ZIP to `public_html`” will **not** run this stack.

### Python 3.14 on Ubuntu

ERPNext / Frappe for this project expect **Python ≥ 3.14**. On Ubuntu 24.04, install a 3.14 toolchain before `bench init` (example with deadsnakes — adjust if your image already has 3.14):

```bash
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt install -y python3.14 python3.14-venv python3.14-dev
python3.14 --version
```

When initializing bench, point at that interpreter:

```bash
bench init --frappe-branch version-16 --python python3.14 frappe-bench
```

---

## Option A — Fresh VPS (first production install)

### 1. Create the VPS

1. Hostinger → **VPS** → create Ubuntu 24.04 (or 22.04 + Python 3.14 as above).
2. Note the **IP**, **root password** (or SSH key).
3. In DNS (Hostinger Domains): set `A` record for your site (e.g. `erp.yourdomain.com`) → VPS IP. Wait for DNS.

### 2. SSH in and prepare the server

```bash
ssh root@YOUR_VPS_IP
apt update && apt upgrade -y
apt install -y git python3-dev python3-pip python3-venv redis-server \
  mariadb-server nginx supervisor curl software-properties-common \
  libffi-dev libssl-dev wkhtmltopdf xvfb fontconfig libxrender1 \
  build-essential libmariadb-dev pkg-config
```

Secure MariaDB (set a strong root password when prompted):

```bash
mysql_secure_installation
```

Create a bench user (do not run bench as root long-term):

```bash
adduser frappe
usermod -aG sudo frappe
su - frappe
```

### 3. Install Frappe Bench + ERPNext 16

As user `frappe`:

```bash
# Node 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g yarn

# Bench CLI
pip3 install frappe-bench --user
echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

# New bench (match ERPNext 16 + Python 3.14)
bench init --frappe-branch version-16 --python python3.14 frappe-bench
cd frappe-bench

bench get-app erpnext --branch version-16
bench get-app https://github.com/resilient-tech/india-compliance --branch version-16
bench get-app hrms --branch version-16
bench get-app gameplan --branch develop

# Instacertify — do NOT use bench get-app on this repo.
# GitHub repo root is erppronxt; the Frappe app lives in the nested
# folder `instacertify/` (pyproject.toml + package). bench get-app
# looks for setup.py at the clone root and fails with FileNotFoundError.
```

Install Instacertify by cloning the repo and symlinking the nested app:

```bash
cd ~/frappe-bench/apps
# Remove any failed get-app / bad rename leftovers
rm -rf erppronxt instacertify

mkdir -p ~/src
if [ -d ~/src/erppronxt/.git ]; then
  git -C ~/src/erppronxt fetch origin
  git -C ~/src/erppronxt checkout main
  git -C ~/src/erppronxt pull origin main
else
  git clone --branch main https://github.com/instacertify/erppronxt.git ~/src/erppronxt
fi

ln -sfn ~/src/erppronxt/instacertify ~/frappe-bench/apps/instacertify

# Must exist:
ls ~/frappe-bench/apps/instacertify/pyproject.toml
ls ~/frappe-bench/apps/instacertify/instacertify/hooks.py

cd ~/frappe-bench
# Rewrite apps.txt cleanly (avoids "hrmsinstacertify" if a prior line lacked a trailing newline)
python3 - <<'PY'
from pathlib import Path
p = Path("sites/apps.txt")
apps = [ln.strip() for ln in p.read_text().splitlines() if ln.strip()]
# undo accidental concatenations from a missing trailing newline
fixed = []
for a in apps:
    if a == "hrmsinstacertify":
        fixed.extend(["hrms", "instacertify"])
    else:
        fixed.append(a)
for name in ("frappe", "erpnext", "india_compliance", "hrms", "gameplan", "instacertify"):
    if name not in fixed and (Path("apps") / name).exists():
        fixed.append(name)
# keep unique order
seen, out = set(), []
for a in fixed:
    if a not in seen:
        seen.add(a)
        out.append(a)
p.write_text("\n".join(out) + "\n")
print(p.read_text())
PY
./env/bin/pip install -e ./apps/instacertify
bench build --app instacertify
```

### 4. Create the site and install apps

```bash
cd ~/frappe-bench
bench new-site erp.yourdomain.com \
  --mariadb-root-password 'YOUR_DB_ROOT_PASSWORD' \
  --admin-password 'STRONG_ADMIN_PASSWORD'

bench --site erp.yourdomain.com install-app erpnext
bench --site erp.yourdomain.com install-app india_compliance
bench --site erp.yourdomain.com install-app hrms
bench --site erp.yourdomain.com install-app gameplan
bench --site erp.yourdomain.com install-app instacertify

bench --site erp.yourdomain.com migrate
bench build --app instacertify
bench --site erp.yourdomain.com clear-cache
bench --site erp.yourdomain.com execute instacertify.setup.workspace_setup.ensure_workspaces
bench --site erp.yourdomain.com execute instacertify.setup.deploy_smoke.run
```

### 5. Production mode (nginx + supervisor + SSL)

```bash
cd ~/frappe-bench
sudo bench setup production frappe
bench setup nginx
sudo bench setup lets-encrypt erp.yourdomain.com
# or: sudo certbot --nginx -d erp.yourdomain.com

sudo supervisorctl restart all
sudo systemctl reload nginx
```

Open `https://erp.yourdomain.com` → login as **Administrator**.

---

## Option B — Update an existing Hostinger bench (recommended)

One-shot script (from bench root, as user `frappe`):

```bash
cd ~/frappe-bench
SITE=erp.yourdomain.com bash apps/instacertify/scripts/hostinger_update.sh
```

What it does: backup → `git pull origin main` → migrate → build → clear-cache → `ensure_workspaces` → smoke check → supervisor restart.

Manual equivalent:

```bash
ssh frappe@YOUR_VPS_IP
cd ~/frappe-bench

bench --site erp.yourdomain.com backup --with-files

# Prefer the update script (handles nested repo + symlink).
# Manual git pull must run on the clone root, not apps/instacertify alone:
git -C ~/src/erppronxt fetch origin
git -C ~/src/erppronxt checkout main
git -C ~/src/erppronxt pull origin main

bench --site erp.yourdomain.com migrate
bench build --app instacertify
bench --site erp.yourdomain.com clear-cache
bench --site erp.yourdomain.com execute instacertify.setup.workspace_setup.ensure_workspaces
bench --site erp.yourdomain.com execute instacertify.setup.deploy_smoke.run

sudo supervisorctl restart all
```

Replace `erp.yourdomain.com` with your real site name (`ls sites` if unsure).

### Quick UI checks after deploy

1. Hard-refresh desk (**Ctrl+Shift+R**).  
2. **Instacertify Home** — greeting + explore tiles load.  
3. **Testing & Samples** — Manage TR: QR, TRF Link / PDF, Edit Price.  
4. **Laboratories** — scope + buying/selling prices.  
5. **Customer → Related Data** — testing / samples sections.  
6. **Quote Format Library** — Use opens a Quotation.  
7. **Team Calendar** — Event list opens.

---

## Option C — Deploy from a release tarball (no git on server)

Only if the VPS cannot reach GitHub:

1. On a machine with the repo:

```bash
git clone https://github.com/instacertify/erppronxt.git
cd erppronxt
git checkout main
tar czf instacertify-main.tar.gz \
  --exclude .git --exclude '__pycache__' --exclude '*.pyc' .
```

2. Upload to the VPS and extract so the **nested** app lands at `apps/instacertify/`
   (archive root should contain `instacertify/pyproject.toml`, then:
   `tar xzf instacertify-main.tar.gz -C /tmp && mv /tmp/instacertify ~/frappe-bench/apps/instacertify`).
3. Run `pip install -e ./apps/instacertify`, then the same `migrate` / `build` /
   `clear-cache` / `ensure_workspaces` / smoke / `supervisorctl restart` as in Option B.

---

## Hostinger firewall / ports

Allow inbound:

- **80** (HTTP → redirect to HTTPS)
- **443** (HTTPS)
- **22** (SSH) — restrict to your IP if possible

Do **not** expose MariaDB (`3306`) to the public internet.

---

## Backups before every update

```bash
cd ~/frappe-bench
bench --site erp.yourdomain.com backup --with-files
# Files: sites/erp.yourdomain.com/private/backups/
```

Download a copy off the VPS before `git pull` / migrate.

---

## Common issues

| Symptom | Fix |
|---------|-----|
| Blank desk / old JS | `bench build --app instacertify` then `clear-cache`; hard-refresh browser |
| Missing Home tiles | `ensure_workspaces` (see above) |
| 502 Bad Gateway | `sudo supervisorctl status` — restart `frappe-bench-web` / workers |
| SSL fail | DNS A record must point to this VPS before Let's Encrypt |
| App not found | Confirm `apps/instacertify/instacertify/hooks.py` exists and `instacertify` is in `sites/apps.txt` |
| `FileNotFoundError: .../erppronxt/setup.py` | Expected — do not use `bench get-app` on this repo. Clone to `~/src/erppronxt` and `ln -sfn ~/src/erppronxt/instacertify apps/instacertify` |
| `ls .../instacertify/instacertify/hooks.py` missing after `mv erppronxt instacertify` | You renamed the **repo** folder, not the app. Remove it and use the symlink install above |
| `No module named 'hrmsinstacertify'` | `sites/apps.txt` glued two app names (missing newline). Fix with the apps.txt rewrite block in §3, or edit so each app is on its own line |
| `requires-python` / pip errors | Use **Python 3.14+** for `bench init` |
| Smoke FAIL | Fix listed DocType/workspace gaps; re-run migrate + ensure_workspaces |

---

## Build identity (this release)

Deploy **`main`** at or after commit **`ea907ee`** (Sample QR Print / Download fix and prior TRF / Testing & Samples work).

Included on `main` for production:

- Manage TR: QR, Print, TRF Link / PDF, Edit TRF / Price  
- TRF fill-once + reopen; guest PDF  
- Generate page: editable buy/sell + currency  
- Sample QR 50×25 mm sticker print + PNG download  
- Customer Data Drive / Related Data  
- Quote Format Library, Document Collection, Lead capture  

Open draft PRs (favicon/orange brand, role profiles, etc.) are **not** on `main` until merged — deploy `main` only unless you intentionally merge those first.

---

## Deploy command cheat-sheet

```bash
# Update production to latest main
SITE=erp.yourdomain.com bash ~/frappe-bench/apps/instacertify/scripts/hostinger_update.sh

# Smoke only
bench --site erp.yourdomain.com execute instacertify.setup.deploy_smoke.run
```
