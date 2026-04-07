"""
Anonymous headless Playwright fetch script.
Used by the /fetch-page skill.

Usage:
    python fetch_page.py <url> [options]

Options:
    --html              Return raw HTML instead of inner_text
    --scroll            Scroll to bottom incrementally before extracting
    --click "sel1,sel2" CSS selectors to click after load (inspect DOM with --html first)
    --wait "selector"   Wait for CSS selector to appear before extracting
    --wait-seconds N    Override default wait time (default: 5)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from playwright_fetch import parse_opts, fetch

url = sys.argv[1]
cfg = parse_opts(sys.argv[2:], default_wait_secs=5)
fetch(url, cfg, label='fetch-page')
