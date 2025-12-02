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
        environment: Optional[str] = None,
        status: Optional[str] = None,
        provider: Optional[str] = None,
        trigger: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        """List deployments with optional filters."""
        params: dict[str, str | int] = {"limit": limit}
        if environment:
            params["environment"] = environment
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

    async def get_deployment(self, deployment_id: str) -> dict:
        """Get deployment by ID."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.api_url}/v1/deployments/{deployment_id}",
                headers=self._headers(),
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

    def _taxonomy_params(
        self,
        name: str,
        environment: str,
        provider: str,
        cloud_account_id: str,
        region: str,
        cell_id: Optional[str] = None,
    ) -> dict[str, str]:
        """Build taxonomy query parameters."""
        params = {
            "name": name,
            "environment": environment,
            "provider": provider,
            "cloud_account_id": cloud_account_id,
            "region": region,
        }
        if cell_id:
            params["cell_id"] = cell_id
        return params

    async def get_current(
        self,
        name: str,
        environment: str,
        provider: str,
        cloud_account_id: str,
        region: str,
        cell_id: Optional[str] = None,
    ) -> Optional[dict]:
        """Get current deployment for a component."""
        params = self._taxonomy_params(
            name, environment, provider, cloud_account_id, region, cell_id
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.api_url}/v1/deployments/current",
                headers=self._headers(),
                params=params,
            )
            if response.status_code == 404:
                return None
            return self._handle_response(response)

    async def get_history(
        self,
        name: str,
        environment: str,
        provider: str,
        cloud_account_id: str,
        region: str,
        cell_id: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        """Get deployment history for a component."""
        params: dict[str, Any] = self._taxonomy_params(
            name, environment, provider, cloud_account_id, region, cell_id
        )
        params["limit"] = limit

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.api_url}/v1/deployments/history",
                headers=self._headers(),
                params=params,
            )
            return self._handle_response(response)

    async def update_status(
        self,
        name: str,
        environment: str,
        provider: str,
        cloud_account_id: str,
        region: str,
        new_status: str,
        cell_id: Optional[str] = None,
        notes: Optional[str] = None,
        deployment_uri: Optional[str] = None,
    ) -> dict:
        """Update deployment status by taxonomy."""
        params: dict[str, str] = self._taxonomy_params(
            name, environment, provider, cloud_account_id, region, cell_id
        )
        params["new_status"] = new_status
        if notes:
            params["notes"] = notes
        if deployment_uri:
            params["deployment_uri"] = deployment_uri

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.patch(
                f"{self.api_url}/v1/deployments/current/status",
                headers=self._headers(),
                params=params,
            )
            return self._handle_response(response)

    async def rollback(
        self,
        name: str,
        environment: str,
        provider: str,
        cloud_account_id: str,
        region: str,
        cell_id: Optional[str] = None,
        target_version: Optional[str] = None,
    ) -> dict:
        """Create rollback deployment."""
        params = self._taxonomy_params(
            name, environment, provider, cloud_account_id, region, cell_id
        )
        if target_version:
            params["target_version"] = target_version

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.api_url}/v1/deployments/rollback",
                headers=self._headers(),
                params=params,
            )
            return self._handle_response(response)
