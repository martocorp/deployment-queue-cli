"""CLI entry point and commands for the Deployment Queue CLI."""

import asyncio
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .auth import (
    clear_credentials,
    device_flow_login,
    get_stored_credentials,
    list_available_organisations,
    pat_login,
    switch_organisation,
)
from .client import DeploymentAPIClient, DeploymentAPIError
from .config import get_settings

app = typer.Typer(
    name="deployment-queue-cli",
    help="CLI for the Deployment Queue API",
    add_completion=False,
)
console = Console()


def get_client(api_url: Optional[str] = None) -> DeploymentAPIClient:
    """Get authenticated API client or exit with error."""
    creds = get_stored_credentials()
    if not creds:
        console.print("[red]Not authenticated. Run 'deployment-queue-cli login' first.[/red]")
        raise typer.Exit(1)
    return DeploymentAPIClient(creds, api_url)


def handle_api_error(e: DeploymentAPIError) -> None:
    """Handle API errors with user-friendly output."""
    if e.status_code == 401:
        console.print("[red]Authentication failed. Try 'deployment-queue-cli login' again.[/red]")
    elif e.status_code == 403:
        console.print(f"[red]Access denied: {e.detail}[/red]")
    elif e.status_code == 404:
        console.print(f"[yellow]Not found: {e.detail}[/yellow]")
    else:
        console.print(f"[red]API error ({e.status_code}): {e.detail}[/red]")
    raise typer.Exit(1)


# -----------------------------------------------------------------------------
# Auth Commands
# -----------------------------------------------------------------------------


@app.command()
def login(
    organisation: str = typer.Option(..., "--org", "-o", help="GitHub organisation"),
    pat: Optional[str] = typer.Option(None, "--pat", help="GitHub PAT (skips device flow)"),
) -> None:
    """
    Authenticate with the Deployment Queue API.

    Uses GitHub Device Flow by default (opens browser).
    Alternatively, provide a PAT with --pat.
    """

    async def _login() -> None:
        if pat:
            creds = await pat_login(pat, organisation)
        else:
            creds = await device_flow_login(organisation)
        console.print(f"[green]Logged in as {creds.username} ({creds.organisation})[/green]")

    try:
        asyncio.run(_login())
    except ValueError as e:
        console.print(f"[red]Login failed: {e}[/red]")
        raise typer.Exit(1)
    except (TimeoutError, PermissionError) as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@app.command()
def logout() -> None:
    """Clear stored credentials."""
    clear_credentials()
    console.print("[green]Logged out[/green]")


@app.command()
def whoami() -> None:
    """Show current authentication status."""
    creds = get_stored_credentials()
    settings = get_settings()
    if creds:
        console.print(
            Panel(
                f"[bold]Username:[/bold] {creds.username}\n"
                f"[bold]Organisation:[/bold] {creds.organisation}\n"
                f"[bold]API URL:[/bold] {settings.api_url}",
                title="Current Session",
                box=box.ROUNDED,
            )
        )
    else:
        console.print("[yellow]Not logged in. Run 'deployment-queue-cli login' first.[/yellow]")


@app.command("switch-org")
def switch_org(
    organisation: str = typer.Argument(..., help="Organisation to switch to"),
) -> None:
    """Switch to a different organisation."""

    async def _switch() -> None:
        creds = await switch_organisation(organisation)
        console.print(f"[green]Switched to {creds.organisation}[/green]")

    try:
        asyncio.run(_switch())
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


@app.command("list-orgs")
def list_orgs() -> None:
    """List available organisations."""

    async def _list() -> list[str]:
        return await list_available_organisations()

    try:
        orgs = asyncio.run(_list())
        console.print("[bold]Available organisations:[/bold]")
        for org in orgs:
            console.print(f"  - {org}")
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


# -----------------------------------------------------------------------------
# Deployment Commands
# -----------------------------------------------------------------------------


@app.command()
def create(
    name: str = typer.Argument(..., help="Component name"),
    version: str = typer.Argument(..., help="Version to deploy"),
    deployment_type: str = typer.Option(
        ..., "--type", "-T", help="Deployment type (k8s/terraform/data_pipeline)"
    ),
    provider: str = typer.Option(..., "--provider", "-p", help="Provider (gcp/aws/azure)"),
    cloud_account_id: Optional[str] = typer.Option(
        None, "--account", "-a", help="Cloud account ID"
    ),
    region: Optional[str] = typer.Option(None, "--region", "-r", help="Region"),
    cell_id: Optional[str] = typer.Option(None, "--cell", help="Cell ID"),
    auto: bool = typer.Option(True, "--auto/--no-auto", help="Auto-deploy when ready"),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Deployment description"
    ),
    notes: Optional[str] = typer.Option(None, "--notes", help="Deployment notes"),
    commit_sha: Optional[str] = typer.Option(None, "--commit", help="Git commit SHA"),
    build_uri: Optional[str] = typer.Option(None, "--build-uri", help="Build URI"),
    pipeline_extra_params: Optional[str] = typer.Option(
        None, "--pipeline-params", help="Pipeline extra params (JSON string)"
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    api_url: Optional[str] = typer.Option(None, "--api-url"),
) -> None:
    """Create a new deployment."""
    client = get_client(api_url)

    deployment: dict = {
        "name": name,
        "version": version,
        "type": deployment_type,
        "provider": provider,
        "auto": auto,
    }
    if cloud_account_id:
        deployment["cloud_account_id"] = cloud_account_id
    if region:
        deployment["region"] = region
    if cell_id:
        deployment["cell"] = cell_id
    if description:
        deployment["description"] = description
    if notes:
        deployment["notes"] = notes
    if commit_sha:
        deployment["commit_sha"] = commit_sha
    if build_uri:
        deployment["build_uri"] = build_uri
    if pipeline_extra_params:
        deployment["pipeline_extra_params"] = pipeline_extra_params

    # Display deployment details
    console.print("=" * 50)
    console.print("[bold]Create Deployment[/bold]")
    console.print("=" * 50)
    console.print(f"[bold]Name[/bold]                  : {name}")
    console.print(f"[bold]Version[/bold]               : {version}")
    console.print(f"[bold]Type[/bold]                  : {deployment_type}")
    console.print(f"[bold]Provider[/bold]              : {provider}")
    console.print(f"[bold]Cloud Account ID[/bold]      : {cloud_account_id or 'N/A'}")
    console.print(f"[bold]Region[/bold]                : {region or 'N/A'}")
    console.print(f"[bold]Cell[/bold]                  : {cell_id or 'N/A'}")
    console.print(f"[bold]Auto Deploy[/bold]           : {auto}")
    console.print(f"[bold]Description[/bold]           : {description or 'N/A'}")
    console.print(f"[bold]Commit SHA[/bold]            : {commit_sha or 'N/A'}")
    console.print(f"[bold]Build URI[/bold]             : {build_uri or 'N/A'}")
    console.print(f"[bold]Pipeline Extra Params[/bold] : {pipeline_extra_params or 'N/A'}")
    console.print("=" * 50)

    if not yes:
        confirm = typer.confirm("Do you want to continue?")
        if not confirm:
            console.print("[yellow]Aborted[/yellow]")
            raise typer.Exit(0)

    async def _create() -> dict:
        return await client.create_deployment(deployment)

    try:
        d = asyncio.run(_create())
    except DeploymentAPIError as e:
        handle_api_error(e)

    console.print(f"[green]Created deployment: {d['name']} @ {d['version']}[/green]")
    console.print(f"  ID: {d['id']}")
    console.print(f"  Status: {d['status']}")


@app.command("list")
def list_deployments(
    all_deployments: bool = typer.Option(
        False, "--all", "-a", help="List all deployments (default: scheduled only)"
    ),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Filter by provider"),
    trigger: Optional[str] = typer.Option(None, "--trigger", "-t", help="Filter by trigger"),
    limit: int = typer.Option(20, "--limit", "-n", help="Max results"),
    sort_by_updated: bool = typer.Option(
        False, "--sort-updated", "-u", help="Sort by updated timestamp (newest first)"
    ),
    api_url: Optional[str] = typer.Option(None, "--api-url", help="Override API URL"),
) -> None:
    """List deployments (scheduled only by default, use --all for all statuses)."""
    client = get_client(api_url)

    # Default to scheduled status unless --all is specified or a specific status is given
    effective_status = status
    if not all_deployments and status is None:
        effective_status = "scheduled"

    async def _list() -> list[dict]:
        return await client.list_deployments(effective_status, provider, trigger, limit)

    try:
        deployments = asyncio.run(_list())
    except DeploymentAPIError as e:
        handle_api_error(e)

    if not deployments:
        console.print("[yellow]No deployments found[/yellow]")
        return

    # Sort by updated_at if requested
    if sort_by_updated:
        deployments.sort(
            key=lambda d: d.get("updated_at", d.get("created_at", "")),
            reverse=True
        )

    table = Table(title="Deployments", box=box.ROUNDED)
    table.add_column("ID")
    table.add_column("Name", style="bold")
    table.add_column("Version")
    table.add_column("Status")
    table.add_column("Updated")
    table.add_column("Provider")
    table.add_column("Account")
    table.add_column("Region")
    table.add_column("Cell")

    status_styles = {
        "deployed": "green",
        "failed": "red",
        "in_progress": "yellow",
        "scheduled": "blue",
        "skipped": "dim",
    }

    for d in deployments:
        status = d.get("status", "")
        style = status_styles.get(status, "white")
        updated_at = d.get("updated_at", d.get("created_at", ""))
        table.add_row(
            d["id"],
            d["name"],
            d["version"],
            f"[{style}]{status}[/{style}]",
            updated_at[:19].replace("T", " ") if updated_at else "",
            d.get("provider", ""),
            d.get("cloud_account_id", ""),
            d.get("region", ""),
            d.get("cell", "") or d.get("cell_id", ""),
        )

    console.print(table)


@app.command()
def rollback(
    deployment_id: str = typer.Argument(..., help="Deployment ID to rollback"),
    target_version: Optional[str] = typer.Option(
        None, "--version", "-v", help="Target version (default: previous)"
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    api_url: Optional[str] = typer.Option(None, "--api-url"),
) -> None:
    """Create rollback deployment from an existing deployment ID."""
    client = get_client(api_url)

    async def _get() -> Optional[dict]:
        return await client.get_deployment(deployment_id)

    async def _rollback() -> dict:
        return await client.rollback_by_id(deployment_id, target_version)

    # Fetch deployment details first
    try:
        d = asyncio.run(_get())
    except DeploymentAPIError as e:
        handle_api_error(e)

    if not d:
        console.print(f"[red]Deployment not found: {deployment_id}[/red]")
        raise typer.Exit(1)

    # Display deployment details
    console.print("=" * 50)
    console.print("[bold]Rollback Deployment[/bold]")
    console.print("=" * 50)
    console.print(f"[bold]Deployment ID[/bold]         : {d['id']}")
    console.print(f"[bold]Provider[/bold]              : {d.get('provider', 'N/A')}")
    console.print(f"[bold]Region[/bold]                : {d.get('region', 'N/A')}")
    console.print(f"[bold]Cloud Account ID[/bold]      : {d.get('cloud_account_id', 'N/A')}")
    console.print(f"[bold]Cell[/bold]                  : {d.get('cell', 'N/A') or 'N/A'}")
    console.print(f"[bold]Type[/bold]                  : {d.get('type', 'N/A')}")
    console.print(f"[bold]Name[/bold]                  : {d['name']}")
    console.print(f"[bold]Version[/bold]               : {d['version']}")
    console.print(f"[bold]Status[/bold]                : {d['status']}")
    if target_version:
        console.print(f"[bold]Target Version[/bold]        : {target_version}")
    console.print("=" * 50)

    if not yes:
        confirm = typer.confirm("Do you want to continue?")
        if not confirm:
            console.print("[yellow]Aborted[/yellow]")
            raise typer.Exit(0)

    try:
        result = asyncio.run(_rollback())
    except DeploymentAPIError as e:
        handle_api_error(e)

    console.print(f"[green]Rollback created: {result['name']} -> {result['version']}[/green]")
    console.print(f"  ID: {result['id']}")
    console.print(f"  Source: {result.get('source_deployment_id', 'N/A')}")
    console.print(f"  Rollback from: {result.get('rollback_from_deployment_id', 'N/A')}")


@app.command()
def release(
    deployment_id: str = typer.Argument(..., help="Deployment ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    api_url: Optional[str] = typer.Option(None, "--api-url"),
) -> None:
    """Release a deployment (set status to in_progress)."""
    client = get_client(api_url)

    async def _get() -> Optional[dict]:
        return await client.get_deployment(deployment_id)

    async def _release() -> dict:
        return await client.update_deployment(deployment_id, {"status": "in_progress"})

    try:
        d = asyncio.run(_get())
    except DeploymentAPIError as e:
        handle_api_error(e)

    if not d:
        console.print(f"[red]Deployment not found: {deployment_id}[/red]")
        raise typer.Exit(1)

    # Display deployment details
    console.print("=" * 50)
    console.print("[bold]Deployment Details[/bold]")
    console.print("=" * 50)
    console.print(f"[bold]Deployment ID[/bold]         : {d['id']}")
    console.print(f"[bold]Provider[/bold]              : {d.get('provider', 'N/A')}")
    console.print(f"[bold]Region[/bold]                : {d.get('region', 'N/A')}")
    console.print(f"[bold]Cloud Account ID[/bold]      : {d.get('cloud_account_id', 'N/A')}")
    console.print(f"[bold]Cell[/bold]                  : {d.get('cell', 'N/A') or 'N/A'}")
    console.print(f"[bold]Type[/bold]                  : {d.get('type', 'N/A')}")
    console.print(f"[bold]Name[/bold]                  : {d['name']}")
    console.print(f"[bold]Version[/bold]               : {d['version']}")
    console.print(f"[bold]Description[/bold]           : {d.get('description', 'N/A') or 'N/A'}")
    console.print(f"[bold]Status[/bold]                : {d['status']}")
    console.print(f"[bold]Commit SHA[/bold]            : {d.get('commit_sha', 'N/A') or 'N/A'}")
    pipeline_params = d.get('pipeline_extra_params', 'N/A') or 'N/A'
    console.print(f"[bold]Pipeline Extra Params[/bold] : {pipeline_params}")
    console.print("=" * 50)

    if d["status"] != "scheduled":
        console.print(
            f"[yellow]Warning: Deployment status is '{d['status']}', expected 'scheduled'[/yellow]"
        )

    if not yes:
        confirm = typer.confirm("Do you want to continue?")
        if not confirm:
            console.print("[yellow]Aborted[/yellow]")
            raise typer.Exit(0)

    try:
        updated = asyncio.run(_release())
    except DeploymentAPIError as e:
        handle_api_error(e)

    console.print(f"[green]Deployment released: {updated['name']} @ {updated['version']}[/green]")
    console.print(f"  Status: {updated['status']}")


@app.command("update-status")
def update_status(
    deployment_id: str = typer.Argument(..., help="Deployment ID"),
    status: str = typer.Argument(
        ..., help="New status (scheduled/in_progress/deployed/failed/skipped)"
    ),
    api_url: Optional[str] = typer.Option(None, "--api-url"),
) -> None:
    """Update deployment status."""
    valid_statuses = ["scheduled", "in_progress", "deployed", "failed", "skipped"]
    if status not in valid_statuses:
        console.print(f"[red]Invalid status: {status}[/red]")
        console.print(f"[yellow]Valid statuses: {', '.join(valid_statuses)}[/yellow]")
        raise typer.Exit(1)

    client = get_client(api_url)

    async def _update() -> dict:
        return await client.update_deployment(deployment_id, {"status": status})

    try:
        d = asyncio.run(_update())
    except DeploymentAPIError as e:
        handle_api_error(e)

    console.print(f"[green]Updated deployment: {d['name']} @ {d['version']}[/green]")
    console.print(f"  Status: {d['status']}")


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
