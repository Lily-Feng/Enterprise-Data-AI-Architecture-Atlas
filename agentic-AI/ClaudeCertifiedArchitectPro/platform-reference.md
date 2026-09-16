# Platform Reference — the Claude facts an Architect is expected to know

> **Scope note.** The exam is architecture-judgment, not API-syntax recall. But several domains (2, 3, 4) assume you know what the platform actually offers, what it costs, and which surface to pick. This page is that layer. Platform facts current as of **September 2026** — verify model IDs and pricing against the [Models API](https://docs.claude.com/en/api/models-list) and the [pricing page](https://claude.com/pricing) before quoting them to a client, since these move faster than any certification.

---

## 1. Models and the trade-off you are actually making

| Model | Model ID | Context | Input $/1M | Output $/1M |
|---|---|---:|---:|---:|
| Claude Fable 5.1 | `claude-fable-5-1` | 1M | $10.00 | $50.00 |
| Claude Fable 5 | `claude-fable-5` | 1M | $10.00 | $50.00 |
| Claude Opus 5 | `claude-opus-5` | 1M | $5.00 | $25.00 |
| Claude Opus 4.8 | `claude-opus-4-8` | 1M | $5.00 | $25.00 |
| Claude Opus 4.7 | `claude-opus-4-7` | 1M | $5.00 | $25.00 |
| Claude Opus 4.6 | `claude-opus-4-6` | 1M | $5.00 | $25.00 |
| Claude Sonnet 5 | `claude-sonnet-5` | 1M | $2.00 | $10.00 |
| Claude Sonnet 4.6 | `claude-sonnet-4-6` | 1M | $3.00 | $15.00 |
| Claude Haiku 4.5 | `claude-haiku-4-5` | 200K | $1.00 | $5.00 |

Prices are Anthropic first-party API rates. Amazon Bedrock and Google Vertex AI are partner-operated with **separate pricing**; Microsoft Foundry bills at standard API rates through the Microsoft Marketplace.

### How to defend a model choice

The architect's answer is never "the biggest one" or "the cheapest one." It is a three-way argument:

1. **Does the task need the capability?** Long-horizon agentic work, hard reasoning, and multi-file code changes repay a frontier model. Classification, routing, extraction, and short summarization usually do not.
2. **What is the latency budget?** Per-request p95 is a design constraint handed to you, not something you discover after launch.
3. **What does a wrong answer cost?** High cost-of-error justifies a more capable model *and* a verification step; low cost-of-error with volume justifies a smaller one.

**The multi-model cascade trap.** Routing cheap work to a small model and hard work to a large one is the obvious optimization and is often wrong. Prompt caches are **model-scoped**, so a cascade forfeits cache reuse across its models. Measure the simpler alternative first: the most capable model at *lower effort* frequently matches a previous-generation model at high effort, and one model means one cache namespace.

**Judge cost per completed task, not cost per request.** A cheaper request that needs three more turns or a retry to finish the job is not cheaper.

### Effort — the first quality-trading lever

`output_config: {effort: "low"|"medium"|"high"|"xhigh"|"max"}`. Default is `high`. Effort trades thoroughness against token spend *within one model*, so it is the lever to reach for before changing models.

- `low` — subagents, simple tasks, high-volume or latency-sensitive routes
- `high` — the usual sweet spot for quality vs. token efficiency
- `xhigh` — best setting for most coding and agentic work on current models
- `max` — only when correctness matters more than cost, and only when measurement shows headroom at the level below

Which workloads repay higher effort is a property of the workload. Coding and long-horizon agentic work respond strongly; chat, classification, and high-volume routes often do not. **Tune per route, not globally, and measure on real requests before raising a default.**

### Extended thinking

Current models use **adaptive thinking** (`thinking: {type: "adaptive"}`) — Claude decides when and how much to think. The older fixed `budget_tokens` concept is deprecated and is rejected outright on current frontier models. If a question or a legacy codebase says "set a thinking budget," the current answer is adaptive thinking plus an `effort` level.

Thinking happens and is billed identically regardless of whether you display it. `display: "summarized"` returns a readable summary; the default on current models is `"omitted"`, which streams empty thinking blocks. If you show reasoning to users, set `summarized` explicitly or the UI looks like a long pause.

---

## 2. Prompt caching — the highest-leverage cost control

**Caching is prefix-match.** Render order is `tools` → `system` → `messages`. Any byte change anywhere in the prefix invalidates everything after it.

**The design rule:** stable content first, volatile content last.

```
[ tools        ]  deterministic, sorted        ┐
[ system       ]  frozen instructions          ├─ cacheable prefix
[ policy docs  ]  static reference material    ┘
──────────────── cache_control breakpoint ────────────────
[ messages     ]  the varying user turn        ← never cached
```

Maximum **4 breakpoints** per request. Minimum cacheable prefix is model-dependent (512–4096 tokens) — shorter prefixes silently do not cache at all.

**Verify, don't assume.** Check `usage.cache_read_input_tokens`. If it is zero across repeated requests, a silent invalidator is at work. The usual suspects:

| Silent invalidator | Fix |
|---|---|
| `datetime.now()` or a request ID in the system prompt | Move it after the last breakpoint |
| Unsorted JSON serialization of tools | Serialize deterministically |
| Tool list that varies per request | Freeze the tool set, or defer-load via tool search |
| A mid-conversation change to top-level `system` | Use a mid-conversation system message in `messages[]` instead |
| Switching models between requests | Caches are model-scoped — expect a cold cache |

**Mid-conversation operator instructions.** On current Opus/Fable models you can append `{"role": "system", ...}` into `messages[]` rather than editing top-level `system`. This preserves the cached prefix *and* is the prompt-injection-safe operator channel — a security property, not just a cost one.

---

## 3. Batch API

`POST /v1/messages/batches` — asynchronous, **50% cost reduction**, up to a 24-hour turnaround window.

Use it for anything genuinely not latency-sensitive: nightly audits, bulk document generation, backfilling classifications, regenerating an eval corpus. Running these synchronously at full price while a pipeline worker blocks is a recurring exam anti-pattern.

Results arrive in **any order** — key by `custom_id`, never by position. Each result carries a status of `succeeded` / `errored` / `canceled` / `expired`.

---

## 4. Tools, MCP, and the integration mechanism decision

### Server-side tools (run on Anthropic's infrastructure)

| Tool | What it gives you |
|---|---|
| Web search | Live search with `allowed_domains` / `blocked_domains` filtering |
| Web fetch | Fetches URLs **already present in the conversation** |
| Code execution | Sandboxed code run; how Agent Skills produce `.pptx` / `.xlsx` / charts |
| Tool search (regex / BM25) | Lets you mark tools `defer_loading: true` and have Claude search for them |

**Tool search is the platform answer to capability bloat** (Domain 3). Instead of putting 40 tool definitions in every request's prefix, defer-load them and let Claude retrieve the ones it needs. Constraint: the search tool itself must not be deferred, and at least one tool must stay non-deferred.

### Choosing an integration mechanism

| Mechanism | Choose when | Watch out for |
|---|---|---|
| **Direct API (Messages)** | You own the loop and the tools; single-tenant integration; you need maximum control | You build and maintain the agent loop, retries, and context management |
| **Tool Runner (SDK)** | You want a custom-tool agent without hand-writing the loop; still want per-turn hooks for approval gates, logging, retries | Harness only — you still host and deploy |
| **MCP (Model Context Protocol)** | A capability should be reusable across multiple clients and teams; you want a standard server boundary instead of N bespoke integrations | Each server is an authorization surface; an MCP server inherits whatever credentials you hand it |
| **Managed Agents** | You want Anthropic to run the loop *and* host a per-session sandbox; persisted, versioned agent configs; scheduled runs | Beta; not available on Bedrock / Vertex / Foundry |
| **Claude Code / CLI (headless)** | The work is repo-shaped: code review, PR summaries, migrations, CI jobs | Never run interactive mode in CI — it blocks on stdin forever |
| **Agent-to-agent** | Genuinely independent systems with separate ownership need to collaborate | Highest coordination cost; do not reach for it when one agent with two tools would do |

**MCP's architectural argument** is reuse and a governed boundary: one server, many clients, one place to audit what the capability can reach. Its architectural cost is that it is another authorization surface. On the exam, MCP is the right answer when the question stresses *reuse across teams/clients* or *a standard interface*; direct API is the right answer when the question stresses *one system, full control*.

### Headless Claude Code for CI

```bash
claude -p "Review this PR for security vulnerabilities" --output-format json
```

Non-interactive (`-p` / `--print`) plus structured output. Pair with the Batch API for anything that can wait.

---

## 5. Context engineering

### Progressive discovery vs. monolithic context

| | Monolithic | Progressive discovery |
|---|---|---|
| Approach | Load everything the agent might need up front | Load a small index; retrieve detail on demand |
| Cost | High and constant per request | Low baseline, pays only for what is used |
| Failure mode | Context saturation, lost-in-the-middle degradation | Extra round-trips; a bad index hides the right document |
| Best for | Small, stable, fully-needed corpora | Large or growing corpora, many tools, long sessions |

Progressive discovery is the default answer at enterprise scale. The exception is a small stable corpus where the whole thing fits comfortably and caches well — then monolithic is cheaper *and* simpler.

### Managing a long session

Three distinct mechanisms, often confused:

| Mechanism | What it does | When |
|---|---|---|
| **Context editing** | *Clears* old tool results or thinking blocks before the model sees them | Tool results are bulky and no longer needed |
| **Compaction** | *Summarizes* earlier context when approaching a threshold (default 150K tokens) | Long conversations that may exceed the window |
| **Memory / external store** | Persists facts outside the window entirely | Knowledge that must survive the session |

Clearing is not summarizing. If the earlier turns carry decisions the agent still needs, clearing them loses the decisions; compaction preserves them in condensed form.

### Forking noisy subtasks

Verbose work — scanning logs, reading 100 files, running a huge test suite — should execute in a **forked subagent or isolated subprocess** that returns only the synthesized finding. Dumping raw output into the main thread is the single most common way a productive session degrades.

---

## 6. Structured output

Two mechanisms, and the exam cares that you do not use regex:

1. **Structured outputs** — `output_config: {format: {...}}` constrains the response to a schema.
2. **Strict tool use** — `strict: true` on the tool definition (requires `additionalProperties: false` and `required`) guarantees `tool_use.input` validates exactly against your schema.

Then **validate programmatically anyway** (Pydantic, Zod, JSON Schema) and gate on the result. Schema enforcement at generation + validation at intake + a confidence gate is the full pattern. "Prompt for JSON and parse with a regex" is always the wrong answer.

---

## 7. Skills

A **Skill** is a packaged, reusable set of instructions and resources Claude loads when a task matches it. Architecturally it is the reuse unit above a prompt and below an agent: modular, versionable, and distributable.

Four distribution mechanisms with materially different governance — see [Course 5](5-team-enablement/README.md) for the full comparison table. The short version:

| Mechanism | Reach | Rollback story |
|---|---|---|
| Org-provisioned Skill | Whole organization | No version pinning; updates are manual re-upload |
| Plugin assigned to group/org | Targeted teams | Strongest: install preferences + version-controlled updates from a connected repo |
| Claude Code project Skill | One team's repos | Rolls back with the repository |
| API Skill | Machine-to-machine | Explicit version pinning |

---

## 8. Deployment surfaces and compliance posture

| Surface | Operated by | Notes |
|---|---|---|
| Claude API (first-party) | Anthropic | Full, same-day feature parity |
| Claude Platform on AWS | Anthropic-operated | Same-day API parity |
| Amazon Bedrock | AWS | Partner pricing; some features unavailable (e.g. Managed Agents) |
| Google Vertex AI | Google | Partner pricing; reduced server-tool availability |
| Microsoft Foundry | Microsoft | Standard API rates via Microsoft Marketplace |

**The compliance rule that shows up on the exam:** a certification is not a property of "the vendor," it is a property of a **specific service, in a specific region, at a specific authorization level**. For a FedRAMP requirement, you confirm that the exact deployment path — cloud platform, region, *and* service — holds the authorization level the agency's data requires. "Anthropic is compliant" is never the answer; "this deployment path is authorized at this level" is.

Same shape for HIPAA: what matters is that a **Business Associate Agreement covers the specific services and settings in use**, and that only the minimum necessary PHI is sent.

---

## 9. Quick numbers to have memorized

| Fact | Value |
|---|---|
| Batch API discount | 50% |
| Batch turnaround window | up to 24 hours |
| Cache breakpoints per request | max 4 |
| Minimum cacheable prefix | 512–4,096 tokens (model-dependent) |
| Default compaction trigger | ~150K tokens |
| Context window, current frontier models | 1M tokens |
| Tools per agent before selection accuracy degrades | ~4–5 |
| Passing scaled score | 720 / 1000 |
