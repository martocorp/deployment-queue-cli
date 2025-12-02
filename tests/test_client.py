"""Tests for the API client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from deployment_queue_cli.auth import Credentials
from deployment_queue_cli.client import DeploymentAPIClient, DeploymentAPIError


class TestDeploymentAPIError:
    """Tests for DeploymentAPIError."""

    def test_error_message(self) -> None:
        """Error includes status code and detail."""
        error = DeploymentAPIError(404, "Not found")
        assert error.status_code == 404
        assert error.detail == "Not found"
        assert "404" in str(error)
        assert "Not found" in str(error)


class TestDeploymentAPIClient:
    """Tests for DeploymentAPIClient."""

    @pytest.fixture
    def client(self, mock_credentials: Credentials) -> DeploymentAPIClient:
        """Create a client for testing."""
        return DeploymentAPIClient(mock_credentials, api_url="https://api.test.com")

    def test_client_initialization(self, mock_credentials: Credentials) -> None:
        """Client initializes with credentials and API URL."""
        client = DeploymentAPIClient(mock_credentials, api_url="https://api.test.com/")
        assert client.credentials == mock_credentials
        assert client.api_url == "https://api.test.com"  # Trailing slash stripped

    def test_client_default_api_url(self, mock_credentials: Credentials) -> None:
        """Client uses default API URL from settings."""
        with patch("deployment_queue_cli.client.get_settings") as mock_settings:
            mock_settings.return_value.api_url = "https://default.api.com"
            client = DeploymentAPIClient(mock_credentials)
            assert client.api_url == "https://default.api.com"

    def test_headers(self, client: DeploymentAPIClient) -> None:
        """Headers include auth and organisation."""
        headers = client._headers()
        assert headers["Authorization"] == "Bearer ghp_test_token_xxxxxxxxxxxxxxxxxxxxx"
        assert headers["X-Organisation"] == "test-org"
        assert headers["Content-Type"] == "application/json"

    def test_handle_response_success(self, client: DeploymentAPIClient) -> None:
        """Successful response returns JSON."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "test"}

        result = client._handle_response(mock_response)
        assert result == {"id": "test"}

    def test_handle_response_no_content(self, client: DeploymentAPIClient) -> None:
        """204 response returns empty dict."""
        mock_response = MagicMock()
        mock_response.status_code = 204

        result = client._handle_response(mock_response)
        assert result == {}

    def test_handle_response_error(self, client: DeploymentAPIClient) -> None:
        """Error response raises DeploymentAPIError."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Not found"}

        with pytest.raises(DeploymentAPIError) as exc:
            client._handle_response(mock_response)

        assert exc.value.status_code == 404
        assert exc.value.detail == "Not found"

    def test_handle_response_error_no_json(self, client: DeploymentAPIClient) -> None:
        """Error response without JSON uses text."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.side_effect = Exception("Invalid JSON")
        mock_response.text = "Internal Server Error"

        with pytest.raises(DeploymentAPIError) as exc:
            client._handle_response(mock_response)

        assert exc.value.status_code == 500
        assert exc.value.detail == "Internal Server Error"


class TestDeploymentAPIClientMethods:
    """Tests for API client methods."""

    @pytest.fixture
    def client(self, mock_credentials: Credentials) -> DeploymentAPIClient:
        """Create a client for testing."""
        return DeploymentAPIClient(mock_credentials, api_url="https://api.test.com")

    @pytest.mark.asyncio
    async def test_list_deployments(
        self, client: DeploymentAPIClient, mock_deployment_list: list[dict]
    ) -> None:
        """List deployments returns deployment list."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_deployment_list

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await client.list_deployments(environment="production", limit=10)

            assert len(result) == 3
            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args.kwargs
            assert call_kwargs["params"]["environment"] == "production"
            assert call_kwargs["params"]["limit"] == 10

    @pytest.mark.asyncio
    async def test_get_deployment(self, client: DeploymentAPIClient, mock_deployment: dict) -> None:
        """Get deployment returns deployment details."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_deployment

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await client.get_deployment("test-deployment-uuid")

            assert result["id"] == "test-deployment-uuid"
            assert "test-deployment-uuid" in mock_get.call_args.args[0]

    @pytest.mark.asyncio
    async def test_create_deployment(
        self, client: DeploymentAPIClient, mock_deployment: dict
    ) -> None:
        """Create deployment posts deployment data."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = mock_deployment

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            deployment_data = {"name": "test-service", "version": "1.0.0"}
            result = await client.create_deployment(deployment_data)

            assert result["id"] == "test-deployment-uuid"
            call_kwargs = mock_post.call_args.kwargs
            assert call_kwargs["json"] == deployment_data

    @pytest.mark.asyncio
    async def test_get_current(self, client: DeploymentAPIClient, mock_deployment: dict) -> None:
        """Get current deployment returns current deployment."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_deployment

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await client.get_current(
                name="test-service",
                environment="production",
                provider="gcp",
                cloud_account_id="project-123",
                region="us-central1",
            )

            assert result is not None
            assert result["name"] == "test-service"

    @pytest.mark.asyncio
    async def test_get_current_not_found(self, client: DeploymentAPIClient) -> None:
        """Get current deployment returns None when not found."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await client.get_current(
                name="test-service",
                environment="production",
                provider="gcp",
                cloud_account_id="project-123",
                region="us-central1",
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_rollback(self, client: DeploymentAPIClient, mock_deployment: dict) -> None:
        """Rollback creates rollback deployment."""
        rollback_deployment = {
            **mock_deployment,
            "trigger": "rollback",
            "source_deployment_id": "previous-uuid",
            "rollback_from_deployment_id": "current-uuid",
        }
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = rollback_deployment

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await client.rollback(
                name="test-service",
                environment="production",
                provider="gcp",
                cloud_account_id="project-123",
                region="us-central1",
            )

            assert result["trigger"] == "rollback"
            assert result["source_deployment_id"] == "previous-uuid"
