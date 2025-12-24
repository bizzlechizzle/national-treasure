# repo-depot GUI Dashboard: Design Specification

> **Version**: 1.0
> **Status**: Design Spec (Phase 4)
> **Design System**: Braun Design Language
> **Priority**: CLI-first, GUI-second

---

## Design Philosophy

> **"The GUI should reveal what the CLI does, not replace it."**

This dashboard follows Dieter Rams' principle: *"Weniger, aber besser"* — Less, but better. The interface exists to provide visibility into sync operations, not to add friction. Every element justifies its existence through function.

### Core Principles

1. **Transparency** — Show what `depot` commands would do
2. **Non-blocking** — Never require the GUI for operations
3. **Real data** — Display actual sync state, no placeholders
4. **Terminal parity** — Every GUI action maps to a CLI command

---

## Information Architecture

```
Dashboard
├── Overview (/)
│   ├── Sync Status Summary
│   ├── Recent Activity Feed
│   └── Quick Actions
│
├── Apps (/apps)
│   ├── App List (grid/table toggle)
│   ├── App Detail View
│   └── Add App Modal
│
├── Config (/config)
│   ├── sync-config.yml Editor
│   ├── user-profile.yml Editor
│   └── Profile Management
│
└── History (/history)
    ├── Sync Log (timeline)
    └── Event Detail Modal
```

---

## Layout Structure

### Shell (All Pages)

```
┌─────────────────────────────────────────────────────────────────┐
│ ┌──────────┐                                        ┌─────────┐ │
│ │  DEPOT   │                                        │ [theme] │ │
│ └──────────┘                                        └─────────┘ │
├─────────────────┬───────────────────────────────────────────────┤
│                 │                                               │
│   Overview      │                                               │
│   Apps          │           [PAGE CONTENT]                      │
│   Config        │                                               │
│   History       │                                               │
│                 │                                               │
│                 │                                               │
│                 │                                               │
│                 │                                               │
├─────────────────┴───────────────────────────────────────────────┤
│ > depot sync --dry-run                              [Run] [Copy]│
└─────────────────────────────────────────────────────────────────┘
```

### CSS Layout

```css
.shell {
  display: grid;
  grid-template-rows: 56px 1fr 48px;
  grid-template-columns: 240px 1fr;
  min-height: 100vh;
  background-color: var(--color-canvas);
}

.header {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid var(--color-border);
}

.sidebar {
  grid-row: 2 / 4;
  padding: 24px 16px;
  border-right: 1px solid var(--color-border);
  background-color: var(--color-surface);
}

.main {
  padding: 32px;
  overflow-y: auto;
}

.command-bar {
  grid-column: 2;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 24px;
  background-color: var(--color-surface);
  border-top: 1px solid var(--color-border);
  font-family: 'Braun Linear', monospace;
  font-size: 13px;
  font-weight: 300;
  color: var(--color-text-secondary);
}
```

---

## Page Specifications

### 1. Overview Page

**Purpose**: At-a-glance sync health and quick actions.

```
┌─────────────────────────────────────────────────────────────────┐
│  OVERVIEW                                                       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  SYNC STATUS                                                ││
│  │                                                             ││
│  │  ● All apps synced                    Last sync: 2 min ago ││
│  │                                                             ││
│  │  12 apps enabled  •  0 pending  •  0 conflicts             ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌────────────────────────┐  ┌────────────────────────────────┐│
│  │  QUICK ACTIONS         │  │  RECENT ACTIVITY               ││
│  │                        │  │                                ││
│  │  [Sync All]            │  │  11:42  my-app         synced  ││
│  │  [Pull from GitHub]    │  │  11:40  my-api         synced  ││
│  │  [Add App]             │  │  11:38  linux-backup   synced  ││
│  │                        │  │  11:30  Push to main triggered ││
│  └────────────────────────┘  └────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

#### Components

**Status Card**
```css
.status-card {
  padding: 24px;
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
}

.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 17px;
  font-weight: 500;
  color: var(--color-text);
}

.status-indicator::before {
  content: '';
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--success);
}

.status-indicator[data-status="warning"]::before {
  background-color: var(--warning);
}

.status-indicator[data-status="error"]::before {
  background-color: var(--error);
}

.status-meta {
  font-size: 13px;
  font-weight: 300;
  color: var(--color-text-secondary);
}

.status-stats {
  margin-top: 16px;
  font-size: 15px;
  font-weight: 400;
  color: var(--color-text-secondary);
}
```

**Activity Feed**
```css
.activity-feed {
  list-style: none;
  padding: 0;
  margin: 0;
}

.activity-item {
  display: grid;
  grid-template-columns: 48px 1fr auto;
  gap: 8px;
  padding: 12px 0;
  border-bottom: 1px solid var(--color-border);
  font-size: 15px;
}

.activity-time {
  font-weight: 300;
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
}

.activity-app {
  font-weight: 500;
  color: var(--color-text);
}

.activity-status {
  font-weight: 300;
  color: var(--color-text-secondary);
}

.activity-status[data-status="synced"] { color: var(--success); }
.activity-status[data-status="failed"] { color: var(--error); }
.activity-status[data-status="pending"] { color: var(--warning); }
```

---

### 2. Apps Page

**Purpose**: Manage local app clones and sync status.

#### List View (Default)

```
┌─────────────────────────────────────────────────────────────────┐
│  APPS                                              [Add App]    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  APP              PROFILE      STATUS    LAST SYNC          ││
│  │  ─────────────────────────────────────────────────────────  ││
│  │  my-app           frontend     ● synced  2 min ago          ││
│  │  my-api           backend      ● synced  2 min ago          ││
│  │  linux-backup     minimal      ○ pending —                  ││
│  │  nightfoxfilms    frontend     ✕ error   Failed             ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

```css
.apps-table {
  width: 100%;
  border-collapse: collapse;
}

.apps-table th {
  text-align: left;
  padding: 12px 16px;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--color-text-secondary);
  border-bottom: 1px solid var(--color-border);
}

.apps-table td {
  padding: 16px;
  font-size: 15px;
  font-weight: 400;
  color: var(--color-text);
  border-bottom: 1px solid var(--color-border);
}

.apps-table tr:hover {
  background-color: var(--color-surface);
}

.app-name {
  font-weight: 500;
}

.profile-badge {
  display: inline-block;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  background-color: var(--color-surface);
  border-radius: 4px;
}
```

#### App Detail Modal

```
┌─────────────────────────────────────────────────────────────────┐
│  my-app                                                    [×]  │
│  bizzlechizzle/my-app                                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PROFILE                                                        │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  ○ default   ○ frontend   ○ backend   ○ fullstack  ● minimal││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  BRANCH         PIN                                             │
│  [main     ▼]   [latest ▼]                                      │
│                                                                 │
│  EXCLUDED FILES                                                 │
│  [CLAUDE.md] [×]                                                │
│  [+ Add exclusion]                                              │
│                                                                 │
│  CLI EQUIVALENT                                                 │
│  > depot profile my-app minimal                                 │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                    [Disable]   [Sync Now]       │
└─────────────────────────────────────────────────────────────────┘
```

---

### 3. Config Page

**Purpose**: Edit YAML configuration with syntax validation.

```
┌─────────────────────────────────────────────────────────────────┐
│  CONFIG                                              [Save]     │
│                                                                 │
│  ┌──────────────────────┬──────────────────────────────────────┐│
│  │  sync-config.yml     │  user-profile.yml                    ││
│  └──────────────────────┴──────────────────────────────────────┘│
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  1  profiles:                                               ││
│  │  2    default:                                              ││
│  │  3      - CLAUDE.md                                         ││
│  │  4      - design/*                                          ││
│  │  5      - coding/*                                          ││
│  │  6      - templates/*                                       ││
│  │  7      - prompts/*                                         ││
│  │  8      - skills/*                                          ││
│  │  9      - "!**/.DS_Store"                                   ││
│  │ 10      - "!**/node_modules"                                ││
│  │ 11                                                          ││
│  │ 12  repos:                                                  ││
│  │ 13    bizzlechizzle/my-app:                                 ││
│  │ 14      profile: frontend                                   ││
│  │ ...                                                         ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ⚠ Line 14: Unknown profile "fronted" (typo?)                  │
└─────────────────────────────────────────────────────────────────┘
```

```css
.config-editor {
  font-family: 'Braun Linear', monospace;
  font-size: 13px;
  font-weight: 300;
  line-height: 1.6;
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
}

.config-line {
  display: flex;
  padding: 0 16px;
}

.config-line:hover {
  background-color: rgba(0, 0, 0, 0.02);
}

.config-line-number {
  width: 40px;
  text-align: right;
  color: var(--color-text-muted);
  user-select: none;
  padding-right: 16px;
  border-right: 1px solid var(--color-border);
  margin-right: 16px;
}

.config-content {
  flex: 1;
  white-space: pre;
}

/* Syntax highlighting - minimal */
.yaml-key { color: var(--color-text); }
.yaml-value { color: var(--color-text-secondary); }
.yaml-string { color: var(--accent-600); }
.yaml-comment { color: var(--color-text-muted); font-style: italic; }

/* Dark mode */
[data-theme="dark"] .config-line:hover {
  background-color: rgba(255, 255, 255, 0.02);
}
```

---

### 4. History Page

**Purpose**: Timeline of sync operations with drill-down.

```
┌─────────────────────────────────────────────────────────────────┐
│  HISTORY                                         [Export CSV]   │
│                                                                 │
│  TODAY                                                          │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  11:42    SYNC COMPLETE                                         │
│           12 apps synced • 0 conflicts • 0 errors               │
│           Source: abc1234 → children                            │
│                                                                 │
│  10:15    SYNC TRIGGERED                                        │
│           Push to main by @bizzlechizzle                        │
│           Commit: "Update CLAUDE.md instructions"               │
│                                                                 │
│  YESTERDAY                                                      │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  16:30    SYNC COMPLETE                                         │
│           12 apps synced • 0 conflicts • 1 error                │
│           my-api: Push rejected (branch protected)              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

```css
.timeline {
  position: relative;
  padding-left: 24px;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 8px;
  top: 0;
  bottom: 0;
  width: 1px;
  background-color: var(--color-border);
}

.timeline-date {
  margin: 32px 0 16px -24px;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--color-text-secondary);
}

.timeline-item {
  position: relative;
  padding: 16px 0;
  border-bottom: 1px solid var(--color-border);
}

.timeline-item::before {
  content: '';
  position: absolute;
  left: -20px;
  top: 20px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--color-border);
  border: 2px solid var(--color-canvas);
}

.timeline-item[data-status="success"]::before {
  background-color: var(--success);
}

.timeline-item[data-status="error"]::before {
  background-color: var(--error);
}

.timeline-time {
  font-size: 13px;
  font-weight: 300;
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
}

.timeline-title {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text);
  margin: 4px 0;
}

.timeline-detail {
  font-size: 13px;
  font-weight: 300;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.timeline-hash {
  font-family: 'Braun Linear', monospace;
  font-size: 13px;
  font-weight: 300;
  color: var(--color-text-muted);
}
```

---

## Command Bar

The persistent command bar shows the CLI equivalent of any action:

```css
.command-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 24px;
  height: 48px;
  background-color: var(--color-surface);
  border-top: 1px solid var(--color-border);
}

.command-prompt {
  font-family: 'Braun Linear', monospace;
  font-size: 13px;
  font-weight: 300;
  color: var(--color-text-muted);
}

.command-text {
  flex: 1;
  font-family: 'Braun Linear', monospace;
  font-size: 13px;
  font-weight: 400;
  color: var(--color-text);
}

.command-action {
  padding: 6px 12px;
  font-size: 13px;
  font-weight: 500;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  color: var(--color-text-secondary);
  cursor: pointer;
}

.command-action:hover {
  border-color: var(--color-text-secondary);
  color: var(--color-text);
}
```

**Behavior**:
- Updates dynamically based on current view/selection
- "Run" executes the command
- "Copy" copies to clipboard

**Examples**:
| Context | Command |
|---------|---------|
| Overview page | `depot status` |
| App selected | `depot sync my-app` |
| Config changed | `depot config validate` |
| History entry | `depot history --commit abc1234` |

---

## Dark Mode Implementation

```css
:root {
  color-scheme: light dark;

  /* Light mode (default) */
  --color-canvas: #FAFAF8;
  --color-surface: #F4F4F2;
  --color-elevated: #FFFFFF;
  --color-text: #1C1C1A;
  --color-text-secondary: #5C5C58;
  --color-text-muted: #8A8A86;
  --color-border: #E2E1DE;
}

@media (prefers-color-scheme: dark) {
  :root {
    --color-canvas: #0a0a0b;
    --color-surface: #111113;
    --color-elevated: #1A1A1C;
    --color-text: rgba(250, 250, 248, 0.87);
    --color-text-secondary: rgba(250, 250, 248, 0.60);
    --color-text-muted: rgba(250, 250, 248, 0.38);
    --color-border: #1f1f23;
  }
}

/* Manual toggle */
[data-theme="dark"] {
  --color-canvas: #0a0a0b;
  --color-surface: #111113;
  --color-elevated: #1A1A1C;
  --color-text: rgba(250, 250, 248, 0.87);
  --color-text-secondary: rgba(250, 250, 248, 0.60);
  --color-text-muted: rgba(250, 250, 248, 0.38);
  --color-border: #1f1f23;
}
```

---

## Typography Summary

All text uses **Braun Linear** exclusively.

| Element | Size | Weight | Use |
|---------|------|--------|-----|
| Page title | 24px | 700 | "OVERVIEW", "APPS" |
| Section label | 11px | 500 | "SYNC STATUS", "RECENT ACTIVITY" |
| Card title | 17px | 500 | Status text |
| Body text | 15px | 400 | General content |
| Meta/captions | 13px | 300 | Timestamps, details |
| Code/hashes | 13px | 300 | Commands, commit SHAs |

---

## Accessibility Checklist

- [ ] All text meets WCAG AA contrast (4.5:1)
- [ ] Touch targets minimum 44×44px
- [ ] Focus states visible on all interactive elements
- [ ] Respects `prefers-reduced-motion`
- [ ] Respects `prefers-color-scheme`
- [ ] Screen reader labels on all icons
- [ ] Keyboard navigation for all actions

---

## Technology Recommendations

| Aspect | Recommendation | Reason |
|--------|----------------|--------|
| Framework | React or Vue 3 | Component-based, good ecosystem |
| Styling | CSS Variables + modules | Matches design token system |
| State | Zustand or Pinia | Minimal, matches CLI-first philosophy |
| Bundler | Vite | Fast, Docker-friendly |
| Server | Express/Fastify | Proxy to Docker container |

### Docker Integration

The GUI runs as a secondary Docker service:

```yaml
services:
  gui:
    build:
      context: ./gui
    ports:
      - "3000:3000"
    volumes:
      - ./config:/app/config:ro
    environment:
      - DEPOT_API_URL=http://repo-depot:8080
    depends_on:
      - repo-depot
    profiles:
      - gui  # Optional, not started by default
```

Start GUI only when needed: `docker compose --profile gui up`

---

## Implementation Priority

| Phase | Components | Effort |
|-------|------------|--------|
| 1 | Shell + Overview page | Low |
| 2 | Apps list + detail | Medium |
| 3 | History timeline | Low |
| 4 | Config editor | High |

**Note**: Phase 4 (Config editor) is high effort due to YAML parsing and validation. Consider read-only view initially.

---

## Anti-Patterns to Avoid

Per Braun Design Language:

| Never | Why |
|-------|-----|
| Animated loading spinners | Motion informs, doesn't entertain |
| Colored accent buttons | Color = functional status only |
| Rounded corners > 8px | Undermines seriousness |
| Decorative illustrations | Content speaks |
| Toast notifications | Use inline status |
| Modal confirmations | CLI doesn't ask, GUI shouldn't either |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-21 | Initial design specification |
