# Use-case sizing and feasibility

> Companion to [README.md](README.md) §9 — *scope a use case* in full: estimate the cost, assess feasibility against the four AI properties, and hand the business owner a verdict they can act on.
>
> **The one-line version:** feasibility is **a verdict plus the constraints that make the verdict true.** A verdict recorded without its constraints becomes an infeasible system the moment one of them is violated.

---

## 1. What sizing is for

The production readiness checklist tells you what a system must achieve to be viable. It covers both the **quality of the model's outputs** and the **reliability of the system around it** — output quality validated through evals, system reliability validated through architecture controls like retries, fallbacks, and circuit breakers. Meeting both bars is what production readiness means.

Sizing tells you whether a *specific business problem* can meet that bar, and what constraints govern the design. Feasibility resolves to one of three states:

| Verdict | Short form |
|---|---|
| **Feasible as scoped** | Works, under stated assumptions |
| **Feasible with constraints** | Works, but only if the constraints are enforced |
| **Not feasible** | Does not work within this scope and budget |

Identifying the state correctly is what makes a scoping document useful. Each verdict's full form — and what it obliges you to document — is in §5.

---

## 2. How to size a use case

Sizing means producing a **cost model before any code is written.** The model does not have to be precise, but it must be accurate enough to validate the architecture against the budget and to surface token-distribution assumptions before they are formalized.

Four inputs drive the model:

| Input | Where the number comes from |
|---|---|
| **Call volume** | The business owner |
| **Token budget per request** | The real input corpus, modeled as a distribution |
| **Model tier** | The capability argument |
| **Sensitivity parameters** | What happens when the first three turn out to be wrong |

### Step 1 — Estimate call volume

How many requests are made per day or per month? **This number comes from the business requirement, not from the developer's intuition.** A customer service agent that handles 1,000 conversations per day produces 1,000 Claude calls per day, plus any multi-turn continuation calls.

> Get this number from the business owner. A sample dataset will not give you an accurate figure.

### Step 2 — Set the token budget per request

The token budget has two components: **input tokens** (system prompt, retrieved context, and user message) and **output tokens** (expected response length).

**Model the distribution rather than just the average.** If document lengths vary widely, the cost model should account for the typical cases as well as the extremes.

If the system prompt is long and stable, prompt caching can meaningfully reduce input costs — with three things the cost model has to carry:

- Caching requires explicit `cache_control` markers in the request.
- **Cache writes cost more per token than standard input.** The model must account for the write cost on first use.
- The default cache TTL is **5 minutes**. Workloads whose request frequency is lower than the TTL will not realize consistent caching savings.

### Step 3 — Project the monthly cost

```
monthly = (call volume × input tokens × input rate)
        + (call volume × output tokens × output rate)
```

**Input and output tokens are priced at different rates on every model tier** — compute the two terms separately, then add them. Where prompt caching applies, price cached input tokens at the **cache read rate**, not the standard input rate, and add the caching savings.

Then compare the result to the cost ceiling from the production readiness checklist. **If the projection exceeds the ceiling, the architecture changes before a line of code is written.**

- **Batch API as a cost alternative.** If it provides a 50% price reduction relative to standard pricing and supports up to 100,000 requests per batch, model it for any workload where the SLA permits asynchronous processing.
- **Regulated workloads:** verify whether batch processing is covered under the partner's BAA and compliance configuration *before* routing PHI or similarly governed data through it.
- **Verify current rates**, the Batch API discount, and the batch size limit at [platform.claude.com/docs — pricing](https://platform.claude.com/docs/en/about-claude/pricing) before finalizing the model.

> The calculator that does this arithmetic — including the cache-write premium and a two-bucket split for the token distribution — is in [fromPOCtoProd.md §2](fromPOCtoProd.md#the-calculator).

### Step 4 — Run sensitivity analysis

What happens to cost if **call volume doubles**? What if the **token distribution shifts toward the tail**?

Sensitivity analysis tells you how fragile the cost model is, and where the assumptions need to be verified with the business owner before committing to the design.

---

## 3. How to scope a use case

The discovery sequence for turning a business requirement into a scoped architecture runs in four steps. **Skipping any step produces a commitment that will not survive the next conversation with the business owner.**

```
business requirement → capability list → architecture sketch → boundary conditions → SOW scope
```

| Step | What it produces | The work |
|---|---|---|
| **1** | Capability list | **Name each capability separately.** "Process insurance claims" is a goal, not a capability. The capabilities might be: extract structured fields from the claim document; look up policy coverage from the policy database; route the claim to the right adjuster queue by type and value; draft the adjuster notification. Identify them separately so each can be assigned to the appropriate owner. |
| **2** | Architecture sketch | For each capability, decide where it belongs. **Which does Claude own? Which belong to existing systems? Which require a human in the loop?** This is the decomposition step from [Module 1](../1-platform-solution-design/README.md), applied to a specific use case. |
| **3** | Boundary conditions | State the conditions under which the architecture works **and the conditions under which it does not.** An architecture that works for documents up to 20 pages but fails for longer ones has a boundary condition that must be documented. |
| **4** | Scope in the SOW | The statement of work carries the boundary conditions, so the development team and the business owner both understand what the system is designed to handle — and what is explicitly out of scope. |

---

## 4. Technical feasibility — the four AI properties

A feasibility assessment that only asks "can Claude do this" is a **capability check**, not an assessment. The four AI properties give you a structured way to identify where the design will require **compensating controls**, and what those controls should be.

| Property | The feasibility question to ask | Where the design compensates |
|---|---|---|
| **Next-token prediction** | Does this task require probabilistic generation, or precision on specific values? Classification, summarization, and drafting are probabilistic tasks where the model excels. Extraction of specific authoritative values — account numbers, policy dates, claim amounts — **requires verification against the source of truth.** | Generator-verifier loops; code-based evals on extracted values; tool calls to retrieve quantitative data |
| **Knowledge** | Does this task depend on information that is rare, contested, recent, or domain-specific in ways that may not be represented in training data? If yes, **the design must bring the knowledge into the context window** — do not rely on the model to supply it. | Retrieval-augmented generation for stable knowledge; tool calls for live-state data; flagging uncertainty on contested claims |
| **Working memory** | Do the inputs fit comfortably in the context window, or does the task require processing inputs that **in aggregate exceed** it? Long documents, multi-document tasks, and extended conversations all hit this constraint. | Chunking strategies; progressive context loading; summarization across turns; pipeline architecture for inputs exceeding the context limit |
| **Steerability** | Are the instructions specific, concrete, and verifiable? Abstract or ambiguous instructions, long reasoning chains, and tasks requiring precise numerical or logical computation are all places the model can **drift from intent.** | System prompts with explicit output schemas; structured outputs; code execution for numerical precision; evaluator-optimizer loops |

---

## 5. Feasibility verdicts

Once the scoping sequence and the technical assessment are complete, the architecture is ready for a verdict. There are three.

| Verdict | What it means | What to document |
|---|---|---|
| **Feasible as scoped** | The arguments across the four AI properties favor Claude for each capability. The cost model is within the ceiling. The latency p95 is within the SLA. No capability requires a compensating control that changes the architecture. | **State the assumptions clearly.** Feasible-as-scoped verdicts become feasible-with-constraints the moment assumptions change. |
| **Feasible with constraints** | The design works under specific conditions **that must be enforced**: document length stays under a threshold; the retrieval index is refreshed on a defined schedule; a human review gate exists for outputs above a confidence threshold. The constraints are part of the architecture. | Document each constraint explicitly, and **for each one, the failure mode when it is violated.** The development team needs to know what they are designing *for*, not just what they are building. |
| **Not feasible** | At least one capability faces an AI property limitation that cannot be compensated for within the scope and budget — or the cost model exceeds the ceiling by a margin that model tier, caching, and architecture changes cannot close. **A not-feasible verdict is a correct assessment** that saves the engagement from a more expensive failure later. | State which constraint is disqualifying and why. Where a scope reduction would change the verdict, **name it and present the business owner with a choice.** |

---

## 6. Business value and ROI mapping

A feasibility verdict tells the business owner the system **can** be built within the budget and the constraints. It does not tell them whether building it is **worth doing.**

ROI mapping answers that second question. It connects the scoped architecture to the financial and operational outcomes the business expects, expressed in terms the business owner already uses — hours saved, error rates reduced, cycle time shortened, revenue protected. The mapping turns a technical design into **a decision a budget holder can defend.**

### The five pillars

| Pillar | What it captures |
|---|---|
| **Efficiency** | The same work done faster or cheaper |
| **Transformation** | Work that was not feasible before becoming possible |
| **Productivity** | More output from the same people |
| **Solution cost** | The run cost of the system itself |
| **Performance SLAs** | The service levels the deployment must hold |

Map each ROI claim to the pillar it advances, so the value statement captures both the number **and the kind of value it represents.**

### The mechanism

A comparison between two states, measured in the same unit:

```
value = (baseline state − projected state)  −  run cost from the sizing model
```

The **baseline state** is how the work is done today. The **projected state** is how it is done once Claude is in the workflow. The cost figure comes directly from the sizing model in §2, so the ROI calculation reuses work already done rather than starting over.

### Step 1 — Name the baseline in a business unit

Start from how the task is performed today, measured in the unit the business already tracks — for a claims review workflow, analyst hours per claim or average days to resolution.

> The baseline must come from the business owner's own **operational data**, because every later number is compared against it. A baseline pulled from intuition produces an ROI figure no finance team will accept.

### Step 2 — Predict the post-deployment state in the same unit

Estimate how the same task performs once Claude is in the workflow, in the **identical unit** as the baseline.

Where the feasibility verdict requires human review, **the projection must include that cost.** Routing low-confidence output to a reviewer reduces labor; it does not eliminate it. When the design specifies human-in-the-loop review, projecting full automation overstates the value and produces a number operations will reject.

### Step 3 — Subtract the run cost from the sizing model

Take the projected monthly cost produced during sizing and treat it as the **recurring** cost of the new state. The value of the deployment is the operational gain from Step 2 minus this run cost.

This step isolates recurring run cost only — **build cost is treated separately**, in the payback period in Step 4. Reusing the sizing output keeps the two analyses consistent: a change to the token budget or model tier then updates the cost ceiling and the value case together.

### Step 4 — State the payback period and the sensitivity

Express the result as a **payback period**: the time it takes for accumulated operational gain to cover the build cost and the run cost. Then state how that period moves if the volume assumptions or the gain-per-task assumptions are wrong.

> Quoting a payback period without sensitivity analysis invites a decision based on a single optimistic scenario — one that often fails when the business case meets real volumes after launch.

The output is a short **value statement** the Architect hands to the business owner alongside the feasibility verdict. It ties "Can we build this?" and "Is it worth building?" back to numbers the business already owns, and the two artifacts travel together into the statement of work.

### The three common ROI map errors

| Risk | Why it happens, and where it shows up |
|---|---|
| **The baseline is estimated rather than measured.** | When the business owner has no clean operational data, the baseline gets filled in from intuition, making the apparent gain misleading. The error stays hidden **until the finance team asks for the source of the baseline number** during business case review — at which point the whole case must be rebuilt. |
| **The projection assumes full automation when the design requires human review.** | A verdict that requires a human review gate means labor is *reduced*, not eliminated; the value case often models it as eliminated. The gap surfaces in the **first operational period after launch**, when actual analyst hours fail to fall as far as the business case promised. |
| **The run cost is taken from an average rather than the sizing distribution.** | An average token cost instead of the distribution understates recurring cost, which overstates net value. Concentrated in **workflows with heavy-tailed inputs**, where a small fraction of large requests drives most of the cost. |

---

## 7. Cost · Complexity · Risk

- **Cost** — sizing based on **average** token counts underestimates cost when some requests are much larger than others. Getting this wrong means renegotiating the architecture after the contract is already signed.
- **Complexity** — a feasibility assessment that skips any of the four AI properties risks missing a constraint that changes the design. **Working memory is the most overlooked**, since it rarely shows up during development on small, clean inputs — but it will surface in production.
- **Risk** — a feasible-with-constraints verdict that is **not documented** becomes an infeasible system when the constraints are violated in production. The constraints are part of the design and carry the same weight as the architecture they qualify.

---

**What to watch out for.** The capability question gets answered before the constraint questions are even asked. Volume, latency, and input size are **inputs to** the feasibility verdict — the verdict is only as sound as the constraints gathered before it.
