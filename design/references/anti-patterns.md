# Anti-Patterns Guide

Visual patterns that violate Braun Design Language principles. If you see these, fix them.

## Color Anti-Patterns

### Colored Accent Buttons

**Violation:** Using colored backgrounds for primary actions.

```css
/* WRONG */
.btn-primary {
  background: #3B82F6; /* Blue */
  background: #10B981; /* Green */
  background: #8B5CF6; /* Purple */
}

/* CORRECT */
.btn-primary {
  background: #1C1C1A; /* Near black (light mode) */
  background: #FAFAF8; /* Near white (dark mode) */
}
```

**Exception:** Amber accent buttons are allowed when specifically needed for emphasis.

---

### Gradient Overlays on Photography

**Violation:** Adding colored gradients over images.

```css
/* WRONG */
.hero-image::after {
  background: linear-gradient(to bottom, rgba(0,0,0,0.5), transparent);
  background: linear-gradient(135deg, #667eea, #764ba2);
}

/* CORRECT */
.hero-image {
  /* No overlay. Let photography speak. */
}
.hero-caption {
  /* Put text below image on solid surface */
  background: var(--color-surface);
}
```

---

### Decorative Color

**Violation:** Using color for visual interest rather than function.

```css
/* WRONG */
.sidebar { border-left: 4px solid #3B82F6; }
.card-accent { background: linear-gradient(90deg, #F0FDFA, #FFFFFF); }
.tag { background: #EEF2FF; color: #4F46E5; }

/* CORRECT */
.sidebar { border-left: none; }
.card-accent { background: var(--color-surface); }
.tag { background: var(--color-surface); color: var(--color-text-secondary); }
```

**Rule:** Color communicates function only: success, error, warning, info.

---

## Shape Anti-Patterns

### Rounded Corners > 8px

**Violation:** Large border radii creating "pill" or "bubble" shapes.

```css
/* WRONG */
.card { border-radius: 12px; }
.btn { border-radius: 9999px; }
.avatar { border-radius: 16px; }

/* CORRECT */
.card { border-radius: 8px; }
.btn { border-radius: 6px; }
.avatar { border-radius: 50%; } /* Full circle OK */
```

---

### Arbitrary Curves

**Violation:** Organic, expressive, or "blob" shapes.

```css
/* WRONG */
.decoration {
  border-radius: 30% 70% 70% 30% / 30% 30% 70% 70%;
}
.wave-divider {
  clip-path: url(#wave-path);
}

/* CORRECT */
.divider {
  border-bottom: 1px solid var(--color-border);
}
```

**Rule:** All curves must be mathematically derived. Circles, straight lines, rectangles only.

---

## Shadow Anti-Patterns

### Decorative Shadows

**Violation:** Heavy shadows for visual effect.

```css
/* WRONG */
.card {
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

/* CORRECT - Light mode */
.card {
  border: 1px solid var(--color-border);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

/* CORRECT - Dark mode */
[data-theme="dark"] .card {
  background: var(--elevation-2);
  box-shadow: none;
}
```

---

### Decorative Glows

**Violation:** Colored glows or halos.

```css
/* WRONG */
.btn:hover {
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
}
.input:focus {
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.3);
}

/* CORRECT */
.btn:hover {
  background: #333330;
}
.input:focus {
  border-color: var(--color-accent);
  outline: none;
}
```

---

## Typography Anti-Patterns

### Multiple Font Families

**Violation:** Using different typefaces for different elements.

```css
/* WRONG - ANY of these */
h1 { font-family: 'Playfair Display', serif; }
body { font-family: 'Inter', sans-serif; }
code { font-family: 'JetBrains Mono', monospace; }
.accent { font-family: 'Lobster', cursive; }

/* CORRECT - Braun Linear ONLY */
* { font-family: 'Braun Linear', system-ui, sans-serif; }
code, pre { font-family: 'Braun Linear', system-ui, sans-serif; font-weight: 300; }
```

---

### Text Shadows

**Violation:** Shadows on text for style.

```css
/* WRONG */
.hero-title {
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

/* CORRECT */
.hero-title {
  color: var(--color-text);
  /* No shadow */
}
```

---

### Gradient Text

**Violation:** Gradient fills on text.

```css
/* WRONG */
.fancy-title {
  background: linear-gradient(90deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* CORRECT */
.title {
  color: var(--color-text);
}
```

---

## Animation Anti-Patterns

### Animated Loading Skeletons

**Violation:** Shimmer/pulse animations on placeholders.

```css
/* WRONG */
.skeleton {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  animation: shimmer 1.5s infinite;
}

/* CORRECT */
.loading-placeholder {
  background: var(--color-surface);
  /* Static. No animation. */
}
```

---

### Decorative Motion

**Violation:** Bounces, pulses, attention-seeking animation.

```css
/* WRONG */
.notification-badge {
  animation: pulse 2s infinite;
}
.cta-button {
  animation: bounce 1s infinite;
}
.icon {
  animation: spin 2s linear infinite;
}

/* CORRECT */
/* No decorative animations */
.element {
  transition: opacity 150ms ease;
}
```

**Rule:** Motion informs, not entertains. Transitions only.

---

## Spacing Anti-Patterns

### Non-Grid Spacing

**Violation:** Arbitrary spacing values not on 8pt grid.

```css
/* WRONG */
.card { padding: 18px; }
.section { margin-bottom: 50px; }
.button { padding: 10px 22px; }
.gap { gap: 15px; }

/* CORRECT */
.card { padding: 16px; }
.section { margin-bottom: 48px; }
.button { padding: 10px 20px; }
.gap { gap: 16px; }
```

**Allowed:** 4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96...

---

## Icon Anti-Patterns

### Ornamental Icons

**Violation:** Decorative icons without function.

```css
/* WRONG */
.feature::before {
  content: '★';
}
.section-header .decorative-icon { /* purely visual */ }

/* CORRECT */
/* Icons only when they communicate function */
/* Search icon for search */
/* Settings icon for settings */
```

---

### Filled/Colored Icons

**Violation:** Icons with fills or multiple colors.

```css
/* WRONG */
.icon {
  fill: linear-gradient(#667eea, #764ba2);
  fill: #3B82F6;
}

/* CORRECT */
.icon {
  stroke: currentColor;
  fill: none;
  stroke-width: 2;
}
```

---

## Quick Verification

For any UI element, ask:

| Question | If Yes... |
|----------|-----------|
| Is there color? | Must communicate function (success/error/warning) |
| Is there a shadow? | Must communicate elevation (light mode only) |
| Is there animation? | Must be functional feedback only |
| Is there decoration? | Remove it |
| Is spacing off-grid? | Fix to 8pt multiple |
| Is border-radius > 8px? | Reduce (unless 50% circle) |
| Is font Braun Linear? | If not, fix it - ONLY Braun Linear allowed |

If any element exists purely for visual interest, it violates the design language.
