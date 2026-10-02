# Course 2 — Enterprise Integration & Production

> **Covers exam Domains 3 (19%) and 4 (16%) — 35% of the exam, ~22 items. The heaviest pair.**
> Course length: 158 minutes.
> Original notes: [notes-original.md](notes-original.md)

**The question this course answers:** you have a design that works in a proof of concept. What has to be true before an enterprise will run it, and how do you prove it stays true?

---

## What you will be able to do

1. **Put evals before code.** Define success criteria and build an eval suite before writing the first line of production code — distinguishing **model-based from code-based evals**, selecting the eval workflow stages, and using evals as the **gating mechanism for any change** to a production system.
2. **Take a POC to production.** Work the POC-to-production checklist: map **cost and latency to a budget**, specify the reliability patterns (**retries, fallbacks, circuit breakers**), and name each failure mode of the chosen architecture with its mitigation — including what makes *agents* (systems that use tools, reason across turns, and take multi-step actions) production-reliable.
3. **Scope a use case.** Estimate **call volume, token consumption, and cost**; assess technical feasibility against the four AI properties from *AI Capabilities and Limitations*; and translate a business problem into a scoped solution architecture with **explicit boundary conditions**.
4. **Architect for the enterprise.** Specify the integration patterns for **compliance** (regulated-industry constraints, BAA coverage, data residency), **identity** (SSO/OAuth), **authorization**, **data handling**, and **observability instrumentation** — placing the right mechanism (API, SDK, MCP, Claude Code) at each integration point.

---

## 1. Evals before code — and why the order matters

This is the organizing idea of the whole course. Evaluations are not a testing phase after the build; they are **acceptance criteria written first**.

Three reasons the order matters:

1. **It forces you to state what success means in measurable terms.** "Better customer support" is not a spec. "≥92% of refund-eligibility determinations match the policy engine, p95 under 4 seconds" is.
2. **It exposes design assumptions early, while changing them is still cheap.** Writing the eval reveals that you have no ground truth, or that two stakeholders disagree about what "correct" means — and you would rather learn that in week one.
3. **It gives you a gate.** Without an eval suite you cannot tell whether a model swap, a prompt change, or a new retrieval strategy measurably improved the system. You are left with anecdote.

> **The consequence:** "run the eval suite" is the correct first step for almost every change question on the exam — new model, new prompt, new retrieval strategy, new chunking. If an answer option skips the eval, it is wrong.

## 2. The grading ladder

Not every behavior should be graded the same way. **Reach for the cheapest reliable method first and climb only when the behavior demands it.**

| Rung | Method | Use for | Properties |
|---|---|---|---|
| 1 | **Code-based grading** | Schema validation, exact match, length, presence, numeric tolerance, citation-target existence | Runs in milliseconds, costs almost nothing, **never drifts**. If a behavior can be checked in code, it must be. |
| 2 | **LLM-as-judge** | Outputs requiring interpretation — tone, helpfulness, faithfulness to a source, reasoning quality | Needs rigor to be trustworthy (see below) |
| 3 | **Human grading** | High-stakes or novel behaviors where neither code nor a calibrated judge is trustworthy yet | Most expensive, least scalable — a last resort, not a default |

### Making LLM-as-judge rigorous

A judge without these four controls is a vibe check with extra steps:

- **Detailed rubrics** — say what each verdict means, with examples
- **Constrained verdicts** — a small fixed set of labels, not a free-form 1–10 score
- **Calibration against human-labeled examples** — measure the judge's agreement with humans before trusting it
- **A different model than the one being evaluated** — avoids self-preference bias

> **Exam tell.** An option that proposes an LLM judge with a free-form numeric score and no calibration is a distractor. So is an option that sends a schema check to a judge — that is a code-based check, one rung down.

## 3. Evaluation metrics

Define metrics across all five axes; a system that is accurate and unaffordable has failed.

| Axis | Representative metrics |
|---|---|
| **Accuracy** | Task success rate, groundedness/faithfulness, citation validity, exact-match on structured fields |
| **Latency** | Time-to-first-token, p50/p95/p99 end-to-end, tool-call round-trip time |
| **Cost** | Cost per completed task, tokens per request, cache hit rate |
| **Safety** | Refusal correctness, jailbreak resistance, harmful-output rate, PII leakage rate |
| **Security** | Prompt-injection resistance, unauthorized tool-call attempts, authorization-bypass attempts |

**Cost per completed task, not cost per request.** A cheaper request that needs three more turns to finish the job is not cheaper.

### Building the dataset

Use mixed methodology deliberately:

- **Real production traffic** — the distribution you actually serve. The backbone of the set.
- **Hand-curated edge cases** — the things that go wrong, including every past incident. Each production bug becomes a permanent eval case.
- **Synthetic generation** — for coverage of rare-but-important cases you do not have enough real examples of.
- **Adversarial cases** — injection attempts, out-of-scope requests, ambiguous inputs.

Hold a **train / validation / test split**. If you tune against the same set you report on, your number means nothing.

## 4. Diagnosing production issues

The exam tests diagnosis heavily: a symptom is described, and you pick the most likely cause. **The discipline is to reason from what changed.**

| Symptom | Most likely cause | Why |
|---|---|---|
| Confident but wrong answers after a **document refresh**; model and latency unchanged | Retrieval/indexing returning irrelevant or stale chunks | The refresh is the only thing that changed. Broken re-index or mismatched embeddings feed bad context. *(Official sample item 3.)* |
| Retrieval quality dropped after adopting a **new embedding model for new documents only** | Queries are embedded with the new model but most stored vectors came from the old one — **similarity scores are not comparable across embedding spaces** | Embedding migrations are all-or-nothing: you must re-embed the entire corpus. *(From the course's challenge material.)* |
| Answers degrade as conversations get longer | Context saturation / lost-in-the-middle | Apply compaction, context editing, or fork noisy subtasks |
| Cost spiked with no traffic change | Cache invalidation | Check `cache_read_input_tokens`; hunt the silent invalidator |
| Agent stops before completing the task | Loop not branching on `stop_reason` | Fire-and-forget anti-pattern |
| Tool-selection accuracy fell after adding tools | Capability bloat past ~4–5 tools | Specialize agents or defer-load tools |
| Output format breaks intermittently | Free-form generation parsed after the fact | Enforce a schema via structured output or strict tools, then validate |
| Quality fell after a model upgrade | Prompt was tuned for the previous model | Re-run evals; prompting written for an older model does not announce itself |

## 5. A/B testing and rollout

The safe-change pattern, which is the correct answer to every "the team wants to switch to X" question:

1. **Run the eval suite** on the candidate and compare against the current baseline
2. **Check cost and latency**, not just accuracy
3. **Roll out gradually** — canary, then a percentage, then full
4. **Keep the ability to roll back** at every stage

For an A/B test specifically: hold everything else constant, define the success metric and the minimum detectable effect *before* you start, run long enough for significance, and segment results — an average can hide a regression in a subgroup that matters.

## 6. RAG pipeline design

### The pipeline, and where each stage fails

```
ingest → chunk → embed → index → retrieve → rerank → assemble context → generate → cite
```

| Stage | Main decision | Characteristic failure |
|---|---|---|
| Chunk | Size and boundary strategy | Semantic units split across chunks; answers require two chunks that never co-retrieve |
| Embed | Which model, and **the whole corpus in one space** | Mixed embedding spaces make scores incomparable |
| Index | Vector / keyword / hybrid; metadata filters | No metadata means no way to scope by tenant, date, or permission |
| Retrieve | Top-k, filters, query transformation | k too small misses; k too large dilutes and costs |
| Rerank | Whether to add a reranker | Skipping it when recall is fine but precision is poor |
| Assemble | Order and dedup | Burying the best chunk in the middle |
| Cite | Require each claim to point to a retrieved source | Citations that do not resolve to a real document |

### Chunking strategy by data shape

| Data shape | Strategy |
|---|---|
| Prose documents, policies | Semantic / recursive splitting on headings and paragraphs, with overlap |
| Structured records | One record per chunk; do not split a row |
| Code | Split on function/class boundaries |
| Tables | Keep the header with every chunk, or the rows lose meaning |
| Long transcripts | Split on speaker turns or time windows, with overlap |

**Overlap exists to stop answers falling in the seam.** Too much overlap inflates the index and retrieves near-duplicates.

### Retrieval strategy by query pattern

| Query pattern | Strategy |
|---|---|
| Conceptual / paraphrased questions | Dense vector search |
| Exact identifiers, codes, product names, error strings | Keyword / BM25 — embeddings are bad at exact tokens |
| Mixed natural-language + identifiers | **Hybrid** (dense + sparse), then rerank |
| Scoped by tenant, date, region, permission | Metadata filtering **before** the vector search, not after |
| Needs multiple facts combined | Multi-query or query decomposition, then fuse |

> **Exam tell.** "Which retrieval strategy?" questions are answered by the *shape of the data and the query*, never by which technique is newest. An error-code lookup wants keyword search, no matter how good your embeddings are.

### Grounding rules that prevent confident fabrication

From the course material, the full pattern is: **base answers on retrieved sources; require each citation to point to one of those sources; check automatically that each cited item actually exists; and let the model say when it cannot find support.**

The fourth clause is the one people skip. A model with no permitted way to say "I couldn't find this" will invent something.

## 7. Capability bloat and authorization

### Least privilege is removal, not supervision

The official sample item: an agent that can read tickets, draft replies, issue refunds, and delete accounts, used by staff who only read and draft. The answer is **remove the refund and delete tools entirely**.

Ranking of controls, weakest to strongest:
- Logging the dangerous tool → *detective*; the damage already happened
- Confirmation prompt before the dangerous tool → *compensating*; better, still relies on a human catching it
- A bigger model that "follows instructions more reliably" → *irrelevant to authorization scope*
- **Removing the capability** → *preventive*; the attack surface is gone

### The authorization questions to ask of every integration

1. **Whose identity is the call made as?** The agent's service account, or the end user's? A service account with broad rights turns every user into an admin.
2. **Is authorization enforced at the tool boundary or only in the prompt?** A prompt is not an access control. The tool must check.
3. **What is the blast radius of the most destructive tool available?**
4. **Are credentials scoped per environment and rotated?**
5. **Can the tool's input be influenced by untrusted content?** If the agent reads email, web pages, or documents, that content is **data, not instructions** — and it can attempt to drive the tools.

## 8. Observability at scale

You need to answer, for any single production response: *what did the model see, what did it do, what did it cost, and why did it answer that way?*

| Layer | Capture |
|---|---|
| **Request** | Prompt version, model, effort, tool set, retrieval query and returned chunk IDs |
| **Execution** | Every tool call with arguments and result status, loop iteration count, `stop_reason` per turn |
| **Output** | Response, citations, confidence signals, whether a gate fired |
| **Cost** | Input/output/cache-read tokens per request; cost per completed task |
| **Quality** | Sampled online scoring against the same rubrics as the offline eval |
| **Safety** | Refusals, injection-classifier hits, blocked tool calls |

**Scale considerations:** trace-sample rather than log everything; redact PII at capture time, not at query time; key every trace by a request ID that appears in the user-facing error message; and version the prompt so you can attribute a regression to a change.

**Feedback loop.** Every production incident becomes a permanent eval case. That is the mechanism by which the system gets more reliable over time rather than just older.

## 9. Cost, latency, reliability against a budget

The architect's job is to map each to a number the business agreed to.

| Lever | Effect on cost | Effect on latency | Cost to quality |
|---|---|---|---|
| Prompt caching | Large reduction | Large reduction (TTFT) | **None** — do this first |
| Input-token hygiene (don't resend what you don't need) | Large | Moderate | None |
| Batch API | 50% reduction | Turnaround up to 24h | None — only for non-urgent work |
| Output-token hygiene (ask for less) | Moderate | Moderate | None if the ask is genuinely shorter |
| Lower `effort` | Moderate | Moderate | Workload-dependent; measure |
| Smaller model | Large | Large | Real; must be eval-verified |
| Multi-model cascade | Variable | Variable | Forfeits cache reuse across models — measure the simpler alternative first |

**Order matters: free wins before trade-offs.** Caching, token hygiene, and batching cost nothing in quality. Effort and model choice do.

**Reliability:** define behavior for every failure — tool timeout, rate limit (429), model error (5xx), refusal, malformed output. Retries with backoff for the retryable classes; a defined degraded mode for the rest. "Fail closed" means the failure path denies rather than proceeds.

## 10. Integration patterns an enterprise will accept

A design passes security review when it can answer these without a follow-up meeting:

- **Data residency** — where does inference run, and can you pin it?
- **Data retention** — what is stored, for how long, and is zero-retention required?
- **Network path** — first-party API, a cloud marketplace (Bedrock / Vertex / Foundry), or a private path?
- **Identity** — how do services authenticate? (API key, OAuth profile, workload identity federation — the last being the right answer when the client refuses long-lived secrets.)
- **Secrets handling** — where do credentials live, and do they ever enter a model-visible context? (They must not.)
- **Auditability** — can you produce, for a named request, who asked, what was retrieved, what tools ran, and what was returned?

Mechanism selection (MCP vs. direct API vs. agent-to-agent vs. headless CLI) is tabulated in [platform-reference.md](../platform-reference.md#4-tools-mcp-and-the-integration-mechanism-decision).

## 11. Self-check

1. Give the three reasons evals come before code.
2. Name the three rungs of the grading ladder and the rule for climbing.
3. List the four controls that make LLM-as-judge rigorous.
4. A RAG system degrades right after a document refresh — what do you check, and why that first?
5. Why does adopting a new embedding model for new documents only break retrieval globally?
6. Choose a retrieval strategy for: a policy question, an error-code lookup, and a tenant-scoped search.
7. Rank logging, confirmation prompts, and tool removal as authorization controls.
8. Give the cost-optimization lever order and say which levers are free.
9. State the four-step safe-change pattern for adopting a new model.
