"""
Authenticated Playwright fetch script using real Chrome cookies.
Used by the /fetch-page-auth skill.

Usage:
    python fetch_auth.py <url> <cookie-domain> [options]

Cookie domain examples: .google.com, .linkedin.com, .sciencedirect.com

Options:
    --html              Return raw HTML instead of inner_text
    --scroll            Scroll to bottom incrementally before extracting
    --click "sel1,sel2" CSS selectors to click after load (inspect DOM with --html first)
    --wait "selector"   Wait for CSS selector to appear before extracting
    --wait-seconds N    Override default wait time (default: 8)
"""
import sys
import os
import browser_cookie3
sys.path.insert(0, os.path.dirname(__file__))
from playwright_fetch import parse_opts, fetch

url = sys.argv[1]
domain = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else None
opts = sys.argv[3:] if domain else sys.argv[2:]

print(f"[fetch-auth] extracting Chrome cookies for domain {domain!r}...", file=sys.stderr)
cj = browser_cookie3.chrome(domain_name=domain)
cookies = [
    {'name': c.name, 'value': c.value, 'domain': c.domain,
     'path': c.path, 'secure': bool(c.secure)}
    for c in cj
]
print(f"[fetch-auth] {len(cookies)} cookies loaded", file=sys.stderr)

cfg = parse_opts(opts, default_wait_secs=8)
fetch(url, cfg, label='fetch-auth', cookies=cookies)
