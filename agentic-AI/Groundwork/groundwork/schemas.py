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
from typing import Annotated, Literal

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

    This is the whole enforcement mechanism. Subclass it and the field becomes
    impossible to state without an official citation behind it.
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


class Money(Cited):
    """A dollar amount that came from an official fee schedule."""

    amount_usd: Annotated[float, Field(ge=0)]

    def __str__(self) -> str:
        return f"${self.amount_usd:,.2f}"


class FormNumber(Cited):
    """An actual form, as the agency names it. Hallucinated form numbers are the
    most common and most expensive way this category of product fails."""

    number: str = Field(min_length=2, max_length=40)
    agency: str = Field(min_length=2)

    def __str__(self) -> str:
        return f"{self.agency} {self.number}"


class Deadline(Cited):
    """When something is due.

    Most deadlines here are rules rather than dates ("no later than two months
    and fifteen days after the beginning of the tax year"), so the rule text is
    required and the resolved date is optional.
    """

    rule: str = Field(min_length=10)
    resolved: date | None = None
    hard: bool = True  # False for "recommended by", True for "you lose the option"


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


class FounderProfile(BaseModel):
    """The typed object every downstream artifact keys off.

    Produced by the discovery interview, which is a workflow: the questions are
    knowable in advance, so nothing here needs an agent.
    """

    model_config = ConfigDict(frozen=True)

    sells: Literal["services", "software", "physical_goods", "mixed"]
    home_state: Literal["TX", "CA", "DE"]
    owners: Annotated[int, Field(ge=1, le=10)]
    hiring_within_12mo: bool
    revenue_band_usd: Literal["pre_revenue", "under_50k", "50k_150k", "150k_400k", "over_400k"]
    touches_client_funds: bool = False
    touches_regulated_data: bool = False
    has_physical_premises: bool = False
    regulated_industry: str | None = None  # health, finance, cannabis, alcohol, firearms
    funding_intent: Literal["bootstrap", "raise_later", "raising_now"] = "bootstrap"
    already_earning: bool = False

    @property
    def out_of_scope_reason(self) -> str | None:
        """v0.1 covers a solo or small services/software business. Anything
        else must escalate to a professional rather than receive a kit."""
        if self.regulated_industry:
            return f"{self.regulated_industry} is a regulated industry"
        if self.hiring_within_12mo:
            return "hiring brings payroll, withholding, and unemployment registration"
        if self.sells == "physical_goods":
            return "physical goods bring sales tax nexus and possibly permits"
        if self.funding_intent == "raising_now":
            return "raising now changes the entity decision materially"
        return None


# --------------------------------------------------------------------------- #
# What the kit contains
# --------------------------------------------------------------------------- #


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
    deadline: Deadline | None = None
    have_ready: list[str] = Field(default_factory=list)
    common_mistakes: list[str] = Field(default_factory=list)
    confidence: Annotated[float, Field(ge=0.0, le=1.0)] = 1.0
    needs_professional: bool = False
    sources: Annotated[list[Source], Field(min_length=1)]

    @model_validator(mode="after")
    def _low_confidence_escalates(self) -> Task:
        """Fail closed. A task the agent is unsure about does not get handed to
        a founder as though it were settled."""
        if self.confidence < 0.75 and not self.needs_professional:
            raise ValueError(
                f"{self.id} has confidence {self.confidence:.2f} and must set "
                "needs_professional=True rather than present as settled"
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

    def all_sources(self) -> list[Source]:
        seen: dict[str, Source] = {}
        for holder in (*self.tasks, *self.decisions, *self.elections):
            for s in holder.sources:
                seen.setdefault(str(s.url), s)
        for t in self.tasks:
            for cited in (t.diy_fee, t.form, t.deadline, t.typical_service_cost):
                if cited is not None:
                    for s in cited.sources:
                        seen.setdefault(str(s.url), s)
        return list(seen.values())
