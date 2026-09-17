"""Repair has to be scoped, and it has to stop."""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from groundwork.repair import MAX_ROUNDS, escalate, repair_round  # noqa: E402
from groundwork.schemas import DecisionBrief, Election, Jurisdiction, Plan, Task  # noqa: E402
from groundwork.validate import validate  # noqa: E402

GOLDEN = pathlib.Path(__file__).parents[1] / "fixtures/golden/tx-solo-consultant/plan.json"
results: list[bool] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append(ok)
    print(f"  {'pass' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not ok else ""))


def load() -> Plan:
    return Plan.model_validate(json.loads(GOLDEN.read_text()))


plan = load()
repairs, structural, ok = repair_round(plan)
check("clean kit needs no repair", ok and not repairs)

# One bad brief must send back one object, not the whole plan.
broken = load()
broken.decisions[0] = broken.decisions[0].model_copy(
    update={"consequences": "You should elect S-corp status; it is the best option here."}
)
repairs, structural, ok = repair_round(broken)
check("advisory language triggers repair", not ok)
check("exactly one object is sent back", len(repairs) == 1, f"{len(repairs)} objects")
check("the right object is sent back", bool(repairs) and repairs[0].object_id == "D001")
check("untouched tasks are not resent",
      all(r.object_id != "T001" for r in repairs))
check("the repair prompt carries the finding",
      bool(repairs) and "advisory language" in repairs[0].as_prompt())
check("the repair prompt forbids widening scope",
      bool(repairs) and "Do not change any other object" in repairs[0].as_prompt())

# Two broken objects, two repairs -- still not the whole plan.
two = load()
two.decisions[0] = two.decisions[0].model_copy(
    update={"consequences": "We recommend the simpler structure for a founder in this position."}
)
two.tasks[0] = two.tasks[0].model_copy(
    update={"why": "We will file this for you and guarantee acceptance within five days."}
)
repairs, structural, ok = repair_round(two)
check("two broken objects produce two repairs", len(repairs) == 2, f"{len(repairs)}")
check("repairs are a subset of the plan", len(repairs) < len(two.tasks) + len(two.decisions))

# Structural failures cannot be fixed by regenerating one object.
cyclic = load()
cyclic.tasks[0] = cyclic.tasks[0].model_copy(update={"depends_on": ["T003"]})
repairs, structural, ok = repair_round(cyclic)
check("a dependency cycle is reported as structural",
      any("cycle" in f.message for f in structural))

# The loop must terminate rather than retry forever.
stuck = load()
stuck.profile = stuck.profile.model_copy(update={"regulated_industry": "cannabis"})
findings, _ = validate(stuck, "strict")
esc = escalate(MAX_ROUNDS, findings)
check("gives up and escalates", esc.rounds == MAX_ROUNDS and bool(esc.unresolved))
check("escalation states nothing was sent", "Nothing was filed" in str(esc))

# The loop, as opposed to the planner. Previously MAX_ROUNDS existed and
# nothing counted against it; the termination test called escalate() directly.
from groundwork.repair import Outcome, merge, run_loop  # noqa: E402

CLEAN = "Filing with the state is what brings the entity into existence."


KINDS = {"T": Task, "D": DecisionBrief, "E": Election}


def fixer(task):
    """Stands in for the generator: hands back the known-good object."""
    for item in (*load().tasks, *load().decisions, *load().elections):
        if item.id == task.object_id:
            return item
    return None


def stubborn(task):
    """Hands back what it was given, which is what a model that cannot fix
    something actually does. The loop has to notice and stop anyway."""
    return KINDS[task.object_id[0]](**task.current)


broken = load()
broken.tasks[0] = broken.tasks[0].model_copy(
    update={"why": "We will file this for you and guarantee acceptance in five days."})
out = run_loop(broken, fixer)
check("the loop repairs and passes", out.passed, str(out))
check("it stops as soon as it passes", out.rounds <= 2, str(out.rounds))
check("only the broken object was attempted", set(out.attempts) == {"T001"}, str(out.attempts))

stuck = load()
stuck.tasks[0] = stuck.tasks[0].model_copy(
    update={"why": "You should file this immediately; it is the best option."})
out = run_loop(stuck, stubborn)
check("a loop that cannot converge terminates", not out.passed)
check("it terminates within the round budget", out.rounds <= MAX_ROUNDS, str(out.rounds))
check("it escalates rather than returning a bad kit", out.escalation is not None)
check("attempts per object are bounded",
      all(v <= MAX_ROUNDS for v in out.attempts.values()), str(out.attempts))

check("an unrepaired plan is never returned as passed", not out.passed)

# Merge must not disturb what passed.
one = load()
swapped = merge(one, one.tasks[2].model_copy(update={"title": "Apply for an EIN from the IRS today"}))
check("merge replaces exactly one object",
      sum(1 for a, b in zip(one.tasks, swapped.tasks) if a != b) == 1)

print(f"\n  {sum(results)}/{len(results)} passed")
raise SystemExit(0 if all(results) else 1)
