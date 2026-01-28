# Database Models API

The backend utilizes **SQLAlchemy** for ORM-based interactions with the SQLite/PostgreSQL database.

Location: `backend/app/models/`

---

## User Model

**File**: [`user.py`](../backend/app/models/user.py)

Represents the identity of an actor in the system. The system supports both authenticated "Registered Users" and temporary "Guest Users".

```python
class User(Base):
    __tablename__ = "Users"
```

| Field Name | Type | Key | Description |
| :--- | :--- | :--- | :--- |
| `id` | `String` | **PK** | Unique Identifier (typically UUID). |
| `username` | `String` | | Display name (Nullable for guests). |
| `email` | `String` | | Login email (Nullable for guests). |
| `is_guest` | `Boolean` | | `True` for temporary sessions, `False` for persistent accounts. |
| `tool_permissions` | `List` | | One-to-Many relation to `ToolPermission`. |

---

## MCP Server Settings

**File**: [`settings.py`](../backend/app/models/settings.py)

This is a critical model that stores the **User Configuration** for external tools. It holds the "keys to the kingdom" (auth tokens), so security here is paramount.

```python
class McpServerSetting(Base):
    __tablename__ = "mcp_server_settings"
```

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `server_name` | `String` | **Unique Index (with user_id)**. A user-friendly name (e.g., "My Notion"). |
| `server_url` | `String` | The endpoint (e.g., `https://api.notion.com/v1/mcp`). |
| `credentials` | `JSON String` | **SENSITIVE**. Stores `{access_token, refresh_token}`. In production, this column should be encrypted at rest. |
| `client_id` / `secret` | `String` | OAuth client details required for token refreshing. |
| `tools_manifest` | `JSON String` | A textual cache of the `tools/list` response. Used to speed up agent boot time by avoiding initial introspection network calls. |

---

## Tool Permissions

**File**: [`tool_permissions.py`](../backend/app/models/tool_permissions.py)

The system checks these records before allowing the Agent to invoke *any* tool.

### Model: `ToolPermission`
**Global Switch**: Controls whether a specific tool (e.g., "delete_page") is fundamentally enabled for a user on a server.

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `user_id` | `FK` | The owner. |
| `server_setting_id` | `FK` | The server this tool belongs to. |
| `tool_name` | `String` | The exact function name (e.g., `notion_archive_page`). |
| `is_enabled` | `Boolean` | If `False`, the tool is completely hidden from the Agent's view. |

### Model: `ToolApproval`
**Runtime Governance**: Used by the "Human-in-the-loop" system. Tracks whether a user has pre-approved a tool's execution.

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `approval_type` | `String` | Enum: `once` (approve just this call), `always` (whitelist for future), `never` (blacklist). |
| `expires_at` | `DateTime` | Optional. Allows granting temporary access (e.g., "Allow for 1 hour"). |
