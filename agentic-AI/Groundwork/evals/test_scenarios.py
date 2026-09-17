"""Scenarios, rather than mutations of one scenario.

The suite this joins exercises a single hand-authored Texas kit and checks that
tampering with it is caught. That is worth having and it is not the same as
knowing the system behaves correctly for a founder who is not that founder.

These cases run whole profiles through routing, readiness and the calendar, and
assert what each founder should actually receive. They are still not a test of
factual accuracy -- see REVIEW.md, which says plainly that the reference answers
have not had domain review.
"""

from __future__ import annotations

import json
import pathlib
import sys
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from groundwork.calendar import form_2553_window, resolve, tx_annual_report, unmet  # noqa: E402
from groundwork.corpus import search  # noqa: E402
from groundwork.schemas import Deadline, FounderProfile, Plan, Source, Tier  # noqa: E402
from groundwork.validate import validate  # noqa: E402

GOLDEN = pathlib.Path(__file__).parents[1] / "fixtures/golden/tx-solo-consultant/plan.json"
results: list[bool] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append(ok)
    print(f"  {'pass' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not ok else ""))


def load() -> Plan:
    return Plan.model_validate(json.loads(GOLDEN.read_text()))


def errors(plan: Plan) -> list[str]:
    f, _ = validate(plan, "strict")
    return [x.message for x in f if x.severity == "error"]


BASE = dict(sells="services", home_state="TX", owners=1,
            hiring_within_12mo=False, revenue_band_usd="50k_150k")

# --- routing: who should not receive a kit at all -------------------------- #

SHOULD_ESCALATE = [
    ("a regulated industry", {"regulated_industry": "cannabis"}),
    ("hiring within the year", {"hiring_within_12mo": True}),
    ("selling physical goods", {"sells": "physical_goods"}),
    ("a mixed goods and services business", {"sells": "mixed"}),
    ("holding client funds", {"touches_client_funds": True}),
    ("handling regulated client data", {"touches_regulated_data": True}),
    ("raising money now", {"funding_intent": "raising_now"}),
    ("operating in two states", {"operating_states": ("TX", "CA")}),
]
for label, override in SHOULD_ESCALATE:
    prof = FounderProfile(**{**BASE, **override})
    check(f"{label} is escalated, not answered", prof.out_of_scope_reason is not None)

in_scope = FounderProfile(**BASE)
check("a solo Texas consultant is in scope", in_scope.out_of_scope_reason is None)

# An out-of-scope founder must not receive a kit even if one was built.
blocked = load()
blocked.profile = blocked.profile.model_copy(update={"touches_client_funds": True})
check("an out-of-scope profile blocks the whole kit",
      any("out of scope" in e for e in errors(blocked)))

# --- the floor every kit owes ---------------------------------------------- #

roles = {t.role for t in load().tasks}
for role in ("entity_formation", "ein", "bank_account", "state_tax_registration"):
    check(f"the kit contains a {role} task", role in roles)

missing = load()
missing.tasks = [t for t in missing.tasks if t.role != "state_tax_registration"]
check("dropping a required role blocks the kit",
      any("state_tax_registration" in e for e in errors(missing)))

# Ordering is the part a founder cannot supply themselves. An EIN applied for
# before the entity exists is attached to a name that does not exist yet.
reordered = load()
ein = next(t for t in reordered.tasks if t.role == "ein")
reordered.tasks = [t if t.role != "ein" else t.model_copy(update={"depends_on": []})
                   for t in reordered.tasks]
check("an EIN that does not follow formation is blocked",
      any("must depend on role=entity_formation" in e for e in errors(reordered)))

bank = load()
bank.tasks = [t if t.role != "bank_account" else t.model_copy(update={"depends_on": ["T001"]})
              for t in bank.tasks]
check("a bank account that does not follow the EIN is blocked",
      any("must depend on role=ein" in e for e in errors(bank)))

# --- the calendar ---------------------------------------------------------- #

may = tx_annual_report(None, in_scope)
check("Texas reporting resolves to a May 15", (may.month, may.day) == (5, 15), str(may))
check("Texas reporting resolves to a future date", may >= date.today(), str(may))

jan_year = FounderProfile(**BASE, tax_year_end="12-31")
window = form_2553_window(None, jan_year)
check("the 2553 window is two months and fifteen days after the tax year starts",
      (window.month, window.day) == (3, 15), str(window))

june_year = FounderProfile(**BASE, tax_year_end="06-30")
window = form_2553_window(None, june_year)
check("the 2553 window follows a non-calendar tax year",
      (window.month, window.day) == (9, 15), str(window))

unknown_year = FounderProfile(**BASE, unknowns=("tax_year_end",))
check("an unknown tax year yields no date, not a guessed one",
      form_2553_window(None, unknown_year) is None)

src = Source(url="https://www.irs.gov/forms-pubs/about-form-2553", tier=Tier.PRIMARY,
             title="IRS - About Form 2553", quote="no later than 2 months and 15 days after the year")
waiting = Deadline(rule="Two months and fifteen days after the tax year begins.",
                   resolver="form_2553_window", needs=("tax_year_end",), sources=[src])
check("a deadline names the fact it is waiting on",
      unmet(waiting, unknown_year) == ("tax_year_end",))
check("and resolves once the fact is known", resolve(waiting, jan_year) is not None)

dated = [(p, c.resolved) for p, c in load().iter_claims() if getattr(c, "resolved", None)]
check("the shipped kit carries real dates", len(dated) >= 2, str(dated))

# --- retrieval quality ------------------------------------------------------ #

hits = search("certificate of formation forms 201 203 205 206", jurisdiction="TX")
check("the fee line is the top hit for its own query",
      bool(hits) and "$300" in hits[0]["text"], hits[0]["text"][:80] if hits else "no hits")
check("the top hit is a primary source", bool(hits) and hits[0]["tier"] == 1)

hits = search("form 2553 election small business corporation")
check("a federal form query reaches the IRS page",
      bool(hits) and "irs" in hits[0]["source_id"], hits[0]["source_id"] if hits else "-")

ca_leak = search("certificate of formation", jurisdiction="TX")
check("no other state's guidance answers a Texas query",
      all(h["jurisdiction"] in ("US", "TX") for h in ca_leak))

print(f"\n  {sum(results)}/{len(results)} passed")
raise SystemExit(0 if all(results) else 1)
