"""What the gate must refuse.

These are the failures a naive build produces on its first run, written as the
outputs themselves rather than as descriptions of them. Run with:

    python3 -m evals.test_gate
"""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from groundwork.schemas import FounderProfile, Jurisdiction, Plan, Source, Task, Tier  # noqa: E402
from groundwork.validate import validate  # noqa: E402

GOLDEN = pathlib.Path(__file__).parents[1] / "fixtures/golden/tx-solo-consultant/plan.json"
PASS, FAIL = "  pass", "  FAIL"
results: list[bool] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    results.append(condition)
    print(f"{PASS if condition else FAIL}  {name}" + (f"  [{detail}]" if detail and not condition else ""))


def load() -> Plan:
    return Plan.model_validate(json.loads(GOLDEN.read_text()))


def errors_for(plan: Plan) -> list[str]:
    findings, _ = validate(plan, "strict")
    return [f.message for f in findings if f.severity == "error"]


# 1. The baseline the rest is measured against.
plan = load()
check("golden kit clears strict mode", not errors_for(plan))

# 2. Advisory language. This is the single most likely output of a naive build:
#    it answers the question it was asked, confidently, and that answer is
#    unlicensed advice.
advised = load()
brief = advised.decisions[0]
advised.decisions[0] = brief.model_copy(
    update={"consequences": "For a consultant at this revenue level you should elect "
                            "S-corp status, which is the best option for most solo owners."}
)
errs = errors_for(advised)
check("blocks advisory language", any("advisory language" in e for e in errs),
      "; ".join(errs) or "nothing raised")

# 3. Promising to act. Groundwork drafts and cites; it never files.
overreach = load()
t = overreach.tasks[0]
overreach.tasks[0] = t.model_copy(update={"why": "We will file this with the state for you and "
                                                 "guarantee acceptance within five days."})
errs = errors_for(overreach)
check("blocks promising to file on the founder's behalf", len(errs) >= 2, "; ".join(errs))

# 4. The Delaware cargo cult, as a jurisdiction leak: a Delaware task in a
#    Texas founder's kit.
leaked = load()
de_task = leaked.tasks[0].model_copy(
    update={"id": "T099", "jurisdiction": Jurisdiction(level="state", code="DE"),
            "title": "File a Delaware Certificate of Formation", "depends_on": []}
)
leaked.tasks = [*leaked.tasks, de_task]
check("blocks out-of-jurisdiction task", any("outside this founder's scope" in e for e in errors_for(leaked)))

# 5. Dependency order. An EIN application filed before the entity exists fails
#    at the IRS, so a cycle is not a cosmetic problem.
cyclic = load()
cyclic.tasks[0] = cyclic.tasks[0].model_copy(update={"depends_on": ["T003"]})
check("blocks a dependency cycle", any("cycle" in e for e in errors_for(cyclic)))

# 6. Fail closed on scope. A regulated industry gets a referral, not a kit.
regulated = load()
regulated.profile = regulated.profile.model_copy(update={"regulated_industry": "cannabis"})
check("blocks out-of-scope founder", any("out of scope" in e for e in errors_for(regulated)))

# 7. The tax inventory is the product. A kit without it is not a kit.
stripped = load()
stripped.elections = []
check("blocks a kit with no tax inventory", any("elections" in e for e in errors_for(stripped)))

# 8. An uncited fee must not be constructible at all -- this one fails at parse
#    time rather than at the gate, which is the stronger guarantee.
try:
    from groundwork.schemas import Money
    Money(amount_usd=300, sources=[Source(url="https://llc-fast.example.com/tx",
                                          tier=Tier.SECONDARY, title="Cheap TX LLC")])
    constructed = True
except Exception:
    constructed = False
check("uncited fee cannot be constructed", not constructed)

# 9. A low-confidence task cannot present itself as settled.
try:
    src = Source(url="https://www.irs.gov/forms-pubs/about-form-ss-4", tier=Tier.PRIMARY, title="SS-4")
    Task(id="T900", title="Something uncertain", why="A reason long enough to pass validation.",
         jurisdiction=Jurisdiction(level="federal", code="US"), agency="IRS",
         official_url=src.url, confidence=0.4, sources=[src])
    constructed = True
except Exception:
    constructed = False
check("low-confidence task must escalate", not constructed)

print(f"\n  {sum(results)}/{len(results)} passed")
raise SystemExit(0 if all(results) else 1)
