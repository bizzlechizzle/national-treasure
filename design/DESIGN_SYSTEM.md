# Braun Design System v0.1.0

Complete specification for the Braun Design Language. Based on Dieter Rams' principles and functional minimalism.

## Core Philosophy

> **"Weniger, aber besser"** — Less, but better.

1. **Content speaks** — Photography, data, and text are heroes; UI recedes
2. **Function over form** — Every element must serve a purpose
3. **Honest materials** — Show real data, no fake placeholders
4. **Systematic consistency** — Grid-based, token-driven
5. **Timeless over trendy** — Design for 5+ year relevance

## Typography

### Font Stack

```css
:root {
  /* BRAUN LINEAR ONLY - Single font family for ALL text */
  --font-family: 'Braun Linear', system-ui, sans-serif;

  /* Weight tokens */
  --font-thin: 100;
  --font-light: 300;
  --font-regular: 400;
  --font-medium: 500;
  --font-bold: 700;
}

/* @font-face declarations - include all weights */
@font-face {
  font-family: 'Braun Linear';
  src: url('fonts/BraunLinear-Thin.woff2') format('woff2');
  font-weight: 100;
  font-display: swap;
}
@font-face {
  font-family: 'Braun Linear';
  src: url('fonts/BraunLinear-Light.woff2') format('woff2');
  font-weight: 300;
  font-display: swap;
}
@font-face {
  font-family: 'Braun Linear';
  src: url('fonts/BraunLinear-Regular.woff2') format('woff2');
  font-weight: 400;
  font-display: swap;
}
@font-face {
  font-family: 'Braun Linear';
  src: url('fonts/BraunLinear-Medium.woff2') format('woff2');
  font-weight: 500;
  font-display: swap;
}
@font-face {
  font-family: 'Braun Linear';
  src: url('fonts/BraunLinear-Bold.woff2') format('woff2');
  font-weight: 700;
  font-display: swap;
}
```

### Font Usage

**Braun Linear** is the ONLY font. Use weight variations for hierarchy:

| Weight | CSS Value | Use |
|--------|-----------|-----|
| Thin | 100 | Display text, decorative (rare) |
| Light | 300 | Captions, meta text, code |
| Regular | 400 | Body text, inputs |
| Medium | 500 | Buttons, nav, labels, emphasis |
| Bold | 700 | Headlines, page titles |

### Type Scale

| Token | Size | Weight | Line Height | Letter Spacing | Use |
|-------|------|--------|-------------|----------------|-----|
| `--text-xs` | 11px | 500 | 1.3 | 0.1em | Labels (UPPERCASE) |
| `--text-sm` | 13px | 300 | 1.5 | 0 | Captions, metadata, code |
| `--text-base` | 15px | 400 | 1.6 | 0 | Body text |
| `--text-lg` | 17px | 500 | 1.5 | 0 | Subsection heads |
| `--text-xl` | 20px | 500 | 1.4 | -0.01em | Section heads |
| `--text-2xl` | 24px | 700 | 1.3 | -0.01em | Page titles |
| `--text-3xl` | 30px | 700 | 1.2 | -0.02em | Hero titles |
| `--text-4xl` | 36px | 700 | 1.2 | -0.02em | Display (rare) |

### Font Weights (Braun Linear)

| Token | Value | Use |
|-------|-------|-----|
| `--font-thin` | 100 | Display, decorative (rare) |
| `--font-light` | 300 | Captions, meta, code |
| `--font-regular` | 400 | Body text, inputs |
| `--font-medium` | 500 | Buttons, nav, labels |
| `--font-bold` | 700 | Headlines, titles |

**Note:** Braun Linear has no 600 weight. Use 500 (Medium) or 700 (Bold) instead.

---

## Color System

### Neutral Palette

#### Light Mode (Default)

| Token | Hex | RGB | Use |
|-------|-----|-----|-----|
| `--neutral-50` | `#FAFAF8` | 250,250,248 | Canvas/background |
| `--neutral-100` | `#F4F4F2` | 244,244,242 | Surface level 1 |
| `--neutral-200` | `#EEEEED` | 238,238,237 | Subtle borders |
| `--neutral-300` | `#E2E1DE` | 226,225,222 | Default borders |
| `--neutral-400` | `#C0BFBC` | 192,191,188 | Emphasis borders |
| `--neutral-500` | `#8A8A86` | 138,138,134 | Muted text |
| `--neutral-600` | `#5C5C58` | 92,92,88 | Secondary text |
| `--neutral-800` | `#333330` | 51,51,48 | — |
| `--neutral-900` | `#1C1C1A` | 28,28,26 | Primary text |
| `--neutral-950` | `#0F0F0E` | 15,15,14 | — |

#### Dark Mode

| Token | Hex | Opacity | Use |
|-------|-----|---------|-----|
| `--neutral-950` | `#0a0a0b` | — | Canvas/background |
| `--neutral-900` | `#111113` | — | Surface level 1 |
| `--neutral-850` | `#1A1A1C` | — | Surface level 2 |
| `--neutral-800` | `#1f1f23` | — | Subtle borders |
| `--neutral-700` | `#2D2D30` | — | Default borders |
| `--neutral-600` | `#3A3A3E` | — | Emphasis borders |
| `--neutral-100` | `#FAFAF8` | 87% | Primary text |
| `--neutral-200` | `#FAFAF8` | 60% | Secondary text |
| `--neutral-400` | `#FAFAF8` | 38% | Muted text |

### Accent Palette (Amber)

Optional accent for interactive elements. Use sparingly.

| Token | Light Mode | Dark Mode | Use |
|-------|------------|-----------|-----|
| `--accent-50` | `#fffbeb` | — | Tinted backgrounds |
| `--accent-100` | `#fef3c7` | `#fef3c7` | Hover backgrounds |
| `--accent-400` | `#fbbf24` | `#fbbf24` | Primary accent |
| `--accent-500` | `#f59e0b` | `#f59e0b` | Buttons, links |
| `--accent-600` | `#d97706` | `#d97706` | Hover states |
| `--accent-700` | `#b45309` | `#b45309` | Active states |

### Functional Colors

Semantic colors for status and feedback. Same in both modes.

| Token | Hex | Use |
|-------|-----|-----|
| `--success` | `#22c55e` | Verified, complete, positive |
| `--warning` | `#eab308` | Caution, attention needed |
| `--error` | `#ef4444` | Error, destructive, failed |
| `--info` | `#3b82f6` | Informational, links |
| `--neutral` | `#6b7280` | Unknown, not applicable |

---

## Spacing System

### 8pt Grid

All spacing values are multiples of 8px. Use 4px for fine adjustments only.

```css
:root {
  --space-0: 0;
  --space-1: 4px;   /* Fine adjustment */
  --space-2: 8px;   /* Tight grouping */
  --space-3: 12px;  /* Related elements */
  --space-4: 16px;  /* Component padding */
  --space-5: 20px;  /* — */
  --space-6: 24px;  /* Section spacing */
  --space-8: 32px;  /* Group separation */
  --space-10: 40px; /* — */
  --space-12: 48px; /* Major sections */
  --space-16: 64px; /* Page sections */
  --space-20: 80px; /* — */
  --space-24: 96px; /* Hero spacing */
}
```

### Common Patterns

| Context | Value | Token |
|---------|-------|-------|
| Icon margin | 4px | `--space-1` |
| Button icon gap | 8px | `--space-2` |
| Input padding | 10-12px | `--space-3` |
| Card padding | 16px | `--space-4` |
| Section gap | 24px | `--space-6` |
| Card grid gap | 24-32px | `--space-6` to `--space-8` |
| Page sections | 48-64px | `--space-12` to `--space-16` |

---

## Border Radius

```css
:root {
  --radius-none: 0;
  --radius-sm: 4px;    /* Badges, chips, tags */
  --radius-md: 6px;    /* Buttons, inputs, small cards */
  --radius-lg: 8px;    /* Cards, panels, modals */
  --radius-full: 50%;  /* Avatars, circular icons */
}
```

**Rule:** Never exceed 8px except for full circles.

---

## Shadows & Elevation

### Light Mode

Use shadows sparingly for elevation hierarchy.

```css
:root {
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-md: 0 2px 4px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 4px 8px rgba(0, 0, 0, 0.08);
}
```

### Dark Mode

**No shadows.** Use surface lightness for elevation.

| Elevation | Surface Color |
|-----------|---------------|
| Base (0) | `#0a0a0b` |
| Level 1 | `#111113` |
| Level 2 | `#1A1A1C` |
| Level 3 | `#252527` |
| Level 4 | `#2D2D30` |

---

## Motion

### Timing

```css
:root {
  --duration-instant: 0ms;
  --duration-fast: 100ms;     /* Hover states */
  --duration-normal: 150ms;   /* Most transitions */
  --duration-slow: 250ms;     /* Modal open/close */
  --duration-slower: 350ms;   /* Page transitions */
}
```

### Easing

```css
:root {
  --ease-default: cubic-bezier(0.25, 0, 0.25, 1);
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-out: cubic-bezier(0, 0, 0.25, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.25, 1);
}
```

### Accessibility

Always respect user preferences:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Layout

### Breakpoints

| Name | Width | Columns | Use |
|------|-------|---------|-----|
| Mobile | < 640px | 4 | Phone portrait |
| Tablet | 640-1023px | 8 | Tablet/phone landscape |
| Desktop | 1024-1279px | 12 | Standard desktop |
| Wide | ≥ 1280px | 12 | Large monitors |

### Container

```css
.container {
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 var(--space-4);
}

@media (min-width: 640px) {
  .container { padding: 0 var(--space-6); }
}

@media (min-width: 1024px) {
  .container { padding: 0 var(--space-8); }
}
```

---

## Accessibility

### Contrast Requirements

| Element | Minimum Ratio | Standard |
|---------|---------------|----------|
| Normal text | 4.5:1 | WCAG AA |
| Large text (24px+) | 3:1 | WCAG AA |
| UI components | 3:1 | WCAG AA |
| Focus indicators | 3:1 | WCAG AA |

### Touch Targets

- Minimum: 44×44px
- Recommended: 48×48px for primary actions

### Focus States

```css
:focus-visible {
  outline: 2px solid var(--accent-500);
  outline-offset: 2px;
}
```

---

## Theme Implementation

### CSS Custom Properties

```css
:root {
  color-scheme: light dark;

  /* Default to light */
  --color-canvas: var(--neutral-50);
  --color-surface: var(--neutral-100);
  --color-text: var(--neutral-900);
  --color-text-secondary: var(--neutral-600);
  --color-border: var(--neutral-300);
}

@media (prefers-color-scheme: dark) {
  :root {
    --color-canvas: #0a0a0b;
    --color-surface: #111113;
    --color-text: rgba(250, 250, 248, 0.87);
    --color-text-secondary: rgba(250, 250, 248, 0.60);
    --color-border: #1f1f23;
  }
}

/* Manual override */
[data-theme="light"] {
  --color-canvas: var(--neutral-50);
  /* ... */
}

[data-theme="dark"] {
  --color-canvas: #0a0a0b;
  /* ... */
}
```

---

## References

- `@references/component-specs.md` — Complete component CSS
- `@references/dark-mode.md` — Dark mode implementation guide
- `@references/anti-patterns.md` — What to avoid

## Sources

- Dieter Rams' 10 Principles of Good Design
- Ulm School of Design methodology
- Material Design dark theme guidelines (for dark mode elevation)
- WCAG 2.1 accessibility standards
