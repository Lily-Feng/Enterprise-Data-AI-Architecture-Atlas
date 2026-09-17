"""Turning deadline rules into dates.

A kit that promises a calendar and ships `resolved: null` on every deadline has
promised nothing. The first golden kit did exactly that: six tasks, four
elections, not one computed date.

Not every rule can be computed, and the ones that cannot are the point of the
`needs` field. "No more than 2 months and 15 days after the beginning of the tax
year" is arithmetic once the tax year is known and is unanswerable before that.
So a deadline either resolves, or it names the fact it is waiting on, and the
thing holding it is marked `needs_info` rather than presented as settled.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Callable

from .schemas import Deadline, FounderProfile, Plan

Resolver = Callable[[Deadline, FounderProfile], date | None]


def _next_annual(month: int, day: int, on: date | None = None) -> date:
    today = on or date.today()
    this_year = date(today.year, month, day)
    return this_year if this_year >= today else date(today.year + 1, month, day)


def tx_annual_report(deadline: Deadline, profile: FounderProfile) -> date | None:
    """Texas franchise tax reporting is due May 15 each year."""
    return _next_annual(5, 15)


def form_2553_window(deadline: Deadline, profile: FounderProfile) -> date | None:
    """Two months and fifteen days after the start of the tax year.

    The IRS states the rule in months, so the month arithmetic is done in
    months rather than in an approximate number of days.
    """
    start = profile.tax_year_start
    if start is None:
        return None
    month = start.month + 2
    year = start.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    day = min(start.day, 28)
    return date(year, month, day) + timedelta(days=14)


RESOLVERS: dict[str, Resolver] = {
    "tx_annual_report": tx_annual_report,
    "form_2553_window": form_2553_window,
}


def resolve(deadline: Deadline, profile: FounderProfile) -> date | None:
    """The date, or None when a required fact is missing or no rule exists."""
    if deadline.resolver is None:
        return None
    if any(not profile.knows(f) for f in deadline.needs):
        return None
    fn = RESOLVERS.get(deadline.resolver)
    return fn(deadline, profile) if fn else None


def unmet(deadline: Deadline, profile: FounderProfile) -> tuple[str, ...]:
    """Which facts this deadline is waiting on."""
    return tuple(f for f in deadline.needs if not profile.knows(f))


def resolve_plan(plan: Plan) -> dict[str, date | None]:
    """Every deadline in the plan, resolved where the facts allow."""
    out: dict[str, date | None] = {}
    for path, claim in plan.iter_claims():
        if isinstance(claim, Deadline):
            out[path] = resolve(claim, plan.profile)
    return out
