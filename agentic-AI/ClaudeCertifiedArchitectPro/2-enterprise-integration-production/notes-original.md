Evals before code: why the order matters

First, state what success means in measurable terms
Second, expose design assumptions early, when changing them is still cheap
Third, give yourself a gate that can determine whether a model swap, a prompt change, or a new retrieval strategy measurably improved the system


The grading ladder: choosing how to grade
Not every behavior should be graded the same way, and the choice of grading method follows a deliberate ladder. Reach for the cheapest reliable method first and climb only when the behavior demands it.

Code-based grading, wherever the behavior allows it. Deterministic checks, including schema validation, exact match, length, and presence, run in milliseconds, cost almost nothing, and never drift. If a behavior can be checked in code, then it should be.
LLM-as-judge, when the behavior needs interpretation. Use a judge model for outputs that require judgment. Make the judging rigorous by using detailed rubrics, constrained verdicts (a small fixed set of labels rather than free-form scores), calibration against human-labeled examples, and grading with a different model than the one whose outputs you're evaluating, to avoid self-preference.
Human grading, as the last resort. Reserve human review for high-stakes or novel behaviors where neither code nor a calibrated judge is trustworthy yet. It is the most expensive and least scalable option.