"""Pytest fixtures for the Deployment Queue CLI tests."""

from typing import Generator
from unittest.mock import AsyncMock, patch

import pytest

from deployment_queue_cli.auth import Credentials


@pytest.fixture
def mock_credentials() -> Credentials:
    """Mock credentials for testing."""
    return Credentials(
        github_token="ghp_test_token_xxxxxxxxxxxxxxxxxxxxx",
        organisation="test-org",
        username="test-user",
    )


@pytest.fixture
def mock_stored_credentials(mock_credentials: Credentials) -> Generator[None, None, None]:
    """Fixture that patches get_stored_credentials to return mock credentials."""
    with patch(
        "deployment_queue_cli.auth.get_stored_credentials", return_value=mock_credentials
    ):
        yield


@pytest.fixture
def mock_github_api() -> Generator[dict[str, AsyncMock], None, None]:
    """Mock GitHub API responses."""
    with (
        patch("deployment_queue_cli.auth._get_user_info") as mock_user_info,
        patch("deployment_queue_cli.auth._get_user_organisations") as mock_orgs,
        patch("deployment_queue_cli.auth._verify_org_membership") as mock_verify,
    ):
        mock_user_info.return_value = {"login": "test-user"}
        mock_orgs.return_value = {"test-org", "other-org"}
        mock_verify.return_value = True

        yield {
            "user_info": mock_user_info,
            "orgs": mock_orgs,
            "verify": mock_verify,
        }


@pytest.fixture
def mock_deployment() -> dict:
    """Mock deployment data."""
    return {
        "id": "test-deployment-uuid",
        "name": "test-service",
        "version": "1.0.0",
        "status": "deployed",
        "trigger": "auto",
        "environment": "production",
        "provider": "gcp",
        "cloud_account_id": "project-123",
        "region": "us-central1",
        "cell_id": None,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:35:00Z",
        "created_by_actor": "test-user",
        "created_by_repo": "test-org/test-repo",
        "source_deployment_id": None,
        "rollback_from_deployment_id": None,
    }


@pytest.fixture
def mock_deployment_list(mock_deployment: dict) -> list[dict]:
    """Mock list of deployments."""
    return [
        mock_deployment,
        {
            **mock_deployment,
            "id": "test-deployment-uuid-2",
            "version": "2.0.0",
            "status": "scheduled",
        },
        {
            **mock_deployment,
            "id": "test-deployment-uuid-3",
            "version": "3.0.0",
            "status": "failed",
        },
    ]
