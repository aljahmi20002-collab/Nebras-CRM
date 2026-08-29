# NebrasCRM

NebrasCRM is a self-hosted CRM application for sales, customer support, invoices, partner management, and internal reporting. The interface supports Arabic (RTL) and English. The backend is FastAPI; the frontend is plain HTML, CSS, and JavaScript.

SQLite is the default database for a local installation. MariaDB, MySQL, and PostgreSQL are available when the application is deployed against a network database server.

## Quick start

```bash
cd crm
./run.sh
```

The application starts on:

```text
http://localhost:8008/app
```

API documentation is available at:

```text
http://localhost:8008/docs
```

If you do not use the helper script:

```bash
python3 -m pip install -r requirements.txt
python3 -m uvicorn main:app --host 0.0.0.0 --port 8008
```

On Windows, use the included launcher from Command Prompt or PowerShell:

```bat
cd crm
run.bat
:: Optional custom port
run.bat 9000
```

`run.bat` detects Python, installs missing requirements, initializes a missing SQLite database, and starts the server on port `8008` by default. Use `python3` for manual commands; Windows installations that only provide the Python launcher may use `py` instead.

For a native local MariaDB service on Windows (not Docker), create the private batch configuration and use the dedicated launcher:

```bat
copy .env.mariadb.local.bat.example .env.mariadb.local.bat
notepad .env.mariadb.local.bat
run-mariadb-local.bat
```

In Command Prompt, environment assignments must use `set`, not Unix syntax such as `CRM_DB_ENGINE=mariadb ./run.sh`:

```bat
set "CRM_DB_ENGINE=mariadb"
set "CRM_DB_HOST=127.0.0.1"
set "CRM_DB_PORT=3306"
set "CRM_DB_NAME=nebrascrm"
set "CRM_DB_USER=nebrascrm"
set "CRM_DB_PASSWORD=your-password"
run.bat
```

On Linux, `./run.sh` creates and uses a local `.venv` automatically. This avoids PEP 668 errors on OS-managed Python installations; do **not** use `--break-system-packages` for NebrasCRM.

## Docker Compose — MySQL 8.4 complete stack

The included `docker-compose.yml` runs the complete NebrasCRM application with the official **MySQL 8.4 LTS** image. The database is private to the Compose network; only the application is published on port `8008`.

On Linux, this one command creates a private `.env.docker` with random database passwords, CRM secrets, and a first-admin password; it then builds and starts the stack:

```bash
bash ./compose-up.sh
```

On Windows, `compose-up.bat` does the same when `python3` is available:

```bat
compose-up.bat
```

If Windows does not have `python3`, it creates `.env.docker` from the template instead. Replace every `replace-with-...` value before running it again:

```bat
notepad .env.docker
compose-up.bat
```

A fresh MySQL volume has no predictable demo account. The application creates the initial administrator once from these private `.env.docker` values:

```env
CRM_BOOTSTRAP_ADMIN_EMAIL=admin@nebrascrm.local
CRM_BOOTSTRAP_ADMIN_PASSWORD=...generated-or-your-strong-password...
```

The bootstrap password is used only while the `users` table is empty; changing it later does **not** reset an existing administrator password. Sign in with that email and password, then use **System Settings → Add demo data** if you want sample business records.

### Complete MySQL 8 setup and verification

Use the dedicated idempotent provisioner when you need to prepare or repair the Docker database account, CRM schema, and first administrator. It starts MySQL, waits for its health check, synchronizes `MYSQL_DATABASE` and `MYSQL_USER` permissions with `.env.docker`, starts the app, and prints the CRM user list without passwords:

```bash
python3 setup_mysql8.py
# or: bash ./setup-mysql8.sh
```

On Windows:

```bat
setup-mysql8.bat
```

To intentionally delete only the Docker MySQL volume and build a clean test instance, add `--reset-data`:

```bash
python3 setup_mysql8.py --reset-data
```

### MySQL 8 SQL compatibility

All application queries pass through `db.py` when `CRM_DB_ENGINE=mysql`. The MySQL 8 dialect converts qmark parameters, SQLite DDL, `date('now')`, `CAST(... AS INTEGER)`, index creation, and SQLite UPSERTs. MySQL 8 UPSERTs use row aliases (`AS new_row`) instead of deprecated `VALUES(column)` syntax; MariaDB retains its compatible legacy form. Queries no longer use SQLite-only `COLLATE NOCASE` or ordinal/alias `GROUP BY` expressions that can be fragile with `ONLY_FULL_GROUP_BY`.

For a source-level schema audit without a database server:

```bash
python3 mysql8_schema_audit.py
```

For a manual start, always pass the same environment file. Docker Compose substitutes `${...}` before it reads a service `env_file`, so a bare `docker compose up` does not satisfy variables such as `MYSQL_PASSWORD`:

```bash
docker compose --env-file .env.docker -f docker-compose.yml up -d --build
```

Useful operations:

```bash
docker compose --env-file .env.docker -f docker-compose.yml ps
docker compose --env-file .env.docker -f docker-compose.yml logs -f app
docker compose --env-file .env.docker -f docker-compose.yml down
```

For disposable test data only, rebuild a completely fresh MySQL volume:

```bash
bash ./compose-up.sh --reset-data
# Windows: compose-up.bat --reset-data
```

The reset deletes the Compose MySQL volume only; it does not delete source files or a host SQLite `crm.db` file.

## Demo accounts

| Role | Email | Password |
|---|---|---|
| System administrator | `admin@nebrascrm.io` | `admin123` |
| Sales manager | `manager@nebrascrm.io` | `manager123` |
| Sales representative | `sara@nebrascrm.io` | `sara123` |
| Read-only user | `viewer@nebrascrm.io` | `viewer123` |

The partner portal is available at `/agent`, and the customer portal at `/portal`.

## Main areas

The application includes the following business areas:

- Leads, accounts, contacts, opportunities, deals, activities, and campaigns
- Support tickets and customer portal conversations
- Products, quotes, invoices, payments, vendors, a full point of sale, and CSV import/export
- POS checkout with a product catalogue, cart, customer lookup, cash shifts, stock control, invoices, payment ledger entries, refunds, and 80 mm printable receipts
- Printable invoices, quotations, and payment vouchers with customer details, item rows, quantities, unit prices, discounts, tax, totals, and balances
- A print action for each CRM record, filtered module matrix, payment matrix, report, and the current system page
- Partners, commissions, territories, consigned stock, and partner portal access
- Customer segments, loyalty rules, stale inventory and inactive customer reports
- Competitor tracking, market research, and comparison reports
- Email templates, outbox, SMTP or Resend delivery settings, notifications, audit history, and workflows
- Public API keys, inbound web hooks, saved dashboards, and custom fields

The AI tools run locally against CRM data. They cover lead scoring, deal probability, sales forecasting, next actions, churn signals, email drafts, meeting summaries, and a daily work digest. An optional LLM key can be added for free-text generation only.

## Point of sale

Open **Point of Sale** from the staff navigation. A completed checkout creates a normal paid invoice and payment record, saves item rows, reduces stock, and offers an 80 mm receipt printout. Cashiers can open and close shifts; administrators can require an open shift or allow negative stock from **System Settings**.

## Email delivery with Resend

Open **Email → Delivery settings**, select **Resend**, and enter a Resend API key plus a verified From address. The key is masked in the UI and APIs after saving. Resend, SMTP, and sandbox delivery all use the same templates and outbox.

For a production deployment, the Resend key can also be supplied outside the database:

```bash
CRM_RESEND_API_KEY='re_...'
```

When using Resend, verify the sending domain and From address in the Resend dashboard first.

## Database options

### SQLite

SQLite is used when `CRM_DB_ENGINE` is not set or is set to `sqlite`.

```bash
CRM_DB_ENGINE=sqlite
CRM_DB_PATH=/var/lib/nebrascrm/crm.db   # optional
./run.sh
```

The bundled `crm.db` contains demonstration data. A new SQLite database is initialized automatically by `run.sh` when the selected file does not exist.

### MariaDB

For a server database, configure these environment variables:

```bash
CRM_DB_ENGINE=mariadb
CRM_DB_HOST=127.0.0.1
CRM_DB_PORT=3306
CRM_DB_NAME=nebrascrm
CRM_DB_USER=nebrascrm
CRM_DB_PASSWORD='use-a-strong-password'
CRM_DB_CHARSET=utf8mb4
```

The MariaDB schema is created on first application startup.

If startup says it cannot connect to `127.0.0.1:3306/nebrascrm`, MariaDB is not running there or one of the `CRM_DB_*` values is incorrect. The launcher stops before starting the web server and prints the configured endpoint. To return to the local SQLite database:

```bash
unset CRM_DB_ENGINE CRM_DB_HOST CRM_DB_PORT CRM_DB_NAME CRM_DB_USER CRM_DB_PASSWORD
CRM_DB_ENGINE=sqlite ./run.sh
```

#### Local MariaDB with Docker

```bash
cp .env.mariadb.example .env.mariadb
# Edit .env.mariadb and set strong passwords.
./setup-mariadb.sh
```

#### Native MariaDB service (no Docker)

On Debian or Ubuntu, install and start the native service:

```bash
sudo apt update
sudo apt install mariadb-server
sudo systemctl enable --now mariadb
```

Create the database and a loopback-only application account. Replace the password before running this block:

```bash
sudo mariadb <<'SQL'
CREATE DATABASE nebrascrm CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'nebrascrm'@'localhost' IDENTIFIED BY 'replace-with-a-strong-password';
CREATE USER 'nebrascrm'@'127.0.0.1' IDENTIFIED BY 'replace-with-a-strong-password';
GRANT ALL PRIVILEGES ON nebrascrm.* TO 'nebrascrm'@'localhost';
GRANT ALL PRIVILEGES ON nebrascrm.* TO 'nebrascrm'@'127.0.0.1';
FLUSH PRIVILEGES;
SQL
```

Create the private local connection file once, then use the dedicated one-command launcher every day:

```bash
cp .env.mariadb.local.example .env.mariadb.local
# Edit the password to match the SQL account, then protect the file.
chmod 600 .env.mariadb.local

# Starts the native MariaDB service when needed, verifies it, and starts NebrasCRM.
./run-mariadb-local.sh
```

The launcher also creates `.env.mariadb.local` from its template when it is missing, then asks you to fill in the password once.

To seed an empty MariaDB instance with the demo records:

```bash
SEED_DEMO=1 CRM_DB_ENGINE=mariadb ./run.sh
```

#### Migrating an existing SQLite installation to MariaDB

Take a backup first. Then configure MariaDB and run:

```bash
CRM_DB_ENGINE=mariadb python3 migrate_mariadb.py --source crm.db --replace
```

The migration copies application data and configuration. Global geographic data is initialized from the bundled GeoNames files rather than copied from SQLite.

### MySQL

MySQL 8+ is supported through the same PyMySQL-compatible dialect used for MariaDB. Use the explicit engine value:

```bash
CRM_DB_ENGINE=mysql
CRM_DB_HOST=127.0.0.1
CRM_DB_PORT=3306
CRM_DB_NAME=nebrascrm
CRM_DB_USER=nebrascrm
CRM_DB_PASSWORD='use-a-strong-password'
CRM_DB_CHARSET=utf8mb4
```

For the everyday one-command local launcher, prepare the private file once and then run only the launcher:

```bash
cp .env.mysql.local.example .env.mysql.local
# Edit CRM_DB_PASSWORD once to match the local MySQL account.
chmod 600 .env.mysql.local
./run-mysql.sh
```

`run-mysql.sh` loads the local configuration, attempts to start the common native `mysql` or `mariadb` service, verifies the connection, and starts NebrasCRM. A current `.env.mariadb.local` installation also works with this launcher.

On Windows, copy `.env.mysql.local.bat.example` to `.env.mysql.local.bat`, set the password, then double-click or run:

```bat
run-mysql.bat
```

For first-time MySQL setup, create the database and local application user with an administrator account:

```sql
CREATE DATABASE nebrascrm CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'nebrascrm'@'localhost' IDENTIFIED BY 'replace-with-a-strong-password';
CREATE USER 'nebrascrm'@'127.0.0.1' IDENTIFIED BY 'replace-with-a-strong-password';
GRANT ALL PRIVILEGES ON nebrascrm.* TO 'nebrascrm'@'localhost';
GRANT ALL PRIVILEGES ON nebrascrm.* TO 'nebrascrm'@'127.0.0.1';
FLUSH PRIVILEGES;
```

To migrate an existing SQLite installation into MySQL, use the MySQL-compatible migration helper:

```bash
CRM_DB_ENGINE=mysql python3 migrate_mariadb.py --source crm.db --replace
```

### PostgreSQL

Configure a PostgreSQL server with:

```bash
CRM_DB_ENGINE=postgresql
CRM_DB_HOST=127.0.0.1
CRM_DB_PORT=5432
CRM_DB_NAME=nebrascrm
CRM_DB_USER=nebrascrm
CRM_DB_PASSWORD='use-a-strong-password'
CRM_DB_SSLMODE=prefer
```

The schema is initialized on first startup. The `postgres` engine alias is also accepted, but `postgresql` is preferred in configuration and documentation.

#### Native PostgreSQL service (no Docker)

On Debian or Ubuntu, install and start PostgreSQL:

```bash
sudo apt update
sudo apt install postgresql
sudo systemctl enable --now postgresql
```

Create an application user and database. Replace the password before running:

```bash
sudo -u postgres psql <<'SQL'
CREATE ROLE nebrascrm LOGIN PASSWORD 'replace-with-a-strong-password';
CREATE DATABASE nebrascrm OWNER nebrascrm ENCODING 'UTF8';
SQL
```

Create a private connection file and run the native launcher:

```bash
cp .env.postgresql.local.example .env.postgresql.local
# Edit the password to match the PostgreSQL role, then protect the file.
chmod 600 .env.postgresql.local
./run-postgresql-local.sh
```

Windows users can copy `.env.postgresql.local.bat.example` to `.env.postgresql.local.bat` and run `run-postgresql-local.bat` after starting their native PostgreSQL service.

#### Local PostgreSQL with Docker

```bash
cp .env.postgresql.example .env.postgresql
# Edit .env.postgresql and set matching strong passwords.
./setup-postgresql.sh
```

#### Migrating an existing SQLite installation to PostgreSQL

```bash
CRM_DB_ENGINE=postgresql python3 migrate_postgresql.py --source crm.db --replace
```

## Global geography

The administrative map uses a bundled GeoNames dataset and does not require a geocoding service at runtime.

| Data | Included coverage |
|---|---:|
| Countries and territories | 252 |
| First-level regions / states | 3,865 |
| Cities and localities | 235,000+ |
| Neighborhoods and streets | Managed inside NebrasCRM |

The city dataset is based on GeoNames `cities500`: cities with population of at least 500 and administrative seats. Source files and checksums are stored under `data/geonames/`. GeoNames data is available under CC BY 4.0.

A previous Yemen-only location hierarchy is migrated automatically. Old location references are cleared because their IDs have a different meaning in the global dataset; customer, partner, and sales records remain intact.

## Demonstration data

At the bottom of **System Settings**, system administrators have two separate controls:

- **Add demo data** adds a compact, idempotent sample pack with products, customers, leads, deals, quotes, invoices, payments, and a POS sale. It requires:

  ```text
  ADD DEMO DATA
  ```

  The sample pack does not overwrite existing business records or change users, settings, or global geography.

- **Delete demo data** removes business records such as customers, deals, invoices, payments, activities, sample partners, POS activity, and related records. It requires:

  ```text
  DELETE DEMO DATA
  ```

  It keeps users, system settings, email templates, workflows, dashboards, custom fields, API keys, integrations, and global geography.

Deletion is intentionally destructive. Do not use it on a production database containing real operating data.

## Building desktop and mobile applications

### Desktop

```bash
./build-desktop.sh linux
./build-desktop.sh win
./build-desktop.sh mac
./build-desktop.sh run
```

The Windows build produces installer and portable artifacts under `dist/`. Build scripts require Node.js 18+ and Python with Pillow. On Windows, run the `.sh` scripts from Git Bash or WSL.

The desktop shell connects to `http://localhost:8008` by default. Make sure the FastAPI server is running before opening it.

### Android

```bash
./build-mobile.sh debug
./build-mobile.sh release
./build-mobile.sh sync
./build-mobile.sh run
```

Android builds require Node.js 18+, JDK 17+, Android SDK API 34, and build tools 34. The release script creates a local test signing key when none exists. For a store release, provide your own key and set:

```bash
NEBRAS_STORE_PASS='...'
NEBRAS_KEY_PASS='...'
NEBRAS_KEY_ALIAS='mykey'
```

The local signing properties file is excluded from Git. Read `BUILD.md` before publishing to Google Play.

## Security and deployment notes

For a production installation, use a separate environment file and set the application secrets before starting the server:

```bash
CRM_ENV=production
CRM_SECRET='at-least-32-characters'
CRM_PORTAL_SECRET='different-secret'
CRM_AGENT_PORTAL_SECRET='different-secret'
CRM_WEBHOOK_SECRET='different-secret'
CRM_CORS_ORIGINS='https://crm.example.com'
# Optional: use this instead of storing a Resend key in the database
CRM_RESEND_API_KEY='re_...'
```

New passwords use salted PBKDF2-SHA256 records. Older demo password records are upgraded when the user signs in successfully. Session tokens are signed and expire by default after eight hours.

Before accepting real payments, replace the bundled mock payment flow with a provider-hosted checkout page and use HTTPS. Do not process real card data directly on this server.

## Project layout

```text
crm/
├── main.py                 FastAPI application and generic CRM API
├── db.py                   SQLite / MariaDB / MySQL / PostgreSQL database layer
├── schema.py               Module and field definitions
├── geo.py                  Global country, region, and city data
├── payments.py             Payment links, web hooks, and reconciliation
├── portal.py               Customer portal
├── agentportal.py          Partner portal
├── static/                 Browser application
├── desktop/                Electron desktop shell
├── mobile/                 Capacitor Android project
├── Dockerfile              Application image for Docker Compose
├── docker-compose.yml      Complete NebrasCRM + MySQL stack
├── compose-up.sh/.bat      One-command Docker Compose launchers
├── setup_mysql8.py         MySQL 8 database/account/schema provisioner
├── setup-mysql8.sh/.bat    Cross-platform launchers for the provisioner
├── mysql8_schema_audit.py  Offline MySQL 8 schema SQL audit
├── data/geonames/          Bundled geographic source data
├── migrate_mariadb.py      SQLite to MariaDB migration helper
├── migrate_postgresql.py   SQLite to PostgreSQL migration helper
├── run-*-local.sh/.bat     Native MariaDB / PostgreSQL launchers
├── run-mysql.sh/.bat       One-command MySQL / MariaDB launchers
└── tests/                  Regression and smoke tests
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```

The test suite uses a temporary database copy. It covers authentication, row-level permissions, payments, demo-data cleanup, geography, and MySQL/MariaDB/PostgreSQL SQL translation.

## Further documentation

- `DOCS.md` — day-to-day operations and permissions
- `BUILD.md` — desktop and mobile builds
- `APPS.md` — desktop, mobile, and PWA notes
- `docs/01-SYSTEM.md` — architecture and deployment notes
- `docs/02-USER-GUIDE.md` — user guide
- `docs/03-DEVELOPER.md` — extension and API notes
- `docs/04-REPORTS.md` — report reference
- `docs/05-API.md` — API reference
