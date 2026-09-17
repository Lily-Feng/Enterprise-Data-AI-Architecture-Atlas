"""Typed shapes for a Groundwork kit.

The load-bearing rule of this project is that Groundwork routes, cites, and
computes -- it never advises and never files. That rule is not a disclaimer in a
README; it is enforced here, in the type system.

A fee, a form number, and a deadline are the three things a founder acts on and
the three things that cost real money when they are wrong. Each is a value
object that cannot be constructed without a tier-1 source. A model that tries to
emit an uncited fee does not produce a bad kit -- it fails to parse.
"""

from __future__ import annotations

from datetime import date, timedelta
from enum import IntEnum
from typing import Annotated, Iterator, Literal

import re

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)

# A cited fact older than this is treated as stale: state fee schedules and
# filing deadlines turn over annually, and a confidently wrong fee is the exact
# failure this project exists to prevent.
STALE_AFTER = timedelta(days=90)

WS_RE = re.compile(r"\s+")


class Tier(IntEnum):
    """How much weight a source is allowed to carry.

    Page one of any search for "form an LLC" is dominated by filing mills with a
    financial interest in the answer. Ranking source authority is therefore a
    safety control, not bookkeeping.
    """

    PRIMARY = 1  # .gov: IRS, Secretary of State, state tax authority
    GUIDANCE = 2  # SBA and other official explanatory material
    SECONDARY = 3  # reputable third parties; orientation only, always labeled


class Jurisdiction(BaseModel):
    """Federal, or one of the states this kit actually covers.

    Three states, honestly maintained, beats fifty that go stale in a month.
    """

    model_config = ConfigDict(frozen=True)

    level: Literal["federal", "state"]
    code: Literal["US", "TX", "CA", "DE"]

    @model_validator(mode="after")
    def _level_matches_code(self) -> Jurisdiction:
        if self.level == "federal" and self.code != "US":
            raise ValueError("federal jurisdiction must use code 'US'")
        if self.level == "state" and self.code == "US":
            raise ValueError("state jurisdiction cannot use code 'US'")
        return self

    def __str__(self) -> str:
        return self.code


class Source(BaseModel):
    """One citation.

    `retrieved_at` is None until something has actually fetched the page. The
    validator refuses to ship a kit containing unverified sources, so a plan may
    be drafted against a URL the agent has not read but may never reach a
    founder that way.
    """

    model_config = ConfigDict(frozen=True)

    url: HttpUrl
    tier: Tier
    title: str = Field(min_length=3)
    retrieved_at: date | None = None
    effective_date: date | None = None
    quote: str | None = Field(default=None, max_length=600)

    @model_validator(mode="after")
    def _primary_must_be_official(self) -> Source:
        if self.tier is Tier.PRIMARY:
            host = (self.url.host or "").lower()
            if not (host.endswith(".gov") or host.endswith(".us")):
                raise ValueError(
                    f"tier-1 source must be an official .gov/.us host, got {host!r}"
                )
        return self

    @property
    def verified(self) -> bool:
        return self.retrieved_at is not None

    @property
    def stale(self) -> bool:
        return self.verified and (date.today() - self.retrieved_at) > STALE_AFTER


class Cited(BaseModel):
    """Base for any value a founder will act on. Requires a tier-1 source.

    A citation proves a page was consulted. It does not prove the page says
    what the claim says -- a fee of $999,999 cited to a schedule reading $300
    satisfies every structural rule here and is still a lie.

    So a citation is necessary and not sufficient. `supports()` is where each
    subclass states what its evidence must actually contain, and
    `validate.check_evidence` is what confronts that evidence with the text
    the fetcher really retrieved.
    """

    model_config = ConfigDict(frozen=True)

    sources: Annotated[list[Source], Field(min_length=1)]

    @field_validator("sources")
    @classmethod
    def _needs_primary(cls, sources: list[Source]) -> list[Source]:
        if not any(s.tier is Tier.PRIMARY for s in sources):
            raise ValueError(
                f"{cls.__name__} states a fact a founder will act on and needs at "
                "least one tier-1 (.gov) source"
            )
        return sources

    @property
    def evidence(self) -> Source | None:
        """The tier-1 source carrying a quote, if any."""
        for s in self.sources:
            if s.tier is Tier.PRIMARY and s.quote:
                return s
        return None

    def supports(self, quote: str) -> bool:
        """Does this quote actually contain the claim?

        Subclasses that assert a checkable value override this. The base case
        is deliberately conservative: unknown claim shapes are not waved
        through.
        """
        return False

    def claim(self) -> str:
        return str(self)


class Money(Cited):
    """A dollar amount that came from an official fee schedule."""

    amount_usd: Annotated[float, Field(ge=0)]

    def __str__(self) -> str:
        return f"${self.amount_usd:,.2f}"

    def supports(self, quote: str) -> bool:
        """The amount has to appear in the quoted text, in some readable form.

        A zero fee is the awkward case: pages say "no fee" or "free" rather
        than "$0.00", so those phrasings count as the amount appearing.
        """
        text = WS_RE.sub(" ", quote.lower())
        if self.amount_usd == 0:
            return any(p in text for p in ("no fee", "no charge", "free of charge",
                                           "at no cost", "for free", "$0",
                                           "never have to pay", "without charge"))
        whole = int(self.amount_usd)
        forms = {f"${whole:,}", f"${whole}", f"{whole:,}", str(whole),
                 f"${self.amount_usd:,.2f}", f"${self.amount_usd:.2f}"}
        return any(f.lower() in text for f in forms)


class FormNumber(Cited):
    """An actual form, as the agency names it. Hallucinated form numbers are the
    most common and most expensive way this category of product fails."""

    number: str = Field(min_length=2, max_length=40)
    agency: str = Field(min_length=2)

    def __str__(self) -> str:
        return f"{self.agency} {self.number}"

    def supports(self, quote: str) -> bool:
        """The form number itself has to be in the quoted text."""
        text = WS_RE.sub(" ", quote.lower())
        n = self.number.lower()
        return n in text or n.replace("form ", "") in text


class Deadline(Cited):
    """When something is due.

    Most deadlines here are rules rather than dates ("no later than two months
    and fifteen days after the beginning of the tax year"), so the rule text is
    required and the resolved date is optional.
    """

    rule: str = Field(min_length=10)
    resolved: date | None = None
    hard: bool = True  # False for "recommended by", True for "you lose the option"
    needs: tuple[str, ...] = ()  # profile fields required to turn the rule into a date
    resolver: str | None = None  # a named rule in calendar.py that computes the date

    @property
    def computable(self) -> bool:
        """A deadline with no unmet input is one the kit owes the founder as a
        date. Every deadline in the first golden kit had resolved=None while the
        kit promised a calendar."""
        return not self.needs

    def claim(self) -> str:
        return self.rule

    def supports(self, quote: str) -> bool:
        """A deadline rule is prose and cannot be matched mechanically.

        What can be required is that the quote carries the words a deadline is
        made of. This is the weakest of the three checks and is documented as
        such rather than presented as equivalent to the fee and form checks.
        """
        text = WS_RE.sub(" ", quote.lower())
        markers = ("day", "month", "year", "due", "deadline", "no later",
                   "within", "before", "by the", "anniversary")
        return any(m in text for m in markers)


class Quote(BaseModel):
    """What a third party charges to do something for you.

    Not a Cited: service pricing is not government data, so it may rest on a
    tier-2 or tier-3 source. It exists only to sit next to the official fee in
    costs.md and make the delta visible.
    """

    model_config = ConfigDict(frozen=True)

    amount_usd: Annotated[float, Field(ge=0)]
    vendor_kind: str = Field(min_length=3)  # "registered agent service", "filing service"
    sources: Annotated[list[Source], Field(min_length=1)]


# --------------------------------------------------------------------------- #
# The founder
# --------------------------------------------------------------------------- #


class DecisionRecord(BaseModel):
    """A decision the founder has actually made, and when.

    Without this the plan is free to assume one. With it, a task that
    presupposes an unmade decision is a validation error rather than a quiet
    recommendation embedded in the ordering.
    """

    model_config = ConfigDict(frozen=True)

    decision_id: str = Field(pattern=r"^D\d{3}$")
    choice: str = Field(min_length=2)
    decided_on: date | None = None


class FounderProfile(BaseModel):
    """The typed object every downstream artifact keys off.

    Produced by the discovery interview, which is a workflow: the questions are
    knowable in advance, so nothing here needs an agent.

    The first version of this carried eight fields and could not support the
    thing the kit promised. A calendar needs to know when the business started,
    what its tax year is, and whether the entity exists yet; none of that was
    asked, so every deadline in the golden kit resolved to null. An unknown is
    now a value the profile can hold, rather than a gap the plan quietly fills.
    """

    model_config = ConfigDict(frozen=True)

    # What the business is
    sells: Literal["services", "software", "physical_goods", "mixed"]
    home_state: Literal["TX", "CA", "DE"]
    operating_states: tuple[Literal["TX", "CA", "DE"], ...] = ()
    owners: Annotated[int, Field(ge=1, le=10)]
    hiring_within_12mo: bool
    revenue_band_usd: Literal["pre_revenue", "under_50k", "50k_150k", "150k_400k", "over_400k"]

    # Where it is in its life. Without these there is no calendar.
    formation_status: Literal["not_formed", "filing_pending", "formed"] = "not_formed"
    formation_date: date | None = None
    business_start_date: date | None = None
    tax_year_end: str = Field(default="12-31", pattern=r"^\d{2}-\d{2}$")
    existing_elections: tuple[str, ...] = ()

    # Risk surface
    touches_client_funds: bool = False
    touches_regulated_data: bool = False
    has_physical_premises: bool = False
    regulated_industry: str | None = None
    funding_intent: Literal["bootstrap", "raise_later", "raising_now"] = "bootstrap"
    already_earning: bool = False

    decided: tuple[DecisionRecord, ...] = ()
    unknowns: tuple[str, ...] = ()  # fields the founder could not answer

    def has_decided(self, decision_id: str) -> bool:
        return any(d.decision_id == decision_id for d in self.decided)

    def knows(self, field: str) -> bool:
        """Whether a fact is available to compute with.

        A field is unknown if the founder said so or if it is simply absent.
        Both have to count, or an unanswered question silently becomes a
        default the plan treats as fact.
        """
        if field in self.unknowns:
            return False
        return getattr(self, field, None) is not None

    @property
    def tax_year_start(self) -> date | None:
        """First day of the current tax year, if the year end is known."""
        if "tax_year_end" in self.unknowns:
            return None
        month, day = (int(x) for x in self.tax_year_end.split("-"))
        today = date.today()
        end_this_year = date(today.year, month, day)
        start = end_this_year + timedelta(days=1)
        return start.replace(year=start.year - 1) if today <= end_this_year else start

    @property
    def out_of_scope_reason(self) -> str | None:
        """v0.1 covers a solo or small services/software business. Anything
        else is escalated rather than answered.

        The first version checked four conditions and collected three more it
        never used: `mixed` sales slipped through the physical-goods rule, and
        the client-funds and regulated-data flags changed nothing at all.
        """
        if self.regulated_industry:
            return f"{self.regulated_industry} is a regulated industry"
        if self.hiring_within_12mo:
            return "hiring brings payroll, withholding, and unemployment registration"
        if self.sells in ("physical_goods", "mixed"):
            return "selling goods brings sales tax nexus and possibly permits"
        if self.touches_client_funds:
            return "holding client funds brings licensing and trust-account obligations"
        if self.touches_regulated_data:
            return "regulated client data brings sector-specific obligations"
        if self.funding_intent == "raising_now":
            return "raising now changes the entity decision materially"
        if len(self.operating_states) > 1 or (
            self.operating_states and self.home_state not in self.operating_states
        ):
            return "operating in more than one state raises foreign qualification"
        return None


# --------------------------------------------------------------------------- #
# What the kit contains
# --------------------------------------------------------------------------- #


class Review(BaseModel):
    """Evidence that the professional review a task asked for actually occurred."""

    model_config = ConfigDict(frozen=True)

    reviewed_by: str = Field(min_length=2)
    reviewed_on: date
    note: str | None = None


class Option(BaseModel):
    """One branch of a real decision."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=2)
    what_it_actually_is: str = Field(min_length=20)
    cost: Money | Quote | None = None
    consequence: str = Field(min_length=20)


class DecisionBrief(BaseModel):
    """A decision the founder has to make, in ADR shape.

    There is deliberately no `recommendation` field. Groundwork lays out what
    differs and what it depends on; the founder and their professional decide.
    Adding a recommendation field here would be the single change that turns
    this product into unlicensed advice, so the shape forbids it.
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(pattern=r"^D\d{3}$")
    title: str = Field(min_length=5)
    context: str = Field(min_length=40)
    common_misconception: str | None = None
    options: Annotated[list[Option], Field(min_length=2)]
    what_actually_differs: str = Field(min_length=40)
    depends_on_facts: Annotated[list[str], Field(min_length=1)]
    consequences: str = Field(min_length=40)
    professional_question: str = Field(min_length=20)
    sources: Annotated[list[Source], Field(min_length=1)]


class Task(BaseModel):
    """One thing the founder does, once, in an order that matters."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(pattern=r"^T\d{3}$")
    title: str = Field(min_length=5)
    why: str = Field(min_length=20)
    jurisdiction: Jurisdiction
    agency: str = Field(min_length=2)
    form: FormNumber | None = None
    official_url: HttpUrl
    diy_fee: Money | None = None
    typical_service_cost: Quote | None = None
    processing_time_days: tuple[int, int] | None = None
    depends_on: list[str] = Field(default_factory=list)
    requires_decision: str | None = Field(default=None, pattern=r"^D\d{3}$")
    deadline: Deadline | None = None
    have_ready: list[str] = Field(default_factory=list)
    common_mistakes: list[str] = Field(default_factory=list)
    confidence: Annotated[float, Field(ge=0.0, le=1.0)] = 1.0
    needs_professional: bool = False
    status: Literal["ready", "needs_info", "awaiting_review"] = "ready"
    review: Review | None = None
    sources: Annotated[list[Source], Field(min_length=1)]

    @model_validator(mode="after")
    def _low_confidence_escalates(self) -> Task:
        """Fail closed, and stay closed until the escalation is answered.

        Setting needs_professional used to be enough to pass. A task can now
        only be `ready` once a Review records that the review happened; until
        then it is awaiting_review, and a founder reading the kit can see the
        difference.
        """
        if self.confidence < 0.75 and not self.needs_professional:
            raise ValueError(
                f"{self.id} has confidence {self.confidence:.2f} and must set "
                "needs_professional=True rather than present as settled"
            )
        if self.needs_professional and self.review is None and self.status == "ready":
            raise ValueError(
                f"{self.id} needs professional review and has none recorded, so it "
                "cannot be status='ready'; use 'awaiting_review'"
            )
        return self

    @property
    def savings_usd(self) -> float:
        """What doing it yourself saves. The kit's headline number."""
        if self.typical_service_cost is None:
            return 0.0
        official = self.diy_fee.amount_usd if self.diy_fee else 0.0
        return max(0.0, self.typical_service_cost.amount_usd - official)


class Election(BaseModel):
    """A tax election or deduction that exists for this profile.

    This is where "maximum tax benefit" lives, and it is inventory rather than
    optimization: what exists, who is eligible, what it costs, when the window
    closes. Founders rarely lose money by choosing wrong. They lose it by never
    hearing the option existed until the deadline had passed.
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(pattern=r"^E\d{3}$")
    name: str = Field(min_length=5)
    what_it_does: str = Field(min_length=30)
    form: FormNumber | None = None
    eligibility: Annotated[list[str], Field(min_length=1)]
    deadline: Deadline | None = None
    admin_cost_note: str | None = None
    lost_if_missed: str = Field(min_length=20)
    professional_question: str = Field(min_length=20)
    sources: Annotated[list[Source], Field(min_length=1)]


class Plan(BaseModel):
    """The whole kit, before it is compiled into files."""

    profile: FounderProfile
    tasks: Annotated[list[Task], Field(min_length=1)]
    decisions: list[DecisionBrief] = Field(default_factory=list)
    elections: list[Election] = Field(default_factory=list)
    generated_at: date = Field(default_factory=date.today)

    @property
    def total_official_fees(self) -> float:
        return sum(t.diy_fee.amount_usd for t in self.tasks if t.diy_fee)

    @property
    def total_savings(self) -> float:
        return sum(t.savings_usd for t in self.tasks)

    def iter_claims(self) -> Iterator[tuple[str, Cited]]:
        """Every Cited value anywhere in the plan, with the path that reaches it.

        Written as a full recursive walk rather than a hand-listed set of
        fields. The hand-listed version silently skipped election forms,
        election deadlines, and decision-option costs, so an unfetched source
        on any of them passed strict validation.
        """

        def walk(node: object, path: str) -> Iterator[tuple[str, Cited]]:
            if isinstance(node, Cited):
                yield path, node
            if isinstance(node, BaseModel):
                for name in type(node).model_fields:
                    yield from walk(getattr(node, name), f"{path}.{name}")
            elif isinstance(node, (list, tuple)):
                for i, item in enumerate(node):
                    yield from walk(item, f"{path}[{i}]")

        for group, items in (("tasks", self.tasks), ("decisions", self.decisions),
                             ("elections", self.elections)):
            for item in items:
                yield from walk(item, getattr(item, "id", group))

    def iter_sources(self) -> Iterator[tuple[str, Source]]:
        """Every Source anywhere, with its path. Not deduplicated: the same URL
        used in two places has to be checked in both."""

        def walk(node: object, path: str) -> Iterator[tuple[str, Source]]:
            if isinstance(node, Source):
                yield path, node
                return
            if isinstance(node, BaseModel):
                for name in type(node).model_fields:
                    yield from walk(getattr(node, name), f"{path}.{name}")
            elif isinstance(node, (list, tuple)):
                for i, item in enumerate(node):
                    yield from walk(item, f"{path}[{i}]")

        for item in (*self.tasks, *self.decisions, *self.elections):
            yield from walk(item, getattr(item, "id", "?"))

    def all_sources(self) -> list[Source]:
        """Distinct sources, for reporting. Validation uses iter_sources so that
        the same URL cited in two places is checked in both."""
        seen: dict[str, Source] = {}
        for _, s in self.iter_sources():
            seen.setdefault(str(s.url), s)
        return list(seen.values())
