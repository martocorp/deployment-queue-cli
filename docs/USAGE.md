# Usage Guide

This document provides detailed usage instructions for the Deployment Queue CLI.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Authentication](#authentication)
- [Commands Reference](#commands-reference)
- [Examples](#examples)

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

### Configuration File

Create a `.env` file in your working directory or set environment variables:

```bash
DEPLOYMENT_QUEUE_CLI_API_URL=https://deployments.example.com
DEPLOYMENT_QUEUE_CLI_GITHUB_CLIENT_ID=Iv1.xxxxxxxxxx
```

### Credentials Storage

Credentials are stored securely at `~/.config/deployment-queue-cli/credentials.json` with restricted permissions (0600).

## Authentication

The CLI supports two authentication methods:

| Method | Use Case | Requirements |
|--------|----------|--------------|
| **Device Flow** | Interactive terminal use | GitHub OAuth App Client ID |
| **PAT** | Scripts, automation | GitHub PAT with `read:org` and `read:user` scopes |

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
| `list` | List deployments with filters |
| `get` | Get deployment details by ID |
| `current` | Get current deployment for a component |
| `history` | Show deployment history for a component |
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

#### list

List deployments with optional filters.

```bash
deployment-queue-cli list [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--env` | `-e` | | Filter by environment |
| `--status` | `-s` | | Filter by status |
| `--provider` | `-p` | | Filter by provider (gcp/aws/azure) |
| `--trigger` | `-t` | | Filter by trigger (auto/manual/rollback) |
| `--limit` | `-n` | 20 | Maximum results |
| `--api-url` | | | Override API URL |

#### get

Get deployment details by ID.

```bash
deployment-queue-cli get <deployment-id> [--api-url <url>]
```

#### current

Get the current (most recent deployed) deployment for a component.

```bash
deployment-queue-cli current <name> [OPTIONS]
```

| Option | Short | Required | Description |
|--------|-------|----------|-------------|
| `--env` | `-e` | Yes | Environment |
| `--provider` | `-p` | Yes | Provider (gcp/aws/azure) |
| `--account` | `-a` | Yes | Cloud account ID |
| `--region` | `-r` | Yes | Cloud region |
| `--cell` | | No | Cell ID |
| `--api-url` | | No | Override API URL |

#### history

Show deployment history for a component.

```bash
deployment-queue-cli history <name> [OPTIONS]
```

| Option | Short | Required | Default | Description |
|--------|-------|----------|---------|-------------|
| `--env` | `-e` | Yes | | Environment |
| `--provider` | `-p` | Yes | | Provider |
| `--account` | `-a` | Yes | | Cloud account ID |
| `--region` | `-r` | Yes | | Cloud region |
| `--cell` | | No | | Cell ID |
| `--limit` | `-n` | No | 10 | Maximum results |
| `--api-url` | | No | | Override API URL |

#### update-status

Update the status of a deployment.

```bash
deployment-queue-cli update-status <name> <status> [OPTIONS]
```

**Valid statuses:** `scheduled`, `in_progress`, `deployed`, `failed`, `skipped`

| Option | Short | Required | Description |
|--------|-------|----------|-------------|
| `--env` | `-e` | Yes | Environment |
| `--provider` | `-p` | Yes | Provider |
| `--account` | `-a` | Yes | Cloud account ID |
| `--region` | `-r` | Yes | Cloud region |
| `--cell` | | No | Cell ID |
| `--notes` | | No | Notes for the update |
| `--api-url` | | No | Override API URL |

**Note:** When setting status to `deployed`, older scheduled deployments for the same taxonomy are automatically marked as `skipped`.

#### rollback

Create a rollback deployment.

```bash
deployment-queue-cli rollback <name> [OPTIONS]
```

| Option | Short | Required | Default | Description |
|--------|-------|----------|---------|-------------|
| `--env` | `-e` | Yes | | Environment |
| `--provider` | `-p` | Yes | | Provider |
| `--account` | `-a` | Yes | | Cloud account ID |
| `--region` | `-r` | Yes | | Cloud region |
| `--cell` | | No | | Cell ID |
| `--version` | `-v` | No | Previous | Target version |
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

### Listing Deployments

#### List All Deployments

```bash
$ deployment-queue-cli list
╭───────────────────── Deployments ─────────────────────╮
│ Name          Version     Environment  Status    ... │
├───────────────────────────────────────────────────────┤
│ user-service  v2.1.0      production   deployed  ... │
│ api-gateway   abc123def   staging      scheduled ... │
│ data-pipeline v1.0.5      production   failed    ... │
╰───────────────────────────────────────────────────────╯
```

#### List with Filters

```bash
# List deployed production deployments
deployment-queue-cli list --env production --status deployed

# List GCP deployments triggered by rollback
deployment-queue-cli list --provider gcp --trigger rollback

# List last 50 scheduled deployments
deployment-queue-cli list --status scheduled --limit 50
```

### Component Operations

#### Get Current Deployment

```bash
$ deployment-queue-cli current user-service \
    --env production \
    --provider gcp \
    --account my-project-123 \
    --region europe-west1

user-service @ v2.1.0
Status: deployed
Trigger: auto
Created: 2024-01-15 10:30:45
```

#### View Deployment History

```bash
$ deployment-queue-cli history user-service \
    --env production \
    --provider gcp \
    --account my-project-123 \
    --region europe-west1 \
    --limit 5

╭────────── History: user-service (production) ──────────╮
│ Version   Status    Trigger   Created            Actor │
├────────────────────────────────────────────────────────┤
│ v2.1.0    deployed  auto      2024-01-15 10:30   ci    │
│ v2.0.9    skipped   auto      2024-01-15 10:25   ci    │
│ v2.0.8    deployed  rollback  2024-01-14 15:00   jsmith│
│ v2.0.9    failed    auto      2024-01-14 14:30   ci    │
│ v2.0.8    deployed  auto      2024-01-13 09:00   ci    │
╰────────────────────────────────────────────────────────╯
```

### Status Updates

#### Mark Deployment as Deployed

```bash
$ deployment-queue-cli update-status user-service deployed \
    --env production \
    --provider gcp \
    --account my-project-123 \
    --region europe-west1 \
    --notes "Deployment verified in monitoring"

Updated user-service to deployed
```

#### Mark Deployment as Failed

```bash
$ deployment-queue-cli update-status user-service failed \
    --env production \
    --provider gcp \
    --account my-project-123 \
    --region europe-west1 \
    --notes "Health check failed after deploy"

Updated user-service to failed
```

### Rollback Operations

#### Rollback to Previous Version

```bash
$ deployment-queue-cli rollback user-service \
    --env production \
    --provider gcp \
    --account my-project-123 \
    --region europe-west1

Rollback created: user-service -> v2.0.8
  ID: abc123-def456-...
  Source: def456...
  Rollback from: abc123...
```

#### Rollback to Specific Version

```bash
$ deployment-queue-cli rollback user-service \
    --env production \
    --provider gcp \
    --account my-project-123 \
    --region europe-west1 \
    --version v1.9.0

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
$ deployment-queue-cli list --env staging
```
