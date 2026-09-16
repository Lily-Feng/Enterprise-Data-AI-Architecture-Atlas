# Course 1 — Claude Platform & Solution Design

> **Covers exam Domains 1 (17%) and 2 (13%) — 30% of the exam, ~19 items.**
> Course length: 238 minutes (the longest of the five).
> Original notes: [notes-original.md](notes-original.md)

**The question this course answers:** given an ambiguous business problem, what should Claude own, what shape should that work take, which architecture fits, and how do you defend the choice against a credible alternative?

---

## 1. The four platform properties every design must absorb

These are not caveats. They are load-bearing constraints that dictate architecture. Every one of them has a required architectural response.

| Property | What it means | Required architectural response |
|---|---|---|
| **Non-determinism** | The same input can yield different outputs across runs. | You cannot certify behavior from one successful observation. Evaluation frameworks are mandatory, not optional. |
| **Context as a finite resource** | The context window is a hard boundary with a token budget. What you include, what you omit, and **the order** all affect capability and cost. | Deliberate context strategy: retrieval, progressive discovery, caching, compaction. |
| **Confidence is not validity** | Claude states a wrong answer in exactly the same fluent, authoritative tone as a right one. | Verification and human-in-the-loop are core requirements placed at design time, not bolted on after an incident. |
| **Knowledge and capability boundaries** | Reliable on common, well-represented topics; unreliable on rare, private, or rapidly changing information. | For unreliable topics, bind to external sources of truth: web search, RAG, tools, MCP. |

> **Exam tell.** Items that describe a system "working well in testing" and then failing in production are usually testing non-determinism or confidence-is-not-validity. The right answer adds evaluation or verification, not a bigger model.

## 2. The ownership split — the first design decision

Before any architecture question, decide who owns what. Getting this wrong makes every downstream decision wrong.

| Owner | What belongs here |
|---|---|
| **What Claude does** | Work that benefits from language understanding, summarization, planning, drafting, or tool-mediated action. |
| **What existing systems do** | Anything the client has already paid to make reliable: the order-status service, the policy engine, the rules table, the database of record. |
| **What humans do** | Judgment calls, exception paths, approvals — the moments where being right matters more than being fast. |

**The failure mode this prevents:** re-implementing a deterministic business rule as a prompt. If a rules engine already computes eligibility correctly and auditably, Claude should *call* it, not *reason about* it. A deterministic system that already works is a feature of your architecture, not a legacy problem to replace.

**Corollary for cost and latency:** every piece of work you hand to an existing system is work you do not pay tokens for and do not have to evaluate.

## 3. Choosing the architecture pattern

Reach for the simplest tier that meets the need. Escalate only when the requirement forces it.

| Tier | Pattern | Use when | Cost of getting it wrong |
|---|---|---|---|
| 1 | **Single LLM call** | Classification, extraction, summarization, Q&A — one request, one response | Over-engineering: you built an agent for a classifier |
| 2 | **Augmented LLM** (retrieval / tools attached) | The model needs facts or capability it does not have, but you control the flow | Under-grounding: hallucination on private data |
| 3 | **Workflow** (code-controlled multi-step) | The steps are known in advance; you orchestrate; each step is verifiable | Rigidity where the path genuinely varies |
| 4 | **Agentic** (model-controlled loop) | The task is multi-step and cannot be fully specified in advance | Cost, latency, and unbounded failure modes |
| 5 | **Multi-agent** | Genuinely separable subtasks, each needing a different specialization or context | Coordination failure, silent gaps in synthesis |

### The four-question gate before you build an agent

Ask all four. A "no" to any one of them means drop back a tier.

1. **Complexity** — Is the task multi-step and hard to fully specify in advance? ("Turn this design doc into a PR" — yes. "Extract the title from this PDF" — no.)
2. **Value** — Does the outcome justify higher cost and latency?
3. **Viability** — Is Claude actually capable at this task type?
4. **Cost of error** — Can errors be caught and recovered from? (tests, review, rollback)

> **Exam tell.** "Agentic" sounds advanced and is frequently the distractor. When the steps are knowable in advance, a workflow is the correct, defensible answer — it is cheaper, faster, more testable, and each step is independently verifiable.

## 4. The agentic loop

Agency emerges from the **loop**, not from the prompt. The Böhm–Jacopini framing: any computable function needs sequence, conditional, and loop. Prompt chaining gives you the first two; only a loop lets the model act, inspect the result, correct, and iterate.

The loop is driven by `stop_reason`:

```
        ┌─────────────────┐
        │   User query    │
        └────────┬────────┘
                 ▼
       ┌───────────────────┐
  ┌───►│  Claude API call  │
  │    └─────────┬─────────┘
  │              ▼
  │        [stop_reason?]
  │         ├── "tool_use" ──► execute tool ──► append tool_result ──┐
  │         │                                                        │
  │         └── "end_turn" ──► [confidence / authorization gate]     │
  │                               ├── clears gate  ──► return        │
  │                               └── fails gate   ──► escalate      │
  └────────────────────────────────────────────────────────────────┘
```

**Two anti-patterns the exam reaches for:**

1. **Fire-and-forget** — treating the invocation as a single-turn call instead of branching on `stop_reason`. The agent terminates before running the required tool, or spins without capturing tool output.
2. **Full autonomy** — no human-in-the-loop fallback anywhere. The agent unilaterally resolves refunds, account changes, and sensitive edge cases.

The correct answer almost always **adds an explicit control check or an escalation gate**.

Other loop mechanics worth knowing: parallel tool calls arrive as multiple `tool_use` blocks in one assistant message — execute them concurrently and return **all** `tool_result` blocks in a **single** user message (splitting them teaches Claude to stop parallelizing). A failed tool returns `tool_result` with `is_error: true` — never drop it silently.

## 5. Multi-agent design

Two rules carry most of the weight.

### Specialize, don't overload
Past roughly **4–5 tools**, an agent's tool-selection accuracy degrades measurably. The fix is hub-and-spoke: narrow, dedicated subagents with minimal toolsets, coordinated by an orchestrator. Giving one generalist agent 15 tools looks capable and is the trap.

### Isolate subagent context
Pass each subagent **only the slice it needs**. A critic agent verifying a claim should receive the claim and the source text — not the coordinator's entire brainstorming trail. Leaking the full trace makes every subagent inherit the coordinator's assumptions, biases, and blind spots, which destroys the independence that made the critic worth having.

### The orchestration failure mode you must be able to diagnose

From the course material, a multi-agent research system returned a confident, fluent summary that was missing a whole section of work. Three things had gone wrong:

1. **No coverage check at synthesis.** The orchestrator synthesized over the results it *happened to receive*. There was no rule that the number of results must equal the number of units dispatched.
2. **A recoverable failure was never recovered.** A timed-out subagent is the recoverable case — but only if something retries it or flags the gap. The failure was silent because nothing was watching the boundary.
3. **Confident synthesis over incomplete work.** The output's fluency masked the gap.

> **The generalizable lesson:** a multi-agent system fails most dangerously when the summary *looks complete and is not*. Every fan-out needs a fan-in check: dispatched count must equal returned count, and a missing unit must either retry or surface.

## 6. Decomposition

When a problem is too big to hand to one call, decompose along one of these seams — and prefer the seam that makes each piece independently verifiable:

| Seam | Split by | Good when |
|---|---|---|
| **Sequential** | Pipeline stages | Each stage's output is the next stage's input, and each is checkable |
| **Parallel / fan-out** | Independent units of work | Units do not depend on each other; requires a fan-in coverage check |
| **Specialization** | Type of expertise needed | Different subtasks want different prompts, tools, or models |
| **Confidence** | Easy vs. hard cases | Route the routine bulk cheaply, escalate the hard tail |

The test of a good decomposition is not elegance — it is **whether you can write an eval for each piece**.

## 7. Business value pillars

You must be able to name which pillar a solution serves, because it determines what you measure and how you justify spend.

| Pillar | Meaning | Measured as |
|---|---|---|
| **Efficiency** | Doing existing work faster | Cycle time, throughput per person |
| **Cost** | Doing existing work cheaper | Cost per transaction, headcount avoided |
| **Productivity** | More output from the same people | Volume per FTE, backlog burn-down |
| **Transformation** | Making possible something that **was not possible before** | New capability, new product, new market |
| **Performance / SLAs** | Meeting a service level you could not meet before | p95 latency, resolution time, availability |

> **Exam tell — this one is explicitly flagged in the source notes.** *Transformation* means enabling something that wasn't possible before. *Efficiency* and *cost* are about doing existing work faster or cheaper. Items will test whether you can distinguish "we now answer tickets 40% faster" (efficiency) from "we can now offer 24/7 multilingual support we never could staff" (transformation). Expect the exam to use these exact words.

## 8. Prompting and context engineering (Domain 2)

### Technique selection

| Technique | Use when | Cost |
|---|---|---|
| **Zero-shot** | The task is common and well-described by instructions | Cheapest |
| **Few-shot** | Output *format* or *edge-case handling* is hard to describe but easy to demonstrate | Adds tokens to every request — cache the examples |
| **Chain-of-thought / thinking** | The task requires multi-step reasoning before the answer | Adds output tokens; use adaptive thinking + `effort`, not a fixed budget |
| **Structured output / strict tools** | You need a machine-parseable result | Near-free; always beats regex parsing |

### System prompt design

A system prompt carries four things: **role**, **task boundaries**, **output contract**, and **escalation rules** (what to do when the model can't comply — including permission to say "I don't know"). The last one is the one people skip and the one that prevents confident fabrication.

### Prompt reuse — the three mechanisms

| Mechanism | Unit of reuse | Governance |
|---|---|---|
| **Prompt caching** | A stable prefix within one application | Runtime optimization; verify with `cache_read_input_tokens` |
| **Modular prompts / templates** | Composable blocks across an application | Your own version control |
| **Skills** | A packaged capability across teams or products | Four distribution mechanisms with different rollback stories — see [Course 5](../5-team-enablement/README.md) |

Caching details, ordering rules, and the silent-invalidator list are in [platform-reference.md](../platform-reference.md#2-prompt-caching--the-highest-leverage-cost-control).

## 9. Traps and their tells

| The trap | Why it's tempting | The defensible answer |
|---|---|---|
| Reach for agentic because it sounds sophisticated | Agents are the interesting part | If steps are knowable in advance, use a workflow |
| One agent with every tool | Looks capable and simple to build | Specialize; ≤4–5 tools per agent |
| Share the full context with every subagent | Feels like "giving it everything it needs" | Pass the minimal slice; isolation is the point |
| Replace a working deterministic system | "AI-first" | Claude calls it; it stays the source of truth |
| Fire-and-forget the API call | The happy path works in the demo | Branch on `stop_reason`; loop until `end_turn` |
| Full autonomy, no escalation | Removes a "bottleneck" | Gate high-impact and low-confidence paths to a human |
| Truncate context to save cost | Direct and obvious | Reorder + cache; truncation loses required policy |
| Prove it works by running it once | It passed! | Non-determinism — you need an eval set |

## 10. Self-check

You can move on when you can answer these without notes:

1. Name the four platform properties and the architectural response each one demands.
2. Given a business problem, split the work three ways (Claude / existing systems / humans) and defend the split.
3. Walk the five architecture tiers and say what forces an escalation from each to the next.
4. State the four-question gate before building an agent.
5. Draw the `stop_reason` loop and name the two anti-patterns it prevents.
6. Explain why a multi-agent fan-out needs a fan-in coverage check, using the silent-gap failure as the example.
7. Distinguish transformation from efficiency using the course's exact wording.
8. Explain why caching is a design decision about *ordering*, not a flag you turn on.
