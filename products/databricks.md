---
title: Databricks
description: A lakehouse platform spanning data engineering, analytics, governance, machine learning, and AI.
status: seed
category: data-ai-platform
vendor: Databricks
open_source: partial
tags: [lakehouse, spark, governance, machine-learning, ai]
last_reviewed: 2026-08-05
---

# Databricks

## Fit

Databricks is a broad data and AI platform centered on the lakehouse model: durable data in lake storage and open table formats, combined with managed engineering, SQL analytics, governance, machine learning, and AI services.

## Capability contribution

- Batch and streaming data engineering.
- Governed tables, files, models, and related assets.
- SQL analytics and managed compute options.
- Machine-learning lifecycle, model serving, and generative-AI tooling.
- Orchestration, monitoring, sharing, and application-adjacent services.

## Best fit

- Organizations consolidating data engineering, analytics, and AI around a governed lakehouse.
- Large-scale transformation, historical analysis, feature preparation, and model development.
- Mixed workloads that benefit from a common catalog and data foundation.

## Poor fit or caution

- Do not assume one compute shape serves every latency, concurrency, and cost profile.
- A lakehouse does not remove the need for operational databases or specialized serving layers.
- Workspace, catalog, identity, network, and cost-governance design should precede broad adoption.
- Portability varies across data formats, SQL, notebooks, jobs, governance, and managed AI services.

## Evaluation checklist

- Separate durable-data portability from control-plane and workflow portability.
- Benchmark representative SQL, streaming, ML, and serving workloads.
- Define catalog boundaries, ownership, privileges, lineage, and environment promotion.
- Measure cost per workload and idle/operational overhead, not only peak performance.

## Related pages

- [Real-time analytics architecture](../architectures/real-time-analytics.md)

## Sources to add

Use current Databricks documentation for product names and availability; record cloud, region, runtime, and edition in all experiments.
