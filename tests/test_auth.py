"""Tests for authentication module."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from deployment_queue_cli.auth import (
    Credentials,
    _get_credentials_from_env,
    _get_credentials_from_file,
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


class TestCredentialsFromEnv:
    """Tests for environment variable credentials."""

    def test_credentials_from_env_success(self) -> None:
        """Credentials loaded from environment variables."""
        mock_settings = MagicMock()
        mock_settings.github_token = "ghp_env_token"
        mock_settings.organisation = "env-org"
        mock_settings.username = "env-user"

        with patch("deployment_queue_cli.auth.get_settings", return_value=mock_settings):
            creds = _get_credentials_from_env()

            assert creds is not None
            assert creds.github_token == "ghp_env_token"
            assert creds.organisation == "env-org"
            assert creds.username == "env-user"

    def test_credentials_from_env_default_username(self) -> None:
        """Username defaults to 'env-user' when not provided."""
        mock_settings = MagicMock()
        mock_settings.github_token = "ghp_env_token"
        mock_settings.organisation = "env-org"
        mock_settings.username = None

        with patch("deployment_queue_cli.auth.get_settings", return_value=mock_settings):
            creds = _get_credentials_from_env()

            assert creds is not None
            assert creds.username == "env-user"

    def test_credentials_from_env_missing_token(self) -> None:
        """Returns None when token is missing."""
        mock_settings = MagicMock()
        mock_settings.github_token = None
        mock_settings.organisation = "env-org"

        with patch("deployment_queue_cli.auth.get_settings", return_value=mock_settings):
            assert _get_credentials_from_env() is None

    def test_credentials_from_env_missing_org(self) -> None:
        """Returns None when organisation is missing."""
        mock_settings = MagicMock()
        mock_settings.github_token = "ghp_env_token"
        mock_settings.organisation = None

        with patch("deployment_queue_cli.auth.get_settings", return_value=mock_settings):
            assert _get_credentials_from_env() is None


class TestCredentialsFromFile:
    """Tests for file-based credentials."""

    def test_credentials_from_file_success(self, tmp_path: Path) -> None:
        """Credentials loaded from custom file path."""
        creds_file = tmp_path / "custom_creds.json"
        creds_file.write_text(
            json.dumps({
                "github_token": "ghp_file_token",
                "organisation": "file-org",
                "username": "file-user",
            })
        )

        creds = _get_credentials_from_file(creds_file)

        assert creds is not None
        assert creds.github_token == "ghp_file_token"
        assert creds.organisation == "file-org"
        assert creds.username == "file-user"

    def test_credentials_from_file_not_found(self, tmp_path: Path) -> None:
        """Returns None when file doesn't exist."""
        creds_file = tmp_path / "nonexistent.json"
        assert _get_credentials_from_file(creds_file) is None

    def test_credentials_from_file_invalid_json(self, tmp_path: Path) -> None:
        """Returns None when file contains invalid JSON."""
        creds_file = tmp_path / "invalid.json"
        creds_file.write_text("not valid json")
        assert _get_credentials_from_file(creds_file) is None


class TestCredentialsPriority:
    """Tests for credential loading priority."""

    def test_env_vars_take_priority(self, tmp_path: Path) -> None:
        """Environment variables take priority over files."""
        # Create a credentials file
        creds_file = tmp_path / "credentials.json"
        creds_file.write_text(
            json.dumps({
                "github_token": "ghp_file_token",
                "organisation": "file-org",
                "username": "file-user",
            })
        )

        # Set up env vars
        mock_settings = MagicMock()
        mock_settings.github_token = "ghp_env_token"
        mock_settings.organisation = "env-org"
        mock_settings.username = "env-user"
        mock_settings.credentials_file = None

        with (
            patch("deployment_queue_cli.auth.get_settings", return_value=mock_settings),
            patch("deployment_queue_cli.auth.CREDENTIALS_FILE", creds_file),
        ):
            creds = get_stored_credentials()

            assert creds is not None
            assert creds.github_token == "ghp_env_token"
            assert creds.organisation == "env-org"

    def test_custom_file_over_default(self, tmp_path: Path) -> None:
        """Custom credentials file takes priority over default."""
        # Create default credentials file
        default_file = tmp_path / "default_creds.json"
        default_file.write_text(
            json.dumps({
                "github_token": "ghp_default",
                "organisation": "default-org",
                "username": "default-user",
            })
        )

        # Create custom credentials file
        custom_file = tmp_path / "custom_creds.json"
        custom_file.write_text(
            json.dumps({
                "github_token": "ghp_custom",
                "organisation": "custom-org",
                "username": "custom-user",
            })
        )

        mock_settings = MagicMock()
        mock_settings.github_token = None
        mock_settings.organisation = None
        mock_settings.credentials_file = str(custom_file)

        with (
            patch("deployment_queue_cli.auth.get_settings", return_value=mock_settings),
            patch("deployment_queue_cli.auth.CREDENTIALS_FILE", default_file),
        ):
            creds = get_stored_credentials()

            assert creds is not None
            assert creds.github_token == "ghp_custom"
            assert creds.organisation == "custom-org"

    def test_falls_back_to_default_file(self, tmp_path: Path) -> None:
        """Falls back to default file when no env vars or custom file."""
        default_file = tmp_path / "credentials.json"
        default_file.write_text(
            json.dumps({
                "github_token": "ghp_default",
                "organisation": "default-org",
                "username": "default-user",
            })
        )

        mock_settings = MagicMock()
        mock_settings.github_token = None
        mock_settings.organisation = None
        mock_settings.credentials_file = None

        with (
            patch("deployment_queue_cli.auth.get_settings", return_value=mock_settings),
            patch("deployment_queue_cli.auth.CREDENTIALS_FILE", default_file),
        ):
            creds = get_stored_credentials()

            assert creds is not None
            assert creds.github_token == "ghp_default"


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
