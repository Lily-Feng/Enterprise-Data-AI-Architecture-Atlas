# Claude Certified Architect · Professional — Study Guide

A complete, self-contained study guide for the **CCAR-P** exam, organized around the five courses in the
[Anthropic Partner Academy learning path](https://anthropic-partners.skilljar.com/path/claude-certified-architect-professional).

Built from course notes, the official exam guide, and Anthropic platform documentation. Open to anyone who wants to use it.

---

## Start here

**Preparing for the exam?** Read [`cram-sheet.md`](cram-sheet.md) first to see the shape of the whole thing, then work
the five course folders in order, then take the mock exam.

**Short on time?** The cram sheet plus [`mock-exam/`](mock-exam/) in Practice mode will get you further than anything else here.

**Just want to practise?** Open [`mock-exam/index.html`](mock-exam/index.html) in a browser. 63 items, no setup.

---

## Contents

### The five courses

| # | Course | Exam domains | Weight | Guide |
|---|---|---|---:|---|
| 1 | **Claude Platform & Solution Design** | 1, 2 | 30% | [→](1-platform-solution-design/README.md) |
| 2 | **Enterprise Integration & Production** | 3, 4 | 35% | [→](2-enterprise-integration-production/README.md) |
| 3 | **Responsible AI, Safety & Risk** | 5 | 14% | [→](3-responsible-ai-safety-risk/README.md) |
| 4 | **Stakeholder Engagement, Lifecycle & GTM** | 6 | 14% | [→](4-stakeholder-engagement-lifecycle-gtm/README.md) |
| 5 | **Team Enablement & Operational Productivity** | 7 | 7% | [→](5-team-enablement/README.md) |

Each folder holds a `README.md` study guide and the `notes-original.md` it was built from.

### Cross-cutting references

| File | What it is |
|---|---|
| [`cram-sheet.md`](cram-sheet.md) | One page. Every decision table and answer shape. Read this last, before the exam. |
| [`exam-blueprint.md`](exam-blueprint.md) | Domains, weights, scoring, logistics, and the three official sample items worked through |
| [`platform-reference.md`](platform-reference.md) | Claude platform facts an architect is assumed to know: models, caching, batch, tools, MCP, context, compliance surfaces |
| [`glossary.md`](glossary.md) | Every term across the five courses |
| [`field-guide-agentic-engineering.md`](field-guide-agentic-engineering.md) | Patterns and anti-patterns for agentic engineering, from a talk on the CCA exam as a curriculum |
| [`mock-exam/`](mock-exam/) | 63-item interactive practice exam — open `index.html` in a browser |
| [`assets/`](assets/) | The official exam guide PDF |

---

## The exam in one table

| | |
|---|---|
| Code | CCAR-P |
| Items | 63, multiple-choice and multiple-response |
| Time | 120 minutes (~1:54 per item) |
| Pass | **720** on a 100–1,000 scale |
| Fee | $175 USD |
| Valid | 12 months, free renewal assessment before expiry |
| Retakes | 14 / 30 / 90 days; max 4 per rolling year |

Full details in [`exam-blueprint.md`](exam-blueprint.md).

---

## Where the weight is

```
Domain 3  Integration                    ███████████████████  19%
Domain 1  Solution Design                █████████████████    17%
Domain 4  Evaluation & Optimization      ████████████████     16%
Domain 5  Governance, Safety & Risk      ██████████████       14%
Domain 6  Stakeholder & Lifecycle        ██████████████       14%
Domain 2  Models, Prompting & Context    █████████████        13%
Domain 7  Developer Productivity         ███████               7%
```

**Domains 1 + 2 + 3 = 49% of the exam**, all covered by Courses 1 and 2. If you study nothing else, study those.

**Domains 5 + 6 = 28%** and are the cheapest points on the exam — the correct answers have a predictable shape
(layer the controls, name the owner and the evidence artifact, diagnose before fixing, roll out gradually with rollback).

---

## A suggested plan

| Phase | Do this |
|---|---|
| **1. Orient** | Read [`exam-blueprint.md`](exam-blueprint.md) and work the three official sample items. Note *why* each distractor loses. |
| **2. Learn** | Work Courses 1 → 5 in order. Each guide ends with a self-check; do not move on until you can answer it from memory. |
| **3. Fill gaps** | Read [`platform-reference.md`](platform-reference.md) end to end. This is where the recall-flavored items live. |
| **4. Drill** | [`mock-exam/`](mock-exam/) in **Practice** mode, one domain at a time. Read every explanation, including on items you got right. |
| **5. Simulate** | **Full exam** mode, timed, one sitting. Then retry the missed items. |
| **6. Cram** | [`cram-sheet.md`](cram-sheet.md) the morning of. |

---

## How the exam actually thinks

Every item is a production scenario, not a definition. Three of the four options are usually one of these:

- **Observe instead of prevent** — "add logging" where the capability could have been removed
- **Add ceremony instead of removing the cause** — "add a confirmation prompt"
- **Swap a component nothing implicated** — "use a larger model"
- **Do the thing that sounds advanced** — "make it multi-agent"
- **A partial answer** — the right idea with a clause missing

The winning answer **removes the root cause, addresses the thing that actually changed, layers a control instead of
relying on one, or names an owner and an artifact.** When two options both look right, pick the **more complete** one.
