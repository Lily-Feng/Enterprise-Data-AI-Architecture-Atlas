---
title: AI infrastructure architecture
description: The memory and interconnect hierarchy that governs GPU cluster design, and why parallelism strategy is a wiring decision.
tags: [gpu, hbm, nvlink, infiniband, fabric, scheduling]
---

# AI infrastructure architecture

The central fact of AI infrastructure is that the memory and interconnect hierarchy spans about three orders of magnitude, and nearly every design decision is really a decision about which tier a given piece of traffic lands on.

```text
HBM3, on-package        ~3,350 GB/s     inside one GPU
NVLink 4 / NVSwitch       ~900 GB/s     between GPUs in one node
NDR InfiniBand             ~50 GB/s     between nodes, per NIC
Storage / Ethernet         ~12 GB/s     to the filesystem        [approx]
```

Each step down is roughly an order of magnitude. A workload that fits in the tier above runs; the same workload one tier down runs five to twenty times slower, and nothing errors — the job completes, the loss goes down, and the cause is invisible from inside the training script.

## The node boundary is the design

The 900 → 50 GB/s step between NVSwitch and the fabric is the most important line in a GPU topology. Almost every architectural rule in this area is downstream of it:

- Tensor parallelism generates per-layer collectives inline with the forward pass, so it must stay inside one node.
- Pipeline parallelism generates little traffic and tolerates latency, so it crosses nodes cheaply.
- Data parallelism generates one large allreduce per step that overlaps with the backward pass, so it crosses nodes acceptably.

That mapping is the whole game, and it's covered in [mapping parallelism onto the interconnect hierarchy](parallelism-to-interconnect.md).

## HBM: capacity and bandwidth are different constraints

Capacity decides **what fits**; bandwidth decides **how fast it runs**. Which one binds depends on arithmetic intensity — FLOPs performed per byte moved. Below the hardware's compute-to-bandwidth ratio, a kernel is memory-bound and additional FLOPs buy nothing, which is why peak-TFLOPS comparisons between accelerators predict real throughput so poorly.

The capacity side is routinely underestimated because people size from parameter count. HBM holds weights *plus* gradients, optimizer states (Adam adds roughly two extra fp32 values per parameter), and activations — which scale with batch size and sequence length and frequently dominate everything else.

## Fabric shape

Rail-optimized topology attaches GPU *n* on every node to fabric rail *n*. Collectives between matching ranks stay on the leaf tier; misaligned ones traverse the spine, where oversubscription lives. A 4:1 spine means a collective crossing it gets a quarter of line rate.

InfiniBand versus RoCE is largely a question of whether you want a purpose-built lossless fabric with its own operational model, or Ethernet with priority flow control and the tuning burden that comes with it. The second is cheaper to staff and harder to get right.

## The scheduler decides whether any of this holds

All of the above assumes ranks land where you intended. Slurm with `--switches` constrains placement to a switch boundary. Plain Kubernetes will satisfy a request for 64 GPUs from eight racks, and nothing in the training script can detect that it happened — the tensor-parallel group you sized to a node is now spread across the fabric.

This is the gap between an AI infrastructure design and an AI infrastructure deployment, and it is where most of the disappointment lives.

## Topics

- [Mapping parallelism onto the interconnect hierarchy](parallelism-to-interconnect.md) — which parallelism belongs on which link, NCCL configuration, and the assertion that catches the expensive misconfiguration
