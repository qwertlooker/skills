---
name: huawei-slides
description: Create, rewrite, or review Huawei-style presentation slides, standalone HTML decks, and PPTX files with conclusion-led business logic, restrained Huawei-red accents, disciplined typography, structured diagrams, and brand-safe logo handling. Use for requests mentioning 华为胶片、华为风PPT、华为式汇报、主打胶片、技术胶片、解决方案胶片、客户交流材料、领导汇报材料, or when adapting content to a Huawei-provided PPT/PPTX template. Do not use for generic presentations with no Huawei-style requirement or when another supplied brand system governs the deck.
---

# Huawei Slides

Create Huawei-style slides by combining rigorous message design with a restrained, technical visual system. Treat “Huawei style” as a communication method first and a red-and-white appearance second.

## Load the references

- Read [design-system.md](references/design-system.md) before planning or styling any deck.
- Read [narrative-and-layouts.md](references/narrative-and-layouts.md) when converting raw material into a storyline or choosing page structures.
- Read [pptx-output.md](references/pptx-output.md) for the default or explicitly requested PPTX route.
- Read [public-mainslide-patterns.md](references/public-mainslide-patterns.md) when the user asks for 主打胶片, wants comparison with Huawei public decks, or when calibrating a short leadership/customer deck to the public ICT Talent Ecosystem mainslide style.
- Read [html-output.md](references/html-output.md) only when the requested deliverable is HTML.
- Read [source-register.md](references/source-register.md) only when provenance, confidence, or official-vs-inferred status matters.
- Use [huawei-slide-tokens.json](assets/huawei-slide-tokens.json) as the default machine-readable style token set when no official template is supplied.
- Use [huawei-pptx-layouts.json](assets/huawei-pptx-layouts.json) to choose PPTX page silhouettes instead of repeating one card grid.

## Route the deliverable before authoring

- **Outline only:** return the storyline and page-level takeaways. Do not create a file.
- **Outline, then file:** publish the complete outline as an early intermediate result, then continue to the requested file without repeating the outline. When no format is named, create PPTX.
- **PPTX, default:** create a native editable PPTX and follow [pptx-output.md](references/pptx-output.md) plus the installed `Presentations` skill.
- **HTML, explicit only:** use [slide-template.html](assets/html/slide-template.html) only when the user explicitly requests HTML. Do not let the HTML template determine a PPTX's visual chrome or convert the HTML into PPTX.

For a small deck when the user already supplied topic, audience, page count, and output format, infer low-risk details and start. Do not browse merely to decorate a generic strategy deck. Research only when the user asks for current facts, when claims require evidence, or when authorized brand assets must be located; otherwise use neutral wording or explicit placeholders.

## Choose the visual route

1. If the user supplies an official or organization-approved template, use it as the only visual authority. Preserve its master, logo, fonts, footer, security marking, page number, spacing, palette, and inherited layout behavior.
2. If the user supplies a Huawei reference deck but no editable template, infer a compact style system from that deck and record deviations. Do not mix it with unrelated templates.
3. If no reference is supplied, build from scratch using this skill's references and tokens. Describe the result as “Huawei-style,” not “official Huawei template.”

Never copy a security classification, “Huawei Proprietary,” confidentiality footer, or internal document identifier from a reference unless the user's output is authorized to carry it.

## Build the message before the page

1. Identify audience, required decision or belief change, meeting type, speaking time, source material, likely objections, and the audience's technical depth. Infer low-risk details when obvious; ask only when the missing choice changes the storyline materially.
2. Write the objective as: “Enable [audience] to understand/believe/decide [specific outcome] within [meeting context or time].”
3. Write a one-sentence deck conclusion and 3–5 supporting messages.
4. Build a storyline using one dominant logic: problem–cause–solution–value, current state–gap–path–outcome, or trend–challenge–response–proof.
5. Make each slide title a claim or takeaway. Avoid topic-only titles such as “行业趋势” when a conclusion can be stated.
6. Give each slide one primary message and normally 2–4 supporting groups. Split slides when the message requires unrelated structures.
7. Translate technical facts into audience-relevant meaning without inventing impact: retain the source metric, add its operational consequence, and then state the decision implication when evidence supports it.
8. Remove producer-facing notes, planning language, duplicate claims, weak adjectives, and decorative content.

## Apply the visual system

- Prefer 16:9 and a white or near-white canvas for normal meetings. Use dark mode only for exhibition, stage, or large-screen contexts, or when the supplied template requires it.
- For a net-new business mainslide deck, default to a light cover and full Huawei-red takeaway titles on content pages. Use a dark cover or neutral-technical title system only when the audience, venue, or supplied reference justifies it; record the choice before authoring.
- Use Huawei red to identify the page's main emphasis: a title system, critical-number family, selected node, focal series, or key object. A full red title may coexist with one related content-emphasis group; scattered unrelated red cues are still noise.
- Do not add a persistent red strip at the top or a red rule below every title. By default, use neither. If a supplied template requires one, preserve it; otherwise choose at most one primary red device on a page.
- Keep one page to at most four semantic colors, excluding neutral shades and necessary logo colors.
- Prefer flat composition, straight edges, light separators, consistent alignment, and generous but purposeful whitespace. Avoid glossy gradients, strong shadows, glass effects, excessive rounded cards, and decorative UI chrome.
- Use diagrams to explain systems, flows, layers, or relationships. Prefer standardized abstract symbols and line icons over a collage of product photographs.
- Use a single strong image on covers or section dividers when it helps. Prefer user-supplied, official, or authorized real imagery for customer evidence. Use generated imagery only as a conceptual cover/divider visual, never as proof of a real customer, facility, product deployment, or result. Do not reuse the same non-background image across the deck.
- Keep charts honest and direct: label the conclusion, highlight one series or point, mute the rest, show units and sources, and avoid 3D effects.

## Use typography deliberately

- Default to Microsoft YaHei for Chinese and Arial for English text and numbers.
- Use 方正兰亭黑 or Huawei Sans only when an approved template explicitly requires them and the licensed fonts are available; never substitute them as the default.
- For Huawei-style template work, use 30–32 pt slide titles and 18–22 pt body text unless the supplied template defines different sizes. Use 38–44 pt for a simple cover title and 9–11 pt only for sources or legal notes.
- Use no more than three visible text levels on a content slide. Use weight and spacing before adding more colors.
- Never reduce body text below 16 pt to rescue an overloaded slide. Shorten, restructure, or split the page.

## Handle brand assets safely

- Use only official artwork supplied by the user or obtained from an authorized official source. Never redraw, recolor, stretch, crop, rotate, add effects to, or rebuild a Huawei logo.
- Preserve clear space and legibility. Prefer the approved red logo on a simple white background; use approved black or reversed-white variants only when the background requires them.
- For co-branding, balance the visual sizes of logos and keep ample separation. Follow the specific partner agreement or supplied co-branding guide when available.
- If no authorized logo asset is available, omit the logo and create a Huawei-style visual system without fabricating one.

## Implement presentation files

When creating or editing PPTX, follow [pptx-output.md](references/pptx-output.md) and the installed `Presentations` skill. A supplied template overrides the practical defaults. Author natively with the presentation tooling; do not convert from HTML or imitate the HTML viewer. Keep all output editable: use native text, tables, charts, and simple shapes; use raster imagery only for photos or illustrative art.

Set Chinese text to Microsoft YaHei and Latin letters/numbers to Arial in the PPTX run properties. Do not assign Microsoft YaHei to the Latin font slot. If the presentation exporter cannot set the two Open XML font slots independently, run `node scripts/fix-pptx-font-mapping.mjs <input.pptx> <output.pptx>` and validate the corrected output. Run `node scripts/validate-pptx-style.mjs <output.pptx> --title-system=ict-business-red-title` before delivery. Use `--title-system=neutral-technical` only when that alternate system was selected before authoring; use `--allow-top-rule` only when an approved inherited template explicitly contains that rule.

For technical diagrams:

- Create connectors before nodes so edges remain behind shapes.
- Use one reading direction per diagram.
- Group by layers, domains, or stages; label interfaces and data flows only when they matter to the slide's conclusion.
- Add a one-sentence “three-second summary” beside a complex architecture so a non-specialist can grasp its purpose before reading components.
- Replace component sprawl with a simplified main view and, if needed, a separate detail page.

## Implement HTML files

- Start from the bundled standalone template; replace its sample slide bodies while preserving the base tokens, keyboard navigation, responsive fit, print behavior, and automatic page numbering.
- Keep the final HTML self-contained unless the user explicitly requests a multi-file site.
- Use the mixed-script stack `Arial, "Microsoft YaHei", "微软雅黑", sans-serif`. Arial must come first so Latin letters and numbers do not silently render in Microsoft YaHei; Chinese glyphs fall back to Microsoft YaHei.
- Keep normal body copy at 24–29 px (18–22 pt equivalent). Keep labels at 21–24 px. Use 13–15 px only for sources, legal notes, page markers, or viewer controls. Shorten or split content instead of shrinking table, diagram, or roadmap text below 21 px.
- Use classes and CSS variables for brand colors. Do not add inline hard-coded red styles to individual phrases.
- Remove all producer-facing labels before delivery, including “Huawei-style presentation,” “华为风格模板,” layout names, TODOs, and instructional placeholders. Audience-facing metadata should be the organization, project, presenter, or date—or be omitted.
- Run `node scripts/validate-html-deck.mjs <output.html>` before delivery. Resolve every error. Then render the deck in one batch when a local browser runtime is available and inspect every slide for clipping, wrapping, density, and control overlap.

## Review before delivery

Run three passes:

1. **Logic:** Does the title state the takeaway? Do the supporting elements prove it? Is the storyline complete and non-repetitive?
2. **Visual:** Are alignment, margins, spacing, font hierarchy, red accents, and diagram semantics consistent? Is every page readable at normal presentation distance?
3. **Integrity:** Are facts, units, dates, sources, logo use, confidentiality labels, and chart values correct? Are all elements editable and free of clipping or unintended overlap?

Render every final PPTX slide and inspect it at full size. If the QA environment lacks a Chinese font, verify the slide XML and font mapping with the validator and do not mistake missing rendered glyphs for empty content; report the visual-QA limitation. For HTML, use the validation and batched rendering workflow above. Fix wrapping, overflow, low contrast, visual noise, and inconsistent footers before delivery.

When reviewing or rewriting an existing deck, inspect the complete deck first, then classify findings as content logic, evidence integrity, visual system, brand compliance, or production quality. Preserve correct facts, approved template elements, and user-owned content; recommend the smallest effective corrections before performing a rewrite unless the user has already requested edits.

## Output behavior

- When the user asks for a plan or outline, return the storyline and page-level takeaways before creating a file.
- When the user asks for a deck, 胶片, presentation, or PPT without naming a format, deliver the editable PPTX and summarize the storyline and any brand assumptions.
- When the user explicitly asks for HTML, use the bundled HTML route. For Marp or Slidev, carry over the same narrative, tokens, typography floor, and brand-safety rules; do not substitute a web format for an editable PPTX without permission.
- When the user asks for a review, classify issues as content logic, visual system, brand compliance, or production quality; propose the smallest effective correction.
- Clearly distinguish official rules from observed public-deck patterns and from this skill's practical defaults.
