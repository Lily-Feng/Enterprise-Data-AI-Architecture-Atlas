"""Fetch every cited page, stamp it, and remember what it said.

This runs twice in a kit's life, and the second run is the interesting one.

    Phase 0 / generation   proves each citation resolves, and stamps
                           `retrieved_at` so the plan can clear strict mode.
    Months later, by the founder
                           re-fetches the same pages and reports which ones
                           changed. State fee schedules and filing deadlines
                           turn over annually, so a kit that cannot re-check
                           itself is confidently wrong on a schedule.

The lock file is what makes drift detectable: a content fingerprint per URL,
compared on every later run.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request
from datetime import date

from .errors import ToolError, classify

UA = "Groundwork/0.1 (+https://github.com/Lily-Feng/Enterprise-Data-AI-Architecture-Atlas)"
TIMEOUT = 20

# Boilerplate that changes on every page load and would otherwise report as
# drift on every run.
NOISE = (
    re.compile(rb"<script\b[^>]*>.*?</script>", re.S | re.I),
    re.compile(rb"<style\b[^>]*>.*?</style>", re.S | re.I),
    re.compile(rb"csrf[-_]?token[^\"']*[\"'][^\"']+[\"']", re.I),
    re.compile(rb"\b\d{4}-\d{2}-\d{2}T[\d:.+-]+\b"),
    re.compile(rb"\s+"),
)


def fingerprint(body: bytes) -> str:
    for pattern in NOISE:
        body = pattern.sub(b" ", body)
    return hashlib.sha256(body.strip().lower()).hexdigest()[:16]


def fetch(url: str) -> tuple[str | None, str | None, ToolError | None]:
    """Returns (fingerprint, readable text, error)."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read()
            return fingerprint(body), readable(body), None
    except Exception as e:  # noqa: BLE001
        return None, None, classify(e)


TAG = re.compile(rb"<[^>]+>")
DROP_EL = (re.compile(rb"<script\b[^>]*>.*?</script>", re.S | re.I),
           re.compile(rb"<style\b[^>]*>.*?</style>", re.S | re.I))


def readable(body: bytes) -> str:
    for pattern in DROP_EL:
        body = pattern.sub(b" ", body)
    import html as _html
    text = TAG.sub(b" ", body).decode("utf-8", "replace")
    return re.sub(r"\s+", " ", _html.unescape(text)).strip().lower()


def quotes_for(plan: dict) -> dict[str, list[str]]:
    """Every quoted claim, by URL. These are what a refresh has to re-confirm."""
    out: dict[str, list[str]] = {}

    def walk(node: object) -> None:
        if isinstance(node, dict):
            if node.get("url") and node.get("quote"):
                out.setdefault(node["url"], []).append(node["quote"])
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(plan)
    return out


def collect_urls(plan: dict) -> list[str]:
    found: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            if "url" in node and "tier" in node:
                found.append(node["url"])
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(plan)
    return sorted(set(found))


def unstamp(plan: dict, urls: set[str]) -> int:
    """Withdraw verification from sources whose evidence no longer holds.

    Detecting a change and carrying on is how a kit keeps quoting a fee that
    moved. Clearing retrieved_at puts the claim back in front of the gate,
    which will refuse to ship it until the evidence is re-established.
    """
    count = 0

    def walk(node: object) -> None:
        nonlocal count
        if isinstance(node, dict):
            if node.get("url") in urls and "tier" in node:
                node["retrieved_at"] = None
                count += 1
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(plan)
    return count


def stamp(plan: dict, verified: dict[str, str]) -> int:
    """Write today's date onto every source that resolved."""
    count = 0

    def walk(node: object) -> None:
        nonlocal count
        if isinstance(node, dict):
            if "url" in node and "tier" in node and node["url"] in verified:
                node["retrieved_at"] = date.today().isoformat()
                count += 1
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(plan)
    return count


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python -m groundwork.verify_sources <plan.json> [--write]")
        return 2
    path = pathlib.Path(argv[1])
    write = "--write" in argv
    plan = json.loads(path.read_text())
    lock_path = path.with_suffix(".lock.json")
    lock: dict[str, dict] = json.loads(lock_path.read_text()) if lock_path.exists() else {}

    urls = collect_urls(plan)
    verified: dict[str, str] = {}
    changed: list[str] = []
    failed: list[str] = []

    quoted = quotes_for(plan)
    broken: list[str] = []

    print(f"verifying {len(urls)} cited sources\n")
    for url in urls:
        fp, text, err = fetch(url)
        if fp is not None:
            # A fingerprint proves the page was reachable. Only the quote proves
            # the claim still has something holding it up.
            gone = [q for q in quoted.get(url, [])
                    if re.sub(r"\s+", " ", q).strip().lower() not in (text or "")]
            if gone:
                broken.append(url)
                print(f"  EVIDENCE GONE  {url}")
                for q in gone:
                    print(f"                 {q[:110]}")
                continue
            previous = lock.get(url, {}).get("fingerprint")
            if previous and previous != fp:
                changed.append(url)
                mark = "CHANGED"
            else:
                mark = "ok     "
            verified[url] = fp
            lock[url] = {"fingerprint": fp, "checked": date.today().isoformat(), "status": 200}
            print(f"  {mark}  {url}")
        else:
            failed.append(url)
            print(f"  FAILED   {url}")
            print(f"           {err}")

    print()
    if changed:
        print(f"  {len(changed)} source(s) changed since the last check. Re-read these before")
        print("  relying on any fee, form number, or deadline that rests on them:")
        for url in changed:
            print(f"    - {url}")
        print()

    if broken:
        print(f"  {len(broken)} source(s) no longer carry the text their claims quote.")
        print("  Verification is being withdrawn from them, so the gate will refuse")
        print("  to ship those claims until the evidence is re-established.\n")

    if write and broken:
        n = unstamp(plan, set(broken))
        print(f"  withdrew verification from {n} source reference(s)")

    if write and verified:
        n = stamp(plan, verified)
        path.write_text(json.dumps(plan, indent=2))
        lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True))
        print(f"  stamped {n} source reference(s) in {path.name}")
        print(f"  wrote {lock_path.name}")
    elif verified:
        print("  dry run. Pass --write to stamp retrieved_at and update the lock file.")

    print(f"\n  {len(verified)} verified, {len(failed)} failed, {len(changed)} changed, "
          f"{len(broken)} evidence gone")
    return 1 if (failed or broken) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
