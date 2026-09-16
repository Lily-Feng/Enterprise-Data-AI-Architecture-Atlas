The risk categories that recur in LLM systems
Most LLM-system risk falls into a small set of categories. Identify these categories and check your designs against each:

Direct prompt injection: A user crafts input that overrides the system's instructions and redirects its behavior.
Indirect prompt injection: Malicious instructions arrive through retrieved content or tool outputs that the model treats as trusted and the vector input screening does not catch.
Token-budget exhaustion: Oversized or adversely padded inputs consume the context or output budget, truncating work or inflating cost.
Tool and action abuse: The model is induced to call a side-effecting tool outside policy, the failure the action-authorization control exists to stop.
Data exposure: Sensitive fields enter the context window or the logs where they should not, creating a leak independent of model behavior.


System vulnerability assessment: where to look
Walk the request and data paths together. At each entry point, user input, retrieved content, tool outputs, the model's own output, and the logs, ask what an adversary could do and which control stands in the way. Look for anywhere without a control where there could be a plausible attack.

Documenting the risk assessment as a deliverable
The risk assessment should be a written artifact. For each identified risk, record the category, the affected component, a likelihood-and-impact judgment, and the mitigation control with an owner and an evidence artifact. That document is what the security reviewer will sign off on, and it is what the cumulative exercise at the end of this module expects you to be able to produce.


Risk for a support agent:
1. Indirect prompt injection via the knowledge base. Retrieved content can carry instructions; mitigation is to treat retrieved text as untrusted and screen tool/content inputs, not just user input.

2. Tool and action abuse on the refund tool. Mitigation is an action-authorization check that runs before the refund tool executes, independent of the model's output.

3. Token-budget exhaustion on large knowledge-base documents. Mitigation is chunking and input limits plus budget monitoring so a large document cannot truncate the work silently.

4. Data exposure in the request log. Mitigation is server-side redaction of sensitive fields before anything is logged.
