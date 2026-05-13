# Glovebox

A simple vehicle tracker website (frontend + backend). Think of it like your digital glovebox where you keep all your maintenance history.

## Overview

- Backend: FastAPI + Beanie (MongoDB)
- Frontend: Vite + Vue 3
- Data: local Mongo files under `data/db`

## Requirements

- Python 3.11 or newer
- Node.js 16+ (for frontend)
- A running MongoDB instance (or local `data/db` files if configured)

## Quick start (backend)

1. Create and activate a virtualenv, then install requirements:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the API (from repo root):

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
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
