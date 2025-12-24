# Anti-Patterns Quick Reference

For Braun Design Language verification.

## Immediate Rejection

- [ ] Colored accent buttons (except neutral or amber)
- [ ] Gradient overlays on images
- [ ] Decorative shadows or glows
- [ ] Border-radius > 8px (except 50% circles)
- [ ] Animated skeleton loaders
- [ ] Text shadows
- [ ] Multiple font families
- [ ] Non-8pt spacing
- [ ] Pure black `#000000`
- [ ] Pure white `#FFFFFF`

## Color Violations

```css
/* WRONG */
.btn { background: #3B82F6; } /* colored button */
.hero::after { background: linear-gradient(...); }

/* CORRECT */
.btn { background: #1C1C1A; }
.hero { /* no overlay */ }
```

## Shape Violations

```css
/* WRONG */
.card { border-radius: 12px; }
.btn { border-radius: 9999px; }

/* CORRECT */
.card { border-radius: 8px; }
.btn { border-radius: 6px; }
```

## Shadow Violations

```css
/* WRONG */
.card { box-shadow: 0 10px 40px rgba(0,0,0,0.2); }
.btn:hover { box-shadow: 0 0 20px rgba(59,130,246,0.5); }

/* CORRECT - Light */
.card { box-shadow: 0 1px 3px rgba(0,0,0,0.04); }

/* CORRECT - Dark */
.card { box-shadow: none; background: var(--elevation-2); }
```

## Animation Violations

```css
/* WRONG */
.skeleton { animation: shimmer 1.5s infinite; }
.badge { animation: pulse 2s infinite; }

/* CORRECT */
.placeholder { background: var(--color-surface); }
/* No decorative animation */
```

## Verification Questions

1. Is there color? → Must be functional (success/error/warning)
2. Is there a shadow? → Must be elevation only (light mode)
3. Is there animation? → Must be feedback only
4. Is there decoration? → Remove it
5. Is spacing on grid? → Must be 8pt multiple
6. Is radius > 8px? → Reduce it
7. Is font Braun Linear? → If not, fix it immediately
