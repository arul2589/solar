"""Tiny in-process sliding-window rate limiter for the public form (one API process).
Behind several workers use a shared store; documented in DECISIONS.md."""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

_lock = threading.Lock()
_hits: dict[str, deque] = defaultdict(deque)


def allow(key: str, limit: int, window_s: int = 3600) -> bool:
    now = time.time()
    with _lock:
        q = _hits[key]
        while q and q[0] < now - window_s:
            q.popleft()
        if len(q) >= limit:
            return False
        q.append(now)
        return True


def blocked(key: str, limit: int, window_s: int = 900) -> bool:
    """True if `key` already has `limit` recorded hits in the window (does not record a hit)."""
    now = time.time()
    with _lock:
        q = _hits[key]
        while q and q[0] < now - window_s:
            q.popleft()
        return len(q) >= limit


def record(key: str) -> None:
    with _lock:
        _hits[key].append(time.time())


def clear(key: str) -> None:
    with _lock:
        _hits.pop(key, None)


def reset() -> None:
    with _lock:
        _hits.clear()
