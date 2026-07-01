# Development

[← Back to README](../README.md)

## System Requirements

- Docker and Docker Compose
- Python 3.11+ (for local development)
- ArangoDB instance

## Local Development Setup

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

See [Configuration & Setup](configuration.md) for running without Docker Compose and the full
environment-variable reference.

## Code Quality

Development tools are pinned in the `dev` dependency group in `pyproject.toml`
(`ruff`, `mypy`, `bump-my-version`). Install them with [uv](https://docs.astral.sh/uv/),
which syncs runtime deps and the `dev` group from `uv.lock` by default:

```sh
uv sync
```

Linting and formatting use [Ruff](https://docs.astral.sh/ruff/). The CI build
**fails** if either check reports a problem, so run them before pushing:

```sh
# Check lint and formatting (these are the exact steps CI runs)
uv run ruff check app run.py
uv run ruff format --check app run.py

# Auto-fix lint findings and reformat in place
uv run ruff check --fix app run.py
uv run ruff format app run.py
```

Running through `uv run` uses the pinned Ruff version from `uv.lock` — a newer
Ruff may report different issues than CI and make your local results disagree
with the pipeline.

Type checking is relaxed for now and runs **non-blocking** in CI:

```sh
uv run mypy app
```

## Releasing

Releases are cut manually with `bump-my-version`; CI handles the rest on tag push.

1. Ensure `main` is green and your working tree is clean.
2. Bump the version — this updates `pyproject.toml`, commits, and creates a
   `vX.Y.Z` tag:
   ```sh
   uv run bump-my-version bump [patch|minor|major]
   ```
3. Push the commit and the tag:
   ```sh
   git push && git push --tags
   ```

On the tag push, CI builds and publishes the Docker image
`lfoppiano/coar-notify-inria-hal:vX.Y.Z` and creates a GitHub Release with
auto-generated notes from the commits since the previous tag.
