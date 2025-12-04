"""Tests for CLI commands."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from deployment_queue_cli.auth import Credentials
from deployment_queue_cli.client import DeploymentAPIError
from deployment_queue_cli.main import app

runner = CliRunner()


class TestCreateCommand:
    """Tests for the create command."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create a mock client."""
        client = MagicMock()
        client.create_deployment = AsyncMock()
        return client

    def test_create_deployment_success(
        self, mock_credentials: Credentials, mock_deployment: dict
    ) -> None:
        """Create deployment with required options."""
        with (
            patch(
                "deployment_queue_cli.main.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.main.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.create_deployment = AsyncMock(return_value=mock_deployment)
            mock_client_class.return_value = mock_client

            result = runner.invoke(
                app,
                [
                    "create",
                    "my-service",
                    "v1.0.0",
                    "--type",
                    "k8s",
                    "--env",
                    "production",
                    "--provider",
                    "gcp",
                ],
            )

            assert result.exit_code == 0
            assert "Created deployment" in result.output
            assert "test-service" in result.output  # Uses mock_deployment name

            # Verify the deployment payload
            call_args = mock_client.create_deployment.call_args[0][0]
            assert call_args["name"] == "my-service"
            assert call_args["version"] == "v1.0.0"
            assert call_args["type"] == "k8s"
            assert call_args["environment"] == "production"
            assert call_args["provider"] == "gcp"
            assert call_args["auto"] is True

    def test_create_deployment_with_all_options(
        self, mock_credentials: Credentials, mock_deployment: dict
    ) -> None:
        """Create deployment with all optional parameters."""
        with (
            patch(
                "deployment_queue_cli.main.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.main.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.create_deployment = AsyncMock(return_value=mock_deployment)
            mock_client_class.return_value = mock_client

            result = runner.invoke(
                app,
                [
                    "create",
                    "my-service",
                    "v1.0.0",
                    "--type",
                    "terraform",
                    "--env",
                    "staging",
                    "--provider",
                    "aws",
                    "--account",
                    "123456789",
                    "--region",
                    "us-west-2",
                    "--cell",
                    "cell-001",
                    "--no-auto",
                    "--description",
                    "Test deployment",
                    "--notes",
                    "Some notes",
                    "--commit",
                    "abc123",
                    "--build-uri",
                    "https://ci.example.com/123",
                ],
            )

            assert result.exit_code == 0

            call_args = mock_client.create_deployment.call_args[0][0]
            assert call_args["type"] == "terraform"
            assert call_args["cloud_account_id"] == "123456789"
            assert call_args["region"] == "us-west-2"
            assert call_args["cell"] == "cell-001"
            assert call_args["auto"] is False
            assert call_args["description"] == "Test deployment"
            assert call_args["notes"] == "Some notes"
            assert call_args["commit_sha"] == "abc123"
            assert call_args["build_uri"] == "https://ci.example.com/123"

    def test_create_deployment_not_authenticated(self) -> None:
        """Create fails when not authenticated."""
        with patch(
            "deployment_queue_cli.main.get_stored_credentials",
            return_value=None,
        ):
            result = runner.invoke(
                app,
                [
                    "create",
                    "my-service",
                    "v1.0.0",
                    "--type",
                    "k8s",
                    "--env",
                    "production",
                    "--provider",
                    "gcp",
                ],
            )

            assert result.exit_code == 1
            assert "Not authenticated" in result.output

    def test_create_deployment_api_error(
        self, mock_credentials: Credentials
    ) -> None:
        """Create handles API errors."""
        with (
            patch(
                "deployment_queue_cli.main.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.main.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.create_deployment = AsyncMock(
                side_effect=DeploymentAPIError(422, "Validation error")
            )
            mock_client_class.return_value = mock_client

            result = runner.invoke(
                app,
                [
                    "create",
                    "my-service",
                    "v1.0.0",
                    "--type",
                    "k8s",
                    "--env",
                    "production",
                    "--provider",
                    "gcp",
                ],
            )

            assert result.exit_code == 1
            assert "422" in result.output

    def test_create_deployment_missing_required_options(self) -> None:
        """Create fails with missing required options."""
        result = runner.invoke(
            app,
            [
                "create",
                "my-service",
                "v1.0.0",
            ],
        )

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()


class TestListCommand:
    """Tests for the list command."""

    def test_list_deployments_success(
        self, mock_credentials: Credentials, mock_deployment_list: list[dict]
    ) -> None:
        """List deployments shows table."""
        with (
            patch(
                "deployment_queue_cli.main.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.main.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.list_deployments = AsyncMock(return_value=mock_deployment_list)
            mock_client_class.return_value = mock_client

            result = runner.invoke(app, ["list"])

            assert result.exit_code == 0
            assert "Deployments" in result.output
            # Rich truncates long values, so check for partial matches
            assert "test-" in result.output  # Truncated service name or ID
            assert "1.0.0" in result.output
            assert "2.0.0" in result.output
            assert "3.0.0" in result.output
            assert "gcp" in result.output

    def test_list_deployments_with_filters(
        self, mock_credentials: Credentials, mock_deployment_list: list[dict]
    ) -> None:
        """List deployments with filter options."""
        with (
            patch(
                "deployment_queue_cli.main.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.main.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.list_deployments = AsyncMock(return_value=mock_deployment_list)
            mock_client_class.return_value = mock_client

            result = runner.invoke(
                app,
                [
                    "list",
                    "--env",
                    "production",
                    "--status",
                    "deployed",
                    "--provider",
                    "gcp",
                    "--limit",
                    "50",
                ],
            )

            assert result.exit_code == 0
            mock_client.list_deployments.assert_called_once_with(
                "production", "deployed", "gcp", None, 50
            )

    def test_list_deployments_empty(
        self, mock_credentials: Credentials
    ) -> None:
        """List shows message when no deployments found."""
        with (
            patch(
                "deployment_queue_cli.main.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.main.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.list_deployments = AsyncMock(return_value=[])
            mock_client_class.return_value = mock_client

            result = runner.invoke(app, ["list"])

            assert result.exit_code == 0
            assert "No deployments found" in result.output

    def test_list_deployments_not_authenticated(self) -> None:
        """List fails when not authenticated."""
        with patch(
            "deployment_queue_cli.main.get_stored_credentials",
            return_value=None,
        ):
            result = runner.invoke(app, ["list"])

            assert result.exit_code == 1
            assert "Not authenticated" in result.output

    def test_list_deployments_shows_all_columns(
        self, mock_credentials: Credentials
    ) -> None:
        """List shows all expected columns."""
        deployment = {
            "id": "uuid-123",
            "name": "my-service",
            "version": "v2.0.0",
            "status": "in_progress",
            "created_at": "2024-01-15T10:30:00Z",
            "provider": "aws",
            "cloud_account_id": "987654321",
            "region": "eu-west-1",
            "cell": "cell-002",
        }

        with (
            patch(
                "deployment_queue_cli.main.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.main.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.list_deployments = AsyncMock(return_value=[deployment])
            mock_client_class.return_value = mock_client

            result = runner.invoke(app, ["list"])

            assert result.exit_code == 0
            # Rich truncates long values, so check for partial matches
            assert "uuid-" in result.output
            assert "my-se" in result.output  # Truncated
            assert "v2.0.0" in result.output
            assert "in_pr" in result.output  # Truncated status
            assert "aws" in result.output
            assert "98765" in result.output  # Truncated account
            assert "eu-w" in result.output  # Truncated region
            assert "cell-" in result.output


class TestGetCommand:
    """Tests for the get command."""

    def test_get_deployment_success(
        self, mock_credentials: Credentials, mock_deployment: dict
    ) -> None:
        """Get deployment shows details."""
        with (
            patch(
                "deployment_queue_cli.main.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.main.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.get_deployment = AsyncMock(return_value=mock_deployment)
            mock_client_class.return_value = mock_client

            result = runner.invoke(app, ["get", "test-deployment-uuid"])

            assert result.exit_code == 0
            assert "test-deployment-uuid" in result.output
            assert "test-service" in result.output
            assert "deployed" in result.output

    def test_get_deployment_not_found(
        self, mock_credentials: Credentials
    ) -> None:
        """Get handles 404 error."""
        with (
            patch(
                "deployment_queue_cli.main.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.main.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.get_deployment = AsyncMock(
                side_effect=DeploymentAPIError(404, "Not found")
            )
            mock_client_class.return_value = mock_client

            result = runner.invoke(app, ["get", "nonexistent-id"])

            assert result.exit_code == 1
            assert "Not found" in result.output


class TestCurrentCommand:
    """Tests for the current command."""

    def test_current_deployment_success(
        self, mock_credentials: Credentials, mock_deployment: dict
    ) -> None:
        """Current shows deployment info."""
        with (
            patch(
                "deployment_queue_cli.main.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.main.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.get_current = AsyncMock(return_value=mock_deployment)
            mock_client_class.return_value = mock_client

            result = runner.invoke(
                app,
                [
                    "current",
                    "test-service",
                    "--env",
                    "production",
                    "--provider",
                    "gcp",
                    "--account",
                    "project-123",
                    "--region",
                    "us-central1",
                ],
            )

            assert result.exit_code == 0
            assert "test-service" in result.output
            assert "1.0.0" in result.output

    def test_current_deployment_not_found(
        self, mock_credentials: Credentials
    ) -> None:
        """Current shows message when no deployment."""
        with (
            patch(
                "deployment_queue_cli.main.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.main.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.get_current = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = runner.invoke(
                app,
                [
                    "current",
                    "test-service",
                    "--env",
                    "production",
                    "--provider",
                    "gcp",
                    "--account",
                    "project-123",
                    "--region",
                    "us-central1",
                ],
            )

            assert result.exit_code == 0
            assert "No deployment found" in result.output


class TestHistoryCommand:
    """Tests for the history command."""

    def test_history_success(
        self, mock_credentials: Credentials, mock_deployment_list: list[dict]
    ) -> None:
        """History shows deployment list."""
        with (
            patch(
                "deployment_queue_cli.main.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.main.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.get_history = AsyncMock(return_value=mock_deployment_list)
            mock_client_class.return_value = mock_client

            result = runner.invoke(
                app,
                [
                    "history",
                    "test-service",
                    "--env",
                    "production",
                    "--provider",
                    "gcp",
                    "--account",
                    "project-123",
                    "--region",
                    "us-central1",
                ],
            )

            assert result.exit_code == 0
            assert "History" in result.output
            assert "1.0.0" in result.output
            assert "2.0.0" in result.output
            assert "3.0.0" in result.output

    def test_history_empty(
        self, mock_credentials: Credentials
    ) -> None:
        """History shows message when empty."""
        with (
            patch(
                "deployment_queue_cli.main.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.main.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.get_history = AsyncMock(return_value=[])
            mock_client_class.return_value = mock_client

            result = runner.invoke(
                app,
                [
                    "history",
                    "test-service",
                    "--env",
                    "production",
                    "--provider",
                    "gcp",
                    "--account",
                    "project-123",
                    "--region",
                    "us-central1",
                ],
            )

            assert result.exit_code == 0
            assert "No deployment history found" in result.output


class TestUpdateStatusCommand:
    """Tests for the update-status command."""

    def test_update_status_success(
        self, mock_credentials: Credentials, mock_deployment: dict
    ) -> None:
        """Update status succeeds."""
        updated = {**mock_deployment, "status": "deployed"}

        with (
            patch(
                "deployment_queue_cli.main.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.main.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.update_status = AsyncMock(return_value=updated)
            mock_client_class.return_value = mock_client

            result = runner.invoke(
                app,
                [
                    "update-status",
                    "test-service",
                    "deployed",
                    "--env",
                    "production",
                    "--provider",
                    "gcp",
                    "--account",
                    "project-123",
                    "--region",
                    "us-central1",
                ],
            )

            assert result.exit_code == 0
            assert "Updated" in result.output
            assert "deployed" in result.output


class TestRollbackCommand:
    """Tests for the rollback command."""

    def test_rollback_success(
        self, mock_credentials: Credentials, mock_deployment: dict
    ) -> None:
        """Rollback creates new deployment."""
        rollback_deployment = {
            **mock_deployment,
            "id": "rollback-uuid",
            "trigger": "rollback",
            "source_deployment_id": "previous-uuid",
            "rollback_from_deployment_id": "current-uuid",
        }

        with (
            patch(
                "deployment_queue_cli.main.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.main.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.rollback = AsyncMock(return_value=rollback_deployment)
            mock_client_class.return_value = mock_client

            result = runner.invoke(
                app,
                [
                    "rollback",
                    "test-service",
                    "--env",
                    "production",
                    "--provider",
                    "gcp",
                    "--account",
                    "project-123",
                    "--region",
                    "us-central1",
                ],
            )

            assert result.exit_code == 0
            assert "Rollback created" in result.output
            assert "rollback-uuid" in result.output

    def test_rollback_with_target_version(
        self, mock_credentials: Credentials, mock_deployment: dict
    ) -> None:
        """Rollback to specific version."""
        with (
            patch(
                "deployment_queue_cli.main.get_stored_credentials",
                return_value=mock_credentials,
            ),
            patch(
                "deployment_queue_cli.main.DeploymentAPIClient"
            ) as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.rollback = AsyncMock(return_value=mock_deployment)
            mock_client_class.return_value = mock_client

            result = runner.invoke(
                app,
                [
                    "rollback",
                    "test-service",
                    "--env",
                    "production",
                    "--provider",
                    "gcp",
                    "--account",
                    "project-123",
                    "--region",
                    "us-central1",
                    "--version",
                    "v0.9.0",
                ],
            )

            assert result.exit_code == 0
            mock_client.rollback.assert_called_once()
            # Check that target_version was passed
            call_kwargs = mock_client.rollback.call_args
            assert call_kwargs[0][5] is None  # cell_id
            assert call_kwargs[0][6] == "v0.9.0"  # target_version
