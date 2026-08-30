---
title: Toolset scoping and the read/write boundary
description: Wiring an investigation agent into a live estate: what each toolset grants, how permissions accumulate, and where the approval gate belongs.
tags: [agentic-ops, holmesgpt, mcp, rbac, credentials, evaluation]
---

# Toolset scoping and the read/write boundary

An investigation agent is not a tool your engineers use. It is a **new principal in your infrastructure** — one that authenticates to a dozen systems, holds the union of every credential you gave it, reads production data continuously, and in Operator mode acts without being asked.

The seam is between the agent and the estate: what it can see, what it can touch, and what it is permitted to conclude on its own. That seam is defined almost entirely by toolset configuration, which is why toolset configuration deserves more care than it usually gets.

## Topology

```text
                    ┌──────────────────────────┐
                    │      LLM provider        │   context window is finite
                    └────────────┬─────────────┘   telemetry is not
                                 │
                    ┌────────────▼─────────────┐
                    │      Agent runtime       │
                    │   (agentic loop, budget) │
                    └────────────┬─────────────┘
                                 │
        ══════════════════ THE SEAM ══════════════════
                                 │
     ┌──────────────┬────────────┼────────────┬──────────────┐
     │              │            │            │              │
┌────▼─────┐  ┌─────▼────┐ ┌─────▼─────┐ ┌────▼─────┐ ┌──────▼──────┐
│Prometheus│  │  K8s API │ │ Cloud API │ │PagerDuty │ │   GitHub    │
│ toolset  │  │  toolset │ │  toolset  │ │ toolset  │ │   toolset   │
│  READ    │  │  READ    │ │  READ     │ │READ/WRITE│ │ READ/WRITE  │
└──────────┘  └──────────┘ └───────────┘ └──────────┘ └─────────────┘
     │              │            │            │              │
  metrics      pods, events   config,     incidents,     branches,
  ~GB/query    logs, exec     IAM, VPC    acks, notes    pull requests
```

The agent's **effective permission is the union of every row.** Each toolset looks reasonable in isolation. Read Kubernetes is fine. Read cloud config is fine. Write to GitHub is fine. Together they are: read every secret-adjacent object in the cluster, enumerate the cloud control plane, and open a pull request. Nobody approved that combination, because nobody was ever shown it as a combination.

| Element | Grants | Blast radius if the agent is wrong |
|---|---|---|
| Prometheus toolset | Query metrics | Wasted context; leaked cardinality |
| K8s toolset (read) | Pods, events, logs, resource specs | **Log contents may include secrets** |
| K8s toolset (exec) | Command execution in containers | Arbitrary code in production |
| Cloud API toolset | Config, IAM, network topology | Full estate reconnaissance |
| PagerDuty toolset | Read + acknowledge incidents | Acked incident nobody looked at |
| GitHub toolset | Open pull requests | A confident, wrong fix in review |

## Wiring

Toolsets are declarative. The important part is not enabling them — it is giving each one **its own identity**, so the union is visible and revocable per source.

```yaml
toolsets:
  prometheus/metrics:
    enabled: true
    config:
      prometheus_url: http://prometheus.monitoring:9090

  kubernetes/core:
    enabled: true          # read-only verbs via the service account below

  kubernetes/live-metrics:
    enabled: false         # exec-adjacent; off until there is an approval gate

  aws/security:
    enabled: true
    config:
      role_arn: arn:aws:iam::111122223333:role/agent-readonly

  github/pr:
    enabled: false         # write; see Autonomy below
```

The Kubernetes side of the seam — deny by default, and note what is deliberately absent:

```yaml
kind: ClusterRole
metadata:
  name: agent-investigator
rules:
  - apiGroups: [""]
    resources: [pods, pods/log, events, services, nodes, configmaps]
    verbs: [get, list]
  - apiGroups: ["apps"]
    resources: [deployments, replicasets, statefulsets]
    verbs: [get, list]
  # deliberately absent: secrets, pods/exec, pods/portforward,
  # and every write verb. Each would need its own decision.
```

`configmaps` is on that list and is worth a second look: teams put connection strings in ConfigMaps constantly. Reading ConfigMaps is nominally read-only and practically a credential read.

## Knobs

| Knob | Controls | Default | When the default hurts | Set to |
|---|---|---|---|---|
| Toolsets enabled | Breadth of access and context pressure | Many on out of the box | Every toolset competes for context; more sources ≠ better answers | Start with 3; add on evidence |
| Per-tool output limit | Bytes a single tool returns | Generous | One `kubectl logs` fills the window and evicts the useful evidence | Cap and truncate at the tool |
| Server-side filtering | Where data is reduced | Often client-side | Petabyte sources; the agent pays to transport what it discards | Push predicates to the source |
| `pods/log` scope | Which namespaces' logs | All namespaces | Logs carry tokens and PII across tenancy boundaries | Namespace-scoped RoleBindings |
| Write toolsets | Whether the agent acts | Off | — | Keep off until verification is measured |
| Operator mode | Continuous vs on-demand | Off | Continuous investigation multiplies token spend and log reads | On only after scoping is settled |
| Model choice per task | Cost and reliability of each loop step | One model for everything | Summarisation and root-cause reasoning have different requirements | Route by step |

**The context knob is the one that determines whether the agent is useful at all.** Telemetry is unbounded; the context window is not. An agent that pulls 200 MB of logs to answer a question about a restart loop has spent its entire budget before reasoning starts, and it will confidently answer from the fragment that survived truncation. Filtering at the source is not an optimisation here — it is the difference between an answer and a plausible sentence.

## Seams

### Permission union nobody reviewed

**Presents as:** a security review, months in, discovering the agent can read every ConfigMap in every namespace and open pull requests.

**Cause:** toolsets are enabled one at a time, each justified on its own. The union is never rendered anywhere. There is no screen that shows it.

**Confirm:** enumerate the agent's effective permissions directly rather than reading the toolset list.

```bash
kubectl auth can-i --list --as=system:serviceaccount:monitoring:holmes
aws iam simulate-principal-policy --policy-source-arn <role-arn> \
  --action-names s3:GetObject iam:ListRoles ec2:DescribeInstances
```

Run this on a schedule and diff it. Permission drift is invisible otherwise.

### Secrets arriving through the log toolset

**Presents as:** nothing. This failure is silent by construction.

**Cause:** `pods/log` is read-only and therefore feels safe. Applications log connection strings, bearer tokens, and PII. Those bytes go to the model provider, into any prompt cache, and into whatever conversation store the agent keeps.

**Confirm:** treat it as a data-flow question, not an RBAC question. Sample what the toolset actually returns for a real investigation and read it as if you were the provider.

Mitigations, in order of effectiveness: namespace-scope the binding; redact at the toolset before the model sees it; fix the logging.

### The confident wrong root cause

**Presents as:** a fluent, specific, plausible explanation naming a real service — and it is wrong. Investigation proceeds down the named path for an hour.

**Cause:** the agentic loop is optimised to produce an answer, not to produce a calibrated one. Truncated evidence, a stale metric, or a coincidental correlation yields the same confident register as a correct finding.

**Confirm:** require every conclusion to cite the specific queries and their results, then check whether the cited evidence actually supports the claim. An unciteable conclusion is a hypothesis regardless of tone.

This is the seam that decides whether the agent earns more autonomy, and it is measurable:

- Replay the agent against **resolved** incidents where ground truth is known.
- Score root-cause accuracy, not answer quality — a well-written wrong answer scores zero.
- Track the false-confidence rate separately: wrong answers offered without hedging are the ones that cost time.
- Set a threshold *before* running the evaluation, and gate write access on clearing it.

An agent at 60% root-cause accuracy is genuinely useful as a first-pass investigator and must not be allowed to open pull requests. Those are separate decisions and the evaluation is what separates them.

### Acting on a stale view

**Presents as:** a fix for a condition that resolved several minutes ago; an incident acknowledged based on a metric window that has already moved.

**Cause:** the agent reads point-in-time snapshots across sources with different lag — Prometheus scrape intervals, log shipping delay, cloud config eventual consistency. It reasons over them as if they were simultaneous.

**Confirm:** require timestamps on every retrieved fact and check the spread. A conclusion drawing on sources minutes apart during a fast-moving incident is reasoning about a state that never existed.

