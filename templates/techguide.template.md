# Project Technical Guide v0.1.0

> Copy this file to your project root as `techguide.md`.
> CLAUDE.md imports it via `@techguide.md`.

## Project Overview

[One paragraph: what this project does and why it exists]

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | [e.g., TypeScript 5.x] |
| Runtime | [e.g., Node 20 LTS] |
| Framework | [e.g., Next.js 14] |
| Database | [e.g., PostgreSQL 16] |
| Testing | [e.g., Vitest + Playwright] |

## Commands

```bash
# Build
npm run build

# Test (all)
npm test

# Test (single file)
npm test -- path/to/file.test.ts

# Lint & format
npm run lint

# Dev server
npm run dev
```

## Directory Structure

```
project/
├── src/           # Source code
│   ├── components/    # UI components
│   ├── lib/           # Shared utilities
│   └── api/           # API routes
├── tests/         # Test files
├── docs/          # Documentation
└── scripts/       # Build/deploy scripts
```

## Critical Gotchas

| Gotcha | Details |
|--------|---------|
| [e.g., ESM only] | [e.g., No CommonJS require() - use import] |
| [e.g., Env required] | [e.g., Copy .env.example to .env before running] |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Build fails | Run `npm clean-install` then rebuild |
| Tests timeout | Check database connection in .env |
| Type errors | Run `npm run typecheck` for details |

## Project-Specific Rules

[Add any rules that apply only to this project, not universally]
