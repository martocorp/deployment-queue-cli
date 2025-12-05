"""MCP server for the Deployment Queue API."""

import asyncio
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .auth import get_stored_credentials
from .client import DeploymentAPIClient, DeploymentAPIError


def get_client(api_url: Optional[str] = None) -> DeploymentAPIClient:
    """Get authenticated API client or raise error."""
    creds = get_stored_credentials()
    if not creds:
        raise ValueError("Not authenticated. Run 'deployment-queue-cli login' first.")
    return DeploymentAPIClient(creds, api_url)


# Tool definitions
TOOLS = [
    Tool(
        name="list_deployments",
        description="List deployments with optional filters",
        inputSchema={
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter by status",
                },
                "provider": {
                    "type": "string",
                    "description": "Filter by provider (gcp/aws/azure)",
                },
                "trigger": {
                    "type": "string",
                    "description": "Filter by trigger (auto/manual/rollback)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 20)",
                    "default": 20,
                },
            },
        },
    ),
    Tool(
        name="create_deployment",
        description="Create a new deployment",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Component name",
                },
                "version": {
                    "type": "string",
                    "description": "Version to deploy",
                },
                "type": {
                    "type": "string",
                    "description": "Deployment type (k8s/terraform/data_pipeline)",
                },
                "provider": {
                    "type": "string",
                    "description": "Provider (gcp/aws/azure)",
                },
                "cloud_account_id": {
                    "type": "string",
                    "description": "Cloud account ID",
                },
                "region": {
                    "type": "string",
                    "description": "Cloud region",
                },
                "cell": {
                    "type": "string",
                    "description": "Cell ID",
                },
                "auto": {
                    "type": "boolean",
                    "description": "Auto-deploy when ready (default: true)",
                    "default": True,
                },
                "description": {
                    "type": "string",
                    "description": "Deployment description",
                },
                "notes": {
                    "type": "string",
                    "description": "Deployment notes",
                },
                "commit_sha": {
                    "type": "string",
                    "description": "Git commit SHA",
                },
                "build_uri": {
                    "type": "string",
                    "description": "Build URI",
                },
                "pipeline_extra_params": {
                    "type": "string",
                    "description": "Pipeline extra params (JSON string)",
                },
            },
            "required": ["name", "version", "type", "provider"],
        },
    ),
    Tool(
        name="get_deployment",
        description="Get a deployment by ID",
        inputSchema={
            "type": "object",
            "properties": {
                "deployment_id": {
                    "type": "string",
                    "description": "Deployment ID",
                },
            },
            "required": ["deployment_id"],
        },
    ),
    Tool(
        name="release_deployment",
        description="Release a deployment (set status to in_progress)",
        inputSchema={
            "type": "object",
            "properties": {
                "deployment_id": {
                    "type": "string",
                    "description": "Deployment ID",
                },
            },
            "required": ["deployment_id"],
        },
    ),
    Tool(
        name="update_deployment_status",
        description="Update deployment status",
        inputSchema={
            "type": "object",
            "properties": {
                "deployment_id": {
                    "type": "string",
                    "description": "Deployment ID",
                },
                "status": {
                    "type": "string",
                    "description": "New status",
                },
            },
            "required": ["deployment_id", "status"],
        },
    ),
    Tool(
        name="rollback_deployment",
        description="Create a rollback deployment from an existing deployment ID",
        inputSchema={
            "type": "object",
            "properties": {
                "deployment_id": {
                    "type": "string",
                    "description": "Deployment ID to rollback",
                },
                "target_version": {
                    "type": "string",
                    "description": "Target version to rollback to (default: previous)",
                },
            },
            "required": ["deployment_id"],
        },
    ),
]


async def handle_list_deployments(arguments: dict) -> str:
    """Handle list_deployments tool call."""
    client = get_client()
    deployments = await client.list_deployments(
        status=arguments.get("status"),
        provider=arguments.get("provider"),
        trigger=arguments.get("trigger"),
        limit=arguments.get("limit", 20),
    )
    if not deployments:
        return "No deployments found"

    lines = ["Deployments:"]
    for d in deployments:
        lines.append(
            f"- {d['id']}: {d['name']} @ {d['version']} "
            f"[{d['status']}] ({d.get('provider', 'N/A')})"
        )
    return "\n".join(lines)


async def handle_create_deployment(arguments: dict) -> str:
    """Handle create_deployment tool call."""
    client = get_client()

    deployment: dict = {
        "name": arguments["name"],
        "version": arguments["version"],
        "type": arguments["type"],
        "provider": arguments["provider"],
        "auto": arguments.get("auto", True),
    }

    optional_fields = [
        "cloud_account_id", "region", "cell", "description",
        "notes", "commit_sha", "build_uri", "pipeline_extra_params"
    ]
    for field in optional_fields:
        if arguments.get(field):
            deployment[field] = arguments[field]

    result = await client.create_deployment(deployment)
    return (
        f"Created deployment: {result['name']} @ {result['version']}\n"
        f"ID: {result['id']}\n"
        f"Status: {result['status']}"
    )


async def handle_get_deployment(arguments: dict) -> str:
    """Handle get_deployment tool call."""
    client = get_client()
    deployment = await client.get_deployment(arguments["deployment_id"])

    if not deployment:
        return f"Deployment not found: {arguments['deployment_id']}"

    lines = [
        "Deployment Details:",
        f"  ID: {deployment['id']}",
        f"  Name: {deployment['name']}",
        f"  Version: {deployment['version']}",
        f"  Status: {deployment['status']}",
        f"  Type: {deployment.get('type', 'N/A')}",
        f"  Provider: {deployment.get('provider', 'N/A')}",
        f"  Region: {deployment.get('region', 'N/A')}",
        f"  Cloud Account: {deployment.get('cloud_account_id', 'N/A')}",
        f"  Cell: {deployment.get('cell', 'N/A') or 'N/A'}",
        f"  Created: {deployment.get('created_at', 'N/A')}",
    ]
    return "\n".join(lines)


async def handle_release_deployment(arguments: dict) -> str:
    """Handle release_deployment tool call."""
    client = get_client()
    deployment_id = arguments["deployment_id"]

    # First get the deployment to show details
    deployment = await client.get_deployment(deployment_id)
    if not deployment:
        return f"Deployment not found: {deployment_id}"

    # Update status to in_progress
    result = await client.update_deployment(deployment_id, {"status": "in_progress"})
    return (
        f"Released deployment: {result['name']} @ {result['version']}\n"
        f"ID: {result['id']}\n"
        f"Status: {result['status']}"
    )


async def handle_update_deployment_status(arguments: dict) -> str:
    """Handle update_deployment_status tool call."""
    valid_statuses = ["scheduled", "in_progress", "deployed", "failed", "skipped"]
    status = arguments["status"]

    if status not in valid_statuses:
        return f"Invalid status: {status}. Valid: {', '.join(valid_statuses)}"

    client = get_client()
    result = await client.update_deployment(
        arguments["deployment_id"],
        {"status": status}
    )
    return (
        f"Updated deployment: {result['name']} @ {result['version']}\n"
        f"ID: {result['id']}\n"
        f"Status: {result['status']}"
    )


async def handle_rollback_deployment(arguments: dict) -> str:
    """Handle rollback_deployment tool call."""
    client = get_client()
    result = await client.rollback_by_id(
        deployment_id=arguments["deployment_id"],
        target_version=arguments.get("target_version"),
    )
    return (
        f"Rollback created: {result['name']} -> {result['version']}\n"
        f"ID: {result['id']}\n"
        f"Source: {result.get('source_deployment_id', 'N/A')}\n"
        f"Rollback from: {result.get('rollback_from_deployment_id', 'N/A')}"
    )


# Tool handlers mapping
TOOL_HANDLERS = {
    "list_deployments": handle_list_deployments,
    "create_deployment": handle_create_deployment,
    "get_deployment": handle_get_deployment,
    "release_deployment": handle_release_deployment,
    "update_deployment_status": handle_update_deployment_status,
    "rollback_deployment": handle_rollback_deployment,
}


def create_server() -> Server:
    """Create and configure the MCP server."""
    server = Server("deployment-queue")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tools."""
        return TOOLS

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Handle tool calls."""
        handler = TOOL_HANDLERS.get(name)
        if not handler:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        try:
            result = await handler(arguments)
            return [TextContent(type="text", text=result)]
        except DeploymentAPIError as e:
            return [TextContent(type="text", text=f"API error ({e.status_code}): {e.detail}")]
        except ValueError as e:
            return [TextContent(type="text", text=str(e))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {e}")]

    return server


async def run_server() -> None:
    """Run the MCP server."""
    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
    """Main entry point for the MCP server."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
