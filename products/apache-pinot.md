---
title: Apache Pinot
description: A distributed OLAP serving system designed for fresh data, low-latency queries, and high concurrency.
status: seed
category: real-time-olap
vendor: Apache Software Foundation project
open_source: true
tags: [real-time-analytics, olap, streaming]
last_reviewed: 2026-08-05
---

# Apache Pinot

## Fit

Apache Pinot is an analytical serving layer optimized for user-facing and operational analytics over streaming and batch data. Its core value is predictable low-latency filtering and aggregation at scale, including on newly arriving events.

## Architecture in one view

Pinot separates ingestion and serving concerns across controllers, brokers, servers, and minions. Tables are split into immutable or mutable segments, distributed across servers, and queried through brokers. Streaming ingestion commonly consumes a partitioned event log; batch ingestion builds segments from historical data.

## Capability contribution

- Near-real-time and batch ingestion into the same query surface.
- Columnar storage, partitioning, indexes, star-tree pre-aggregation, and approximate functions.
- Horizontal scaling for throughput and concurrency.
- Upsert support for selected mutable-event use cases.

## Best fit

- User-facing analytics with strict latency and concurrency targets.
- Operational dashboards and anomaly investigation over fresh events.
- High-volume event data with known filter and aggregation patterns.

## Poor fit or caution

- General-purpose transactional workloads and multi-row transactions.
- A sole durable system of record for enterprise history.
- Workloads dominated by unconstrained joins or unpredictable ad hoc exploration.
- Teams unwilling to model tables, segments, indexes, and partitioning for access patterns.

## Evaluation checklist

- Test the real query mix, concurrency, skew, cardinality, and freshness target.
- Validate late events, upserts, deletes, reprocessing, and schema evolution.
- Measure segment size, index overhead, broker fan-out, and hot partitions.
- Plan deep-store durability, retention, backup, replay, and operational ownership.

## Related pages

- [Real-time analytics architecture](../architectures/real-time-analytics.md)

## Sources to add

Validate implementation details against the current Apache Pinot documentation and record the tested version in labs and benchmarks.
