# Mock Exam

**Open [`index.html`](index.html) in a browser.** Double-click it, or drag it onto a browser window. No server, no build step, no network.

63 original practice items weighted to the official CCAR-P blueprint:

| Domain | Items |
|---|---:|
| 1. Solution Design & Architecture | 11 |
| 2. Models, Prompting & Context Engineering | 8 |
| 3. Integration | 12 |
| 4. Evaluation, Testing & Optimization | 10 |
| 5. Governance, Safety & Risk Management | 9 |
| 6. Stakeholder Communication & Lifecycle | 9 |
| 7. Developer Productivity & Enablement | 4 |
| **Total** | **63** |

Ten items are multi-response, matching the real format where each item states how many answers to select.

## Modes

- **Full exam** — all 63 items, 120-minute timer, no feedback until you submit.
- **Quick 20** — 20 items sampled proportionally across domains, 38-minute timer.
- **Practice** — pick your domains, no timer, correct answer and reasoning shown as soon as an item is fully answered.

Keyboard: <kbd>1</kbd>–<kbd>4</kbd> select · <kbd>←</kbd>/<kbd>→</kbd> navigate · <kbd>F</kbd> flag.

## How to actually use it

Start in **Practice** by domain and **read every explanation, including on items you got right**. Each explanation says why the distractors lose, which is the skill the real exam tests — the correct answer is rarely the hard part.

Move to **Full exam** only when explanations stop telling you anything new. Then use **Retry missed items** on the results screen to drill the gaps.

## About the score

The pass mark is **720 / 1000**. The scaled score here is an *estimate* derived from your raw percentage, anchored so that 70% raw ≈ 720. The real exam's scale comes from a formal standard-setting study, so the mapping is not identical — **treat anything borderline here as not yet ready.**

Domain percentages are diagnostic only, exactly as on the real score report: they tell you what to restudy, not whether you would pass.

## Editing the bank

Questions live in [`questions.js`](questions.js), one object per item:

```js
{
  id: 64, domain: 3,
  q: "The scenario and the question.",
  choices: ["A", "B", "C", "D"],
  answer: [1],            // array of correct indices; length > 1 = multi-response
  why: "Why the right answer is right AND why each distractor loses."
}
```

`id` must be unique. `answer` indices are into the unshuffled `choices` array. Keep `why` explaining the distractors — that is where the learning is.

---

**These are not real exam questions.** They are original items written against the published exam objectives. Exam content is confidential and covered by an NDA you accept before testing; nothing here is drawn from a live item bank.

Progress is saved to this browser's local storage so you can close the tab and resume. Nothing is uploaded anywhere.
