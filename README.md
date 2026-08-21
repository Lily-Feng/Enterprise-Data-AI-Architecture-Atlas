---
title: Enterprise Data & AI Architecture Atlas
description: A capability-first field guide to modern cloud data platforms, with Snowflake and Databricks as the primary architectural anchors.
status: active
last_reviewed: 2026-08-20
---

# Enterprise Data & AI Architecture Atlas

Understand enterprise data and AI systems by decomposing modern cloud platforms into reusable architectural capabilities—and comparing how Snowflake and Databricks implement those patterns.

This repository is a personal, docs-as-code learning project. Snowflake and Databricks are the primary focus areas: the Atlas starts with capabilities such as warehousing, lakehouse design, governance, data sharing, real-time analytics, and AI-assisted operations, then studies how these platforms implement them in practice.

There is no daily publishing schedule and no expectation that every section grows at the same pace. Work on one question at a time. A short learning note is a complete contribution; larger articles and labs are optional follow-ups.

## A simple way to start

1. Pick one question you want to understand.
2. Capture what you learn with the [learning-note template](templates/learning-note.md).
3. Stop there, or connect the note to a more durable page when you have the interest and evidence.

The main places to explore are:

| Goal | Go to |
|---|---|
| Capture a question or useful source | [Notes](notes/README.md) |
| Learn an idea or platform capability | [Concepts](concepts/README.md) and [Capabilities](capabilities/README.md) |
| See the idea in a system or product | [Architectures](architectures/README.md) and [Products](products/README.md) |
| Test a claim | [Labs](labs/README.md) |
| Record a decision or rationale | [Thinking](thinking/README.md) |

Featured starting points:

- [Snowflake overview](products/snowflake.md)
- [Databricks overview](products/databricks.md)
- [Ontology capability](capabilities/ontology.md)
- [Real-time analytics architecture](architectures/real-time-analytics.md)

## Knowledge model

```text
Question → Learning note → Connected page → Optional experiment
```

Notes preserve early learning. Concepts and capabilities explain reusable ideas. Architectures and products connect those ideas to real systems. Labs add evidence, while thinking pages record rationale. Not every note needs to move through every stage.

## Editorial conventions

Every durable article begins with YAML front matter:

```yaml
---
title: Human-readable title
description: One-sentence scope and value
status: seed # seed | draft | reviewed | mature | archived
tags: [lowercase, kebab-case]
last_reviewed: YYYY-MM-DD
---
```

Product pages also record `category`, `vendor`, and `open_source`. Architecture decisions use `decision_status`. Prefer evidence over feature lists, link related pages using relative links, distinguish fact from opinion, and include sources and a review date for time-sensitive claims.

## Repository map

```text
concepts/          foundational ideas, independent of tools
capabilities/      outcomes a platform must enable
architectures/     end-to-end reference architectures
products/          product analyses and capability mappings
labs/              reproducible hands-on exercises
thinking/          ADRs, principles, and synthesis essays
notes/             lightweight learning notes and source trails
templates/         article templates and contribution scaffolds
```

See the [glossary](glossary.md) and [contribution guide](CONTRIBUTING.md).

## Scope and independence

This is an independent learning project. Snowflake and Databricks are the main platform lenses, while other tools remain comparative references. Product names and trademarks belong to their respective owners. Descriptions should be based on public information and hands-on evidence; the goal is to learn transferable architecture, not to reproduce proprietary software or imply vendor affiliation.

## License

The repository already includes the [Apache License 2.0](LICENSE). Contributions are accepted under that license unless stated otherwise.
