# A/B testing and observability at scale

> Companion to [README.md](README.md) §5 (A/B testing and rollout) and §8 (observability at scale). [integration.md](integration.md) gets Claude into the enterprise stack; this answers whether it is **performing the way it should** once it is there.
>
> **The one-line version:** observability answers the **monitoring** question, structured A/B testing answers the **improvement** question. Without both, you are either flying blind or making changes you cannot measure.

---

## 1. Structured A/B testing for live Claude systems

An A/B test for a Claude system follows the same structure as any experiment: a hypothesis, a treatment group, a control group, a metric, and a sample size large enough to make the result statistically meaningful.

> **What makes it different:** LLM outputs are **probabilistic**, which makes the results noisier and the interaction effects harder to control.

### The hypothesis must be specific and testable

> ❌ *"The new prompt is better."*
>
> Fails on both counts — it names no treatment, no metric, and no threshold.

> ✅ *"Replacing the instruction to **summarize** with an instruction to **extract the three most important action items** will increase task success rate by at least **5%** without degrading response latency **p95**."*
>
> It names the treatment, the metric, the threshold for success, and the constraint.

### The four components

| Component | What it requires | What goes wrong when it is missing |
|---|---|---|
| **Hypothesis** | A specific, falsifiable statement naming the treatment, the expected direction of the primary metric, and any constraints on secondary metrics. | Without a hypothesis, **any result can be interpreted as a win.** You can always find a metric that moved in the right direction if you look at enough of them after the fact. |
| **Treatment and control assignment** | **Random** assignment of requests to treatment (new version) or control (current version). Assignment must be **consistent for a given user or session** to avoid contamination. | Non-random assignment means the groups are not comparable. If the treatment group happens to receive more complex queries, an apparent win may be **an artifact of input distribution**. |
| **Primary metric** | A single metric defined **before** the experiment runs — task success rate, cost per completion, latency p95, or a user satisfaction proxy. Choosing the metric after seeing the results is **outcome-shopping**. | An unspecified primary metric turns an experiment into a **retrospective correlation**, which is a much weaker basis for a decision. |
| **Sample size** | Calculated from the minimum detectable effect, the baseline metric value, and the required confidence level. **For LLM systems the variance in outputs is higher** than for deterministic systems, so the required sample size is larger. | An underpowered experiment cannot distinguish a real effect from noise. A team that runs until they see what they want **will find what they were looking for**, whether it is real or not. |

---

## 2. Reading results without overclaiming

**Statistical significance means the result is unlikely to have occurred by chance** given the sample size. Whether it is *large enough to matter* is a separate question. A change can be statistically significant and still too small to justify the operational cost of shipping and maintaining the new version.

Two questions before declaring a winner:

1. **Is the effect large enough** to justify the operational overhead of maintaining the new version?
2. **Did any secondary metric degrade?**

> A prompt change that improves task success rate while **increasing cost by 30%** may not be a net win, depending on the budget constraints of the deployment.

**The failure mode classical A/B tests don't have:** interaction effects between the treatment and specific input types. A prompt change that improves performance on typical inputs may degrade performance on **edge-case inputs that appear rarely in the test period but frequently in a future seasonal spike.** Test period and input distribution alignment matters more in LLM experiments than in most other software contexts.

---

## 3. Shadow testing — validating a change before any user sees it

A live A/B test sends real users to the new version, which means **a regression reaches some fraction of them** before the experiment closes. Shadow testing avoids that exposure:

```
live request ──┬──→ current version ──→ response served to user
               │
               └──→ new version ──────→ output logged, never returned
                                           ↓
                                    scored offline, after the fact
```

The deployment decision is made **before a single user has seen the new version.**

### Choosing between them

The choice comes down to **how much risk the deployment can carry** and **how much traffic it sees.**

| | **Live A/B test** | **Shadow testing** |
|---|---|---|
| **Use when** | The deployment can absorb a small, bounded amount of exposure to a worse version, **and** traffic volume is high enough to reach a statistically meaningful sample in a reasonable window. | A single bad output carries **too much risk**, or traffic is **too low** to support a live split before the change is needed. |
| **The payoff** | You measure against **real user behavior**, including the downstream signals a live response produces — whether the user accepted the answer, whether they followed up. | **Zero user exposure.** For a regulated-industry deployment, where exposing users to an unvalidated model change may not be permissible at all, this is often the only acceptable way to validate. |
| **The cost** | Some users see the worse version. | **Loss of downstream signal.** With no users receiving the shadow output, scoring relies on an offline rubric or golden answers rather than real user behavior. |

---

## 4. Observability at scale — instrumentation, dashboards, anomaly detection

Production observability for a Claude system needs to answer four questions, and **each question requires a different layer of instrumentation.**

| The question | The layer | What it requires |
|---|---|---|
| **What is the system doing?** | **Request-level tracing** | Every request produces a trace: model, model version, input token count, output token count, latency, stop reason, and any tool calls made. **This is the raw material for everything else.** |
| **How well is it performing?** | **Metric aggregation** | Aggregate request-level data into what the dashboard displays: cost per request, latency p50 and p95, task success rate (where the downstream system provides an acceptance signal), and error rate by error type. |
| **When did it change?** | **Anomaly detection** | Threshold alerts on the metrics that matter — a cost spike exceeding **150% of the 7-day average**, a latency p95 crossing the SLA threshold. **Model drift** is harder to catch with threshold alerts and benefits from periodic distribution comparison. |
| **Why did it change?** | **Change attribution** | The instrumentation must distinguish the three causes below. |

> **Per-request decomposition is critical.** Aggregate metrics can look healthy while **a small fraction of requests consumes most of the budget.**

### The three causes a metric move can have

| Cause | What changed |
|---|---|
| **Model drift** | The model's behavior on **stable inputs** changed |
| **Data drift** | The **input distribution** changed |
| **Model update effects** | The **model version** changed, and the new version behaves differently on existing inputs |

> These three have **different mitigations**, and mixing them up produces the wrong fix.

---

## 5. A failure taxonomy — classifying what you are looking at

Instrumentation tells you a metric moved; **diagnosis tells you what kind of failure moved it.** Classify the failure before attributing the change.

| Class | What it is | The fix |
|---|---|---|
| **Prompt failure** | The instruction was ambiguous or underspecified and the model filled the gap. | In the **prompt**, not the model. |
| **Hallucination** | The model produced confident, fluent content **not grounded** in the input or a reliable source. | **Grounding** through retrieval, tool use, or verification. **Stronger instruction will not resolve it.** |
| **Model mismatch** | The chosen tier is wrong for the task, or was swapped without re-evaluation. | **Model selection, gated by an eval.** |
| **Orchestrator-workers failure** | In multi-agent systems, a **recoverable** subagent failure (retry or flag) looks different from an **unrecoverable** orchestrator failure. | Attribution requires **a trace that spans both**. |

### Discernment — judging the output

**Discernment** is one of the four AI Fluency competencies: the discipline of judging the quality of what the model produced rather than accepting it at face value.

Applied to a production system, it is the habit of classifying each output as **acceptable, needs revision, or needs override**, and feeding that judgment back into the evals and the monitoring.

> A team without Discernment **watches metrics move and never asks whether the underlying outputs were actually good.**

---

## 6. Connecting observability data to business value

The people who funded the Claude deployment are not reading the request-level trace. They are reading **a KPI dashboard that measures the outcome the deployment was designed to improve.** The observability stack needs a **translation layer** between the two.

For a customer service agent:

| The observability stack measures | Which maps to the business metric |
|---|---|
| Task success rate | **First-contact resolution rate** |
| Latency | **Average handle time** |
| Error rate | *(and customer satisfaction score as the outcome above both)* |

**Build this translation layer when the system is designed, not after the first business review.** If the technical and business metrics are not mapped at build time, the first business review will raise a question about what is driving the change in handle time — and answering it requires a **retrospective reconstruction** rather than a live query.

---

## 7. Cost · Complexity · Risk

- **Cost** — running an A/B test **without pre-specifying the primary metric** means you can always find a result you want. Underpowered experiments produce false positives: a change that looks like an improvement gets deployed, and the team maintains a version no better than what it replaced while absorbing the full operational overhead.
- **Complexity** — observability instrumentation added **after** the first production incident means the root cause question cannot be answered from the existing log data. The incremental complexity of building the instrumentation correctly the first time is **lower** than the complexity of retroactive log reconstruction.
- **Risk** — an LLM system with **aggregate-only** observability can look healthy while a small fraction of requests consumes most of the budget and produces wrong outputs. Aggregate metrics protect against the obvious failures; **per-request decomposition protects against the non-obvious ones.**
