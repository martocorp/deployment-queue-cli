# Code Style Guide

This document outlines the coding standards and conventions used in the Deployment Queue CLI project.

## Table of Contents

- [General Principles](#general-principles)
- [Python Version](#python-version)
- [Code Formatting](#code-formatting)
- [Linting](#linting)
- [Type Hints](#type-hints)
- [Naming Conventions](#naming-conventions)
- [Project Structure](#project-structure)
- [Imports](#imports)
- [Documentation](#documentation)
- [Testing](#testing)
- [Error Handling](#error-handling)
- [Security](#security)

## General Principles

1. **Readability**: Code should be easy to read and understand
2. **Simplicity**: Prefer simple solutions over complex ones
3. **Consistency**: Follow established patterns throughout the codebase
4. **Explicit over implicit**: Be explicit about types, return values, and behavior

## Python Version

This project requires **Python 3.13+**. Use features available in Python 3.13 including:

- Type hint improvements (`list[T]` instead of `List[T]`)
- Union types with `|` operator
- `match` statements where appropriate

## Code Formatting

### Tools

- **Ruff**: Used for both linting and formatting
- Configuration is in `pyproject.toml`

### Line Length

Maximum line length is **100 characters**.

```toml
[tool.ruff]
line-length = 100
target-version = "py313"
```

### Running Formatters

```bash
make format
```

Or manually:

```bash
ruff check --fix src/ tests/
ruff format src/ tests/
```

## Linting

### Enabled Rules

The following Ruff rule sets are enabled:

- `E` - pycodestyle errors
- `F` - Pyflakes
- `I` - isort (import sorting)
- `W` - pycodestyle warnings

```toml
[tool.ruff.lint]
select = ["E", "F", "I", "W"]
```

### Running Linter

```bash
make lint
```

Or manually:

```bash
ruff check src/ tests/
mypy src/ --python-version 3.13 --ignore-missing-imports
```

## Type Hints

### Requirements

- All function parameters must have type hints
- All function return types must be annotated
- Use `Optional[T]` or `T | None` for nullable types

### Examples

```python
# Good
async def list_deployments(
    environment: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    ...

def get_client(api_url: Optional[str] = None) -> DeploymentAPIClient:
    ...

# Bad - missing type hints
def get_client(api_url):
    ...
```

### Optional vs None Union

Prefer `Optional[T]` for consistency with the existing codebase:

```python
from typing import Optional

# Preferred in this project
def func(param: Optional[str] = None) -> Optional[str]:
    ...
```

## Naming Conventions

### Variables and Functions

- Use `snake_case` for variables and functions
- Use descriptive names that indicate purpose

```python
# Good
deployment_id = "abc-123"
cloud_account_id = "project-123"

def get_current_deployment() -> dict:
    ...

# Bad
id = "abc-123"  # Too generic, shadows builtin
d = "abc-123"   # Not descriptive

def get() -> dict:  # Not descriptive
    ...
```

### Classes

- Use `PascalCase` for class names
- Dataclasses and Pydantic models should be nouns describing the data

```python
# Good
@dataclass
class Credentials:
    ...

class DeploymentAPIClient:
    ...

class Settings(BaseSettings):
    ...
```

### Constants

- Use `UPPER_SNAKE_CASE` for constants
- Define at module level

```python
CONFIG_DIR = Path.home() / ".config" / "deployment-queue-cli"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"
GITHUB_API_URL = "https://api.github.com"
```

## Project Structure

```
deployment-queue-cli/
├── src/
│   └── deployment_queue_cli/     # Main package
│       ├── __init__.py           # Package init with version
│       ├── main.py               # Typer CLI app and commands
│       ├── client.py             # API client for HTTP requests
│       ├── auth.py               # GitHub authentication (Device Flow + PAT)
│       └── config.py             # Settings via pydantic-settings
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Pytest fixtures
│   ├── test_auth.py              # Authentication tests
│   └── test_client.py            # API client tests
└── docs/
    ├── USAGE.md                  # Usage documentation
    └── CODESTYLE.md              # This file
```

### Module Organization

- `main.py`: Typer app instance, CLI command definitions, Rich console output
- `client.py`: Async HTTP client for API communication using httpx
- `auth.py`: GitHub Device Flow and PAT authentication, credentials storage
- `config.py`: Application settings using pydantic-settings

## Imports

### Order

Imports should be sorted in the following order (handled by Ruff):

1. Standard library imports
2. Third-party imports
3. Local application imports

```python
# Standard library
import asyncio
import json
from typing import Optional

# Third-party
import httpx
import typer
from rich.console import Console

# Local
from .auth import get_stored_credentials
from .client import DeploymentAPIClient
from .config import get_settings
```

### Import Style

- Import specific items, not entire modules
- Group related imports on the same line when reasonable

```python
# Good
from .auth import (
    clear_credentials,
    device_flow_login,
    get_stored_credentials,
    pat_login,
)

# Avoid
from . import auth
# Then using: auth.get_stored_credentials, auth.device_flow_login
```

## Documentation

### Module Docstrings

Every module should have a docstring explaining its purpose:

```python
"""CLI entry point and commands for the Deployment Queue CLI."""
```

### Function Docstrings

Use docstrings for public functions. Keep them concise:

```python
def get_client(api_url: Optional[str] = None) -> DeploymentAPIClient:
    """Get authenticated API client or exit with error."""
    ...
```

### Inline Comments

- Use sparingly and only when the code isn't self-explanatory
- Explain "why", not "what"

```python
# Owner read/write only - credentials contain sensitive token
CREDENTIALS_FILE.chmod(0o600)
```

## Testing

### Test Structure

- Test files mirror source structure with `test_` prefix
- Test classes group related tests
- Test methods use descriptive names

```python
class TestDeviceFlowLogin:
    """Tests for GitHub Device Flow authentication."""

    async def test_device_flow_login_success(self):
        ...

    async def test_device_flow_login_missing_client_id(self):
        ...
```

### Fixtures

- Define reusable fixtures in `conftest.py`
- Use pytest-asyncio for async tests

```python
@pytest.fixture
def mock_credentials() -> Credentials:
    """Fixture for test credentials."""
    return Credentials(
        github_token="test-token",
        organisation="test-org",
        username="test-user",
    )
```

### Running Tests

```bash
make test
```

Or manually:

```bash
PYTHONPATH=src/ coverage run -m pytest tests/ -v
coverage report
coverage html --directory target/coverage
```

## Error Handling

### CLI Errors

Use Typer's exit mechanism with user-friendly Rich output:

```python
from rich.console import Console
import typer

console = Console()

def handle_api_error(e: DeploymentAPIError) -> None:
    """Handle API errors with user-friendly output."""
    if e.status_code == 401:
        console.print("[red]Authentication failed. Try 'deployment-queue-cli login' again.[/red]")
    elif e.status_code == 404:
        console.print(f"[yellow]Not found: {e.detail}[/yellow]")
    else:
        console.print(f"[red]API error ({e.status_code}): {e.detail}[/red]")
    raise typer.Exit(1)
```

### Exceptions

- Use built-in exceptions (`ValueError`, `TimeoutError`) for auth errors
- Create custom exceptions for API-specific errors

```python
class DeploymentAPIError(Exception):
    """Exception raised for API errors."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API error {status_code}: {detail}")
```

## Security

### Security Scanning

Run Bandit for security analysis:

```bash
make security
```

### Credential Storage

- Store credentials in user's config directory: `~/.config/deployment-queue-cli/`
- Set restrictive file permissions (0o600 - owner read/write only)
- Never log or display tokens

```python
def store_credentials(creds: Credentials) -> None:
    """Store credentials to disk securely."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_FILE.write_text(json.dumps({...}))
    CREDENTIALS_FILE.chmod(0o600)  # Owner read/write only
```

### Sensitive Data

- Never commit `.env` files (they're in `.gitignore`)
- Use environment variables for configuration
- Support both Device Flow and PAT authentication
