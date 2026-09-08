# Glovebox

A simple vehicle tracker website (frontend + backend). Think of it like your digital glovebox where you keep all your maintenance history.

## Overview

- Backend: FastAPI + Beanie (MongoDB)
- Frontend: Vite + Vue 3
- Data: persistent Docker volume by default, or an externally configured MongoDB instance

## Requirements

- Python 3.11 or newer
- Node.js 20.19+ or 22.12+ (for frontend)
- A running MongoDB instance

## Quick start (backend)

1. Create and activate a virtualenv, then install requirements:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Use the virtualenv interpreter when starting the API so Uvicorn loads the same packages you just installed.

2. Run the API (from repo root):

Set `MONGODB_URI=mongodb://localhost:27017` for a local MongoDB instance.
For network-accessible installs, configure `SETUP_TOKEN` and
`SETUP_TOKEN_REQUIRED=true` before starting the API.

```bash
.venv/bin/uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

3. Open the API docs: http://localhost:8000/docs

## Quick start (frontend)

1. Change into the frontend folder and install dependencies:

```bash
cd frontend
npm install
```

2. Start the dev server:

```bash
npm run dev
```

3. Open the frontend (http://localhost:5173)

## Tests

Run backend tests with pytest from the repo root:

```bash
pytest
```

Real-MongoDB tests use a separate `glovebox_test` database by default. Set
`TEST_DATABASE_NAME` to override it; never point it at your application database.

## Database migrations

MongoDB preserves existing documents when the backend is updated. On startup,
Glovebox backfills missing fields that have a model default, without replacing
an existing value. For example, add an optional car field with a default:

```python
nickname: str | None = None
```

The next backend startup adds `nickname: null` to existing car documents. A
new required field or a data transformation needs an explicit migration before
deployment; do not use a default to invent data that is not known.

## Docker data

### Reminders and notifications

The vehicle dashboard has **Overview** and **Reminders** tabs. Only configured
reminders appear in the Reminders tab. Time and mileage progress are shown
separately; reaching either deadline makes a reminder due, and passing either
deadline makes it overdue (red). Mileage alerts depend on the latest odometer
reading entered in Glovebox, not live vehicle telemetry. Date checks use the
server's current date (UTC in the supplied container).

Open **Settings** from the account menu to configure oil-change defaults and
optional custom HTTPS webhook, Discord webhook, or email destinations. New oil
changes default to **5,000 miles / 6 months**, whichever comes first. Explicit
intervals override defaults; clearing both disables the reminder. Defaults apply
to new manual oil-change entries, not historical imports or existing records.
The newest oil-change entry supersedes older oil reminders for the same car.
For other services, clear an old reminder when it is no longer applicable.

Home shows due services for your own cars and shared cars for which you can view
maintenance. Persistent bell notifications and external deliveries go to the
vehicle owner only. The background worker checks on startup and periodically
(`REMINDER_CHECK_SECONDS`, default 60) while the API is running; no browser needs
to be open. The bell refreshes every 60 seconds. Keep at least one API instance
running with `REMINDER_WORKER_ENABLED=true`.

Notifications are deduplicated per service and deadline. Marking one read does
not resend it. Removing a reminder, recording a newer oil change, or deleting its
car removes that alert from the current notification feed and cancels pending
delivery. Destinations enabled when an alert is created are queued; adding a
destination later does not resend past alerts. Pending deliveries use the current
configured destination and stop if it is cleared.

Custom webhooks receive JSON `{ "title": "...", "message": "..." }`. Discord
webhooks receive a text message with mentions disabled. Only public HTTPS
destinations on port 443 are supported: private addresses, credentials in URLs,
and redirects are blocked. DNS addresses are validated and pinned for connection
to prevent access to internal services. Treat webhook URLs as secrets; they are
stored in your database and visible only through your authenticated settings.

Email requires operator-provided `SMTP_HOST`, `SMTP_PORT` (default 587),
`SMTP_FROM`, and, if required, `SMTP_USERNAME` / `SMTP_PASSWORD`. STARTTLS is on
by default; only disable it for a trusted local relay. Email entry is unavailable
in the UI until a host and sender are configured. The bundled client uses SMTP
with STARTTLS, not implicit TLS on port 465. SMTP credentials never go to the
browser.

Failed external deliveries retry with backoff up to five attempts, independently
of successful in-app notifications. Generic delivery failures are logged without
destination URLs or credentials. Database leases coordinate multiple workers;
external delivery is at-least-once, so a process crash after a successful send but
before recording success can produce a duplicate. Network delivery should be
verified with your own endpoints and SMTP provider before relying on alerts.

### Production deployment

1. Copy `.env.example` to `.env`, generate a secret with `openssl rand -hex 32`,
   and set `SETUP_TOKEN` to that value. Keep `.env` private and out of Git.
2. Back up the database before upgrading an existing installation.
3. Run `docker compose up -d --build`.
4. Open `http://localhost:5173`. Enter the setup token, choose an administrator
   username and password, then add a car or select **Skip for now**.
5. For remote access, put an HTTPS reverse proxy in front of
   `127.0.0.1:5173`. Do not send passwords or session tokens over public HTTP.

Compose serves built assets with Nginx and forwards `/api/` to the backend.
Only the frontend is published, on loopback; MongoDB and the API remain on the
internal Docker network. Do not publish their ports to the internet. The
setup token must remain configured on container restarts, but setup is closed
after the first administrator is created. Restrict access during upgrades.

The first administrator receives any existing ownerless vehicles. Each account
has a private garage; administrators manage accounts, not other users' car pages.
Use **Users** to create accounts, reset passwords, or delete users and their
garage data. There is no public registration. Users can change their own
password from **Account**. Administrator accounts cannot be deleted.

Sessions are opaque bearer tokens held in browser `sessionStorage`, so closing
the tab ends browser persistence. Logout revokes the current token; password
resets revoke all target-user sessions. Password changes retain only the current
session. New passwords preserve whitespace and support 4-128 characters.

Login throttling is process-local. Multi-worker or public deployments should
also enforce rate limits at the trusted HTTPS ingress. If that ingress is
another proxy, configure trusted client-IP forwarding deliberately rather than
trusting arbitrary incoming `X-Forwarded-For` headers. The bundled Nginx limits
request bodies to 11 MB; PDF uploads retain the application's 10 MB file limit.
Database backups and HTTPS certificate management remain operator responsibilities.

Run frontend checks from `frontend` with `npm test -- --run` and `npm run build`.

Docker Compose stores MongoDB data in the persistent `glovebox-mongodb-data`
volume. `docker compose down` and `docker compose up -d` preserve it. Do not
run `docker compose down -v` unless you intentionally want to permanently
delete all local database data.
