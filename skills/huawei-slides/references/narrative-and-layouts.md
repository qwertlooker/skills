# Narrative and layout recipes

## Content principles

Treat the deck as a decision instrument. Start from what the audience needs to understand, believe, or approve.

### Presentation brief

Before outlining pages, define six items:

1. **Audience:** Who attends, and who decides?
2. **Interest:** Which outcome matters most—growth, efficiency, cost, risk, compliance, delivery, or technical feasibility?
3. **Knowledge:** What can be assumed, and what needs one layer of explanation?
4. **Attitude:** Are they supportive, neutral, skeptical, or committed to another approach?
5. **Objective:** What should they understand, believe, or decide after the meeting?
6. **Constraint:** Speaking time, page limit, required template, available evidence, and confidentiality level.

Write the objective in a testable form:

> Enable [audience] to understand/believe/decide [specific outcome] within [meeting context or time].

Use likely objections to decide where evidence belongs. Address a decisive objection before the decision page; do not create an exhaustive rebuttal section unless the meeting requires one.

### Deck-level logic

Choose one dominant sequence:

1. **Problem–cause–solution–value** for proposals and technical remedies.
2. **Current state–gap–path–outcome** for transformation and planning.
3. **Trend–challenge–response–proof** for market or industry presentations.
4. **Goal–architecture–capability–roadmap** for solution and platform decks.
5. **Conclusion–evidence–risk–decision** for leadership briefings.

Do not force every deck to include company introduction, market trend, architecture, roadmap, and case studies. Include only pages that advance the audience's decision.

### Page-level logic

Each content slide should pass this test:

- **Claim:** What is the one takeaway?
- **Proof:** Which facts, comparison, mechanism, or example supports it?
- **Implication:** Why does it matter to this audience?

Use the slide title for the claim. Use the body for proof. Add the implication only if it is not already obvious.

### Translate data into business meaning

Use three levels without fabricating causality:

1. **Source fact:** Preserve the measured technical or operational metric.
2. **Operational consequence:** Explain what the metric changes in the real process.
3. **Decision implication:** State why it supports the proposed choice.

Example:

- Weak: “Inference throughput increased 2.3×.”
- Better when supported: “Inference throughput increased 2.3×, allowing the same cluster to absorb the forecast peak without immediate expansion.”

Do not convert a benchmark into ROI, savings, quality improvement, or customer value unless a valid model or source supports the conversion. Label scenarios and estimates explicitly.

### Give complex diagrams a three-second summary

Place one short sentence beside an architecture or network diagram that answers:

- What is this system designed to achieve?
- Which mechanism is decisive?
- What should the audience notice first?

The summary is not a second title. It is a reading aid that connects the diagram to the slide takeaway.

### Title transformation examples

| Weak topic title | Strong takeaway title |
| --- | --- |
| 行业趋势 | 数智化需求正在从单点工具转向端到端业务闭环 |
| 当前问题 | 数据、模型与流程割裂是规模化落地的主要瓶颈 |
| 解决方案 | 统一底座与分层解耦可同时提升复用率和交付速度 |
| 项目计划 | 以两阶段试点验证精度，再复制到高价值场景 |
| 客户案例 | 标准化方法已在同类场景验证周期和质量收益 |

## Layout recipes

### 1. Cover

- One short title, optional subtitle, date/organization.
- Default to one strong high-key contextual image or a clean light canvas. Use a dark cover only when the venue, audience, or supplied reference supports it.
- No agenda, paragraph, or decorative icon grid.

### 1A. Section divider

- Use one large section number, one short section name, and one relevant image or illustration.
- Keep supporting lines to at most three short items; remove normal content-page chrome.
- Use the red accent on the selected section item or image focal point, not as a decorative band.

### 2. Executive takeaway

- Top: one-sentence conclusion.
- Body: 3 supporting facts or decisions in a horizontal or vertical sequence.
- Bottom/right: one callout for the decision or next step.

### 3. Trend or evidence page

- Left or top: chart or quantified evidence.
- Right or bottom: 2–3 implications.
- Highlight only the data that supports the title.

### 4. Problem and cause

- Use a causal chain, fishbone-like grouping, or 2×2 only when the axes are meaningful.
- Separate symptoms from root causes.
- Use red only for the critical bottleneck.

### 5. Layered architecture

- Use 3–5 horizontal layers with clear ownership.
- Put cross-cutting capabilities in a narrow vertical rail only when truly shared.
- Show interfaces and flows selectively.
- Use a concise title that states what the architecture enables.

### 6. Process or operating model

- Use 4–7 stages, left to right.
- Add owner, input/output, or control point only when essential.
- Distinguish current and target states through structure, not merely color.

### 7. Comparison

- Use a clean table or aligned before/after columns.
- Compare on one consistent set of dimensions.
- Use red to mark decisive differences, not every cell.

### 8. Roadmap

- Use phases with an outcome at the end of each phase.
- Keep activities subordinate to milestone and value.
- Show dependencies and decision gates when they affect feasibility.

### 9. Case study

- Context → action → measurable result.
- Use one real image, small architecture, or result chart.
- Do not claim impact without a source or clearly labeled estimate.
- Prefer a visible evidence spine such as timeline, before/after, baseline/result, or challenge/action/outcome; avoid a loose collage of screenshots.

### 10. Closing / decision

- Restate the conclusion, requested decision, and immediate next action.
- Avoid a generic “Thanks” slide when the meeting requires a decision.

## Density controls

- Prefer 2–4 peer groups per page.
- Keep paragraphs to 2–3 short lines; convert only true lists into bullets.
- Avoid more than 7 nodes in a single linear process.
- If the title needs a paragraph to be accurate, split the concept across slides.
- Preserve editability; do not flatten an entire slide into an image.
- For a 4–7 page leadership deck, give every content slide one decisive proof object: a quantified baseline, comparison, mechanism, architecture, evidence matrix, customer proof, or decision gate. If no evidence is available, label the object `示意`, `待客户确认`, or `建议口径` instead of making it look measured.

## Scenario adjustments

### Leadership briefing

- Put the conclusion and decision early.
- Use fewer pages, stronger titles, and explicit risk/choice framing.
- Keep technical detail in backup pages.

### Customer solution deck

- Start from customer outcome and scenario, not product catalog.
- Connect pain point → capability → architecture → value → proof.
- Make product names serve the solution logic.

### Technical workshop

- Allow denser architecture and flow pages.
- Keep consistent symbol semantics and provide overview before detail.
- Separate factual current state from proposed target design.

### Exhibition or keynote

- Use fewer words, larger type, stronger imagery, and dark mode only if the environment benefits.
- Keep one idea per screen and remove footnote-heavy evidence from the live view.

## Speaking-mode adjustments

| Mode | Recommended sequence | Emphasis |
| --- | --- | --- |
| Knowledge transfer | concept → mechanism → example → recap | comprehension and terminology |
| Persuasion | position → evidence → objection response → decision | credibility and choice |
| Progress report | outcome → evidence → issue → action → request | status, risk, ownership |
| Product or solution | scenario → pain → capability → proof → path | customer outcome before catalog |

## Worked outline example

Input: “Create a five-page AI manufacturing proposal for a manufacturing CIO.”

1. **Cover:** AI-enabled quality and production optimization proposal.
2. **Challenge:** “Quality variation and changeover loss are the two highest-value intervention points.” Support with customer-provided baseline evidence.
3. **Solution:** “A closed loop from sensing to model to execution turns isolated AI models into operational improvement.” Show a simplified layered architecture plus a three-second summary.
4. **Value and proof:** “Pilot success must be judged by agreed operational metrics, not model accuracy alone.” Show baseline, target, measurement method, and source; keep unknown values as placeholders.
5. **Decision:** “Start with one measurable pilot, then scale only after accuracy, cycle time, and operating ownership pass the gate.” State decision, owners, and next step.

Never invent metrics such as accuracy, ROI, savings, or implementation time to make the example look complete.
