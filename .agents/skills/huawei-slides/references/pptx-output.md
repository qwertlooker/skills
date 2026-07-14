# PPTX output route

Use this route by default whenever the user asks for 胶片, PPT, presentation, or a deck without naming another format.

## Visual baseline

The practical default is informed by the public Huawei ICT Talent Ecosystem mainslides: light canvas, full red takeaway titles, gray structural lines, substantial diagrams or evidence, compact footers, and red attached to meaningful content groups. Do not copy its logo, security footer, internal identifiers, QR codes, customer-specific material, or measured outcomes.

## Choose one title system

Use one system consistently across a deck unless an inherited template specifies another:

1. **ICT business mainslide, default:** set the complete slide title in Huawei red; use no top strip and no title underline. Keep the remaining page mostly dark gray and neutral. The full red title does not consume the page's one supporting red content group.
2. **Neutral technical:** set the title in dark text and use red for one short phrase, decisive number, focal series, or selected architecture node; use no top strip and no title underline.

Do not combine a red title, a top red strip, a title red rule, unrelated red module borders, and a red page number on the same page. A slide normally uses one title system plus at most one semantically related red content group. Multiple red metrics are acceptable when they form one KPI row or comparison family. Every red group must answer “what should the audience notice first?”

Write the chosen title system into the deck's design notes before page construction. Do not choose neutral technical merely to preserve a mixed-color title already drafted.

## Decoration rules

- Default `topRedRule` and `titleUnderline` to false.
- Use light gray lines for tables, grids, separators, and footer rules.
- Do not add a short red locator line above every title merely to signal the brand.
- Do not put red top borders on every card or phase. Highlight only the active, recommended, abnormal, or selected item.
- Keep page numbers and routine footer text gray unless an inherited template says otherwise.
- Avoid giant red circles, ellipses, waves, or blobs on covers. Prefer one relevant image, an evidence-bearing illustration, or a restrained gray technical composition with one red focal cue.

## Layout patterns

Choose the layout that proves the slide title:

- **Image + claim + key figures:** company, market, customer, or outcome overview.
- **Trend or evolution diagram:** technology change, maturity, or phased development.
- **Loop or operating model:** two-way drive, feedback, ecosystem, or governance mechanism.
- **Layered architecture:** business applications, reusable capabilities, data/platform, and existing systems.
- **Evidence table or curriculum map:** comparisons, scope, capability coverage, or implementation detail.
- **Phased roadmap:** stage outputs and decision gates; use red only on the current or recommended stage.
- **Section divider with large numeral:** one image/illustration, one oversized gray section number, and one short section name.
- **Customer case evidence:** challenge/action/outcome, timeline, or baseline/result with real images and dated sources.

Avoid repeating a three-card layout across most pages. Vary silhouettes while retaining the same margins, title position, typography, and footer behavior.

## Native PPTX production

- Build the PPTX directly with the installed `Presentations` skill and its required artifact tooling. Do not convert the standalone HTML template or screenshot HTML pages into slides.
- Use editable text, tables, charts, connectors, and simple shapes.
- Use Microsoft YaHei in the East Asian font slot and Arial in the Latin font slot for every text run. This applies even when a run currently contains only Chinese because later edits may introduce numbers or English.
- When the exporter applies one typeface to both font slots, run `node scripts/fix-pptx-font-mapping.mjs <input.pptx> <output.pptx>` after export. Keep the original export as an intermediate and deliver the corrected output.
- Keep the deck title at 38–44 pt, slide titles at 30–32 pt, body at 18–22 pt, and diagram labels at 14–18 pt. Do not reduce normal body text below 16 pt.
- Use `#C7000B` as the default Huawei red; use `#990000` only to match an inherited legacy template.

## QA

1. Render every slide and inspect the complete deck at full size.
2. Run the presentation overflow test from the installed `Presentations` skill.
3. Run `node scripts/validate-pptx-style.mjs <deck.pptx> --title-system=ict-business-red-title`. Use `--title-system=neutral-technical` only when that route was explicitly selected before authoring.
4. Fix incorrect Latin/East Asian font mapping, mixed title systems, producer-facing text, repeated top/title red rules, and decoration-only red shapes.
5. If the render environment has no Chinese font, record that limitation and rely on XML text/font validation for content presence; do not approve spacing and wrapping from a blank-glyph render.

Use `--allow-top-rule` only for an approved inherited template. The flag does not permit gratuitous title underlines or multiple decorative red lines.
