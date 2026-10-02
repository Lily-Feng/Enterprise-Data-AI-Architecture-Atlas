# Cumulative Exercise — Architect an RFP Drafting Assistant

> Capstone for [Course 2 — Enterprise Integration & Production](README.md).
> One self-contained brief, five decisions, worked in order. **Each decision builds on the last.**

---

## The brief

A professional services firm is deploying an **RFP drafting assistant** over its historical engagement corpus. A consultant queries the system, it retrieves relevant excerpts and firm methodology, and drafts an RFP response the consultant then **accepts or revises**.

| Fact | Detail | What it drives |
|---|---|---|
| **Volume** | 800 requests/day → **24,000 requests/month** | The cost model (Decision 2) |
| **Corpus** | **12,000 documents**, 5–80 pages — ~14,600 tokens average, ~175M tokens total | Corpus scale forces RAG (Decision 3) |
| **Token shape** | ~2,000 system + ~3,000 retrieved context + ~200 query = **~5,200 input**; ~600 output | Cost model and caching strategy (Decision 2) |
| **Model tier** | **Sonnet**, caching on the stable system prompt, Haiku fallback | Cost and reliability posture (Decision 2) |
| **Proprietary content** | Firm methodologies **not in training data** | The knowledge-axis mitigation (Decision 3) |
| **Confidentiality** | Client-confidential documents, tagged in **SharePoint** | Retrieval-layer access control (Decisions 1, 4) |
| **Identity** | **Okta** | Server-side verification (Decision 4) |
| **SLA** | Latency **p95 under 8 seconds** | Alerting and the A/B constraint (Decisions 4, 5) |
| **Baseline** | Draft acceptance without major revision at **70%** | The A/B hypothesis (Decision 5) |

---

## The five decisions at a glance

| # | Decision | Framework applied | The answer, in one line |
|---|---|---|---|
| **1** | Eval strategy | The grading ladder + golden dataset | **Code-based** on citation schema, **model-based** on draft relevance; golden set built from redacted past RFPs |
| **2** | POC-to-production | Cost model, reliability controls, failure modes | Within range at Sonnet with caching — but **on flat averages**, and the corpus is bimodal |
| **3** | Sizing and feasibility | The four AI properties | **Feasible with constraints.** Corpus scale (not document length) drives RAG; **retrieval index coverage is the load-bearing boundary condition** |
| **4** | Integration pattern | The five-layer integration model | Okta verified **server-side**, role injected by the server; the **retrieval layer** enforces confidentiality before Claude sees content |
| **5** | A/B testing posture | Hypothesis, sample size, input-distribution control | 70% → **75%** acceptance, ~1,500 sessions/group, ~**4 days**; control for RFP complexity |

**The chain:** the eval strategy (1) defines what "good" means, which the cost and reliability model (2) has to hold at production volume; feasibility (3) says it is buildable *only while the retrieval index stays current*; the integration pattern (4) is where the confidentiality constraint is actually enforced; and the A/B posture (5) is how any later change to the system gets proven rather than asserted.

---

## Decision 1 · Eval strategy

> **Ask:** Name the code-based and model-based evals, and say where the golden dataset comes from.

- **Code-based eval:** schema compliance on extracted citations — **document name, page number, section**.
- **Model-based eval:** relevance and appropriateness of the draft response to the RFP.
- **Golden dataset:** built from **past RFPs with redacted client names**, sourced from the firm's historical engagements.
- **Exclusion rule:** client-confidential documents are **excluded from the eval set** unless the client has given explicit approval.

---

## Decision 2 · POC-to-production checklist

> **Ask:** Build the cost model, specify the reliability pattern, and name the most critical failure mode.

**Cost model**

```
800 requests/day × 30 days            = 24,000 requests/month
~2,000 system + ~3,000 context + ~200 query = ~5,200 input tokens
                                        ~600 output tokens
```

At **Sonnet tier with caching on the stable system prompt**, projected cost is within range.

> **State the weakness in the answer.** These are **flat averages** — the projection assumes requests cluster near the mean with no heavy tail. The corpus runs from 5 to 80 pages, so retrieved-context size is likely **bimodal**, and a tail of large excerpt requests **understates input cost** on a flat-average model.
>
> The within-ceiling verdict holds *under the assumed distribution* and should be checked with the sensitivity analysis from the sizing cluster ([sizing.md §2, Step 4](sizing.md#step-4--run-sensitivity-analysis)) before it is relied on. The two-bucket form of the model is in [fromPOCtoProd.md §2](fromPOCtoProd.md#the-calculator).

**Reliability** — fallback chain from **Sonnet to Haiku** for latency spikes.

**Most critical failure mode** — **retrieval quality drift** as documents are added to the corpus. If new documents are indexed inconsistently, retrieval precision degrades and draft quality degrades with it.

---

## Decision 3 · Use-case sizing and feasibility

> **Ask:** Work the four AI properties, then give the feasibility verdict and its boundary condition.

### Working memory — the binding constraint is corpus scale, not document length

- A single 80-page document is **~29,000 tokens** — it fits well within the **1M-token** context window on most current models and **is not a constraint on its own**.
- Average document length across the 5–80-page range is **~14,600 tokens**; the full 12,000-document corpus is **~175 million tokens**, which far exceeds any context window.
- **12,000 documents cannot be loaded into context simultaneously. This is what drives the RAG architecture.**
- Chunking strategies are available for individual documents but are **not the load-bearing constraint here.** The architecture requires a retrieval layer to surface relevant excerpts at query time.

### Knowledge — proprietary methodology is not in training data

- The firm's proprietary methodologies **are not in Claude's training data**, so the model cannot supply them from memory.
- **Mitigation — retrieval.** Methodology documents are indexed in the same RAG layer as the engagement reports and surfaced into the context window at query time. This is the standard compensating control for knowledge gaps on domain-specific content.
- **The system does not need Claude to know the methodologies; it needs Claude to reason over methodology excerpts the retrieval layer puts in front of it.**
- **The constraint:** retrieval quality must be high enough to surface the right methodology content for a given query. If retrieval misses the relevant section, the response is incomplete **regardless of how well the model reasons over what it receives.**
- **Therefore:** retrieval precision on methodology queries is tracked as a **separate metric** in the eval suite *and* in production observability.

### Verdict — feasible with constraints

All four AI property axes are addressable within the scoped architecture:

| Axis | Resolved by |
|---|---|
| **Working memory** | The RAG layer |
| **Knowledge** | Indexing methodology documents into the same retrieval corpus |
| **Steerability** | The system prompt structure and the output schema for RFP drafts |

> **The load-bearing boundary condition is retrieval index coverage and freshness.** The system works as long as the index contains the relevant methodology and engagement documents and is kept current as the corpus changes.
>
> If the index is incomplete, if documents are added without being indexed, or if the index drifts out of sync with the document management system, **the knowledge-axis mitigation fails** and the system produces responses that omit or misrepresent firm methodology.
>
> **That condition must be documented as an explicit operational constraint in the statement of work.**

---

## Decision 4 · Integration pattern selection

> **Ask:** Specify identity, confidential-document handling, PII, and observability.

- **Identity:** the **Okta token is verified server-side.** User role and authorized document sets are **injected into the system prompt by the server, not supplied by the user.**
- **Client-confidential handling:** documents tagged confidential in SharePoint are retrievable **only** by consultants whose role includes the relevant client engagement. **The retrieval layer enforces this access control before passing content to Claude.**
- **PII:** client names in documents are replaced with **anonymized identifiers before the document enters the context window.**
- **Observability — what to log:**

| Layer | Logged |
|---|---|
| **Request** | Model version, input token count (**with caching hit/miss**), output token count |
| **Quality** | **Retrieval precision per request**, measured against the grounding documents |
| **Context** | User role, session ID |
| **Outcome** | The consultant's **acceptance or revision** of the RFP draft |

- **Alerts:** latency **p95 crossing 8 seconds**, and **retrieval precision dropping below threshold**.

---

## Decision 5 · A/B testing posture

> **Ask:** State the hypothesis, compute the sample size, and name the input-distribution control.

- **Hypothesis:** the new retrieval configuration will increase RFP draft task success rate — measured by **consultant acceptance of the draft without major revision** — from **70% to at least 75%**, without increasing latency p95 above **8 seconds** or cost per request by more than **10%**.
- **Sample size:** detecting a **5-point improvement at a 70% baseline** with **80% power** and **5% significance** requires approximately **1,500 sessions per group**. At 800 requests/day split evenly, that is **~4 days** — feasible.
- **Input-distribution control:** ensure treatment and control groups have similar distributions of **RFP complexity** (proxy: document length and number of source documents retrieved). **Segment by RFP type** where possible.
