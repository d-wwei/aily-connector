#!/usr/bin/env python3
"""
Aily Connector — Preflight Check.

Validate credentials and connectivity.

Usage:
    python3 preflight.py
"""

import json
import os
import subprocess
import sys
import platform
import time
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import load_env

# cookie-provider paths
_VENV_BIN = "Scripts" if platform.system() == "Windows" else "bin"
_VENV_PY = "python.exe" if platform.system() == "Windows" else "python3"


def _cookie_provider_candidates():
    if os.environ.get("COOKIE_PROVIDER_DIR"):
        yield os.path.expanduser(os.environ["COOKIE_PROVIDER_DIR"])
    yield os.path.expanduser("~/.anyweb/deps/cookie-provider")
    yield os.path.expanduser("~/.claude/skills/cookie-provider")
    yield os.path.expanduser("~/.codex/skills/cookie-provider")


def _resolve_cookie_provider():
    for root in _cookie_provider_candidates():
        get_cookie = os.path.join(root, "scripts", "get_cookie.py")
        if not os.path.isfile(get_cookie):
            continue
        venv_python = os.path.join(root, "scripts", "venv", _VENV_BIN, _VENV_PY)
        return (venv_python if os.path.isfile(venv_python) else sys.executable), get_cookie
    return None, None


PROVIDER_PYTHON, GET_COOKIE_SCRIPT = _resolve_cookie_provider()

BASE_URL = "https://aily.feishu.cn"
SITE_ALIAS = "aily"

# Test endpoint for connectivity check. The site root returns HTML, so use a
# lightweight JSON API captured from the authenticated Aily app.
TEST_ENDPOINT_PATH = "/play/api/v1/user/info"
TEST_ENDPOINT_METHOD = "GET"


CREDENTIALS_FILE = os.path.expanduser("~/.aily_connector/credentials.env")


def _save_credentials(csrf, cookie_string):
    """Persist credentials to credentials.env so query.py can use them."""
    from datetime import datetime
    lines = [
        "# Aily Connector credentials",
        f"# Auto-refreshed via cookie-provider: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"AILY_CONNECTOR_CSRF={csrf}",
        f"AILY_CONNECTOR_COOKIE={cookie_string}",
        "",
    ]
    os.makedirs(os.path.dirname(CREDENTIALS_FILE), exist_ok=True)
    with open(CREDENTIALS_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    if sys.platform != 'win32':
        os.chmod(CREDENTIALS_FILE, 0o600)


def try_cookie_provider():
    """Try to fetch cookie via cookie-provider. Returns dict or None."""
    if not PROVIDER_PYTHON or not GET_COOKIE_SCRIPT:
        return None
    try:
        result = subprocess.run(
            [PROVIDER_PYTHON, GET_COOKIE_SCRIPT, "--site", SITE_ALIAS, "--format", "json", "--auto-login"],
            capture_output=True, text=True, encoding="utf-8", timeout=360
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            cookies = data.get("cookies", {})
            csrf = (
                cookies.get("lgw_csrf_token", "")
                or cookies.get("csrfToken", "")
                or data.get("csrf_token", "")
                or ""
            )
            cookie_string = data.get("cookie_string", "")
            if cookie_string:
                return {"csrf": csrf, "cookie_string": cookie_string, "cookies": cookies}
        elif result.returncode == 1:
            print("[INFO] SSO expired, run: /cookie-provider login", file=sys.stderr)
    except Exception:
        pass
    return None


def _try_refresh_and_retry(url, headers, start_time):
    """尝试通过 cookie-provider 刷新 cookie 并重试连接。"""
    print("[INFO] Cookie expired, trying auto-refresh via cookie-provider...")
    provider_result = try_cookie_provider()
    if provider_result:
        csrf = provider_result["csrf"] or ""
        cookie_string = provider_result["cookie_string"]
        _save_credentials(csrf, cookie_string)
        os.environ["AILY_CONNECTOR_CSRF"] = csrf
        os.environ["AILY_CONNECTOR_COOKIE"] = cookie_string
        print(f"[INFO] Cookie refreshed: ...{cookie_string[-30:]}")
        headers = {
            "Cookie": cookie_string,
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Origin": BASE_URL,
            "User-Agent": "Mozilla/5.0",
        }
        if csrf:
            headers["X-LGW-CSRF-Token"] = csrf
        try:
            req2 = urllib.request.Request(url, method=TEST_ENDPOINT_METHOD)
            for k, v in headers.items():
                req2.add_header(k, v)
            with urllib.request.urlopen(req2, timeout=15) as resp2:
                body2 = json.loads(resp2.read().decode("utf-8"))
                elapsed2 = int((time.time() - start_time) * 1000)
                print(f"[OK] Connected after refresh ({elapsed2}ms)")
                print("=" * 50)
                return
        except Exception as e2:
            print(f"[FAIL] Retry after refresh failed: {e2}")
    else:
        print("Auto-refresh failed. Run: /cookie-provider login")
    sys.exit(1)


def main():
    print("=" * 50)
    print("  Aily Connector — Preflight Check")
    print("=" * 50)

    # Check credentials
    csrf = os.environ.get("AILY_CONNECTOR_CSRF", "")
    cookie_string = os.environ.get("AILY_CONNECTOR_COOKIE", "")

    if not cookie_string:
        print("[INFO] Credentials missing, trying cookie-provider...")
        provider_result = try_cookie_provider()
        if provider_result:
            csrf = provider_result["csrf"] or ""
            cookie_string = provider_result["cookie_string"]
            # Persist to credentials.env so query.py can use them
            _save_credentials(csrf, cookie_string)
            os.environ["AILY_CONNECTOR_CSRF"] = csrf
            os.environ["AILY_CONNECTOR_COOKIE"] = cookie_string
            print("[OK] Auto-fetched via cookie-provider and saved to credentials.env")
        else:
            if not cookie_string:
                print("[FAIL] AILY_CONNECTOR_COOKIE not set")
            print("  Option A: run /cookie-provider login")
            print("  Option B: copy credentials.env.example to ~/.aily_connector/credentials.env")
            print("            and fill AILY_CONNECTOR_COOKIE plus AILY_CONNECTOR_CSRF")
            sys.exit(1)

    csrf = csrf or ""
    print(f"[OK] CSRF: {csrf[:8]}..." if len(csrf) > 8 else f"[OK] CSRF: {csrf or '(empty)'}")
    print(f"[OK] Cookie: ...{cookie_string[-30:]}" if len(cookie_string) > 30
          else f"[OK] Cookie: {cookie_string}")

    # Test connectivity
    headers = {
        "Cookie": cookie_string,
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Origin": BASE_URL,
        "User-Agent": "Mozilla/5.0",
    }
    if csrf:
        headers["X-LGW-CSRF-Token"] = csrf

    print("-" * 50)
    start_time = time.time()

    try:
        url = f"{BASE_URL}{TEST_ENDPOINT_PATH}"
        if TEST_ENDPOINT_METHOD == "GET":
            req = urllib.request.Request(url, method="GET")
        else:
            req = urllib.request.Request(url, data=b"", method=TEST_ENDPOINT_METHOD)
        for k, v in headers.items():
            req.add_header(k, v)

        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            elapsed = int((time.time() - start_time) * 1000)
            # Check for session-expired in JSON body (HTTP 200 but code indicates expired)
            _SESSION_EXPIRED_CODES = {140001000, 140001001}
            if isinstance(body, dict) and body.get("code") in _SESSION_EXPIRED_CODES:
                print(f"[FAIL] Session expired (code={body.get('code')}) ({elapsed}ms)")
                _try_refresh_and_retry(url, headers, start_time)
                return
            print(f"[OK] Connected ({elapsed}ms)")

    except urllib.error.HTTPError as e:
        elapsed = int((time.time() - start_time) * 1000)
        body_text = e.read().decode("utf-8", errors="replace")[:500]
        print(f"[FAIL] HTTP {e.code} ({elapsed}ms)")
        print(f"  {body_text}")
        if e.code in (401, 403):
            _try_refresh_and_retry(url, headers, start_time)
            return
        sys.exit(1)

    except urllib.error.URLError as e:
        print(f"[FAIL] Network error: {e.reason}")
        sys.exit(2)

    print("=" * 50)


if __name__ == "__main__":
    main()
