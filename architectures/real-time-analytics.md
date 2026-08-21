---
title: Real-time Analytics
description: A reference architecture for turning continuously changing operational data into low-latency insight and action.
status: seed
tags: [real-time, streaming, olap, operational-analytics]
last_reviewed: 2026-08-05
---

# Real-time Analytics

## Goal

Serve fresh, high-concurrency analytics over events and changing dimensions while preserving correctness, observability, replay, and a path to governed action.

## Reference flow

```text
Operational sources → CDC/events → durable event log → stream processing
                                              ├→ real-time analytical store → APIs/dashboards/alerts
                                              └→ lakehouse history → batch correction/ML/replay
Dimension sources  ─────────────────────────────→ enrichment/cache
Decisions → governed workflow → system of record → outcome event
```

## Component responsibilities

| Layer | Responsibility | Important choices |
|---|---|---|
| Capture | Represent changes as durable, ordered events | CDC vs. application events; schema contracts |
| Transport | Buffer, partition, retain, and replay | ordering key; retention; delivery semantics |
| Processing | Validate, enrich, aggregate, and detect | event time; state; late data; idempotency |
| Serving | Filter and aggregate with low latency | ingestion mode; indexes; rollups; upserts |
| History | Preserve complete, economical evidence | open formats; compaction; batch reconciliation |
| Consumption | Deliver context to people and software | APIs; dashboards; alerts; concurrency controls |
| Action | Apply decisions safely | approval; policy; audit; retries; compensation |

## Quality attributes to make explicit

- End-to-end freshness target, not only database ingestion latency.
- Query latency at expected concurrency and data skew.
- Correctness under duplicates, late events, updates, and deletion requests.
- Recovery point, recovery time, replay duration, and degraded behavior.
- Cost per ingested event and per query at representative load.
- Operator effort: deployments, schema changes, incidents, and capacity planning.

## Product mapping

[Apache Pinot](../products/apache-pinot.md) is a candidate serving layer for high-concurrency, low-latency analytics. [Databricks](../products/databricks.md) can provide durable history, transformation, governance, and ML. [Couchbase](../products/couchbase.md) can serve operational application state.

## Failure modes

- Calling a dashboard “real time” without defining an end-to-end freshness SLO.
- Dual-writing to multiple stores without an outbox, CDC, or reconciliation path.
- Ignoring late events and mutable dimensions until production.
- Using the serving store as the only historical record.
- Benchmarking uniform synthetic queries that hide skew and concurrency collapse.

## Validation plan

1. Define business scenarios and measurable freshness/correctness SLOs.
2. Generate duplicates, out-of-order events, schema evolution, and hot keys.
3. Load realistic query mixes at target concurrency.
4. Test replay, backfill, region/zone loss, and dependency degradation.
5. Record raw results and limitations in a [learning note](../notes/README.md).
