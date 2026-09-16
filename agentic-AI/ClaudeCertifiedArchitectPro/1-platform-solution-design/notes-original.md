
# Claude Platform & Solution Design

| Highlight | Meaning |
|---|---|
| **Non-determinism** | The same input can yield different outputs across different runs. You cannot certify behavior based on a single successful observation, which makes robust evaluation frameworks mandatory. |
| **Context as a finite resource** | The context window is a hard boundary with a strict token budget. Deciding what to include, what to omit, and the order of information affects both the model's capabilities and the operational cost. |
| **Confidence is not validity** | Claude can state an incorrect answer with the exact same fluent, authoritative tone as a correct one. Verification and human-in-the-loop steps are core architectural requirements, not afterthoughts. |
| **Knowledge and capability boundaries** | The model is reliable with common, recent topics heavily featured in its training data, but unreliable with rare, private, or rapidly changing information. For unreliable topics, architects must use web search, retrieval (RAG), tools, and MCP to rely on external sources of truth. |

| Owner | What belongs here |
|---|---|
| **What Claude does** | The work that benefits from language understanding, summarization, planning, drafting, or tool-mediated action. |
| **What existing systems do** | Anything your partner has already paid to make reliable: the order-status service, the policy engine, the rules table, the database of record. |
| **What humans do** | The judgment calls, the exception paths, the approvals, the moments where being right matters more than being fast. |



What broke and why
No coverage check at synthesis. The orchestrator synthesized over the results it happened to receive, with no rule that the number of results must equal the number of units dispatched.
A recoverable failure was never recovered. A timed-out subagent is the recoverable case, but only if something retries it or flags the gap. Here the failure was silent because nothing was watching the boundary.
Confident synthesis over incomplete work. The output's fluency masked the gap. A multi-agent system fails most dangerously when the summary looks complete and is not.
