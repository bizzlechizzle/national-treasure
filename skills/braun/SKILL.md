---
name: braun
description: Verify front-end UI changes against Braun Design Language (Functional Minimalism) principles. Use when reviewing UI components, pages, or design systems for compliance with Dieter Rams' 10 principles, checking color usage, typography, spacing, geometry, and avoiding anti-patterns. Supports both light mode and dark mode verification. Trigger for design reviews, UI audits, component checks, pull request reviews of front-end changes, or when ensuring adherence to functional minimalism principles.
---

# Braun Design Language Verification v0.1.0

Verify front-end UI against Braun Design Language: Functional Minimalism.

## Core Philosophy

**"Weniger, aber besser"** — Less, but better.

The interface must recede so content speaks. Every element must justify its existence through function.

## Quick Verification Checklist

Run through these checks for any UI change:

### 1. Color Verification

**Light Mode Palette:**
- Canvas/Background: `#FAFAF8` (warm white)
- Surface/Cards: `#F4F4F2` or `#FFFFFF`
- Primary Text: `#1C1C1A` (near-black)
- Secondary Text: `#5C5C58`
- Tertiary/Meta: `#8A8A86`
- Borders: `#E2E1DE` (standard), `#EEEEED` (subtle), `#C0BFBC` (emphasis)

**Dark Mode Palette:**
- Canvas/Background: `#0a0a0b` (never pure black)
- Surface/Cards: `#111113` to `#1A1A1C`
- Primary Text: `rgba(250,250,248,0.87)` (never pure white)
- Secondary Text: `rgba(250,250,248,0.60)`
- Tertiary/Meta: `rgba(250,250,248,0.38)`
- Borders: `#1f1f23` (subtle), `#2D2D30` (standard), `#3A3A3E` (emphasis)

**Accent Color (Optional - Amber):**
- Primary: `#f59e0b` (amber-500)
- Hover: `#d97706`
- Light Surface: `#fef3c7`
- Dark Surface: `rgba(251,191,36,0.15)`

**Functional Colors (both modes):**
- Success: `#22c55e`
- Warning: `#eab308`
- Error: `#ef4444`
- Info: `#3b82f6`
- Neutral: `#6b7280`

### 2. Typography Verification

**Font: Braun Linear (EXCLUSIVE)**

Single font family for ALL text. No exceptions.

```css
font-family: 'Braun Linear', system-ui, sans-serif;
```

**Available Weights:**
| Weight | CSS Value | Use |
|--------|-----------|-----|
| Thin | 100 | Display text, decorative |
| Light | 300 | Captions, meta, code |
| Regular | 400 | Body text, inputs |
| Medium | 500 | Buttons, nav items, emphasis |
| Bold | 700 | Headlines, strong emphasis |

**Scale (in pixels):**
| Size | Weight | Use | Letter Spacing |
|------|--------|-----|----------------|
| 36px | 700 Bold | Hero titles | -0.02em |
| 24px | 700 Bold | Page titles | -0.01em |
| 20px | 500 Medium | Section heads | -0.01em |
| 17px | 500 Medium | Subsections | 0 |
| 15px | 400 Regular | Body text | 0 |
| 13px | 300 Light | Captions/meta | 0 |
| 11px | 500 Medium | Labels (UPPERCASE) | 0.1em |

### 3. Spacing Verification (8pt Grid)

All spacing must be multiples of 8px: `8, 16, 24, 32, 40, 48, 56, 64...`

Fine adjustments use 4px half-step for icons/text alignment.

**Common Values:**
- Component gap: 16px
- Section gap: 24-32px
- Card padding: 16px or 24px
- Button padding: 10px vertical, 20px horizontal
- Input padding: 10-12px
- Page sections: 48-64px

### 4. Border Radius Verification

**ALLOWED:**
- 4px: Badges, chips, tags
- 6px: Buttons, inputs, small cards
- 8px: Cards, panels, modals
- 50%: Avatars, circular icons

**FORBIDDEN:**
- Border-radius > 8px (except full circles)
- Inconsistent radii within component
- Pill shapes (9999px)

### 5. Geometry Verification

**ALLOWED:**
- Rectangles
- Circles (for avatars, icons)
- Straight lines
- Mathematically proportional curves

**FORBIDDEN:**
- Arbitrary curves
- Expressive/organic shapes
- Blob shapes
- Wave dividers

### 6. Anti-Pattern Check

**REJECT if present:**
- [ ] Colored accent buttons (use neutral or amber only)
- [ ] Gradient overlays on imagery
- [ ] Decorative shadows (shadows communicate elevation only)
- [ ] Decorative glows or halos
- [ ] Rounded corners > 8px
- [ ] Animated loading skeletons (use static)
- [ ] Text shadows on titles
- [ ] Color used for decoration (not function)
- [ ] Ornamental icons/illustrations
- [ ] Any font other than Braun Linear
- [ ] Non-grid-aligned spacing
- [ ] Pure black (#000000) or pure white (#FFFFFF)

## Rams' 10 Principles Verification

For comprehensive design reviews, verify against all 10 principles:

1. **Innovative** — Solves real problems, not innovation for novelty
2. **Useful** — Every element serves user task completion
3. **Aesthetic** — Clean, harmonious, mathematically proportioned
4. **Understandable** — Self-explanatory interface, minimal instruction needed
5. **Unobtrusive** — Interface recedes, content speaks
6. **Honest** — No deceptive patterns, states what it does
7. **Long-lasting** — Avoids trends, timeless design
8. **Thorough** — Every detail considered, nothing arbitrary
9. **Environmentally conscious** — Efficient, minimal resource use
10. **Minimal** — "Less, but better" — only essential elements

## Component Standards

### Buttons
```css
.btn {
  padding: 10px 20px;
  font-family: 'Braun Linear', system-ui, sans-serif;
  font-size: 15px;
  font-weight: 500; /* Medium */
  border-radius: 6px;
  transition: all 150ms ease;
}
.btn-primary { background: #1C1C1A; color: #FFFFFF; }
.btn-secondary { background: transparent; border: 1px solid #C0BFBC; }
.btn-ghost { background: transparent; color: #5C5C58; }
.btn-accent { background: #f59e0b; color: #1C1C1A; }
```

### Inputs
```css
.input {
  padding: 10px 12px;
  font-family: 'Braun Linear', system-ui, sans-serif;
  font-size: 15px;
  font-weight: 400; /* Regular */
  border: 1px solid #C0BFBC;
  border-radius: 6px;
}
.input:focus { border-color: #f59e0b; outline: none; }
```

### Cards
```css
.card {
  background: #FFFFFF;
  border: 1px solid #E2E1DE;
  border-radius: 8px;
  padding: 16px;
}
```

## Theme Detection

Default to system preference, fallback to light:

```css
:root { color-scheme: light dark; }

@media (prefers-color-scheme: dark) {
  :root { /* dark tokens */ }
}

[data-theme="light"] { /* force light */ }
[data-theme="dark"] { /* force dark */ }
```

## Dark Mode Guidelines

See `references/dark-mode.md` for complete dark mode implementation guide.

**Key principles:**
- Never use pure black (`#000000`) — use `#0a0a0b`
- Never use pure white (`#FFFFFF`) — use `rgba(250,250,248,0.87)`
- Use surface elevation (lighter = closer) instead of shadows
- Maintain 4.5:1 minimum contrast ratio (WCAG AA)

## Verification Workflow

1. **Extract** current styles from component/page
2. **Compare** against design system values
3. **Check** for anti-patterns
4. **Verify** grid alignment (8pt system)
5. **Validate** color contrast (WCAG AA - 4.5:1 minimum)
6. **Confirm** typography scale adherence
7. **Report** findings with specific remediation

## Additional References

- `references/dark-mode.md` — Complete dark mode color system
- `references/component-specs.md` — Detailed component specifications
- `references/anti-patterns.md` — Expanded anti-pattern examples

## Sources

- Dieter Rams' 10 Principles of Good Design
- Ulm School of Design methodology
- Material Design dark theme guidelines
- WCAG 2.1 accessibility standards
