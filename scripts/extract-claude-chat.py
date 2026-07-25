#!/usr/bin/env python3
"""
Extract the full content of a Claude.ai conversation to Markdown.

Usage:
    # With CDP (Chrome must be running with --remote-debugging-port=9222):
    python3 scripts/extract-claude-chat.py --url https://claude.ai/chat/<id> --cdp

    # With Playwright headless (requires an active claude.ai session cookie):
    python3 scripts/extract-claude-chat.py --url https://claude.ai/chat/<id>

    # Save output to a specific file:
    python3 scripts/extract-claude-chat.py --url https://claude.ai/chat/<id> --output notes/chat-export.md

Requirements:
    - playwright (conda env afrikaans-aac)
    - For --cdp: Chrome running with --remote-debugging-port=9222
    - For headless: CLAUDE_SESSION_COOKIE env var or --cookie flag with sessionKey value
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")[:80]


def extract_chat_via_playwright(url: str, session_cookie: str | None = None) -> dict:
    """
    Launch real Chrome, inject session cookies, intercept the API response
    that claude.ai makes when loading the chat, and return parsed JSON.
    This bypasses Cloudflare because we use the real Chrome binary.
    """
    chat_id = url.rstrip("/").split("/")[-1]
    captured = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=False,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        cookies = []
        if session_cookie:
            cookies.append({"name": "sessionKey", "value": session_cookie,
                            "domain": ".claude.ai", "path": "/", "httpOnly": True, "secure": True})
        # Try to pull cf_clearance + lastActiveOrg from real Chrome store automatically
        try:
            import sqlite3, shutil, tempfile, re as _re, os as _os
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            from cryptography.hazmat.primitives import hashes as _hashes
            from cryptography.hazmat.backends import default_backend as _backend
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            import subprocess as _sp
            pw_result = _sp.run(["security", "find-generic-password", "-wa", "Chrome"],
                                capture_output=True, text=True)
            if pw_result.returncode == 0:
                password = pw_result.stdout.strip().encode("utf-8")
                kdf = PBKDF2HMAC(algorithm=_hashes.SHA1(), length=16, salt=b"saltysalt",
                                 iterations=1003, backend=_backend())
                key = kdf.derive(password)
                src = _os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Cookies")
                tmp = tempfile.mktemp(suffix=".db")
                shutil.copy2(src, tmp)
                conn = sqlite3.connect(tmp)
                cur = conn.cursor()
                cur.execute("SELECT name, encrypted_value FROM cookies WHERE host_key LIKE '%claude.ai%' "
                            "AND name IN ('cf_clearance','lastActiveOrg')")
                rows = cur.fetchall()
                conn.close()
                _os.unlink(tmp)
                for name, enc in rows:
                    if enc[:3] == b"v10":
                        iv = b" " * 16
                        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=_backend())
                        dec = cipher.decryptor()
                        decrypted = dec.update(enc[3:]) + dec.finalize()
                        pad = decrypted[-1]
                        val = decrypted[:-pad].decode("latin-1")
                        cookies.append({"name": name, "value": val, "domain": ".claude.ai",
                                        "path": "/", "httpOnly": False, "secure": True})
        except Exception as e:
            print(f"[WARN] could not auto-load Chrome cookies: {e}", file=sys.stderr)

        if cookies:
            ctx.add_cookies(cookies)

        page = ctx.new_page()

        def on_response(response):
            if chat_id in response.url and "chat_conversations" in response.url:
                print(f"[API] {response.status} {response.url}", file=sys.stderr)
                if response.status == 200:
                    try:
                        captured["data"] = response.json()
                    except Exception as e:
                        print(f"  parse error: {e}", file=sys.stderr)

        page.on("response", on_response)
        print(f"Navigating to {url} …", file=sys.stderr)
        page.goto(url, wait_until="domcontentloaded", timeout=30000)

        for _ in range(15):
            if "data" in captured:
                break
            time.sleep(1)

        title = page.title().replace(" - Claude", "").strip()
        browser.close()

    if "data" not in captured:
        return {"url": url, "title": title, "turns": [], "raw_text": "API capture failed."}

    data = captured["data"]
    turns = []
    for msg in data.get("chat_messages", []):
        role = "human" if msg.get("sender") == "human" else "assistant"
        parts = []
        for block in msg.get("content", []):
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block["text"])
        turns.append({"role": role, "content": "\n".join(parts)})

    return {"url": url, "title": data.get("name", title), "turns": turns, "_raw": data}


def extract_chat_cdp(url: str, cdp_port: int = 9222) -> dict:
    """Connect to an already-running Chrome via CDP and extract the chat."""
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{cdp_port}")
        context = browser.contexts[0]
        page = context.new_page()

        print(f"Navigating to {url} …", file=sys.stderr)
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(6)  # let React fully render

        return _extract_from_page(page, url)


def extract_chat_headless(url: str, session_cookie: str | None = None) -> dict:
    """Launch a headless Chromium and extract the chat using a session cookie."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox"],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36"
        )

        if session_cookie:
            context.add_cookies([{
                "name": "sessionKey",
                "value": session_cookie,
                "domain": "claude.ai",
                "path": "/",
                "httpOnly": True,
                "secure": True,
            }])

        page = context.new_page()
        print(f"Navigating to {url} …", file=sys.stderr)
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(8)

        return _extract_from_page(page, url)


def _extract_from_page(page, url: str) -> dict:
    """DOM scrape: pull every human/assistant turn from the rendered page."""

    # Wait for at least one message bubble to appear
    try:
        page.wait_for_selector('[data-testid="human-turn"], [data-testid="ai-turn"]',
                                timeout=20_000)
    except PlaywrightTimeoutError:
        # Fall back — dump raw text so the caller still gets something
        print("WARNING: could not find turn selectors; dumping visible text.", file=sys.stderr)
        return {
            "url": url,
            "title": page.title(),
            "turns": [],
            "raw_text": page.inner_text("body"),
        }

    # Try to get the conversation title
    title = page.title().replace(" - Claude", "").strip()

    turns = []

    # Scroll to the very top first so we don't miss earlier messages
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(1)

    # Collect all turn elements in DOM order
    turn_elements = page.query_selector_all(
        '[data-testid="human-turn"], [data-testid="ai-turn"]'
    )

    for el in turn_elements:
        role_attr = el.get_attribute("data-testid")
        role = "human" if role_attr == "human-turn" else "assistant"

        # Get the inner markdown-ish text; preserve code blocks as best we can
        # Try structured extraction first
        text = _extract_turn_text(el)
        turns.append({"role": role, "content": text})

    # If we got nothing via selectors, try a broader approach
    if not turns:
        turns = _fallback_extraction(page)

    return {"url": url, "title": title, "turns": turns}


def _extract_turn_text(el) -> str:
    """Extract readable text from a turn element, preserving code blocks."""
    # Pull code blocks out first (they lose formatting in inner_text)
    code_blocks = el.query_selector_all("pre code, pre")
    code_map = {}
    for i, code_el in enumerate(code_blocks):
        placeholder = f"__CODE_BLOCK_{i}__"
        lang_el = code_el.query_selector("[class*='language-']")
        lang = ""
        if lang_el:
            cls = lang_el.get_attribute("class") or ""
            m = re.search(r"language-(\w+)", cls)
            if m:
                lang = m.group(1)
        code_text = code_el.inner_text()
        code_map[placeholder] = f"```{lang}\n{code_text}\n```"

    # Get plain text representation
    full_text = el.inner_text()

    # Re-inject code blocks (best-effort; inner_text may already include them)
    # This won't produce perfect reconstruction but gives readable output
    return full_text


def _fallback_extraction(page) -> list[dict]:
    """Broader DOM walk when the standard selectors don't match."""
    print("Using fallback extraction …", file=sys.stderr)
    # Look for any large text containers that look like messages
    candidates = page.query_selector_all("div[class*='message'], div[class*='turn'], div[class*='chat']")
    turns = []
    for el in candidates:
        text = el.inner_text().strip()
        if len(text) > 50:  # skip tiny UI chrome elements
            turns.append({"role": "unknown", "content": text})
    return turns


def to_markdown(data: dict) -> str:
    """Convert extracted data to a clean Markdown document."""
    lines = []
    title = data.get("title", "Claude Chat Export")
    url = data.get("url", "")

    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"**Source:** {url}")
    lines.append(f"**Exported:** {time.strftime('%Y-%m-%d')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    turns = data.get("turns", [])
    if not turns:
        raw = data.get("raw_text", "")
        if raw:
            lines.append("*Note: structured extraction failed; raw page text follows.*")
            lines.append("")
            lines.append(raw)
        else:
            lines.append("*No content extracted.*")
        return "\n".join(lines)

    for turn in turns:
        role = turn["role"]
        content = turn["content"].strip()

        if role == "human":
            lines.append("## Human")
        elif role == "assistant":
            lines.append("## Assistant")
        else:
            lines.append(f"## [{role}]")

        lines.append("")
        lines.append(content)
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Extract a Claude.ai chat to Markdown.")
    parser.add_argument("--url", required=True, help="Full claude.ai/chat/<id> URL")
    parser.add_argument("--cdp", action="store_true",
                        help="Connect via CDP to running Chrome (port 9222)")
    parser.add_argument("--cdp-port", type=int, default=9222)
    parser.add_argument("--cookie", default=None,
                        help="sessionKey cookie value (for headless mode)")
    parser.add_argument("--output", default=None,
                        help="Output .md file path (default: auto-generated in notes/)")
    parser.add_argument("--json", action="store_true",
                        help="Also save raw JSON alongside the Markdown")
    args = parser.parse_args()

    session_cookie = args.cookie or os.environ.get("CLAUDE_SESSION_COOKIE")

    if args.cdp:
        data = extract_chat_cdp(args.url, cdp_port=args.cdp_port)
    else:
        data = extract_chat_headless(args.url, session_cookie=session_cookie)

    md = to_markdown(data)

    # Determine output path
    if args.output:
        out_path = Path(args.output)
    else:
        chat_id = args.url.rstrip("/").split("/")[-1]
        title_slug = slugify(data.get("title", chat_id))
        repo_root = Path(__file__).parent.parent
        out_path = repo_root / "notes" / "chat-exports" / f"{title_slug}-{chat_id[:8]}.md"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")
    print(f"Saved to: {out_path}", file=sys.stderr)
    print(out_path)  # stdout: machine-readable path

    if args.json:
        json_path = out_path.with_suffix(".json")
        json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"JSON saved to: {json_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
