# Glossary

Terms used across the five courses, alphabetical. Terms marked **†** are defined verbatim or near-verbatim in the course material.

---

**A/B testing** — Comparing two configurations on live traffic with everything else held constant, a success metric and minimum detectable effect defined in advance, and results segmented rather than averaged.

**Adaptive thinking** — The current mechanism for extended reasoning: Claude decides when and how much to think. Replaces the deprecated fixed `budget_tokens` budget. Depth is controlled with `effort`.

**Agentic pattern** — An architecture in which the model drives a loop: act, observe the result, correct, iterate — as opposed to a workflow, where code drives the sequence. Agency comes from the loop, not from the prompt.

**Architecture Decision Record (ADR)** † — A record capturing the context, the options considered, the decision, the reasons for it, and its consequences. The artifact that stops a team re-litigating or repeating a decision after the architect leaves.

**Augmented LLM** — A single model call extended with retrieval, tools, or both, where the application still controls the flow.

**Batch API** — Asynchronous message processing at a 50% cost reduction with up to a 24-hour turnaround. Results return in arbitrary order and must be keyed by `custom_id`.

**Business Associate Agreement (BAA)** — The HIPAA contract that must cover *the specific services and settings in use*. Coverage does not transfer to a service added later or a setting outside the agreement.

**Capability bloat** — Accumulating tools on one agent past the point where tool-selection accuracy degrades (roughly 4–5 tools). Fixed by removal, specialization, or deferred tool loading.

**Champion-per-department rollout** † — An adoption pattern that enables one champion per team first to prove the workflow, then seeds adoption batch by batch.

**Chunking** — Splitting source documents into retrievable units. Strategy follows the shape of the data: semantic boundaries for prose, one record per chunk for structured data, function boundaries for code, header-preserved rows for tables.

**`CLAUDE.md`** — A file of *instructions* Claude reads and follows. Loaded and merged across three scopes — user (`~/.claude/`), project (`<repo>/`), and directory (`<repo>/<subpkg>/`) — with the most specific rule winning on conflict. Distinct from settings, which are enforceable.

**Compaction** — Summarizing earlier conversation context when it approaches a threshold (default ~150K tokens) so a long session can continue. Distinct from context editing, which *clears* rather than summarizes.

**Confidence is not validity** † — Claude can state an incorrect answer with the same fluent, authoritative tone as a correct one. The reason verification and human-in-the-loop are architectural requirements rather than afterthoughts.

**Context editing** — Clearing old tool results or thinking blocks from the conversation before the model sees it. Removes content rather than condensing it.

**Context window as a finite resource** † — The context window is a hard boundary with a strict token budget. What you include, what you omit, and the *order* of information all affect both capability and cost.

**Defense in depth** — Layering input screening, system prompt, tool permissions, output screening, and monitoring so that one control missing does not lead to harm. A single control is a single point of failure.

**Degraded mode** — The defined behavior of the system when a dependency is unavailable. Part of the SLA, not an afterthought.

**Escalation path** † — A named definition of who handles what and when an operational issue leaves the team.

**Eval suite** — The set of graded test cases that defines acceptance criteria and gates every change. Written before code, grown by every production incident.

**Fail closed** — Denying or degrading when a control cannot run, rather than proceeding. The opposite — skipping a check because the checker is unavailable — is a control that does not exist.

**Fan-in coverage check** — The rule that the number of results collected must equal the number of units dispatched in a fan-out, so a missing subagent result triggers a retry or a surfaced gap rather than a confident partial synthesis.

**FedRAMP** — U.S. federal cloud authorization program. Authorization attaches to a specific service offering, in a specific boundary, at a specific impact level — so the architect confirms the exact deployment path (platform, region, and service), never "the vendor."

**Few-shot prompting** — Supplying worked examples in the prompt. Right when output format or edge-case handling is hard to describe but easy to demonstrate; the examples belong in the cacheable prefix.

**Grading ladder** — The rule that grading method escalates only when behavior demands it: code-based grading wherever possible, LLM-as-judge when interpretation is required, human grading as a last resort.

**Grounding** — Constraining answers to retrieved sources, requiring each citation to point to one of those sources, automatically verifying that each cited item exists, and permitting the model to say it cannot find support.

**Hub-and-spoke** — The multi-agent topology in which a coordinator dispatches to narrow, specialized subagents with minimal toolsets and isolated context slices.

**Human-in-the-loop (HITL)** — Human approval placed where reversibility, impact, or confidence demand it. Calibrated: required for high-impact or irreversible actions, with low-risk actions running automatically and a sample of them audited.

**LLM-as-judge** — Using a model to grade outputs requiring interpretation. Trustworthy only with detailed rubrics, constrained verdicts, calibration against human-labeled examples, and a different model than the one being evaluated.

**Least privilege** — Removing capability a role does not require, rather than monitoring or guarding it. Removal is preventive; logging is detective; confirmation is compensating.

**Lost in the middle** — Degraded recall of information positioned in the middle of a long context. A reason ordering matters and context grows bounded.

**Managed Agents** — The surface where Anthropic runs the agent loop *and* hosts a per-session sandbox, with persisted, versioned agent configurations. Contrast with Tool Runner and the Claude Agent SDK, which supply a harness but leave deployment to you.

**MCP (Model Context Protocol)** — A standard protocol for exposing a capability as a server that multiple clients can use. Chosen for reuse across clients and teams and for a governed, auditable boundary; its cost is that each server is an authorization surface.

**Minimum necessary** — The HIPAA principle that only the PHI needed for the task is used. An architecture constraint on what you put in a prompt, what you retrieve, and what you log.

**Monolithic context** — Loading everything the agent might need up front. Simple and cache-friendly for a small stable corpus; saturating and expensive at scale. Contrast progressive discovery.

**Non-determinism** † — The same input can yield different outputs across runs. You cannot certify behavior from a single successful observation, which makes robust evaluation frameworks mandatory.

**Progressive discovery** — Loading a small index and retrieving detail on demand rather than loading everything up front. The default at enterprise scale.

**Prompt caching** — Reuse of a stable request prefix to cut both time-to-first-token and per-request cost. Prefix-match, rendered `tools → system → messages`, maximum four breakpoints, model-scoped. Verified through `usage.cache_read_input_tokens`.

**Prompt injection** — Untrusted content in the context attempting to act as instructions. Countered by treating all read content as data, constraining the tool surface during untrusted processing, and gating irreversible actions on human approval.

**Reranking** — A second-pass scoring of retrieved candidates to improve precision when recall is adequate but ordering is poor.

**Runbook** † — A captured set of known symptom-to-cause-to-action paths that lets a team resolve recurring operational issues without the Architect.

**Shared configuration** † — A single team baseline (for example a project `CLAUDE.md`, agreed tools, and a permission posture) that every member starts from, instead of individual setups that drift apart.

**Skill** — A packaged, reusable set of instructions and resources Claude loads when a task matches. The reuse unit above a prompt and below an agent.

**Skills distribution** † — Getting a Skill in front of the right people through one of four mechanisms with different access, versioning, and rollback behavior: org-provisioned Skills for organization-wide availability; plugins assigned to a group or org for scoped distribution with install preferences, version-controlled updates, and rollback; Claude Code project Skills versioned with the repository and scoped to a team; and API Skills called programmatically with explicit version pinning.

**Spend posture** † — The model defaults, model allowlists and restrictions, effort guidance, and spend, rate, and per-user caps set as part of team configuration to keep consumption within bounds.

**`stop_reason`** — The field an agentic loop branches on. `tool_use` means execute the tool, append the result, and continue; `end_turn` means the model is done and the confidence or authorization gate applies.

**Structured output** — Constraining the response to a schema via `output_config.format` or `strict: true` tool definitions, followed by programmatic validation. Replaces free-form generation plus regex parsing.

**Tool search / deferred loading** — Marking tools `defer_loading: true` and letting Claude retrieve the ones it needs, so a large tool catalog does not occupy every request's prefix. The search tool itself and at least one other tool must remain non-deferred.

**Transformation** — The business value pillar meaning something becomes possible that was not possible before. Distinct from efficiency and cost, which are about doing existing work faster or cheaper.

**Verification checklist** † — The explicit set of correctness, security, maintainability, and human-understanding checks AI-generated output must pass before production.

**Workflow pattern** — Multi-step processing where code, not the model, controls the sequence. Cheaper, faster, and more testable than an agent, and the correct choice whenever the steps are knowable in advance.

**Workload identity federation** — Authenticating a service to the API through a short-lived federated token rather than a long-lived API key. The answer when a client refuses long-lived secrets.
