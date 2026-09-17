"""The gate a kit must pass before a founder ever sees it.

Layers 1, 2 and 4 of the safety model -- input screening, the system prompt, and
output screening -- are soft: a model can talk its way past all three. This
module is layer 3, and it is hard. It runs after generation, on the parsed
object, and nothing reaches a founder without clearing it.

Two modes:

    draft   what the agent runs mid-loop. Unverified sources are allowed,
            because the agent may legitimately be mid-fetch.
    strict  what shipping requires. Every cited page must actually have been
            retrieved, nothing may be stale, and no advisory language survives.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from typing import Iterable, Literal

from .audit import Run
from .schemas import Cited, Deadline, Plan, Source, Tier

Mode = Literal["draft", "strict"]
Severity = Literal["error", "warning"]

# Groundwork routes, cites, and computes. It does not advise. These are the
# constructions that turn a brief into an opinion, and they are rejected in the
# generated text rather than discouraged in a prompt.
ADVISORY_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\byou should\b", "directive"),
    (r"\bwe recommend\b", "recommendation"),
    (r"\bI recommend\b", "recommendation"),
    (r"\bwe suggest\b", "recommendation"),
    (r"\bthe best (option|choice|structure)\b", "superlative"),
    (r"\byour best bet\b", "superlative"),
    (r"\byou ought to\b", "directive"),
    (r"\bgo with\b", "directive"),
    (r"\bis better than\b", "comparative judgment"),
    (r"\b(is|are) the right (choice|option|entity)\b", "superlative"),
)

# Phrases that promise something Groundwork must never do.
FORBIDDEN_CLAIMS: tuple[tuple[str, str], ...] = (
    (r"\bwe (will |can )?file\b", "Groundwork never files on a founder's behalf"),
    (r"\bwe('ll| will) submit\b", "Groundwork never files on a founder's behalf"),
    (r"\bguarantee(d|s)?\b", "no outcome here is guaranteed"),
)


@dataclass(frozen=True)
class Finding:
    severity: Severity
    where: str
    message: str

    def __str__(self) -> str:
        mark = "ERROR" if self.severity == "error" else "warn "
        return f"  {mark}  {self.where}: {self.message}"


def _text_fields(plan: Plan) -> Iterable[tuple[str, str]]:
    """Every piece of free text that reaches a founder's eyes."""
    for d in plan.decisions:
        yield f"{d.id}.context", d.context
        yield f"{d.id}.what_actually_differs", d.what_actually_differs
        yield f"{d.id}.consequences", d.consequences
        if d.common_misconception:
            yield f"{d.id}.common_misconception", d.common_misconception
        for i, o in enumerate(d.options):
            yield f"{d.id}.options[{i}].what_it_actually_is", o.what_it_actually_is
            yield f"{d.id}.options[{i}].consequence", o.consequence
    for t in plan.tasks:
        yield f"{t.id}.why", t.why
        for i, m in enumerate(t.common_mistakes):
            yield f"{t.id}.common_mistakes[{i}]", m
    for e in plan.elections:
        yield f"{e.id}.what_it_does", e.what_it_does
        yield f"{e.id}.lost_if_missed", e.lost_if_missed


def check_language(plan: Plan) -> list[Finding]:
    out: list[Finding] = []
    for where, text in _text_fields(plan):
        low = text.lower()
        for pattern, kind in ADVISORY_PATTERNS:
            if re.search(pattern, low):
                match = re.search(pattern, low)
                out.append(
                    Finding("error", where, f"advisory language ({kind}): {match.group(0)!r}")
                )
        for pattern, why in FORBIDDEN_CLAIMS:
            if re.search(pattern, low):
                out.append(Finding("error", where, why))
    return out


CHUNKS = __import__("pathlib").Path(__file__).resolve().parent.parent / "corpus" / "chunks.jsonl"
_WS = re.compile(r"\s+")


def _retrieved_text() -> dict[str, str]:
    """What the fetcher actually pulled down, keyed by URL.

    This is the trust boundary. A model can write any `retrieved_at` and any
    `quote` it likes into a plan; it cannot put text into the corpus, because
    the corpus is written by the fetcher from bytes the server returned. So
    evidence is confronted with this, never with the plan's own say-so.
    """
    if not CHUNKS.exists():
        return {}
    joined: dict[str, list[str]] = {}
    for line in CHUNKS.read_text().splitlines():
        if not line.strip():
            continue
        c = json.loads(line)
        joined.setdefault(c["url"], []).append(c["text"])
    return {u: _WS.sub(" ", " ".join(parts)).lower() for u, parts in joined.items()}


def check_evidence(plan: Plan, mode: Mode) -> list[Finding]:
    """Every fee, form number and deadline must be carried by its own evidence.

    A citation proves a page was consulted. It does not prove the page says
    what the claim says. Three things are required here, and the claim is
    blocked if any fails:

      1. a tier-1 source carrying a quote,
      2. the quote actually contains the claim (see `Cited.supports`),
      3. the quote actually appears in what the fetcher retrieved.

    (3) is what makes (1) and (2) worth anything. Without it a model could
    supply a quote that says whatever the claim needs it to say.

    Deadlines are the weak case: a rule expressed in prose cannot be matched
    against a page mechanically, so (2) only confirms the quote is deadline-
    shaped. That limit is real and is reported as such rather than papered over.
    """
    out: list[Finding] = []
    corpus = _retrieved_text()
    for path, claim in plan.iter_claims():
        ev = claim.evidence
        if ev is None:
            out.append(Finding("error", path,
                               f"{type(claim).__name__} states a fact with no quoted "
                               "tier-1 evidence; a bare citation is not proof"))
            continue
        if not claim.supports(ev.quote or ""):
            out.append(Finding("error", path,
                               f"quoted evidence does not contain the claim "
                               f"({claim.claim()!r} not found in the quote)"))
        if not corpus:
            sev: Severity = "error" if mode == "strict" else "warning"
            out.append(Finding(sev, path,
                               "no retrieved corpus to check this evidence against; "
                               "run: python3 -m groundwork.corpus refresh"))
            continue
        page = corpus.get(str(ev.url))
        if page is None:
            sev = "error" if mode == "strict" else "warning"
            out.append(Finding(sev, path,
                               f"{ev.url} is cited but not in the corpus; add it to "
                               "corpus/manifest.json so its evidence can be checked"))
        elif _WS.sub(" ", ev.quote).strip().lower() not in page:
            out.append(Finding("error", path,
                               "the quoted evidence does not appear on the retrieved "
                               f"page ({ev.url})"))
    return out


def check_sources(plan: Plan, mode: Mode) -> list[Finding]:
    """Every source reference, not every distinct URL.

    Deduplicating by URL hid unverified references: the same page cited once
    with a retrieval date and once without collapsed to a single 'verified'
    entry.
    """
    out: list[Finding] = []
    today = date.today()
    for path, s in plan.iter_sources():
        where = f"{path} ({s.url})"
        if not s.verified:
            if mode == "strict":
                out.append(Finding("error", where, "cited but never retrieved"))
            else:
                out.append(Finding("warning", where, "not yet retrieved"))
            continue
        if s.stale:
            age = (today - s.retrieved_at).days
            sev: Severity = "error" if mode == "strict" and s.tier is Tier.PRIMARY else "warning"
            out.append(Finding(sev, where, f"retrieved {age} days ago; re-verify before shipping"))
    return out


def check_graph(plan: Plan) -> tuple[list[Finding], list[str]]:
    """Resolve dependencies and topologically sort.

    Order is the product's core value: founders get it wrong constantly, and an
    EIN application filed before the entity exists simply fails. A plan whose
    graph does not sort is not a plan.
    """
    out: list[Finding] = []
    ids = {t.id for t in plan.tasks}
    if len(ids) != len(plan.tasks):
        out.append(Finding("error", "plan.tasks", "duplicate task ids"))

    edges: dict[str, list[str]] = {}
    for t in plan.tasks:
        deps = []
        for d in t.depends_on:
            if d not in ids:
                out.append(Finding("error", t.id, f"depends on unknown task {d!r}"))
            elif d == t.id:
                out.append(Finding("error", t.id, "depends on itself"))
            else:
                deps.append(d)
        edges[t.id] = deps

    # Kahn's algorithm; whatever fails to drain is a cycle.
    indegree = {tid: 0 for tid in edges}
    for tid, deps in edges.items():
        for _ in deps:
            indegree[tid] += 1
    ready = sorted(t for t, n in indegree.items() if n == 0)
    order: list[str] = []
    while ready:
        node = ready.pop(0)
        order.append(node)
        for tid, deps in edges.items():
            if node in deps:
                indegree[tid] -= 1
                if indegree[tid] == 0:
                    ready.append(tid)
                    ready.sort()
    if len(order) != len(edges):
        stuck = sorted(set(edges) - set(order))
        out.append(Finding("error", "plan.tasks", f"dependency cycle among {stuck}"))
    return out, order


def check_jurisdiction(plan: Plan) -> list[Finding]:
    """A California rule answering a Texas question is the permission leak of
    this domain, and it is expensive rather than merely embarrassing."""
    out: list[Finding] = []
    allowed = {"US", plan.profile.home_state}
    for t in plan.tasks:
        if t.jurisdiction.code not in allowed:
            out.append(
                Finding(
                    "error",
                    t.id,
                    f"jurisdiction {t.jurisdiction.code} is outside this founder's "
                    f"scope {sorted(allowed)}",
                )
            )
    return out


def check_scope(plan: Plan) -> list[Finding]:
    """Fail closed. Out-of-scope founders get a referral, not a kit."""
    reason = plan.profile.out_of_scope_reason
    if reason:
        return [
            Finding(
                "error",
                "profile",
                f"out of scope for v0.1 ({reason}); escalate to a professional "
                "instead of generating a kit",
            )
        ]
    return []


def check_completeness(plan: Plan) -> list[Finding]:
    """Every kit owes the founder the same floor, regardless of profile."""
    out: list[Finding] = []
    titles = " ".join(t.title.lower() for t in plan.tasks)
    for needle, label in (("ein", "an EIN task"), ("bank", "a business bank account task")):
        if needle not in titles:
            out.append(Finding("error", "plan.tasks", f"kit is missing {label}"))
    if not plan.elections:
        out.append(
            Finding("error", "plan.elections", "no elections listed; the tax inventory is the point")
        )
    for e in plan.elections:
        if e.deadline is None:
            out.append(Finding("warning", e.id, "no deadline; confirm the window really is open-ended"))
    return out


def validate(plan: Plan, mode: Mode = "strict") -> tuple[list[Finding], list[str]]:
    graph_findings, order = check_graph(plan)
    findings = [
        *check_scope(plan),
        *graph_findings,
        *check_jurisdiction(plan),
        *check_sources(plan, mode),
        *check_evidence(plan, mode),
        *check_language(plan),
        *check_completeness(plan),
    ]
    return findings, order


def report(findings: list[Finding], order: list[str], mode: Mode) -> bool:
    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]
    for f in findings:
        print(f)
    print()
    if order:
        print(f"  order: {' -> '.join(order)}")
    ok = not errors
    verdict = "PASS" if ok else "BLOCKED"
    print(f"  [{mode}] {verdict} - {len(errors)} error(s), {len(warnings)} warning(s)")
    return ok


def main(argv: list[str]) -> int:
    import json

    if len(argv) < 2:
        print("usage: python -m groundwork.validate <plan.json> [draft|strict]")
        return 2
    mode: Mode = argv[2] if len(argv) > 2 else "strict"  # type: ignore[assignment]
    plan = Plan.model_validate(json.loads(open(argv[1]).read()))
    with Run("gate", plan=argv[1], mode=mode) as run:
        findings, order = validate(plan, mode)
        for f in findings:
            run.finding(f)
        ok = report(findings, order, mode)
        run.event("gate_result", passed=ok, mode=mode, order=order,
                  errors=sum(f.severity == "error" for f in findings),
                  warnings=sum(f.severity == "warning" for f in findings))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
