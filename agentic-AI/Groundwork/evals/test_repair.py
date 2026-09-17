"""Repair has to be scoped, and it has to stop."""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from groundwork.repair import MAX_ROUNDS, escalate, repair_round  # noqa: E402
from groundwork.schemas import Jurisdiction, Plan  # noqa: E402
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

print(f"\n  {sum(results)}/{len(results)} passed")
raise SystemExit(0 if all(results) else 1)
