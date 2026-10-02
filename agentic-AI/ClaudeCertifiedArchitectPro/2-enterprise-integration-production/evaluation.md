# Evals before code, and the grading ladder

> Companion to [README.md](README.md) §1–2.
>
> **The one-line version:** evals are not a testing phase after the build — they are **acceptance criteria written first.** And not every behavior is graded the same way: reach for the cheapest reliable method, climb only when the behavior demands it.

---

## 1. Evals before code — why the order matters

Three reasons:

1. **State what success means in measurable terms.** Writing the eval forces the definition.
2. **Expose design assumptions early**, while changing them is still cheap.
3. **Give yourself a gate** — something that can determine whether a model swap, a prompt change, or a new retrieval strategy **measurably** improved the system.

---

## 2. The grading ladder — choosing how to grade

Not every behavior should be graded the same way, and the choice of grading method follows a deliberate ladder.

> **Reach for the cheapest reliable method first, and climb only when the behavior demands it.**

| Rung | Method | Reach for it when | Properties |
|---|---|---|---|
| **1** | **Code-based grading** | Wherever the behavior allows it — deterministic checks: schema validation, exact match, length, presence. | Runs in **milliseconds**, costs almost nothing, and **never drifts**. If a behavior can be checked in code, it should be. |
| **2** | **LLM-as-judge** | The behavior needs **interpretation** — outputs that require judgment. | Trustworthy only with the four controls below. |
| **3** | **Human grading** | **Last resort** — high-stakes or novel behaviors where neither code nor a calibrated judge is trustworthy yet. | The **most expensive and least scalable** option. |

### Making rung 2 rigorous

Four controls make a judge trustworthy:

- **Detailed rubrics**
- **Constrained verdicts** — a small fixed set of labels, not free-form scores
- **Calibration against human-labeled examples**
- **A different model** than the one whose outputs you are evaluating, to avoid **self-preference**
