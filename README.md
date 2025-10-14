# COAR-Notify-INRIA-HAL

This project implements the COAR notify specification for the INRIA HAL repository for extraction of software mentions from research papers.

## Table of Contents
- [Overview](#overview)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Environment Variables](#environment-variables)
- [Database Schema](#database-schema)
- [API Documentation](#api-documentation)
  - [Authentication](#authentication)
  - [Health Endpoints](#health-endpoints)
  - [Document Management](#document-management)
  - [Software Endpoints](#software-endpoints)
  - [Blacklist Management](#blacklist-management)
  - [Provider Detection](#provider-detection)
  - [COAR Notify Inbox](#coar-notify-inbox)
- [Notification System](#notification-system)
- [Development](#development)

## Overview

The COAR Notify INRIA HAL system is a comprehensive platform for extracting and managing software mentions from research papers stored in the HAL repository. The system implements the COAR (Coalition of Open Access Repositories) notification specification to enable bidirectional communication between research repositories and external services.

### Key Features

- **Automated Software Mention Extraction**: Processes research papers to identify software mentions with confidence scoring
- **Multi-Provider Support**: Handles HAL, Software Heritage, Zenodo, and GitHub repositories
- **COAR-Compliant Notifications**: Sends and receives standardized notifications for verification workflows
- **Graph-Based Data Model**: Uses ArangoDB to store complex relationships between documents and software
- **Blacklist Management**: Filters out generic or non-software terms with a managed blacklist system
- **RESTful API**: Complete API for document management, software queries, and system administration
- **Provider-Aware Processing**: Different notification types and processing logic per data provider

### Architecture

The system consists of three main collections in ArangoDB:
- **Documents**: Stores HAL paper metadata
- **Software**: Contains extracted software mentions with context and confidence scores
- **Edges**: Links documents to their software mentions for graph traversal

For detailed database schema information, see the [Database Schema Documentation](docs/database.md).

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

## Database Schema

The system uses ArangoDB with three main collections:

- **Documents Collection** (`documents`): Stores HAL document metadata with unique HAL identifiers
- **Software Collection** (`software`): Contains extracted software mentions with confidence scores and context
- **Edge Collection** (`edge_doc_to_software`): Creates relationships between documents and software mentions

### Key Database Features

- **Graph Capabilities**: Enables complex traversal queries between documents and software
- **Automatic Indexing**: Optimized for performance with unique constraints
- **Blacklist Filtering**: 255+ terms filtered automatically during ingestion
- **Verification Tracking**: COAR notifications update `verification_by_author` status

For comprehensive database documentation including schemas, queries, and performance considerations, see [Database Schema Documentation](docs/database.md).

## API Documentation

### Base URL and reverse-proxy prefix
- Default base URL (local): `http://localhost:5000`
- If served behind NGINX under a prefix (e.g., `/coar`), prepend that prefix to all paths (e.g., `/coar/api/software/status`, `/coar/health`).

### Authentication

Some endpoints require an API key via the `x-api-key` header. The key is read from `auth_admin.json` (`TOKEN`).

Example header:
```
x-api-key: <your-token>
```

### Health Endpoints

#### Service Health
- **GET `/health`**
  - Returns service status and basic ArangoDB info
  - Returns 200 when up; 503 when down

Example:
```sh
curl -s http://localhost:5000/health | jq
```

#### General Status (with auth)
- **GET `/status`**
  - Headers: `x-api-key`
  - Checks API access and database reachability; lists existence of key collections

Example:
```sh
curl -s -H "x-api-key: $API_KEY" http://localhost:5000/status | jq
```

### Document Management

#### Insert Document
- **POST `/api/document`**
  - Headers: `x-api-key`
  - Content-Type: `multipart/form-data` with fields:
    - `file`: JSON file containing software metadata (required)
    - `document_id`: HAL identifier for the document (required)
  - Returns 201 on new insert, 409 if already exists
  - Triggers notification send attempt

Example:
```sh
curl -s -X POST \
  -H "x-api-key: $API_KEY" \
  -F "file=@/path/to/your.json" \
  -F "document_id=hal-01478788" \
  http://localhost:5000/api/document | jq
```

### Software Endpoints

#### Software Status
- **GET `/api/software/status`**
  - Returns a count of documents in the `software` collection

#### Get Software by ID
- **GET `/api/software/<id_software>`**
  - Returns all software docs with the same normalized name as the given software `_key`

#### Get Software Mention
- **GET `/api/software_mention/<id_mention>`**
  - Returns a single software mention document by `_key`

Examples:
```sh
curl -s http://localhost:5000/api/software/status | jq
curl -s http://localhost:5000/api/software/soft123 | jq
curl -s http://localhost:5000/api/software_mention/mention456 | jq
```

### Blacklist Management

The blacklist system filters out generic or non-software terms during document processing.

#### View Blacklist
- **GET `/api/blacklist`**
  - Query Parameters:
    - `search`: Search terms (optional)
    - `limit`: Maximum number of results (default: 50)
  - Returns blacklist terms with statistics

#### Get Blacklist Statistics
- **GET `/api/blacklist/stats`**
  - Returns statistics about the blacklist (total terms, file info)

#### Add Term to Blacklist
- **POST `/api/blacklist`**
  - Headers: `x-api-key`
  - JSON Body: `{"term": "term_to_add"}`
  - Returns 201 on success, 409 if term already exists

#### Remove Term from Blacklist
- **DELETE `/api/blacklist/<term>`**
  - Headers: `x-api-key`
  - Returns 200 on success, 404 if term not found

#### Export Blacklist
- **GET `/api/blacklist/export`**
  - Downloads the blacklist as a CSV file

#### Import Blacklist
- **POST `/api/blacklist/import`**
  - Headers: `x-api-key`
  - Form Data:
    - `file`: CSV file to import (required)
    - `overwrite`: Whether to overwrite existing blacklist (default: false)

Examples:
```sh
# View blacklist
curl -s http://localhost:5000/api/blacklist | jq

# Get statistics
curl -s http://localhost:5000/api/blacklist/stats | jq

# Add term (requires API key)
curl -s -X POST \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"term": "example"}' \
  http://localhost:5000/api/blacklist | jq

# Export blacklist
curl -s http://localhost:5000/api/blacklist/export -o blacklist.csv
```

### Provider Detection

The system automatically detects data providers from filenames and document IDs.

#### Detect Provider from Filename
- **GET `/api/software/provider/<filename>`**
  - Returns provider information for the given filename

#### List Supported Providers
- **GET `/api/software/providers`**
  - Returns all supported providers and their detection patterns

Supported providers:
- **HAL**: `hal-`, `oai:hal:`, `.hal.` patterns
- **Software Heritage**: `swh-`, `softwareheritage`, `.swh.` patterns

Example:
```sh
curl -s http://localhost:5000/api/software/provider/hal-01478788 | jq
curl -s http://localhost:5000/api/software/providers | jq
```

### COAR Notify Inbox

#### Receive Notification
- **POST `/inbox`**
  - Accepts a JSON-LD COAR notification payload
  - Returns 202 with a minimal summary

#### View Notifications
- **GET `/notifications`**
  - Renders an HTML page displaying received notifications (best-effort debugging/inspection)

Examples:
```sh
# Send notification
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d @notification.json \
  http://localhost:5000/inbox | jq

# View notifications in browser
# http://localhost:5000/notifications
```

## Notification System

The notification system implements the COAR specification for bidirectional communication between research repositories and external services.

### Supported Notification Types

- **ActionReview**: Used for peer review and citation notifications (HAL, Zenodo)
- **RelationshipAnnounce**: Used for linking and repository announcements (Software Heritage, GitHub)

### Provider-Specific Processing

The system automatically detects the provider and selects the appropriate notification type:

- **HAL**: ActionReview notifications for peer review workflows
- **Software Heritage**: RelationshipAnnounce notifications for software linking

### Verification Workflow

1. **Software Mention Extraction**: Papers are processed to identify software mentions
2. **Notification Sending**: Automated notifications are sent to relevant providers
3. **Author Response**: External systems send accept/reject notifications
4. **Status Updates**: `verification_by_author` field is updated in the database
5. **Feedback Loop**: Verification status influences future processing

### Configuration

Notification endpoints are configured via environment variables:

```bash
# HAL Configuration
HAL_BASE_URL=https://inria.hal.science
HAL_INBOX_URL=https://inbox-preprod.archives-ouvertes.fr/

# Software Heritage Configuration
SWH_BASE_URL=https://archive.softwareheritage.org
SWH_INBOX_URL=https://inbox.softwareheritage.org

# Development URLs
DEV_BASE_URL=http://127.0.0.1:5500/
DEV_INBOX_URL=http://127.0.0.1:5500/inbox
```

## Development

### System Requirements

- Docker and Docker Compose
- Python 3.9+ (for local development)
- ArangoDB instance

### Local Development Setup

1. **Clone the repository**:
   ```sh
   git clone <repository-url>
   cd COAR-Notify-INRIA-HAL
   ```

2. **Set up environment**:
   ```sh
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start services**:
   ```sh
   docker compose up --build
   ```

4. **Access services**:
   - Flask app: http://localhost:5000
   - ArangoDB UI: http://localhost:8529
