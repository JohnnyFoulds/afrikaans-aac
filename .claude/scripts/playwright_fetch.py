"""
Shared Playwright fetch logic used by fetch_page.py and fetch_auth.py.

Not invoked directly — import and call fetch().
"""
import sys
import time
from playwright.sync_api import sync_playwright

USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
)


def parse_opts(opts, default_wait_secs=5):
    """Parse option list into a config dict."""
    mode_html = '--html' in opts
    do_scroll = '--scroll' in opts
    wait_sel = None
    click_sels = []
    wait_secs = default_wait_secs

    i = 0
    while i < len(opts):
        if opts[i] == '--click' and i + 1 < len(opts):
            click_sels = [s.strip() for s in opts[i + 1].split(',')]
            i += 2
        elif opts[i] == '--wait' and i + 1 < len(opts):
            wait_sel = opts[i + 1]
            i += 2
        elif opts[i] == '--wait-seconds' and i + 1 < len(opts):
            wait_secs = int(opts[i + 1])
            i += 2
        else:
            i += 1

    return {
        'mode_html': mode_html,
        'do_scroll': do_scroll,
        'wait_sel': wait_sel,
        'click_sels': click_sels,
        'wait_secs': wait_secs,
    }


def fetch(url, cfg, label, cookies=None):
    """
    Fetch a page with Playwright and print the result to stdout.

    Args:
        url:     The URL to fetch.
        cfg:     Config dict from parse_opts().
        label:   Trace prefix, e.g. 'fetch-page' or 'fetch-auth'.
        cookies: Optional list of cookie dicts to inject (for authenticated fetches).
    """
    def log(msg):
        print(f"[{label}] {msg}", file=sys.stderr)

    log(f"url={url}")
    log(f"mode={'html' if cfg['mode_html'] else 'text'} "
        f"scroll={cfg['do_scroll']} "
        f"wait_sel={cfg['wait_sel']!r} "
        f"click_sels={cfg['click_sels']} "
        f"wait_secs={cfg['wait_secs']}")

    with sync_playwright() as p:
        log("launching headless Chromium...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT)

        if cookies:
            log(f"injecting {len(cookies)} cookies...")
            context.add_cookies(cookies)

        page = context.new_page()
        log(f"navigating to {url}...")
        page.goto(url, timeout=30000)

        if cfg['wait_sel']:
            log(f"waiting for selector {cfg['wait_sel']!r}...")
            page.wait_for_selector(cfg['wait_sel'], timeout=15000)
        else:
            log(f"waiting {cfg['wait_secs']}s for JS render...")
            time.sleep(cfg['wait_secs'])

        if cfg['do_scroll']:
            log("scrolling to trigger lazy-load...")
            for i in range(5):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                time.sleep(1)
                log(f"  scroll pass {i + 1}/5")
            page.evaluate('window.scrollTo(0, 0)')
            time.sleep(1)

        for sel in cfg['click_sels']:
            try:
                elements = page.query_selector_all(sel)
                log(f"clicking selector {sel!r} — {len(elements)} element(s) found")
                for el in elements:
                    try:
                        el.click()
                        time.sleep(0.5)
                    except Exception as e:
                        log(f"  click failed: {e}")
            except Exception as e:
                log(f"selector query failed for {sel!r}: {e}")

        if cfg['click_sels']:
            log("waiting 2s after clicks...")
            time.sleep(2)

        log("extracting content...")
        output = page.content() if cfg['mode_html'] else page.inner_text('body')
        log(f"done — {len(output)} chars extracted")

        browser.close()
        print(output)
