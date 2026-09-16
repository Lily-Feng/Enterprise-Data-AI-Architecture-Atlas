=======Responsible AI, Safety & Risk (8 questions)

Treat email content as untrusted data, limit what the agent can do while handling it, and require human approval for refunds and outgoing messages


It's a single point of failure. Controls should be layered (input checks, system prompt, tool permissions, output checks, monitoring) so that one miss doesn't lead to harm.


Require approval only for high-impact or irreversible actions, let low-risk actions like reading run automatically, and audit a sample of them

That a Business Associate Agreement (BAA) covers the specific services and settings being used, and that only the minimum PHI needed is sent



GDPR: Deleting the data from every place it lives, including embeddings, caches, logs, and any eval datasets built from it, which means tracking where their data goes in the first place



Base answers on retrieved sources, require each citation to point to one of those sources, check automatically that each cited case exists, and let the model say when it can't find support


 Use evals to compare outcomes across demographic groups, keep humans responsible for final decisions, document the system's limitations, and keep monitoring after launch.



 ======Stakeholder Engagement, Lifecycle & GTM (8 questions)


 Identifying every stakeholder early, including the sponsor, end users, security, legal, and compliance, and involving anyone who must approve the project from the start

Handing over runbooks, the eval suite, dashboards and alerts, and escalation paths, then letting the team run operations while you're still around to help


Find out why: how well it fits into people's daily work and tools, whether they were trained, whether they trust it, and what they say about it. Then fix those issues.

An architecture decision record that captures the context, the options considered, the decision, the reasons for it, and its consequences



Which of these is the best choice for a first pilot?
A contained use case with clear current-state metrics, available data, an engaged sponsor, and manageable risk


A newer Claude model has been released, and the team wants to switch to it. What's the best approach?
Run the eval suite on the new model, check cost and latency, roll it out gradually, and keep the ability to roll back
