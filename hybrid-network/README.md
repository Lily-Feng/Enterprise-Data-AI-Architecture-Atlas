---
title: Hybrid network architecture
description: How an enterprise on-premise network and a cloud network are actually joined, and why the failures are rarely in the circuit.
tags: [hybrid, networking, dns, routing, landing-zone]
---

# Hybrid network architecture

Two networks built decades apart, under different assumptions about addressing, naming, trust, and who owns the default route, joined by a circuit and expected to behave as one.

The defining property of this seam is that **the transport almost always works and the integration almost always doesn't.** The fibre is lit, BGP is established, packets flow — and the application still can't reach the database, because a name resolved to the wrong address or a packet was forty bytes too large. Enterprises buy the circuit and then spend a year on everything above it.

## The layers that have to line up

A working hybrid connection is five independent agreements, and each can fail while the others look healthy:

```text
  identity      ── can the caller prove who it is on both sides?
  naming        ── does the name resolve to the right address, from both sides?
  routing       ── is there a return path, and does it match the forward path?
  addressing    ── do the ranges collide?
  transport     ── is there a circuit?          ← the only one with a dashboard
```

Monitoring covers the bottom layer almost exclusively. That mismatch — the visible layer being the one that rarely breaks — is why hybrid incidents take so long to diagnose and why the first hour usually goes to the wrong team.

## Structural decisions, in the order they constrain each other

**Addressing comes first and is nearly irreversible.** The RFC1918 range you allocate to cloud constrains every later choice. Enterprises that grew by acquisition arrive with overlapping 10.0.0.0/8 space already in use, and the honest options are renumbering (expensive, disruptive) or NAT at the boundary (cheap, and it costs you the ability to trace a flow end to end). Deciding this badly is the one mistake you live with for a decade.

**Transit topology decides what can talk to what.** Hub-and-spoke with a transit gateway or virtual WAN is the default shape because it centralises inspection and route control. The recurring surprise is transitive routing: traffic passing *through* one attached network to reach a third is frequently unsupported, and the failure is silent — routes simply aren't propagated, so it presents as an unreachable host rather than as a configuration error.

**Naming is where it actually breaks.** Each side has a complete, self-consistent DNS system that knows nothing about the other. Joining them means pointing each at the other for a specific set of zones, in both directions, without building a loop. See [DNS across the on-prem/cloud boundary](dns-across-the-boundary.md) — the deepest and most reliably useful topic in this area.

**Identity is the layer people design last and need first.** On-premise directory federated to a cloud identity provider, workload identity that works on both sides, secrets that must exist in two places with two rotation mechanisms. A credential valid on one side of the boundary and not the other produces failures that look exactly like network failures.

## The asymmetry worth internalising

On-premise networks assume a trusted interior and a hard perimeter. Cloud networks assume no interior trust and identity at every hop. Hybrid architecture is mostly the work of reconciling those two positions at a single line — which is why "extend the corporate network into the cloud" and "treat cloud as a separate trust domain reachable over a private circuit" produce completely different designs from the same requirements document.

The second is generally the better default. The first is what most enterprises build, because it requires fewer conversations.

## Topics

- [DNS across the on-prem/cloud boundary](dns-across-the-boundary.md) — bidirectional resolution, resolver endpoints, split-horizon, and the MTU failure that gets misfiled as DNS
