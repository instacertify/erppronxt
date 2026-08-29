# Deploy Instacertify (ERPNext) on Hostinger

This build is a **Frappe / ERPNext** app (`instacertify`). It needs a **Linux VPS** (Hostinger **KVM VPS** or Cloud VPS), **not** shared Web Hosting / hPanel PHP hosting.

**Repo:** `https://github.com/instacertify/erppronxt`  
**Branch to deploy:** `main` (all feature PRs are merged here)

---

## What you need on Hostinger

| Item | Recommendation |
|------|----------------|
| Plan | Hostinger **VPS** (Ubuntu 22.04 or 24.04) |
| RAM | 4 GB minimum (8 GB preferred) |
| Disk | 40 GB+ SSD |
| Access | Root SSH |
| Domain | Point A record to the VPS public IP |

Shared hosting, WordPress, or “upload ZIP to public_html” will **not** run this stack.

---

## Option A — Fresh VPS (first production install)

### 1. Create the VPS

1. Hostinger → **VPS** → create Ubuntu 22.04/24.04.
2. Note the **IP**, **root password** (or SSH key).
3. In DNS (Hostinger Domains): set `A` record for your site (e.g. `erp.yourdomain.com`) → VPS IP. Wait for DNS.

### 2. SSH in and prepare the server

```bash
ssh root@YOUR_VPS_IP
apt update && apt upgrade -y
apt install -y git python3-dev python3-pip python3-venv redis-server \
  mariadb-server nginx supervisor curl software-properties-common \
  libffi-dev libssl-dev wkhtmltopdf xvfb fontconfig libxrender1
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

# New bench (match ERPNext 16)
bench init --frappe-branch version-16 frappe-bench
cd frappe-bench

bench get-app erpnext --branch version-16
bench get-app https://github.com/resilient-tech/india-compliance --branch version-16
bench get-app hrms --branch version-16
bench get-app gameplan --branch develop

# Instacertify app (this repo)
bench get-app https://github.com/instacertify/erppronxt.git --branch main
# The app folder name on disk is typically "erppronxt" or "instacertify"
# depending on the repo layout. Ensure the Python package `instacertify` is
# under apps/<app>/instacertify. If the clone folder is erppronxt:
#   ln -s erppronxt instacertify   # only if needed for naming
```

If `get-app` clones as `erppronxt` but hooks expect the app name `instacertify`, rename or set the app path so `apps/instacertify/instacertify/hooks.py` exists:

```bash
# Example when clone directory is erppronxt:
cd apps
mv erppronxt instacertify   # only if hooks.py lives at instacertify/instacertify/hooks.py
cd ..
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
```

Restore Instacertify workspaces if migrate removes orphans:

```bash
bench --site erp.yourdomain.com execute instacertify.setup.workspace_setup.ensure_workspaces
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

## Option B — Update an existing Hostinger bench (most common after this merge)

When production already has ERPNext + Instacertify and you only need the **latest `main` build**:

```bash
ssh frappe@YOUR_VPS_IP
cd ~/frappe-bench

# Pull latest Instacertify
cd apps/instacertify
git fetch origin
git checkout main
git pull origin main
cd ../..

bench --site erp.yourdomain.com migrate
bench build --app instacertify
bench --site erp.yourdomain.com clear-cache
bench --site erp.yourdomain.com execute instacertify.setup.workspace_setup.ensure_workspaces

sudo supervisorctl restart all
```

Replace `erp.yourdomain.com` with your real site name (`bench --site all list` if unsure).

### Quick health checks after deploy

1. Desk → **Laboratories** — list loads; open any lab → scope / buying & selling prices visible.  
2. **Testing Request** — Product | Test side-by-side; **Compare Labs** / Lab Offer works.  
3. **Quote Format Library** — Use opens a new Quotation (no “Not found”).  
4. **Samples** — Label / 50×25 mm sticker actions present.  
5. **Customer → Data Drive** — Share Report + 8-digit code.

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

2. Upload to the VPS (`scp` / SFTP) into `~/frappe-bench/apps/`.
3. Extract over `apps/instacertify/`, then run the same `migrate` / `build` / `clear-cache` / `ensure_workspaces` / `supervisorctl restart` as in Option B.

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
# Files land under sites/erp.yourdomain.com/private/backups/
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
| App not found | Confirm `apps/instacertify/instacertify/hooks.py` exists and app is in `sites/apps.txt` |

---

## Build identity (this release)

Deploy **`main`** at or after:

- Sample report upload, report share + 8-digit code  
- Laboratories upload / editable fields  
- Testing Request Product \| Test + lab buying-rate picker  
- Sample QR sticker 50×25 mm  
- Quote Format Library Use fix, Document Collection Library, Lead full-width  

Only open PR left historically: **#60** (8mm sticker) — superseded by the 50×25 mm sticker on `main`; safe to ignore or close.
