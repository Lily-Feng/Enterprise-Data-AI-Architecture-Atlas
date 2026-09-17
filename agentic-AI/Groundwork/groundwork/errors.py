"""Structured failures.

A tool that fails by returning a string forces every caller to guess. The
corpus fetcher had exactly that shape, and the guess it forced was expensive:
Texas returns 403 to any fetcher and will do so on every future attempt, while
a timeout on the same URL should simply be tried again. Both arrived as
`(0, None, "something")`.

So failures carry the three things a caller actually branches on -- what kind
of failure, whether trying again could help, and how long to wait -- and the
same object serializes straight into a `tool_result` block with `is_error`
set, which is what an agent loop needs to reason about the failure rather than
stall on it.
"""

from __future__ import annotations

import json
import urllib.error
from dataclasses import asdict, dataclass
from typing import Literal

Category = Literal[
    "blocked",       # the host refuses automated access; trying again changes nothing
    "not_found",     # the URL is wrong or the page is gone; the manifest needs fixing
    "rate_limited",  # slow down and come back
    "unavailable",   # the server is having a bad day; retry with backoff
    "timeout",
    "network",
    "parse",
]

RETRYABLE: dict[Category, bool] = {
    "blocked": False,
    "not_found": False,
    "rate_limited": True,
    "unavailable": True,
    "timeout": True,
    "network": True,
    "parse": False,
}


@dataclass(frozen=True)
class ToolError:
    category: Category
    detail: str
    retry_after_ms: int | None = None
    is_error: bool = True

    @property
    def retryable(self) -> bool:
        return RETRYABLE[self.category]

    def as_tool_result(self) -> str:
        """The JSON an agent loop should see in a tool_result block."""
        payload = {**asdict(self), "retryable": self.retryable}
        return json.dumps(payload)

    def __str__(self) -> str:
        wait = f", retry in {self.retry_after_ms}ms" if self.retry_after_ms else ""
        return f"{self.category} ({'retryable' if self.retryable else 'permanent'}{wait}): {self.detail}"


def _retry_after_ms(exc: urllib.error.HTTPError) -> int | None:
    raw = exc.headers.get("Retry-After") if exc.headers else None
    if raw and raw.strip().isdigit():
        return int(raw.strip()) * 1000
    return None


def classify(exc: Exception) -> ToolError:
    """Turn whatever the network raised into something a caller can branch on."""
    if isinstance(exc, urllib.error.HTTPError):
        code = exc.code
        if code in (401, 403):
            return ToolError("blocked", f"HTTP {code}; host refuses automated access")
        if code == 404:
            return ToolError("not_found", f"HTTP {code}")
        if code == 429:
            return ToolError("rate_limited", f"HTTP {code}", _retry_after_ms(exc) or 30_000)
        if 500 <= code < 600:
            return ToolError("unavailable", f"HTTP {code}", _retry_after_ms(exc) or 5_000)
        return ToolError("network", f"HTTP {code}")
    name = type(exc).__name__
    if "Timeout" in name or "timed out" in str(exc).lower():
        return ToolError("timeout", name, 5_000)
    if isinstance(exc, (urllib.error.URLError, OSError)):
        return ToolError("network", f"{name}: {exc}", 5_000)
    return ToolError("parse", f"{name}: {exc}")
