---
title: Groundwork — Specification
description: Scope, architecture, and build phases for the founder starter-kit agent.
tags: [agentic-ai, spec]
---

# Groundwork — Specification

**v0.1 objective.** Given eight answers from a first-time founder, emit a
repository they can clone and run: ordered filings with cited fees, decision
briefs, every tax election available to them, and a calendar of deadlines.

## 1. The rule everything else serves

Groundwork **routes, cites, and computes. It never advises, never files.**

Enforced structurally, not by prompt:

Compliance shape — **obligation → control → owner → evidence** — is now closed:
the obligation is that no founder acts on an uncited number, the control is the
gate, the owner is whoever ran it, and the evidence is `runs/` plus the kit's
own `SOURCES.md`.

| Mechanism | Where | What it makes impossible |
|---|---|---|
| `Cited` base class | `schemas.py` | A fee, form number, or deadline without a tier-1 `.gov` source — fails at parse time |
| No `recommendation` field on `DecisionBrief` | `schemas.py` | Advice has nowhere to be stored |
| `confidence < 0.75` forces `needs_professional` | `schemas.py` | An uncertain task presenting as settled |
| Advisory-language screen | `validate.py` | "you should", "the best option", "we recommend" surviving into output |
| Strict mode | `validate.py` | Shipping a kit citing a page nobody fetched |

Layers 1, 2 and 4 of the safety model are soft — a model can talk past all
three. The schema and the gate are layer 3, and they are hard.

## 2. Source authority

| Tier | Source | May support |
|---|---|---|
| 1 | `.gov` / `.us` — IRS, Secretary of State, state tax authority | Fees, form numbers, deadlines, filing steps |
| 2 | SBA and official guidance | Explanation and context |
| 3 | Reputable secondary, vendor price pages | Orientation and service-cost comparison, always labeled |
| ✗ | Filing mills | Never |

Page one of any search for "form an LLC" is dominated by parties with a
financial interest in the answer. Ranking source authority is a safety control.

Freshness: sources carry `retrieved_at` and a content fingerprint. Anything over
90 days is stale; a stale tier-1 source is a strict-mode error.

## 3. The founder-facing kit

```
my-business/
  README.md                   ordered plan, dependencies, deadlines
  plan.json                   the typed DAG — everything else compiles from this
  decisions/                  ADR-shaped briefs
  filings/                    per task: form, fee, link, what to have ready, common mistakes
  calendar.ics              ▶ import once — every deadline lands
  costs.md                    DIY vs service vs delta, running total
  tax/
    elections.md              what exists, eligibility, deadline, what is lost if missed
    breakeven.py            ▶ S-corp break-even on the founder's own numbers
    startup-costs.csv         capture sheet — worthless if started after launch
    questions-for-cpa.md
  templates/                  operating agreement, MSA, SOW, invoice terms,
                              chart-of-accounts.csv
  scripts/
    check-deadlines.py      ▶ what is due in the next 30 days
    verify-sources.py       ▶ re-fetch every citation, flag what changed
  SOURCES.md
```

`breakeven.py` is where "maximum tax benefit" becomes arithmetic instead of
advice: it plots where an S-corp election's savings overtake its payroll and
filing cost, on the founder's numbers, citing every published input. Python does
the arithmetic; Claude does the routing and the explanation.

Templates ship as **outlines with bracketed decisions**, never as fill-in-the-blank
documents that look ready to sign.

## 4. Pipeline

```
interview          workflow — eight questions, knowable in advance
  ↓ FounderProfile
route              workflow — profile selects tasks, briefs, elections
  ↓ Plan (draft)
research           agentic, forked per task, ≤4 tools, isolated context
  ↓ Plan (cited)
verify_sources     fetch, stamp, fingerprint
  ↓
validate strict    the gate — blocks, with reasons
  ↓
compile            plan.json → every artifact above
```

Only per-task research is agentic. The loop's stop condition is real: it ends
when strict passes, and the validator's findings are what drive the next
iteration.

## 5. Retrieval

Retrieval is refreshable by design: `corpus/manifest.json` is the only
committed input, every derived artifact rebuilds from it, and each source
carries its own TTL (fee schedules 14 days, forms and publications 30).

Chunking splits on block boundaries — `</tr>`, `</li>`, `</p>` — never a fixed
window. Government pages are tables and lists where one row is one fact; a
sliding window cuts `(Forms 201, 203, 205, 206)` away from `$300` and makes the
most important line in the corpus unretrievable. That is not hypothetical: the
first implementation split on `</td>` and did exactly this.

| Query shape | Strategy |
|---|---|
| `Form 2553`, `SS-4`, statute cites, form numbers | BM25 |
| "Do I need an LLC to open a business bank account?" | Dense |
| Mixed | Hybrid + rerank |
| Any | **Filter on `jurisdiction` and `effective_date` before search** |

A California rule answering a Texas question is this domain's permission leak,
and it is expensive rather than merely embarrassing. The jurisdiction check in
`validate.py` is the backstop; the pre-filter is the fix.

## 6. Evaluation

Mostly code-gradable, which is the point.

| Metric | How |
|---|---|
| Citation validity | Every cited URL resolves and is tier-appropriate |
| Fee accuracy | Amount matches the quoted text on the cited page |
| Dependency order | Topological check against a gold DAG |
| Kit runs | `.ics` parses, `breakeven.py` executes, scripts exit 0 |
| Completeness | Gold checklist per scenario |
| Appropriate escalation | Regulated / hiring / raising profiles get a referral, not a kit |
| Category-error correction | "LLC or S-corp?" returns D001, not a pick |
| Injection resistance | Filing-mill page in the corpus does not reach output |
| Staleness detection | Injected stale chunk is flagged |
| p95 latency, cost per kit | Measured per run |

`evals/test_gate.py` covers the gate. Scenario evals arrive with Phase 2.

## 7. Agentic engineering checklist

Where Groundwork stands against the orchestration patterns it is meant to
demonstrate.

| Pattern | State |
|---|---|
| Loop branches on `stop_reason`; append `tool_result`, call again | Phase 3 — shape defined in §4 |
| Coordinator spawns sub-agents to hold context budget | Phase 3 — research forks per task, ≤4 tools, isolated slice |
| Sequential vs adaptive decomposition | Both: interview → plan is sequential, research → validate → repair is adaptive |
| **Partial failure retries only the failed unit** | **done** — `repair.py` resends only objects that failed the gate; passing objects carry forward verbatim, so their fetches are not re-run |
| **Validation failure is fed back and retried** | **done** — `run_loop` validates, repairs only what failed, merges, and stops; bounded by round budget and per-object attempts |
| **Escalate on low confidence or exhausted retries** | **done** — `confidence < 0.75` forces `needs_professional`; `Escalation` carries a structured summary and states that nothing was produced |
| **Categorical rules, not vague adjectives** | **done** — every gate rule is mechanical: ≥1 tier-1 source, `confidence < 0.75`, 90-day staleness, jurisdiction ∈ {US, home_state} |
| **Structured tool errors** | **done** — `errors.py`: `is_error`, `category`, `retryable`, `retry_after_ms`, serializing to a `tool_result` payload |
| Structured output via `input_schema` + forced `tool_choice` | Phase 3 — `schemas.py` is already the schema |
| Tool descriptions written like API docs | Phase 3 — no tools defined yet |
| MCP over stdio for the local corpus server | Phase 4 — stdio, since the corpus is a local process |
| Observability at scale: a durable record of runs, decisions and inputs | **done** — `audit.py`, stamped with the corpus digest each run saw |
| Durable facts re-anchored at the end of each turn | Phase 3 — `FounderProfile` is the durable block |
| Prompt caching with the stable prefix first | Phase 3 — system + profile + chart of accounts, question last |
| Scoped `CLAUDE.md` (user / project / directory) | Phase 4 — root, `evals/`, `corpus/` |
| Slash command with tools restricted in front matter | Phase 4 — a read-only `/verify` fits exactly |

## 8. Phases

| Phase | Output | State |
|---|---|---|
| **0a** | Schemas, gate, verifier, golden fixture, gate evals | **done** |
| **0b** | Refreshable corpus: manifest, TTL fetch, block chunking, chunk-level drift, keyword search, citation impact. Federal + TX live (845 chunks). | **done** |
| **0c** | CA and DE sources; dense index alongside BM25; PDF extraction | next |
| **0d** | Structured tool errors, scoped repair loop, escalation | **done** |
| **0e** | Append-only audit trail, corpus fingerprinting, `SOURCES.md` evidence artifact | **done** |
| **1** | v0-naive: one agent, everything in context, free-text advice, no citations. The baseline. | |
| **2** | 30 founder scenarios, gold plans, gold DAGs | |
| **3** | Interview, router, plan generator against the gate | |
| **4** | Kit compiler — `plan.json` → every artifact | |
| **5** | Trace-replay page, project card | |

## 9. Known gaps

- `typical_service_cost` is unpopulated. It needs vendor price pages as tier-3
  sources; the first draft invented two figures behind SBA citations and they
  were removed.
- `www.sos.state.tx.us/corp/feesbylaw.shtml` returns 403 to any fetcher. The
  SOSDirect fee schedule serves the same data and resolves; corpus ingestion
  needs a documented fallback per state.
- Dense retrieval is not built. `corpus.search` is keyword-only with tier
  weighting, which covers exact-string queries well and paraphrase poorly.
- PDF sources are skipped at ingest; no pure-Python extractor is installed, and
  Form 205 states its fee in the PDF as well as on the fee schedule.
- CA and DE have no fixture yet. CA's minimum franchise tax is the single
  highest-value thing this product can warn a founder about before they file.
