/* Mock question bank — Claude Certified Architect · Professional (CCAR-P)
 * 63 items, weighted to the official blueprint.
 * These are original practice items written against the published objectives.
 * They are NOT real exam content and are not drawn from any live item bank.
 * `answer` is an array of correct choice indices; length > 1 means multi-response.
 */
const DOMAINS = {
  1: "Solution Design & Architecture",
  2: "Models, Prompting & Context Engineering",
  3: "Integration",
  4: "Evaluation, Testing & Optimization",
  5: "Governance, Safety & Risk Management",
  6: "Stakeholder Communication & Lifecycle",
  7: "Developer Productivity & Enablement"
};
const DOMAIN_WEIGHTS = { 1: 17, 2: 13, 3: 19, 4: 16, 5: 14, 6: 14, 7: 7 };

const QUESTIONS = [
/* ================= DOMAIN 1 — Solution Design & Architecture (11) ================= */
{
  id: 1, domain: 1,
  q: "An insurer wants Claude to determine claim eligibility. A rules engine already computes eligibility correctly and produces an audit trail regulators accept. What should the architecture do with the rules engine?",
  choices: [
    "Keep it as the source of truth and have Claude call it, using Claude to gather inputs and explain the outcome",
    "Replace it with a prompt that encodes the same rules, so eligibility logic lives in one place",
    "Run both and have Claude reconcile disagreements between itself and the rules engine",
    "Use the rules engine only as a fallback when Claude's confidence is low"
  ],
  answer: [0],
  why: "The ownership split assigns to existing systems anything the client has already paid to make reliable. The rules engine is deterministic, correct, and auditable — three properties a prompt cannot match. Claude adds value at the edges: gathering messy inputs and explaining the determination in language. Replacing it trades an auditable system for a non-deterministic one; reconciling or falling back still puts a non-deterministic component in the decision path."
},
{
  id: 2, domain: 1,
  q: "A document-processing workflow has five steps that are the same for every document, in the same order, each with a checkable output. The team proposes an agent that decides which step to run next. What is the strongest objection?",
  choices: [
    "The steps are knowable in advance, so a workflow is cheaper, faster, and independently testable per step",
    "Agents cannot call the same tool more than once",
    "Claude is not capable of document processing at production quality",
    "Agentic architectures cannot produce structured output"
  ],
  answer: [0],
  why: "Escalate tiers only when the requirement forces it. A fixed, known sequence is the definition of a workflow. Choosing an agent adds cost, latency, and unbounded failure modes while giving up per-step verifiability, and buys nothing because there is no decision for the model to make."
},
{
  id: 3, domain: 1,
  q: "Which conditions must all hold before escalating from a workflow to an agentic architecture? (Select all that apply.)",
  choices: [
    "The task is multi-step and cannot be fully specified in advance",
    "The outcome justifies the higher cost and latency",
    "Errors can be caught and recovered from",
    "The task will run at high enough volume to justify the engineering effort"
  ],
  answer: [0, 1, 2],
  why: "The gate is complexity, value, viability, and recoverable cost of error. Volume is a business consideration but is not part of the gate — a low-volume, high-value task can absolutely justify an agent, and a high-volume task with unrecoverable errors should not have one."
},
{
  id: 4, domain: 1,
  q: "A multi-agent research system dispatched eight subagents. One timed out. The orchestrator produced a fluent, confident summary that silently omitted that subagent's topic. Which change most directly prevents recurrence?",
  choices: [
    "Require at synthesis that the number of results equals the number of units dispatched, and retry or surface any gap",
    "Increase the subagent timeout so slow subagents have more time",
    "Instruct the orchestrator in its system prompt to mention when information is missing",
    "Use a more capable model for the orchestrator so it notices the omission"
  ],
  answer: [0],
  why: "The failure was structural: nothing was watching the fan-out boundary, so a recoverable failure became silent. A coverage check turns a missing unit into an explicit condition the system must handle. Raising the timeout reduces frequency without closing the hole; a prompt instruction is a soft control over a condition the orchestrator has no way to detect; model capability does not help when the missing data was never in context."
},
{
  id: 5, domain: 1,
  q: "A retailer currently cannot offer support outside business hours because it cannot staff overnight multilingual coverage. A Claude system now handles those hours. Which business value pillar does this primarily serve?",
  choices: [
    "Transformation",
    "Efficiency",
    "Cost",
    "Productivity"
  ],
  answer: [0],
  why: "Transformation means making possible something that was not possible before. Efficiency and cost describe doing existing work faster or cheaper; productivity means more output from the same people. Here the capability itself is new — the coverage did not exist at any price the retailer would pay."
},
{
  id: 6, domain: 1,
  q: "Why is a single successful end-to-end test insufficient evidence that a Claude system is ready for production?",
  choices: [
    "The system is non-deterministic — the same input can yield different outputs across runs, so one observation does not characterize behavior",
    "Production traffic always has higher volume than test traffic",
    "Test environments use a different model than production",
    "Latency in testing is never representative of production"
  ],
  answer: [0],
  why: "Non-determinism is the platform property that makes evaluation frameworks mandatory rather than optional. You need a distribution of graded cases, not an anecdote. The other options describe real operational concerns but none of them is the reason a single pass proves nothing."
},
{
  id: 7, domain: 1,
  q: "An orchestrator passes its full conversation history — including its own brainstorming and working hypotheses — to a critic subagent whose job is to independently verify a claim. What is the architectural flaw?",
  choices: [
    "The critic inherits the orchestrator's assumptions and biases, destroying the independence that made the critic valuable",
    "Passing history exceeds the context window in most cases",
    "Subagents are not permitted to receive assistant-role messages",
    "The critic will run more slowly than necessary"
  ],
  answer: [0],
  why: "Context isolation is the point of a critic. Passing only the claim and the evidence lets it evaluate on the merits; passing the reasoning trail anchors it to the conclusion it was supposed to test. Token cost and latency are real but secondary — the primary loss is independence."
},
{
  id: 8, domain: 1,
  q: "A support agent is built as a single API call: send the user message with tools attached, take whatever comes back, and return it. In testing it sometimes returns a reply that references data it never actually looked up. What is the defect?",
  choices: [
    "The loop does not branch on stop_reason, so a tool_use response is never executed and its result never returned to the model",
    "The tools are described too vaguely for the model to select correctly",
    "The model needs a larger context window to hold the tool definitions",
    "Temperature is set too high for a support use case"
  ],
  answer: [0],
  why: "This is the fire-and-forget anti-pattern. When stop_reason is tool_use, the application must execute the tool, append the tool_result, and call again. Treating the first response as final means the model's intent to look something up is discarded, and whatever text accompanied it gets returned as if it were an answer."
},
{
  id: 9, domain: 1,
  q: "Which decomposition seam is most appropriate when a task has a routine high-volume majority and a difficult minority that needs deeper reasoning?",
  choices: [
    "Confidence-based: route the routine bulk cheaply and escalate the hard tail",
    "Sequential: run every case through the same pipeline stages",
    "Parallel fan-out: process all cases simultaneously",
    "Specialization: assign each case type a differently-prompted agent regardless of difficulty"
  ],
  answer: [0],
  why: "Splitting on confidence matches the shape of the workload: most cases are cheap and the expensive path is reserved for cases that need it. A uniform pipeline pays the hard-case price for every case; fan-out addresses throughput, not difficulty; specialization by type is the right seam only when the differences are about kind rather than difficulty."
},
{
  id: 10, domain: 1,
  q: "A stakeholder asks for 'an AI assistant for our operations team.' Which two questions most directly turn this into a scoped design? (Select two.)",
  choices: [
    "What does the team do today, step by step, and how often?",
    "What would make you turn it off?",
    "Which Claude model would you prefer we use?",
    "Should this be built as a multi-agent system?"
  ],
  answer: [0, 1],
  why: "The first establishes the current-state process and its volume, which is where the ownership split and the baseline metric come from. The second surfaces real risk tolerance and failure conditions. Model selection and architecture pattern are your decisions to make from the requirements, not questions to hand back to a non-technical stakeholder."
},
{
  id: 11, domain: 1,
  q: "An agent has fifteen tools covering ticketing, billing, inventory, shipping, and CRM. Tool-selection accuracy is measurably poor. Which two responses address the cause? (Select two.)",
  choices: [
    "Split into specialized subagents, each holding a small toolset for one domain",
    "Mark most tools defer_loading and add a tool-search tool so the model retrieves what it needs",
    "Write longer, more detailed descriptions for all fifteen tools",
    "Increase the model's effort level so it reasons longer about tool choice"
  ],
  answer: [0, 1],
  why: "Selection accuracy degrades as the toolbelt grows past roughly four or five tools. Both correct options reduce the number of tools in play at decision time — one by partitioning across agents, the other by deferring them out of the prefix. Longer descriptions add tokens to the same crowded decision; more effort spends more to reason over the same bad surface."
},

/* ================= DOMAIN 2 — Models, Prompting & Context (8) ================= */
{
  id: 12, domain: 2,
  q: "An application sends an identical 8,000-token system prompt and policy document on every request, followed by a short varying user message. Both latency and cost are concerns. What most directly addresses both?",
  choices: [
    "Place the static system prompt and policy before the dynamic content and enable prompt caching",
    "Truncate the policy document to the first 1,000 tokens",
    "Switch to the smallest available model regardless of task fit",
    "Move the policy document into a few-shot example block"
  ],
  answer: [0],
  why: "Ordering stable content first and caching lets the repeated prefix be reused, cutting time-to-first-token and per-request cost without discarding required context. Truncation loses policy the system needs; blind downsizing risks quality; relocating the policy into few-shot examples does not by itself create a cacheable, reusable prefix."
},
{
  id: 13, domain: 2,
  q: "Prompt caching was enabled two weeks ago but usage.cache_read_input_tokens is zero on nearly every request. Which is the most likely cause?",
  choices: [
    "The system prompt includes a current timestamp, changing the prefix on every request",
    "The user messages are too short to benefit from caching",
    "The account has exceeded its cache storage quota",
    "Caching only applies to requests that use tools"
  ],
  answer: [0],
  why: "Caching is prefix-match: any byte change anywhere in the prefix invalidates everything after it. A timestamp, request ID, or unsorted JSON serialization in the cached region is the classic silent invalidator. The fix is to move volatile content after the last breakpoint. User message length is irrelevant — the cache covers the prefix, not the varying turn."
},
{
  id: 14, domain: 2,
  q: "A team's code sets a fixed thinking token budget on a current frontier model and receives a 400 error. What is the correct modern equivalent?",
  choices: [
    "Use adaptive thinking and control depth with output_config effort",
    "Lower the fixed budget below max_tokens and retry",
    "Disable thinking entirely and rely on chain-of-thought prompting",
    "Switch to a model that still accepts a fixed thinking budget"
  ],
  answer: [0],
  why: "Fixed thinking budgets are deprecated and rejected on current frontier models. Adaptive thinking lets the model decide when and how much to think, with effort (low through max) as the depth and spend control. Downgrading the model to keep a deprecated parameter is the wrong direction."
},
{
  id: 15, domain: 2,
  q: "A classification route runs at very high volume with a tight latency budget. Caching and token hygiene are already in place. Which lever should be tried next, before changing models?",
  choices: [
    "Lower the effort level for that route and measure quality on the eval set",
    "Introduce a multi-model cascade routing easy cases to a smaller model",
    "Increase max_tokens so responses are never truncated",
    "Enable extended thinking to improve classification accuracy"
  ],
  answer: [0],
  why: "Effort is the first quality-trading lever and operates within a single model, so it costs nothing in cache reuse. Classification is exactly the workload shape that usually holds quality at low effort. A cascade should be measured against this simpler alternative first, because caches are model-scoped and a cascade forfeits reuse across its models."
},
{
  id: 16, domain: 2,
  q: "Which situation most justifies few-shot examples over a purely zero-shot instruction?",
  choices: [
    "The required output format and its edge-case handling are hard to describe but easy to demonstrate",
    "The task requires multi-step numerical reasoning",
    "The prompt needs to stay under a token budget",
    "The model must call a specific tool on every request"
  ],
  answer: [0],
  why: "Few-shot earns its token cost when demonstration is cheaper than description — typically formatting conventions and edge cases. Multi-step reasoning is served by thinking, not examples; few-shot increases rather than reduces tokens; and forcing a tool call is a tool_choice or instruction concern, not an example concern."
},
{
  id: 17, domain: 2,
  q: "Which two elements of a system prompt most directly reduce confident fabrication? (Select two.)",
  choices: [
    "Explicit permission and instruction to say when it cannot find support for an answer",
    "Clear task boundaries stating what is out of scope",
    "A statement that the assistant is highly accurate and authoritative",
    "A request to always provide a complete answer"
  ],
  answer: [0, 1],
  why: "A model given no permitted way to decline will produce something. Explicit escalation rules and stated boundaries give it a correct action for the case it cannot handle. The other two options push in the opposite direction: asserting authority and demanding completeness both increase the pressure to fabricate."
},
{
  id: 18, domain: 2,
  q: "A long-running agent session degrades in quality after many turns. The earlier turns contain decisions the agent still needs, but tool results from those turns are very large. What is the best approach?",
  choices: [
    "Compact the older history so decisions survive in condensed form, and clear the bulky tool results",
    "Clear all history older than the last four turns",
    "Increase max_tokens so the model can produce longer responses",
    "Restart the session and re-prompt with the original task"
  ],
  answer: [0],
  why: "Context editing clears; compaction summarizes. Because the earlier turns carry decisions that still matter, clearing them outright loses those decisions — compaction preserves them condensed, while the bulky tool results are exactly what clearing is for. The two mechanisms are complementary, not interchangeable."
},
{
  id: 19, domain: 2,
  q: "A large, frequently-growing document corpus must be available to an agent. Which context strategy is appropriate, and why?",
  choices: [
    "Progressive discovery — load a compact index and retrieve detail on demand, keeping the per-request baseline low",
    "Monolithic — load the full corpus so the model never misses relevant material",
    "Monolithic — a single large prefix caches better than many small retrievals",
    "Progressive discovery — because retrieval is always more accurate than full context"
  ],
  answer: [0],
  why: "At scale, loading everything saturates the window, invites lost-in-the-middle degradation, and pays for content the request does not use. Progressive discovery keeps the baseline small. Note the reasoning matters: retrieval is not inherently more accurate — a bad index can hide the right document — it is the cost and saturation profile that decides this at scale."
},

/* ================= DOMAIN 3 — Integration (12) ================= */
{
  id: 20, domain: 3,
  q: "A customer-support agent exposes tools to read tickets, draft replies, issue refunds, and delete user accounts. Support staff only ever need to read tickets and draft replies. Applying least privilege, which change best reduces risk?",
  choices: [
    "Remove the refund and delete tools from the agent's configuration entirely",
    "Add logging to the refund and delete tools so misuse can be audited later",
    "Keep all tools but add a confirmation prompt before refunds and deletions",
    "Replace the agent with a larger model that follows instructions more reliably"
  ],
  answer: [0],
  why: "Least privilege means removing capability the role does not require, eliminating the attack surface rather than monitoring or guarding it. Logging is detective and acts after the damage; a confirmation prompt is compensating and depends on a human catching it; model size has nothing to do with authorization scope."
},
{
  id: 21, domain: 3,
  q: "An agent calls internal services using a single service account that holds broad read-write permissions across all tenants. Users authenticate to the application separately. What is the security gap?",
  choices: [
    "Authorization is not enforced per user at the tool boundary, so any user's request runs with full cross-tenant privilege",
    "The service account credential will expire and cause outages",
    "Service accounts cannot be used with tool-calling agents",
    "The application should use a larger model to better respect tenant boundaries"
  ],
  answer: [0],
  why: "Identity collapse: every user effectively becomes an administrator because the tool executes with the agent's privilege, not the caller's. Authorization must be enforced at the tool boundary against the end user's identity. A system prompt instructing the model to respect tenancy is not an access control."
},
{
  id: 22, domain: 3,
  q: "Two teams and an external partner product all need the same 'lookup policy document' capability. Which integration mechanism best fits, and why?",
  choices: [
    "An MCP server — one governed boundary, reusable across multiple clients, with a single place to audit what the capability can reach",
    "A direct Messages API integration in each consumer, for maximum per-consumer control",
    "An agent-to-agent protocol, so each consumer runs its own agent that negotiates with a policy agent",
    "A headless CLI invocation wrapped in a shell script that each consumer calls"
  ],
  answer: [0],
  why: "MCP's architectural argument is exactly reuse across clients plus a standard, auditable server boundary. Three bespoke direct integrations means three things to maintain and three places to audit. Agent-to-agent is far more coordination than a lookup needs, and a shared shell script is an integration mechanism only by accident."
},
{
  id: 23, domain: 3,
  q: "A knowledge base contains product manuals in prose, a table of error codes with short descriptions, and source code samples. Users most often paste an exact error code and ask what it means. Which retrieval strategy fits best?",
  choices: [
    "Hybrid search combining keyword/BM25 with dense vectors, then rerank",
    "Dense vector search only, with a high top-k",
    "Dense vector search over chunks that merge the manual and the code samples",
    "Keyword search only, since all queries contain an error code"
  ],
  answer: [0],
  why: "Embeddings are weak on exact tokens like error codes, so dense-only will miss the primary query pattern. But users also ask what the code means, which needs the prose explanation — so keyword-only is too narrow. Hybrid plus reranking covers the exact-match lookup and the conceptual follow-through."
},
{
  id: 24, domain: 3,
  q: "A RAG team adopted a new embedding model and used it only for newly added documents; older documents kept their original vectors. Retrieval quality then dropped across the board. What is the most likely cause?",
  choices: [
    "Queries are embedded with the new model but most stored vectors came from the old one, so similarity scores are not comparable",
    "The new embedding model produces lower-quality embeddings than the old one",
    "The index grew too large after adding new documents",
    "The chunking strategy changed at the same time as the embedding model"
  ],
  answer: [0],
  why: "Embeddings from different models occupy different vector spaces. Distances computed between a new-model query and old-model vectors are meaningless, which degrades results for the whole corpus, not just the new documents. Embedding migrations are all-or-nothing: re-embed everything."
},
{
  id: 25, domain: 3,
  q: "A multi-tenant RAG application must never return one tenant's documents to another. Where should the tenant constraint be applied?",
  choices: [
    "As a metadata filter applied before or during the vector search, enforced server-side",
    "In the system prompt, instructing Claude to ignore documents from other tenants",
    "As a post-processing step that removes foreign documents from the model's answer",
    "By running a separate model instance per tenant"
  ],
  answer: [0],
  why: "Tenant isolation is an access-control property and must be enforced where it cannot be bypassed — in the query itself, before content ever reaches the context. A prompt instruction is a soft control over data already exposed, and post-processing the answer means the model already saw the other tenant's data. Per-tenant model instances address nothing, since the index is the shared surface."
},
{
  id: 26, domain: 3,
  q: "An agent processes long PDFs. A single chunking strategy is applied uniformly: fixed 500-token splits with no overlap. Users report that answers spanning a section boundary are frequently wrong or incomplete. What should change?",
  choices: [
    "Chunk on semantic boundaries such as headings and paragraphs, and add overlap so answers do not fall in the seam",
    "Reduce chunk size to 200 tokens so more chunks are retrieved",
    "Increase top-k substantially so more of the document is always in context",
    "Switch to a model with a larger context window"
  ],
  answer: [0],
  why: "The symptom points precisely at boundaries: a semantic unit is being split and its halves never co-retrieve. Semantic splitting plus overlap addresses the cause. Smaller chunks make the seam problem worse; raising top-k dilutes context and raises cost without fixing the split; a bigger window does not help if the right chunk is never retrieved."
},
{
  id: 27, domain: 3,
  q: "A nightly job analyzes every merged PR in depth and posts a summary the next morning. It currently runs synchronously through the standard API and is expensive. What is the appropriate change?",
  choices: [
    "Move it to the Batch API for roughly half the cost, since a next-morning deliverable tolerates a long turnaround",
    "Reduce the analysis depth so each request costs less",
    "Run it on the smallest available model regardless of output quality",
    "Cache the PR diffs so repeated analysis is cheaper"
  ],
  answer: [0],
  why: "Match latency to task priority. The deliverable is needed the next morning, so an asynchronous window is free in business terms and buys a 50% cost reduction with no quality trade-off. The other options all trade quality or address a cost driver that is not the one in play here."
},
{
  id: 28, domain: 3,
  q: "A team adds Claude Code to their CI pipeline for security review. The job hangs and eventually times out with no output. What is the most likely cause?",
  choices: [
    "It is running in interactive mode, so it blocks waiting for terminal input that CI never provides",
    "The repository is too large for the context window",
    "CI runners cannot make outbound network requests to the API",
    "The security review prompt triggered a refusal"
  ],
  answer: [0],
  why: "This is the signature of interactive mode in a pipeline: the process waits on stdin indefinitely and produces nothing parseable. The fix is headless invocation with structured output — claude -p \"...\" --output-format json. Context limits, network blocks, and refusals all produce errors or output, not a silent hang."
},
{
  id: 29, domain: 3,
  q: "At what point in an agent's request path must a tool's authorization check run for it to be a real control?",
  choices: [
    "Inside the tool implementation, before the action is taken, against the caller's identity",
    "In the system prompt, as an instruction the model follows before calling the tool",
    "In the tool description, so the model knows who may use it",
    "In output screening, so unauthorized results are removed before they reach the user"
  ],
  answer: [0],
  why: "Tool permissions are the one hard layer in the safety stack — they determine what is physically possible. Prompts and tool descriptions are instructions the model can be talked around, and output screening runs after the action has already happened, which is far too late for a refund or a deletion."
},
{
  id: 30, domain: 3,
  q: "Which three signals should production observability capture to make a single bad answer diagnosable after the fact? (Select three.)",
  choices: [
    "The prompt version and model configuration used for that request",
    "The retrieval query and the IDs of the chunks actually returned",
    "Every tool call with its arguments and result status, plus stop_reason per turn",
    "The end user's full profile record from the CRM"
  ],
  answer: [0, 1, 2],
  why: "To explain an answer you need to reconstruct what the model saw, what it did, and under what configuration. Prompt version attributes regressions to changes; retrieval IDs distinguish a retrieval failure from a generation failure; the tool trace shows the actual execution path. Pulling the user's full CRM record adds personal data to logs without adding diagnostic value — the opposite of what data minimization requires."
},
{
  id: 31, domain: 3,
  q: "An enterprise security team refuses to issue long-lived API keys for a service that will call the Claude API from their Kubernetes cluster. What is the appropriate authentication approach?",
  choices: [
    "Workload identity federation, exchanging a short-lived cluster-issued token for API credentials",
    "Store a long-lived key in a secrets manager and inject it at pod startup",
    "Put the key in the system prompt so it is only present at request time",
    "Have each end user supply their own API key through the application"
  ],
  answer: [0],
  why: "Federation is exactly the mechanism for a client that will not accept long-lived secrets: the workload proves its identity and receives short-lived, automatically refreshed credentials. A secrets manager still stores a long-lived key, which is what was refused. Putting a credential in a prompt exposes it to the model context and any logging of it — never do this. Per-user keys shift the problem to users and break the service model."
},

/* ================= DOMAIN 4 — Evaluation, Testing & Optimization (10) ================= */
{
  id: 32, domain: 4,
  q: "A RAG system suddenly returns confident but incorrect answers after a document refresh, while latency and model version are unchanged. What is the most likely first place to investigate?",
  choices: [
    "The retrieval/indexing step returning irrelevant or stale chunks",
    "The model weights have silently changed",
    "The temperature setting is too low",
    "The context window has shrunk"
  ],
  answer: [0],
  why: "Reason from what changed. The document refresh is the only variable, and a broken re-index or mismatched embeddings feeds poor context to a model that will then state a wrong answer fluently. None of the other options would be triggered specifically by a document refresh."
},
{
  id: 33, domain: 4,
  q: "Which behaviors should be graded with code rather than an LLM judge? (Select all that apply.)",
  choices: [
    "Whether the output validates against the required JSON schema",
    "Whether every cited case identifier exists in the source corpus",
    "Whether the response stayed under the maximum length",
    "Whether the explanation is appropriately empathetic for a distressed customer"
  ],
  answer: [0, 1, 2],
  why: "The grading ladder says reach for the cheapest reliable method first: code-based checks run in milliseconds, cost almost nothing, and never drift. Schema validity, citation-target existence, and length are all deterministic. Empathy requires interpretation and is the case a calibrated judge is for."
},
{
  id: 34, domain: 4,
  q: "A team evaluates response quality with an LLM judge. Which two changes would most improve the trustworthiness of the scores? (Select two.)",
  choices: [
    "Replace free-form 1-to-10 scores with a small fixed set of labeled verdicts backed by a detailed rubric",
    "Calibrate the judge against a set of human-labeled examples and measure agreement",
    "Use the same model as the one being evaluated, so the judge understands its output style",
    "Raise the judge's effort level to maximum on every case"
  ],
  answer: [0, 1],
  why: "Constrained verdicts with a rubric make scores reproducible; calibration against human labels tells you whether the judge is measuring what you think. Using the same model introduces self-preference bias — judge with a different model. Maximum effort raises cost without addressing either source of untrustworthiness."
},
{
  id: 35, domain: 4,
  q: "Why should evaluation criteria be defined before implementation begins?",
  choices: [
    "They force success to be stated measurably, expose design assumptions while changing them is still cheap, and provide the gate for every later change",
    "Regulators require evaluation documentation before development starts",
    "Writing evaluations later is technically more difficult",
    "Evaluation datasets cannot be constructed once production traffic exists"
  ],
  answer: [0],
  why: "Those three reasons are the whole argument for evals-before-code. Writing the eval first reveals that there is no ground truth, or that two stakeholders disagree about what correct means — and week one is when that is cheap to resolve. The other options are not true in general."
},
{
  id: 36, domain: 4,
  q: "A newer Claude model has been released and the team wants to switch to it. What is the best approach?",
  choices: [
    "Run the eval suite on the new model, check cost and latency, roll it out gradually, and keep the ability to roll back",
    "Switch in production and monitor error rates for a week",
    "Switch only for new customers, leaving existing customers on the current model permanently",
    "Benchmark the new model on published evaluations and adopt it if it scores higher"
  ],
  answer: [0],
  why: "All four clauses matter. Your eval suite measures your task, which public benchmarks do not; cost and latency can regress even when accuracy improves; gradual rollout limits blast radius; and rollback is what makes the change reversible. An option missing any clause is incomplete."
},
{
  id: 37, domain: 4,
  q: "After a prompt change, aggregate accuracy on the eval set improved from 88% to 91%. What should be verified before shipping?",
  choices: [
    "Whether any segment regressed, since an aggregate gain can hide a loss in a subgroup that matters",
    "Whether the eval set is large enough to reach 95% confidence on the aggregate",
    "Whether the same prompt improves scores on a public benchmark",
    "Whether the improvement persists after switching to a smaller model"
  ],
  answer: [0],
  why: "Averages hide disparate impact and regressions in important minorities of traffic. Segmentation is the discipline that catches a change which helps the common case and breaks the high-stakes one. Confidence intervals matter too, but a segment regression is the failure that reaches production and hurts."
},
{
  id: 38, domain: 4,
  q: "An eval dataset is assembled entirely from hand-written cases an engineer thought of. What is the primary weakness?",
  choices: [
    "It does not reflect the distribution of real production traffic, so scores will not predict production behavior",
    "Hand-written cases cannot be graded with code",
    "It will be too small to run automatically",
    "Synthetic cases are always more reliable than human-written ones"
  ],
  answer: [0],
  why: "A dataset should be built from mixed sources: production traffic as the backbone for distribution, curated edge cases for the known failure modes, synthetic generation for rare-but-important coverage, and adversarial cases for safety. Imagination alone systematically misses what users actually send."
},
{
  id: 39, domain: 4,
  q: "Monthly API spend rose 40% while request volume stayed flat and no prompt or model change was deployed. What should be checked first?",
  choices: [
    "Cache read token counts, to find whether a silent invalidator broke prefix reuse",
    "Whether the model provider raised prices",
    "Whether output token limits were increased",
    "Whether more users were added to the account"
  ],
  answer: [0],
  why: "Flat volume with rising cost points at cost per request, and the largest single swing factor is cache hit rate. A dependency change that reordered tools, a newly added timestamp, or a changed tool set can silently stop the prefix from matching. Verify with cache_read_input_tokens before investigating anything else."
},
{
  id: 40, domain: 4,
  q: "A production incident is resolved by fixing a prompt. What should happen to the incident afterward?",
  choices: [
    "The failing case becomes a permanent case in the eval suite so the regression cannot silently return",
    "The incident is documented in the postmortem and closed",
    "The prompt is frozen so it cannot be changed again",
    "The case is added to the training data for a fine-tune"
  ],
  answer: [0],
  why: "This is the mechanism by which a system becomes more reliable rather than merely older: every incident converts into a permanent gate. A postmortem records what happened but does not prevent recurrence; freezing the prompt prevents improvement rather than regression."
},
{
  id: 41, domain: 4,
  q: "Which metric best reflects the true economics of an agentic system?",
  choices: [
    "Cost per completed task",
    "Cost per API request",
    "Input tokens per request",
    "Average response latency"
  ],
  answer: [0],
  why: "An agent may take many requests to finish one unit of work. A configuration with cheaper requests that needs three more turns or a retry is not cheaper. Per-request cost and per-request token counts are inputs to the calculation, not the answer; latency is a separate axis entirely."
},

/* ================= DOMAIN 5 — Governance, Safety & Risk (9) ================= */
{
  id: 42, domain: 5,
  q: "A team argues that a carefully written system prompt is sufficient safety for their agent. What is the strongest architectural objection?",
  choices: [
    "It is a single point of failure — controls should be layered across input checks, system prompt, tool permissions, output checks, and monitoring so one miss does not lead to harm",
    "System prompts consume tokens that could be used for retrieved context",
    "System prompts cannot be versioned or tested",
    "Users can read the system prompt and work around it"
  ],
  answer: [0],
  why: "Defense in depth is the organizing principle of the whole safety domain. The system prompt is a soft control — an instruction the model can be argued out of — and it is one layer of five. The others are token budget concerns or claims that are simply not true."
},
{
  id: 43, domain: 5,
  q: "An agent reads incoming customer emails and can issue refunds and send outbound replies. Which combination correctly handles the risk? (Select all that apply.)",
  choices: [
    "Treat email content as untrusted data rather than as instructions to follow",
    "Limit what the agent is able to do while it is handling that content",
    "Require human approval for refunds and outgoing messages",
    "Instruct the model in the system prompt to ignore instructions found in emails"
  ],
  answer: [0, 1, 2],
  why: "The design is three-part: classify the content as data, constrain the capability available while processing it, and gate the irreversible or outward-facing actions on a human. The fourth option is not harmful, but it is a soft instruction against an adversarial input — worth adding, and nowhere near sufficient on its own, so it is not part of the correct control set."
},
{
  id: 44, domain: 5,
  q: "An agent performs hundreds of read operations and a handful of account modifications each day. How should human approval be applied?",
  choices: [
    "Require approval only for the high-impact or irreversible actions, let reads run automatically, and audit a sample of them",
    "Require approval for every action so nothing is unreviewed",
    "Require approval for nothing, and review the daily log the following morning",
    "Require approval only when the model reports low confidence"
  ],
  answer: [0],
  why: "Approval must be calibrated by reversibility, impact, and confidence. Approving everything destroys the value of the system and trains reviewers to rubber-stamp; approving nothing is negligent. The sampled audit of the automatic path is the clause people omit — it is how you find out the low-risk classification was wrong."
},
{
  id: 45, domain: 5,
  q: "A healthcare client wants to process clinical notes with Claude. Which verification matters most before design proceeds?",
  choices: [
    "That a Business Associate Agreement covers the specific services and settings being used, and that only the minimum PHI needed is sent",
    "That the model was trained on medical literature",
    "That all clinicians sign an acceptable-use policy",
    "That responses are reviewed by a physician before reaching a patient"
  ],
  answer: [0],
  why: "Both halves are load-bearing: a BAA covering one service does not cover a different service added later or a setting outside the agreement, and minimum-necessary is an architecture constraint that dictates what goes in the prompt, what you retrieve, and what you log. Physician review is a good control but does not establish the legal basis for processing PHI at all."
},
{
  id: 46, domain: 5,
  q: "A user exercises their GDPR right to erasure. What does satisfying that request actually require?",
  choices: [
    "Deleting the data from every place it lives — including embeddings, caches, logs, and any eval datasets built from it — which means tracking where their data goes in the first place",
    "Deleting the user's record from the primary database and confirming within 30 days",
    "Excluding the user from future model requests",
    "Requesting deletion from the model provider's training corpus"
  ],
  answer: [0],
  why: "This is the requirement architects most often discover too late. Derived copies are still personal data: vectors, cached prefixes, logs, and eval sets built from production traffic are all in scope. The real obligation therefore lands at ingest — subject-keyed metadata, retention limits, and a purge path must exist before the first request arrives."
},
{
  id: 47, domain: 5,
  q: "A federal agency requires FedRAMP compliance. Which statement should the architect verify?",
  choices: [
    "That the exact deployment path — cloud platform, region, and service — holds the authorization level the agency's data requires",
    "That the model provider holds a FedRAMP authorization",
    "That the application code has passed a FedRAMP audit",
    "That all agency users access the system from government networks"
  ],
  answer: [0],
  why: "Authorization attaches to a specific service offering, in a specific boundary, at a specific impact level (Low, Moderate, High) — not to a company. 'The vendor is FedRAMP authorized' is never the answer; 'this deployment path is authorized at this level for this data' is."
},
{
  id: 48, domain: 5,
  q: "A hiring-adjacent screening system must be shown to be fair. Which combination is correct? (Select all that apply.)",
  choices: [
    "Use evals to compare outcomes across demographic groups",
    "Keep humans responsible for final decisions",
    "Document the system's limitations",
    "Keep monitoring after launch"
  ],
  answer: [0, 1, 2, 3],
  why: "All four are required, and each covers a different failure. Segmented evals catch disparate impact that aggregate accuracy hides; human accountability means responsibility does not transfer to a model; documented limits set correct expectations; and continued monitoring catches drift, because a system fair at launch is not permanently fair."
},
{
  id: 49, domain: 5,
  q: "A safety classifier that screens inputs becomes unavailable during a partial outage. What should the system do?",
  choices: [
    "Deny or degrade to a restricted mode — fail closed",
    "Proceed without the check and log that it was skipped",
    "Retry the classifier indefinitely until it responds",
    "Fall back to having the model classify its own input"
  ],
  answer: [0],
  why: "A control that is skipped when its checker is unavailable is not a control. Logging the skip records the gap without closing it; indefinite retry converts a safety failure into an availability failure with no defined behavior; and asking the model to screen its own input removes the independence that made screening meaningful."
},
{
  id: 50, domain: 5,
  q: "A legal research assistant must not invent case citations. Which combination of controls addresses this? (Select all that apply.)",
  choices: [
    "Base answers on retrieved sources only",
    "Require each citation to point to one of those retrieved sources",
    "Automatically check that each cited case actually exists",
    "Let the model state when it cannot find support"
  ],
  answer: [0, 1, 2, 3],
  why: "All four clauses together are the grounding pattern. Retrieval supplies the facts; the citation constraint binds claims to them; the automated existence check is a code-based grader that catches fabrication deterministically; and the permission to decline is what prevents the model inventing something when nothing supports the answer."
},

/* ================= DOMAIN 6 — Stakeholder Communication & Lifecycle (9) ================= */
{
  id: 51, domain: 6,
  q: "A project reaches week eleven and is blocked because security has not approved the data path. What should have happened during discovery?",
  choices: [
    "Identify every stakeholder early — including the sponsor, end users, security, legal, and compliance — and involve anyone who must approve the project from the start",
    "Build a proof of concept first, then present it to security with evidence it works",
    "Design to the strictest possible security posture so no review is needed",
    "Escalate to the sponsor to override the security team's timeline"
  ],
  answer: [0],
  why: "An integration that skips security review never reaches production. Anyone who can say no belongs in discovery, when changing the design is still cheap. A working proof of concept does not make an unacceptable data path acceptable, over-designing wastes budget on constraints that may not exist, and escalation makes an adversary of a required approver."
},
{
  id: 52, domain: 6,
  q: "A client offers four candidate use cases. Which is the best choice for a first pilot?",
  choices: [
    "A contained use case with clear current-state metrics, available data, an engaged sponsor, and manageable risk",
    "The highest-value use case, so the return justifies the investment",
    "The most technically interesting use case, so the team builds the deepest capability",
    "The most visible use case, so executives see the results"
  ],
  answer: [0],
  why: "A pilot's job is to produce evidence, not revenue. All five properties are required: without a current-state baseline you cannot prove improvement, and 'it feels better' does not fund phase two. High-value, interesting, and visible use cases are usually the ones with unavailable data, unbounded scope, or unsurvivable risk."
},
{
  id: 53, domain: 6,
  q: "Six months after a system ships, a new engineer asks why the team chose a workflow instead of an agent. What artifact should answer this?",
  choices: [
    "An architecture decision record capturing the context, the options considered, the decision, the reasons for it, and its consequences",
    "The original requirements document",
    "The eval suite and its historical results",
    "The runbook for the system"
  ],
  answer: [0],
  why: "An ADR exists precisely for this moment. Options considered and consequences are the two parts people omit, and they are the two parts that stop a team either re-litigating the decision or repeating the mistake it was avoiding. Requirements say what was needed, evals say whether it works, and runbooks say how to operate it — none explains why."
},
{
  id: 54, domain: 6,
  q: "Adoption of a launched system is at 12% three months in. What should the architect do first?",
  choices: [
    "Find out why — how well it fits people's daily work and tools, whether they were trained, whether they trust it, and what they say about it — then fix those issues",
    "Add the most-requested features from the original backlog",
    "Upgrade to a more capable model to improve output quality",
    "Mandate use of the system through the sponsor"
  ],
  answer: [0],
  why: "Diagnose before you fix. Low adoption has four common causes with four different remedies: fit is an integration problem, training is an enablement problem, trust is an accuracy-and-transparency problem, and sentiment usually reflects one of the others. Adding features or capability to a system nobody uses spends budget on a cause you have not established."
},
{
  id: 55, domain: 6,
  q: "Which describes a handoff most likely to survive the architect's departure?",
  choices: [
    "Hand over runbooks, the eval suite, dashboards and alerts, and escalation paths, then let the team run operations while you are still around to help",
    "Deliver complete architecture documentation and a recorded walkthrough on the final day",
    "Schedule a series of knowledge-transfer sessions covering every component",
    "Remain the escalation point of contact for six months after the project ends"
  ],
  answer: [0],
  why: "Two parts, and the sequencing is the part people get wrong. The artifacts matter, but the team must actually operate the system, hit real problems, and resolve them with you available as a backstop — that is the only way you discover which parts of the documentation do not work. A document drop on the last day has never been tested."
},
{
  id: 56, domain: 6,
  q: "How should a latency commitment be expressed in an SLA for a Claude-based system?",
  choices: [
    "As a p95 (or p99) target, with a defined degraded mode when a dependency is unavailable",
    "As an average response time across all requests",
    "As a guaranteed maximum for every request",
    "As the model provider's published latency figures"
  ],
  answer: [0],
  why: "Averages hide the tail that users actually complain about, and a hard per-request guarantee is not something a system with external dependencies can honor. The degraded-mode clause is part of the SLA rather than an afterthought, because availability includes your retrieval store and your tools. Provider figures cover one hop of a multi-hop path."
},
{
  id: 57, domain: 6,
  q: "A stakeholder expects the system to give the same answer to the same question every time. What must the architect communicate?",
  choices: [
    "That the system is non-deterministic, so quality is committed as a measured rate on a defined eval set with stated behavior on the remainder",
    "That determinism can be achieved by setting temperature to zero",
    "That the question is unlikely to be asked identically twice in practice",
    "That determinism will improve as the model matures"
  ],
  answer: [0],
  why: "Non-determinism violates what stakeholders expect from software and must be surfaced explicitly, before the demo rather than after the incident. This is why the eval suite is a stakeholder artifact and not merely an engineering one: it converts 'it usually works' into a number that can go into a contract."
},
{
  id: 58, domain: 6,
  q: "An architect presents three viable architectures with their trade-offs and asks the steering committee to choose. What is missing?",
  choices: [
    "A recommendation — the architect has the most information and owes a defended position, not just an enumeration",
    "A cost estimate for each option",
    "A fourth option for completeness",
    "A vote from the engineering team"
  ],
  answer: [0],
  why: "Stakeholders cannot act on 'it depends.' The obligation is to present the options, what each costs, what each gives up, and which one you recommend and why. Handing the decision to people with less information is an abdication dressed as consultation."
},
{
  id: 59, domain: 6,
  q: "During discovery a business lead says the goal is 'better customer support.' Which restatement is a usable requirement?",
  choices: [
    "At least 92% of refund-eligibility determinations match the policy engine, with p95 response under 4 seconds and escalation on the remainder",
    "Customer satisfaction scores should increase measurably after launch",
    "Support agents should find the system helpful in their daily work",
    "The system should handle the majority of incoming tickets without human involvement"
  ],
  answer: [0],
  why: "A usable requirement names a metric, a threshold, a latency budget, and the behavior on the cases that fall outside it — which is exactly what the eval suite will encode. The others are outcomes or aspirations with no defined measurement, no threshold, and no specified behavior for the failure case."
},

/* ================= DOMAIN 7 — Developer Productivity & Enablement (4) ================= */
{
  id: 60, domain: 7,
  q: "A capability must reach three specific teams, with version-controlled updates and the ability to roll back to a prior version. Which Skills distribution mechanism fits best?",
  choices: [
    "A plugin assigned to those groups, with install preferences and version-controlled updates from a connected repository",
    "An org-provisioned Skill, which everyone in the organization receives",
    "A Claude Code project Skill committed to each team's repository",
    "An API Skill called programmatically with a pinned version"
  ],
  answer: [0],
  why: "Plugins are the strongest governance option for group-scoped distribution: group targeting, install preferences (required, installed by default, or available), and versioned updates from a connected repo. Org-provisioned Skills reach everyone and have no native rollback. Project Skills would work but require the same artifact maintained in three repos; API Skills are machine-to-machine rather than human-facing."
},
{
  id: 61, domain: 7,
  q: "A team's root CLAUDE.md has grown to cover conventions for every subproject. Engineers report that rules meant for one module are being applied in unrelated ones. What is the fix?",
  choices: [
    "Scope instructions hierarchically across user, project, and directory CLAUDE.md files, letting the most specific rule win on conflict",
    "Shorten the root CLAUDE.md so fewer rules can conflict",
    "Move all rules into enforceable settings instead of CLAUDE.md",
    "Maintain a separate root CLAUDE.md per branch"
  ],
  answer: [0],
  why: "One flat instruction blob causes directory-specific rules to bleed into unrelated subprojects. All three scopes are loaded and merged with the most specific winning, so the fix is to place each rule at the level it applies to. Shortening loses rules rather than scoping them; settings are for things that must be enforced rather than for conventions; and per-branch files do not address the module dimension at all."
},
{
  id: 62, domain: 7,
  q: "Which check in a team's verification checklist for AI-generated code is about accountability rather than code quality?",
  choices: [
    "The developer submitting the change can explain what the code does and why, including how it handles inputs it was not explicitly tested against",
    "Tests exist and pass, and behavior matches the requirement including edge cases",
    "No secrets in code; inputs validated; external calls use least-privilege access",
    "The code reads clearly, follows team conventions, and contains no unexplained complexity"
  ],
  answer: [0],
  why: "The first three check the artifact; the fourth checks that a human is answerable for it. A change nobody on the team can explain is unmaintainable regardless of test results, and the reviewer has no basis for judging the untested paths — which is precisely where the risk lives."
},
{
  id: 63, domain: 7,
  q: "An architect is preparing to disengage from a team that now runs a live Claude system. Which approach best produces self-sufficiency?",
  choices: [
    "Capture known symptom-to-cause-to-action paths as runbooks and define named escalation paths, so the team needs the architect for new problems rather than familiar ones",
    "Remain available on a shared channel for ad-hoc questions indefinitely",
    "Produce a comprehensive architecture document covering every component in detail",
    "Train one engineer as the designated expert for all operational issues"
  ],
  answer: [0],
  why: "Operational support is translation plus self-sufficiency: connect symptoms to architecture causes, then leave behind the artifacts. Every issue resolved for the team should end in a runbook entry, or it will be resolved again. Indefinite availability prevents self-sufficiency; an architecture document explains structure but not what to do at 2am; and a single designated expert is a new single point of failure."
}
];
