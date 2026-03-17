# Dashboard Design Specification
**Project:** McDonald's Store Compliance Dashboard (Tarsyer AI)
**Stack:** Flask + Jinja2 templates, Chart.js, Font Awesome 6.5, Google Inter font

---

## Brand & Colour Palette

| Token | Hex | Usage |
|---|---|---|
| `--mcd-red` | `#DA291C` | Primary brand colour — buttons, header logo block, active states, spinners, focus rings |
| `--mcd-gold` | `#FFC72C` | Active nav tab underline & text, quick-btn active state |
| `--mcd-dark` | `#27251F` | Nav bar background |
| `--bg` | `#f4f5f8` | Page background (light grey) |
| `--card` | `#ffffff` | Card / surface background |
| `--text` | `#1e2235` | Primary text |
| `--text-2` | `#374151` | Secondary text (table cells, labels) |
| `--muted` | `#8492a6` | Muted / helper text, card titles |
| `--border` | `#e8eaf0` | Borders, dividers |
| `--green` | `#16a37a` | Positive trend, best rank |
| `--red` | `#d94040` | Negative trend, worst rank, danger |
| `--yellow` | `#d97706` | Warning states |
| `--blue` | `#3b7dd8` | Informational badges |

**Typography:** `Inter` (Google Fonts), weights 300/400/500/600/700. Fallback: `Segoe UI`, `sans-serif`. Font smoothing: `-webkit-font-smoothing: antialiased`. Base size: 14px.

---

## Login Page (`login.html`)

**Layout:** Full-viewport centred card, no sidebar or nav.

**Background:** Red diagonal gradient — `linear-gradient(135deg, #7f1d1d 0%, #dc2626 60%, #ef4444 100%)`.

**Login box:**
- Width: 400px, `border-radius: 16px`, `overflow: hidden`
- Heavy shadow: `0 20px 60px rgba(0,0,0,.35)`
- Two-section card (header + form), no outer padding

**Header section (`.login-header`):**
- Background: `linear-gradient(135deg, #991b1b 0%, #dc2626 100%)`
- Padding: `36px 40px 28px`, flex column, centred, `gap: 14px`
- **Logo row:** Tarsyer owl logo + vertical separator + McDonald's logo, side by side
  - Both logos: `height: 64px`, white background, `border-radius: 10px`, padding `8px 10px` (Tarsyer) / `6px 10px` (McDonald's)
  - Separator: `width: 1px; height: 50px; background: rgba(255,255,255,.35)`
- **Title:** `"Store Monitor"` — 22px, weight 700, white, `text-shadow: 0 1px 3px rgba(0,0,0,.2)`
- **Subtitle:** `"McDonald's compliance dashboard — Tarsyer AI"` — 13px, `rgba(255,255,255,.65)`

**Form section (`.login-form`):**
- Background: `#ffffff`, padding `32px 36px 28px`
- Inputs: full width, `padding: 10px 14px`, `border: 1px solid #e5e7eb`, `border-radius: 8px`, 14px
  - Focus: `border-color: #dc2626`
- Submit button: full width, `padding: 11px`, `background: #dc2626`, white text, 15px, weight 600, `border-radius: 8px`
  - Hover: `#b91c1c`
- Error message: red `#ef4444`, 13px, flex row with Font Awesome `fa-circle-exclamation` icon

**Static assets used:**
- `/static/img/tarsyer.png` — Tarsyer owl logo
- `/static/img/mcd.png` — McDonald's golden arches logo

---

## Dashboard Shell (`base.html`)

### Top Header (`.topheader`)
- Height: 56px, white background, `border-bottom: 1px solid var(--border)`
- `position: sticky; top: 0; z-index: 100`
- Three zones: **Logo block** | **Page title** | **Right side**

**Logo block (`.header-logo`):**
- Left-aligned, red background (`var(--mcd-red)`)
- Diagonal right edge: `clip-path: polygon(0 0, calc(100% - 20px) 0, 100% 100%, 0 100%)`
- `min-width: 280px`, padding `0 36px 0 16px`, `gap: 12px`
- **Icon container (`.header-logo-icon`):** white background, `border-radius: 10px`, `38×38px`, centres the Tarsyer owl image at `28×28px`
- **Text (`.header-logo-text`):** flex row, baseline aligned, `gap: 8px`
  - `.logo-name`: `"TARSYER"` — 16px, weight 900, white, `letter-spacing: 1.5px`, uppercase
  - `.logo-sub`: `"Tarsyer Store Manager"` — 13px, weight 600, `rgba(255,255,255,0.88)`

**Page title (`.header-title`):**
- Flex, left-padded 28px, 16px font, weight 700, `var(--text)`, `letter-spacing: -0.2px`
- Fills remaining space (`flex: 1`)
- Each page injects its own icon + label via `{% block page_title %}`

**Right side (`.header-right`):**
- Flex row, `gap: 14px`, padding `0 20px`
- User chip: Font Awesome `fa-circle-user` icon + `{{ session.user }}` — 12px, muted colour
- Vertical divider: `1px wide, 28px tall, var(--border)`
- Customer logo: `/static/img/mcd.png`, `height: 46px`

### Navigation Bar (`.topnav`)
- Background: `#27251F` (near-black)
- Height: 40px, flex row, `padding: 0 20px`, `gap: 2px`
- **Nav items (`.nav-item`):** 12.5px, `rgba(255,255,255,0.55)`, `padding: 0 14px`
  - Active: `var(--mcd-gold)` text + `2px solid var(--mcd-gold)` bottom border, weight 500
  - Hover: `rgba(255,255,255,0.9)`
  - Icons: Font Awesome, 12px, 0.8 opacity (1.0 when active)
- **Sign Out link:** pushed to right via `margin-left: auto`

**Nav items in this dashboard:**
1. Overview — `fa-gauge-high`
2. Alert Review — `fa-magnifying-glass`
3. Device Health — `fa-heart-pulse`
4. Sign Out — `fa-right-from-bracket` (right-aligned)

### Filter Bar (`.filter-bar`)
- White background, `border-bottom: 1px solid var(--border)`
- Padding `9px 24px`, flex row, `gap: 10px`, `flex-wrap: wrap`
- Contains: From/To date inputs, store multi-select dropdown, Apply button (red), quick-range pills (Today / Yesterday / 7 Days / 30 Days / 90 Days), Export Excel button (right-aligned via `margin-left: auto`)
- Date inputs: 12.5px, `border-radius: 6px`, focus ring `var(--mcd-red)` with `rgba(218,41,28,0.08)` shadow
- Quick-range pills (`.quick-btn`): `border-radius: 20px`, 11.5px — active/hover state: red background + white text
- Primary button (`.btn-primary`): `background: var(--mcd-red)`, white, `border-radius: 6px`
- Outline button (`.btn-outline`): transparent bg, `border: 1px solid var(--border)`

### Page Content (`.content`)
- Padding: `18px 24px 12px`

### Cards (`.card`)
- White background, `border-radius: 10px`, padding `14px 18px`
- Subtle shadow: `0 1px 3px rgba(0,0,0,0.05), 0 0 0 1px rgba(0,0,0,0.03)`
- Card title (`.card-title`): 11px, weight 600, `var(--muted)`, uppercase, `letter-spacing: 0.7px`

### Tables
- Full width, `border-collapse: collapse`, 13px
- `thead th`: `var(--bg)` background, 10.5px, muted uppercase, `letter-spacing: 0.6px`
- `tbody tr:hover`: `#f8f9fc`
- Cell padding: `8px 12px`

### Chips (`.chip`)
- `border-radius: 20px`, `padding: 4px 11px`, 11.5px, weight 600, `border: 1.5px solid`
- Variants: `chip-red`, `chip-gold`, `chip-green`, `chip-blue`, `chip-gray`, `chip-purple`

### Badges (`.badge`)
- `border-radius: 20px`, `padding: 3px 8px`, 11px, weight 600
- Variants: `badge-red`, `badge-green`, `badge-orange`, `badge-blue`, `badge-gray`

### Spinner (`.spinner`)
- `border: 3px solid var(--border); border-top: 3px solid var(--mcd-red)`
- `border-radius: 50%`, `28×28px`, `animation: spin 0.8s linear infinite`

### Modals (`.modal-overlay`)
- Fixed overlay: `rgba(0,0,0,0.5)`, centred flex, `z-index: 200`
- Box: white, `border-radius: 16px`, `max-width: 700px`, `width: 90%`, `padding: 24px`
- Close button: float right, 18px, muted colour

### Trend Indicators
- `.trend-up`: `var(--red)` — more violations is bad
- `.trend-down`: `var(--green)` — fewer violations is good
- `.trend-flat`: `var(--muted)`

### Scrollbar
- Width/height: 5px, transparent track, `var(--border)` thumb, `border-radius: 4px`

---

## Mobile Breakpoint (`max-width: 768px`)
- Header logo: hide text, reduce padding
- Header title: 14px
- Nav: `overflow-x: auto`
- Grid 2-col and 3-col: collapse to 1 column
- Period grid: 2 columns instead of 4

---

## External Dependencies
```html
<!-- Icons -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"/>
<!-- Font -->
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet"/>
<!-- Charts (dashboard pages only) -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
```

---

## Static Assets
| File | Usage |
|---|---|
| `/static/img/tarsyer.png` | Tarsyer owl logo — header icon, login page |
| `/static/img/mcd.png` | McDonald's golden arches — header right, login page |

---

## Key Design Principles
1. **Red is primary** — every interactive primary action uses `#DA291C`. Violations/alerts are always red.
2. **Gold is active** — `#FFC72C` marks the currently selected nav tab only.
3. **Near-black nav** — `#27251F` creates strong separation between the sticky header and content.
4. **Diagonal logo cut** — the red header-logo block uses `clip-path` to create an angled right edge, not a straight vertical cut.
5. **Muted card titles** — section headings inside cards are small, uppercase, muted grey — never bold or dark.
6. **Trend colours are inverted** — more violations = red (bad), fewer = green (good).
7. **Subtle cards** — white surface, very light shadow + 1px border ring. No heavy drop shadows.
8. **Two logos on login** — Tarsyer (vendor) and McDonald's (client) displayed side by side with equal sizing and white rounded backgrounds, separated by a semi-transparent vertical rule.
