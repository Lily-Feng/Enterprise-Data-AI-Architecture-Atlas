---
title: Glossary
description: Working definitions for terms that recur at infrastructure seams.
type: index
status: draft
last_reviewed: 2026-08-29
tags: [glossary]
---

# Glossary

Definitions are operational — what the term means when you are wiring something. For conceptual treatment, see [Calm Data and AI](https://github.com/Lily-Feng/Calm.Data.and.AI).

**Asymmetric routing** — traffic leaving by one path and returning by another. Harmless until a stateful firewall on one path sees a reply for a session it never saw opened, and drops it.

**Blast radius** — what an identity or a failure can reach. For an agent, it is the union of every credential it holds, which is never the same as any single toolset's scope.

**Conditional forwarder** — a rule telling a resolver "for this zone, ask that server." The primary mechanism for joining two DNS systems, and the primary way to build a resolution loop.

**Cross connect** — the physical cable in a colocation facility joining two cages, or a cage to a carrier or cloud on-ramp. The literal object this repository is named for.

**Gang scheduling** — placing all ranks of a distributed job together or not at all. Without it, a job can start partially placed and either deadlock or run across an unintended topology.

**HBM** — High Bandwidth Memory, on the accelerator package. *Capacity* decides what fits; *bandwidth* decides how fast it runs. Sizing from parameter count alone ignores optimizer state and activations, which usually dominate.

**MSS clamping** — rewriting the TCP maximum segment size at a boundary device so sessions negotiate a size that survives the path. The standard fix when path MTU discovery is broken by filtered ICMP.

**MCP server** — a process exposing tools to a model over the Model Context Protocol. At a seam, it is a credentialed principal: what it can reach, the model can reach.

**NVLink / NVSwitch** — the intra-node GPU interconnect. Roughly an order of magnitude faster than the inter-node fabric, which is why the node boundary is the most important line in a GPU topology.

**Oversubscription ratio** — leaf uplink capacity versus the downlink capacity it serves. A 4:1 spine means a collective crossing it gets a quarter of line rate, on a good day.

**Private endpoint** — a service reachable by a private address inside a virtual network. Its DNS name resolves correctly only where the private zone is reachable, which is the source of most "it works from the cloud but not from on-prem" reports.

**Rail-optimized** — a fabric where GPU *n* on every node attaches to fabric rail *n*. Rail-aligned collectives stay on the leaf tier; misaligned ones cross the spine.

**Seam** — two systems, designed separately, that must interoperate. The unit of a page here.

**Split-horizon DNS** — the same name resolving differently depending on which resolver answered. Intentional as a design; the leading cause of hybrid connectivity reports when unintentional.

**Toolset** — a bundle of capabilities exposed to an agent for one data source. Enabling one is a permission grant, not a feature flag.

**Transitive routing** — traffic passing *through* one attached network to reach a third. Frequently assumed and frequently not supported; the failure is silent, since routes simply are not propagated.
