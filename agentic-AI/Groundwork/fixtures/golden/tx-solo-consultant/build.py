"""The golden kit: a solo consultant in Texas, services, pre-S-corp revenue.

Hand-authored so that generation has a target to be graded against. Every
amount here is provisional: sources carry `retrieved_at=None` until Phase 0
actually fetches them, which is why this fixture passes `draft` and is blocked
by `strict`. That is the gate working, not a bug to route around.
"""

import json
import pathlib
import sys
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from groundwork.calendar import resolve  # noqa: E402
from groundwork.schemas import (  # noqa: E402
    Deadline, DecisionBrief, DecisionRecord, Election, FormNumber, FounderProfile,
    Jurisdiction, Money, Option, Plan, Quote, Source, Task, Tier,
)

US = Jurisdiction(level="federal", code="US")
TX = Jurisdiction(level="state", code="TX")


def gov(url: str, title: str) -> Source:
    return Source(url=url, tier=Tier.PRIMARY, title=title)


def guidance(url: str, title: str) -> Source:
    return Source(url=url, tier=Tier.GUIDANCE, title=title)


SOS_FORMS = gov("https://www.sos.state.tx.us/corp/forms_boc.shtml",
                "Texas SOS - Business Organizations Code Forms")
SOS_FORM_205 = Source(
    url="https://www.sos.state.tx.us/corp/forms_boc.shtml",
    tier=Tier.PRIMARY, title="Texas SOS - Business Organizations Code Forms",
    quote="Form 205 - Certificate of Formation for a Limited Liability Company",
)
SOS_FEES = Source(
    url="https://direct.sos.state.tx.us/help/help-corp.asp?pg=fee",
    tier=Tier.PRIMARY,
    title="Texas SOSDirect - Filing Fee Schedule",
    quote="Certificate of formation for a Texas entity (except nonprofit corporation, "
          "cooperative association, PA or LP) (Forms 201, 203, 205, 206) $300",
)
EIN = gov("https://www.irs.gov/businesses/small-businesses-self-employed/apply-for-an-employer-identification-number-ein-online",
          "IRS - Apply for an EIN Online")
EIN_FREE = Source(
    url="https://www.irs.gov/businesses/small-businesses-self-employed/apply-for-an-employer-identification-number-ein-online",
    tier=Tier.PRIMARY, title="IRS - Apply for an EIN Online",
    quote="Beware of websites that charge for an EIN. You never have to pay a fee for an EIN.",
)
SS4 = gov("https://www.irs.gov/forms-pubs/about-form-ss-4", "IRS - About Form SS-4")
SS4_FORM = Source(
    url="https://www.irs.gov/forms-pubs/about-form-ss-4", tier=Tier.PRIMARY,
    title="IRS - About Form SS-4",
    quote="Use Form SS-4 to apply for an employer identification number (EIN).",
)
F2553 = gov("https://www.irs.gov/forms-pubs/about-form-2553",
            "IRS - About Form 2553, Election by a Small Business Corporation")
F2553_FORM = Source(
    url="https://www.irs.gov/forms-pubs/about-form-2553", tier=Tier.PRIMARY,
    title="IRS - About Form 2553, Election by a Small Business Corporation",
    quote="About Form 2553, Election by a Small Business Corporation",
)
TX_FRANCHISE = gov("https://comptroller.texas.gov/taxes/franchise/",
                   "Texas Comptroller - Franchise Tax")
TX_NO_TAX_DUE = Source(
    url="https://comptroller.texas.gov/taxes/franchise/", tier=Tier.PRIMARY,
    title="Texas Comptroller - Franchise Tax",
    quote="If you are at or below the no tax due threshold, simply file your 2026 "
          "Public Information Report or Ownership Report.",
)
# Publication 535 is retained only as evidence that it was discontinued.
PUB535_GONE = Source(
    url="https://www.irs.gov/forms-pubs/about-publication-535", tier=Tier.PRIMARY,
    title="IRS - About Publication 535, Business Expenses",
    quote="Note: We have discontinued Publication 535, Business Expenses; the last "
          "revision was for 2022.",
)
I2553 = Source(
    url="https://www.irs.gov/instructions/i2553", tier=Tier.PRIMARY,
    title="IRS - Instructions for Form 2553",
    quote="No more than 2 months and 15 days after the beginning of the tax year the "
          "election is to take effect, or",
)
I2553_LATE = Source(
    url="https://www.irs.gov/instructions/i2553", tier=Tier.PRIMARY,
    title="IRS - Instructions for Form 2553",
    quote="Relief for Late Elections",
)
PUB583 = Source(
    url="https://www.irs.gov/publications/p583", tier=Tier.PRIMARY,
    title="IRS - Publication 583, Starting a Business and Keeping Records",
    quote="You can elect to deduct up to $5,000 of business start-up costs",
)
PUB560_DUE = Source(
    url="https://www.irs.gov/publications/p560", tier=Tier.PRIMARY,
    title="IRS - Publication 560, Retirement Plans for Small Business",
    quote="You can make deductible contributions for a tax year up to the due date of "
          "your return (plus extensions) for that year.",
)
PUB334 = Source(
    url="https://www.irs.gov/forms-pubs/about-publication-334", tier=Tier.PRIMARY,
    title="IRS - About Publication 334, Tax Guide for Small Business",
    quote="About Publication 334, Tax Guide for Small Business",
)
PUB587 = gov("https://www.irs.gov/forms-pubs/about-publication-587",
             "IRS - About Publication 587, Business Use of Your Home")
PUB560 = Source(
    url="https://www.irs.gov/forms-pubs/about-publication-560", tier=Tier.PRIMARY,
    title="IRS - About Publication 560, Retirement Plans for Small Business",
    quote="About Publication 560, Retirement Plans for Small Business "
          "(SEP, SIMPLE and Qualified Plans)",
)
SBA_REGISTER = guidance("https://www.sba.gov/business-guide/launch-your-business/register-your-business",
                        "SBA - Register your business")
SBA_INSURANCE = guidance("https://www.sba.gov/business-guide/launch-your-business/get-business-insurance",
                         "SBA - Get business insurance")

# This kit files an LLC, so it presupposes that the founder chose one. That was
# previously implicit in the task ordering, which let the plan recommend by
# arrangement. Recording it makes T001 legal and makes the assumption visible.
profile = FounderProfile(
    sells="services", home_state="TX", owners=1, hiring_within_12mo=False,
    revenue_band_usd="50k_150k", funding_intent="bootstrap", already_earning=True,
    decided=(DecisionRecord(decision_id="D001", choice="LLC (state legal entity)"),),
    formation_status="not_formed",
    business_start_date=date(2026, 3, 1),
    tax_year_end="12-31",
    # Said plainly rather than defaulted. The formation date cannot be known
    # before the filing is accepted, and anything keyed to it stays needs_info.
    unknowns=("formation_date",),
)

tasks = [
    Task(
        id="T001", role="entity_formation",
        title="File the Certificate of Formation with the Texas Secretary of State",
        why="The LLC does not exist until the state accepts this filing, and every "
            "later step depends on it existing.",
        jurisdiction=TX, agency="Texas Secretary of State",
        requires_decision="D001",
        form=FormNumber(number="Form 205", agency="Texas SOS", sources=[SOS_FORM_205]),
        official_url=SOS_FORMS.url,
        diy_fee=Money(amount_usd=300.00, sources=[SOS_FEES]),
        processing_time_days=(3, 15),
        have_ready=["Entity name plus two alternates", "Registered agent name and Texas street address",
                    "Governing authority (member-managed or manager-managed)", "Your mailing address"],
        common_mistakes=[
            "Using a PO box as the registered agent address; Texas requires a physical street address.",
            "Filing before checking name availability, which forces a refile at full fee.",
        ],
        sources=[SOS_FORMS, SOS_FEES],
    ),
    Task(
        id="T002", role="governing_document",
        title="Adopt a written operating agreement",
        why="Texas does not file it, but banks ask for it and it is what separates "
            "the entity from its owner if that separation is ever tested.",
        jurisdiction=TX, agency="Internal document - not filed",
        official_url=SBA_REGISTER.url,
        depends_on=["T001"],
        have_ready=["Ownership percentages", "How profit is distributed", "What happens if an owner leaves"],
        common_mistakes=["Skipping it because a single-member LLC 'does not need one' - the bank will still ask."],
        sources=[SBA_REGISTER],
    ),
    Task(
        id="T003", role="ein",
        title="Apply for an EIN from the IRS",
        why="The EIN is the business's tax identity and is required to open a "
            "business bank account without using a Social Security number.",
        jurisdiction=US, agency="IRS",
        form=FormNumber(number="Form SS-4", agency="IRS", sources=[SS4_FORM]),
        official_url=EIN.url,
        diy_fee=Money(amount_usd=0.00, sources=[EIN_FREE]),
        processing_time_days=(0, 1),
        depends_on=["T001"],
        have_ready=["Exact legal entity name as filed", "Formation date and state", "Responsible party SSN or ITIN"],
        common_mistakes=[
            "Paying a service for this. The IRS issues an EIN at no charge and the online "
            "application takes minutes.",
            "Applying before the entity is formed, which produces an EIN attached to the wrong name.",
        ],
        sources=[EIN, SS4],
    ),
    Task(
        id="T004", role="bank_account",
        title="Open a business bank account",
        why="Commingling personal and business funds is the most common way the "
            "liability separation an LLC provides gets argued away.",
        jurisdiction=US, agency="Your bank",
        official_url=SBA_REGISTER.url,
        depends_on=["T001", "T002", "T003"],
        have_ready=["Filed Certificate of Formation", "EIN letter (CP 575)", "Operating agreement", "Photo ID"],
        common_mistakes=["Running revenue through a personal account 'just until things settle'."],
        sources=[SBA_REGISTER],
    ),
    Task(
        id="T005", role="state_tax_registration",
        title="Set up a Texas franchise tax account and file the annual report",
        why="A Texas LLC has an annual filing with the Comptroller even when it owes "
            "no tax. Which filing depends on where the entity sits relative to the no "
            "tax due threshold, and missing it is what puts the entity out of good "
            "standing.",
        jurisdiction=TX, agency="Texas Comptroller of Public Accounts",
        official_url=TX_FRANCHISE.url,
        depends_on=["T001"],
        deadline=Deadline(
            rule="Franchise tax reports are due each May 15. An entity at or below the "
                 "no tax due threshold files a Public Information Report or Ownership "
                 "Report rather than a tax report.",
            hard=True, resolver="tx_annual_report", sources=[TX_NO_TAX_DUE]),
        common_mistakes=[
            "Assuming no tax due means nothing is due. For report years 2024 and later "
            "the separate No Tax Due Report was discontinued, but an entity at or below "
            "the threshold still files a Public Information Report or Ownership Report.",
            "Looking up the threshold for the wrong report year. It is set per year.",
        ],
        confidence=0.8,
        sources=[TX_FRANCHISE],
    ),
    Task(
        id="T006", role="insurance",
        title="Obtain professional liability and general liability insurance",
        why="An LLC limits owner liability for business debts; it does not cover "
            "a claim arising from the work itself.",
        jurisdiction=US, agency="Private carrier",
        official_url=SBA_INSURANCE.url,
        depends_on=["T001"],
        confidence=0.7, needs_professional=True, status="awaiting_review",
        common_mistakes=["Assuming the entity itself is the insurance."],
        sources=[SBA_INSURANCE],
    ),
]

decisions = [
    DecisionBrief(
        id="D001",
        title="'LLC or S-corp' is two separate questions wearing one coat",
        context="First-time founders almost always arrive asking whether to form an "
                "LLC or an S-corp, and the question has no answer as posed because "
                "the two words describe different layers of the stack.",
        common_misconception="That an LLC and an S-corp are two entity types to pick between.",
        options=[
            Option(name="LLC (state legal entity)",
                   what_it_actually_is="A legal entity created by filing with a state. It determines "
                                       "who is liable for the business's obligations.",
                   consequence="By default a single-member LLC is taxed as a sole proprietorship: "
                               "profit flows to a Schedule C and is subject to self-employment tax."),
            Option(name="S-corp (federal tax election)",
                   what_it_actually_is="An election filed with the IRS on Form 2553 that changes how an "
                                       "existing LLC or corporation is taxed. It creates no entity.",
                   consequence="Profit splits into reasonable salary plus distribution, which changes the "
                               "self-employment tax base, and it adds payroll administration and a "
                               "separate business return."),
        ],
        what_actually_differs="The entity decision and the tax-treatment decision are made at different "
                              "times, with different agencies, on different deadlines. An LLC can make "
                              "the S-corp election later; the election cannot exist without an entity "
                              "under it.",
        depends_on_facts=["Annual profit after expenses",
                          "What counts as reasonable salary for this work in this market",
                          "Cost of payroll administration and a second tax return",
                          "Whether the 2553 window for the intended tax year is still open"],
        consequences="Treating these as one decision is how founders either form an entity they did not "
                     "need or miss an election window they did. The two decisions are sequenced, not "
                     "traded off.",
        professional_question="Given my projected profit, at what point does the self-employment tax "
                              "saved by an S-corp election exceed the payroll and filing cost it adds?",
        sources=[F2553, SBA_REGISTER],
    ),
    DecisionBrief(
        id="D002",
        title="Forming in Delaware while living and working in Texas",
        context="Delaware's reputation as the default state of incorporation comes from venture-backed "
                "C-corps, and it propagates to solo founders whose situation does not resemble that one.",
        common_misconception="That Delaware formation is a neutral default with no cost.",
        options=[
            Option(name="Form in Texas",
                   what_it_actually_is="One filing, one state, one annual report, and the registered "
                                       "agent can be the founder at a Texas street address.",
                   consequence="One set of fees and one set of deadlines."),
            Option(name="Form in Delaware, operate from Texas",
                   what_it_actually_is="A Delaware entity that transacts business in Texas generally must "
                                       "also register in Texas as a foreign entity.",
                   consequence="Two states' fees, two annual obligations, and a registered agent in "
                               "Delaware who must be paid because the founder is not there."),
        ],
        what_actually_differs="Whether the business pays one state or two for the same operation, and "
                              "whether a paid registered agent becomes mandatory.",
        depends_on_facts=["Whether outside investors have asked for a Delaware entity",
                          "Where the work is actually performed",
                          "Delaware franchise tax and registered agent cost at current rates"],
        consequences="For a founder whose customers, work, and residence are all in one state, the "
                     "second state adds recurring cost and a second calendar without changing the "
                     "liability outcome.",
        professional_question="Does anything in my funding plan over the next 24 months require a "
                              "Delaware entity, and what does it cost to convert later if it does?",
        sources=[SOS_FORMS, SBA_REGISTER],
    ),
]

elections = [
    Election(
        id="E001", name="S corporation election",
        what_it_does="Changes how an existing LLC's profit is taxed by splitting it into reasonable "
                     "salary and distribution, which changes the self-employment tax base.",
        form=FormNumber(number="Form 2553", agency="IRS", sources=[F2553_FORM]),
        eligibility=["A domestic entity with allowable shareholders",
                     "One class of stock or equivalent membership interest",
                     "All owners consent"],
        deadline=Deadline(
            rule="No more than two months and fifteen days after the beginning of the tax year the "
                 "election is to take effect, or at any time during the preceding tax year.",
            hard=True, resolver="form_2553_window", needs=("tax_year_end",),
            sources=[I2553]),
        admin_cost_note="Adds payroll administration and a separate business return.",
        lost_if_missed="A late election generally takes effect the following tax year. The IRS "
                       "does document conditional relief for late elections, so a missed window is "
                       "not automatically a year lost, but relief is conditional and is not "
                       "something to plan around.",
        professional_question="I missed (or expect to miss) the window. Do I qualify for late "
                              "election relief, and what does the filing have to show?",
        sources=[I2553, I2553_LATE],
    ),
    Election(
        id="E002", name="Business start-up cost deduction",
        what_it_does="Allows a portion of costs incurred investigating and setting up the business "
                     "before it opened to be deducted, with the remainder amortized.",
        eligibility=["Costs incurred before the business began operating",
                     "Costs would have been deductible had the business already been active"],

        lost_if_missed="Receipts discarded before launch cannot be reconstructed later, so this is "
                       "lost by inaction rather than by decision.",
        admin_cost_note="Older guidance cites Publication 535, which the IRS discontinued after its "
                        "2022 revision. Current material sits in Publication 583 and the Tax Guide "
                        "for Small Business.",
        professional_question="Which of my pre-launch costs qualify, and how should I be recording them "
                              "starting today?",
        sources=[PUB583, PUB334, PUB535_GONE],
    ),
    Election(
        id="E003", name="Business use of home deduction",
        what_it_does="Allows a portion of home expenses to be attributed to a space used regularly and "
                     "exclusively as the principal place of business.",
        eligibility=["Regular and exclusive business use of the space",
                     "The space is the principal place of business"],
        lost_if_missed="Contemporaneous records of the space and its use are far harder to assemble "
                       "after the fact than to keep from the start.",
        professional_question="Does my workspace meet the regular-and-exclusive test, and which "
                              "calculation method fits my situation?",
        sources=[PUB587],
    ),
    Election(
        id="E004", name="Solo 401(k) or SEP plan",
        what_it_does="Creates a retirement plan for an owner-only business, with contribution room well "
                     "above an individual retirement account.",
        eligibility=["Self-employment income", "No employees other than a spouse"],
        deadline=Deadline(
            rule="Deductible contributions for a tax year may be made up to the due date "
                 "of the return, plus extensions, for that year. Establishment deadlines "
                 "differ by plan type and must be confirmed per plan.",
            hard=True, sources=[PUB560_DUE]),
        admin_cost_note="Some plan types require an annual filing once assets pass a threshold.",
        lost_if_missed="A plan not established within its window cannot be applied retroactively to that "
                       "tax year.",
        professional_question="Which plan type fits my income, and what is the establishment deadline "
                              "for the current tax year?",
        sources=[PUB560_DUE],
    ),
]

plan = Plan(profile=profile, tasks=tasks, decisions=decisions, elections=elections)

# A deadline the rules can compute is computed here, so the kit ships dates
# rather than nulls. Anything waiting on an unknown stays unresolved and says so.
def _with_resolved(obj):
    dl = obj.deadline
    if dl is None or dl.resolved is not None:
        return obj
    computed = resolve(dl, profile)
    if computed is None:
        return obj
    return obj.model_copy(update={"deadline": dl.model_copy(update={"resolved": computed})})


plan = plan.model_copy(update={
    "tasks": [_with_resolved(t) for t in plan.tasks],
    "elections": [_with_resolved(e) for e in plan.elections],
})
out = pathlib.Path(__file__).parent / "plan.json"
out.write_text(plan.model_dump_json(indent=2))
print(f"wrote {out}")
print(f"  {len(tasks)} tasks, {len(decisions)} briefs, {len(elections)} elections")
print(f"  official fees ${plan.total_official_fees:,.2f} | avoided service cost ${plan.total_savings:,.2f}")
dated = [(p, c.resolved) for p, c in plan.iter_claims() if getattr(c, "resolved", None)]
print(f"  calendar: {len(dated)} resolved deadline(s) -> " +
      ", ".join(f"{p} {d}" for p, d in dated))
