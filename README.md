# Glovebox

A simple vehicle tracker website (frontend + backend). Think of it like your digital glovebox where you keep all your maintenance history.

## Overview

- Backend: FastAPI + Beanie (MongoDB)
- Frontend: Vite + Vue 3
- Data: persistent Docker volume by default, or an externally configured MongoDB instance

## Requirements

- Python 3.11 or newer
- Node.js 16+ (for frontend)
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

Docker Compose stores MongoDB data in the persistent `glovebox-mongodb-data`
volume. `docker compose down` and `docker compose up -d` preserve it. Do not
run `docker compose down -v` unless you intentionally want to permanently
delete all local database data.
