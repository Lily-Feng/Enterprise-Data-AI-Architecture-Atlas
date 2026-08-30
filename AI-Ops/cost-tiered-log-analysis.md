---
title: Cost-tiered log analysis
description: Why log intelligence is shaped by cost per record rather than model quality, and where the expensive tier belongs in the pipeline.
tags: [aiops, logs, observability, opentelemetry, anomaly-detection, llm]
---

# Cost-tiered log analysis

[LogAI](https://github.com/salesforce/logai) (Salesforce AI Research, [arXiv:2301.13415](https://arxiv.org/abs/2301.13415), January 2023) is the useful reference implementation here, because it was designed at the last moment before language models changed what the top of the pipeline could do. Its plumbing aged well and its intelligence layer did not, and the split between those two halves is exactly where the architectural argument lives.

The governing number is not model quality. At even 10⁹ lines per day `[approx]`, per-line inference is not expensive, it is arithmetically impossible: Drain templates a line in microseconds, and no hosted model does. That ratio, and nothing else, dictates the shape.

So the pipeline is a **funnel with a hard cost boundary in the middle**. Left of it, deterministic code runs on every line with no model in the loop. Right of it, metered inference runs on a population small enough to pay for.

## Topology

```text
              deterministic · every line · no model                         metered · survivors only
  ═════════════════════════════════════════════════════════════     ═══════════════════════════════════════

  ┌───────────────┐     ┌───────────────┐     ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
  │    01 EDGE    │     │    02 LAKE    │     │   03 SCREEN   │     │    04 RANK    │     │   05 EXPLAIN  │
  │───────────────│     │───────────────│     │───────────────│     │───────────────│     │───────────────│
  │ redact first  │write│ Iceberg on    │ scan│ counters, ETS │ flag│ embeddings +  │top-k│ agent joins   │
  │ Drain inline  │ ──▶ │ object store  │ ──▶ │ per template  │ ──▶ │ tuned encoder │ ──▶ │ context, then │
  │ no model here │     │ push-down     │     │ rarity        │     │ on survivors  │     │ cites records │
  └───────────────┘     └───────────────┘     └───────────────┘     └───────────────┘     └───────────────┘
    10⁹ lines/day         full fidelity          → 10⁴ groups          → 10³ cands         → 10¹ incidents
```

| Stage | Runs on | Cost per record | Emits |
|---|---|---|---|
| 01 Edge collect | Every line | ~µs, no model | Template id, attributes, redacted body |
| 02 Lake | Every line | Storage only | Columnar rows, predicates pushed into the scan |
| 03 Screen | Every partition | ~µs, no model | 10⁴ suspicious groups `[approx]` |
| 04 Rank | Screened groups | One small-model pass | 10³ ranked candidates `[approx]` |
| 05 Explain | Ranked candidates | Full inference + tool calls | ~10 incidents with citations `[approx]` |

Volumes are order-of-magnitude and estate-specific; the ratios between stages are the design, not the absolute numbers.

## The boundary is between 03 and 04

Everything upstream of stage 04 exists to make stage 05 affordable. This inverts the usual reading of the classical components: per-template counters and ETS baselines are not the legacy part of the system that a model replaces, they are the part that buys the model its budget.

Two consequences follow.

**Screening precision is the budget lever.** If stage 03 passes 10⁶ groups instead of 10⁴, the agent tier is unaffordable and no amount of model quality recovers it. That pass-through rate is the first number to instrument, ahead of any accuracy metric.

**Parsing stays where it is, but gains a second mode.** Drain in the hot path at microseconds per line is not negotiable at volume. The model's role is offline: bootstrap the template set on a new source, repair it when a deploy breaks the patterns, name clusters in terms an engineer recognises, and emit patterns that compile down to cheap regex which then runs forever without inference.

What genuinely does not survive is the vectorizer tier. TF-IDF, Word2Vec and FastText with a custom-trained vocabulary degrade on templates they have never seen — and every deploy produces those. This is the practical form of log drift, and it is the failure mode the 2023 design never confronts.

## The join that was declared and never made

LogAI's `LogRecordObject` defines `TraceId` and `SpanId` — it inherits them from the OpenTelemetry log record — and then no stage of the pipeline ever joins on them. That omission caps the ceiling on everything downstream, because a model reasoning over log text alone is guessing at causes it structurally cannot see.

Stage 05 is only worth its cost if what enters the context window is a join rather than a log excerpt.

```text
   SIGNAL                        JOIN KEY

   [ candidate log partition    ] ┄┄ seed ┄┄┄┄┄┄┄┄┄┄┐   ← the only one v0.1 had
   [ distributed traces         ] ── trace_id ──────┤
   [ service metrics            ] ── svc · t±15m ───┤
   [ deploy & config changes    ] ── svc · t±15m ───┤
   [ log statement call site    ] ── template→src ──┤
   [ runbooks & past incidents  ] ── embedding ─────┘
                                                    │
                                                    ▼
                                     ┌─────────────────────────────┐
                                     │ CONTEXT WINDOW              │
                                     │ deduped and budgeted,       │
                                     │ re-redacted                 │
                                     └──────────────┬──────────────┘
                                                    ▼
                                     ┌─────────────────────────────┐
                                     │ AGENT                       │
                                     │ reasons over tools          │
                                     │ must cite record ids        │
                                     └──────────────┬──────────────┘
                                                    ▼
                                      narrative · evidence links ·
                                       suspect change · next check
```

Each arrow is labelled with the key the join actually runs on, because that key is the requirement the design places on instrumentation. Without trace context propagating across services, five of the six inputs degrade or vanish and the figure collapses back to logs in isolation — which is the 2023 architecture again, wearing a newer model.

The output shape matters as much as the inputs. An anomaly score hands an on-call engineer a number and no next step. The deliverable is a narrative that cites the record ids it rests on, names the suspect change, and proposes the next check — and an unciteable conclusion is a hypothesis regardless of how confidently it reads. That constraint is the same one that governs any investigation agent; see [fluency is not calibration](../agentic-ops/README.md).

## Wiring

The config-driven, plug-in component design is the part of LogAI worth keeping verbatim. What changes is that redaction becomes a gate rather than an option, and the analysis layers are exposed as typed tools rather than as a form in a portal.

```yaml
edge:
  input: otlp                      # OTLP/gRPC in, not file loaders
  redact:
    enforce: true                  # a gate, not a preprocessing option
    on_classifier_failure: drop    # fail closed; the model tier is downstream
  parse:
    algorithm: drain               # hot path, ~µs/line
    template_store: managed        # repaired offline, see below

lake:
  format: iceberg
  pushdown: [service, severity, template_id, timestamp]

screen:                            # tier 3 — deterministic, does the reduction
  detectors: [template_counter, ets_baseline, rarity]
  partition:
    strategy: identifier           # or sliding_window / fixed_window
    key: trace_id
  budget:
    max_groups_out: 10000          # the cost lever; alert if saturated

rank:                              # tier 4 — one small model pass
  embedder: sentence-encoder
  scorer: tuned-encoder
  top_k: 1000

explain:                           # tier 5 — metered inference
  join:
    traces:   { on: trace_id }
    metrics:  { on: service, window: 15m }
    changes:  { on: service, window: 15m }
    code:     { on: template_id }
    runbooks: { on: embedding }
  context:
    max_tokens: 120000
    re_redact: true                # assume the join re-introduced raw fields
  require_citations: true          # uncited conclusion is rejected, not shown
```

## Component verdicts

| Component in v0.1 | Verdict | What changes |
|---|---|---|
| `LogRecordObject` on OpenTelemetry | **Keep** | The best call in the paper — OTLP became the neutral format they bet on. Add the streaming loader v0.1 deferred to "future versions". |
| Regex cleaning, partitioning | **Keep** | Session, sliding-window and identifier partitioning survive intact; partitioning is context assembly under another name. Redaction is promoted to a hard gate. |
| Drain / IPLoM / AEL parsers | **Reposition** | Drain stays in the hot path. A model bootstraps and repairs the template set offline and emits patterns that compile to cheap regex. |
| TF-IDF / Word2Vec / FastText | **Replace** | Modern embeddings, for one reason: custom vocabularies degrade on unseen templates, and every deploy produces those. |
| Counters, ETS, ARIMA, Isolation Forest | **Keep** | Stage 03. Unglamorous and load-bearing — it does the reduction that makes inference affordable at all. |
| LSTM / CNN / Transformer / LogBERT | **Narrow** | One small fine-tuned encoder still wins on cost per scored candidate at stage 04. The rest of the zoo was benchmark furniture. |
| Anomaly score as the output | **Replace** | Emit a cited narrative. A score is not an action. |
| *(absent)* cross-signal correlation | **Add** | The whole of the second diagram. The keys were declared in the data model and never joined on. |
| Plotly Dash portal | **Reframe** | The point about needing visual validation holds. Keep the charts, drive them from an agent that writes the query, expose the four layers as typed tools. |

## What breaks

**Screening precision sets the entire budget.** Covered above, and repeated because it is the failure that makes every other decision moot. Instrument the stage 03 pass-through rate before anything else.

**Redaction is best-effort.** Regex and classifiers miss. Assume some sensitive data reaches the model, and let that assumption pick the deployment tier — local weights for regulated estates, hosted for the rest — rather than discovering it after the fact.

**The join is only as good as the instrumentation.** The second diagram assumes trace context actually propagates. In most estates it partly does, and the agent silently receives a thinner context than the design promises, with no signal that it happened.

**There is no benchmark for the right half.** HDFS and BGL measure stage 03 at best. They sit near saturation — LogAI reports F1 ≈ 0.98 across nearly every configuration, and the spread between libraries is smaller than the variance from train/test splits, which means the benchmark has stopped discriminating. Le and Zhang had already shown these datasets fall to simple baselines ([ICSE 2022](https://doi.org/10.1145/3510003.3510155)), and they now sit in every pretraining corpus, so any model-based result on them is contaminated by construction. Evaluating stages 04 and 05 needs incident-level, time-split, held-out-system data that does not exist publicly.

## Relationship to the rewrite plan

This note records the architecture. The [LogAI rewrite plan](LogAI-Rewrite-Plan.md) is the research programme built on the same source paper, and it is the more considered document on scope, evaluation and what may honestly be claimed.

Two mappings are worth holding onto. The funnel above is the plan's **evidence funnel** figure — raw telemetry reduced to incident evidence and then to verified findings — drawn with the cost boundary made explicit. The component verdicts table is a condensed form of the plan's retain / modernize / replace matrix, and the plan's version is more complete: it also covers the operator experience, the remediation lifecycle, and the governance controls that this note does not attempt.

The one thing this note adds that the plan leaves implicit is the arithmetic: which stage pays for which, and the pass-through rate that decides whether the reasoning tier is affordable at all.

---

A visual version of both diagrams is published [here](https://claude.ai/code/artifact/4253df1c-a4a2-4bc9-8af7-69dbc5313f43).

Source paper: Cheng, Saha, Yang, Liu, Sahoo and Hoi, *LogAI: A Library for Log Analytics and Intelligence*, Salesforce AI Research, 2023 — [`LogAI.pdf`](LogAI.pdf).
