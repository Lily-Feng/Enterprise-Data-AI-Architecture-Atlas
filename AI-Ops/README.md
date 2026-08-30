---
title: AIOps and log intelligence architecture
description: How log analysis pipelines are shaped by cost per record, using the LogAI library as the reference implementation.
tags: [aiops, logs, observability, opentelemetry, anomaly-detection, llm]
---

# AIOps and log intelligence architecture

Log analysis is the part of operations where the volume is genuinely adversarial. A large estate produces logs faster than anyone can read, store cheaply, or push through a model, and every architectural decision here is downstream of that one fact.

[LogAI](https://github.com/salesforce/logai) (Salesforce AI Research, 2023) is the reference implementation for this section. It is a good one precisely because of when it was built — the last coherent design of a log intelligence pipeline before language models changed what the top of it could do. Reading it now separates cleanly into two halves: the data model, the parsers and the statistical detectors, which aged well, and the representation and analysis layers, which did not.

The through-line for this section is that **cost per record, not model quality, determines the shape of the pipeline.**

## Cheap work runs on everything; expensive work runs on survivors

Drain templates a log line in microseconds. A hosted model does not. At 10⁹ lines a day `[approx]` that ratio is not a tuning consideration, it is a hard constraint that splits the pipeline in two — deterministic parsing and statistical screening on every line, metered inference only on what survives.

The practical consequence is counterintuitive: per-template counters and ETS baselines are not the legacy tier that a model replaces. They are the tier that buys the model its budget, and their pass-through rate is the number that decides whether the expensive tier is affordable at all.

## The correlation keys are usually declared and rarely used

The OpenTelemetry log record carries `TraceId` and `SpanId`, and most pipelines — LogAI included — define those fields and then never join on them. A model reasoning over log text alone is guessing at causes it structurally cannot see. What makes an investigation tier worth its cost is that its context is a join across traces, metrics, deploy events, call sites and prior incidents, on keys that only exist if the estate is instrumented for them.

## Scores are not answers

An anomaly score hands an on-call engineer a number and no next step. The output of the expensive tier should be a narrative that cites the records it rests on, names the suspect change, and proposes the next check. This is the same constraint that governs any investigation agent, and it is covered from the agent's side in [agentic operations architecture](../agentic-ops/).

## Topics

- [Cost-tiered log analysis](cost-tiered-log-analysis.md) — the five-stage funnel, where the cost boundary sits, the cross-signal join, and a component-by-component verdict on LogAI v0.1
- [LogAI rewrite plan](LogAI-Rewrite-Plan.md) — thesis, research questions, paper structure and execution phases for a successor paper to the 2023 technical report

The two are different documents about the same subject. The rewrite plan is the research programme — what a successor paper should claim, evaluate and refuse to claim. The topic note is the architecture as this Atlas records it: topology, wiring, and what survives from v0.1. Where they disagree, the rewrite plan is the more considered source.

## Sources

- [`LogAI.pdf`](LogAI.pdf) — Cheng, Saha, Yang, Liu, Sahoo and Hoi, *LogAI: A Library for Log Analytics and Intelligence*, [arXiv:2301.13415](https://arxiv.org/abs/2301.13415)
