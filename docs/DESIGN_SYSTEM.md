# hook.press Design System — Control Deck

**Version:** 1.0 (2026-07-15)  
**Product metaphor:** Producer control desk — focused, measurable progress, not entertainment streaming.

## Self-critique (pre-implementation)

| Initial instinct | Problem | Decision |
|------------------|---------|----------|
| Purple/violet SaaS gradient | Generic “AI startup” look; already overused in repo | **Rejected** — shift to cyan meter + slate console |
| Warm cream + terracotta | Explicitly banned in design prompt | **Rejected** |
| Pure black + single neon accent | Banned without justification | **Rejected** — use layered slate surfaces + dual signal colors |
| Spotify-style dark green | Too close to competitor | **Rejected** — cyan/teal = “signal LED”, amber = peak/warning only |

**Signature element:** **Progress Rail** — horizontal VU-style meter used for AI task progress, upload progress, and release pipeline fill. Appears in dashboard cards, studio audio panel, and office stepper connector.

---

## Color palette

| Token | Light | Dark | Meaning |
|-------|-------|------|---------|
| `--hp-bg` | `#f0f3f8` | `#080b10` | Console desk surface |
| `--hp-bg-elevated` | `#ffffff` | `#12161f` | Panels, cards |
| `--hp-bg-subtle` | `#e4e9f2` | `#1a2030` | Hover, inset areas |
| `--hp-fg` | `#0b0f16` | `#eef1f6` | Primary text |
| `--hp-fg-muted` | `#5c6578` | `#8b95a8` | Secondary text |
| `--hp-border` | `#d4dbe8` | `#2a3344` | Dividers |
| `--hp-accent` | `#0891b2` | `#22d3ee` | Active signal (meter LED) |
| `--hp-accent-hover` | `#0e7490` | `#67e8f9` | Hover |
| `--hp-accent-muted` | `rgba(8,145,178,0.12)` | `rgba(34,211,238,0.14)` | Selected nav, chips |
| `--hp-signal` | `#ea580c` | `#fb923c` | Peak / attention (sparingly) |
| `--hp-success` | `#15803d` | `#4ade80` | Succeeded meter |
| `--hp-warning` | `#b45309` | `#fbbf24` | Processing / caution |
| `--hp-danger` | `#dc2626` | `#f87171` | Failed / error |

Gradients use **cyan → teal** only on hero accents, not full-page washes.

---

## Typography

| Role | Font | CSS variable | Usage |
|------|------|--------------|-------|
| Display | **Syne** | `--font-display` | Page titles, track names, chart positions |
| Body | **DM Sans** | `--font-body` | UI copy, paragraphs |
| Utility | **JetBrains Mono** | `--font-mono` | BPM, ISRC, task IDs, statuses, durations |

Scale: `text-xs` metadata → `text-sm` UI → `text-base` body → `text-2xl/3xl font-display` headings.

---

## Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Top bar: logo · primary nav · search · notif · profile      │
├──────────┬──────────────────────────────────────────────────┤
│ Optional │ Main content (PageShell + PageHeader)            │
│ sidebar  │ Cards in 12-col grid, max-width 1280px           │
│ (dash)   │ Footer on marketing + app pages                  │
└──────────┴──────────────────────────────────────────────────┘
```

- **Marketing home:** full-bleed hero, no sidebar.
- **App screens:** `PageShell` + `PageHeader` + `Footer`; studio/office use **two/three column** editor layouts on `lg+`.
- **Mobile:** nav collapses to drawer; editor stacks vertically.

### Wireframes (ASCII)

**Dashboard**
```
[ Active studio projects ] [ AI tasks rail    ]
[ Office releases stepper] [ Notifications    ]
[ Market snapshot        ] [ Wallet balance   ]
```

**Studio**
```
[Project list] | [ Lyric editor    ] | [ Syllables / rhymes / assistant ]
               | [ Progress rail   ] | [ AI task status chips           ]
               | [ Waveform player ] | [ Send to office CTA             ]
```

**Office**
```
[ Projects ] | [ Release stepper: Draft → Validating → … → Released ]
             | [ Metadata form · tracklist · scoring card           ]
```

---

## Components (packages/ui)

- `Button`, `Card`, `Input`, `Textarea`, `Badge`, `Modal`, `Toast`
- `EmptyState`, `Skeleton`, `ProgressRail`, `StatusStepper`

## States (every screen)

1. **Loading** — `Skeleton` matching layout grid  
2. **Empty** — `EmptyState` + primary CTA  
3. **Error** — message + `retry` action  
4. **Populated** — real API data  

## Accessibility

- WCAG 2.1 AA contrast on `--hp-fg` vs surfaces  
- Visible `:focus-visible` ring (globals.css)  
- Semantic landmarks: one `<main>` per page (layout only)  
- i18n: all strings in `messages/{locale}.json`

## Theming

Tokens in `packages/ui/src/tokens.css`; components use `var(--hp-*)` only — no hardcoded zinc/emerald in app pages after migration.
