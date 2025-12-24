# Braun Design Language v0.1.0

**"Weniger, aber besser"** — Less, but better.

Quick reference for functional minimalism. Full spec: `@DESIGN_SYSTEM.md`

## Philosophy

Content speaks. Interface recedes. Every element justifies its existence through function.

## Typography

**Font: Braun Linear (EXCLUSIVE)**

Single font family. No exceptions.

| Use | Size | Weight |
|-----|------|--------|
| Hero titles | 36px | 700 (Bold) |
| Page titles | 24px | 700 (Bold) |
| Section heads | 20px | 500 (Medium) |
| Subsections | 17px | 500 (Medium) |
| Body | 15px | 400 (Regular) |
| Captions/meta | 13px | 300 (Light) |
| Labels (UPPERCASE) | 11px | 500 (Medium) |
| Code/hashes | 13px | 300 (Light) |

**Available Weights:** Thin (100), Light (300), Regular (400), Medium (500), Bold (700)

## Colors

### Light Mode
- Canvas: `#FAFAF8` | Surface: `#F4F4F2` | Cards: `#FFFFFF`
- Text: `#1C1C1A` | Secondary: `#5C5C58` | Muted: `#8A8A86`
- Border: `#E2E1DE` | Emphasis: `#C0BFBC`

### Dark Mode
- Canvas: `#0a0a0b` | Surface: `#111113` | Elevated: `#1A1A1C`
- Text: `rgba(250,250,248,0.87)` | Secondary: `0.60` | Muted: `0.38`
- Border: `#1f1f23` | Emphasis: `#3A3A3E`

### Functional (both modes)
- Success: `#22c55e` | Warning: `#eab308` | Error: `#ef4444` | Info: `#3b82f6`

### Accent (optional)
- Primary: `#f59e0b` (amber-500) | Hover: `#d97706` | Light surface: `#fef3c7`

## Spacing (8pt Grid)

`4 | 8 | 12 | 16 | 24 | 32 | 48 | 64` px

- Component padding: 16px
- Section gap: 24-32px
- Page sections: 48-64px

## Border Radius

- Badges/chips: `4px`
- Buttons/inputs: `6px`
- Cards: `8px`
- Avatars: `50%`

## Anti-Patterns

| Never | Why |
|-------|-----|
| Colored accent buttons | Color = function only |
| Gradients on images | Let photography speak |
| Drop shadows (dark mode) | Use surface elevation |
| Border-radius > 8px | Undermines seriousness |
| Animated skeletons | Motion informs, not entertains |
| Pure black `#000` | Eye strain |
| Any font except Braun Linear | One font family only |

## Theme Detection

```css
/* System preference, fallback light */
@media (prefers-color-scheme: dark) {
  :root { /* dark tokens */ }
}
```

## Verification Checklist

- [ ] Colors from palette only
- [ ] Spacing on 8pt grid
- [ ] Border-radius ≤ 8px
- [ ] No decorative elements
- [ ] Contrast ≥ 4.5:1 (WCAG AA)
- [ ] Touch targets ≥ 44px

## References

- `@DESIGN_SYSTEM.md` — Complete specification
- `@references/component-specs.md` — CSS for all components
- `@references/dark-mode.md` — Dark mode implementation
- `@references/anti-patterns.md` — Detailed violations guide
