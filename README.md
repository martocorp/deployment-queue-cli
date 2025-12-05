# Deployment Queue CLI

A CLI tool and MCP server for interacting with the Deployment Queue API. Manage deployments, view history, update status, and perform rollbacks from your terminal or through Claude.

## Key Features

- **Dual Authentication**: GitHub Device Flow for interactive use, PAT for scripts
- **Organisation-Aware**: Switch between organisations, verify membership
- **Rich Output**: Formatted tables and panels using Rich
- **Async HTTP**: Fast API communication using httpx
- **MCP Server**: Expose deployment operations as tools for Claude

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
| `create` | Create a new deployment |
| `list` | List deployments with filters |
| `release` | Release a deployment (set to in_progress) |
| `update-status` | Update deployment status |
| `rollback` | Create rollback deployment |

## Authentication

The CLI supports multiple authentication methods with the following priority:

1. **Environment Variables** - Direct credentials via env vars
2. **Custom Credentials File** - Path specified via env var
3. **Default Credentials File** - `~/.config/deployment-queue-cli/credentials.json`

| Method | Use Case | Setup |
|--------|----------|-------|
| **Device Flow** | Interactive terminal | `deployment-queue-cli login --org my-org` |
| **PAT via CLI** | One-time setup | `deployment-queue-cli login --org my-org --pat ghp_xxx` |
| **Environment Variables** | CI/CD, MCP server | See below |
| **Credentials File** | Shared config | See below |

### Environment Variables (for CI/CD and MCP)

```bash
export DEPLOYMENT_QUEUE_CLI_GITHUB_TOKEN=ghp_xxxxxxxxxxxx
export DEPLOYMENT_QUEUE_CLI_ORGANISATION=my-org
export DEPLOYMENT_QUEUE_CLI_USERNAME=my-username  # Optional
```

### Custom Credentials File

```bash
export DEPLOYMENT_QUEUE_CLI_CREDENTIALS_FILE=/path/to/credentials.json
```

The file should contain:
```json
{
  "github_token": "ghp_xxxxxxxxxxxx",
  "organisation": "my-org",
  "username": "my-username"
}
```

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

### Create Deployments

```bash
# Create a Kubernetes deployment
deployment-queue-cli create my-service v1.2.3 \
  --type k8s \
  --provider gcp \
  --account my-project \
  --region europe-west1

# Create with pipeline params
deployment-queue-cli create my-service v1.2.3 \
  --type k8s \
  --provider gcp \
  --pipeline-params '{"replicas": 3}'
```

### List Deployments

```bash
# List all deployments
deployment-queue-cli list

# Filter by status
deployment-queue-cli list --status deployed

# Filter by provider
deployment-queue-cli list --provider gcp --limit 50
```

### Release Deployment

```bash
# Release a deployment (interactive confirmation)
deployment-queue-cli release ca58b04e-1530-40be-a84c-2c3541468424

# Skip confirmation prompt
deployment-queue-cli release ca58b04e-1530-40be-a84c-2c3541468424 --yes
```

### Update Deployment Status

```bash
# Set deployment to deployed
deployment-queue-cli update-status ca58b04e-1530-40be-a84c-2c3541468424 deployed

# Set deployment to failed
deployment-queue-cli update-status ca58b04e-1530-40be-a84c-2c3541468424 failed
```

### Rollback

```bash
# Rollback to previous version
deployment-queue-cli rollback my-service \
  --provider gcp \
  --account my-project \
  --region europe-west1

# Rollback to specific version
deployment-queue-cli rollback my-service \
  --provider gcp \
  --account my-project \
  --region europe-west1 \
  --version v1.0.0
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
│   ├── mcp_server.py     # MCP server for Claude integration
│   ├── client.py         # Async API client (httpx)
│   ├── auth.py           # GitHub authentication
│   └── config.py         # Settings via pydantic-settings
├── tests/                # Test suite
└── docs/                 # Documentation
```

## MCP Server

The MCP server exposes deployment operations as tools for Claude.

### Setup with Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "deployment-queue": {
      "command": "deployment-queue-mcp",
      "env": {
        "DEPLOYMENT_QUEUE_CLI_API_URL": "https://deployments.example.com"
      }
    }
  }
}
```

### Available Tools

| Tool | Description |
|------|-------------|
| `list_deployments` | List deployments with optional filters |
| `create_deployment` | Create a new deployment |
| `get_deployment` | Get deployment details by ID |
| `release_deployment` | Release a deployment (set to in_progress) |
| `update_deployment_status` | Update deployment status |
| `rollback_deployment` | Create a rollback deployment |

### Authentication

The MCP server uses the same credentials as the CLI. You can either:

1. Run `deployment-queue-cli login` first to authenticate, or
2. Pass credentials via environment variables in the MCP config:

```json
{
  "mcpServers": {
    "deployment-queue": {
      "command": "deployment-queue-mcp",
      "env": {
        "DEPLOYMENT_QUEUE_CLI_API_URL": "https://deployments.example.com",
        "DEPLOYMENT_QUEUE_CLI_GITHUB_TOKEN": "ghp_xxxxxxxxxxxx",
        "DEPLOYMENT_QUEUE_CLI_ORGANISATION": "my-org"
      }
    }
  }
}
```

## GitHub OAuth App Setup

To enable Device Flow authentication:

1. Go to GitHub Settings → Developer settings → OAuth Apps → New OAuth App
2. Set application name and homepage URL
3. Enable "Device Flow" in the app settings
4. Set `DEPLOYMENT_QUEUE_CLI_GITHUB_CLIENT_ID` to the Client ID

No client secret is needed for Device Flow.
