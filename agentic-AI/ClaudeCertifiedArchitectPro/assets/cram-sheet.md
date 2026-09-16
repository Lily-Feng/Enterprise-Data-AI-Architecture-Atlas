# Cram Sheet — last hour before the exam

One page. Decision tables and the answer shapes that recur. Everything here is expanded in the course folders.

---

## The meta-rule

Every item gives you four options. Three of them are usually one of these:

| Distractor shape | Example | Why it loses |
|---|---|---|
| **Observe instead of prevent** | "Add logging to the refund tool" | Detective control where a preventive one was available |
| **Add ceremony instead of removing cause** | "Add a confirmation prompt" | Compensating, not eliminating |
| **Swap a component that wasn't implicated** | "Use a larger model" | Nothing in the scenario points at model capability |
| **Do the thing that sounds advanced** | "Make it multi-agent" | Complexity not forced by the requirement |
| **Partial answer** | "Run the eval" (but no rollback / no cost check) | The right idea with a clause missing |

**The winning answer usually: removes the root cause, addresses the thing that actually changed, layers a control rather than relying on one, or names an owner and an artifact.**

When two options both look right, pick the **more complete** one — the exam favors the answer with all the clauses (eval + cost/latency + gradual rollout + rollback), not the shortest correct-sounding one.

---

## Architecture tier — pick the simplest that works

| Need | Tier |
|---|---|
| One in, one out | Single call |
| Needs facts/capability it lacks, you control the flow | Augmented LLM |
| **Steps are knowable in advance** | **Workflow** ← most common correct answer |
| Multi-step, cannot be specified in advance | Agentic loop |
| Genuinely separable specialized subtasks | Multi-agent |

**Agent gate (all four must pass):** complexity · value · viability · **recoverable cost of error**.

## Ownership split (do this before anything else)

**Claude** — language, summarization, planning, drafting, tool-mediated action.
**Existing systems** — anything already paid for and reliable: the rules engine, the DB of record, the policy service.
**Humans** — judgment, exceptions, approvals, where being right beats being fast.

## The loop

Branch on `stop_reason`: `tool_use` → execute, append `tool_result`, continue. `end_turn` → confidence/authorization gate → return or escalate.
Anti-patterns: **fire-and-forget** (single-turn call) and **full autonomy** (no escalation).
Parallel tool calls → return **all** `tool_result` blocks in **one** user message. Failed tool → `is_error: true`, never dropped.

## Multi-agent

- **≤4–5 tools per agent.** Past that, tool-selection accuracy drops.
- **Isolate context** — pass each subagent only its slice, not the coordinator's trace.
- **Fan-out needs fan-in:** results returned must equal units dispatched, or retry / surface the gap.
- Worst failure: **confident synthesis over incomplete work** — the summary looks complete and isn't.

## Business value pillars

**Transformation** = something that *wasn't possible before*. **Efficiency / cost** = existing work, faster/cheaper. **Productivity** = more output per person. **Performance/SLA** = a service level you couldn't meet before. *(Exam uses these exact words.)*

---

## Model & context

| Lever | Order to reach for it |
|---|---|
| Prompt caching | 1st — free |
| Input/output token hygiene | 2nd — free |
| Batch API (50% off, ≤24h) | 3rd — free if latency allows |
| Lower `effort` | 4th — measure per route |
| Smaller model | 5th — must be eval-verified |
| Multi-model cascade | last — forfeits cache reuse (caches are model-scoped) |

**Judge cost per completed task, not per request.**

**Caching:** prefix-match, render order `tools → system → messages`. Stable first, volatile last. Max 4 breakpoints. Verify with `usage.cache_read_input_tokens`. Silent invalidators: timestamps in the system prompt, unsorted JSON, varying tool set, model switch.

**Thinking:** adaptive thinking + `effort` (`low`…`max`, default `high`). Fixed `budget_tokens` is deprecated.

**Context strategy:** progressive discovery beats monolithic at scale. **Context editing** *clears*; **compaction** *summarizes* (~150K trigger); **memory** persists outside the window. Fork noisy subtasks; return only the synthesis.

**Structured output:** `output_config.format` or `strict: true` tools, **then validate programmatically**. Never regex.

---

## Integration mechanism

| Pick | When |
|---|---|
| Direct API / Tool Runner | One system, full control, your own tools |
| **MCP** | **Reuse across multiple clients/teams; a governed standard boundary** |
| Managed Agents | Anthropic runs the loop and hosts the sandbox; versioned configs; scheduled runs |
| Headless Claude Code | Repo-shaped work, CI: `claude -p "..." --output-format json` |
| Agent-to-agent | Independent systems with separate ownership |

**Capability bloat fix:** remove tools, specialize agents, or defer-load via tool search.

## RAG

| Query shape | Retrieval |
|---|---|
| Conceptual / paraphrased | Dense vectors |
| Error codes, IDs, exact strings | **Keyword / BM25** |
| Mixed | Hybrid + rerank |
| Tenant / date / permission scoped | Metadata filter **before** the search |
| Needs multiple facts | Multi-query decomposition + fuse |

**Grounding, all four clauses:** base on retrieved sources · each citation points to one of them · **automatically verify each cited item exists** · **let the model say it can't find support**.

**Embedding migration is all-or-nothing.** New model for new docs only ⇒ queries in the new space vs. vectors in the old ⇒ similarity scores not comparable ⇒ global quality drop.

---

## Evals

**Evals before code** because they (1) make success measurable, (2) expose assumptions while they're cheap to change, (3) give you a gate for any change.

**Grading ladder — cheapest reliable first:** code-based → LLM-as-judge → human.
Judge rigor: **detailed rubric · constrained verdicts · calibrated against human labels · different model than the one evaluated.**

**Metrics:** accuracy · latency (p95) · cost · safety · security.
**Dataset:** production traffic + curated edge cases + synthetic coverage + adversarial; train/val/test split.
**Every production incident becomes a permanent eval case.**

**Change pattern (memorize all four clauses):** run the eval suite → check cost and latency → roll out gradually → keep the ability to roll back.

## Diagnosis — reason from what changed

| Symptom | Cause |
|---|---|
| Confident-wrong right after doc refresh | Retrieval/index stale or mismatched |
| Quality dropped after partial embedding swap | Incomparable vector spaces |
| Degrades as session lengthens | Context saturation |
| Cost spiked, traffic flat | Cache invalidation |
| Agent stops early | Not branching on `stop_reason` |
| Wrong tool picked after adding tools | Capability bloat |
| Format breaks intermittently | No schema enforcement |
| Quality fell after model upgrade | Prompt tuned for the old model |

---

## Safety

**Five layers:** input screening · system prompt · **tool permissions** · output screening · monitoring.
Layers 1/2/4 are *soft*; **layer 3 is hard**. Given a prompt-based and a permission-based control for the same risk, **permissions win**.
*"A single control is a single point of failure."*

**Least privilege = removal.** Remove > confirm > log > bigger model.

**Untrusted content (email, web, docs, tool results):** treat as **data, not instructions** · limit tool surface while handling it · **human approval for irreversible/outward actions**.

**HITL calibration:** approval only for **high-impact or irreversible** actions; low-risk reads run automatically; **audit a sample of them**.

**Fail closed:** classifier down → deny; tool timeout → error into the loop; validation fail → reject; low confidence → escalate; unknown action → deny.

## Compliance — obligation → control → owner → evidence

| Regime | The exam's answer |
|---|---|
| **HIPAA** | A **BAA covers the specific services and settings in use**, and only the **minimum necessary PHI** is sent |
| **GDPR erasure** | Delete from **every place it lives — embeddings, caches, logs, eval datasets** ⇒ you must **track where the data goes at ingest** |
| **FedRAMP** | Confirm the **exact deployment path (platform + region + service)** holds the required authorization level. "The vendor is authorized" is never the answer |

**Bias/fairness, all four:** evals **segmented by demographic group** · humans responsible for final decisions · document limitations · keep monitoring after launch.

---

## Stakeholders & lifecycle

**Discovery:** identify every stakeholder early — sponsor, end users, **security, legal, compliance** — and involve anyone who must approve **from the start**.

**First pilot:** contained · clear current-state metrics · available data · engaged sponsor · manageable risk. *(Not the highest-value or most interesting one.)*

**ADR:** context · options considered · decision · rationale · **consequences**.

**Handoff:** runbooks · eval suite · dashboards and alerts · escalation paths — **and the team runs operations while you're still there.**

**Low adoption:** diagnose first — **fit** in daily work/tools · **training** · **trust** · what they **say** about it. Then fix those. Never "add features."

**SLA:** latency as **p95**; accuracy as a measured rate on a defined eval set; define the degraded mode; state what's out of scope.

---

## Team enablement

**Shared config:** shared `CLAUDE.md` + agreed tools/MCP servers + permission posture.
`CLAUDE.md` = **instructions**; settings = **enforceable**. Scopes: user → project → directory, all merged, **most specific wins**.

**Skills distribution:**

| | Reach | Rollback |
|---|---|---|
| Org-provisioned | Whole org | **None** — manual re-upload |
| Plugin (group/org) | Targeted teams | **Strongest** — install prefs + versioned repo updates |
| Project Skill | One team's repos | With the repository |
| API Skill | Machine-to-machine | Explicit version pinning |

**Spend posture:** model defaults · allowlists/restrictions · effort guidance · spend/rate/per-user caps.

**Adoption:** **champion per team first, then batches.** Access without enablement stalls at basic chat; lumpy adoption never standardizes the gain.

**Verification checklist:** correctness (incl. edge cases) · security (no secrets, validated input, least privilege) · maintainability · **the author can explain what it does and why, including untested inputs**.

**Runbook** = symptom → cause → action. **Escalation path** = who handles what, and when it leaves the team. Goal: *they need you for the new problem, not the familiar one.*

**CI:** never interactive. `claude -p "..." --output-format json`. Batch API for anything that can wait.

---

## Numbers

720/1000 pass · 63 items · 120 min · ~1:54 per item · Batch = 50% off, ≤24h · 4 cache breakpoints · 512–4096 min cacheable prefix · ~150K compaction trigger · ≤4–5 tools per agent · 1M context on current frontier models · retakes at 14 / 30 / 90 days, 4 per year · credential valid 12 months
