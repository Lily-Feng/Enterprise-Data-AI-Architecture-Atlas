---
title: Cross Connect
description: Infrastructure architecture — how enterprise networks, GPU fabrics, and AI agents are actually set up, connected, and tuned.
tags: [infrastructure, architecture, networking, gpu, agentic-ops]
---

# Cross Connect

A cross connect is the cable in a colocation facility joining your cage to a carrier or a cloud on-ramp — the point where two systems designed separately have to physically meet.

This is a knowledge base about those points: how infrastructure is **set up, connected, and tuned**, rather than how any individual system works inside.

It's the infrastructure counterpart to [Calm Data and AI](https://github.com/Lily-Feng/Calm.Data.and.AI), which covers data and AI from the software perspective — the concepts, the algorithms, how a thing works internally. Here the subject is topology, integration, and the knobs.

## [Hybrid network architecture](hybrid-network/)

Enterprise on-premise networks joined to cloud. Addressing, transit topology, routing, naming, identity federation — and why the transport almost always works while the integration almost always doesn't.

- [DNS across the on-prem/cloud boundary](hybrid-network/dns-across-the-boundary.md)

## [AI infrastructure architecture](ai-infra/)

The memory and interconnect hierarchy that governs GPU cluster design: HBM, NVLink and NVSwitch, InfiniBand fabrics, rail alignment, and topology-aware scheduling. The through-line is that parallelism strategy is a wiring decision wearing a software costume.

- [Mapping parallelism onto the interconnect hierarchy](ai-infra/parallelism-to-interconnect.md)

## [Agentic operations architecture](agentic-ops/)

What changes structurally when an AI agent becomes a principal in your infrastructure — permission accumulation, context budgets against unbounded telemetry, and the difference between fluency and calibration. [HolmesGPT](https://github.com/HolmesGPT/holmesgpt) as the reference implementation.

- [Toolset scoping and the read/write boundary](agentic-ops/toolset-scoping.md)

## [AIOps and log intelligence architecture](AI-Ops/)

Log analysis at a volume that is genuinely adversarial. Cost per record, not model quality, determines the shape of the pipeline: deterministic parsing and statistical screening on every line, metered inference only on what survives. [LogAI](https://github.com/salesforce/logai) as the reference implementation.

- [Cost-tiered log analysis](AI-Ops/cost-tiered-log-analysis.md)

## Reference

- [Glossary](glossary.md) — terms as they're used when you're wiring something

---

Figures marked `[verify: DATE]` come from documentation rather than a confirmed run; `[approx]` means order-of-magnitude. Configurations are reconstructed generically — invented addresses and names throughout.

[Apache License 2.0](LICENSE).
