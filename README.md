# zoho-mail-mcp

A [Model Context Protocol](https://modelcontextprotocol.io/) server that connects Claude to your Zoho Mail account. Read, search, and navigate your inbox directly from Claude.

## Tools

| Tool | Description |
|------|-------------|
| `get_inbox` | Fetch recent messages from your inbox |
| `search_emails` | Search by keyword across subject, body, and sender |
| `read_email` | Read the full content of a specific message |
| `get_folders` | List all mail folders |
| `get_folder_mail` | Fetch messages from a specific folder |
| `get_accounts` | List linked Zoho Mail accounts |

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/LON/zoho-mail-mcp.git
cd zoho-mail-mcp
```

### 2. Install dependencies

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Register a Zoho API app

1. Go to [https://api-console.zoho.com/](https://api-console.zoho.com/)
2. Click **Add Client** → choose **Server-based Applications**
3. Fill in:
   - **Client Name**: `zoho-mail-mcp` (or anything you like)
   - **Homepage URL**: `http://localhost`
   - **Authorized Redirect URIs**: `http://localhost:8080/callback`
4. Click **Create** — you'll get a **Client ID** and **Client Secret**

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your `ZOHO_CLIENT_ID` and `ZOHO_CLIENT_SECRET`.

> **Regional accounts**: If your Zoho account is on a regional data centre (EU, India, Australia, Japan), update `ZOHO_ACCOUNTS_URL` and `ZOHO_MAIL_API_URL` accordingly. See `.env.example` for the correct URLs.

> **Note**: `.env` and the token file are resolved relative to the project
> directory, so the server works no matter what working directory the MCP
> client launches it from. If you override `TOKEN_FILE` in `.env`, use an
> absolute path.

### 5. Authenticate

Run the OAuth setup script once to authorise the app:

```bash
python auth.py
```

This will:
1. Print an authorisation URL — open it in your browser
2. Prompt you to grant access to your Zoho Mail
3. Ask you to paste the `code` from the redirect URL
4. Save your tokens to `.zoho_tokens.json`

Tokens refresh automatically after that — you won't need to repeat this step.

### 6. Test the server

```bash
python server.py
```

You should see the MCP server start with no errors.

---

## Connect to Claude

### Claude Desktop (recommended — install as an extension)

Newer versions of the Claude desktop app ignore custom `mcpServers` entries in
`claude_desktop_config.json`. Local MCP servers must be installed as **Desktop
Extensions** (`.mcpb` bundles) instead.

1. Edit `manifest.json` so `server.mcp_config.command` and `args` point to your
   venv's Python and `server.py` (absolute paths).
2. Zip the manifest into a bundle:

   ```powershell
   Compress-Archive -Path manifest.json -DestinationPath zoho-mail.zip -Force
   Move-Item zoho-mail.zip zoho-mail.mcpb -Force
   ```

3. In the Claude app: **Settings → Extensions**, then drag `zoho-mail.mcpb`
   onto the page (or **Advanced settings → Install extension…**) and enable it.
4. Start a **new conversation** — the Zoho Mail tools will be available.

If your app version rejects `.mcpb`, rename the bundle to `.dxt` and retry.

### Claude Desktop (older versions)

Older app versions read `claude_desktop_config.json` directly:

```json
{
  "mcpServers": {
    "zoho-mail": {
      "command": "/absolute/path/to/venv/bin/python",
      "args": ["/absolute/path/to/zoho-mail-mcp/server.py"]
    }
  }
}
```

Config file location:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Restart Claude Desktop after saving.

### Claude Code (CLI)

```bash
claude mcp add zoho-mail /absolute/path/to/venv/bin/python -- /absolute/path/to/server.py
```

---

## Usage examples

Once connected, you can ask Claude:

- *"Check my inbox and summarise the last 10 emails"*
- *"Search my email for anything from procurement@company.com"*
- *"Find emails about the Lihir contract and read the most recent one"*
- *"What folders do I have in Zoho Mail?"*
- *"Read message ID 12345"*

---

## Project structure

```
zoho-mail-mcp/
├── server.py          # MCP server — tool definitions
├── auth.py            # OAuth 2.0 flow handler
├── zoho_client.py     # Zoho Mail REST API wrapper
├── config.py          # Environment variable management
├── manifest.json      # Desktop Extension manifest (for .mcpb bundle)
├── requirements.txt
├── .env.example       # Template — copy to .env
├── .gitignore
└── README.md
```

---

## Security notes

- `.env` and `.zoho_tokens.json` are in `.gitignore` — never commit them
- Tokens are stored locally on your machine only
- The server requests read-only scopes by default (`ZohoMail.messages.READ`)
- To add write capabilities (send, delete), extend the scope in `auth.py` and add tools in `server.py`

---

## Extending the server

To add a new tool, add a function to `zoho_client.py` and decorate it in `server.py`:

```python
@mcp.tool()
def my_new_tool(param: str) -> dict:
    """Description Claude will use to decide when to call this tool."""
    return zoho.some_new_function(param)
```

Zoho Mail API reference: [https://www.zoho.com/mail/help/api/](https://www.zoho.com/mail/help/api/)

---

## Licence

MIT
