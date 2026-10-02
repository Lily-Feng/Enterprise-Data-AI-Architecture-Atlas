# Cumulative Exercise — Architect a Regulated Multi-Platform Deployment

> Capstone for [Course 4 — Stakeholder Engagement, Lifecycle & GTM](README.md).
> One self-contained brief, seven decisions, worked in order. **Each decision builds on the last.**

---

## The brief

A regional healthcare network is deploying a **clinical documentation assistant** across two cloud platforms. Nurses dictate patient interactions, the assistant drafts the structured clinical note, and **a licensed clinician must authorize every note** before it reaches the patient record.

| Fact | Detail | What it drives |
|---|---|---|
| **Footprint** | Network runs across two states | Multi-jurisdiction, multi-platform |
| **Regulation** | Health-privacy obligation with an **audit-trail requirement** and a **data-residency rule** | The must-prove constraint (Decision 1) |
| **Human control** | Licensed clinician authorizes every note | Supplies the auditable control (Decision 6) |
| **Platforms** | Partner standardized on **AWS**; some non-regulated back-end work on the **direct API** | Primary vs. secondary entry point (Decision 5) |
| **People** | The original Architect is **rotating off** | Documentation must survive the handoff (Decision 4) |
| **Timing** | **Week four**, and the CFO is asking what the deployment is worth | Outcome document and phase gate (Decisions 6–7) |

---

## The seven decisions at a glance

| # | Decision | Framework applied | The answer, in one line |
|---|---|---|---|
| **1** | Discovery | Discovery translation framework | The health-privacy **audit-trail obligation** is the must-prove constraint; it forces a requirement row for a traceable clinician-review record |
| **2** | Tradeoff framing | Tradeoff translation map | Trimming logging buys latency and spends audit detail — and the **reversal cost** is an interaction-layer redesign plus a disclosable compliance gap |
| **3** | Feedback loop | Feedback-loop governance table | A **quarterly** output audit that fires on the calendar, not on any metric, owned by the compliance lead |
| **4** | Documentation | Documentation completeness checklist | Log the **in-region Bedrock** choice with its rejected global-endpoint alternative, or a successor silently reverts it |
| **5** | Entry point | Entry-point decision matrix | **Bedrock, explicit in-region** (primary) + **direct API** for non-regulated work (secondary); set the region parameter explicitly |
| **6** | Outcome document | Customer outcome documentation template | **Dictation → authorized note** time, before and after, made auditable by the clinician-authorization log |
| **7** | Phase transition | Lifecycle-phase gating | The outcome document gates expansion — and at week four it is **not yet satisfied** |

**The chain:** the constraint (1) sets what may not be traded away (2), which needs a loop to stay live (3) and a decision log to survive handoff (4); the entry point (5) is where residency is actually enforced; the outcome document (6) turns all of it into the CFO's evidence, and (7) judges whether that evidence yet exists.

---

## Decision 1 · Discovery

> **Ask:** From the brief, name the must-prove constraint that most shapes the architecture, and write the one requirement row it forces.

- **Must-prove constraint:** the health-privacy obligation with its audit-trail requirement.
- **Requirement row:** the deployment must produce an auditable record of every model-generated note reviewed by a licensed clinician, traceable to the specific interaction, because the workflow carries a formal proof obligation under a health-privacy regime.
- **Assumption to document:** scope confirmed with compliance before design.

## Decision 2 · Tradeoff framing

> **Ask:** The network asks for the lowest-latency design. Frame the tradeoff between trimming logging for latency and keeping the audit trail, in three elements including the reversal cost.

- **Gain (trim logging):** faster perceived response, smoother clinician workflow.
- **Give up:** the per-interaction audit detail required to satisfy the health-privacy obligation.
- **Reversal cost:** once the system is built around the latency gain, restoring logging requires a redesign of the interaction layer — and any gap period creates a compliance exposure that must be disclosed and remediated.

## Decision 3 · Feedback loop

> **Ask:** Define one governance-table row that maps the required output audit to a stakeholder-review trigger on schedule, independent of any metric.

| Signal | Trigger | Owner | Action |
|---|---|---|---|
| Periodic output audit against the health-privacy documentation standard | **Calendar-based (quarterly, per regulatory obligation)** — fires regardless of eval scores or error rates | Compliance lead | Stakeholder review, with the audit record submitted to the compliance officer |

## Decision 4 · Documentation

> **Ask:** Name the one decision-log row whose absence would let your successor reverse a compliance-load-bearing choice, and state the rejected alternative it must carry.

- **Decision row:** context strategy — explicit **in-region execution via Bedrock**, not a global endpoint.
- **Rejected alternative:** global Bedrock endpoint, for simpler configuration.
- **Tradeoff named:** simpler setup versus data-residency compliance.
- **Why it is load-bearing:** a successor who never sees this rationale will revert to the global configuration to solve a performance problem and break residency — exactly as in the financial-services postmortem.

## Decision 5 · Entry point selection

> **Ask:** Pick the primary and secondary entry points given AWS standardization, a strict obligation, and a residency rule, and name the configuration step that prevents the common residency failure.

- **Primary — AWS Bedrock, configured for explicit in-region execution** (not the global endpoint): the partner is AWS-standardized and the residency rule governs. Verify that the specific compliance requirement (HIPAA BAA or data sovereignty) is satisfied by the Bedrock configuration in use.
- **Secondary — direct API**, for non-regulated back-end tasks where the newest features matter and no residency rule applies.
- **Configuration step:** set the **region parameter explicitly** in the Bedrock client. Do not rely on default endpoint resolution.

## Decision 6 · Outcome document

> **Ask:** Name the before-and-after business metric and the auditable control that make the document usable for the CFO's expansion case.

- **Before metric:** average time from nurse dictation to completed, clinician-authorized clinical note, baselined before deployment.
- **After metric:** the same metric post-deployment, using the same measurement definition.
- **Auditable control:** the clinician-authorization log — every note carries a timestamped authorization record tying clinician, note, and interaction together, which makes the before-and-after comparison **auditable rather than asserted**.

## Decision 7 · Phase transition

> **Ask:** Name the artifact that gates the next phase transition for this brief, and judge whether that gate is satisfied.

- **Gate artifact:** the outcome document — before-and-after metric, auditable control, and named measurement owner. It gates the move from the current deployment phase to the expansion decision the CFO is being asked to make.
- **Judgment: not satisfied at week four.** The before metric exists from baseline, but the after metric needs enough post-deployment runtime to measure, so the outcome document cannot yet be completed.
- **Correct action:** name the measurement owner, confirm the control is logging, and schedule completion of the outcome document at a defined post-launch milestone.
