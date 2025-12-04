"""API client for the Deployment Queue API."""

from typing import Any, Optional

import httpx

from .auth import Credentials
from .config import get_settings


class DeploymentAPIError(Exception):
    """Exception for API errors."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API error {status_code}: {detail}")


class DeploymentAPIClient:
    """Client for the Deployment Queue API."""

    def __init__(self, credentials: Credentials, api_url: Optional[str] = None):
        self.credentials = credentials
        settings = get_settings()
        self.api_url = (api_url or settings.api_url).rstrip("/")

    def _headers(self) -> dict[str, str]:
        """Build request headers with auth."""
        return {
            "Authorization": f"Bearer {self.credentials.github_token}",
            "X-Organisation": self.credentials.organisation,
            "Content-Type": "application/json",
        }

    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle API response, raising on errors."""
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise DeploymentAPIError(response.status_code, detail)

        if response.status_code == 204:
            return {}

        return response.json()

    # -------------------------------------------------------------------------
    # Deployments
    # -------------------------------------------------------------------------

    async def list_deployments(
        self,
        status: Optional[str] = None,
        provider: Optional[str] = None,
        trigger: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        """List deployments with optional filters."""
        params: dict[str, str | int] = {"limit": limit}
        if status:
            params["status"] = status
        if provider:
            params["provider"] = provider
        if trigger:
            params["trigger"] = trigger

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.api_url}/v1/deployments",
                headers=self._headers(),
                params=params,
            )
            return self._handle_response(response)

    async def create_deployment(self, deployment: dict) -> dict:
        """Create a new deployment."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.api_url}/v1/deployments",
                headers=self._headers(),
                json=deployment,
            )
            return self._handle_response(response)

    async def update_deployment(self, deployment_id: str, update: dict) -> dict:
        """Update deployment by ID."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.patch(
                f"{self.api_url}/v1/deployments/{deployment_id}",
                headers=self._headers(),
                json=update,
            )
            return self._handle_response(response)

    # -------------------------------------------------------------------------
    # Taxonomy-based operations
    # -------------------------------------------------------------------------

    async def rollback(
        self,
        name: str,
        provider: str,
        cloud_account_id: str,
        region: str,
        cell: Optional[str] = None,
        target_version: Optional[str] = None,
    ) -> dict:
        """Create rollback deployment."""
        params: dict[str, str] = {
            "name": name,
            "provider": provider,
            "cloud_account_id": cloud_account_id,
            "region": region,
        }
        if cell:
            params["cell"] = cell
        if target_version:
            params["target_version"] = target_version

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.api_url}/v1/deployments/rollback",
                headers=self._headers(),
                params=params,
            )
            return self._handle_response(response)
