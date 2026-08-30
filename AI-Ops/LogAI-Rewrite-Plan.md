# LogAI Paper Rewrite Plan

## Working title

**From Log Analytics to Evidence-Grounded Agentic AIOps: A Modern Architecture for Detection, Diagnosis, and Safe Remediation**

## Source and intent

This plan uses [LogAI.pdf](./LogAI.pdf) as the 2023 baseline. The rewrite should be a clearly attributed successor paper, not a silent modification of the original authors' work. It should preserve LogAI's useful architectural ideas while developing a new thesis, architecture, and evaluation appropriate for current LLM capabilities.

The intended paper should answer this question:

> How should a modern AIOps platform combine deterministic telemetry processing, classical anomaly detection, multimodal evidence, retrieval, and tool-using LLM agents to reduce incident resolution time without sacrificing reliability, security, or operator control?

## Executive decision

Do not frame the new paper as "LogAI with a newer language model." Reframe it as a hybrid AIOps system in which:

1. Deterministic and statistical components continuously process high-volume telemetry.
2. An incident bundler converts anomalies into a compact, correlated evidence package.
3. An LLM investigator queries tools and grounded knowledge at incident time.
4. Every diagnosis is expressed as evidence-backed, ranked hypotheses rather than an unsupported answer.
5. Remediation passes through policy, approval, execution, verification, and rollback controls.

The key message is that LLMs should operate on selected incident evidence, not on every raw log line.

## What to retain, modernize, and replace

| Original element | Decision | Rewrite direction |
| --- | --- | --- |
| OpenTelemetry-aligned record model | Retain and expand | Use the complete current OTLP model and correlate logs, metrics, traces, profiles, topology, and change events. |
| Layered, reusable components | Retain | Preserve modular interfaces, but make them streaming-capable, observable, versioned, and independently deployable. |
| Parsing, partitioning, and feature extraction | Retain and modernize | Add adaptive parsing, semantic deduplication, failed-versus-healthy diffs, topology-aware windows, and LLM-oriented evidence selection. |
| Classical anomaly detection | Retain | Position statistical and compact ML models as the low-cost continuous detection tier. |
| BERT/Transformer models | Reposition | Treat them as representation or detection baselines, not as the paper's definition of current LLM intelligence. |
| Log-only analysis | Replace | Use multimodal observability and operational context. Logs alone rarely establish causality. |
| Pattern-count "summarization" | Expand | Produce an incident narrative containing impact, timeline, evidence, hypotheses, uncertainty, and next actions. |
| Root-cause-analysis claim | Rebuild | Define the task precisely and implement evidence-linked causal localization and hypothesis ranking. |
| File-upload GUI | Replace | Design an incident investigation workspace triggered by an alert or SLO violation. |
| YAML/JSON experiment setup | Retain and expand | Add schema versions, lineage, model and prompt versions, evaluation records, deployment stages, and rollback. |
| HDFS/BGL/Thunderbird-only evaluation | Replace | Retain them as regression baselines but add temporal, cross-system, multimodal, and production-like incident evaluation. |
| Autonomous model output | Reject | Require grounding, confidence, abstention, policy enforcement, human approval, and post-action verification. |

## Proposed contributions

The new paper should claim only contributions that are implemented and evaluated. Target contributions are:

1. **A hybrid evidence-funnel architecture** that combines streaming detection with incident-level LLM reasoning.
2. **An OpenTelemetry-native multimodal incident representation** linking logs, metrics, traces, profiles, topology, deployments, and configuration changes.
3. **A tool-using investigation agent** that retrieves evidence, runs telemetry queries, compares healthy and failed periods, and returns structured hypotheses.
4. **A provenance and verification model** requiring each diagnostic claim to cite source evidence and expose uncertainty.
5. **A guarded remediation lifecycle** with read-only defaults, simulation, approval, scoped execution, verification, and rollback.
6. **A deployment-oriented evaluation framework** covering accuracy, drift, latency, cost, safety, groundedness, and operator outcomes.

## Research questions

- **RQ1 - Detection:** Does a hybrid cascade match or improve incident detection quality while reducing inference cost relative to an LLM-only pipeline?
- **RQ2 - Diagnosis:** How much do metrics, traces, topology, and change events improve root-cause localization beyond logs alone?
- **RQ3 - Grounding:** Which combination of retrieval, tool use, structured output, and verification most reduces unsupported diagnostic claims?
- **RQ4 - Generalization:** How well does the system handle unseen services, template drift, software-version changes, and previously unseen incidents?
- **RQ5 - Human outcomes:** Does the system reduce investigation time and cognitive load for SREs without increasing harmful recommendations or automation errors?
- **RQ6 - Remediation:** Under what policies can proposed or automated remediation be executed safely, verified, and rolled back?

## Proposed paper structure

### Abstract

State the production problem, the limitations of log-only model pipelines, the hybrid architecture, the evaluation setting, and measured results. Do not advertise autonomous RCA unless the evaluation demonstrates it.

### 1. Introduction

- Establish the growth and heterogeneity of operational telemetry.
- Explain why anomaly detection is not equivalent to diagnosis or causality.
- Contrast the 2023 model-centric paradigm with current retrieval- and agent-based systems.
- State the new thesis and contributions.
- Define the intended operating boundary: an SRE copilot with guarded automation, not an omniscient autonomous operator.

### 2. Background and evolution since LogAI

- Summarize the original LogAI workflow and its historical contribution.
- Distinguish encoders such as BERT/LogBERT from instruction-following LLMs and reasoning agents.
- Cover developments in LLM-based parsing, log diagnosis, retrieval-augmented generation, tool use, structured generation, and agent evaluation.
- Explain the continuing value of classical parsing and anomaly detection.
- Review evidence that narrow, highly grounded systems can be useful while broad real-world RCA remains difficult.

### 3. Problem definition and system boundaries

Define separately:

- Anomaly detection.
- Event and alert correlation.
- Failure localization.
- Root-cause hypothesis generation.
- Root-cause verification.
- Remediation proposal and execution.

Specify users, environments, latency requirements, data-retention constraints, privacy requirements, and what the system must refuse or escalate.

### 4. Design principles

1. Telemetry-native rather than log-only.
2. Cheap continuous processing before expensive reasoning.
3. Evidence before explanation.
4. Tools and retrieval instead of unsupported memory.
5. Explicit uncertainty and abstention.
6. Human control over material actions.
7. Reproducibility across data, models, prompts, tools, and policies.
8. Security and privacy by construction.

### 5. Reference architecture

Use the following logical flow:

```text
OpenTelemetry and operational change sources
                    |
                    v
Validation -> redaction -> enrichment -> correlation
                    |
                    v
Streaming baselines, templates, deduplication, and drift detection
                    |
                    v
Incident bundler: timeline + topology + anomalous evidence
                    |
                    v
Evidence-grounded, tool-using LLM investigator
                    |
                    v
Ranked hypotheses + evidence + confidence + next queries
                    |
                    v
Policy gate -> approval -> execute -> verify -> rollback
```

The architecture section should describe deployment boundaries, interfaces, persistence, failure modes, and data flow—not only class abstractions.

### 6. Telemetry and evidence plane

- Adopt current OTLP records rather than a custom subset.
- Include `ObservedTimestamp`, `TraceFlags`, `EventName`, resource attributes, instrumentation scope, schema URL, service identity, deployment version, environment, region, and tenant.
- Correlate logs with spans, metrics, profiles, Kubernetes or cloud events, configuration changes, deployments, feature flags, and tickets.
- Preserve raw records while creating normalized and redacted analytical views.
- Document cardinality management, late and out-of-order events, sampling, clock skew, backpressure, retention, and schema evolution.
- Define a provenance identifier that survives every transformation and can be cited by downstream claims.

### 7. Detection and incident construction

- Keep parsing, frequency baselines, time-series detectors, outlier models, and compact sequence models.
- Add template and embedding drift detection.
- Compare failed periods with service-specific healthy baselines.
- Deduplicate repeated errors and preserve representative examples plus counts.
- Build a service and dependency graph from traces and topology metadata.
- Convert correlated anomalies into an incident package bounded by time, topology, and suspected impact.
- Route only ambiguous, novel, or high-impact incidents to the LLM layer.

### 8. LLM investigation layer

The agent should receive tools rather than a raw telemetry dump. Candidate tools include:

- Query logs by service, trace, severity, template, and time range.
- Compare incident and healthy windows.
- Inspect trace critical paths and dependency edges.
- Query metric changes and correlations.
- Retrieve recent deployments and configuration changes.
- Search runbooks, historical incidents, tickets, code, and ownership metadata.
- Ask for additional evidence when confidence is insufficient.

Require a structured response containing:

- Incident summary and likely impact.
- Timeline.
- Ranked root-cause hypotheses.
- Evidence identifiers for every material claim.
- Evidence that contradicts each hypothesis.
- Confidence and calibration metadata.
- Unknowns and missing telemetry.
- Recommended next diagnostic queries.
- Proposed remediation clearly separated from verified facts.

### 9. Knowledge and retrieval layer

- Use hybrid lexical, semantic, metadata, and graph retrieval.
- Separate authoritative runbooks from informal historical discussion.
- Apply access control before retrieval, not only after generation.
- Version documents and attach ownership, recency, and trust metadata.
- Detect stale or conflicting procedures.
- Evaluate retrieval recall independently from generation quality.

### 10. Safety, security, and governance

- Redact secrets and sensitive identifiers before model access.
- Treat telemetry and retrieved documents as untrusted input that may contain prompt injection.
- Isolate tenants and enforce least-privilege tool credentials.
- Default the agent to read-only investigation.
- Apply allowlists, parameter validation, rate limits, blast-radius limits, and maintenance-window policies to actions.
- Require approval for material changes.
- Log prompts, evidence, tool calls, outputs, approvals, and outcomes for audit.
- Verify post-action health and support automatic or operator-triggered rollback.

### 11. Operator experience

Replace the upload-and-run GUI with an incident workspace containing:

- SLO and impact summary.
- Incident timeline.
- Service dependency graph.
- Correlated logs, metrics, traces, changes, and prior incidents.
- Ranked hypotheses with expandable evidence.
- Tool-call and query history.
- Confidence, unknowns, and abstention state.
- Proposed action, policy status, approval controls, and rollback plan.
- Operator feedback and final incident resolution.

### 12. Experimental design

#### Baselines

- Rules and dynamic thresholds.
- Classical parser plus statistical or ML detector.
- LSTM/CNN/Transformer and LogBERT baselines from the original work.
- Prompt-only LLM over raw logs.
- Filtered-log LLM.
- Retrieval-augmented LLM.
- Tool-using agent.
- Full multimodal agent with verification.

#### Datasets

- Retain HDFS, BGL, and Thunderbird for backward comparison.
- Add modern microservice and distributed-system incident datasets.
- Include logs, metrics, traces, topology, and change-event data where possible.
- Add real or carefully controlled fault-injection incidents.
- Separate incidents temporally and by software version.
- Include unseen systems or services to test transfer.
- Document contamination and possible model pretraining exposure.

#### Metrics

Detection metrics:

- Precision, recall, F1, PR-AUC, and calibrated confidence.
- False alerts per service-hour.
- Time to detect.

Diagnosis metrics:

- Root-cause top-1 and top-k accuracy.
- Service and component localization accuracy.
- Evidence precision and recall.
- Unsupported-claim and contradiction rates.
- Correct abstention rate.

Operational metrics:

- Investigation latency and time to resolution.
- Tokens, compute, storage, and cost per incident.
- Tool-call count and failed-query rate.
- Operator acceptance, correction, override, and escalation rates.

Safety metrics:

- Unsafe recommendation rate.
- Unauthorized action attempts blocked.
- Successful verification and rollback rate.
- Prompt-injection and data-leakage resistance.

#### Experimental controls

- Publish immutable train, validation, and test manifests.
- Use temporal splits and prevent incident-family leakage.
- Run multiple seeds and report confidence intervals.
- Freeze prompts, retrieval indexes, tool versions, and model versions for each run.
- Report hyperparameter and threshold selection procedures.
- Perform ablations for preprocessing, filtering, topology, retrieval, tool use, verification, and human approval.
- Evaluate drift and degraded telemetry through missing, delayed, duplicated, reordered, and adversarial inputs.

### 13. Results and discussion

- Report accuracy together with cost and latency rather than presenting F1 alone.
- Separate detection success from diagnosis success and verified root cause.
- Analyze cases where the agent reaches the right answer for the wrong reason.
- Include failure taxonomies and representative incident studies.
- Discuss which incidents should remain human-led.
- Avoid claiming statistical significance without the corresponding test and uncertainty interval.

### 14. Limitations and responsible deployment

Explicitly discuss:

- Incomplete or misleading telemetry.
- Correlation versus causality.
- Model and infrastructure drift.
- Context limitations and retrieval failures.
- Hallucination and overconfident recommendations.
- Privacy and regulatory constraints.
- Dependence on organizational knowledge quality.
- Benchmark representativeness and contamination.
- Limits of automated remediation.

### 15. Conclusion

Conclude that modern AIOps is a layered evidence system. LLMs improve interpretation, knowledge access, and investigation orchestration, but deterministic telemetry engineering, verification, governance, and human judgment remain essential.

## Figures and tables to produce

1. **Evolution figure:** 2023 LogAI pipeline versus the proposed hybrid agentic pipeline.
2. **Reference architecture:** telemetry, evidence, reasoning, action, and governance planes.
3. **Evidence funnel:** raw telemetry volume reduced to incident evidence and then to verified findings.
4. **Agent investigation loop:** hypothesize, query, retrieve, compare, verify, and either answer or abstain.
5. **Remediation state machine:** propose, simulate, approve, execute, verify, rollback, and close.
6. **Incident workspace wireframe:** topology, timeline, evidence, hypotheses, and controls.
7. **Claim-to-evidence schema table.**
8. **Evaluation matrix:** baselines, modalities, grounding methods, datasets, and metrics.
9. **Failure taxonomy:** detection, retrieval, reasoning, tool, policy, execution, and verification failures.

## Writing and evidence standards

- Use primary papers, specifications, official documentation, and verifiable project records.
- Attach a source to every quantitative or time-sensitive claim.
- Distinguish measured results, cited results, design proposals, and author inference.
- Define overloaded terms such as "anomaly," "root cause," "agent," and "autonomous."
- Do not call BERT tokenization or a small Transformer an LLM capability without qualification.
- Avoid vendor feature lists unless they support a specific architectural comparison.
- Preserve negative results and document failure cases.
- Make diagrams consistent with the actual implementation and experiments.

## Initial source set to validate and expand

- OpenTelemetry Logs Data Model and current semantic conventions.
- Original LogAI technical report and surviving release documentation.
- LogEval: LLM evaluation for parsing, anomaly detection, diagnosis, and summarization.
- OpenRCA: multimodal enterprise root-cause benchmark.
- SoK: LLM-based log parsing.
- LogSage: filtered evidence, retrieval, tool calling, and industrial CI/CD validation.
- LLM4Log systematic review and its cited primary studies.
- Recent work on agent-trace debugging, evidence attribution, telemetry prompt injection, and safe automated remediation.

Every source should be checked for publication status, dataset availability, code availability, evaluation leakage, and reproducibility before it is used to support a claim.

## Execution plan

### Phase 1 - Scope and evidence map

- Freeze the paper thesis, audience, terminology, and system boundary.
- Build a claim-to-source matrix for all background and capability statements.
- Decide whether the output is a design paper, implemented system paper, or evaluated prototype paper.
- Mark proposed contributions that cannot yet be supported by implementation or data.

**Output:** approved thesis, research questions, source matrix, and contribution boundary.

### Phase 2 - Architecture and data contracts

- Define the OTLP-based incident and provenance schemas.
- Specify the detector, incident-bundler, retrieval, agent-tool, claim-evidence, and remediation interfaces.
- Produce the reference architecture and safety state machine.
- Write Sections 3-10 as an architecture draft.

**Output:** architecture specification, schemas, figures, and first technical draft.

### Phase 3 - Evaluation design and prototype

- Freeze datasets and immutable splits.
- Implement or select baselines.
- Build the minimum evidence bundler and read-only investigation agent.
- Create the evaluation harness before tuning the system.
- Run ablations, drift tests, safety tests, and cost measurements.

**Output:** reproducible experiment bundle, raw results, and statistical analysis.

### Phase 4 - Full manuscript

- Write the introduction and related work after the contribution boundary is stable.
- Integrate architecture, methods, experiments, case studies, and limitations.
- Ensure every claim is supported by an experiment or citation.
- Make terminology, diagrams, algorithms, and data contracts consistent.

**Output:** complete manuscript draft with bibliography and appendices.

### Phase 5 - Review and reproducibility audit

- Conduct technical, SRE, security, privacy, and research-method reviews.
- Re-run experiments from a clean environment.
- Audit tables against raw results.
- Test every artifact link and citation.
- Check that unsupported autonomous-RCA claims have been removed.

**Output:** submission-ready paper and reproducibility package.

## Recommended deliverables

- `LogAI-Modernized-Paper.md` or a LaTeX manuscript directory.
- Architecture and workflow figures in editable source format.
- OTLP incident, evidence, hypothesis, and action-policy schemas.
- Evaluation harness and immutable dataset manifests.
- Prompt, retrieval, tool, model, and policy version manifests.
- Experiment results with seeds and confidence intervals.
- Threat model and safety test suite.
- Reproducibility and responsible-use appendices.

## Definition of done

The rewrite is complete only when:

- The title, abstract, contributions, architecture, implementation, and evaluation describe the same system.
- Root-cause claims are separated from anomaly detection and backed by appropriate labels or verification.
- All diagnostic examples trace claims to evidence.
- Classical, prompt-only, retrieval, tool-use, and multimodal baselines are compared fairly.
- Accuracy, cost, latency, drift, safety, and human outcomes are reported.
- Data splits, prompts, tools, models, policies, and seeds are reproducible.
- Security, privacy, prompt-injection, authorization, approval, verification, and rollback are addressed.
- The original LogAI paper is attributed as the historical foundation rather than overwritten or misrepresented.
