# Aily Connector

AnyWeb Connector for `https://aily.feishu.cn`.

This package is a portable web/API CLI connector. Claude and Codex use the same runtime CLI through adapter instructions.

## Can This Be Shared?

Yes, the connector code can be shared. Credentials cannot.

Each user must authenticate with their own Feishu/Aily account. This repository does not include cookies, OAuth tokens, recorded browser sessions, generated artifacts, or personal API responses.

Cookie-provider is optional:

- With cookie-provider: the CLI can fetch and refresh the user's local Aily session automatically.
- Without cookie-provider: create `~/.aily_connector/credentials.env` manually from `credentials.env.example`.

Manual credentials look like this:

```bash
mkdir -p ~/.aily_connector
cp credentials.env.example ~/.aily_connector/credentials.env
chmod 600 ~/.aily_connector/credentials.env
```

Fill `AILY_CONNECTOR_COOKIE` with your own `Cookie` header for `https://aily.feishu.cn`.
Fill `AILY_CONNECTOR_CSRF` with the value of the `lgw_csrf_token` cookie. Session cookies expire, so manual credentials may need to be refreshed.

## Quick Start

```bash
python3 scripts/preflight.py
python3 scripts/query.py --list
```

## High-Level Aily Commands

```bash
# Send a message, create a conversation automatically, and wait for the reply.
python3 scripts/aily.py send '请只回复 OK' --wait

# Read a conversation's events/replies.
python3 scripts/aily.py events <conversation_id> --summary

# List files/artifacts attached to a conversation.
python3 scripts/aily.py files <conversation_id>

# Read artifact metadata.
python3 scripts/aily.py artifacts <artifact_id>

# Download a generated workspace file/image.
python3 scripts/aily.py download-workspace-file <conversation_id> /home/workspace/artifacts/example.png --output ./example.png
```

Recorded message workflow endpoints include conversation creation, async chat send,
conversation events, artifact metadata, conversation file listing, and workspace
file download redirects.

## Codex / Claude Skill Use

Install or symlink this repository as a skill directory, then invoke it by name:

```bash
ln -s "$PWD" ~/.codex/skills/aily-connector
```

In Codex, ask for Aily work directly, for example:

```text
用 aily-connector 给 Aily 发消息：请只回复 OK
```

The included skill instructions prefer `scripts/aily.py` for sending messages,
reading replies, listing files/artifacts, and downloading generated files.

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


## Files

- `scripts/query.py` — endpoint whitelist and API caller
- `scripts/preflight.py` — credential and connectivity check
- `config/endpoints.json` — endpoint metadata
- `openapi.yaml` — standard OpenAPI export
- `references/api-catalog.md` — endpoint documentation
- `adapters/claude/SKILL.md` — Claude adapter
- `adapters/codex/SKILL.md` — Codex adapter

Credentials are stored outside this directory:

```text
~/.aily_connector/credentials.env
```

Do not commit that file or paste its values into chat.
