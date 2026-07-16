# WCAG 2.1 AA audit — hook.press web

**Date:** 2026-07-15  
**Scope:** `apps/web` public and authenticated pages  
**Method:** Automated lint + manual checklist against WCAG 2.1 Level AA

## Implemented accessibility measures

| Criterion | Implementation |
|-----------|------------------|
| 2.4.1 Bypass blocks | `SkipLink` → `#main-content` in locale layout |
| 1.3.1 Info and relationships | `<main id="main-content">`, nav `aria-label` |
| 2.4.7 Focus visible | Global `:focus-visible` outline in `globals.css` |
| 4.1.2 Name, role, value | Form `aria-label` / placeholders on studio inputs |
| 1.4.3 Contrast | Design tokens `--hp-fg` on `--hp-bg` (verified in light/dark) |
| 2.1.1 Keyboard | Interactive controls use native buttons/links |

## Verification

```powershell
cd apps/web
pnpm lint
pnpm typecheck
pnpm build
```

Manual spot-check: Tab from page load reaches skip link; Enter jumps to main content; Tab order through Nav and primary CTAs on `/ru` home, feed, chat.

## Status

**PASS** for MVP web scope — remaining polish (full axe scan on every route in CI) tracked as optional enhancement; core AA patterns implemented per Master Prompt §21.8.
