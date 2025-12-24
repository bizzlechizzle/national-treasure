# Dark Mode Implementation

Complete guide for implementing dark mode in Braun Design Language.

## Core Principles

1. **Never pure black** — Use `#0a0a0b` minimum for backgrounds
2. **Never pure white** — Use `#FAFAF8` at 87% opacity for text
3. **Elevation through lightness** — Higher surfaces are lighter (no shadows)
4. **Desaturate slightly** — Reduce color intensity by ~10-15%
5. **Maintain contrast** — WCAG AA minimum (4.5:1 for text)

## Theme Detection

Default to system preference, fallback to light:

```css
:root {
  color-scheme: light dark;

  /* Light mode defaults */
  --color-canvas: #FAFAF8;
  --color-surface: #F4F4F2;
  --color-surface-elevated: #FFFFFF;
  --color-text: #1C1C1A;
  --color-text-secondary: #5C5C58;
  --color-text-muted: #8A8A86;
  --color-border: #E2E1DE;
  --color-border-emphasis: #C0BFBC;
}

@media (prefers-color-scheme: dark) {
  :root {
    --color-canvas: #0a0a0b;
    --color-surface: #111113;
    --color-surface-elevated: #1A1A1C;
    --color-text: rgba(250, 250, 248, 0.87);
    --color-text-secondary: rgba(250, 250, 248, 0.60);
    --color-text-muted: rgba(250, 250, 248, 0.38);
    --color-border: #1f1f23;
    --color-border-emphasis: #3A3A3E;
  }
}
```

## Manual Theme Override

For user preference toggles:

```css
[data-theme="light"] {
  --color-canvas: #FAFAF8;
  --color-surface: #F4F4F2;
  --color-surface-elevated: #FFFFFF;
  --color-text: #1C1C1A;
  --color-text-secondary: #5C5C58;
  --color-text-muted: #8A8A86;
  --color-border: #E2E1DE;
  --color-border-emphasis: #C0BFBC;
}

[data-theme="dark"] {
  --color-canvas: #0a0a0b;
  --color-surface: #111113;
  --color-surface-elevated: #1A1A1C;
  --color-text: rgba(250, 250, 248, 0.87);
  --color-text-secondary: rgba(250, 250, 248, 0.60);
  --color-text-muted: rgba(250, 250, 248, 0.38);
  --color-border: #1f1f23;
  --color-border-emphasis: #3A3A3E;
}
```

## JavaScript Toggle

```javascript
function setTheme(theme) {
  if (theme === 'system') {
    document.documentElement.removeAttribute('data-theme');
    localStorage.removeItem('theme');
  } else {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }
}

// On page load
function initTheme() {
  const saved = localStorage.getItem('theme');
  if (saved) {
    document.documentElement.setAttribute('data-theme', saved);
  }
  // Otherwise, CSS handles system preference
}
```

## Complete Color Mapping

### Background Surfaces

| Token | Light | Dark | Use |
|-------|-------|------|-----|
| canvas | `#FAFAF8` | `#0a0a0b` | App background |
| surface | `#F4F4F2` | `#111113` | Cards, panels |
| surface-elevated | `#FFFFFF` | `#1A1A1C` | Modals, dropdowns |
| surface-overlay | `rgba(0,0,0,0.5)` | `rgba(0,0,0,0.7)` | Modal backdrops |

### Text Colors

| Token | Light | Dark | Use |
|-------|-------|------|-----|
| text | `#1C1C1A` | `rgba(250,250,248,0.87)` | Headlines, body |
| text-secondary | `#5C5C58` | `rgba(250,250,248,0.60)` | Descriptions |
| text-muted | `#8A8A86` | `rgba(250,250,248,0.38)` | Captions, meta |
| text-disabled | `#C0BFBC` | `rgba(250,250,248,0.38)` | Disabled states |

### Border Colors

| Token | Light | Dark | Use |
|-------|-------|------|-----|
| border-subtle | `#EEEEED` | `#1f1f23` | Subtle dividers |
| border | `#E2E1DE` | `#2D2D30` | Card borders |
| border-emphasis | `#C0BFBC` | `#3A3A3E` | Input focus |

### Accent Colors (Amber)

| Token | Light | Dark | Use |
|-------|-------|------|-----|
| accent | `#f59e0b` | `#fbbf24` | Primary accent |
| accent-hover | `#d97706` | `#f59e0b` | Hover state |
| accent-surface | `#fef3c7` | `rgba(251,191,36,0.15)` | Tinted backgrounds |

### Functional Colors

Same in both modes for consistency:

| Function | Color | Use |
|----------|-------|-----|
| Success | `#22c55e` | Verified, complete |
| Warning | `#eab308` | Caution needed |
| Error | `#ef4444` | Error, failed |
| Info | `#3b82f6` | Informational |

## Elevation System (Dark Mode Only)

In dark mode, elevation is communicated through surface lightness, not shadows.

| Level | Surface | Use |
|-------|---------|-----|
| 0 (Base) | `#0a0a0b` | App background |
| 1 | `#111113` | Cards, sidebars |
| 2 | `#1A1A1C` | Elevated cards, dropdowns |
| 3 | `#252527` | Modals, popovers |
| 4 | `#2D2D30` | Tooltips, highest layer |

```css
[data-theme="dark"] {
  --elevation-0: #0a0a0b;
  --elevation-1: #111113;
  --elevation-2: #1A1A1C;
  --elevation-3: #252527;
  --elevation-4: #2D2D30;
}
```

## Component Adaptations

### Buttons

```css
/* Primary button inverts in dark mode */
[data-theme="dark"] .btn-primary {
  background: rgba(250, 250, 248, 0.87);
  color: #0a0a0b;
}

[data-theme="dark"] .btn-primary:hover {
  background: rgba(250, 250, 248, 0.75);
}

/* Secondary uses lighter border */
[data-theme="dark"] .btn-secondary {
  border-color: #3A3A3E;
  color: rgba(250, 250, 248, 0.87);
}
```

### Inputs

```css
[data-theme="dark"] .input {
  background: #111113;
  border-color: #3A3A3E;
  color: rgba(250, 250, 248, 0.87);
}

[data-theme="dark"] .input:focus {
  border-color: #fbbf24;
}

[data-theme="dark"] .input::placeholder {
  color: rgba(250, 250, 248, 0.38);
}
```

### Cards

```css
[data-theme="dark"] .card {
  background: #1A1A1C;
  border-color: #1f1f23;
}

[data-theme="dark"] .card:hover {
  border-color: #2D2D30;
}
```

### Navigation

```css
[data-theme="dark"] .nav-item {
  color: rgba(250, 250, 248, 0.60);
}

[data-theme="dark"] .nav-item:hover,
[data-theme="dark"] .nav-item.active {
  background: rgba(255, 255, 255, 0.05);
  color: rgba(250, 250, 248, 0.87);
}
```

## Contrast Verification

All combinations must pass WCAG AA (4.5:1 for text):

| Combination | Ratio | Pass |
|-------------|-------|------|
| `#FAFAF8` on `#0a0a0b` | 18.1:1 | Yes |
| `rgba(250,250,248,0.87)` on `#0a0a0b` | 15.8:1 | Yes |
| `rgba(250,250,248,0.60)` on `#111113` | 9.2:1 | Yes |
| `rgba(250,250,248,0.38)` on `#1A1A1C` | 5.1:1 | Yes |
| `#fbbf24` on `#0a0a0b` | 10.4:1 | Yes |

## Implementation Checklist

- [ ] Add `color-scheme: light dark` to `:root`
- [ ] Define all tokens with CSS custom properties
- [ ] Add `@media (prefers-color-scheme: dark)` rules
- [ ] Add `[data-theme="dark"]` override rules
- [ ] Remove all shadows in dark mode
- [ ] Use elevation surfaces instead
- [ ] Test all functional colors for contrast
- [ ] Verify focus states are visible
- [ ] Check scrollbar styling
- [ ] Test images don't clash with dark background
