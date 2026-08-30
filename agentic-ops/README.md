---
title: Agentic operations architecture
description: What changes structurally when an AI agent becomes a principal in your infrastructure, using HolmesGPT as the reference implementation.
tags: [agentic-ops, holmesgpt, mcp, observability, rbac, evaluation]
---

# Agentic operations architecture

[HolmesGPT](https://github.com/HolmesGPT/holmesgpt) is a CNCF sandbox project — originally from Robusta.dev, with Microsoft contributions — that runs an agentic loop over live observability data to find root causes. It connects to 60+ sources: Prometheus, Grafana, Datadog, Loki, New Relic, Splunk, Sentry, Kubernetes, the three major clouds, ArgoCD, Postgres and friends, PagerDuty, Jira, GitHub. Its Operator mode runs continuously rather than waiting to be asked, notifying Slack and opening pull requests.

It's a useful reference implementation because it makes the architectural shift concrete: an investigation agent is not a tool your engineers use. It is a **new principal in your infrastructure**, and that changes three things structurally.

## 1. Permissions accumulate into something nobody approved

The agent's effective authority is the union of every toolset it holds. Each is defensible alone — read metrics, read pod logs, read cloud config, write to GitHub. Together they are: enumerate the control plane, read every log line in production, and open a pull request. No screen anywhere renders that union, so no one reviews it.

The design response is one identity per toolset rather than one identity for the agent, so the union stays visible and revocable per source. See [toolset scoping and the read/write boundary](toolset-scoping.md).

The subtler version of this problem is that "read-only" is not a security boundary when applications log credentials. `pods/log` and `configmaps` are both nominally read verbs and both routinely return connection strings.

## 2. Context is finite and telemetry is not

An agent investigating a restart loop can pull 200 MB of logs before it starts reasoning, spend its entire window on transport, and then answer confidently from whatever fragment survived truncation.

This makes **where data is reduced** an architectural decision rather than an optimisation. Filtering server-side — pushing predicates into Prometheus, into the log backend, into the cloud API query — is the difference between an answer and a plausible sentence. HolmesGPT's design notes call this out directly: server-side filtering and streaming with per-tool memory limits, so a single tool call can't exhaust the process or the window.

The corollary is that connecting more sources does not monotonically improve answers. Past some point each additional toolset competes for the same context and dilutes it. Three well-chosen sources beat twelve.

## 3. Fluency is not calibration

An agentic loop is optimised to produce an answer. Truncated evidence, a stale metric, or a coincidental correlation yields the same confident register as a correct finding — a specific, plausible explanation naming a real service, which is wrong, and which sends an on-call engineer down that path for an hour.

There is no way to fix this from inside the loop. The only structural answer is external: require every conclusion to cite the queries it rests on, then check whether the cited evidence supports the claim. An unciteable conclusion is a hypothesis regardless of how it reads.

## Autonomy is earned in tiers, and the tiers are measurable

The three levels — **investigate**, **notify**, **act** — are separate grants, and the mistake is treating them as one product decision.

They can be separated empirically. Replay the agent against resolved incidents where ground truth is known, score root-cause accuracy rather than answer quality, and track the false-confidence rate — wrong answers offered without hedging — as its own number, because those are the ones that cost time.

An agent at 60% root-cause accuracy is genuinely valuable as a first-pass investigator and must not be permitted to open pull requests. That threshold, set before the evaluation runs rather than after, is what turns autonomy from a vibe into a decision.

## Topics

- [Toolset scoping and the read/write boundary](toolset-scoping.md) — what each toolset grants, how permissions accumulate, credential blast radius, and the incident-replay evaluation that gates write access
