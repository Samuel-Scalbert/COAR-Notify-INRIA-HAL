# COAR-Notify-INRIA-HAL

## Quick Start (Docker Compose)

1. Copy `.env.example` to `.env` and adjust your secrets (recommended):
   ```sh
   cp .env.example .env
   ```
2. Build and start the stack:
   ```sh
   docker compose up --build
   ```
3. Access the services:
   - Flask app: http://localhost:5000
   - ArangoDB UI: http://localhost:8529 (login as `root` with the password from `.env`, default: `changeme`)

## Configuration

- The app loads `config.json` and then applies environment overrides. In containers (Compose), env variables take precedence.
- Inside Docker Compose networks, containers must use service names to talk to each other (e.g., `ARANGO_HOST=arangodb`), not `localhost`.
- Defaults now match Compose so it works out-of-the-box in containers:
  - `ARANGO_HOST=arangodb`
  - `ARANGO_PORT=8529`
  - `ARANGO_DB=COAR_NOTIFY_DB`
  - `ARANGO_USERNAME=root`
  - `ARANGO_PASSWORD=changeme`
  - `FLASK_PORT=5000`

### Running without Docker Compose (local dev)

If you run the app locally (e.g., `python run.py` or via a local virtualenv), set `ARANGO_HOST=localhost` in a `.env` file or environment variables, because `arangodb` is only resolvable inside Compose.

Example `.env` for local runs:
```
ARANGO_HOST=localhost
ARANGO_PORT=8529
ARANGO_USERNAME=root
ARANGO_ROOT_PASSWORD=changeme
ARANGO_DB=COAR_NOTIFY_DB
FLASK_PORT=5000
```

## Environment Variables

- `ARANGO_HOST`: Hostname for ArangoDB (Compose default: `arangodb`; local: `localhost`)
- `ARANGO_PORT`: Port for ArangoDB (default: `8529`)
- `ARANGO_ROOT_PASSWORD`: Root password for ArangoDB (default: `changeme`)
- `ARANGO_USERNAME`: Username for ArangoDB (default: `root`)
- `ARANGO_DB`: Database name (default: `COAR_NOTIFY_DB`)
- `FLASK_PORT`: Port for Flask app (default: `5000`)

## Notes
- The app waits for ArangoDB to be healthy before starting.
- DB initialization is idempotent across multiple Gunicorn workers.
- For production, change the default passwords, review Compose security, and consider externalizing secrets.

## API

### Base URL and reverse-proxy prefix
- Default base URL (local): `http://localhost:5000`
- If served behind NGINX under a prefix (e.g., `/coar`), prepend that prefix to all paths (e.g., `/coar/api/software/status`, `/coar/health`).

### Authentication
Some endpoints require an API key via the `x-api-key` header. The key is read from `auth_admin.json` (`TOKEN`).

Example header:
```
x-api-key: <your-token>
```

### Health
- GET `/health`
  - Returns service status and basic ArangoDB info.
  - 200 when up; 503 when down.

Example:
```sh
curl -s http://localhost:5000/health | jq
```

### General status (with auth)
- GET `/status`
  - Headers: `x-api-key`
  - Checks API access and database reachability; lists existence of key collections.

Example:
```sh
curl -s -H "x-api-key: $API_KEY" http://localhost:5000/status | jq
```

### Software endpoints
- GET `/api/software/status`
  - Returns a count of documents in the `software` collection.
- GET `/api/software/<id_software>`
  - Returns all software docs with the same normalized name as the given software `_key`.
- GET `/api/software_mention/<id_mention>`
  - Returns a single software mention document by `_key`.
- POST `/api/software`
  - Headers: `x-api-key`
  - Content-Type: `multipart/form-data` with a field `file` containing the JSON to insert.
  - Returns 201 on new insert, 409 if already exists. Triggers notification send attempt.

Examples:
```sh
curl -s http://localhost:5000/api/software/status | jq
curl -s http://localhost:5000/api/software/soft123 | jq
curl -s http://localhost:5000/api/software_mention/mention456 | jq
curl -s -X POST \
  -H "x-api-key: $API_KEY" \
  -F file=@/path/to/your.json \
  http://localhost:5000/api/software | jq
```

### Document endpoints
- GET `/api/documents/status`
  - Returns a count of documents in the `documents` collection.
- GET `/api/documents/<id>`
  - Returns the document with `_key = <id>`.
- GET `/api/documents/<id_document>/software`
  - Returns all software linked to a given document via `edge_doc_to_software`.
- GET `/api/documents/<id_document>/software/<id_software>`
  - Returns the software linked to the document matching the normalized name of `<id_software>`.

Examples:
```sh
curl -s http://localhost:5000/api/documents/status | jq
curl -s http://localhost:5000/api/documents/docABC | jq
curl -s http://localhost:5000/api/documents/docABC/software | jq
curl -s http://localhost:5000/api/documents/docABC/software/soft123 | jq
```

### COAR Notify inbox
- POST `/inbox`
  - Accepts a JSON-LD COAR notification payload.
  - Returns 202 with a minimal summary.
- GET `/notifications`
  - Renders an HTML page displaying received notifications (best-effort debugging/inspection).

Examples:
```sh
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d @notification.json \
  http://localhost:5000/inbox | jq

# View in browser:
# http://localhost:5000/notifications
```

## Notification

Relationship (in-progress)

## Inbox 

Waiting for notification
