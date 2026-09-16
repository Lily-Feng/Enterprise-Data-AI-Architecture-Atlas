# Anthropic CCA Exam Field Guide: Patterns & Anti-Patterns for Agentic Engineering

> **Source Material:** UC Berkeley / AI Engineer World's Fair 2026  
> **Speaker:** Frank P. Coyle, PhD (UC Berkeley)  
> **Topic:** *Anthropic's CCA Exam as a Field-Guide for Agentic Engineering* ([Video Reference](https://www.youtube.com/watch?v=Z-c11pV_uvU&t=644s))  
> **Target Certification:** Claude Certified Architect – Foundations (CCA-F)

---

## 1. Executive Summary & Exam Architecture

Anthropic released the **Claude Certified Architect (CCA)** exam as its first official technical certification through the Claude Partner Network. 

* **Format:** 60 scenario-based, timed multiple-choice questions (120 minutes).
* **Passing Score:** 720 on a scaled range (100–1,000).
* **Delivery:** Timed and proctored; retake policy limited to once every 6 months.
* **Core Philosophy:** The exam is **"a curriculum in disguise."** Rather than rote syntax memorization, every question drops you into a realistic production problem (e.g., broken agent loops, tool selection failures, context saturation, unguided autonomous errors) and asks for the soundest systems-architecture decision.
* **Selection Mechanism:** Every sitting randomly draws **4 of 6 production scenarios**, and all questions in that sitting anchor to those 4 scenarios.

---

## 2. The Five Exam Domains & Weightings

The exam tests five core areas. Notice that **orchestration and architecture form the heaviest slice (27%)**—confirming that agentic AI is treated as a systems-engineering discipline first:

| Domain | Focus Area | Share | Key Competencies Tested |
| :--- | :--- | :---: | :--- |
| **Domain 1** | **Agentic Architecture & Orchestration** | **27%** | Loops, control flow, branching on `stop_reason`, human escalation gates, guardrails. |
| **Domain 3** | **Claude Code Configuration & Workflows** | **20%** | Scoped `CLAUDE.md` hierarchy, custom skills/tools, headless execution, automation. |
| **Domain 4** | **Prompt Engineering & Structured Output** | **20%** | Clear constraints, success criteria, schema enforcement via `tool_use` and JSON schemas. |
| **Domain 2** | **Tool Design & MCP Integration** | **18%** | Narrow tool boundaries, structured error payloads, Model Context Protocol (MCP) servers. |
| **Domain 5** | **Context Management & Reliability** | **15%** | Context positioning, compaction vs. degradation risks, long-horizon session memory. |

---

## 3. The Underlying Paradigm: Rediscovering the Loop

In 1966, the **Böhm–Jacopini theorem** proved that any computable function can be implemented using only three control structures:
1. **Sequence** (step-by-step execution)
2. **Conditional** (`if / then / else` branching)
3. **Loop** (`while` iteration until termination condition)

Traditional prompt engineering relied only on sequences and conditionals (e.g., chained prompts). True **agentic AI** emerges when the **loop** is introduced, allowing the model to act, inspect tool feedback, correct mistakes, and iterate until completion.

> *"My job is to write loops."* — **Boris Cherny**, creator of Claude Code, Anthropic  
> *"Design loops that prompt your agents."* — **Peter Steinberger**, creator of OpenClaw

---

## 4. The Six Production Scenarios: Problems, Anti-Patterns & Solutions

---

### Scenario 1: Customer Support Resolution Agent
* **Applicable Domains:** 1, 2, 3, 4, 5  
* **Production Problem:** An autonomous agent handling customer support requests must resolve inquiries using internal APIs (account status, billing, order lookup) while guaranteeing safety, accuracy, and appropriate boundaries.

```
       ┌─────────────────┐
       │   User Query    │
       └────────┬────────┘
                │
                ▼
      ┌──────────────────┐
 ┌───►│  Claude API Call │
 │    └────────┬─────────┘
 │             │
 │      [stop_reason?]
 │       ├── "tool_use"  ──► [Execute Tool] ──► [Append Result] ──┐
 │       │                                                        │
 │       └── "end_turn"  ──► [Confidence Gate?]                   │
 │                                ├── High Confidence ──► Return  │
 │                                └── Low Confidence  ──► Escalate│
 └────────────────────────────────────────────────────────────────┘
```

#### The Tempting Traps (Anti-Patterns)
1. **Fire-and-forget the loop:** Treating the model invocation as a single-turn call instead of continuously evaluating `stop_reason`. The agent prematurely terminates before running the required tool or spins indefinitely without capturing tool outputs.
2. **Resolve everything autonomously:** Leaving no human-in-the-loop fallback. The agent attempts to unilaterally resolve refund disputes, account modifications, or sensitive edge cases without human oversight.

#### The Sound Solution (Pattern)
1. **Drive the loop strictly on `stop_reason`:** 
   * If `resp.stop_reason == "tool_use"`: execute tool, append tool result message, continue loop.
   * If `resp.stop_reason == "end_turn"`: process final answer.
2. **Build an explicit escalation path:** Gate high-stakes actions and low-confidence responses by routing to human agents.

> **Exam Tell:** Distractors push full autonomy and one-shot API calls. The correct answer almost always adds an explicit control check or a human escalation gate.

#### Reference Implementation (Python)
```python
import anthropic

client = anthropic.Anthropic()

def run_support_agent(messages, tools):
    while True:
        resp = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            messages=messages,
            tools=tools
        )
        
        # Branch explicitly on stop_reason
        if resp.stop_reason == "tool_use":
            # Extract tool invocation, execute safely, and capture result
            result = run_tool(resp)
            messages.append(result)      # Feed tool result back into context
            continue                     # Continue the agentic loop
            
        elif resp.stop_reason == "end_turn":
            answer = final_answer(resp)  # Resolution generated by model
            if low_confidence(answer) or requires_human_approval(answer):
                escalate_to_human(answer) # Safety gate
            return answer
```

---

### Scenario 2: Code Generation with Claude Code
* **Applicable Domains:** 2, 3  
* **Production Problem:** Guiding Claude Code across enterprise repositories with disparate sub-packages, varying coding standards, and high-risk legacy code.

#### The Tempting Traps (Anti-Patterns)
1. **One flat instruction blob:** Dumping every instruction and guideline into a single root `CLAUDE.md`. Directory-specific rules bleed into unrelated subprojects, causing silent instruction conflicts.
2. **Direct-execute everything:** Skipping plan mode on non-trivial refactors or architecture changes. The agent edits files immediately, and errors are only discovered after codebase breakage.

#### The Sound Solution (Pattern)
1. **Leverage the hierarchical `CLAUDE.md` scoping:**
   * `~/.claude/CLAUDE.md` (User scope: personal defaults across all repos)
   * `<repo>/CLAUDE.md` (Project scope: repo-wide standards and test commands)
   * `<repo>/<subpkg>/CLAUDE.md` (Directory scope: fine-grained rules for specific modules)
   * *Resolution Rule:* Claude loads all three scopes and merges them; the most specific directory rule wins on conflict.
2. **Plan before you execute:** Enforce plan mode for architectural or multi-file changes to review and gate proposals before files are modified.

> **Exam Tell:** Answers suggesting "just start editing directly" or centralizing all rules into one global file are traps. The correct answer scopes context hierarchically and gates modifications behind a plan.

#### Scoping Architecture
```
~/.claude/CLAUDE.md             # USER LEVEL (applies to all projects)
"Prefer type hints. Always explain approach before editing."
         │
         ▼
myrepo/CLAUDE.md                # PROJECT LEVEL
"Use pytest. Run 'npm test' before commit. Never touch /legacy."
         │
         ▼
myrepo/api/CLAUDE.md            # DIRECTORY LEVEL (most specific wins)
"All endpoints must be async. Validate inputs with Pydantic v2."
```

---

### Scenario 3: Multi-Agent Research System
* **Applicable Domains:** 1, 2, 3, 4, 5  
* **Production Problem:** Building a research and fact-checking system where multiple tasks (search, reading, reasoning, verification) must collaborate without losing fidelity or hallucinating.

#### The Tempting Traps (Anti-Patterns)
1. **One agent, every tool:** Giving a single generalist agent 10–20 tools. As tool count exceeds ~4–5, reasoning degrades and tool selection accuracy plunges.
2. **Leak the full context:** Passing the coordinator’s entire conversational and reasoning trace to every subagent. Subagents inherit the primary agent’s biases, assumptions, and blind spots.

#### The Sound Solution (Pattern)
1. **Specialize, don't overload:** Hub-and-spoke pattern. Deploy narrow, dedicated subagents with minimal toolsets ($\le 4$ tools each).
2. **Isolate subagent context:** Pass only the exact slice of data required for the subtask (e.g., give a critic agent only the specific claim and source text to verify, omitting the brainstorming trail).

> **Exam Tell:** Giant toolbelts and shared monolithic context look deceptively capable, but are wrong. The sound answer decomposes tasks into specialized agents and isolates their context slices.

#### Reference Implementation (Python)
```python
def run_critic_agent(claim: str, evidence: str) -> dict:
    """
    Subagent isolated context: receives ONLY the claim and evidence,
    preventing anchoring bias from the main coordinator's thought process.
    """
    return client.messages.create(
        model="claude-3-7-sonnet-20250219",
        system=CRITIC_SYSTEM_PROMPT,     # One specialized role definition
        tools=[verify_source_tool],       # Narrow toolset (1 single tool)
        messages=[{
            "role": "user",
            "content": f"Verify whether this evidence supports the claim.\nClaim: {claim}\nEvidence: {evidence}"
        }]
    )
```

---

### Scenario 4: Developer Productivity with Claude
* **Applicable Domains:** 3, 4, 5  
* **Production Problem:** Long-running coding sessions produce huge outputs (long build logs, massive test dumps, large diffs) that saturate context windows and degrade model recall.

#### The Tempting Traps (Anti-Patterns)
1. **Pollute the main session:** Allowing verbose subtasks (e.g., searching 100 log files) to dump thousands of lines directly into the primary conversation thread.
2. **Let context grow unbounded:** Never compacting or pruning. As the context approaches token limits, "lost-in-the-middle" degradation sets in, costs spike, and latency balloons.

#### The Sound Solution (Pattern)
1. **Fork noisy subtasks:** Execute verbose operations in a forked sub-agent or isolated subprocess. Return only the concise synthesized findings to the parent session.
2. **Compact long sessions proactively:** Summarize older conversation turns once tokens exceed a safe threshold (e.g., >150k tokens), preserving recent turns verbatim.

> **Exam Tell:** Options that keep all history in one monolithic thread are traps. The correct choice isolates noisy work and applies context compaction.

#### Reference Implementation (Python)
```python
# 1. Isolate verbose tool execution in a forked context
summary = run_in_subagent(
    task="Scan 2GB error logs and identify root cause timestamps",
    context="fork"   # Isolated memory: raw log dumps stay here
)
main_messages.append({"role": "user", "content": summary})

# 2. Compact main session context when token budget is reached
if token_count(main_messages) > 150_000:
    main_messages = compact_history(
        main_messages,
        preserve_recent_turns=4  # Summarize older history, keep recent exact
    )
```

---

### Scenario 5: Claude Code for CI/CD
* **Applicable Domains:** 3, 5  
* **Production Problem:** Integrating Claude into automated delivery pipelines (GitHub Actions, GitLab CI) for automated code review, PR summaries, or security scanning.

#### The Tempting Traps (Anti-Patterns)
1. **Interactive mode in a pipeline:** Running Claude Code in default interactive mode inside CI. The job stalls indefinitely waiting for interactive terminal input (`stdin`) and produces unstructured output.
2. **Block on work that can wait:** Running synchronous, high-priority API calls for batch-friendly jobs (e.g., overnight deep PR analysis), running up full API prices and stalling pipeline workers.

#### The Sound Solution (Pattern)
1. **Run headless with structured output:** Invoke Claude Code using non-interactive flags:
   ```bash
   claude -p "Review this PR for security vulnerabilities" --output-format json
   ```
2. **Match latency to task priority via Batch API:** For asynchronous workflows (nightly audits, bulk doc generation), use the **Claude Batch API** (50% cost reduction, 24-hour turnaround window).

> **Exam Tell:** Answers proposing interactive sessions or synchronous execution for non-urgent tasks are traps. Look for non-interactive flags, structured output, and Batch API pricing optimization.

---

### Scenario 6: Structured Data Extraction
* **Applicable Domains:** 4, 5  
* **Production Problem:** Extracting complex domain entities (contracts, invoices, medical records) reliably from messy unstructured inputs.

#### The Tempting Traps (Anti-Patterns)
1. **Free-form text generation + Regex parsing:** Asking the model to generate plain text and attempting to parse fields with regular expressions or post-hoc string splitting.
2. **Unvalidated field intake:** Assuming model output always conforms to data types without runtime schema validation.

#### The Sound Solution (Pattern)
1. **Schema enforcement via `tool_use`:** Define a strict JSON schema via tool calling (`input_schema`) and force tool execution (`tool_choice: {"type": "tool", "name": "..."}`).
2. **Programmatic validation & confidence gating:** Pass the extracted payload through validation libraries (e.g., Pydantic v2). If validation fails or confidence is low, trigger programmatic self-correction or human review.

---

## 5. Quick Reference: Exam Cheat Sheet

| Production Scenario | Common Exam Trap (Anti-Pattern) | Correct Architectural Pattern | Key Keyword / Tell |
| :--- | :--- | :--- | :--- |
| **1. Customer Support** | Fire-and-forget loop; full autonomy without human escalation | Branch on `stop_reason`; human gate on low confidence | `stop_reason == "tool_use"`, human escalation |
| **2. Code Generation** | Single monolithic `CLAUDE.md`; direct-execute without plan | Scoped hierarchy (user/project/directory); plan mode | `CLAUDE.md` precedence, Plan Mode |
| **3. Multi-Agent Research** | One agent with 15 tools; leaking full reasoning trace | Specialize subagents ($\le 4$ tools); context isolation | Hub-and-spoke, narrow context slice |
| **4. Dev Productivity** | Dumping verbose logs into main thread; unbounded context growth | Fork subtasks; compact context when token threshold is reached | Context compaction, forked subtask |
| **5. CI/CD Integration** | Interactive REPL in CI; synchronous calls for batch jobs | Headless mode (`-p`, `--output-format json`); Batch API | `-p / --print`, JSON output, Batch 50% discount |
| **6. Structured Extraction**| Text prompt + regex parsing; trusting unvalidated JSON | Tool use schema enforcement + programmatic validation | `tool_choice`, Pydantic schema validation |

