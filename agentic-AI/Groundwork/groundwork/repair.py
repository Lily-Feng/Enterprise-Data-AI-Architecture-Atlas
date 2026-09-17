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

The loop terminates. After `MAX_ROUNDS` it escalates to a human with a
structured summary rather than trying forever, because a kit that cannot be
made to pass is a kit nobody should receive.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass

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
