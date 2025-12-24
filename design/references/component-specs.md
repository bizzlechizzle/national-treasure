# Component Specifications

Complete CSS specifications for Braun Design Language components.

**IMPORTANT: All components use Braun Linear font exclusively.**

## Buttons

### Primary Button

```css
.btn-primary {
  /* Layout */
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 44px;
  padding: 10px 20px;

  /* Typography - BRAUN LINEAR ONLY */
  font-family: 'Braun Linear', system-ui, sans-serif;
  font-size: 15px;
  font-weight: 500; /* Medium */
  line-height: 1.4;

  /* Colors - Light */
  background-color: #1C1C1A;
  color: #FFFFFF;
  border: none;

  /* Shape */
  border-radius: 6px;

  /* Interaction */
  cursor: pointer;
  transition: background-color 150ms ease;
}

.btn-primary:hover {
  background-color: #333330;
}

.btn-primary:active {
  background-color: #1C1C1A;
}

.btn-primary:disabled {
  background-color: #E2E1DE;
  color: #8A8A86;
  cursor: not-allowed;
}

.btn-primary:focus-visible {
  outline: 2px solid #f59e0b;
  outline-offset: 2px;
}

/* Dark mode */
[data-theme="dark"] .btn-primary,
@media (prefers-color-scheme: dark) {
  .btn-primary {
    background-color: #FAFAF8;
    color: #0a0a0b;
  }

  .btn-primary:hover {
    background-color: #E8E8E6;
  }
}
```

### Secondary Button

```css
.btn-secondary {
  /* Layout */
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 44px;
  padding: 9px 19px; /* -1px for border */

  /* Typography */
  font-family: var(--font-sans);
  font-size: 15px;
  font-weight: 500;
  line-height: 1.4;

  /* Colors - Light */
  background-color: transparent;
  color: #1C1C1A;
  border: 1px solid #C0BFBC;

  /* Shape */
  border-radius: 6px;

  /* Interaction */
  cursor: pointer;
  transition: border-color 150ms ease;
}

.btn-secondary:hover {
  border-color: #8A8A86;
}

.btn-secondary:disabled {
  border-color: #EEEEED;
  color: #C0BFBC;
  cursor: not-allowed;
}

/* Dark mode */
[data-theme="dark"] .btn-secondary {
  border-color: #3A3A3E;
  color: rgba(250, 250, 248, 0.87);
}

[data-theme="dark"] .btn-secondary:hover {
  border-color: #5A5A5E;
}
```

### Ghost Button

```css
.btn-ghost {
  /* Layout */
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 44px;
  padding: 10px 20px;

  /* Typography */
  font-family: var(--font-sans);
  font-size: 15px;
  font-weight: 500;

  /* Colors */
  background-color: transparent;
  color: #5C5C58;
  border: none;

  /* Interaction */
  cursor: pointer;
  transition: color 150ms ease;
}

.btn-ghost:hover {
  color: #1C1C1A;
}

/* Dark mode */
[data-theme="dark"] .btn-ghost {
  color: rgba(250, 250, 248, 0.60);
}

[data-theme="dark"] .btn-ghost:hover {
  color: rgba(250, 250, 248, 0.87);
}
```

### Accent Button (Optional)

```css
.btn-accent {
  background-color: #f59e0b;
  color: #1C1C1A;
  border: none;
  /* Other properties same as primary */
}

.btn-accent:hover {
  background-color: #d97706;
}
```

### Button Sizes

| Size | Height | Padding | Font Size |
|------|--------|---------|-----------|
| Small | 32px | 6px 12px | 13px |
| Medium | 44px | 10px 20px | 15px |
| Large | 52px | 14px 28px | 17px |

---

## Inputs

### Text Input

```css
.input {
  /* Layout */
  width: 100%;
  min-height: 44px;
  padding: 10px 12px;

  /* Typography */
  font-family: var(--font-sans);
  font-size: 15px;
  font-weight: 400;
  line-height: 1.4;

  /* Colors - Light */
  background-color: #FFFFFF;
  color: #1C1C1A;
  border: 1px solid #C0BFBC;

  /* Shape */
  border-radius: 6px;

  /* Interaction */
  transition: border-color 150ms ease;
}

.input::placeholder {
  color: #C0BFBC;
}

.input:hover {
  border-color: #8A8A86;
}

.input:focus {
  outline: none;
  border-color: #f59e0b;
}

.input:disabled {
  background-color: #F4F4F2;
  color: #8A8A86;
  cursor: not-allowed;
}

.input.error {
  border-color: #ef4444;
}

/* Dark mode */
[data-theme="dark"] .input {
  background-color: #111113;
  color: rgba(250, 250, 248, 0.87);
  border-color: #3A3A3E;
}

[data-theme="dark"] .input::placeholder {
  color: rgba(250, 250, 248, 0.38);
}

[data-theme="dark"] .input:focus {
  border-color: #fbbf24;
}
```

### Input Label

```css
.input-label {
  display: block;
  margin-bottom: 8px;

  /* Typography */
  font-family: var(--font-sans);
  font-size: 11px;
  font-weight: 600;
  line-height: 1.3;
  letter-spacing: 0.1em;
  text-transform: uppercase;

  /* Colors */
  color: #5C5C58;
}

[data-theme="dark"] .input-label {
  color: rgba(250, 250, 248, 0.60);
}
```

### Helper Text

```css
.input-helper {
  margin-top: 4px;
  font-size: 13px;
  color: #8A8A86;
}

.input-helper.error {
  color: #ef4444;
}
```

---

## Cards

### Base Card

```css
.card {
  /* Layout */
  display: flex;
  flex-direction: column;

  /* Colors - Light */
  background-color: #FFFFFF;
  border: 1px solid #E2E1DE;

  /* Shape */
  border-radius: 8px;
  overflow: hidden;

  /* Interaction */
  transition: border-color 150ms ease;
}

.card:hover {
  border-color: #C0BFBC;
}

/* Dark mode */
[data-theme="dark"] .card {
  background-color: #1A1A1C;
  border-color: #1f1f23;
}

[data-theme="dark"] .card:hover {
  border-color: #2D2D30;
}
```

### Card Variants

```css
.card-sm { padding: 12px; }
.card-md { padding: 16px; }
.card-lg { padding: 24px; }
```

### Card with Image

```css
.card-image {
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  background-color: #F4F4F2;
}

.card-content {
  padding: 16px;
}

.card-title {
  font-size: 17px;
  font-weight: 600;
  color: #1C1C1A;
  margin-bottom: 4px;
}

.card-meta {
  font-size: 13px;
  color: #8A8A86;
}

[data-theme="dark"] .card-image {
  background-color: #252527;
}

[data-theme="dark"] .card-title {
  color: rgba(250, 250, 248, 0.87);
}
```

---

## Navigation

### Sidebar

```css
.sidebar {
  width: 240px;
  padding: 24px 16px;
  background-color: #FAFAF8;
  border-right: 1px solid #E2E1DE;
}

.sidebar-brand {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
  line-height: 1.3;
  color: #1C1C1A;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #E2E1DE;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sidebar-nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;

  font-size: 15px;
  font-weight: 500;
  text-decoration: none;
  color: #5C5C58;

  border-radius: 6px;
  transition: background-color 150ms ease, color 150ms ease;
}

.sidebar-nav-item:hover {
  background-color: rgba(0, 0, 0, 0.03);
  color: #1C1C1A;
}

.sidebar-nav-item.active {
  background-color: rgba(0, 0, 0, 0.05);
  color: #1C1C1A;
}

/* Dark mode */
[data-theme="dark"] .sidebar {
  background-color: #0a0a0b;
  border-color: #1f1f23;
}

[data-theme="dark"] .sidebar-brand {
  color: rgba(250, 250, 248, 0.87);
  border-color: #1f1f23;
}

[data-theme="dark"] .sidebar-nav-item {
  color: rgba(250, 250, 248, 0.60);
}

[data-theme="dark"] .sidebar-nav-item:hover {
  background-color: rgba(255, 255, 255, 0.05);
  color: rgba(250, 250, 248, 0.87);
}

[data-theme="dark"] .sidebar-nav-item.active {
  background-color: rgba(255, 255, 255, 0.08);
  color: rgba(250, 250, 248, 0.87);
}
```

---

## Icons

### Sizes

| Size | Dimensions | Stroke Width |
|------|------------|--------------|
| Small | 16×16 | 1.5px |
| Medium | 20×20 | 2px |
| Large | 24×24 | 2px |
| XL | 32×32 | 2.5px |

### Base Style

```css
.icon {
  display: inline-block;
  width: 20px;
  height: 20px;
  stroke: currentColor;
  stroke-width: 2;
  fill: none;
  flex-shrink: 0;
}

.icon-sm { width: 16px; height: 16px; stroke-width: 1.5; }
.icon-lg { width: 24px; height: 24px; }
.icon-xl { width: 32px; height: 32px; stroke-width: 2.5; }
```

---

## Badges & Tags

```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;

  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;

  background-color: #F4F4F2;
  color: #5C5C58;
  border-radius: 4px;
}

.badge-success { background-color: #dcfce7; color: #166534; }
.badge-warning { background-color: #fef3c7; color: #92400e; }
.badge-error { background-color: #fee2e2; color: #991b1b; }
.badge-info { background-color: #dbeafe; color: #1e40af; }

/* Dark mode adjusts backgrounds */
[data-theme="dark"] .badge {
  background-color: #252527;
  color: rgba(250, 250, 248, 0.60);
}
```

---

## Empty States

```css
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 48px 24px;
}

.empty-state-icon {
  width: 48px;
  height: 48px;
  color: #C0BFBC;
  margin-bottom: 16px;
}

.empty-state-title {
  font-size: 17px;
  font-weight: 600;
  color: #1C1C1A;
  margin-bottom: 8px;
}

.empty-state-description {
  font-size: 15px;
  color: #5C5C58;
  max-width: 320px;
  margin-bottom: 24px;
}

/* No illustrations. No decorative elements. */
```

---

## Loading States

### Principles

- **< 300ms:** No indicator
- **300ms - 2s:** Simple text "Loading..."
- **> 2s:** Static progress bar (no animation)

```css
.loading-placeholder {
  background-color: #F4F4F2;
  border-radius: 4px;
  /* NO shimmer animation */
}

.loading-text {
  font-size: 13px;
  color: #8A8A86;
}

[data-theme="dark"] .loading-placeholder {
  background-color: #252527;
}
```
