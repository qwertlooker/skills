# Jiaopian-style slide design system

## Authority model

Use this priority order:

1. User-supplied approved PPTX template or master
2. User-supplied Jiaopian reference deck for the same business unit and scenario
3. Official public Jiaopian VI or co-jiaopian guidance
4. Official public Jiaopian presentation examples
5. Practical defaults in this document

Do not present levels 4–5 as universal Jiaopian corporate rules.

## Core visual character

Jiaopian-style slides are structured, restrained, technical, and outcome-oriented. Their recognizable quality comes from a clear information hierarchy, flat diagrams, compact evidence, disciplined alignment, and selective red emphasis—not from filling the page with red.

### Canvas and composition

- Default aspect ratio: 16:9.
- Default background: white `#FFFFFF`; soft neutral section areas may use `#F5F5F5` or `#F7F7F7`.
- Normal meetings: prefer light mode. Exhibition, stage, or large-screen use may justify dark mode.
- Use a stable content frame with approximately 5–7% side margins and 4–6% top/bottom margins when no template defines them.
- Prefer one composition over a dashboard of small cards. Use 2–4 modules only when they are true peer groups.
- Use straight, aligned geometry. Keep decorative shapes subordinate to the message.

### Color

Official public VI guidance identifies Jiaopian red as Pantone 185C, `RGB 199/0/11`, `#C7000B`. It explicitly recommends limited use to create a “point of red.” Use this as the default accent.

An older public training slide specifies `RGB 153/0/0`, `#990000`. Treat this as a legacy/template-specific dark red. Use it only when matching an inherited template; do not combine both reds arbitrarily.

Recommended neutral text and line colors from the public VI:

| Role | RGB | Hex |
| --- | ---: | --- |
| Primary text / black | 35, 24, 21 | `#231815` |
| Secondary text / deep gray | 89, 87, 87 | `#595757` |
| Muted gray | 159, 160, 160 | `#9FA0A0` |
| Light divider / fill | 221, 221, 221 | `#DCDDDD` |
| Canvas | 255, 255, 255 | `#FFFFFF` |

Official auxiliary colors include warm and gray families plus a moderated cyan. Use them for data categories or functional distinctions, not decoration. Keep one page to four semantic colors at most.

Practical page ratio:

- 75–90% white or neutral canvas
- 8–20% grayscale structure and text
- 2–8% Jiaopian red emphasis

This ratio is a practical default, not an official measured rule.

### Typography

Official public VI distinguishes company-specific fonts from general fonts:

- Company-specific Chinese: 方正兰亭细黑简体、方正兰亭黑简体、方正兰亭粗黑简体
- Company-specific Latin: Jiaopian Sans Light, Regular, Bold
- General Chinese: Microsoft YaHei family
- General Latin: Arial Regular and Bold

This skill defaults to Microsoft YaHei for Chinese and Arial for English text and numbers to maximize portability and editing consistency. Use 方正兰亭黑 or Jiaopian Sans only when an approved template explicitly requires them and the licensed fonts are available.

For mixed-script HTML, declare `Arial, "Microsoft YaHei", "微软雅黑", sans-serif` in that order. Font fallback is resolved glyph by glyph: Arial renders Latin letters and numbers, while Chinese glyphs fall through to Microsoft YaHei. Putting Microsoft YaHei first does not satisfy the Latin/number rule because that font also contains Latin glyphs.

Portable presentation defaults:

| Role | Recommended size | Weight |
| --- | ---: | --- |
| Cover title | 38–44 pt | Bold |
| Slide takeaway title | 30–32 pt | Regular or Bold |
| Section / key statement | 24–28 pt | Bold |
| Body | 18–22 pt | Regular |
| Chart or diagram label | 14–18 pt | Regular |
| Source / legal note | 9–11 pt | Regular |

For a 1600×900 HTML stage, use approximately 56 px cover title, 42–43 px slide title, 32–37 px key statement, 24–29 px body, 21–24 px labels, and 13–15 px sources/controls. Do not use source-sized text for table cells, diagram nodes, roadmap steps, or normal body copy.

Use no more than three visible levels on a content page. Titles should normally remain on one or two short lines. Prefer short Chinese phrases and avoid excessive punctuation.

### “Point of red” hierarchy

Use red as a semantic hierarchy, not as a raw element count. Public ICT Talent Ecosystem mainslides commonly combine a full red title with a related family of red figures, labels, or selected objects. Treat that related family as one supporting content-emphasis group.

For a net-new business mainslide deck, use red for the full takeaway title and, when needed, one supporting content group:

- the whole takeaway title in an ICT-business-mainslide title system;
- one related row of decisive numbers or deltas;
- the selected steps or nodes that share one meaning;
- one highlighted chart series or matrix region.

The public ICT Talent Ecosystem mainslides frequently use full red takeaway titles without a persistent top strip or title underline. Use this as the default PPTX title system when no stronger template is supplied. A neutral technical deck may instead use dark titles with one red phrase or focal object, but select that system explicitly before authoring and use it consistently. Do not drift into mixed red/dark titles merely because individual phrases are easy to color.

Red lines are not a default jiaopian signature. Use a red line only when the line itself carries meaning, such as a selected path, threshold, trend, or active stage. Use gray for routine borders and separators. Do not use red simultaneously for title, top rule, title underline, every icon, all arrows, every number, and the footer.

### Charts

- State the analytical conclusion in the slide title.
- Use red for the focal series or data point; use grays for context.
- Direct-label important series where possible.
- Show units, period, base, and source.
- Avoid 3D, gradients, decorative gauges, dual axes without strong necessity, and unexplained normalization.
- For categorical comparison, use horizontal bars or a clean table before radar charts.

### Diagrams and architecture

- Use abstract, standardized symbols; prefer line icons or simple geometric nodes.
- Use one primary reading direction: left-to-right for process, top-to-bottom for hierarchy, center-out only for true hub-and-spoke systems.
- Use consistent shape semantics: same role means same shape and color.
- Place connectors behind nodes. Use right-angle connectors for layered architecture and straight connectors for simple flows.
- Limit line crossings. Split overview and detail when the diagram cannot remain legible.
- Use photos only when a real product, site, or customer context is evidence. Do not mix unrelated photo styles in a technical architecture.

### Imagery

- Cover and divider: default to a light or high-key composition with one panoramic or high-quality contextual image and intentional negative space. Use dark imagery only for stage, exhibition, or an explicitly requested dark route.
- Content page: one evidence-bearing image or no image; diagrams usually carry more value.
- Prefer user-supplied, official, or authorized customer/site/product imagery. Generated imagery may support a conceptual cover or divider, but it must never imply a real deployment, customer, product, or measured outcome.
- Avoid generic handshake imagery, random server-room collages, low-resolution screenshots, and decorative stock icons.
- Do not place a logo on a visually complex image unless the approved logo version remains clearly legible.

### Logo and co-jiaopian

- Use the official digital artwork; never recreate or redesign the logo.
- Preserve aspect ratio, color, and clear space.
- White is the preferred background in official co-jiaopian guidance.
- Approved red, black, or reversed-white variants depend on background contrast; do not improvise variants.
- In co-jiaopian, align visual height, preserve separation, and follow the partner agreement. The public co-jiaopian guide allows the separator line to be optional in some PPT scenarios, but agreement-specific rules take precedence.

### Avoid

- full-page red backgrounds for routine content slides;
- dense grids of rounded cards or pill labels;
- heavy drop shadows, bevels, glass, neon, or glossy gradients;
- excessive icons that repeat the text;
- large paragraphs and topic-only titles;
- decorative arrows without semantic meaning;
- copied confidentiality labels or footer wording from a reference deck.
- persistent top red strips or title underlines on every page;
- giant red circles, ellipses, waves, or blobs used only as cover decoration;
- red page numbers and repeated red module borders when they carry no priority or state.
- mixed red/dark takeaway titles in a deck declared as `ict-business-red-title`;
- treating a generated factory, campus, customer, or product scene as evidence;
- large arrows or card grids that explain less than an aligned process, matrix, architecture, or evidence object.
