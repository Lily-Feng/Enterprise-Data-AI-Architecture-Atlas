# Course 5 — Team Enablement & Operational Productivity

> **Covers exam Domain 7 (7%) — ~4 items.** The smallest domain, and the shortest course (45 minutes) — but 4 items is the difference between 715 and 730.
> Original notes: [notes-original.md](notes-original.md)

**The question this course answers:** how does a team adopt a live Claude system and run it without depending on you?

Three parts: **team setup**, **developer workflows**, **operational support**.

---

## 1. Team setup is a shared configuration, decided up front

Deploy the environment as a **shared configuration**, not as individual setups that drift apart. The baseline is:

- A **shared `CLAUDE.md`** — team conventions, test commands, and constraints
- An **agreed set of tools and MCP servers**
- A **permission posture** — what runs without asking, what requires approval

> **The distinction the exam cares about:** `CLAUDE.md` contains *instructions* — Claude reads and follows them, and they can be talked around. **Settings and permissions are *enforceable*** — the harness applies them. Put conventions in `CLAUDE.md`; put anything that must hold in settings.

### `CLAUDE.md` scoping

Three scopes, all loaded and merged, **most specific wins on conflict**:

```
~/.claude/CLAUDE.md          USER scope — personal defaults across all repos
        ▼
<repo>/CLAUDE.md             PROJECT scope — repo-wide standards, test commands
        ▼
<repo>/<subpkg>/CLAUDE.md    DIRECTORY scope — rules for one module
```

**Anti-pattern:** one flat instruction blob at the root. Directory-specific rules bleed into unrelated subprojects and cause silent instruction conflicts. The fix is to scope hierarchically, not to write a longer root file.

**Related anti-pattern:** direct-executing non-trivial refactors. Enforce plan mode for architectural or multi-file changes so proposals are reviewed before files are modified.

## 2. Skills distribution — the team-scale version of reuse

Four mechanisms. They differ most in **governance and rollback**, and that is what gets tested.

| Mechanism | Best when | Governance and rollback |
|---|---|---|
| **Org-provisioned Skill**<br>(Organization settings › Skills) | A capability should reach **everyone** in the organization | Owner-managed availability and removal across the org. Users can toggle individual skills off but cannot remove them. **No version pinning or native rollback** — updates require manual re-upload. |
| **Plugin assigned to a group / org** | A procedure or tool set should reach **specific teams**, or needs governed rollout | **Strongest governance for group-scoped distribution.** Group targeting; install preferences (required / installed by default / available to users); version-controlled updates from a connected repo. |
| **Claude Code project Skill** | A tool or convention **one team** shares across its own projects | A filesystem artifact in the repo (`.claude/skills/`). Versioning follows the repository; scoped to the projects that carry it. |
| **API Skill**<br>(Messages API container) | A capability called **programmatically** by the partner's own products | Governed in the calling system; **supports explicit version pinning**. Reuse is machine-to-machine rather than human-facing. |

> **Nuance worth holding on to.** Plugins are the strongest governance option *for group-scoped distribution*, but they are **not the only mechanism with a path back to a prior version**: API Skills support explicit version pinning, and Claude Code project Skills roll back with the repository that carries them. The mechanism with no native rollback story is the **org-provisioned Skill**.

**How to choose, in one line each:**
- Everyone in the org, and you accept manual update handling → org-provisioned
- Specific teams, and you need versioned rollout with a way back → plugin
- One team, versioned with their code → project Skill
- Called by software rather than people, pinned version → API Skill

## 3. Spend posture — set before the first bill

Decide as part of team configuration, not after finance asks:

- **Model defaults** — what people get if they do not choose
- **Model allowlists and restrictions** — which models are permitted at all
- **Effort guidance** — the default effort level, and when to raise it
- **Spend, rate, and per-user caps** — hard bounds on consumption

The point is that consumption stays within bounds by construction. A per-user cap is a design decision; an overage conversation is a failure of one.

## 4. Adoption is engineered — champions, then batches

**The pattern: enable one champion per team first to prove the workflow, then seed adoption batch by batch.**

Why not a single org-wide launch:

- **Access without enablement stalls at basic chat.** People with a license and no workflow use it as a chatbot and conclude it is not that useful.
- **Lumpy adoption never standardizes the gain.** If three people get 10× and everyone else gets nothing, the team's throughput barely moves and there is no shared practice to improve.

A champion proves the workflow *in that team's actual codebase and constraints*, then carries a working example — not a generic demo — into the next batch.

## 5. Developer workflow — the verification checklist

AI-generated output is held to the same bar as human-written code, made explicit as a checklist that **gates before production**:

| Check | The bar |
|---|---|
| **Correctness** | Tests exist and pass; behavior matches the stated requirement, **including edge cases** |
| **Security** | No secrets in code; inputs are validated; tools and external calls use least-privilege access |
| **Maintainability** | Reads clearly, follows team conventions, contains no unexplained complexity |
| **Human understanding** | **The developer submitting the change can explain what the code does and why — including how it handles inputs it was not explicitly tested against** |

> **The fourth check is the distinctive one and the one most likely to be tested.** It is not about the code's quality; it is about whether a human is accountable for it. A change nobody on the team can explain is unmaintainable regardless of whether it passes tests, and it means the reviewer cannot judge the untested paths.

## 6. Operational support — translation plus self-sufficiency

The architect's operational job is **connecting symptoms to architecture causes**, then leaving behind artifacts so the team does not need you for the familiar problem.

| Artifact | Definition |
|---|---|
| **Runbook** | A captured set of known **symptom → cause → action** paths that lets the team resolve recurring operational issues without the Architect |
| **Escalation path** | A named definition of **who handles what**, and **when** an operational issue leaves the team |

**The goal, stated precisely:** the team needs you for the *new* problem, not the familiar one. Every issue you resolve for them should end with a runbook entry, or you will resolve it again.

Symptom-to-cause translation is the [Course 2 diagnosis table](../2-enterprise-integration-production/README.md#4-diagnosing-production-issues) — that table is the raw material for the runbook.

## 7. CI/CD and headless operation

Two anti-patterns, both explicitly exam-relevant:

1. **Interactive mode in a pipeline.** Claude Code in default interactive mode inside CI stalls indefinitely waiting on stdin and produces unstructured output. Run headless:
   ```bash
   claude -p "Review this PR for security vulnerabilities" --output-format json
   ```
2. **Blocking on work that can wait.** Synchronous, full-price calls for batch-friendly jobs (nightly deep PR analysis, bulk doc generation) both cost more and stall pipeline workers. Match latency to task priority: the **Batch API** gives a 50% cost reduction with up to a 24-hour turnaround.

## 8. The four things that hold across everything here

From the course recap:

1. **Team setup is shared configuration, distribution, and spend posture decided up front.** A shared baseline plus a Skills distribution approach — org-provisioned for everyone, plugins for group and org targeting with versioned updates and rollback, project Skills for one team, API Skills for programmatic reuse — all bounded by model and budget guardrails.
2. **Adoption is engineered through champions and batches.** Access without enablement stalls at basic chat; lumpy adoption never standardizes the gain.
3. **Diligence keeps AI-assisted work trustworthy.** Correctness, security, and maintainability standards, plus the requirement that the author can explain what shipped — captured as a verification checklist that gates before production.
4. **Operational support is translation plus self-sufficiency.** Connect symptoms to architecture causes, and leave behind runbooks and escalation paths.

## 9. Self-check

1. What three things make up a shared team configuration?
2. What is the difference between `CLAUDE.md` and settings, and what belongs in each?
3. Give the `CLAUDE.md` scope order and the conflict-resolution rule.
4. Name the four Skills distribution mechanisms and which one has **no** native rollback.
5. What belongs in a spend posture?
6. Why champions-then-batches rather than an org-wide launch? Give both failure modes.
7. State the four verification checks, and explain why the fourth one exists.
8. Define a runbook and an escalation path, and state the goal they serve.

## 10. Sources cited by the course

- Anthropic Skilljar, *Building with the Claude API* — tool use, API integration mechanics, baseline Skills concepts
- Claude Code configuration docs (code.claude.com) — `CLAUDE.md` instructions vs. enforceable settings, permissions, hooks, MCP, managed settings
- Claude Code Skills and organization Skills provisioning docs — Skill package structure, project Skills, plugin-based distribution, owner-provisioned org-wide availability
- Organization plugin management support docs — plugin marketplaces, group assignment, install preferences, required/default install, hide/deprecate behavior, manual upload, GitHub sync, update and removal mechanics
