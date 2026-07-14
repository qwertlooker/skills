# HTML output route

Use this route only when the user explicitly requests HTML.

## Fast path

1. Copy `assets/html/slide-template.html` to the requested output path.
2. Keep the base CSS and viewer script intact. Replace the sample content and remove unused sample slides or layouts.
3. Set the deck title, audience-facing cover metadata, footer label, and source notes. Omit fields that are not known; never expose style names, prompts, TODOs, or production notes.
4. Use one of the existing layout families before adding new CSS: cover, claim-plus-modules, comparison table, layered architecture, or phased roadmap.
5. Run `node scripts/validate-html-deck.mjs <output.html>` and fix every error.
6. When a local browser runtime is available, capture all slides in one run and inspect them at full size. Do not spend time installing a browser solely for routine HTML QA; use the validator and state the limitation if rendering is unavailable.

## Content and evidence

- A generic strategy deck may use clearly framed recommendations without external research.
- Do not invent customer baselines, ROI, accuracy, market share, dates, or implementation results. Use `[待确认]` during drafting, then remove the placeholder or retain it only when the user wants an explicit data-gap marker.
- Add a source note when a page contains externally verifiable facts, benchmarks, or user-provided data. A page of original recommendations does not need a fake source.

## Typography and density

- Preserve the template's mixed-script font stack with Arial first and Microsoft YaHei as the Chinese fallback.
- Keep slide titles to one or two short lines.
- Keep normal body text at 24–29 px and labels at 21–24 px. Only sources, legal notes, page markers, and controls may use 13–15 px.
- If a table, architecture, or roadmap no longer fits, remove detail, change the structure, or split the slide. Do not shrink core text.

## Production rules

- Deliver one self-contained HTML file by default.
- Keep `#C7000B` in the `--huawei-red` token and reference the variable through classes. Do not scatter hard-coded red values or inline styles.
- Do not add a persistent top red strip or title underline. Use either a red title or a dark title with one red focal phrase/object; do not stack both systems with decorative rules.
- Page numbers must be generated from the actual slide count.
- Keep arrow-key, Page Up/Down, Home/End, responsive fitting, and print-to-PDF behavior.
- Omit the Huawei logo when no authorized asset is supplied. Do not create a text imitation or visible logo placeholder.
- The final visible deck must not contain “Huawei-style presentation,” “华为风格模板,” “仅供参考,” layout names, or implementation instructions unless the user explicitly wants that wording for the audience.

## Delivery contract

When the user says “先输出大纲，再生成HTML,” show the full page outline first as an intermediate result and continue implementation. The final response should link the HTML and briefly state the storyline, evidence assumptions, and any unresolved placeholders. Do not repeat the full outline.
