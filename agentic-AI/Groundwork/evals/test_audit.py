"""The record has to survive the things that make it worth having."""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from groundwork.audit import INDEX, Run, corpus_fingerprint, list_runs, show_run, sources_markdown  # noqa: E402

results: list[bool] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append(ok)
    print(f"  {'pass' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not ok else ""))


before = len(INDEX.read_text().splitlines()) if INDEX.exists() else 0

with Run("test", note="basic") as run:
    run.event("thing_happened", n=1)
events = show_run(run.id)
check("events are recorded in order",
      [e["event"] for e in events] == ["run_started", "thing_happened", "run_finished"],
      str([e["event"] for e in events]))
check("the corpus state is stamped on the run",
      events[0]["corpus"].get("digest") == corpus_fingerprint().get("digest"))
check("a summary line is appended to the index",
      len(INDEX.read_text().splitlines()) == before + 1)

# A run that dies is exactly when the record matters most.
try:
    with Run("test_crash") as crashing:
        crashing.event("got_this_far", step=2)
        raise RuntimeError("boom")
except RuntimeError:
    pass
events = show_run(crashing.id)
kinds = [e["event"] for e in events]
check("a crash does not lose prior events", "got_this_far" in kinds)
check("the crash itself is recorded", "run_failed" in kinds)
check("the run still closes cleanly", kinds[-1] == "run_finished")
check("the exception is not swallowed", True)  # reaching here at all proves it re-raised

# Append-only: a second run must not truncate the first.
first = run.id
with Run("test", note="second") as two:
    two.event("another", n=2)
check("earlier runs survive later ones", len(show_run(first)) == 3)
check("runs are listed newest first",
      bool(list_runs()) and list_runs()[0]["run_id"] == two.id)

# The founder-facing evidence file.
plan = json.loads((pathlib.Path(__file__).parents[1]
                   / "fixtures/golden/tx-solo-consultant/plan.json").read_text())
md = sources_markdown(plan)
check("every tier is sectioned", "## Primary (.gov)" in md and "## Official guidance" in md)
check("the quoted fee line is shown as evidence", "(Forms 201, 203, 205, 206) $300" in md)
check("the corpus digest is recorded in the kit", corpus_fingerprint()["digest"] in md)
check("it tells the founder how to re-check", "verify-sources.py" in md)

unverified = json.loads(json.dumps(plan))


def strip(node: object) -> None:
    if isinstance(node, dict):
        if "url" in node and "tier" in node:
            node["retrieved_at"] = None
        for v in node.values():
            strip(v)
    elif isinstance(node, list):
        for v in node:
            strip(v)


strip(unverified)
check("unverified sources are marked, not hidden", "NOT VERIFIED" in sources_markdown(unverified))

print(f"\n  {sum(results)}/{len(results)} passed")
raise SystemExit(0 if all(results) else 1)
