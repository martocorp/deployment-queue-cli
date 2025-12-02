"""Tests for authentication module."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from deployment_queue_cli.auth import (
    Credentials,
    clear_credentials,
    get_stored_credentials,
    pat_login,
    store_credentials,
)


class TestCredentials:
    """Tests for Credentials dataclass."""

    def test_credentials_creation(self) -> None:
        """Credentials stores all fields correctly."""
        creds = Credentials(
            github_token="ghp_test",
            organisation="test-org",
            username="test-user",
        )

        assert creds.github_token == "ghp_test"
        assert creds.organisation == "test-org"
        assert creds.username == "test-user"


class TestCredentialsStorage:
    """Tests for credential storage functions."""

    def test_store_and_retrieve_credentials(self, tmp_path: Path) -> None:
        """Credentials can be stored and retrieved."""
        creds_file = tmp_path / "credentials.json"

        with (
            patch("deployment_queue_cli.auth.CREDENTIALS_FILE", creds_file),
            patch("deployment_queue_cli.auth.CONFIG_DIR", tmp_path),
        ):
            creds = Credentials(
                github_token="ghp_test",
                organisation="test-org",
                username="test-user",
            )
            store_credentials(creds)

            # Verify file exists with correct permissions
            assert creds_file.exists()
            assert oct(creds_file.stat().st_mode)[-3:] == "600"

            # Verify content
            retrieved = get_stored_credentials()
            assert retrieved is not None
            assert retrieved.github_token == "ghp_test"
            assert retrieved.organisation == "test-org"
            assert retrieved.username == "test-user"

    def test_get_stored_credentials_no_file(self, tmp_path: Path) -> None:
        """Returns None when no credentials file exists."""
        creds_file = tmp_path / "credentials.json"

        with patch("deployment_queue_cli.auth.CREDENTIALS_FILE", creds_file):
            assert get_stored_credentials() is None

    def test_get_stored_credentials_invalid_json(self, tmp_path: Path) -> None:
        """Returns None when credentials file contains invalid JSON."""
        creds_file = tmp_path / "credentials.json"
        creds_file.write_text("invalid json")

        with patch("deployment_queue_cli.auth.CREDENTIALS_FILE", creds_file):
            assert get_stored_credentials() is None

    def test_get_stored_credentials_missing_keys(self, tmp_path: Path) -> None:
        """Returns None when credentials file is missing required keys."""
        creds_file = tmp_path / "credentials.json"
        creds_file.write_text(json.dumps({"github_token": "test"}))

        with patch("deployment_queue_cli.auth.CREDENTIALS_FILE", creds_file):
            assert get_stored_credentials() is None

    def test_clear_credentials(self, tmp_path: Path) -> None:
        """Clear credentials removes the file."""
        creds_file = tmp_path / "credentials.json"
        creds_file.write_text(
            json.dumps(
                {
                    "github_token": "test",
                    "organisation": "org",
                    "username": "user",
                }
            )
        )

        with patch("deployment_queue_cli.auth.CREDENTIALS_FILE", creds_file):
            clear_credentials()
            assert not creds_file.exists()

    def test_clear_credentials_no_file(self, tmp_path: Path) -> None:
        """Clear credentials does not error when file doesn't exist."""
        creds_file = tmp_path / "credentials.json"

        with patch("deployment_queue_cli.auth.CREDENTIALS_FILE", creds_file):
            clear_credentials()  # Should not raise


class TestPATLogin:
    """Tests for PAT login."""

    @pytest.mark.asyncio
    async def test_pat_login_success(
        self, tmp_path: Path, mock_github_api: dict[str, AsyncMock]
    ) -> None:
        """PAT login succeeds with valid token and org membership."""
        creds_file = tmp_path / "credentials.json"

        with (
            patch("deployment_queue_cli.auth.CREDENTIALS_FILE", creds_file),
            patch("deployment_queue_cli.auth.CONFIG_DIR", tmp_path),
        ):
            creds = await pat_login("ghp_valid_token", "test-org")

            assert creds.github_token == "ghp_valid_token"
            assert creds.organisation == "test-org"
            assert creds.username == "test-user"

    @pytest.mark.asyncio
    async def test_pat_login_invalid_token(self, mock_github_api: dict[str, AsyncMock]) -> None:
        """PAT login fails with invalid token."""
        mock_github_api["user_info"].side_effect = ValueError("Invalid GitHub token")

        with pytest.raises(ValueError, match="Invalid GitHub Personal Access Token"):
            await pat_login("invalid_token", "test-org")

    @pytest.mark.asyncio
    async def test_pat_login_not_org_member(self, mock_github_api: dict[str, AsyncMock]) -> None:
        """PAT login fails when user is not org member."""
        mock_github_api["verify"].return_value = False
        mock_github_api["orgs"].return_value = {"other-org"}

        with pytest.raises(ValueError, match="not a member"):
            await pat_login("ghp_valid_token", "test-org")
