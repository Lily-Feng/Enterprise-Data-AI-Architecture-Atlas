# Course 3 — Responsible AI, Safety & Risk for Architects

> **Covers exam Domain 5 (14%) — ~9 items.**
> Course length: 114 minutes.
> Original notes: [notes-original.md](notes-original.md)

**The question this course answers:** where does each safety control sit, and what happens when one of them fails?

The course framing is precise: *"a safety control merely assumed fails at the worst moment."* Every answer in this domain is about **placement** and **failure behavior**, not about intent.

---

## 1. Defense in depth — the organizing principle

**A single control is a single point of failure.** Controls must be layered so that one miss does not lead to harm.

The five layers, in order of where they sit in the request path:

| # | Layer | What it does | Fails how |
|---|---|---|---|
| 1 | **Input screening** | Classifies and filters what enters the context: injection attempts, PII, out-of-scope requests, known-bad patterns | Novel phrasing gets through |
| 2 | **System prompt** | Sets role, boundaries, refusal rules, and the permission to say "I don't know" | It is an *instruction*, not an enforcement mechanism — a determined input can talk around it |
| 3 | **Tool permissions** | Constrains what the model can actually *do*: which tools exist, what scope their credentials have, what needs approval | Over-broad scope; credentials wider than the task |
| 4 | **Output screening** | Checks what leaves: PII leakage, unsupported claims, harmful content, schema violations, citation validity | Can only catch what it is checking for |
| 5 | **Monitoring** | Detects in production what the first four missed | Detective, not preventive — it tells you afterwards |

> **The key asymmetry:** layers 1, 2, and 4 are *soft* — they influence or inspect. Layer 3 is *hard* — it determines what is physically possible. When an exam item offers you a prompt-based control and a permission-based control for the same risk, **the permission-based control is the stronger answer.**

> **Exam tell.** "Why is relying only on the system prompt insufficient?" → *It's a single point of failure. Controls should be layered (input checks, system prompt, tool permissions, output checks, monitoring) so that one miss doesn't lead to harm.*

## 2. Fail closed, not open

A control that fails open is not a control. Specify, for every gate:

- **Classifier unavailable** → deny or degrade, do not skip the check
- **Tool timeout** → return an error to the loop, do not synthesize a result
- **Validation failure** → reject and retry or escalate, do not pass the payload through
- **Low confidence** → escalate, do not answer anyway
- **Unknown action** → default deny

Fail-closed is also what makes the multi-agent coverage check from [Course 1](../1-platform-solution-design/README.md#the-orchestration-failure-mode-you-must-be-able-to-diagnose) work: a missing subagent result must block or flag synthesis, not be silently synthesized around.

## 3. Prompt injection and untrusted content

**The rule:** anything the agent *reads* is data, not instructions. Email bodies, web pages, documents, ticket text, file contents, tool results, and another agent's output are all untrusted.

The course's worked example is an agent that processes email and can issue refunds and send messages. The correct design has three parts:

1. **Treat email content as untrusted data** — never as instructions to follow
2. **Limit what the agent can do while handling it** — reduce the tool surface available during untrusted-content processing
3. **Require human approval for refunds and outgoing messages** — the irreversible, outward-facing actions

Notice the shape: *classify the content, constrain the capability, gate the irreversible action.* All three, not one.

Supporting techniques: keep operator instructions in a channel the untrusted content cannot occupy (a mid-conversation system message rather than user text); never let retrieved content decide which tool to call; and never send data to a URL, recipient, or endpoint that came from the content rather than from the user.

## 4. Human-in-the-loop — calibrated, not universal

Requiring approval for everything destroys the value of the system and trains reviewers to rubber-stamp. Requiring it for nothing is negligent.

**The course's rule:** *require approval only for high-impact or irreversible actions, let low-risk actions like reading run automatically, and audit a sample of them.*

Route by three properties:

| Property | Ask | Higher risk → |
|---|---|---|
| **Reversibility** | Can this be undone? | Approval gate |
| **Impact** | What is the blast radius if wrong? | Approval gate |
| **Confidence** | Does the system know it might be wrong? | Escalation path |

| Action class | Control |
|---|---|
| Read, search, retrieve, draft | Run automatically; **audit a sample** |
| Write to an internal system, reversible | Run automatically with logging; review exceptions |
| Financial transactions, external messages, deletions, account changes | **Human approval before execution** |
| Anything below a confidence threshold | Escalate regardless of class |

**Sampled audit of the automatic path is not optional** — it is how you learn that the "low-risk" classification was wrong.

## 5. LLM failure modes an architect must name

| Failure mode | What it looks like | Architectural response |
|---|---|---|
| **Hallucination** | Fluent, specific, wrong | Ground in retrieval; require resolvable citations; permit "I don't know" |
| **Confident error** | Wrong answer in the same tone as a right one | Verification step; confidence gating; human review on high stakes |
| **Prompt injection** | Untrusted content redirects the agent | Treat content as data; constrain tools; gate irreversible actions |
| **Non-determinism** | Passes in testing, fails in production | Eval suite over a distribution, not a single run |
| **Context degradation** | Quality falls as the session grows | Compaction, context editing, forked subtasks |
| **Capability bloat** | Wrong tool chosen as the toolbelt grows | ≤4–5 tools per agent; defer-load; specialize |
| **Silent incompleteness** | A fan-out result goes missing; the summary looks whole | Fan-in coverage check; retry or surface the gap |
| **Training-data boundaries** | Unreliable on rare, private, or fast-changing facts | Bind to external sources of truth |
| **Bias** | Systematically different outcomes across groups | Evals segmented by group; human accountability; documented limits |

## 6. Compliance — map each obligation to a named control, owner, and evidence

The architect's deliverable is not "we are compliant." It is a table: **obligation → control → owner → evidence artifact.**

### HIPAA
The question to answer is: **does a Business Associate Agreement cover the specific services and settings being used, and is only the minimum necessary PHI being sent?**

Both halves matter. A BAA that covers one service does not cover a different one you added last month, and a covered service used with a setting outside the agreement is not covered either. Minimum-necessary is an architecture constraint: it dictates what you put in the prompt, what you retrieve, and what you log.

### GDPR — the right to erasure
This is the one that catches architects, and the course states it directly. Deletion means **deleting the data from every place it lives — including embeddings, caches, logs, and any eval datasets built from it.**

Which means the real requirement is upstream: **you must track where a subject's data goes in the first place.** A deletion request you cannot satisfy is an architecture failure that happened months earlier, at ingest.

Practical consequences:
- Vector stores need subject-keyed metadata so vectors are findable and deletable
- Caches need TTLs and a purge path
- Logs need retention limits and redaction at capture
- **Eval datasets built from production traffic are personal data** — they are in scope
- Also in scope: lawful basis, data minimization, purpose limitation, and transparency about automated decision-making

### FedRAMP
Confirm that **the exact deployment path — cloud platform, region, and service — holds the authorization level the agency's data requires.**

"The vendor is FedRAMP authorized" is never the answer. Authorization attaches to a specific service offering in a specific boundary at a specific impact level (Low / Moderate / High). The architect's job is to verify the path, not the brand.

### The general pattern
Whatever the regime, the exam wants: **a named control, a named owner, and an evidence artifact you could hand an auditor.** An answer that says "ensure compliance" without naming who and what is a distractor.

## 7. Ethical AI — bias, fairness, transparency

The course's four-part answer, which generalizes to most Domain 5 fairness items:

1. **Use evals to compare outcomes across demographic groups** — an aggregate accuracy number hides disparate impact; segment it
2. **Keep humans responsible for final decisions** — accountability does not transfer to a model
3. **Document the system's limitations** — what it is not reliable for, stated where users will see it
4. **Keep monitoring after launch** — distributions shift; a system fair at launch is not permanently fair

Transparency in practice: disclose that a decision was AI-assisted, cite sources for factual claims, surface confidence where it is actionable, and provide a route to a human.

## 8. Routing a decision to the right reviewer

Not every decision needs the same reviewer. Route on three properties:

| Property | Low | High |
|---|---|---|
| **Confidence** | Escalate | Proceed |
| **Reversibility** | Escalate | Proceed |
| **Cost of being wrong** | Proceed | Escalate |

Then map to a **named reviewer**: security review for anything touching authorization or data egress; legal/compliance for regulated data and retention; the business owner for policy and tone; engineering for the technical rollback path. A decision with no named reviewer is a decision that will be made by whoever is in the room at deploy time.

## 9. Self-check

1. Name the five control layers in request-path order and say which one is *hard* rather than soft.
2. Why is the system prompt alone insufficient? (Use the course's own phrasing.)
3. Give the three-part design for an agent that processes untrusted email and can issue refunds.
4. State the HITL calibration rule — including what you do with the actions that run automatically.
5. What must a GDPR erasure request reach, and what does that imply about ingest?
6. Why is "the vendor is FedRAMP authorized" the wrong answer?
7. Give the four-part answer on bias and fairness.
8. Define fail-closed for: classifier unavailable, tool timeout, low confidence, unknown action.
