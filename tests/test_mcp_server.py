"""Tests for MCP server."""

from unittest.mock import AsyncMock, patch

import pytest

from deployment_queue_cli.auth import Credentials
from deployment_queue_cli.client import DeploymentAPIError
from deployment_queue_cli.mcp_server import (
    TOOLS,
    create_server,
    handle_create_deployment,
    handle_get_deployment,
    handle_list_deployments,
    handle_release_deployment,
    handle_rollback_deployment,
    handle_update_deployment_status,
)


class TestToolDefinitions:
    """Tests for tool definitions."""

    def test_tools_defined(self) -> None:
        """All expected tools are defined."""
        tool_names = {t.name for t in TOOLS}
        expected = {
            "list_deployments",
            "create_deployment",
            "get_deployment",
            "release_deployment",
            "update_deployment_status",
            "rollback_deployment",
        }
        assert tool_names == expected

    def test_create_deployment_required_fields(self) -> None:
        """Create deployment has required fields."""
        tool = next(t for t in TOOLS if t.name == "create_deployment")
        assert tool.inputSchema["required"] == ["name", "version", "type", "provider"]

    def test_rollback_deployment_required_fields(self) -> None:
        """Rollback deployment has required fields."""
        tool = next(t for t in TOOLS if t.name == "rollback_deployment")
        assert tool.inputSchema["required"] == ["deployment_id"]


class TestListDeployments:
    """Tests for list_deployments handler."""

    @pytest.mark.asyncio
    async def test_list_deployments_success(
        self, mock_credentials: Credentials, mock_deployment_list: list[dict]
    ) -> None:
        """List deployments returns formatted output."""
        with (
            patch(
                "deployment_queue_cli.mcp_server.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.mcp_server.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.list_deployments = AsyncMock(return_value=mock_deployment_list)
            mock_client_class.return_value = mock_client

            result = await handle_list_deployments({"limit": 20})

            assert "Deployments:" in result
            assert "test-service" in result
            assert "1.0.0" in result

    @pytest.mark.asyncio
    async def test_list_deployments_empty(self, mock_credentials: Credentials) -> None:
        """List deployments returns message when empty."""
        with (
            patch(
                "deployment_queue_cli.mcp_server.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.mcp_server.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.list_deployments = AsyncMock(return_value=[])
            mock_client_class.return_value = mock_client

            result = await handle_list_deployments({})

            assert result == "No deployments found"


class TestCreateDeployment:
    """Tests for create_deployment handler."""

    @pytest.mark.asyncio
    async def test_create_deployment_success(
        self, mock_credentials: Credentials, mock_deployment: dict
    ) -> None:
        """Create deployment returns success message."""
        with (
            patch(
                "deployment_queue_cli.mcp_server.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.mcp_server.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.create_deployment = AsyncMock(return_value=mock_deployment)
            mock_client_class.return_value = mock_client

            result = await handle_create_deployment({
                "name": "test-service",
                "version": "1.0.0",
                "type": "k8s",
                "provider": "gcp",
            })

            assert "Created deployment" in result
            assert "test-service" in result
            assert mock_deployment["id"] in result

    @pytest.mark.asyncio
    async def test_create_deployment_with_optional_fields(
        self, mock_credentials: Credentials, mock_deployment: dict
    ) -> None:
        """Create deployment includes optional fields."""
        with (
            patch(
                "deployment_queue_cli.mcp_server.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.mcp_server.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.create_deployment = AsyncMock(return_value=mock_deployment)
            mock_client_class.return_value = mock_client

            await handle_create_deployment({
                "name": "test-service",
                "version": "1.0.0",
                "type": "k8s",
                "provider": "gcp",
                "region": "us-central1",
                "cloud_account_id": "project-123",
                "description": "Test deployment",
            })

            call_args = mock_client.create_deployment.call_args[0][0]
            assert call_args["region"] == "us-central1"
            assert call_args["cloud_account_id"] == "project-123"
            assert call_args["description"] == "Test deployment"


class TestGetDeployment:
    """Tests for get_deployment handler."""

    @pytest.mark.asyncio
    async def test_get_deployment_success(
        self, mock_credentials: Credentials, mock_deployment: dict
    ) -> None:
        """Get deployment returns formatted details."""
        with (
            patch(
                "deployment_queue_cli.mcp_server.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.mcp_server.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.get_deployment = AsyncMock(return_value=mock_deployment)
            mock_client_class.return_value = mock_client

            result = await handle_get_deployment({"deployment_id": "test-uuid"})

            assert "Deployment Details:" in result
            assert mock_deployment["id"] in result
            assert mock_deployment["name"] in result
            assert mock_deployment["version"] in result

    @pytest.mark.asyncio
    async def test_get_deployment_not_found(self, mock_credentials: Credentials) -> None:
        """Get deployment returns not found message."""
        with (
            patch(
                "deployment_queue_cli.mcp_server.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.mcp_server.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.get_deployment = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await handle_get_deployment({"deployment_id": "nonexistent"})

            assert "not found" in result.lower()


class TestReleaseDeployment:
    """Tests for release_deployment handler."""

    @pytest.mark.asyncio
    async def test_release_deployment_success(
        self, mock_credentials: Credentials, mock_deployment: dict
    ) -> None:
        """Release deployment returns success message."""
        released = {**mock_deployment, "status": "in_progress"}

        with (
            patch(
                "deployment_queue_cli.mcp_server.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.mcp_server.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.get_deployment = AsyncMock(return_value=mock_deployment)
            mock_client.update_deployment = AsyncMock(return_value=released)
            mock_client_class.return_value = mock_client

            result = await handle_release_deployment({"deployment_id": "test-uuid"})

            assert "Released deployment" in result
            assert "in_progress" in result

    @pytest.mark.asyncio
    async def test_release_deployment_not_found(self, mock_credentials: Credentials) -> None:
        """Release deployment returns not found when deployment missing."""
        with (
            patch(
                "deployment_queue_cli.mcp_server.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.mcp_server.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.get_deployment = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await handle_release_deployment({"deployment_id": "nonexistent"})

            assert "not found" in result.lower()


class TestUpdateDeploymentStatus:
    """Tests for update_deployment_status handler."""

    @pytest.mark.asyncio
    async def test_update_status_success(
        self, mock_credentials: Credentials, mock_deployment: dict
    ) -> None:
        """Update status returns success message."""
        updated = {**mock_deployment, "status": "deployed"}

        with (
            patch(
                "deployment_queue_cli.mcp_server.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.mcp_server.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.update_deployment = AsyncMock(return_value=updated)
            mock_client_class.return_value = mock_client

            result = await handle_update_deployment_status({
                "deployment_id": "test-uuid",
                "status": "deployed",
            })

            assert "Updated deployment" in result
            assert "deployed" in result

    @pytest.mark.asyncio
    async def test_update_status_invalid(self) -> None:
        """Update status returns error for invalid status."""
        result = await handle_update_deployment_status({
            "deployment_id": "test-uuid",
            "status": "invalid_status",
        })

        assert "Invalid status" in result
        assert "scheduled" in result  # Shows valid options


class TestRollbackDeployment:
    """Tests for rollback_deployment handler."""

    @pytest.mark.asyncio
    async def test_rollback_success(
        self, mock_credentials: Credentials, mock_deployment: dict
    ) -> None:
        """Rollback returns success message."""
        rollback = {
            **mock_deployment,
            "trigger": "rollback",
            "source_deployment_id": "previous-uuid",
            "rollback_from_deployment_id": "current-uuid",
        }

        with (
            patch(
                "deployment_queue_cli.mcp_server.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.mcp_server.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.rollback_by_id = AsyncMock(return_value=rollback)
            mock_client_class.return_value = mock_client

            result = await handle_rollback_deployment({
                "deployment_id": "test-deployment-uuid",
            })

            assert "Rollback created" in result
            assert "previous-uuid" in result


class TestMCPServer:
    """Tests for MCP server creation."""

    def test_create_server(self) -> None:
        """Server is created successfully."""
        server = create_server()
        assert server is not None
        assert server.name == "deployment-queue"

    def test_tools_count(self) -> None:
        """Correct number of tools are defined."""
        assert len(TOOLS) == 6

    @pytest.mark.asyncio
    async def test_handler_api_error(
        self, mock_credentials: Credentials
    ) -> None:
        """Handler raises API errors correctly."""
        with (
            patch(
                "deployment_queue_cli.mcp_server.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.mcp_server.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = AsyncMock()
            mock_client.list_deployments = AsyncMock(
                side_effect=DeploymentAPIError(500, "Server error")
            )
            mock_client_class.return_value = mock_client

            with pytest.raises(DeploymentAPIError) as exc:
                await handle_list_deployments({})

            assert exc.value.status_code == 500
            assert "Server error" in exc.value.detail

    @pytest.mark.asyncio
    async def test_handler_not_authenticated(self) -> None:
        """Handler raises error when not authenticated."""
        with patch(
            "deployment_queue_cli.mcp_server.get_stored_credentials",
            return_value=None,
        ):
            with pytest.raises(ValueError) as exc:
                await handle_list_deployments({})

            assert "Not authenticated" in str(exc.value)
