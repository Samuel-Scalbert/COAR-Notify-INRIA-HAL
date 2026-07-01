# Configuration & Setup

[← Back to README](../README.md)

## Quick Start

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

- The app reads all configuration from environment variables, loaded from a `.env` file via `python-dotenv` (see `.env.example`). In containers (Compose), env variables provided by the orchestrator take precedence.
- Inside Docker Compose networks, containers must use service names to talk to each other (e.g., `ARANGO_HOST=arangodb`), not `localhost`.
- Defaults now match Compose so it works out-of-the-box in containers:
    - `ARANGO_HOST=arangodb`
    - `ARANGO_PORT=8529`
    - `ARANGO_DB=COAR_NOTIFY_DB`
    - `ARANGO_USERNAME=root`
    - `ARANGO_PASSWORD=changeme`
    - `FLASK_PORT=5000`

### Running without Docker Compose (local dev)

If you run the app locally (e.g., `python run.py` or via a local virtualenv), set `ARANGO_HOST=localhost` in a `.env`
file or environment variables, because `arangodb` is only resolvable inside Compose.

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
- `HAL_NOTIFICATION_FILTER`: Which software mentions are sent to HAL (default: `all`); see
  [Notification Filtering](notifications.md#notification-filtering)
- `SWH_NOTIFICATION_FILTER`: Which software mentions are sent to Software Heritage (default: `all`); see
  [Notification Filtering](notifications.md#notification-filtering)
- `MENTION_QUALITY_FILTER_ENABLED`: Enable the Mention Quality Filter (default: `false`); see
  [Mention Quality Filter](mention-quality-filter.md)
- `MENTION_QUALITY_FILTER_THRESHOLD`: Minimum `quality_score` (P(valid)) for a name to count as valid (default: `0.4`)
  - The previous names `MODEL_FILTER_ENABLED` / `MODEL_FILTER_THRESHOLD` are deprecated but still honored as a
    fallback (a one-time deprecation warning is logged when they are used).

For the database schema, collections, and indexes, see the
[Database Schema Documentation](database.md).
