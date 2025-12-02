# Deployment Queue CLI

CLI tool for interacting with the Deployment Queue API.

## Installation

```bash
pip install deployment-queue-cli
# or
uv pip install deployment-queue-cli
```

## Development Setup

```bash
# Clone the repository
git clone https://github.com/your-org/deployment-queue-cli.git
cd deployment-queue-cli

# Set up virtual environment and install dependencies
make init

# Run tests
make test

# Run linting
make lint

# Format code
make format

# Build package
make build
```

## Configuration

Set environment variables or create a `.env` file:

```bash
# API URL (required)
export DEPLOYMENT_QUEUE_CLI_API_URL=https://deployments.example.com

# GitHub OAuth App Client ID (required for device flow login)
export DEPLOYMENT_QUEUE_CLI_GITHUB_CLIENT_ID=your_oauth_app_client_id
```

Or per-command:

```bash
deployment-queue-cli list --api-url https://deployments.example.com
```

## Authentication

### Device Flow (Recommended)

```bash
deployment-queue-cli login --org your-org
```

This opens a browser for GitHub authentication.

### Personal Access Token

```bash
deployment-queue-cli login --org your-org --pat ghp_xxxxxxxxxxxx
```

PAT requires `read:org` and `read:user` scopes.

## Commands

### Authentication Commands

#### Check auth status

```bash
deployment-queue-cli whoami
```

#### Login

```bash
# Device flow (recommended)
deployment-queue-cli login --org your-org

# With Personal Access Token
deployment-queue-cli login --org your-org --pat ghp_xxxxxxxxxxxx
```

#### Logout

```bash
deployment-queue-cli logout
```

#### List available organisations

```bash
deployment-queue-cli list-orgs
```

#### Switch organisation

```bash
deployment-queue-cli switch-org other-org
```

### Deployment Commands

#### List deployments

```bash
deployment-queue-cli list
deployment-queue-cli list --env production --status deployed
deployment-queue-cli list --provider gcp --trigger auto --limit 50
```

Options:
- `--env, -e`: Filter by environment
- `--status, -s`: Filter by status
- `--provider, -p`: Filter by provider
- `--trigger, -t`: Filter by trigger
- `--limit, -n`: Max results (default: 20)
- `--api-url`: Override API URL

#### Get deployment details

```bash
deployment-queue-cli get <deployment-id>
```

Options:
- `--api-url`: Override API URL

#### Get current deployment

```bash
deployment-queue-cli current my-service \
  --env production \
  --provider gcp \
  --account my-project-id \
  --region europe-west1
```

Options:
- `--env, -e`: Environment (required)
- `--provider, -p`: Provider - gcp/aws/azure (required)
- `--account, -a`: Cloud account ID (required)
- `--region, -r`: Region (required)
- `--cell`: Cell ID (optional)
- `--api-url`: Override API URL

#### View deployment history

```bash
deployment-queue-cli history my-service \
  --env production \
  --provider gcp \
  --account my-project-id \
  --region europe-west1 \
  --limit 20
```

Options:
- `--env, -e`: Environment (required)
- `--provider, -p`: Provider (required)
- `--account, -a`: Cloud account ID (required)
- `--region, -r`: Region (required)
- `--cell`: Cell ID (optional)
- `--limit, -n`: Max results (default: 10)
- `--api-url`: Override API URL

#### Update deployment status

```bash
deployment-queue-cli update-status my-service deployed \
  --env production \
  --provider gcp \
  --account my-project-id \
  --region europe-west1 \
  --notes "Deployment completed successfully"
```

Valid statuses: `scheduled`, `in_progress`, `deployed`, `failed`, `skipped`

Options:
- `--env, -e`: Environment (required)
- `--provider, -p`: Provider (required)
- `--account, -a`: Cloud account ID (required)
- `--region, -r`: Region (required)
- `--cell`: Cell ID (optional)
- `--notes`: Notes for the status update (optional)
- `--api-url`: Override API URL

#### Rollback deployment

```bash
# Rollback to previous version
deployment-queue-cli rollback my-service \
  --env production \
  --provider gcp \
  --account my-project-id \
  --region europe-west1

# Rollback to specific version
deployment-queue-cli rollback my-service \
  --env production \
  --provider gcp \
  --account my-project-id \
  --region europe-west1 \
  --version v1.2.0
```

Options:
- `--env, -e`: Environment (required)
- `--provider, -p`: Provider (required)
- `--account, -a`: Cloud account ID (required)
- `--region, -r`: Region (required)
- `--cell`: Cell ID (optional)
- `--version, -v`: Target version (default: previous)
- `--api-url`: Override API URL

## GitHub OAuth App Setup

To enable Device Flow authentication, create a GitHub OAuth App:

1. Go to GitHub Settings -> Developer settings -> OAuth Apps -> New OAuth App
2. Fill in:
   - Application name: `Deployment Queue CLI`
   - Homepage URL: Your documentation URL
   - Authorization callback URL: `https://github.com` (not used for device flow)
3. After creation, note the **Client ID** (this is public, not a secret)
4. Enable Device Flow: Check "Enable Device Flow" in the app settings
5. Set `DEPLOYMENT_QUEUE_CLI_GITHUB_CLIENT_ID` environment variable

No client secret is needed for device flow - only the public client ID.

## License

MIT
