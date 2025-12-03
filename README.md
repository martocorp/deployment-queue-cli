# Deployment Queue CLI

A CLI tool for interacting with the Deployment Queue API. Manage deployments, view history, update status, and perform rollbacks from your terminal.

## Key Features

- **Dual Authentication**: GitHub Device Flow for interactive use, PAT for scripts
- **Organisation-Aware**: Switch between organisations, verify membership
- **Rich Output**: Formatted tables and panels using Rich
- **Async HTTP**: Fast API communication using httpx

## Documentation

- [Usage Guide](docs/USAGE.md) - Detailed CLI reference and examples
- [Code Style Guide](docs/CODESTYLE.md) - Coding standards and conventions

## Quick Start

### Prerequisites

- Python 3.13+
- GitHub account with organisation membership
- Access to the Deployment Queue API

### Installation

```bash
pip install deployment-queue-cli
```

Or from source:

```bash
make init
```

### Configuration

```bash
# Set API URL and GitHub OAuth Client ID
export DEPLOYMENT_QUEUE_CLI_API_URL=https://deployments.example.com
export DEPLOYMENT_QUEUE_CLI_GITHUB_CLIENT_ID=Iv1.xxxxxxxxxx

# Login
deployment-queue-cli login --org my-organisation
```

## Commands

| Command | Description |
|---------|-------------|
| `login` | Authenticate with GitHub (Device Flow or PAT) |
| `logout` | Clear stored credentials |
| `whoami` | Show current session info |
| `switch-org` | Switch to different organisation |
| `list-orgs` | List available organisations |
| `list` | List deployments with filters |
| `get` | Get deployment details by ID |
| `current` | Get current deployment for a component |
| `history` | Show deployment history for a component |
| `update-status` | Update deployment status |
| `rollback` | Create rollback deployment |

## Authentication

The CLI supports two authentication methods:

| Method | Use Case | Command |
|--------|----------|---------|
| **Device Flow** | Interactive terminal | `deployment-queue-cli login --org my-org` |
| **PAT** | Scripts, automation | `deployment-queue-cli login --org my-org --pat ghp_xxx` |

### Device Flow

```bash
$ deployment-queue-cli login --org my-company

To authenticate, visit: https://github.com/login/device
   Enter code: ABCD-1234

Waiting for authorization... Done

Logged in as jsmith (my-company)
```

### Personal Access Token

```bash
$ deployment-queue-cli login --org my-company --pat ghp_xxxxxxxxxxxx
Logged in as jsmith (my-company)
```

PAT requires `read:org` and `read:user` scopes.

## Usage Examples

### List Deployments

```bash
# List all deployments
deployment-queue-cli list

# Filter by environment and status
deployment-queue-cli list --env production --status deployed

# Filter by provider
deployment-queue-cli list --provider gcp --limit 50
```

### Component Operations

```bash
# Get current deployment
deployment-queue-cli current my-service \
  --env production \
  --provider gcp \
  --account my-project \
  --region europe-west1

# View history
deployment-queue-cli history my-service \
  --env production \
  --provider gcp \
  --account my-project \
  --region europe-west1

# Update status
deployment-queue-cli update-status my-service deployed \
  --env production \
  --provider gcp \
  --account my-project \
  --region europe-west1

# Rollback
deployment-queue-cli rollback my-service \
  --env production \
  --provider gcp \
  --account my-project \
  --region europe-west1
```

## Development

| Command | Description |
|---------|-------------|
| `make init` | Set up virtual environment and install dependencies |
| `make lint` | Run ruff and mypy |
| `make format` | Format code with ruff |
| `make test` | Run tests with coverage |
| `make security` | Run bandit security scan |
| `make build` | Full build: lint, test, security, package |

## Project Structure

```
deployment-queue-cli/
├── src/deployment_queue_cli/
│   ├── main.py           # Typer CLI app and commands
│   ├── client.py         # Async API client (httpx)
│   ├── auth.py           # GitHub authentication
│   └── config.py         # Settings via pydantic-settings
├── tests/                # Test suite
└── docs/                 # Documentation
```

## GitHub OAuth App Setup

To enable Device Flow authentication:

1. Go to GitHub Settings → Developer settings → OAuth Apps → New OAuth App
2. Set application name and homepage URL
3. Enable "Device Flow" in the app settings
4. Set `DEPLOYMENT_QUEUE_CLI_GITHUB_CLIENT_ID` to the Client ID

No client secret is needed for Device Flow.
