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

Software mentions' routes:
- /api/software/status
- /api/software/<id_software>
- /api/software_mention/<id_mention>

Documents' routes:
- /api/document/status
- /api/document/<id>
- /api/document/<id_document>/software
- /api/document/<id_document>/software/<id_software>


## Notification

Relationship (in-progress)

## Inbox 

Waiting for notification
