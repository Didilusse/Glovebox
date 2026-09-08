# Glovebox

Glovebox is a vehicle tracker for keeping maintenance history, reminders, and
shared vehicle information in one place.

## Stack

- Backend: FastAPI, Beanie, and MongoDB
- Frontend: Vue 3 and Vite
- Deployment: Docker Compose with persistent MongoDB storage

## Local Development

Requirements: Python 3.11+, Node.js 20.19+ or 22.12+, and MongoDB.

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
MONGODB_URI=mongodb://localhost:27017 \
DATABASE_NAME=glovebox \
.venv/bin/uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API is available at `http://localhost:8000`. API docs are at
`http://localhost:8000/docs` when `API_DOCS_ENABLED=true`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Set `VITE_API_BASE_URL` if the API is not running
at `http://localhost:8000`.

## Docker Deployment

1. Copy `.env.example` to `.env`.
2. Generate a setup token:

   ```bash
   openssl rand -hex 32
   ```

3. Put the token in `.env` as `SETUP_TOKEN`, keep
   `HTTP_BIND_ADDRESS=127.0.0.1`, and restrict the file:

   ```bash
   chmod 600 .env
   ```

4. Validate and start the stack:

   ```bash
   docker compose config --quiet
   docker compose up -d --build --wait
   ```

5. Open `http://127.0.0.1:5173`, enter the setup token, and create the first
   administrator.

The frontend serves the built application and proxies `/api/` to the backend
over HTTP. The backend and MongoDB ports are not published to the host.
MongoDB has no database-level credentials in this stack; it is isolated on an
internal Docker network. Configure an external trusted edge and TLS before
binding the frontend beyond localhost.

The setup token is required at production startup and setup closes after the
first administrator is created. Keep it configured for future restarts.

## Data and Migrations

MongoDB data is stored in the persistent `glovebox-mongodb-data` volume.
`docker compose down` preserves it. Do not use `docker compose down -v` unless
you intend to delete the database.

On startup, the backend backfills missing fields that have model defaults.
Required fields and data transformations need an explicit migration before
deployment. Back up MongoDB and test restores regularly.

## Reminders and Notifications

Reminders can be based on time, mileage, or either deadline. The background
worker checks them periodically while the API is running; configure
`REMINDER_WORKER_ENABLED` and `REMINDER_CHECK_SECONDS` in `.env`.

Optional email and webhook notifications are configured through the account
settings and operator-provided SMTP variables. Webhook URLs should be treated
as secrets. Delivery retries up to five times and is at-least-once.

## Accounts

There is no public registration. The first administrator can create accounts,
reset passwords, and manage users. Each account has a private garage, and
sharing grants other users limited vehicle access.

## Tests

From the repository root:

```bash
.venv/bin/pytest -q backend/tests
```

From `frontend`:

```bash
npm test -- --run
npm run build
```

Real MongoDB tests use the separate `glovebox_test` database by default. Set
`TEST_DATABASE_NAME` to override it, but never point it at the application
database.

## Deployment Workflow

The GitHub Actions deployment runs after CI succeeds on `main`, deploys the
tested revision, preserves the server's `.env`, waits for container health, and
checks both frontend and API health. Configure the `production` environment
with `SSH_PRIVATE_KEY`, `SSH_KNOWN_HOSTS`, `SERVER_HOST`, and `SERVER_USER`.
