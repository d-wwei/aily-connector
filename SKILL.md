---
name: aily-connector
description: |
  AnyWeb connector for Feishu Aily
  Query Aily APIs, send messages, read replies, list artifacts, and download generated files.
  Trigger on: aily-connector, aily_connector, aily.
  Message sending is allowed only when the user explicitly asks to send a message to Aily.
argument-hint: "[send|events|files|artifacts|download-workspace-file|query] ..."
allowed-tools: ["Bash", "Read"]
---

# Aily Connector

Use the local AnyWeb connector for Feishu Aily via internal API.

**Base URL**: `https://aily.feishu.cn`

Before low-level endpoint queries, read `SKILL_DIR/references/api-catalog.md` for endpoint documentation.

---

## First-time Setup

### Cookie-provider auto-fetch (recommended)

Cookie expiry triggers auto-refresh via cookie-provider.
If SSO session also expires:
```bash
/cookie-provider login
```

### Manual credentials (without cookie-provider)

If cookie-provider is unavailable, create `~/.aily_connector/credentials.env`
from `credentials.env.example`. Use your own browser session only:

```bash
mkdir -p ~/.aily_connector
cp SKILL_DIR/credentials.env.example ~/.aily_connector/credentials.env
chmod 600 ~/.aily_connector/credentials.env
```

Set `AILY_CONNECTOR_COOKIE` to the Cookie header value for `https://aily.feishu.cn`.
Set `AILY_CONNECTOR_CSRF` to the value of the `lgw_csrf_token` cookie.

---

## Session Startup: Preflight Check

**Every new session**, run before querying:

```bash
python3 SKILL_DIR/scripts/preflight.py
```

If cookie expired, preflight.py will auto-refresh via cookie-provider.
If SSO also expired, run `/cookie-provider login`.

---

## High-Level Aily Commands

Prefer `scripts/aily.py` for normal use:

```bash
# Send a message, create a conversation automatically, and wait for the reply.
python3 SKILL_DIR/scripts/aily.py send '请只回复 OK' --wait

# Continue an existing conversation.
python3 SKILL_DIR/scripts/aily.py send '继续总结' --conversation-id <conversation_id> --wait

# Read conversation replies/events.
python3 SKILL_DIR/scripts/aily.py events <conversation_id> --summary

# List files/artifacts attached to a conversation.
python3 SKILL_DIR/scripts/aily.py files <conversation_id>

# Read artifact metadata.
python3 SKILL_DIR/scripts/aily.py artifacts <artifact_id>

# Download generated workspace file/image.
python3 SKILL_DIR/scripts/aily.py download-workspace-file <conversation_id> /home/workspace/artifacts/example.png --output ./example.png
```

Recorded message workflow capabilities:

- Create conversation: `POST /play/api/v1/conversations`
- Send async message: `POST /play/api/v1/chat/async`
- Read replies/events: `GET /play/api/v1/conversations/{id}/events`
- List generated files: `GET /play/api/v1/conversations/{id}/files`
- Fetch artifact metadata: `POST /play/api/v1/artifacts/mget`
- Download generated files/images: `GET /play/api/v1/conversations/{id}/workspace/file?path=...`

Do not call trigger creation or other configuration-changing endpoints unless the user explicitly asks for that write action.

## Low-Level Query Command

```bash
python3 SKILL_DIR/scripts/query.py --endpoint <endpoint_name> [OPTIONS]
```

### Available Endpoints

| Endpoint Name | Method | Path | Description |
|--------------|--------|------|-------------|
| `default` | GET | `/` | 自动纳入: 安全只读方法 (GET) |
| `app-settings` | GET | `/ai/api/v1/bff/app/settings` | 自动纳入: 安全只读方法 (GET) |
| `admin-tenant_info` | GET | `/play/api/v1/admin/tenant_info` | 自动纳入: 安全只读方法 (GET) |
| `v1-check_fg_access` | GET | `/play/api/v1/check_fg_access` | 自动纳入: 安全只读方法 (GET) |
| `enterprise-knowledge` | GET | `/play/api/v1/check/enterprise/knowledge` | 自动纳入: 安全只读方法 (GET) |
| `tcc-config` | GET | `/play/api/v1/tcc/config` | 自动纳入: 安全只读方法 (GET) |
| `tenant_display-full_conf` | GET | `/play/api/v1/user/tenant_display/full_conf` | 自动纳入: 安全只读方法 (GET) |
| `tenant-aily_releated_tenants` | GET | `/ai/api/v1/tenant/aily_releated_tenants` | 自动纳入: 安全只读方法 (GET) |
| `v1-placeholder` | GET | `/play/api/v1/placeholder` | 自动纳入: 安全只读方法 (GET) |
| `trigger-list` | GET | `/play/api/v1/trigger/list` | 自动纳入: 安全只读方法 (GET) |
| `user-info` | GET | `/play/api/v1/user/info` | 自动纳入: 安全只读方法 (GET) |
| `claim-status` | GET | `/play/api/v1/bots/claim/status` | 自动纳入: 安全只读方法 (GET) |
| `ws-token` | GET | `/play/api/v1/ws/token` | 自动纳入: 安全只读方法 (GET) |
| `entitlement-user_entitlement` | GET | `/play/api/v1/entitlement/user_entitlement` | 自动纳入: 安全只读方法 (GET) |
| `v1-speech_access_token` | GET | `/play/api/v1/speech_access_token` | 自动纳入: 安全只读方法 (GET) |
| `templates-types` | GET | `/play/api/v1/templates/types` | 自动纳入: 安全只读方法 (GET) |
| `v1-runtime_templates` | GET | `/play/api/v1/runtime_templates` | 自动纳入: 安全只读方法 (GET) |
| `v1-conversations` | GET | `/play/api/v1/conversations` | 自动纳入: 安全只读方法 (GET) |

### Common Options

- `--params '<json>'` — Request parameters as JSON string (required for most POST endpoints)
- `--output <file>` — Save result to file (default: stdout)
- `--page <n>` — Page number (if endpoint supports pagination)
- `--page-size <n>` — Page size (if endpoint supports pagination)
- `--list` — List all available endpoints

### Quick Start Examples

```bash
# default (GET)
python3 SKILL_DIR/scripts/query.py --endpoint default
```

```bash
# app-settings (GET)
python3 SKILL_DIR/scripts/query.py --endpoint app-settings
```

```bash
# admin-tenant_info (GET)
python3 SKILL_DIR/scripts/query.py --endpoint admin-tenant_info
```

```bash
# v1-check_fg_access (GET)
python3 SKILL_DIR/scripts/query.py --endpoint v1-check_fg_access
```

```bash
# enterprise-knowledge (GET)
python3 SKILL_DIR/scripts/query.py --endpoint enterprise-knowledge
```


For full parameter documentation, see `SKILL_DIR/references/api-catalog.md`.

---

## Error Handling

- **HTTP 401/403**: Auto-refreshed via cookie-provider
- If SSO expired: `/cookie-provider login`
- **Network error**: Check VPN connection

## Credential Storage

- **File**: `~/.aily_connector/credentials.env`
- **Variables**: `AILY_CONNECTOR_CSRF, AILY_CONNECTOR_COOKIE`
- **Permission**: chmod 600 (owner-only)
- **Never commit or reveal these values**

## Endpoint Metadata

All endpoint definitions are stored in `SKILL_DIR/config/endpoints.json`.
This file is the source of truth for incremental updates via site-skill-builder.
