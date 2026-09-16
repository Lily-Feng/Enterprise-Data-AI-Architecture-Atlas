# Exam Blueprint — Claude Certified Architect · Professional (CCAR-P)

> Source: *Claude Certified Architect – Professional Exam Guide*, Version 1.0, effective July 2026.
> Full PDF: [assets/Claude-Certified-Architect-Professional-Exam-Guide-v1.0.pdf](assets/Claude-Certified-Architect-Professional-Exam-Guide-v1.0.pdf)

## 1. Exam at a glance

| Item | Value |
|---|---|
| Credential | Claude Certified Architect – Professional |
| Exam code | CCAR-P |
| Items | 63 |
| Format | Multiple-choice and multiple-response; each item states how many responses to select |
| Time limit | 120 minutes (≈ 1 min 54 s per item) |
| Delivery | Proctored — online proctored and/or Pearson VUE test center |
| Passing score | **720** on a scaled range of 100–1,000 |
| Fee | $175 USD |
| Validity | 12 months from award date |
| Reporting | Pass/fail + scaled score, plus percent-correct by domain (domain percentages are informational only; the pass decision is on total scaled score) |

**Scoring model.** Criterion-referenced — you are measured against a fixed standard set by SMEs in a standard-setting study, not against other candidates. There is no curve.

**Retakes.** 14 days after a first failure, 30 after a second, 90 after a third. Maximum four attempts per exam in a rolling 12 months. Fee applies each attempt.

**Renewal.** Free, non-proctored renewal assessment on the Anthropic Partner Academy before expiry. Let it lapse and you retake the full exam at full price.

## 2. Domain weights

| # | Domain | Weight | Approx. items (of 63) | Course that covers it |
|---|---|---:|---:|---|
| 1 | Solution Design & Architecture | 17% | ~11 | [Course 1](1-platform-solution-design/) |
| 2 | Claude Models, Prompting & Context Engineering | 13% | ~8 | [Course 1](1-platform-solution-design/) |
| 3 | Integration | **19%** | ~12 | [Course 2](2-enterprise-integration-production/) |
| 4 | Evaluation, Testing & Optimization | 16% | ~10 | [Course 2](2-enterprise-integration-production/) |
| 5 | Governance, Safety & Risk Management | 14% | ~9 | [Course 3](3-responsible-ai-safety-risk/) |
| 6 | Stakeholder Communication & Lifecycle Management | 14% | ~9 | [Course 4](4-stakeholder-engagement-lifecycle-gtm/) |
| 7 | Developer Productivity & Operational Enablement | 7% | ~4 | [Course 5](5-team-enablement/) |

**Where the weight actually sits.** Domains 1 + 2 + 3 = **49%** of the exam and all live in Courses 1–2. Domain 3 alone is the single heaviest domain. Domains 5 + 6 = 28% and are mostly judgment questions with a predictable "right answer" shape (layered controls, named owner, evidence artifact, gradual rollout with rollback) — these are the cheapest points on the exam to secure.

## 3. Objectives by domain

### Domain 1 — Solution Design & Architecture (17%)
- Translate business problems into Claude-based AI solutions
- Design end-to-end architectures (input → processing → output → feedback loops)
- Select appropriate architectural patterns (workflow, agentic, augmented LLM)
- Design multi-agent systems and orchestration strategies
- Apply decomposition techniques for complex problem solving
- Align solutions to business value pillars (efficiency, transformation, productivity, cost, performance SLAs)

### Domain 2 — Claude Models, Prompting & Context Engineering (13%)
- Select appropriate Claude models based on trade-offs
- Design system prompts, templates, and guardrails
- Apply prompt engineering techniques (zero-shot, few-shot, chain-of-thought)
- Optimize context windows and manage token usage
- Implement prompt reuse strategies (caching, modular prompts, Skills)

### Domain 3 — Integration (19%)
- Evaluate tool/agent configuration for capability bloat
- Analyze authentication and authorization requirements to identify security gaps
- Evaluate accuracy–latency trade-offs and justify configuration decisions
- Analyze observability challenges and select monitoring strategies at scale
- Design a RAG pipeline with appropriate chunking and indexing strategies
- Apply retrieval strategies matched to data shape and query pattern
- Evaluate connection protocols and select the appropriate integration mechanism (MCP, API/CLI, agent-to-agent)
- Evaluate progressive discovery vs. monolithic context strategy

### Domain 4 — Evaluation, Testing & Optimization (16%)
- Define evaluation metrics (accuracy, latency, cost, safety, security)
- Design evaluation datasets and test frameworks using mixed methodologies
- Conduct A/B testing and iterative improvements
- Diagnose system issues (prompt failure, hallucinations, model mismatch)
- Optimize token usage, latency, and cost-performance trade-offs
- Monitor system performance using logging and observability tools

### Domain 5 — Governance, Safety & Risk Management (14%)
- Implement guardrails and safety controls
- Identify risks, limitations, and failure modes of LLM systems
- Apply human-in-the-loop validation strategies
- Ensure compliance with regulations (e.g., GDPR, HIPAA, FedRAMP)
- Address ethical AI considerations (bias, fairness, transparency)

### Domain 6 — Stakeholder Communication & Lifecycle Management (14%)
- Conduct structured discovery and requirement gathering
- Communicate architectural decisions and trade-offs
- Manage stakeholder feedback loops and expectation alignment (including SLAs)
- Document architectures and provide implementation guidance
- Support lifecycle phases (discovery, design, handoff, monitoring, iteration)

### Domain 7 — Developer Productivity & Operational Enablement (7%)
- Configure Claude tools and environments for teams (e.g., Claude Code)
- Improve developer workflows using AI-assisted tooling
- Support debugging and operational issue resolution

## 4. Candidate profile

The exam targets a **minimally qualified candidate (MQC)**: an experienced practitioner who designs, implements, and governs Claude-powered solutions in production.

Recommended (not required — there are no mandatory prerequisites):
- Foundation in software engineering practice (modular design, separation of concerns, scalability)
- 3+ years in systems architecture or platform engineering
- 6+ months hands-on with Claude or comparable LLM systems **in production**
- Experience delivering end-to-end systems from discovery through operationalization

Explicitly **not** for: entry-level developers, casual users, or roles limited to prompt writing without system-design responsibility.

## 5. The three official sample items

These are published in the Exam Guide and are the best available signal on item style. Note that every one of them is a *diagnosis-then-choose-the-control* item, not a recall item.

**Sample 1 · Domain 3 — Integration.** A support agent can read tickets, draft replies, issue refunds, and delete accounts. Staff only need read + draft. Best least-privilege change?
→ **Remove the refund and delete tools from the agent's configuration entirely.**
*Rationale:* least privilege means removing capability the role does not need, not monitoring it. Logging is detective; confirmation prompts are compensating; model size is unrelated to authorization scope.

**Sample 2 · Domain 2 — Models, Prompting & Context.** Same 8,000-token system prompt + policy doc on every request, then a short varying user message. Latency *and* cost both matter.
→ **Put the static system prompt and policy before the dynamic content and enable prompt caching.**
*Rationale:* a stable prefix is reusable, cutting both time-to-first-token and per-request cost with no loss of required context. Truncation drops needed policy; blind downsizing risks quality; moving to few-shot does not create a cacheable prefix.

**Sample 3 · Domain 4 — Evaluation & Optimization.** RAG returns confident but wrong answers right after a document refresh; latency and model version unchanged.
→ **Investigate the retrieval/indexing step returning irrelevant or stale chunks.**
*Rationale:* the change correlates with the refresh. Broken re-index or mismatched embeddings feed bad context to a model that then sounds certain. The other options are not triggered by a document refresh.

**The pattern in all three:** the correct answer removes the root cause or addresses the thing that actually changed. Distractors add observation, add ceremony, or swap a component that was never implicated.

## 6. Exam-day rules worth knowing in advance

- Valid, unexpired **government-issued photo ID**; name must match registration exactly. Name corrections go to `certifications-support@anthropic.com` **before** scheduling.
- Accommodations must be requested and **approved by Pearson VUE before you schedule**.
- Cancel or reschedule up to **24 hours** before the appointment; inside 24 hours you forfeit the fee.
- Workspace must be clear: no notes, books, phones, smart watches, headphones, or secondary monitors. Stay in webcam view the whole session if testing online.
- You accept an NDA before the exam begins. Declining ends the session with no refund.
- Appeals go to Pearson VUE within 14 days. The standard-setting outcome and individual item content are **not** appealable.
