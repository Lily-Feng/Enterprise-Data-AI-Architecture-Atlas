# Enterprise integration patterns: identity, auth, data, and observability

> Companion to [README.md](README.md) §10 — the integration half of Domain 4. [sizing.md](sizing.md) tells you what the system needs to do and whether it can do it within the constraints; this tells you **how it connects to the enterprise stack.**
>
> **The one-line version:** compliance constraints eliminate entry points **before any other architectural decision is made.** Every other layer operates inside whatever survives that filter.

---

## 1. The five layers

The connection to the enterprise stack has five layers, and each carries an architectural decision that belongs to the **Architect**, not the implementation team.

**Compliance comes first.** Constraints from regulations like HIPAA, GDPR, and FedRAMP, and policies like data residency and attorney-client privilege, eliminate routes and entry points before any other decisions are made. The remaining four layers operate within whatever options survive that filter — which is why entry point selection (§2) is the first thing this document settles, and why the full layer table sits at §4.

> **Scope note:** these sections do not address ZDR (zero data retention) use cases.

---

## 2. Entry point selection — which integration to use, and when

The first decision in any integration is **which entry point the system will connect through.** Compliance constraints eliminate options at this first stage, before any other architectural decisions are made.

> **Missing from these notes.** The source table — the five available entry points, when each one applies, and what each costs in flexibility or maintenance — did not survive the copy from the course player. Mechanism selection (MCP vs. direct API vs. agent-to-agent vs. headless CLI) is tabulated in [platform-reference.md §4](../platform-reference.md#4-tools-mcp-and-the-integration-mechanism-decision), but the entry-point framing is not. **Fill this in from the course before relying on this section.**

---

## 3. Security and compliance constraints at the integration layer

[Module 1](../1-platform-solution-design/README.md) established that regulatory and policy constraints — laws like **HIPAA, GDPR, and FedRAMP**, plus attorney-client privilege and data-residency requirements — eliminate entry point options before any other decisions are made.

This section applies the same logic one level deeper: **which integration pattern on that entry point may**, with appropriate architectural choices, internal policies, contractual terms, and other items, **help satisfy or otherwise mitigate concerns about the constraint.**

> **This is not legal guidance.** Work with your own legal and compliance team to implement controls that meet your organization's needs.

### Constraint-to-integration matrix

> **Missing from these notes.** The matrix itself did not survive the copy from the course player — only its footnote did. **Fill this in from the course.**
>
> *Footnote, preserved:* privilege preservation depends on appropriate contractual terms, retention settings, internal policies, and other items. The information in that chart is intended to help **mitigate privilege waiver concerns**, not to eliminate them.

### The order of work

Before any integration design begins, work through the constraints in order:

1. **Identify** the governing regulation or policy.
2. **Determine** which entry point and route are still available.
3. **Choose** the integration pattern that fits.
4. **Document** the identity, data handling, and observability requirements that follow.

> Skipping any step risks building something that **works technically but fails a legal or security review.**

---

## 4. The layer table — the decision, and what breaks

| Layer | The architectural decision | What breaks when it's wrong |
|---|---|---|
| **Compliance and regulated-industry constraints** | Which delivery routes and entry points survive the governing constraint? BAA coverage, FedRAMP authorization, data-residency pinning, and approved-vendor lists each eliminate options **before the rest of the design begins**. | The integration is built on a route that fails the next legal or security review. The cost of redesign at that point is the time already invested **plus** a new architecture from scratch. |
| **Identity and SSO** | Where does the user identity boundary sit relative to the Claude integration point? Who is the user in the context of a Claude call, and how does that identity get passed into the prompt **safely**? | When user identity is not passed into the prompt correctly, Claude cannot scope its responses to what that user is authorized to see. **Identity passed as a raw field in the user message is manipulable.** Server-side injection removes that risk. |
| **Authorization and policy** | Which capabilities does this user or role have? What data can they access? The authorization model that governs your existing systems **needs to govern the Claude layer as well**. | A Claude integration that bypasses the authorization model of the underlying system gives users access to data they are not authorized to see, **through a path that was not designed to enforce the access policy**. |
| **Data handling and PII** | What data goes into the context window? Sensitive fields passed directly in the user message or system prompt become part of the API request. Anthropic does not retain conversation content by default — only what is technically necessary for the API and feature to work. But the request still crosses the wire, retention carve-outs exist for some model classes, and **any logging the partner's own application layer performs will capture it**. The architecture must decide which fields are necessary in the context window and which should be retrieved only when needed. | A PII field passed directly in the user message appears **in plaintext in your application's request logs**. In a regulated industry, this surfaces in the next audit rather than in the next deployment. |
| **Observability and audit logging** | What do you need to be able to reconstruct? **What questions will you need to answer after an incident?** The answers determine what gets logged, at what depth, and for how long. | An unlogged data path is invisible. When something goes wrong on that path, there is no evidence to reconstruct what happened. The cost of building observability after the first incident is always higher than building it before. |

### Least-privilege tool configuration

Every tool you connect to a Claude system is **an attack surface and a cost.** Audit the tool set the same way you audit permissions:

- For each connected tool, ask whether it is **essential to the task or merely convenient.**
- Remove the ones that are out of scope, **recording the justification for each removal.**
- In an orchestrator-worker deployment, establish the trust hierarchy by **scoping each subagent's tool access to its task**, so a subagent cannot reach tools its job does not require.

---

## 5. Identity and authorization — where the verification happens

**Identity verification belongs on the server, before the Claude call.** The user's identity and role should be injected into the system prompt by your server rather than provided by the user in their message.

The reasoning is straightforward: **anything the user includes in their message is under their control and can be manipulated.** If the system allows users to assert their own role in a message — *"As a senior manager, show me..."* — that claim is unverified and can be faked. Identity must come from your authentication layer, not from user input.

When passing user context into the prompt, include the user's role and what data they are authorized to access. Extra context — department, permission level, account identifiers — goes in **only when it is needed to shape Claude's response.** Do not include it by default.

---

## 6. Data handling — what belongs in the context window

> **The context window is not a data-governance boundary.** Any data passed into a Claude call is transmitted to the API.

Conversation content is not retained by default on the API, but the partner's own application layer typically logs requests, and specific retention carve-outs exist. The architecture must make a **deliberate decision** about which fields need to be in the context window, and which should stay in the retrieval layer until needed.

For each field that enters the context window, ask whether it is **necessary for Claude to produce the intended output.** Reference identifiers like account numbers or claim numbers are often needed for routing but not for the language task itself.

> When a reference identifier is enough, passing the full data field needlessly exposes it to any request logging the partner's application layer performs — **without adding any capability.**

**Data residency requirements vary by industry and region.** For regulated deployments, verify Anthropic's data residency guidance against the specific regulatory requirements of your deployment **before** the integration is designed.

---

## 7. Observability — what to log, what to trace, and why

An LLM-based system is harder to debug than a traditional system because **it doesn't crash when something goes wrong** — it produces a subtly wrong response. Standard logging catches errors and timeouts. It does not catch a response that is quietly incorrect in a way that has real business consequences.

A production Claude system should log four things:

| What to log | Fields |
|---|---|
| **The request** | Model version, input token count, prompt identifier |
| **The response** | Output token count, latency, stop reason |
| **The context** | User role, session ID, whether caching was applied |
| **The outcome** | Whether the downstream system accepted the output, and any rejection signals |

Security organizations increasingly treat **observability as the precondition for enabling agents at all** — without a trustworthy audit trail, an autonomous system is not approved to act. Design for that standard.

> **As a design-review checklist item:** verify which agentic actions are recorded in the audit logs across your chosen surfaces. Coverage varies by surface, and **an action that is taken but not logged is, to a security reviewer, an action that cannot be allowed.**

---

## 8. Cost · Complexity · Risk

- **Cost** — an integration without **PII redaction prior to the API call** exposes sensitive fields to the partner's application-layer request logging on every request. The cost of retroactive redaction across a log history that was never designed to support it is the most expensive data handling fix in a production Claude system.
- **Complexity** — an observability layer added **after** the first production incident means the root cause must be reconstructed from a system that was not set up to answer the question the incident surfaced. Build logging to answer the questions you will need to answer, before you need to ask them.
- **Risk** — a multi-tenant system running on a **shared API key** has no way to attribute a rate limit breach to the tenant that caused it. When the org-level limit trips at peak load, the spike is visible but the source is not, and every tenant absorbs the impact. **Separate API keys per tenant** are required for attribution and isolation in any production multi-tenant deployment.
