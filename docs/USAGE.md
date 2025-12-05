# Usage Guide

This document provides detailed usage instructions for the Deployment Queue CLI.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Authentication](#authentication)
- [Commands Reference](#commands-reference)
- [Examples](#examples)
- [MCP Server](#mcp-server)

## Prerequisites

- Python 3.13 or higher
- GitHub account with organisation membership
- Access to the Deployment Queue API

## Installation

### Using pip

```bash
pip install deployment-queue-cli
```

### Using uv

```bash
uv pip install deployment-queue-cli
```

### From Source

```bash
git clone https://github.com/your-org/deployment-queue-cli.git
cd deployment-queue-cli
make init
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEPLOYMENT_QUEUE_CLI_API_URL` | Yes | `https://deployments.example.com` | Deployment Queue API URL |
| `DEPLOYMENT_QUEUE_CLI_GITHUB_CLIENT_ID` | For Device Flow | - | GitHub OAuth App Client ID |
| `DEPLOYMENT_QUEUE_CLI_GITHUB_TOKEN` | For env auth | - | GitHub token (direct auth) |
| `DEPLOYMENT_QUEUE_CLI_ORGANISATION` | For env auth | - | Organisation name (direct auth) |
| `DEPLOYMENT_QUEUE_CLI_USERNAME` | No | `env-user` | Username (direct auth) |
| `DEPLOYMENT_QUEUE_CLI_CREDENTIALS_FILE` | No | - | Path to credentials JSON file |

### Configuration File

Create a `.env` file in your working directory or set environment variables:

```bash
DEPLOYMENT_QUEUE_CLI_API_URL=https://deployments.example.com
DEPLOYMENT_QUEUE_CLI_GITHUB_CLIENT_ID=Iv1.xxxxxxxxxx
```

### Credentials Storage

Credentials are loaded with the following priority:

1. **Environment Variables** - `DEPLOYMENT_QUEUE_CLI_GITHUB_TOKEN` + `DEPLOYMENT_QUEUE_CLI_ORGANISATION`
2. **Custom Credentials File** - Path from `DEPLOYMENT_QUEUE_CLI_CREDENTIALS_FILE`
3. **Default Credentials File** - `~/.config/deployment-queue-cli/credentials.json`

The default credentials file is stored securely with restricted permissions (0600).

#### Credentials File Format

```json
{
  "github_token": "ghp_xxxxxxxxxxxx",
  "organisation": "my-org",
  "username": "my-username"
}
```

## Authentication

The CLI supports multiple authentication methods:

| Method | Use Case | Requirements |
|--------|----------|--------------|
| **Device Flow** | Interactive terminal use | GitHub OAuth App Client ID |
| **PAT** | Scripts, automation | GitHub PAT with `read:org` and `read:user` scopes |
| **Environment Variables** | CI/CD, MCP server | `GITHUB_TOKEN` + `ORGANISATION` env vars |
| **Credentials File** | Shared configuration | JSON file with credentials |

### Device Flow (Recommended)

Device Flow opens a browser for GitHub authentication:

```bash
deployment-queue-cli login --org my-organisation
```

**Setup Requirements:**

1. Create a GitHub OAuth App at Settings → Developer settings → OAuth Apps
2. Enable "Device Flow" in the app settings
3. Set `DEPLOYMENT_QUEUE_CLI_GITHUB_CLIENT_ID` to the app's Client ID

**Flow:**

1. CLI displays a code and URL
2. Open the URL in your browser
3. Enter the code when prompted
4. Authorise the application
5. CLI receives token and verifies organisation membership

### Personal Access Token

For scripts or when Device Flow is not available:

```bash
deployment-queue-cli login --org my-organisation --pat ghp_xxxxxxxxxxxx
```

**PAT Requirements:**

- `read:org` scope (to verify organisation membership)
- `read:user` scope (to get username)

### Session Management

```bash
# Check current session
deployment-queue-cli whoami

# List available organisations
deployment-queue-cli list-orgs

# Switch to different organisation
deployment-queue-cli switch-org other-org

# Clear credentials
deployment-queue-cli logout
```

## Commands Reference

### Authentication Commands

| Command | Description |
|---------|-------------|
| `login` | Authenticate with GitHub |
| `logout` | Clear stored credentials |
| `whoami` | Show current session info |
| `switch-org` | Switch to different organisation |
| `list-orgs` | List available organisations |

### Deployment Commands

| Command | Description |
|---------|-------------|
| `create` | Create a new deployment |
| `list` | List deployments with filters |
| `release` | Release a deployment (set to in_progress) |
| `update-status` | Update deployment status |
| `rollback` | Create rollback deployment |

### Command Details

#### login

Authenticate with the Deployment Queue API.

```bash
deployment-queue-cli login --org <organisation> [--pat <token>]
```

| Option | Short | Required | Description |
|--------|-------|----------|-------------|
| `--org` | `-o` | Yes | GitHub organisation |
| `--pat` | | No | GitHub PAT (skips Device Flow) |

#### logout

Clear stored credentials.

```bash
deployment-queue-cli logout
```

#### whoami

Show current authentication status.

```bash
deployment-queue-cli whoami
```

#### switch-org

Switch to a different organisation using existing token.

```bash
deployment-queue-cli switch-org <organisation>
```

#### list-orgs

List all organisations available to the authenticated user.

```bash
deployment-queue-cli list-orgs
```

#### create

Create a new deployment.

```bash
deployment-queue-cli create <name> <version> [OPTIONS]
```

| Option | Short | Required | Default | Description |
|--------|-------|----------|---------|-------------|
| `--type` | `-T` | Yes | | Deployment type (k8s/terraform/data_pipeline) |
| `--provider` | `-p` | Yes | | Provider (gcp/aws/azure) |
| `--account` | `-a` | No | | Cloud account ID |
| `--region` | `-r` | No | | Cloud region |
| `--cell` | | No | | Cell ID |
| `--auto/--no-auto` | | No | `--auto` | Auto-deploy when ready |
| `--description` | `-d` | No | | Deployment description |
| `--notes` | | No | | Deployment notes |
| `--commit` | | No | | Git commit SHA |
| `--build-uri` | | No | | Build URI |
| `--pipeline-params` | | No | | Pipeline extra params (JSON string) |
| `--yes` | `-y` | No | false | Skip confirmation prompt |
| `--api-url` | | No | | Override API URL |

#### list

List deployments. By default, only shows scheduled deployments. Use `--all` to see all statuses.

```bash
deployment-queue-cli list [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--all` | `-a` | false | List all deployments (default: scheduled only) |
| `--status` | `-s` | scheduled | Filter by status |
| `--provider` | `-p` | | Filter by provider (gcp/aws/azure) |
| `--trigger` | `-t` | | Filter by trigger (auto/manual/rollback) |
| `--limit` | `-n` | 20 | Maximum results |
| `--sort-updated` | `-u` | false | Sort by updated timestamp (newest first) |
| `--api-url` | | | Override API URL |

#### release

Release a deployment (set status to in_progress).

```bash
deployment-queue-cli release <deployment-id> [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--yes` | `-y` | false | Skip confirmation prompt |
| `--api-url` | | | Override API URL |

#### update-status

Update deployment status.

```bash
deployment-queue-cli update-status <deployment-id> <status>
```

| Argument | Required | Description |
|----------|----------|-------------|
| `deployment-id` | Yes | Deployment ID |
| `status` | Yes | New status (scheduled/in_progress/deployed/failed/skipped) |

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--api-url` | | | Override API URL |

#### rollback

Create a rollback deployment from an existing deployment ID.

```bash
deployment-queue-cli rollback <deployment_id> [OPTIONS]
```

| Option | Short | Required | Default | Description |
|--------|-------|----------|---------|-------------|
| `--version` | `-v` | No | Previous | Target version |
| `--yes` | `-y` | No | false | Skip confirmation prompt |
| `--api-url` | | No | | Override API URL |

## Examples

### Authentication Examples

#### Login with Device Flow

```bash
$ deployment-queue-cli login --org my-company

To authenticate, visit: https://github.com/login/device
   Enter code: ABCD-1234

Waiting for authorization... Done

Logged in as jsmith (my-company)
```

#### Login with PAT

```bash
$ deployment-queue-cli login --org my-company --pat ghp_xxxxxxxxxxxx
Logged in as jsmith (my-company)
```

#### Check Session

```bash
$ deployment-queue-cli whoami
╭──────────────── Current Session ────────────────╮
│ Username: jsmith                                │
│ Organisation: my-company                        │
│ API URL: https://deployments.example.com        │
╰─────────────────────────────────────────────────╯
```

### Creating Deployments

#### Create a Kubernetes Deployment

```bash
$ deployment-queue-cli create user-service v2.1.0 \
    --type k8s \
    --provider gcp \
    --account my-project-123 \
    --region europe-west1

Created deployment: user-service @ v2.1.0
  ID: abc123-def456-...
  Status: scheduled
```

#### Create with All Options

```bash
$ deployment-queue-cli create user-service v2.1.0 \
    --type k8s \
    --provider gcp \
    --account my-project-123 \
    --region europe-west1 \
    --cell cell-001 \
    --commit abc123def \
    --description "Release 2.1.0" \
    --notes "Feature X enabled" \
    --build-uri "https://ci.example.com/builds/123" \
    --pipeline-params '{"replicas": 3, "memory": "2Gi"}'

Created deployment: user-service @ v2.1.0
  ID: abc123-def456-...
  Status: scheduled
```

#### Create with Manual Approval Required

```bash
$ deployment-queue-cli create user-service v2.1.0 \
    --type terraform \
    --provider aws \
    --no-auto

Created deployment: user-service @ v2.1.0
  ID: xyz789-...
  Status: scheduled
```

### Listing Deployments

#### List All Deployments

```bash
$ deployment-queue-cli list
╭──────────────────────────────────── Deployments ─────────────────────────────────────╮
│ ID           │ Name          │ Version  │ Status    │ Created     │ Provider │ ... │
├──────────────┼───────────────┼──────────┼───────────┼─────────────┼──────────┼─────┤
│ abc123...    │ user-service  │ v2.1.0   │ deployed  │ 2024-01-15  │ gcp      │ ... │
│ def456...    │ api-gateway   │ abc123de │ scheduled │ 2024-01-15  │ aws      │ ... │
│ ghi789...    │ data-pipeline │ v1.0.5   │ failed    │ 2024-01-14  │ gcp      │ ... │
╰──────────────┴───────────────┴──────────┴───────────┴─────────────┴──────────┴─────╯
```

#### List with Filters

```bash
# List deployed deployments
deployment-queue-cli list --status deployed

# List GCP deployments triggered by rollback
deployment-queue-cli list --provider gcp --trigger rollback

# List last 50 scheduled deployments
deployment-queue-cli list --status scheduled --limit 50
```

### Releasing Deployments

#### Release with Confirmation

```bash
$ deployment-queue-cli release ca58b04e-1530-40be-a84c-2c3541468424
==================================================
Deployment Details
==================================================
Deployment ID         : ca58b04e-1530-40be-a84c-2c3541468424
Provider              : gcp
Region                : europe-west2
Cloud Account ID      : my-project-123
Cell                  : 01
Type                  : k8s
Name                  : user-service
Version               : v2.1.0
Description           : Feature release
Status                : scheduled
Commit SHA            : 3a7622e74e19d9c16d8ad7af6c4b28f32ffee7d3
Pipeline Extra Params : {"chart_version": "0.28.0"}
==================================================
Do you want to continue? [y/n]: y

Deployment released: user-service @ v2.1.0
  Status: in_progress
```

#### Release without Confirmation

```bash
$ deployment-queue-cli release ca58b04e-1530-40be-a84c-2c3541468424 --yes

Deployment released: user-service @ v2.1.0
  Status: in_progress
```

### Updating Deployment Status

#### Mark Deployment as Deployed

```bash
$ deployment-queue-cli update-status ca58b04e-1530-40be-a84c-2c3541468424 deployed

Updated deployment: user-service @ v2.1.0
  Status: deployed
```

#### Mark Deployment as Failed

```bash
$ deployment-queue-cli update-status ca58b04e-1530-40be-a84c-2c3541468424 failed

Updated deployment: user-service @ v2.1.0
  Status: failed
```

### Rollback Operations

#### Rollback to Previous Version

```bash
$ deployment-queue-cli rollback abc123-def456-ghi789

Rollback created: user-service -> v2.0.8
  ID: new123-def456-...
  Source: def456...
  Rollback from: abc123...
```

#### Rollback to Specific Version

```bash
$ deployment-queue-cli rollback abc123-def456-ghi789 --version v1.9.0

Rollback created: user-service -> v1.9.0
  ID: xyz789-...
  Source: older123...
  Rollback from: abc123...
```

### Working with Multiple Organisations

```bash
# List available organisations
$ deployment-queue-cli list-orgs
Available organisations:
  - my-company
  - my-company-sandbox
  - partner-org

# Switch to sandbox
$ deployment-queue-cli switch-org my-company-sandbox
Switched to my-company-sandbox

# View deployments in sandbox
$ deployment-queue-cli list --status scheduled
```

## MCP Server

The package includes an MCP (Model Context Protocol) server that exposes deployment operations as tools for Claude.

### Setup

#### Claude Desktop

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

#### Claude Code

Add to your Claude Code MCP settings:

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

### Authentication

The MCP server uses the same credentials as the CLI. Authenticate first:

```bash
deployment-queue-cli login --org my-organisation
```

### Available Tools

| Tool | Description |
|------|-------------|
| `list_deployments` | List deployments with optional filters (status, provider, trigger, limit) |
| `create_deployment` | Create a new deployment (requires name, version, type, provider) |
| `get_deployment` | Get deployment details by ID |
| `release_deployment` | Release a deployment (set status to in_progress) |
| `update_deployment_status` | Update deployment status |
| `rollback_deployment` | Create a rollback deployment |

### Tool Parameters

#### list_deployments

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter by status |
| `provider` | string | No | Filter by provider (gcp/aws/azure) |
| `trigger` | string | No | Filter by trigger (auto/manual/rollback) |
| `limit` | integer | No | Maximum results (default: 20) |

#### create_deployment

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Component name |
| `version` | string | Yes | Version to deploy |
| `type` | string | Yes | Deployment type (k8s/terraform/data_pipeline) |
| `provider` | string | Yes | Provider (gcp/aws/azure) |
| `cloud_account_id` | string | No | Cloud account ID |
| `region` | string | No | Cloud region |
| `cell` | string | No | Cell ID |
| `auto` | boolean | No | Auto-deploy when ready (default: true) |
| `description` | string | No | Deployment description |
| `notes` | string | No | Deployment notes |
| `commit_sha` | string | No | Git commit SHA |
| `build_uri` | string | No | Build URI |
| `pipeline_extra_params` | string | No | Pipeline extra params (JSON string) |

#### get_deployment

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `deployment_id` | string | Yes | Deployment ID |

#### release_deployment

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `deployment_id` | string | Yes | Deployment ID |

#### update_deployment_status

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `deployment_id` | string | Yes | Deployment ID |
| `status` | string | Yes | New status |

#### rollback_deployment

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `deployment_id` | string | Yes | Deployment ID to rollback |
| `target_version` | string | No | Target version (default: previous) |
