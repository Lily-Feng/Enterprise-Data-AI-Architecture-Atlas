"""Turning a blocked kit back into a prompt.

The gate says no. Something has to act on that, and the naive move is to
regenerate the whole plan and hope. That is wasteful and it is unsafe: the
tasks that passed already cost real fetches against government hosts, and
re-rolling them re-runs those side effects and re-rolls text that was fine.

So repair is scoped the way a partial sub-agent failure should be -- only the
objects that actually failed are sent back, each with its own findings
attached, and everything else is carried forward verbatim.

Findings already name their object (`T001.why`, `D001.consequences`), so the
scoping falls straight out of the gate's own output.

`run_loop` is the loop: validate, hand each failed object back to a generator,
merge the replacement, repeat. It is bounded twice -- a round budget for the
whole loop, and a per-object attempt cap, because an object failing the same way
three times is not going to be argued into passing. When either bound is reached
it escalates with a structured summary rather than returning a kit that did not
pass.

The generator is injected rather than called directly, so the control flow is
testable without an API and Phase 3 can supply a real one without changing it.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable

from .audit import Run
from .schemas import Plan
from .validate import Finding, Mode, validate

MAX_ROUNDS = 3

KIND = {"T": "task", "D": "decision brief", "E": "election"}


@dataclass(frozen=True)
class RepairTask:
    """One object to regenerate, and why."""

    object_id: str
    kind: str
    findings: tuple[Finding, ...]
    current: dict

    def as_prompt(self) -> str:
        problems = "\n".join(f"  - {f.where}: {f.message}" for f in self.findings)
        return (
            f"The {self.kind} {self.object_id} did not pass validation.\n\n"
            f"Problems:\n{problems}\n\n"
            f"Current value:\n{json.dumps(self.current, indent=2)}\n\n"
            "Return a corrected version of this object only. Do not change any "
            "other object. Every fee, form number, and deadline needs a tier-1 "
            "source that has actually been retrieved. State what the sources say; "
            "do not recommend a course of action."
        )


def owner(where: str) -> str:
    """The object a finding belongs to. 'T001.common_mistakes[0]' -> 'T001'."""
    return where.split(".", 1)[0].split("[", 1)[0]


def plan_objects(plan: Plan) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for t in plan.tasks:
        out[t.id] = t.model_dump(mode="json")
    for d in plan.decisions:
        out[d.id] = d.model_dump(mode="json")
    for e in plan.elections:
        out[e.id] = e.model_dump(mode="json")
    return out


def plan_repairs(plan: Plan, findings: list[Finding]) -> tuple[list[RepairTask], list[Finding]]:
    """Split findings into per-object repairs and whole-plan problems.

    Anything that is not scoped to a single object -- a dependency cycle, a
    missing tax inventory, an out-of-scope founder -- cannot be fixed by
    regenerating one thing, so it is returned separately for the caller to
    handle at the plan level or escalate.
    """
    objects = plan_objects(plan)
    grouped: dict[str, list[Finding]] = defaultdict(list)
    structural: list[Finding] = []

    for f in findings:
        if f.severity != "error":
            continue
        key = owner(f.where)
        if key in objects:
            grouped[key].append(f)
        else:
            structural.append(f)

    repairs = [
        RepairTask(
            object_id=key,
            kind=KIND.get(key[0], "object"),
            findings=tuple(items),
            current=objects[key],
        )
        for key, items in sorted(grouped.items())
    ]
    return repairs, structural


@dataclass
class Escalation:
    """What a human receives when the loop gives up."""

    rounds: int
    unresolved: tuple[Finding, ...]
    summary: str

    def __str__(self) -> str:
        lines = [
            f"ESCALATION after {self.rounds} repair round(s)",
            f"  {self.summary}",
            "",
            "  Unresolved:",
            *[f"    - {f.where}: {f.message}" for f in self.unresolved],
            "",
            "  No kit was produced. Nothing was filed and nothing was sent.",
        ]
        return "\n".join(lines)


def repair_round(plan: Plan, mode: Mode = "strict",
                 run: Run | None = None, round_no: int = 1
                 ) -> tuple[list[RepairTask], list[Finding], bool]:
    """One pass: validate, and say what would need regenerating.

    `run` is optional so the function stays usable in tests and one-off calls,
    but a real loop should always pass one. Which objects were resent, and how
    many times, is the part worth being able to answer later.
    """
    findings, _ = validate(plan, mode)
    errors = [f for f in findings if f.severity == "error"]
    if not errors:
        if run:
            run.event("repair_round", round=round_no, passed=True, resent=[])
        return [], [], True
    repairs, structural = plan_repairs(plan, findings)
    if run:
        for f in errors:
            run.finding(f, phase=f"repair_round_{round_no}")
        run.event("repair_round", round=round_no, passed=False,
                  resent=[r.object_id for r in repairs],
                  structural=[f.where for f in structural])
    return repairs, structural, False


def escalate(rounds: int, findings: list[Finding], run: Run | None = None) -> Escalation:
    scoped = {owner(f.where) for f in findings if f.severity == "error"}
    if run:
        run.event("escalation", rounds=rounds, objects=sorted(scoped),
                  unresolved=[f"{f.where}: {f.message}" for f in findings
                              if f.severity == "error"])
    return Escalation(
        rounds=rounds,
        unresolved=tuple(f for f in findings if f.severity == "error"),
        summary=(
            f"{len(scoped)} object(s) still failing after the retry budget. "
            "These need a person, not another round."
        ),
    )



# --------------------------------------------------------------------------- #
# The loop itself
# --------------------------------------------------------------------------- #


Applier = Callable[[RepairTask], object | None]


@dataclass
class Outcome:
    """What the loop did, whether or not it worked."""

    plan: Plan
    rounds: int
    passed: bool
    escalation: Escalation | None = None
    attempts: dict[str, int] = field(default_factory=dict)

    def __str__(self) -> str:
        verdict = "passed" if self.passed else "escalated"
        return (f"repair {verdict} after {self.rounds} round(s); "
                f"attempts {self.attempts or '{}'}")


def merge(plan: Plan, repaired: object) -> Plan:
    """Put a regenerated object back, leaving everything else untouched.

    Everything else genuinely untouched matters: the objects that passed were
    built from fetches against government hosts, and re-rolling them would
    re-run those side effects for no reason.
    """
    oid = getattr(repaired, "id", None)
    if oid is None:
        raise ValueError("a repaired object must carry its id")
    swap = lambda items: [repaired if i.id == oid else i for i in items]  # noqa: E731
    return plan.model_copy(update={
        "tasks": swap(plan.tasks),
        "decisions": swap(plan.decisions),
        "elections": swap(plan.elections),
    })


def run_loop(plan: Plan, apply: Applier, mode: Mode = "strict",
             max_rounds: int = MAX_ROUNDS, run: Run | None = None) -> Outcome:
    """Validate, repair what failed, and stop.

    `apply` is injected rather than called on a model directly, so the loop is
    testable without an API and so Phase 3 can drop a real generator in without
    touching the control flow.

    Two bounds, not one. `max_rounds` caps the whole loop; `attempts` caps how
    many times a single object may be resent, because an object that fails the
    same way three times is not going to be argued into passing and should stop
    consuming the budget.
    """
    attempts: dict[str, int] = {}
    current = plan

    for round_no in range(1, max_rounds + 1):
        repairs, structural, ok = repair_round(current, mode, run=run, round_no=round_no)
        if ok:
            return Outcome(current, round_no, True, attempts=attempts)
        if structural:
            findings, _ = validate(current, mode)
            esc = escalate(round_no, findings, run=run)
            return Outcome(current, round_no, False, esc, attempts)

        progressed = False
        for task in repairs:
            if attempts.get(task.object_id, 0) >= max_rounds:
                continue
            attempts[task.object_id] = attempts.get(task.object_id, 0) + 1
            replacement = apply(task)
            if replacement is None:
                continue
            current = merge(current, replacement)
            progressed = True

        if not progressed:
            findings, _ = validate(current, mode)
            esc = escalate(round_no, findings, run=run)
            if run:
                run.event("repair_exhausted", round=round_no, attempts=dict(attempts))
            return Outcome(current, round_no, False, esc, attempts)

    findings, _ = validate(current, mode)
    return Outcome(current, max_rounds, False,
                   escalate(max_rounds, findings, run=run), attempts)
