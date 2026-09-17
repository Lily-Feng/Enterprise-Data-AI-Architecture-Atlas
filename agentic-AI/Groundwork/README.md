---
title: Groundwork
description: An agent that hands a first-time founder a runnable starter kit — ordered filings, cited fees, every tax election that exists for them, and a calendar of the deadlines that cannot be fixed in April.
tags: [agentic-ai, rag, evaluation, governance, structured-output]
---

# Groundwork

A first-time founder faces an unordered pile of decisions with dependencies they
cannot see. Groundwork turns that pile into a repository they can clone and run.

It **routes, cites, and computes. It never advises and it never files.** That is
not a disclaimer — it is enforced in [`groundwork/schemas.py`](groundwork/schemas.py)
and [`groundwork/validate.py`](groundwork/validate.py), and a model cannot talk
its way past either.

## The thesis

> **"LLC or S-corp?" has no answer as posed.** An LLC is a state legal entity.
> An S-corp is a federal tax election — Form 2553 — made *on top of* an LLC or a
> corporation. Two decisions, two agencies, two deadlines, wearing one coat.

A product whose first job is to correct the question is worth more than one that
answers it. The same applies to cost and to tax:

- **Minimum cost** is mostly subtraction. The IRS issues an EIN at no charge.
  A solo founder in their home state can usually be their own registered agent.
  Delaware generally means paying two states for one business.
- **Maximum tax benefit** is inventory and timing, not optimization. Founders
  rarely lose money by choosing wrong; they lose it by never hearing the option
  existed until the window closed.

## What is built

| Piece | State |
|---|---|
| [`groundwork/schemas.py`](groundwork/schemas.py) | Typed kit objects. A fee, form number, or deadline cannot be constructed without a tier-1 `.gov` source. |
| [`groundwork/validate.py`](groundwork/validate.py) | The gate. Draft and strict modes, dependency sort, jurisdiction scoping, advisory-language screening. |
| [`groundwork/verify_sources.py`](groundwork/verify_sources.py) | Fetches every citation, stamps it, fingerprints it — and later reports which pages have changed. |
| [`groundwork/corpus.py`](groundwork/corpus.py) | Refreshable retrieval. Fetches on a per-source TTL, chunks on block boundaries, and reports drift at the level of the individual line. |
| [`corpus/manifest.json`](corpus/manifest.json) | What to fetch and how often. 11 sources, 845 chunks. |
| [`fixtures/golden/tx-solo-consultant/`](fixtures/golden/tx-solo-consultant/) | Hand-authored target kit. 11 sources, all live-verified. Clears strict. |
| [`groundwork/errors.py`](groundwork/errors.py) | Structured tool failures — `category`, `retryable`, `retry_after_ms`. A 403 is permanent; a 503 is not. |
| [`groundwork/repair.py`](groundwork/repair.py) | Gate findings → a scoped repair turn. Only failing objects are regenerated; the loop is bounded and escalates. |
| [`groundwork/audit.py`](groundwork/audit.py) | Append-only run record. Every gate result, repair round, escalation and corpus change, stamped with the corpus state it saw. |
| [`evals/`](evals/) | 35 cases across the gate, the repair loop, and the audit trail. |
| Interview, plan generator, kit compiler | Not yet — see [SPEC.md](SPEC.md). |

## The corpus refreshes

Retrieval reads what the agencies publish today, not a snapshot someone committed
once. Nothing derived is in git; it all rebuilds from the manifest.

The unit of change is the **chunk**, not the page. Pages churn constantly for
reasons nobody cares about — a rotated banner, a new footer link. What matters is
whether the specific line a kit rests on still says what it said. So a chunk's
identity is derived from the *opening* of its text, which survives its own edit:

```
Certificate of formation for a Texas entity … (Forms 201, 203, 205, 206) $300
└──────────────── key: this holds ─────────────────┘        └ hash: this moves ┘
```

When Texas raises that fee, refresh reports `CHANGED` against that exact line
with its before and after — not "the page is different somehow":

```
CHANGED - anything resting on these needs re-reading:
  [tx-sos-fees] … (Forms 201, 203, 205, 206) $300
    was:        … (Forms 201, 203, 205, 206) $325
```

`impact` closes the loop the other way: given an already-generated kit, it checks
every quoted citation against the live corpus and names the ones that lost their
supporting text.

## Tools

### What you can run today

```bash
# Corpus -- refreshable retrieval
python3 -m groundwork.corpus refresh                     # fetch what is past its TTL
python3 -m groundwork.corpus refresh --force             # fetch everything
python3 -m groundwork.corpus refresh --only tx-sos-fees  # one source, scoped diff
python3 -m groundwork.corpus search "<query>" [--jurisdiction TX]
python3 -m groundwork.corpus impact <plan.json>          # citations that lost support

# Kit lifecycle
python3 fixtures/golden/tx-solo-consultant/build.py      # rebuild the golden plan
python3 -m groundwork.verify_sources <plan.json> [--write]
python3 -m groundwork.validate <plan.json> [draft|strict]

# Audit trail
python3 -m groundwork.audit list                         # every run, newest first
python3 -m groundwork.audit show <run_id>                # one run, event by event
python3 -m groundwork.audit sources <plan.json> [-o SOURCES.md]

# Tests
python3 -m evals.test_gate                               # 9 -- what the gate must refuse
python3 -m evals.test_repair                             # 12 -- scoping and termination
python3 -m evals.test_audit                              # 14 -- the record survives
```

`errors.py` and `repair.py` are library-only. They are called by the loop that
Phase 3 builds.

### What the agent will have

The ceiling is **four to five tools per agent**, past which tool-selection
accuracy drops. Groundwork has two agents, so each gets its own narrow set.

**Research subagent** — forked per task, isolated context slice:

| Tool | Purpose |
|---|---|
| `search_corpus` | `corpus.search`, jurisdiction pre-filtered |
| `fetch_official_page` | `corpus.fetch`, returns a `ToolError` on failure |
| `get_profile` | The `FounderProfile` block, re-anchored each turn |
| `emit_task` | Forced `tool_choice`; `Task` as the `input_schema` |

**Coordinator:**

| Tool | Purpose |
|---|---|
| `run_research` | Dispatch one subagent for one task |
| `validate_plan` | Wrap the gate, return findings |
| `emit_plan` | `Plan` as the `input_schema` |

Note what is absent: nothing files, pays, emails, or writes outside the kit
directory. Those capabilities are not gated and not logged — they do not exist.
Least privilege means removal, not observation.

## The trail

Provenance says what a claim rests on. An audit trail says what the system did.
Groundwork keeps both, because the question that gets asked months later is not
"where did $300 come from" but "what did the system see on the day it told me
$300, and has anything moved since".

Every run appends to `runs/<id>.jsonl` and is stamped with a fingerprint of the
corpus as it stood:

```
repair_round  {"round": 1, "passed": false, "resent": ["D001", "T001"]}
repair_round  {"round": 2, "passed": false, "resent": ["D001", "T001"]}
escalation    {"rounds": 3, "objects": ["D001", "T001"], "unresolved": [...]}
```

Writes are flushed per event, so a run that crashes still leaves everything it
had done — which is when the record is worth most. Nothing is ever rewritten: a
log that can be edited afterwards to match the outcome is not evidence.

`audit sources` compiles the founder-facing half — a `SOURCES.md` listing every
citation by tier with its retrieval date, the quoted line behind each fee, the
corpus digest the kit was built against, and the command to re-check it all.
Unverified sources are printed as `NOT VERIFIED` rather than quietly omitted.

## Certification coverage

Groundwork exists partly to work the [Claude Certified Architect · Professional
study guide](../ClaudeCertifiedArchitectPro/) as running code rather than as
notes. Coverage by exam domain:

| # | Domain | Weight | Where Groundwork demonstrates it | State |
|---|---|---:|---|---|
| 1 | Solution Design & Architecture | 17% | Workflow for the interview and plan; agentic only for per-task research. Ownership split: SQLite/Python compute, Claude routes and explains | planned |
| 2 | Models, Prompting & Context | 13% | Stable-prefix caching, progressive discovery over 845 chunks rather than a monolithic context, `FounderProfile` as the durable block | planned |
| 3 | **Integration** | **19%** | Tier-weighted hybrid retrieval, jurisdiction filter before search, ≤4 tools per agent, `ToolError` contract, MCP over stdio | **partial** |
| 4 | Evaluation & Optimization | 16% | 35 tests; citation validity, dependency order, and "does the kit run" are all code-gradable; run logs make repair rounds and escalation rate measurable | **partial** |
| 5 | Governance, Safety & Risk | 14% | The citation gate, advisory-language screen, fail-closed scope check, escalation with a structured hand-off, append-only audit trail | **done** |
| 6 | Stakeholder & Lifecycle | 14% | Structured discovery is the product; `DecisionBrief` is an ADR; the kit is the handoff artifact | **partial** |
| 7 | Developer Productivity | 7% | Scoped `CLAUDE.md`, a read-only slash command, headless eval in CI | planned |

### Orchestration patterns

| Pattern | State |
|---|---|
| Partial failure retries only the failed unit | **done** — [`repair.py`](groundwork/repair.py) |
| Validation failure fed back and retried, bounded | **done** — `RepairTask.as_prompt()`, `MAX_ROUNDS` |
| Escalate on low confidence, ambiguity, or exhausted retries | **done** — three triggers, see [`schemas.py`](groundwork/schemas.py) and [`repair.py`](groundwork/repair.py) |
| Categorical rules, never vague adjectives | **done** — every gate rule is mechanically checkable |
| Structured tool errors with `retryable` and `retry_after_ms` | **done** — [`errors.py`](groundwork/errors.py) |
| Observability: durable record of what ran, what it saw, what it decided | **done** — [`audit.py`](groundwork/audit.py) |
| Sequential and adaptive decomposition | partial — the dependency sort is real; agent-side sequencing is Phase 3 |
| Structured output via `input_schema` + forced `tool_choice` | partial — the schema exists and is enforced; nothing calls an API yet |
| Agent loop on `stop_reason`; coordinator spawns subagents | Phase 3 |
| Tool descriptions as API docs; MCP over stdio | Phase 3–4 |
| Case blocks re-anchored per turn; prompt caching | Phase 3 |
| Scoped `CLAUDE.md`; tool-restricted slash command | Phase 4 |

Full item-by-item detail lives in [SPEC.md §7](SPEC.md).

**Honest summary: what is covered runs without a model. What is missing needs
the agent.** That follows from building the gate before the generator, which is
the order the study guide argues for — evals first, so every later change has
something to be measured against.

## Requirements

Python 3.11+ and `pydantic>=2`. Nothing else — no API key is needed for anything
currently in the repo.

## Scope

Covered: solo or small **services / software** businesses in **TX, CA, DE**.

Out of scope, and routed to a professional rather than answered: legal advice,
tax advice, filing on anyone's behalf, handling payment, non-US, regulated
industries, employees and payroll, fundraising and cap tables.

Three states honestly maintained beats fifty that go stale in a month.

## A note on the numbers

Every dollar figure, form number, and deadline in a generated kit comes from a
cited page that something actually fetched — never from a model's memory. The
strict gate refuses to ship a kit containing a citation nobody has read.

This bit already earned itself during construction: the first draft priced two
filing services from SBA pages that say nothing about vendor pricing. Real-looking
citation, invented number — the exact failure this project exists to prevent.
Both were removed rather than rounded.
