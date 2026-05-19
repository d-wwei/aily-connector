---
name: aily-connector
description: |
  AnyWeb connector for Feishu Aily
  Send messages to Aily, read replies, list artifacts, and download generated files.
  Trigger on: aily-connector, aily_connector, aily.
argument-hint: "[send|events|files|artifacts|download-workspace-file|query] ..."
---

# Aily Connector

This is an AnyWeb Connector: a portable web API CLI package with a Codex adapter.

Prefer `scripts/aily.py` for high-level Aily workflows. Read `references/api-catalog.md` before low-level endpoint queries.

## Preflight

```bash
python3 scripts/preflight.py
```

If cookie-provider is unavailable, create `~/.aily_connector/credentials.env`
from `credentials.env.example`. Set `AILY_CONNECTOR_COOKIE` to the Cookie
header value for `https://aily.feishu.cn`, and set `AILY_CONNECTOR_CSRF` to
the value of the `lgw_csrf_token` cookie. Never commit or reveal these values.

## Query

```bash
python3 scripts/query.py --endpoint <endpoint_name> [--params JSON]
```

## High-Level Commands

```bash
python3 scripts/aily.py send '请只回复 OK' --wait
python3 scripts/aily.py events <conversation_id> --summary
python3 scripts/aily.py files <conversation_id>
python3 scripts/aily.py artifacts <artifact_id>
python3 scripts/aily.py download-workspace-file <conversation_id> /home/workspace/artifacts/example.png --output ./example.png
```

## Available Endpoints

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

## Safety

- Sending messages to Aily is allowed only when the user explicitly asks.
- Low-level `query.py` runtime calls are restricted to the generated endpoint whitelist.
- Do not call trigger creation or configuration-changing endpoints unless explicitly requested.
- Credentials live outside the connector source tree in `~/.aily_connector/credentials.env`.
