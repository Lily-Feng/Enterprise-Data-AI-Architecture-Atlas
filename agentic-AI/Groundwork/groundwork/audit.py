"""An append-only record of what the system did, and what it was looking at.

Provenance and audit are different things, and Groundwork had only the first.
`Source.retrieved_at` says what a claim rests on. It does not say that the gate
blocked this kit four times, which objects were regenerated, or what the corpus
said on the day the kit quoted $300.

That last question is the one that actually gets asked, months later, when a fee
turns out to have moved. Answering it requires knowing the state of the corpus
at emit time, so every run records a fingerprint of it.

The file is append-only and never rewritten. A record that can be edited after
the fact to match the outcome is not evidence, and the whole product rests on
being able to show its work.

    with Run("refresh") as run:
        run.event("source_fetched", source_id="tx-sos-fees", chunks=97)

    python3 -m groundwork.audit list
    python3 -m groundwork.audit show <run_id>
    python3 -m groundwork.audit sources <plan.json>    # the founder-facing evidence file
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
import uuid
from datetime import datetime, timezone
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent.parent
RUNS = ROOT / "runs"
INDEX = RUNS / "index.jsonl"
CORPUS_LOCK = ROOT / "corpus" / "corpus.lock.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def corpus_fingerprint() -> dict[str, Any]:
    """What the corpus looked like, compactly enough to store on every run.

    This is what makes "what did the system see that day" answerable rather
    than a shrug.
    """
    if not CORPUS_LOCK.exists():
        return {"state": "absent"}
    lock = json.loads(CORPUS_LOCK.read_text())
    chunks = lock.get("chunks", {})
    joined = "".join(f"{k}:{v['hash']}" for k, v in sorted(chunks.items()))
    return {
        "state": "present",
        "refreshed_at": lock.get("refreshed_at"),
        "chunks": len(chunks),
        "digest": hashlib.sha256(joined.encode()).hexdigest()[:16],
    }


class Run:
    """One execution, recorded as it happens.

    Events are flushed on write rather than buffered to the end: a run that
    crashes should still leave behind everything it had done up to the crash,
    which is exactly when the record is most worth having.
    """

    def __init__(self, kind: str, **meta: Any) -> None:
        self.kind = kind
        self.started = now()
        stamp = self.started.replace(":", "").replace("-", "")
        # Timestamps are second-resolution and a process can open two runs of
        # the same kind inside one second. Without the random tail they collide
        # onto a single file and two distinct runs become indistinguishable,
        # which defeats the point of keeping a record at all.
        self.id = f"{stamp}-{kind}-{uuid.uuid4().hex[:8]}"
        self.meta = meta
        self.counts: dict[str, int] = {}
        self.path = RUNS / f"{self.id}.jsonl"
        self._fh = None
        self._corpus = corpus_fingerprint()

    def __enter__(self) -> Run:
        RUNS.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("a", encoding="utf-8")
        self.event("run_started", kind=self.kind, pid=os.getpid(),
                   corpus=self._corpus, **self.meta)
        return self

    def event(self, name: str, **payload: Any) -> None:
        """Append one event. `name` rather than `kind` so a payload may carry
        its own `kind` field without colliding with the parameter."""
        if self._fh is None:
            raise RuntimeError("Run must be used as a context manager")
        self.counts[name] = self.counts.get(name, 0) + 1
        self._fh.write(json.dumps({"ts": now(), "event": name, **payload},
                                  ensure_ascii=False, default=str) + "\n")
        self._fh.flush()

    def finding(self, finding: Any, phase: str = "gate") -> None:
        """Record one validator finding, with its object scope preserved."""
        self.event("finding", phase=phase, severity=finding.severity,
                   where=finding.where, message=finding.message)

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is not None:
            self.event("run_failed", error=f"{exc_type.__name__}: {exc}")
        self.event("run_finished", counts=dict(self.counts))
        if self._fh:
            self._fh.close()
        # A one-line summary per run, small enough to commit, so the history
        # survives when the full logs are cleaned out.
        RUNS.mkdir(parents=True, exist_ok=True)
        with INDEX.open("a", encoding="utf-8") as idx:
            idx.write(json.dumps({
                "run_id": self.id, "kind": self.kind, "started": self.started,
                "finished": now(), "corpus": self._corpus,
                "counts": dict(self.counts),
                "ok": exc_type is None and not self.counts.get("run_failed"),
            }, default=str) + "\n")
        return False  # never swallow the exception


# --------------------------------------------------------------------------- #
# Reading it back
# --------------------------------------------------------------------------- #


def list_runs(limit: int = 20) -> list[dict]:
    if not INDEX.exists():
        return []
    rows = [json.loads(line) for line in INDEX.read_text().splitlines() if line.strip()]
    return rows[-limit:][::-1]


def show_run(run_id: str) -> list[dict]:
    path = RUNS / f"{run_id}.jsonl"
    if not path.exists():
        matches = sorted(RUNS.glob(f"*{run_id}*.jsonl"))
        if not matches:
            raise FileNotFoundError(f"no run matching {run_id!r}")
        path = matches[-1]
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def sources_markdown(plan: dict) -> str:
    """The evidence file that ships inside a founder's kit.

    Every claim in the kit points at a page, a tier, and a date. This is the
    artifact that makes the kit auditable by the person holding it, rather than
    only by whoever generated it.
    """
    seen: dict[str, dict] = {}

    def walk(node: object) -> None:
        if isinstance(node, dict):
            if "url" in node and "tier" in node:
                seen.setdefault(node["url"], node)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(plan)
    tiers = {1: "Primary (.gov)", 2: "Official guidance", 3: "Secondary"}
    lines = [
        "# Sources",
        "",
        "Every fee, form number, and deadline in this kit comes from one of these",
        "pages. Nothing here was written from memory.",
        "",
        f"Kit generated {plan.get('generated_at', 'unknown')}. "
        f"Corpus state at generation: `{corpus_fingerprint().get('digest', 'n/a')}`.",
        "",
    ]
    for tier in (1, 2, 3):
        rows = [s for s in seen.values() if s["tier"] == tier]
        if not rows:
            continue
        lines += [f"## {tiers[tier]}", ""]
        for s in sorted(rows, key=lambda r: r["title"]):
            stamp = s.get("retrieved_at") or "NOT VERIFIED"
            lines.append(f"- [{s['title']}]({s['url']}) — retrieved {stamp}")
            if s.get("quote"):
                lines.append(f"  > {s['quote']}")
        lines.append("")
    lines += [
        "## Re-checking these",
        "",
        "Fee schedules and filing deadlines turn over annually. To confirm nothing",
        "has moved since this kit was generated:",
        "",
        "```bash",
        "python3 scripts/verify-sources.py",
        "```",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == "list":
        rows = list_runs()
        if not rows:
            print("  no runs recorded yet")
            return 0
        for r in rows:
            mark = "ok " if r["ok"] else "FAIL"
            counts = ", ".join(f"{k}={v}" for k, v in r["counts"].items()
                               if k not in ("run_started", "run_finished"))
            print(f"  {mark}  {r['started']}  {r['kind']:<10} {counts or '-'}")
            print(f"        {r['run_id']}  corpus {r['corpus'].get('digest', 'n/a')}")
        return 0
    if cmd == "show":
        if len(argv) < 3:
            print("usage: show <run_id>")
            return 2
        for e in show_run(argv[2]):
            payload = {k: v for k, v in e.items() if k not in ("ts", "event")}
            print(f"  {e['ts']}  {e['event']}")
            for k, v in payload.items():
                print(f"      {k}: {v}")
        return 0
    if cmd == "sources":
        if len(argv) < 3:
            print("usage: sources <plan.json> [-o SOURCES.md]")
            return 2
        plan = json.loads(pathlib.Path(argv[2]).read_text())
        md = sources_markdown(plan)
        if "-o" in argv:
            out = pathlib.Path(argv[argv.index("-o") + 1])
            out.write_text(md)
            print(f"  wrote {out}")
        else:
            print(md)
        return 0
    print(f"unknown command {cmd!r}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
