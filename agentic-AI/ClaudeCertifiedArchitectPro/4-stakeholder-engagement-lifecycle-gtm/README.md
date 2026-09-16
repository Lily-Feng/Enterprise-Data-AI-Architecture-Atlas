# Course 4 — Stakeholder Engagement, Lifecycle & GTM

> **Covers exam Domain 6 (14%) — ~9 items.**
> Course length: 178 minutes.
> Original notes: [notes-original.md](notes-original.md)

**The question this course answers:** a system that works technically still has to ship, get adopted, and survive your departure. What makes that happen?

The course framing: *"a design that only the Architect understands falls apart the moment they leave the room."*

---

## 1. Discovery — find everyone who can say no

**The rule:** identify every stakeholder early — **including the sponsor, end users, security, legal, and compliance — and involve anyone who must approve the project from the start.**

The failure this prevents is the most expensive one in the whole track: an integration that skips security review never reaches production. You do not discover a blocking requirement in week eleven; you discover it in week one and design around it.

| Stakeholder | What they can block | Bring them in to establish |
|---|---|---|
| **Executive sponsor** | Funding and priority | The business outcome and how it will be measured |
| **End users** | Adoption (the silent veto) | Current workflow, actual pain, where the tool must live |
| **Security** | Deployment | Data path, identity model, secrets handling, auditability |
| **Legal / compliance** | Deployment | Regulated data, retention, BAAs, jurisdiction, disclosure |
| **Data owners** | Access to the corpus | What exists, its quality, who may see it |
| **Ops / platform** | Runtime | SLOs, on-call, monitoring, escalation |
| **Finance** | Renewal | Budget, unit economics, spend caps |

### Questions that produce a specification

Non-technical stakeholders answer "what would you like it to do" with a wish. These produce requirements instead:

- What happens today, step by step, and who does each step?
- How often, and how long does each instance take?
- What does it cost you when this goes wrong today — and how do you find out?
- Show me three real recent examples, including one that went badly.
- Who has to sign off before this reaches a customer?
- What would make you turn it off?

Last one is the most useful question in discovery. It surfaces the real risk tolerance and the real failure conditions.

## 2. Choosing the first pilot

**The course's answer:** *a contained use case with clear current-state metrics, available data, an engaged sponsor, and manageable risk.*

Four criteria, all four required:

| Criterion | Why it is required |
|---|---|
| **Contained** | A bounded scope you can finish and evaluate |
| **Clear current-state metrics** | Without a baseline you cannot prove improvement — and "it feels better" does not fund phase two |
| **Available data** | A pilot blocked on a six-month data-access request is not a pilot |
| **Engaged sponsor** | Someone whose problem it actually is, who will clear obstacles |
| **Manageable risk** | The cost of a wrong answer during the pilot is survivable |

> **Exam tell.** Distractors pick the highest-value use case, the most technically interesting one, or the most visible one. The right pilot is the one that *can be finished and measured*. A pilot's job is to produce evidence, not revenue.

## 3. Communicating trade-offs

Stakeholders cannot act on "it depends." Present a decision as: **the options, what each costs, what each gives up, and your recommendation.**

The architect's obligation is to *make a recommendation*, not to enumerate possibilities and leave the choice to someone with less information.

### Architecture Decision Records

The exam names this explicitly. An **ADR** captures:

1. **Context** — the situation and constraints at the time
2. **Options considered** — the credible alternatives, not strawmen
3. **The decision** — what was chosen
4. **The reasons** — why, against those alternatives
5. **The consequences** — what this makes easy, what it makes hard, what it forecloses

> **Exam tell.** "How should the team record why this architecture was chosen?" → an ADR with context, options, decision, rationale, and consequences. Options considered and consequences are the two parts people omit, and they are the two parts that make the record useful to whoever inherits it.

**Why it matters for the handoff:** six months later, nobody remembers why the boring option was rejected. Without the ADR, the team either re-litigates it or repeats the mistake it was avoiding.

## 4. Expectation alignment and SLAs

Set expectations before the demo, not after the incident.

- **Accuracy is a target with a distribution, not a promise.** Commit to a measured rate on a defined eval set, with a stated behavior on the remainder.
- **Latency is p95, not average.** An average hides the tail that users actually complain about.
- **Availability includes upstream dependencies** — your retrieval store and your tools are in the path.
- **Define the degraded mode.** What the system does when a dependency is down is part of the SLA, not an afterthought.
- **Say what is out of scope,** in writing, early.

**Non-determinism has to be communicated explicitly**, because it violates what stakeholders expect from software: the same question may get a differently-worded answer, and a demo that worked is not a guarantee. This is why the eval suite is a stakeholder artifact, not just an engineering one — it converts "it usually works" into a number that can go in a contract.

## 5. The lifecycle

```
discovery → design → build → evaluate → pilot → rollout → handoff → monitor → iterate
```

Two gates that are easy to skip and expensive to skip:

- **Between design and build:** security, legal, and compliance sign-off. Design is when changing the answer is still cheap.
- **Between pilot and rollout:** the eval suite passes at the agreed threshold, *and* pilot users say they would keep using it.

## 6. The handoff that survives your absence

**The course's answer:** *hand over runbooks, the eval suite, dashboards and alerts, and escalation paths — then let the team run operations while you're still around to help.*

Two parts, and the second is the one people get wrong.

### The artifacts

| Artifact | What it answers |
|---|---|
| **Runbooks** | "This symptom is happening — what do I do?" Symptom → cause → action. |
| **The eval suite** | "Is this change safe to ship?" |
| **Dashboards and alerts** | "Is it healthy right now, and who gets woken up?" |
| **Escalation paths** | "This is beyond us — who owns it next?" |
| **ADRs** | "Why is it built this way?" |

### The sequence

**The team runs operations while you are still there.** A handoff is not a document drop on your last day. The team must operate the system, hit real problems, and resolve them with you available as a backstop — that is the only way you find out which parts of the documentation do not work.

> **Exam tell.** Options that describe handoff as "deliver complete documentation" or "schedule a knowledge-transfer session" are weaker than the option where the receiving team operates the system before the architect disengages.

## 7. Adoption — diagnose before you fix

When a launched system is not being used, the wrong move is to add features or send another announcement. **Find out why first.**

The course's diagnostic covers four things:

1. **Fit** — how well does it fit into people's daily work and tools? (A system that lives somewhere people do not already go will not be used, regardless of quality.)
2. **Training** — were they actually enabled, or just given access?
3. **Trust** — do they believe the output? Has it been wrong in a memorable way?
4. **Sentiment** — what do they say about it, to each other?

**Then fix those issues.** Each cause has a different remedy: fit is an integration problem, training is an enablement problem, trust is an accuracy-and-transparency problem, sentiment is usually a symptom of one of the other three.

> **Exam tell.** Any option that responds to low adoption with more features, more capability, or a better model without first diagnosing the cause is wrong.

## 8. Iteration after launch

**Model upgrade — the safe-change pattern** (the course states this one directly): *run the eval suite on the new model, check cost and latency, roll it out gradually, and keep the ability to roll back.*

All four clauses. An option missing the eval, missing cost/latency, missing gradual rollout, or missing rollback is incomplete.

**Ongoing feedback loop:** production incidents become eval cases; user corrections become training signal for the prompt or retrieval; monitoring reveals drift; the eval suite grows and is the gate for every change. This is the mechanism by which the system improves rather than merely ages.

## 9. Self-check

1. Who must be identified in discovery, and when?
2. Give the five properties of a good first pilot.
3. Name the five parts of an ADR and say which two are usually omitted.
4. Why is latency committed as p95 rather than average?
5. List the handoff artifacts and state the sequencing rule that makes a handoff real.
6. Adoption is low three months after launch. What do you do, in order?
7. Give the four-step safe pattern for adopting a newer model.
