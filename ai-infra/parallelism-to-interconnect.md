---
title: Mapping parallelism onto the interconnect hierarchy
description: Which form of model parallelism belongs on which physical link, and what it costs when one spills to the tier below.
tags: [gpu, nvlink, infiniband, nccl, parallelism, hbm]
---

# Mapping parallelism onto the interconnect hierarchy

Parallelism strategy is presented as a modelling decision and is actually a wiring decision. Tensor, pipeline, and data parallelism each generate a characteristically different traffic pattern, the physical hierarchy offers tiers that differ by more than an order of magnitude, and the entire performance question is whether each pattern landed on the right tier.

Get the mapping wrong and nothing errors. The job runs, the loss goes down, and it takes five times longer than it should for a reason invisible from inside the training script.

## Topology

The hierarchy on a current 8-GPU node, with the boundary that matters marked:

```text
  ┌─────────────────────────── NODE ────────────────────────────┐
  │                                                             │
  │   GPU0   GPU1   GPU2   GPU3   GPU4   GPU5   GPU6   GPU7      │
  │    │      │      │      │      │      │      │      │       │
  │  80GB   80GB   80GB   80GB   80GB   80GB   80GB   80GB HBM3 │
  │  3.35TB/s each, on-package                                  │
  │    │      │      │      │      │      │      │      │       │
  │    └──────┴──────┴──┬───┴──────┴──────┴──────┴──────┘       │
  │              ┌──────▼──────┐                                │
  │              │  NVSwitch   │   ~900 GB/s per GPU, all-to-all│
  │              └──────┬──────┘                                │
  │                     │                                       │
  │            ┌────────▼────────┐                              │
  │            │  8 x NDR NIC    │   400 Gb/s = 50 GB/s each    │
  └────────────┴────────┬────────┴──────────────────────────────┘
                        │
        ══════════ THE BOUNDARY ══════════   ~18x bandwidth drop
                        │
              ┌─────────▼─────────┐
              │  InfiniBand leaf  │
              └─────────┬─────────┘
                        │
              ┌─────────▼─────────┐
              │       spine       │   oversubscription lives here
              └───────────────────┘
```

| Tier | Bandwidth | Scope | Notes |
|---|---:|---|---|
| HBM3 | ~3.35 TB/s | Within one GPU | Capacity (80 GB) decides what fits |
| NVLink 4 / NVSwitch | ~900 GB/s per GPU | Within one node | All-to-all, uniform |
| NDR InfiniBand | ~50 GB/s per NIC | Between nodes | 8 NICs/node; rail-aligned |
| Storage / Ethernet | ~12 GB/s `[approx]` | To filesystem | Checkpoints only |

The 900 → 50 GB/s step at the node boundary is the whole design constraint. Everything below follows from it.

## Wiring

The mapping, in order of how much traffic each pattern generates:

| Parallelism | Traffic per step | Latency tolerance | Belongs on |
|---|---|---|---|
| **Tensor (TP)** | Very high — allreduce **per layer** | None; it is inline | NVLink, inside one node |
| **Pipeline (PP)** | Low — activations at stage boundaries only | Moderate | InfiniBand, across nodes |
| **Data (DP)** | High — gradient allreduce **once per step** | High; overlaps with backward pass | InfiniBand, across nodes |
| **Expert (EP)** | Bursty all-to-all | Low | NVLink if it fits, else rail-aligned IB |

The rule that follows: **TP degree must not exceed GPUs per node.**

```python
# 64 GPUs = 8 nodes x 8 GPUs
tensor_parallel   = 8    # == GPUs per node; stays on NVSwitch
pipeline_parallel = 2    # crosses nodes; low traffic, tolerant
data_parallel     = 4    # 8 * 2 * 4 = 64
```

NCCL needs to be told about the fabric, and its defaults do not discover rail alignment on their own:

```bash
export NCCL_IB_HCA=mlx5_0,mlx5_1,mlx5_2,mlx5_3,mlx5_4,mlx5_5,mlx5_6,mlx5_7
export NCCL_SOCKET_IFNAME=eth0      # bootstrap only, not data path
export NCCL_IB_GID_INDEX=3          # RoCEv2 fabrics
export NCCL_DEBUG=INFO              # confirms the ring/tree it actually built
```

Read the `NCCL_DEBUG=INFO` output once at the start of every new cluster. It prints the topology NCCL chose, and that is the only direct evidence of whether your mapping survived contact with the scheduler.

## Knobs

| Knob | Controls | Default | When the default hurts | Set to |
|---|---|---|---|---|
| TP degree | GPUs sharing a layer's tensors | Framework-dependent, often 1 | Model does not fit in 80 GB | ≤ GPUs per node, never more |
| PP microbatches | Pipeline bubble size | Equal to PP degree | Bubble wastes a large fraction of the step | 4× PP degree or higher |
| `NCCL_ALGO` | Ring vs Tree for collectives | Auto | Auto mispicks at certain sizes | Benchmark both; Tree favours small, Ring large |
| `NCCL_IB_HCA` | Which NICs NCCL uses | All discovered | Non-rail-aligned traffic crosses the spine | Explicit, rail-aligned list |
| Gradient accumulation | Steps between allreduce | 1 | DP allreduce dominates on a thin fabric | Raise until compute-bound |
| Scheduler topology awareness | Where ranks are placed | **Off in plain Kubernetes** | Ranks scattered across racks; TP silently spans nodes | Gang + topology-aware plugin |

**The scheduler row is the one that bites.** Slurm with `--switches` places a job within a switch boundary. Plain Kubernetes will happily satisfy "64 GPUs" from eight racks, and nothing in the training script can detect that it happened. The TP=8 group you carefully sized to a node is now spread across the fabric, and your 900 GB/s link is a 50 GB/s link.

**Microbatch count** is the cheapest large win and is routinely left at the default. Pipeline bubble fraction is approximately `(PP - 1) / (microbatches + PP - 1)`. At PP=4 and 4 microbatches, that is 3/7 — **43% of the pipeline idle**. Raise microbatches to 16 and the bubble drops to about 16%.

## Seams

### Tensor parallelism spilled across the node boundary

**Presents as:** a step time several times slower than expected, with GPU utilisation looking healthy. No error, no warning.

**Cause:** TP degree exceeds GPUs per node, or the scheduler placed a TP group across two nodes. Per-layer allreduce that assumed 900 GB/s now runs at 50 GB/s, and it is inline with the forward pass, so nothing overlaps it away.

**Confirm:** print the physical placement of each rank before training, and assert it.

```bash
scontrol show hostnames $SLURM_JOB_NODELIST   # what you actually got
```

```python
# fail fast rather than train slowly
assert tensor_parallel <= gpus_per_node, \
    f"TP={tensor_parallel} exceeds {gpus_per_node} GPUs/node — will cross the fabric"
```

Add that assertion to every training entrypoint. It costs nothing and catches the most expensive misconfiguration in this domain.

### Rail misalignment across the spine

**Presents as:** allreduce bandwidth well below line rate; congestion counters climbing on spine links while leaf links are quiet.

**Cause:** in a rail-optimized fabric, GPU *n* on every node connects to rail *n*. A collective between GPU 0 on one node and GPU 3 on another must traverse the spine, where oversubscription lives. Rail-aligned collectives stay on the leaf tier.

**Confirm:** `NCCL_DEBUG=INFO` prints the rings it built; check whether ranks are paired within rails. Correlate against spine port counters.

### Checkpoint write stalls every rank

**Presents as:** periodic cliffs in throughput, evenly spaced, correlated with checkpoint interval.

**Cause:** the storage tier is an order of magnitude below the compute fabric, and a synchronous checkpoint makes every rank wait for the slowest writer. This is a seam between the compute fabric and the storage fabric, and it is usually designed last.

**Confirm:** overlay checkpoint timestamps on the throughput graph. Cliffs aligned to the interval, not to data, means storage.

### HBM capacity, not bandwidth, is what actually failed

**Presents as:** OOM at a batch size that "should" fit, or a mysterious requirement for more TP than the model size suggests.

**Cause:** HBM holds more than weights — optimizer states, gradients, and activations. Adam holds roughly 2 extra fp32 states per parameter; activation memory scales with batch size and sequence length and frequently dominates. Sizing from parameter count alone underestimates by a large multiple.

**Confirm:** `nvidia-smi` peak memory against a computed budget of weights + gradients + optimizer states + activations. If activations dominate, gradient checkpointing buys memory at roughly 30% recompute cost — often a better trade than raising TP and risking the node boundary.

