"""GitHub authentication for the Deployment Queue CLI (Device Flow + PAT)."""

import asyncio
import json
import time
from dataclasses import dataclass
from typing import Optional

import httpx

from .config import CONFIG_DIR, CREDENTIALS_FILE, get_settings

# GitHub OAuth endpoints
DEVICE_CODE_URL = "https://github.com/login/device/code"
ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"  # nosec B105
GITHUB_API_URL = "https://api.github.com"


@dataclass
class Credentials:
    """Stored credentials for CLI authentication."""

    github_token: str
    organisation: str
    username: str


def get_stored_credentials() -> Optional[Credentials]:
    """Load stored credentials from disk."""
    if not CREDENTIALS_FILE.exists():
        return None

    try:
        data = json.loads(CREDENTIALS_FILE.read_text())
        return Credentials(
            github_token=data["github_token"],
            organisation=data["organisation"],
            username=data["username"],
        )
    except (json.JSONDecodeError, KeyError):
        return None


def store_credentials(creds: Credentials) -> None:
    """Store credentials to disk securely."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_FILE.write_text(
        json.dumps(
            {
                "github_token": creds.github_token,
                "organisation": creds.organisation,
                "username": creds.username,
            }
        )
    )
    CREDENTIALS_FILE.chmod(0o600)  # Owner read/write only


def clear_credentials() -> None:
    """Remove stored credentials."""
    if CREDENTIALS_FILE.exists():
        CREDENTIALS_FILE.unlink()


def _github_headers(token: Optional[str] = None) -> dict[str, str]:
    """Build headers for GitHub API requests."""
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def _get_user_info(token: str) -> dict:
    """Get GitHub user information."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{GITHUB_API_URL}/user",
            headers=_github_headers(token),
        )
        if response.status_code == 401:
            raise ValueError("Invalid GitHub token")
        response.raise_for_status()
        return response.json()


async def _get_user_organisations(token: str) -> set[str]:
    """Get all organisations the user is a member of."""
    orgs: set[str] = set()
    page = 1

    async with httpx.AsyncClient(timeout=10.0) as client:
        while True:
            response = await client.get(
                f"{GITHUB_API_URL}/user/orgs",
                headers=_github_headers(token),
                params={"page": page, "per_page": 100},
            )
            response.raise_for_status()
            page_orgs = response.json()

            if not page_orgs:
                break

            orgs.update(org["login"] for org in page_orgs)
            page += 1

            if page > 10:  # Safety limit
                break

    return orgs


async def _verify_org_membership(token: str, organisation: str) -> bool:
    """Verify user is member of organisation."""
    user_orgs = await _get_user_organisations(token)
    return organisation.lower() in {org.lower() for org in user_orgs}


async def device_flow_login(organisation: str) -> Credentials:
    """
    Authenticate using GitHub Device Flow.

    Flow:
    1. Request device code from GitHub
    2. Display code and URL for user
    3. User opens browser and enters code
    4. Poll GitHub until user authorizes
    5. Verify org membership
    6. Store and return credentials
    """
    settings = get_settings()
    if not settings.github_client_id:
        raise ValueError(
            "GitHub client ID not configured. "
            "Set DEPLOYMENT_QUEUE_CLI_GITHUB_CLIENT_ID environment variable."
        )

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Request device code
        response = await client.post(
            DEVICE_CODE_URL,
            data={
                "client_id": settings.github_client_id,
                "scope": "read:org read:user",
            },
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        device_data = response.json()

        device_code = device_data["device_code"]
        user_code = device_data["user_code"]
        verification_uri = device_data["verification_uri"]
        interval = device_data.get("interval", 5)
        expires_in = device_data.get("expires_in", 900)

        # Step 2: Display instructions
        print(f"\nTo authenticate, visit: {verification_uri}")
        print(f"   Enter code: {user_code}\n")
        print("Waiting for authorization", end="", flush=True)

        # Step 3: Poll for token
        start_time = time.time()
        while time.time() - start_time < expires_in:
            await asyncio.sleep(interval)
            print(".", end="", flush=True)

            response = await client.post(
                ACCESS_TOKEN_URL,
                data={
                    "client_id": settings.github_client_id,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
                headers={"Accept": "application/json"},
            )

            token_data = response.json()

            if "access_token" in token_data:
                print(" Done\n")
                github_token = token_data["access_token"]

                # Get username
                user_info = await _get_user_info(github_token)
                username = user_info["login"]

                # Verify org membership
                if not await _verify_org_membership(github_token, organisation):
                    user_orgs = await _get_user_organisations(github_token)
                    raise ValueError(
                        f"You are not a member of organisation '{organisation}'.\n"
                        f"Your organisations: {', '.join(sorted(user_orgs))}"
                    )

                creds = Credentials(
                    github_token=github_token,
                    organisation=organisation,
                    username=username,
                )
                store_credentials(creds)
                return creds

            error = token_data.get("error")
            if error == "authorization_pending":
                continue
            elif error == "slow_down":
                interval += 5
            elif error == "expired_token":
                print(" Failed")
                raise TimeoutError("Device code expired. Please try again.")
            elif error == "access_denied":
                print(" Failed")
                raise PermissionError("Authorization denied by user.")
            else:
                print(" Failed")
                raise Exception(f"Unexpected error: {error}")

        print(" Failed")
        raise TimeoutError("Authorization timed out. Please try again.")


async def pat_login(pat: str, organisation: str) -> Credentials:
    """
    Authenticate using a GitHub Personal Access Token.

    The PAT needs 'read:org' and 'read:user' scopes.
    """
    # Verify token
    try:
        user_info = await _get_user_info(pat)
    except ValueError:
        raise ValueError("Invalid GitHub Personal Access Token")

    username = user_info["login"]

    # Verify org membership
    if not await _verify_org_membership(pat, organisation):
        user_orgs = await _get_user_organisations(pat)
        raise ValueError(
            f"You are not a member of organisation '{organisation}'.\n"
            f"Your organisations: {', '.join(sorted(user_orgs))}"
        )

    creds = Credentials(
        github_token=pat,
        organisation=organisation,
        username=username,
    )
    store_credentials(creds)
    return creds


async def switch_organisation(organisation: str) -> Credentials:
    """Switch to a different organisation using existing token."""
    creds = get_stored_credentials()
    if not creds:
        raise ValueError("Not logged in. Run 'deployment-queue-cli login' first.")

    # Verify membership in new org
    if not await _verify_org_membership(creds.github_token, organisation):
        user_orgs = await _get_user_organisations(creds.github_token)
        raise ValueError(
            f"You are not a member of organisation '{organisation}'.\n"
            f"Your organisations: {', '.join(sorted(user_orgs))}"
        )

    # Update stored credentials
    new_creds = Credentials(
        github_token=creds.github_token,
        organisation=organisation,
        username=creds.username,
    )
    store_credentials(new_creds)
    return new_creds


async def list_available_organisations() -> list[str]:
    """List organisations available to the current user."""
    creds = get_stored_credentials()
    if not creds:
        raise ValueError("Not logged in. Run 'deployment-queue-cli login' first.")

    orgs = await _get_user_organisations(creds.github_token)
    return sorted(orgs)
