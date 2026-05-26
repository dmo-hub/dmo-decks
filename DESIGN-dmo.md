---
version: alpha
name: DMO-Tracker-PlayStation
description: A PlayStation-inspired theme for DMO Tracker. Channel-tile layout on a deep blue-black canvas, PS Blue (#0070D1) as the primary, cyan hover-scale on interactive tiles, geometric sans display at tight tracking. Mood = console retail / PS5 home dashboard — "quiet authority," big tiles, minimal chrome, the imagery (Digimon banners) does the talking. This replaces the previous Anthropic-warm-cream system entirely; surfaces flip from cream → dark, type flips from serif → tight sans.

colors:
  # Brand
  primary: "#0070D1"
  primary-active: "#005ba8"
  primary-soft: "#1a3a6e"
  accent-cyan: "#5eb1ef"
  accent-cyan-glow: "rgba(94, 177, 239, 0.18)"

  # Surfaces — channel/tile layered blacks
  canvas: "#0a0a0f"
  surface-soft: "#11151c"
  surface-card: "#1a1f2e"
  surface-strong: "#232838"
  surface-dark: "#050608"
  surface-dark-elevated: "#11151c"

  # Text on dark canvas
  ink: "#f0f3f7"
  body-strong: "#d0d6df"
  body: "#b0b8c4"
  muted: "#6e7682"
  muted-soft: "#4a5160"

  on-primary: "#ffffff"
  on-dark: "#f0f3f7"
  on-dark-soft: "#8a92a0"

  # Hairlines
  hairline: "#2a2f3d"
  hairline-soft: "#1f2330"

  # Semantic
  teal: "#00d9c0"
  amber: "#f5a623"
  success: "#00d9c0"
  warning: "#f5a623"
  error: "#ef4d4d"

  # Deck-page note callout (dark amber wash)
  note-bg: "#2a1a0a"

typography:
  # PlayStation uses SST Pro (proprietary). Open substitute: Inter at tight tracking, weight 500–700.
  # No serif anywhere — channel UI is sans-only.
  display:
    fontFamily: "Inter, 'SST Pro', -apple-system, 'Segoe UI', sans-serif"
    fontWeight: 600
    letterSpacing: -0.5px
  display-tight:
    fontFamily: "Inter, 'SST Pro', sans-serif"
    fontWeight: 700
    letterSpacing: -0.8px
  body:
    fontFamily: "Inter, 'SST Pro', sans-serif"
    fontWeight: 400
    letterSpacing: 0
  caption-uppercase:
    fontFamily: "Inter, sans-serif"
    fontWeight: 600
    letterSpacing: 1.5px
    textTransform: uppercase
  code:
    fontFamily: "JetBrains Mono, 'Geist Mono', ui-monospace, monospace"
    fontWeight: 400

rounded:
  xs: 4px
  sm: 6px
  md: 8px
  lg: 10px
  xl: 14px       # PS tiles use slightly less curve than Anthropic — sharper edges
  pill: 9999px

spacing:
  xxs: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 48px
  section: 80px  # PS pages stack tighter than Anthropic editorial
---

## Overview

PlayStation's web/console interface is built around **channel tiles on deep dark**. The PS5 home dashboard is a horizontal row of large rounded-rectangle tiles (game art), each with a subtle hover-scale + cyan glow. The retail site (playstation.com) carries the same pattern: dark canvas, big imagery, minimal text, PS-Blue CTAs.

For DMO Tracker this means:

1. **Canvas flips to near-black** (`#0a0a0f`). The cream editorial floor is replaced by a near-black with a slight blue tilt — reads cool, console-y.
2. **Cards become channel tiles** — `#1a1f2e`, sharper corners (10–14px radius, not 12–16), and they *scale on hover* (1.015×) with a cyan glow.
3. **Primary action goes PS Blue** (`#0070D1`). Used scarcely on individual CTAs; the surface contrast itself does most of the chrome work.
4. **Hover state is cyan** (`#5eb1ef`) — this is the PS signature: cyan ring + scale + brightness pop. Replaces all the warm-coral hover states.
5. **Typography goes sans-only** at tight tracking. Display Copernicus/Source Serif 4 is gone — PS uses SST Pro (geometric sans), Inter is the closest open substitute at weight 600–700 with -0.5 to -0.8px tracking.
6. **Imagery carries the page.** Digimon banner images on dark canvas read as glowing tiles (the way game art reads on PS5 home). Cream-canvas thumbnails would be wrong here.

The mood is **console retail / quiet authority** — fewer words, bigger tiles, more breathing room around imagery.

## Colors

### Brand & Hover
- **PS Blue / Primary** (`#0070D1`): The signature PlayStation primary. Used on every primary CTA, brand wordmark dot, timeline node, active filter pill fill. Saturated, slightly desaturated from pure blue.
- **PS Blue Active** (`#005ba8`): Press / hover-darker variant for buttons.
- **PS Blue Soft** (`#1a3a6e`): Disabled / very-soft tint on dark surfaces (replaces Anthropic's cream-disabled which would be invisible here).
- **Accent Cyan** (`#5eb1ef`): The PS hover-scale glow color. Used on card hover border, focus rings, active-link underline. *This is the brand's most distinctive interactive signal.*
- **Cyan Glow** (`rgba(94,177,239,0.18)`): Soft cyan wash used as box-shadow on hovered cards. ~18% alpha so the underlying surface still reads.

### Surfaces (channel-tile ladder)
- **Canvas** (`#0a0a0f`): Default page floor. Near-black, slight blue tilt.
- **Surface Soft** (`#11151c`): Section bands and filter-bar background.
- **Surface Card** (`#1a1f2e`): Card / channel-tile background. One step up from canvas.
- **Surface Strong** (`#232838`): Elevated tile / hovered card surface.
- **Surface Dark** (`#050608`): Footer and the deepest sectional bands.
- **Surface Dark Elevated** (`#11151c`): Nested-card backgrounds inside dark sections.
- **Hairline** (`#2a2f3d`): 1px border tone between tiles.
- **Hairline Soft** (`#1f2330`): Barely-visible interior divider.

### Text (inverted from cream version)
- **Ink** (`#f0f3f7`): All headlines and primary text. Off-white with a slight cool tint — never pure #fff.
- **Body Strong** (`#d0d6df`): Lead paragraphs, emphasized text.
- **Body** (`#b0b8c4`): Default running text.
- **Muted** (`#6e7682`): Sub-headings, captions, metadata.
- **Muted Soft** (`#4a5160`): Fine-print, copyright.

### Semantic
- **Teal** (`#00d9c0`): TH-source badge, success indicators (electric — a darker mint is too quiet on this dark canvas).
- **Amber** (`#f5a623`): KR-source badge, warning callouts.
- **Error** (`#ef4d4d`): Validation errors.

## Typography

### Family
- **Display & body**: Inter (substitute for SST Pro). The fallback stack walks `'SST Pro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`.
- **Code / dates / idx tags**: JetBrains Mono (kept from previous theme — JetBrains Mono reads as "data" regardless of theme).

### Hierarchy
- **Display tight (hero h1)**: Inter 700, -0.8px tracking, 36–48px. Bold but tight.
- **Display (section h2/h3)**: Inter 600, -0.5px tracking.
- **Body**: Inter 400, normal tracking, 15px.
- **Caption-uppercase**: Inter 600, 1.5px tracking, 10–11px. Used on month dividers, section headers ("RECENT ACTIVITY"), badges.

### Principles
- No serif anywhere. Editorial warmth is replaced by tight modern sans. If a label needs emphasis, it goes uppercase + tracked, not italic + serif.
- Display weights run heavier (600–700) than the Anthropic version (400) because dark canvas absorbs visual weight — thin display fonts read as ghostly on near-black.
- Numbers stay tabular-nums (`font-variant-numeric: tabular-nums`) on hero stats and dates — this preserves the "data dashboard" feel of the previous theme.

## Layout

### Spacing
Same token names as parent (`xs` through `section`), but **section padding tightens from 96px → 80px**. PS pages stack denser; cream-editorial 96px feels sparse on dark.

### Grid
- Max content width 1200px (unchanged).
- Feature grid → 3-up tiles at desktop, 2-up tablet, 1-up mobile.
- Timeline → single column with a 1px rail, same as parent.

### Whitespace
On dark canvas, internal card padding feels right at 24–28px (parent: 28–32px). Tighter padding + bigger imagery is the PS rhythm.

## Elevation & Hover

| State | Treatment |
|---|---|
| Resting tile | `#1a1f2e` surface, 1px `#2a2f3d` hairline, no shadow |
| Hovered tile | `transform: scale(1.015)`, border → `#5eb1ef` (cyan), `box-shadow: 0 0 0 1px rgba(94,177,239,0.4), 0 12px 24px rgba(0,112,209,0.18)` |
| Pressed tile | scale 0.995, border stays cyan |
| Active filter pill | `#0070D1` fill, white text |
| Focused input | `#5eb1ef` border, 3px cyan-at-20% outer ring |

The **scale + cyan-glow on hover** is non-negotiable — it's the single most identifiable PlayStation interaction. Skip it and the theme reads as "generic dark dashboard."

## Shapes

| Token | Value | Use |
|---|---|---|
| `rounded.xs` | 4px | Pills, badge accents |
| `rounded.sm` | 6px | Small buttons |
| `rounded.md` | 8px | Standard CTAs, inputs |
| `rounded.lg` | 10px | Cards, tiles |
| `rounded.xl` | 14px | Hero band, large feature tiles |
| `rounded.pill` | 9999px | Filter pills, source badges |

PS tiles use **slightly sharper corners** (10–14px) than Anthropic cards (12–16px). The harder edge reads as "console UI" rather than "consumer SaaS."

## Components

Component definitions inherit structurally from DESIGN.md. The mapping:

- **`top-nav`** → dark canvas bg, ink text, cyan hover on links. Brand dot becomes the PlayStation-style 4-symbol mark (or kept as Anthropic radial-spike but in cyan).
- **`button-primary`** → PS Blue fill, white text, scale-on-hover (1.02×).
- **`feature-card` / `card` / `tile`** → `surface-card` bg, hairline border, hover = cyan ring + scale + soft glow.
- **`hero-band`** → `surface-card` bg (slight lift from canvas), no border, rounded `xl`.
- **`badge-primary`** (replaces `badge-coral`) → PS Blue fill, white uppercase text.
- **`src-label-kr`** → amber fill (warm signal on cold canvas).
- **`src-label-th`** → teal fill.
- **`gk-table`** → table headers go `surface-strong` bg with ink text (NOT inverted black-on-white anymore — would clash with the dark canvas).
- **`note-card`** (deck-page rule callout) → `note-bg` (#2a1a0a, dark amber wash), amber text.
- **`footer`** → `surface-dark` (#050608), muted text, cyan link hover.

## Do's and Don'ts

### Do
- Keep imagery (Digimon banners) prominent. The dark canvas is designed to make game art glow — don't reduce image sizes to make room for text.
- Use cyan hover EVERYWHERE interactive. Card, link, filter pill, input. The cyan signal is the PS interaction language.
- Scale-on-hover on cards (1.015×). It's subtle but unmistakable.
- Stack tighter than the cream version. 80px section gap, 24px card padding.
- Tabular-nums on every number (date, idx, stat count).

### Don't
- Don't use serif anywhere. The literary editorial voice is gone — this is console retail.
- Don't put PS Blue on body backgrounds. Blue is for actions and tiny accent moments; the surface ladder stays the blue-black ladder.
- Don't introduce warm tones (orange/amber) as canvas — only as semantic badges (KR/warning) on the dark floor.
- Don't bold the display font weight to 800/900. PS sits at 600–700; heavier reads as "esports brand" not "console retail."
- Don't add box-shadow on resting state. Depth comes from the surface ladder (canvas → surface-soft → surface-card → surface-strong); shadow only appears on hover.

## Migration from Anthropic-cream

Surface flip is the work — palette tokens in `:root` get rewritten, but most components don't need per-rule changes because they reference variables (`var(--canvas)`, `var(--ink)`, etc.). The two exceptions:

1. **Display headline font swap** — `.hero h1`, `.card-title`, `.deck-name`, `.feature h3`, `.hero-stat .num`, `.feature .stat b` all explicitly set `font-family: "Source Serif 4", "Georgia", serif`. These must be flipped to the Inter sans stack.
2. **`.gk-table th`** uses `background: var(--ink)` (a dark-on-cream contrast trick). On dark canvas this becomes dark-on-dark — needs to switch to `var(--surface-strong)`.

Everything else (filter pills, timeline rail, source badges, hover states) re-themes automatically because they reference the brand variables that we're swapping.
