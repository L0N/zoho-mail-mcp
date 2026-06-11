"""
Zoho Mail OAuth 2.0 handler.
Manages token acquisition, storage, and refresh.
"""

import json
import time
import httpx
from pathlib import Path
from config import (
    ZOHO_CLIENT_ID,
    ZOHO_CLIENT_SECRET,
    ZOHO_REDIRECT_URI,
    ZOHO_ACCOUNTS_URL,
    TOKEN_FILE,
)


def get_authorization_url() -> str:
    """
    Step 1 of OAuth: Generate the URL to send the user to for consent.
    Open this URL in a browser to kick off the flow.
    """
    params = {
        "scope": "ZohoMail.messages.READ,ZohoMail.folders.READ,ZohoMail.accounts.READ",
        "client_id": ZOHO_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": ZOHO_REDIRECT_URI,
        "access_type": "offline",  # required to get a refresh token
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{ZOHO_ACCOUNTS_URL}/oauth/v2/auth?{query}"


def exchange_code_for_tokens(auth_code: str) -> dict:
    """
    Step 2 of OAuth: Exchange the authorization code for access + refresh tokens.
    Call this with the `code` param from the redirect URL after user consent.
    """
    response = httpx.post(
        f"{ZOHO_ACCOUNTS_URL}/oauth/v2/token",
        data={
            "grant_type": "authorization_code",
            "client_id": ZOHO_CLIENT_ID,
            "client_secret": ZOHO_CLIENT_SECRET,
            "redirect_uri": ZOHO_REDIRECT_URI,
            "code": auth_code,
        },
    )
    response.raise_for_status()
    tokens = response.json()

    if "error" in tokens:
        raise ValueError(f"Token exchange failed: {tokens['error']}")

    # Add expiry timestamp so we know when to refresh
    tokens["expires_at"] = time.time() + tokens.get("expires_in", 3600)
    _save_tokens(tokens)
    return tokens


def get_valid_access_token() -> str:
    """
    Returns a valid access token, refreshing if expired.
    Raises RuntimeError if no tokens exist yet (run the OAuth flow first).
    """
    tokens = _load_tokens()

    if not tokens:
        raise RuntimeError(
            "No tokens found. Run the OAuth flow first:\n"
            "  python auth.py\n"
            "Then follow the instructions to authenticate."
        )

    # Refresh if expired (with 60s buffer)
    if time.time() >= tokens.get("expires_at", 0) - 60:
        tokens = _refresh_tokens(tokens["refresh_token"])

    return tokens["access_token"]


def _refresh_tokens(refresh_token: str) -> dict:
    """Exchange a refresh token for a new access token."""
    response = httpx.post(
        f"{ZOHO_ACCOUNTS_URL}/oauth/v2/token",
        data={
            "grant_type": "refresh_token",
            "client_id": ZOHO_CLIENT_ID,
            "client_secret": ZOHO_CLIENT_SECRET,
            "refresh_token": refresh_token,
        },
    )
    response.raise_for_status()
    new_tokens = response.json()

    if "error" in new_tokens:
        raise ValueError(f"Token refresh failed: {new_tokens['error']}")

    # Preserve the refresh token (Zoho doesn't always return a new one)
    new_tokens.setdefault("refresh_token", refresh_token)
    new_tokens["expires_at"] = time.time() + new_tokens.get("expires_in", 3600)
    _save_tokens(new_tokens)
    return new_tokens


def _save_tokens(tokens: dict) -> None:
    Path(TOKEN_FILE).write_text(json.dumps(tokens, indent=2))


def _load_tokens() -> dict | None:
    path = Path(TOKEN_FILE)
    if not path.exists():
        return None
    return json.loads(path.read_text())


# ─── Run this file directly to complete the OAuth flow ───────────────────────
if __name__ == "__main__":
    print("\n=== Zoho Mail MCP — OAuth Setup ===\n")
    print("Step 1: Open this URL in your browser and authorise the app:\n")
    print(get_authorization_url())
    print("\nStep 2: After authorising, you'll be redirected to your redirect URI.")
    print("Copy the `code` value from the URL and paste it below.\n")

    code = input("Authorization code: ").strip()
    tokens = exchange_code_for_tokens(code)
    print("\n✅ Authentication successful! Tokens saved to", TOKEN_FILE)
    print("You can now start the MCP server: python server.py")
