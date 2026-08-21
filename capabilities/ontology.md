---
title: Ontology
description: A governed operational model that connects enterprise data to business objects, relationships, policies, and actions.
status: seed
tags: [ontology, semantic-layer, knowledge-graph, operational-workflows]
last_reviewed: 2026-08-05
---

# Ontology

## Why it matters

Tables describe how data is stored; an ontology describes the world the organization operates. It gives people, applications, and AI systems a shared model of objects such as Customer, Order, Plant, Aircraft, and Claim—plus their relationships, policies, derived state, and allowed actions.

## Capability boundary

An enterprise ontology typically provides:

1. **Object model:** typed objects, properties, identities, and relationships.
2. **Data binding:** mappings from source records and transformations to object state.
3. **Logic:** computed properties, constraints, metrics, and lifecycle rules.
4. **Security:** policy evaluated using user, object, purpose, and context.
5. **Actions:** governed mutations such as approve, reroute, assign, or notify.
6. **Interfaces:** consistent APIs and events for apps, analytics, automation, and AI.
7. **Evolution:** versioning, ownership, lineage, testing, and migration.

## What it is not

- A semantic layer usually standardizes analytical meaning but may not model operational actions.
- A knowledge graph emphasizes graph representation and reasoning but may not bind to governed workflows.
- A digital twin emphasizes state and behavior of a physical or logical system.

These can be ingredients of an ontology capability; the boundaries depend on the use case.

## Open implementation shape

| Responsibility | Possible building blocks |
|---|---|
| Object schemas and contracts | JSON Schema, Protobuf, Avro, OpenAPI |
| Storage and identity | relational/JSON stores, graph databases, lakehouse tables, entity resolution |
| Transformations and lineage | dbt, Spark, Flink, OpenLineage-compatible tooling |
| Metrics and semantics | semantic-layer tools and governed SQL models |
| Policy | policy engines, catalog permissions, application authorization |
| Actions and workflows | APIs, workflow engines, event buses, transactional outbox |
| Search and AI context | search indexes, vector stores, graph retrieval, tool APIs |

No single component creates the capability. The hard part is maintaining identity, meaning, policy, and actions consistently across boundaries.

## Maturity model

- **Level 1 — vocabulary:** shared names and definitions.
- **Level 2 — governed objects:** stable identity, ownership, and mapped data.
- **Level 3 — reusable interfaces:** objects power multiple applications and analyses.
- **Level 4 — actions:** policies and workflows safely change operational state.
- **Level 5 — adaptive operations:** decisions and outcomes feed models and process improvement.

## Key design questions

- Where is object identity resolved, and how are merges reversed?
- Which system remains authoritative for each property and action?
- How are schema and policy changes tested against existing applications?
- Can a user understand why an object, recommendation, or denied action exists?
- How are writes made idempotent, auditable, and recoverable?

## Failure modes

- Rebranding a set of tables as an ontology without ownership or action semantics.
- Creating one universal model that cannot evolve at domain speed.
- Hiding source lineage behind convenient objects.
- Letting AI invoke actions without explicit policy, preview, approval, and audit.
- Treating ontology design as a one-time modeling project rather than a product.

## Related pages

- [Palantir](../products/palantir.md)
- [Real-time analytics](../architectures/real-time-analytics.md)
- [Architecture pattern template](../templates/architecture-pattern.md)

## Sources to add

Prioritize public product documentation, standards, implementation evidence, and comparisons with semantic-layer and knowledge-graph approaches.
