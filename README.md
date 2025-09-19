# COAR-Notify-INRIA-HAL

## Quick Start (Docker Compose)

1. Copy `.env` to configure your environment (or use the defaults):
   ```sh
   cp .env .env.local  # (optional, edit as needed)
   ```
2. Build and start the stack:
   ```sh
   docker compose up --build
   ```
3. Access the services:
   - Flask app: http://localhost:5000
   - ArangoDB UI: http://localhost:8529 (login as `root` with the password from `.env`)

## Configuration

- All configuration for ArangoDB and the Flask app is managed via environment variables (see `.env`).
- You can override any value in `.env` by setting an environment variable directly.
- The app will fall back to `config.json` only if an environment variable is not set.

## Environment Variables

- `ARANGO_HOST`: Hostname for ArangoDB (default: arangodb)
- `ARANGO_PORT`: Port for ArangoDB (default: 8529)
- `ARANGO_ROOT_PASSWORD`: Root password for ArangoDB (default: examplepassword)
- `ARANGO_USERNAME`: Username for ArangoDB (default: root)
- `ARANGO_DB`: Database name (default: test)
- `FLASK_PORT`: Port for Flask app (default: 5000)

## Notes
- The app will wait for ArangoDB to be healthy before starting.
- You can customize the stack by editing `.env` and `docker-compose.yml`.
- For production, be sure to change the default passwords and review security settings.

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
