# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build Commands

```bash
make init      # Set up venv and install dependencies (run first)
make test      # Run tests with coverage
make lint      # Run ruff and mypy
make format    # Auto-fix and format code
make build     # Full build: lint, test, security, package
make clean     # Remove venv and all build artifacts
```

CI variants (no venv, for GitHub Actions):
```bash
make init:ci   # Install dependencies system-wide
make build:ci  # Full build without venv activation
```

Run a single test:
```bash
. .venv/bin/activate && PYTHONPATH=src/ pytest tests/test_auth.py::TestCredentials::test_credentials_creation -v
```

## Architecture

This is a CLI tool for the Deployment Queue API, built with Typer and Rich for terminal output.

**Module responsibilities:**

- `config.py` - Settings via pydantic-settings, loads from `DEPLOYMENT_QUEUE_CLI_*` env vars. Credentials stored at `~/.config/deployment-queue-cli/credentials.json`
- `auth.py` - GitHub authentication (Device Flow and PAT). Handles token storage, org membership verification
- `client.py` - Async HTTP client for the Deployment Queue API using httpx. All API methods are async
- `main.py` - Typer CLI commands. Wraps async client calls with `asyncio.run()`

**Key patterns:**

- All API operations use `DeploymentAPIClient` which requires `Credentials` from auth
- Commands that need auth call `get_client()` which exits with error if not logged in
- Taxonomy-based operations (current, history, rollback) require: name, environment, provider, cloud_account_id, region

## Code Standards

- Python 3.13+, 100 char line length
- Type hints required on all functions
- Use `Optional[T]` for nullable types
- Async functions for HTTP operations
- Test classes named `Test<Feature>`, methods named `test_<scenario>`

## Testing

Tests use pytest-asyncio with `asyncio_mode = "auto"`. Mock external dependencies:
- `mock_credentials` fixture for auth
- `mock_github_api` fixture patches GitHub API calls
- `mock_deployment` / `mock_deployment_list` for API response data
- Use `patch("deployment_queue_cli.module.function")` for mocking
