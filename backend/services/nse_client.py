"""
Shared NSE India HTTP session.
Centralises cookie management and browser-like headers so all services
share the same authenticated session without conflicting refreshes.
"""

import requests
import threading
import time

NSE_BASE = 'https://www.nseindia.com'

_NSE_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/123.0.0.0 Safari/537.36'
    ),
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Referer': 'https://www.nseindia.com/',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
}

_session: requests.Session = None  # type: ignore
_lock = threading.Lock()
_created_at: float = 0.0
_TTL: float = 240.0  # Refresh every 4 minutes


def get_session() -> requests.Session:
    """Return a live NSE session, creating or refreshing it as needed."""
    global _session, _created_at
    now = time.time()
    # Fast path: session is fresh
    if _session is not None and (now - _created_at) < _TTL:
        return _session
    with _lock:
        now = time.time()
        if _session is not None and (now - _created_at) < _TTL:
            return _session
        sess = requests.Session()
        sess.headers.update(_NSE_HEADERS)
        # Visit the home page to collect cookies (bot-mitigation warm-up)
        try:
            sess.get(NSE_BASE, timeout=10)
            time.sleep(0.25)
        except Exception:
            pass
        _session = sess
        _created_at = time.time()
    return _session
