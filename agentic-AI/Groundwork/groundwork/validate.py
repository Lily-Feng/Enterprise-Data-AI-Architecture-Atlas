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
from pydantic import BaseModel

from .calendar import resolve, unmet
from .schemas import Cited, Deadline, Plan, Source, Tier

Mode = Literal["draft", "strict"]
Severity = Literal["error", "warning"]

# Groundwork routes, cites, and computes. It does not advise.
#
# This list is a limited additional check, not the boundary. It catches known
# constructions in generated prose and will miss paraphrases -- "Elect S-corp
# status immediately to minimise your tax bill" contains none of these phrases.
# The load-bearing controls are structural: no recommendation field exists to
# hold advice, and check_presupposed_decisions stops a plan from recommending
# by arrangement. Treat a clean language pass as weak evidence.
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


# Field names whose contents are not our prose. `quote` is verbatim text from a
# government page: screening it would flag the source, not the kit.
NOT_OUR_WORDS = {"quote", "url", "official_url", "id", "decision_id"}


def _text_fields(plan: Plan) -> Iterable[tuple[str, str]]:
    """Every piece of free text that reaches a founder's eyes.

    Walked generically rather than hand-listed. The hand-listed version read
    four fields per object and missed `title`, `have_ready`, `eligibility`,
    `professional_question`, `admin_cost_note` and every option name -- so
    a task titled "You should form an LLC now." passed.
    """

    def walk(node: object, path: str) -> Iterable[tuple[str, str]]:
        if isinstance(node, Source):
            return
        if isinstance(node, BaseModel):
            for name in type(node).model_fields:
                if name in NOT_OUR_WORDS:
                    continue
                yield from walk(getattr(node, name), f"{path}.{name}")
        elif isinstance(node, str):
            yield path, node
        elif isinstance(node, (list, tuple)):
            for i, item in enumerate(node):
                yield from walk(item, f"{path}[{i}]")

    for item in (*plan.tasks, *plan.decisions, *plan.elections):
        yield from walk(item, getattr(item, "id", "?"))


def check_presupposed_decisions(plan: Plan) -> list[Finding]:
    """A task may not presuppose a decision the founder has not made.

    This is the structural half of "never advises". The language screen catches
    a kit that says "you should form an LLC"; this catches a kit that simply
    opens with the LLC filing and lets the ordering do the recommending.
    """
    out: list[Finding] = []
    briefs = {d.id for d in plan.decisions}
    for t in plan.tasks:
        if t.requires_decision is None:
            continue
        if t.requires_decision not in briefs:
            out.append(Finding("error", t.id,
                               f"presupposes decision {t.requires_decision}, which this "
                               "kit does not brief"))
        elif not plan.profile.has_decided(t.requires_decision):
            out.append(Finding("error", t.id,
                               f"presupposes decision {t.requires_decision}, which the "
                               "founder has not recorded making; brief it or mark the "
                               "task conditional"))
    return out


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


def check_calendar(plan: Plan) -> list[Finding]:
    """A deadline the kit can compute, it must compute.

    The alternative is a calendar full of nulls, which is what the kit shipped
    before this existed. Where a fact is genuinely missing the deadline stays
    unresolved and says which fact it is waiting on -- that is information, and
    a null is not.
    """
    out: list[Finding] = []
    by_id = {t.id: t for t in plan.tasks}
    for path, claim in plan.iter_claims():
        if not isinstance(claim, Deadline):
            continue
        missing = unmet(claim, plan.profile)
        if missing:
            owner_id = path.split(".", 1)[0]
            task = by_id.get(owner_id)
            if task is not None and task.status == "ready":
                out.append(Finding("error", path,
                                   f"waiting on {list(missing)} but its task is "
                                   "status='ready'; use 'needs_info'"))
            elif task is None and not plan.profile.unknowns:
                out.append(Finding("warning", path,
                                   f"waiting on {list(missing)}, which the profile does "
                                   "not record as unknown"))
            continue
        computed = resolve(claim, plan.profile)
        if computed is not None and claim.resolved is None:
            out.append(Finding("error", path,
                               f"is computable ({computed.isoformat()}) but ships "
                               "unresolved; the kit promises a calendar"))
        elif computed is not None and claim.resolved != computed:
            out.append(Finding("error", path,
                               f"resolved to {claim.resolved} but the rule computes "
                               f"{computed.isoformat()}"))
        elif claim.resolved is not None and claim.hard and claim.resolved < date.today():
            out.append(Finding("warning", path,
                               f"resolved to {claim.resolved.isoformat()}, which has "
                               "already passed; the kit must say so rather than list it "
                               "as upcoming"))
        elif claim.resolver is None and claim.hard:
            out.append(Finding("warning", path,
                               "is a hard deadline with no resolver, so it cannot reach "
                               "the calendar"))
    return out


def check_readiness(plan: Plan) -> list[Finding]:
    """A task that asked for review may not call itself ready without one."""
    out: list[Finding] = []
    for t in plan.tasks:
        if t.needs_professional and t.review is None and t.status == "ready":
            out.append(Finding("error", t.id,
                               "needs professional review with none recorded but is "
                               "status='ready'"))
        if t.review is not None and not t.needs_professional:
            out.append(Finding("warning", t.id,
                               "records a review it never asked for"))
    return out


# The floor every kit owes a founder, as roles rather than as words. The old
# version searched the concatenated titles for "ein" and "bank", so a single
# task called "EIN and bank" satisfied both and a kit of one task passed.
REQUIRED_ROLES: dict[str, str] = {
    "entity_formation": "a formation filing",
    "ein": "an EIN application",
    "bank_account": "a business bank account",
    "state_tax_registration": "a state tax registration",
}

# Order a founder cannot get right by guessing, and that fails at the counter
# when they get it wrong.
REQUIRED_ORDER: tuple[tuple[str, str], ...] = (
    ("ein", "entity_formation"),
    ("bank_account", "ein"),
    ("bank_account", "entity_formation"),
    ("state_tax_registration", "entity_formation"),
)


def check_completeness(plan: Plan) -> list[Finding]:
    """Every kit owes the founder the same floor, regardless of profile."""
    out: list[Finding] = []
    by_role: dict[str, list[str]] = {}
    for t in plan.tasks:
        by_role.setdefault(t.role, []).append(t.id)

    for role, label in REQUIRED_ROLES.items():
        if role not in by_role:
            out.append(Finding("error", "plan.tasks", f"kit is missing {label} (role={role})"))
        elif len(by_role[role]) > 1:
            out.append(Finding("warning", "plan.tasks",
                               f"{len(by_role[role])} tasks claim role={role}: {by_role[role]}"))

    # Ordering is the part of the kit a founder cannot supply themselves.
    ids = {t.id: t for t in plan.tasks}
    for later, earlier in REQUIRED_ORDER:
        for lid in by_role.get(later, []):
            reached, frontier = set(), list(ids[lid].depends_on)
            while frontier:
                nxt = frontier.pop()
                if nxt in reached or nxt not in ids:
                    continue
                reached.add(nxt)
                frontier.extend(ids[nxt].depends_on)
            if not any(ids[r].role == earlier for r in reached):
                out.append(Finding("error", lid,
                                   f"role={later} must depend on role={earlier}, directly "
                                   "or through the chain"))

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
        *check_presupposed_decisions(plan),
        *check_calendar(plan),
        *check_readiness(plan),
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
