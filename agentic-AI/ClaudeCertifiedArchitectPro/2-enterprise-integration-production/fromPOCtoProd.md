# From POC to Production

> Companion to [README.md](README.md) §9 (cost, latency, reliability against a budget) — the POC-to-production checklist in full.
>
> **The one-line version:** a POC is built to demonstrate capability; a production system is built to survive real volume, real inputs, and impatient users. The four dimensions where a POC misleads you are **cost, latency, reliability, and failure modes.**

---

## 1. Where a POC and a production system differ

A POC runs at low volume, on clean inputs, with a patient user. A production system runs at the volume your partner's business generates, on real inputs, with users who have no tolerance for slow or incorrect responses.

| Dimension | Why it's invisible in a demo | What it looks like when it fails |
|---|---|---|
| **Cost** | A POC running 10–50 requests per day produces a negligible bill. Monthly cost at production volume is a different calculation entirely. | The billing dashboard exceeds the budget signed off at project approval, and the architecture has to be renegotiated **after** deployment. |
| **Latency** | A demo runs one request at a time. **p95 under concurrent load is a different number** than median latency on a single request. | SLA breaches and user abandonment. Latency that is fine for a demo can be unacceptable in a real-time user-facing workflow. |
| **Reliability** | A POC has no retries, no fallback, no circuit breaker. When it fails, the developer refreshes and tries again — nobody is waiting. | Any transient API failure takes the entire user-facing workflow down instead of degrading gracefully. |
| **Failure modes** | A demo is tested on the inputs the developer expected. Production supplies the ones they didn't. Failure modes are **specific to architecture type**. | Silent degradation, made-up outputs on edge cases, or complete failure on an input class nobody tested. |

---

## 2. Cost and latency modeling — know the numbers before you build

Build the model **before** you finalize the architecture. Three inputs:

1. **Call volume** — requests per day or per month
2. **Token budget per request** — input tokens plus expected output tokens
3. **Model tier**

From those three you estimate monthly cost and check it against the budget ceiling before any code is written.

### The trap: averaging the token budget

Teams compute the average token count over the inputs they have and assume that is the distribution. Token distributions are usually **skewed** — most requests are short, but a tail of long requests consumes a disproportionate share of total cost.

> A cost model built on average usage can underestimate the cost of those long requests **by a factor of two or three.**

### Design to p95, not the median

Median latency describes the middle of the pack; SLA breaches come from the high end. **p95 is the latency value below which 95% of requests complete** — only the slowest 5% fall above it. That makes it the useful design target.

### Caching: the highest-leverage lever

Prompt caching is the most effective cost *and* latency lever **when the system prompt is long and stable**. It preserves the processed prompt prefix for the cached tokens, so the API does not reprocess them on later requests. What is stored is **the prompt prefix**.

- **Savings scale with two things:** the length of the cached prefix, and how often it is reused. If cache reads are charged at, say, 10% of the standard input-token rate, a long prefix reused across many requests produces the largest effective saving.
- **Current rate:** [platform.claude.com/docs — pricing](https://platform.claude.com/docs/en/about-claude/pricing)

> **The risk is consistency.** If the cached content must reflect live state, caching creates a consistency window that may violate the use case's requirements.

### The calculator

Two multipliers do most of the work. Every token is billed at the model's base rate times one of these:

| Token class | Multiplier |
|---|---:|
| Uncached input | **1.00** × input rate |
| Cache write — 5-minute TTL | **1.25** × input rate |
| Cache write — 1-hour TTL | **2.00** × input rate |
| Cache read (a hit) | **0.10** × input rate |
| Output | **1.00** × output rate |
| Batch API — applies to the whole request | **0.50** × everything |

Base rates per model: [platform-reference.md §1](../platform-reference.md). Verify them against the [pricing page](https://platform.claude.com/docs/en/about-claude/pricing) before quoting a number to a client.

**Per request:**

```
prefix_multiplier = hit_rate × 0.10  +  (1 − hit_rate) × 1.25
billed_input      = prefix_tokens × prefix_multiplier  +  variable_input_tokens
request_cost      = (billed_input × input_rate + output_tokens × output_rate) ÷ 1,000,000
```

**Per month — two buckets, not one average:**

```
monthly = Σ  bucket_share × monthly_volume × bucket_request_cost
```

> **Use the mean, or model the buckets.** Cost is linear in tokens, so a *correct* mean gives the correct total. The trap is that the number a team reaches for is the **typical** request — and on a skewed distribution the typical request sits well below the mean. Two buckets make the tail impossible to leave out, and they hand you the per-request ceiling the budgets in §4 need.

#### Worked example

A policy-answering assistant on **Claude Sonnet 5** — $2.00 input / $10.00 output per 1M tokens.

| Input | Value |
|---|---|
| Monthly volume | 400,000 requests |
| Cached prefix (system + policy docs + tool definitions) | 12,000 tokens |
| Cache hit rate | 95% |
| **Body** — 90% of requests | 600 variable input tokens, 300 output |
| **Tail** — 10% of requests, a document is attached | 40,000 variable input tokens, 3,000 output |

Prefix multiplier: `0.95 × 0.10 + 0.05 × 1.25` = **0.1575** — the 12,000-token prefix bills as 1,890 tokens.

| Bucket | Requests | Cost per request | Monthly |
|---|---:|---:|---:|
| Body | 360,000 | $0.00798 | $2,872.80 |
| Tail | 40,000 | $0.11378 | $4,551.20 |
| **Total** | **400,000** | | **$7,424.00** |

**The tail is 10% of the volume and 61% of the bill.** That is the number a median-based estimate never shows: priced on the typical request alone, this system models at $3,192/month — **understating the real bill by 2.3×.**

Two variations off the same model, each one line of input changed:

| Change | Monthly | vs. baseline |
|---|---:|---|
| Baseline | $7,424 | — |
| **No prompt caching** (prefix billed at 1.00 every request) | $15,512 | **2.1× the cost**, for one config change |
| **Tail routed through the Batch API** (document processing is not latency-sensitive) | $5,148 | **31% saved**, no quality cost |

Both of those are free wins — no quality traded. Before modelling a cheaper tier for the tail, note that **caches are model-scoped**: splitting buckets across two models forfeits cache reuse on the second one, and the calculator only shows that if you set its `HIT_RATE` to what a cold cache actually delivers.

#### The script

```python
# Rates: $ per 1M tokens. Check them against the pricing page before quoting a number.
INPUT_RATE, OUTPUT_RATE = 2.00, 10.00      # Claude Sonnet 5
CACHE_READ, CACHE_WRITE = 0.10, 1.25       # multipliers on INPUT_RATE (1.25 = 5-min TTL, 2.00 = 1-hour)

def request_cost(prefix_tokens, hit_rate, variable_in, out, batch=False):
    prefix_mult = hit_rate * CACHE_READ + (1 - hit_rate) * CACHE_WRITE
    billed_in = prefix_tokens * prefix_mult + variable_in
    cost = (billed_in * INPUT_RATE + out * OUTPUT_RATE) / 1e6
    return cost * (0.5 if batch else 1.0)

VOLUME, PREFIX, HIT_RATE = 400_000, 12_000, 0.95
BUCKETS = [
    # name,   share, variable_in,    out,  batch
    ("body",   0.90,         600,    300,  False),
    ("tail",   0.10,      40_000,  3_000,  False),
]

total = 0.0
for name, share, var_in, out, batch in BUCKETS:
    per, n = request_cost(PREFIX, HIT_RATE, var_in, out, batch), VOLUME * share
    total += per * n
    print(f"{name:<6}{n:>9,.0f} req   ${per:>9.5f}/req   ${per*n:>10,.2f}/mo")
print(f"{'TOTAL':<6}{VOLUME:>9,} req   {'':>21}${total:>10,.2f}/mo")
```

```
body    360,000 req   $  0.00798/req   $  2,872.80/mo
tail     40,000 req   $  0.11378/req   $  4,551.20/mo
TOTAL   400,000 req                        $  7,424.00/mo
```

#### Fill this in before you commit to an architecture

| Input | Where the number comes from | Yours |
|---|---|---|
| Monthly volume | The partner's business, not the POC's traffic | |
| Cached prefix size | `count_tokens` on the frozen system + tools | |
| Cache hit rate | `usage.cache_read_input_tokens` ÷ total input, measured — not assumed | |
| Bucket shares and token shapes | The **real** input corpus, split at the knee of the distribution | |
| Output tokens per bucket | Measured on real requests; capped by `max_tokens` | |
| Budget ceiling | **Signed off at project approval** — the number this has to come in under | |

> If the total exceeds the ceiling, the levers are in [README.md §9](README.md#9-cost-latency-reliability-against-a-budget) and they have an order: **caching, token hygiene, and batching cost nothing in quality — spend those before touching effort or model tier.**

---

## 3. Reliability controls — what belongs in every model call

Three controls, addressing different failure scenarios at different layers of the call stack.

| Control | What it handles | How to size it |
|---|---|---|
| **Transient error recovery with exponential backoff** | Transient errors — rate limit (429), timeout, 5xx — retried with progressively longer delays, so a flood of retries doesn't turn a brief hiccup into a prolonged outage | Set max attempts and total wait time by how much delay the use case tolerates |
| **Fallback chains** | Primary model or endpoint unavailable — route automatically to an alternative (different model tier, cached response) rather than raising an error to the user | Test fallback behavior **as part of the eval suite** |
| **Circuit breakers** | A degraded downstream dependency — trips when the error rate crosses a threshold, after which requests fail immediately instead of waiting for a timeout | Set the error-rate threshold; prevents one bad dependency taking down the broader system |

### Placement decides whether they work

| Control | Where it sits |
|---|---|
| Retries / new attempts | **Close to the API call** |
| Circuit breakers | **At the service boundary** |
| Fallback chains | **In the orchestration layer** |

> Placed in the wrong layer, they protect the wrong part of the system and leave the right part exposed.

---

## 4. Failure modes by architecture type

**Agents** handle tasks that cannot be completed in a single model call: they use tools, observe results, adjust plans mid-execution, and complete multi-step processes requiring dynamic reasoning at each step. Claude Code is a production example — navigating codebases, running tests, applying fixes, iterating across a workflow that is impossible single-turn. The controls below govern how to build these reliably.

| Architecture | What breaks first | Mitigation |
|---|---|---|
| **Agent** | **Unbounded tool use and growing context.** An agent that can call tools without budget constraints or turn limits runs up cost and latency invisibly — until one request blows the budget ceiling. | Set per-turn token budgets, max tool-call counts, and explicit stopping criteria. Constrain the tool set to the minimum required. **Eval the stopping behavior, not just output quality.** |
| **RAG** (retrieval-augmented generation) | **Retrieval quality drift** — documents added or removed without reindexing, query and document representations falling out of alignment, or a refresh schedule that leaves live-state queries stale. | Keep retrieval quality in the eval loop. Monitor **precision and recall as system metrics**, not just output quality. Separate live-state queries from static knowledge queries. |
| **Document processing pipeline** (evaluator-optimizer) | **No exception path for low-confidence extractions.** One flow for every document produces wrong outputs on edge cases at the same rate it produces right ones on clean documents. | Add confidence scoring to the extraction step. Route low-confidence extractions to a **human review queue** instead of downstream processing. Put edge cases and difficult documents in the eval set. |
| **Orchestrator-workers** | **Blurred failure boundaries** between orchestrator and subagents — traces fragment, and a dropped subagent can fail silently at synthesis. | Define recoverable (subagent: retry or flag) versus unrecoverable (orchestrator) boundaries. Use a **shared trace ID** across all agents. Reconcile coverage at synthesis so results equal the units submitted. |

### Model version pinning applies to all four

It is an **operational discipline, not an architecture choice** — it applies to every architecture in the table equally:

1. Pin model versions in configuration
2. Monitor the [model deprecations page](https://platform.claude.com/docs/en/about-claude/model-deprecations)
3. Maintain a version-update runbook

---

## 5. Cost · Complexity · Risk

- **Cost** — don't assume POC costs scale to production. Model costs **before** committing to an architecture, not after the first billing cycle.
- **Complexity** — retries, fallback chains, and circuit breakers are far harder to retrofit into a system that wasn't designed for them. Build reliability in from the start rather than scrambling after the first production incident.
- **Risk** — a system with no fallback and no circuit breaker has exactly one point of failure: the primary model endpoint. When it goes down at peak load there is no recovery path, and the whole user-facing workflow fails instead of degrading gracefully.


The POC was treated as a production model in three dimensions simultaneously: cost, input distribution, and reliability. All three are production-system properties that must be designed in separately, and a POC establishes none of them.