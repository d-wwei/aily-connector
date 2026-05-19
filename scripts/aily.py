#!/usr/bin/env python3
"""
High-level Aily CLI.

Recorded capabilities:
- create a conversation
- send a message
- poll/read conversation events
- list conversation files
- read artifact metadata
- download files from the conversation workspace
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import load_env  # noqa: F401
import query as generated_query


BASE_URL = generated_query.BASE_URL
DEFAULT_AGENT_ID = "agent_play"
DEFAULT_TOOLS = ["deep_think", "enterprise_knowledge"]


def log(message: str) -> None:
    print(f"[aily] {message}", file=sys.stderr)


def _csrf_from_cookie(cookie_string: str) -> str:
    for item in cookie_string.split("; "):
        key, _, value = item.partition("=")
        if key == "lgw_csrf_token":
            return value
    return ""


def credentials() -> tuple[str, str]:
    csrf = os.environ.get("AILY_CONNECTOR_CSRF", "")
    cookie_string = os.environ.get("AILY_CONNECTOR_COOKIE", "")
    if not cookie_string:
        refreshed = generated_query.refresh_cookie_via_provider()
        if not refreshed:
            raise SystemExit(
                "Missing credentials. Run preflight.py, cookie-provider login, "
                "or create ~/.aily_connector/credentials.env from credentials.env.example."
            )
        csrf, cookie_string = refreshed
    if not csrf:
        csrf = _csrf_from_cookie(cookie_string)
    return csrf or "", cookie_string


def headers(accept: str = "application/json, text/plain, */*") -> dict[str, str]:
    csrf, cookie_string = credentials()
    result = generated_query.build_headers(csrf, cookie_string)
    result["Accept"] = accept
    return result


def request_json(method: str, path: str, payload: dict | None = None,
                 params: dict | None = None) -> dict:
    url = f"{BASE_URL}{path}"
    if params:
        query_string = urllib.parse.urlencode(params, doseq=True)
        url = f"{url}?{query_string}"
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method.upper())
    for key, value in headers().items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        log(f"HTTP {exc.code}: {body[:1000]}")
        raise SystemExit(1)
    return json.loads(body)


def create_conversation(tool_list: list[str] | None = None) -> dict:
    payload = {
        "config": {"toolList": tool_list or DEFAULT_TOOLS},
        "type": 2,
        "outputConfig": {
            "strategy": 2,
            "wsConfig": {"deviceID": "0", "clientVersion": 1},
        },
    }
    return request_json("POST", "/play/api/v1/conversations", payload=payload)


def send_message(conversation_id: str, message: str, expected_type: str | None = None,
                 web_search: bool = False, enterprise_knowledge: bool = True,
                 gen_page: bool = True) -> dict:
    parts = [{"type": "text", "text": message}]
    if expected_type:
        parts.append({"type": "text", "text": f"<预期产物类别>{expected_type}</预期产物类别>"})
    payload = {
        "conversationID": conversation_id,
        "userMessage": {
            "role": "user",
            "content": message,
            "attachmentIDs": [],
            "quoteAttachmentIDs": [],
            "parts": parts,
        },
        "options": {
            "model": "",
            "lang": "zh_cn",
            "mcpServers": [],
            "toolSwitch": {
                "enterprise_knowledge": enterprise_knowledge,
                "web_search": web_search,
                "gen_page": gen_page,
            },
            "tag": {},
        },
    }
    return request_json("POST", "/play/api/v1/chat/async", payload=payload)


def get_events(conversation_id: str, page_size: int = 30,
               include_history: bool = True) -> dict:
    return request_json(
        "GET",
        f"/play/api/v1/conversations/{conversation_id}/events",
        params={"pageSize": page_size, "includeHistory": str(include_history).lower()},
    )


def list_files(conversation_id: str) -> dict:
    return request_json("GET", f"/play/api/v1/conversations/{conversation_id}/files")


def get_artifacts(artifact_ids: list[str]) -> dict:
    return request_json("POST", "/play/api/v1/artifacts/mget", payload={"artifactIDs": artifact_ids})


def _message_from_event(event: dict) -> dict | None:
    message = (event.get("eventData") or {}).get("message")
    if not isinstance(message, dict):
        return None
    content = message.get("content") or ""
    tool_messages = []
    for call in message.get("tool_calls") or []:
        function = call.get("function") or {}
        if function.get("name") == "message":
            try:
                args = json.loads(function.get("arguments") or "{}")
                if args.get("message"):
                    tool_messages.append(args["message"])
            except json.JSONDecodeError:
                pass
    return {
        "event_id": event.get("id"),
        "role": message.get("role"),
        "status": message.get("status"),
        "content": content,
        "tool_messages": tool_messages,
        "created_at": message.get("createdAt"),
    }


def _artifact_from_event(event: dict) -> dict | None:
    artifact = (event.get("eventData") or {}).get("artifact")
    if not isinstance(artifact, dict):
        return None
    return {
        "id": artifact.get("id"),
        "name": artifact.get("name") or artifact.get("label"),
        "subType": artifact.get("subType"),
        "type": artifact.get("type"),
        "files": artifact.get("files") or [],
        "typeMeta": artifact.get("typeMeta") or {},
    }


def summarize_events(events_response: dict) -> dict:
    events = (events_response.get("data") or {}).get("events") or []
    messages = [item for item in (_message_from_event(event) for event in events) if item]
    artifacts = [item for item in (_artifact_from_event(event) for event in events) if item]
    return {
        "event_count": len(events),
        "messages": messages,
        "artifacts": artifacts,
    }


def download_workspace_file(conversation_id: str, remote_path: str, output: str | None = None) -> dict:
    params = urllib.parse.urlencode({"path": remote_path})
    url = f"{BASE_URL}/play/api/v1/conversations/{conversation_id}/workspace/file?{params}"
    req = urllib.request.Request(url, method="GET")
    for key, value in headers("*/*").items():
        req.add_header(key, value)
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
        final_url = resp.url
        content_type = resp.headers.get("content-type", "")
    output_path = Path(output or Path(remote_path).name).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(data)
    return {
        "output": str(output_path),
        "bytes": len(data),
        "content_type": content_type,
        "final_url_host": urllib.parse.urlparse(final_url).netloc,
    }


def print_json(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_create(args: argparse.Namespace) -> None:
    result = create_conversation(args.tool or None)
    print_json(result)


def cmd_send(args: argparse.Namespace) -> None:
    conversation_id = args.conversation_id
    created = None
    if not conversation_id:
        created = create_conversation(args.tool or None)
        conversation_id = ((created.get("data") or {}).get("conversation") or {}).get("id")
        if not conversation_id:
            print_json(created)
            raise SystemExit("Could not create conversation.")
    send_result = send_message(
        conversation_id,
        args.message,
        expected_type=args.expected_type,
        web_search=args.web_search,
        enterprise_knowledge=not args.no_enterprise_knowledge,
        gen_page=not args.no_gen_page,
    )
    output = {"conversation_id": conversation_id, "send_result": send_result}
    if created:
        output["created"] = created
    if args.wait:
        deadline = time.time() + args.timeout
        last_summary = {}
        while time.time() < deadline:
            events = get_events(conversation_id, page_size=args.page_size, include_history=True)
            last_summary = summarize_events(events)
            if last_summary.get("artifacts"):
                break
            messages = last_summary.get("messages") or []
            if any(m.get("content") or m.get("tool_messages") for m in messages):
                if time.time() + args.interval >= deadline:
                    break
            time.sleep(args.interval)
        output["events_summary"] = last_summary
    print_json(output)


def cmd_events(args: argparse.Namespace) -> None:
    events = get_events(args.conversation_id, args.page_size, include_history=not args.no_history)
    print_json(summarize_events(events) if args.summary else events)


def cmd_files(args: argparse.Namespace) -> None:
    print_json(list_files(args.conversation_id))


def cmd_artifacts(args: argparse.Namespace) -> None:
    print_json(get_artifacts(args.artifact_id))


def cmd_download(args: argparse.Namespace) -> None:
    print_json(download_workspace_file(args.conversation_id, args.path, args.output))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Aily high-level CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create-conversation")
    create.add_argument("--tool", action="append", help="Tool id; may be repeated")
    create.set_defaults(func=cmd_create)

    send = sub.add_parser("send")
    send.add_argument("message")
    send.add_argument("--conversation-id")
    send.add_argument("--expected-type", help="Optional expected artifact type, e.g. 图片 or 文件")
    send.add_argument("--tool", action="append", help="Tool id for new conversations; may be repeated")
    send.add_argument("--web-search", action="store_true")
    send.add_argument("--no-enterprise-knowledge", action="store_true")
    send.add_argument("--no-gen-page", action="store_true")
    send.add_argument("--wait", action="store_true")
    send.add_argument("--timeout", type=int, default=120)
    send.add_argument("--interval", type=float, default=3)
    send.add_argument("--page-size", type=int, default=30)
    send.set_defaults(func=cmd_send)

    events = sub.add_parser("events")
    events.add_argument("conversation_id")
    events.add_argument("--page-size", type=int, default=30)
    events.add_argument("--no-history", action="store_true")
    events.add_argument("--summary", action="store_true")
    events.set_defaults(func=cmd_events)

    files = sub.add_parser("files")
    files.add_argument("conversation_id")
    files.set_defaults(func=cmd_files)

    artifacts = sub.add_parser("artifacts")
    artifacts.add_argument("artifact_id", nargs="+")
    artifacts.set_defaults(func=cmd_artifacts)

    download = sub.add_parser("download-workspace-file")
    download.add_argument("conversation_id")
    download.add_argument("path")
    download.add_argument("--output")
    download.set_defaults(func=cmd_download)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
