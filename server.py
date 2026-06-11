"""
Zoho Mail MCP Server
Exposes Zoho Mail to Claude via the Model Context Protocol.

Tools available:
  - get_inbox        : Fetch recent inbox messages
  - search_emails    : Search by keyword
  - read_email       : Read full message content
  - get_folders      : List all mail folders
  - get_folder_mail  : Fetch messages from a specific folder
  - get_accounts     : List Zoho Mail accounts
"""

from mcp.server.fastmcp import FastMCP
from config import validate_config
import zoho_client as zoho

# Validate env vars at startup before anything else
validate_config()

mcp = FastMCP(
    name="zoho-mail",
    instructions="Read and search your Zoho Mail inbox from Claude."
)


# ─── Tools ────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_inbox(limit: int = 20) -> list[dict]:
    """
    Fetch the most recent emails from your Zoho Mail inbox.

    Args:
        limit: Number of messages to return (default 20, max 200).

    Returns:
        List of message summaries with subject, sender, date, and message ID.
    """
    limit = min(limit, 200)
    messages = zoho.get_inbox(limit=limit)
    return [_format_summary(m) for m in messages]


@mcp.tool()
def search_emails(query: str, limit: int = 20) -> list[dict]:
    """
    Search your Zoho Mail for emails matching a keyword or phrase.
    Searches across subject, body, and sender fields.

    Args:
        query: Search term (e.g. "invoice", "from:boss@example.com", "project alpha").
        limit: Max number of results to return (default 20).

    Returns:
        List of matching message summaries.
    """
    messages = zoho.search_emails(query=query, limit=limit)
    return [_format_summary(m) for m in messages]


@mcp.tool()
def read_email(message_id: str) -> dict:
    """
    Read the full content of a specific email including body text.
    Get the message_id from get_inbox() or search_emails() results.

    Args:
        message_id: The unique ID of the message to read.

    Returns:
        Full message with subject, sender, recipients, date, and body.
    """
    msg = zoho.read_email(message_id=message_id)
    return {
        "messageId": msg.get("messageId"),
        "subject": msg.get("subject"),
        "from": msg.get("fromAddress"),
        "to": msg.get("toAddress"),
        "date": msg.get("receivedTime"),
        "body": msg.get("content", ""),
        "hasAttachments": bool(msg.get("attachments")),
        "attachments": [
            {"name": a.get("attachmentName"), "size": a.get("attachmentSize")}
            for a in msg.get("attachments", [])
        ],
    }


@mcp.tool()
def get_folders() -> list[dict]:
    """
    List all mail folders in your Zoho Mail account.
    Use the folder ID with get_folder_mail() to read specific folders.

    Returns:
        List of folders with ID, name, and unread count.
    """
    folders = zoho.get_folders()
    return [
        {
            "folderId": f.get("folderId"),
            "name": f.get("folderName"),
            "unreadCount": f.get("unreadCount", 0),
            "messageCount": f.get("messageCount", 0),
        }
        for f in folders
    ]


@mcp.tool()
def get_folder_mail(folder_id: str, limit: int = 20) -> list[dict]:
    """
    Fetch emails from a specific folder (e.g. Sent, Drafts, or a custom folder).
    Use get_folders() to find valid folder IDs.

    Args:
        folder_id: The folder ID to read from.
        limit: Number of messages to return (default 20).

    Returns:
        List of message summaries.
    """
    messages = zoho.get_messages_in_folder(folder_id=folder_id, limit=limit)
    return [_format_summary(m) for m in messages]


@mcp.tool()
def get_accounts() -> list[dict]:
    """
    List all Zoho Mail accounts linked to your profile.
    Useful if you manage multiple email addresses.

    Returns:
        List of accounts with ID and email address.
    """
    accounts = zoho.get_accounts()
    return [
        {
            "accountId": a.get("accountId"),
            "email": a.get("primaryEmailAddress"),
            "displayName": a.get("displayName"),
        }
        for a in accounts
    ]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _format_summary(msg: dict) -> dict:
    """Normalise a message summary from Zoho's API response."""
    return {
        "messageId": msg.get("messageId"),
        "subject": msg.get("subject", "(no subject)"),
        "from": msg.get("fromAddress", ""),
        "date": msg.get("receivedTime", ""),
        "isRead": msg.get("isRead", False),
        "hasAttachments": msg.get("hasAttachment", False),
        "folderId": msg.get("folderId", ""),
        "summary": msg.get("summary", ""),
    }


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
