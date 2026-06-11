"""
Zoho Mail API client.
Wraps the REST API calls so server.py stays clean.
Docs: https://www.zoho.com/mail/help/api/
"""

import httpx
from auth import get_valid_access_token
from config import ZOHO_MAIL_API_URL


def _headers() -> dict:
    """Build auth headers with a fresh/valid token."""
    return {
        "Authorization": f"Zoho-oauthtoken {get_valid_access_token()}",
        "Content-Type": "application/json",
    }


def _get(path: str, params: dict = None) -> dict:
    """Make an authenticated GET request to the Zoho Mail API."""
    response = httpx.get(
        f"{ZOHO_MAIL_API_URL}/{path}",
        headers=_headers(),
        params=params or {},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


# ─── Account ──────────────────────────────────────────────────────────────────

def get_accounts() -> list[dict]:
    """
    List all Zoho Mail accounts for the authenticated user.
    Returns a list with account IDs — needed for most other calls.
    """
    data = _get("accounts")
    return data.get("data", [])


def get_primary_account_id() -> str:
    """Return the account ID of the first (primary) account."""
    accounts = get_accounts()
    if not accounts:
        raise RuntimeError("No Zoho Mail accounts found for this user.")
    return accounts[0]["accountId"]


# ─── Folders ──────────────────────────────────────────────────────────────────

def get_folders(account_id: str = None) -> list[dict]:
    """
    List all mail folders (Inbox, Sent, Drafts, custom folders, etc.)
    """
    account_id = account_id or get_primary_account_id()
    data = _get(f"accounts/{account_id}/folders")
    return data.get("data", [])


# ─── Messages ─────────────────────────────────────────────────────────────────

def get_inbox(limit: int = 20, account_id: str = None) -> list[dict]:
    """
    Fetch the most recent messages from the inbox.
    Returns summary info (subject, sender, date) — not full body.
    Note: messages/view defaults to the inbox when folderId is omitted;
    the param only accepts numeric folder IDs, not names like "inbox".
    """
    account_id = account_id or get_primary_account_id()
    data = _get(
        f"accounts/{account_id}/messages/view",
        params={"limit": limit},
    )
    return data.get("data", [])


def search_emails(
    query: str,
    limit: int = 20,
    account_id: str = None,
) -> list[dict]:
    """
    Search emails by keyword. Zoho searches subject, body, and sender.
    """
    account_id = account_id or get_primary_account_id()
    data = _get(
        f"accounts/{account_id}/messages/search",
        params={"searchKey": query, "limit": limit},
    )
    return data.get("data", [])


def read_email(message_id: str, folder_id: str = None, account_id: str = None) -> dict:
    """
    Fetch the full content of a single email including body and attachments list.
    The content endpoint requires the folder ID in the path; if not supplied,
    each folder is tried until the message is found.
    """
    account_id = account_id or get_primary_account_id()

    if folder_id:
        data = _get(
            f"accounts/{account_id}/folders/{folder_id}/messages/{message_id}/content"
        )
        return data.get("data", {})

    for folder in get_folders(account_id):
        try:
            data = _get(
                f"accounts/{account_id}/folders/{folder['folderId']}"
                f"/messages/{message_id}/content"
            )
            return data.get("data", {})
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                continue
            raise
    raise RuntimeError(f"Message {message_id} not found in any folder.")


def get_messages_in_folder(
    folder_id: str,
    limit: int = 20,
    account_id: str = None,
) -> list[dict]:
    """
    Fetch messages from a specific folder by folder ID.
    Use get_folders() first to find folder IDs.
    """
    account_id = account_id or get_primary_account_id()
    data = _get(
        f"accounts/{account_id}/messages/view",
        params={"limit": limit, "folderId": folder_id},
    )
    return data.get("data", [])
