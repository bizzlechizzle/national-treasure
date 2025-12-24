# Universal Development Standards v0.1.3

Consistent, maintainable code across all projects.

> **This file is centrally managed.** Do not modify without explicit user approval.

## Instruction Files

| File | Location | Purpose |
|------|----------|---------|
| `CLAUDE.md` | Root | Universal rules (this file) |
| `techguide.md` | Root | Project-specific details (import via `@techguide.md`) |
| `.claude/rules/*.md` | .claude/rules/ | Modular, path-scoped rules |

Files load in order. Missing files are skipped.

## Boot Sequence

1. Read this file completely
2. Read `@techguide.md` if it exists
3. Read the task
4. Begin implementation

## Commands & Gotchas

Define in `@techguide.md`. Every project must document:
- Build, test, lint, and run commands
- Critical gotchas (non-obvious failures, environment quirks)
- Troubleshooting steps for common issues

Use hooks (settings.json) for formatting/linting—not CLAUDE.md.

## Development Rules

1. **Scope Discipline** — Only implement what the request describes
2. **Verify Before Done** — Run build and tests; incomplete until passing
3. **Keep It Simple** — Favor obvious code, minimal abstraction, fewer files
4. **One Script = One Purpose** — Keep scripts focused (~300 lines guideline)
5. **Open Source First** — Prefer open tools unless project specifies otherwise
6. **Binaries Welcome** — Use ffmpeg, exiftool, etc. when appropriate for the environment
7. **Respect Folder Structure** — Place files in designated directories (templates in `templates/`, scripts in `scripts/`, etc.)
8. **Build Complete** — No "V2" or deferred features. Plan thoroughly, build once. ("Buy once, cry once")

## Security

- Validate all external input at system boundaries (APIs, CLI, file reads)
- Never log secrets, credentials, or PII
- Use parameterized queries for databases
- Escape output to prevent injection (XSS, SQL, command)

## Do Not

- Invent features beyond what the task authorizes
- Hardcode paths, credentials, or environment-specific values
- Leave TODOs or unexplained code in production
- **Assume when uncertain** — Stop and ask
- **Modify CLAUDE.md** — This file is managed centrally; changes require explicit approval

## Stop and Ask When

- Task conflicts with a rule in this file
- Referenced file or path doesn't exist
- Task scope is unclear or spans multiple features
- About to delete code without understanding why it exists
- Schema, API, or breaking change not explicitly authorized

## Code Quality

### Prefer
- Explicit over implicit
- Pure functions where possible
- Descriptive names over comments
- Early returns over deep nesting

### Avoid
- Magic numbers and strings
- Global mutable state
- Premature abstraction

## Testing

- Write tests for new functionality
- Run affected tests (files touched or related) before marking complete
- Test edge cases and error paths

## Git

- Atomic commits (one logical change)
- Messages explain what and why
- Never force push to main/master
- Never commit secrets or .env files

## Versioning

### repo-depot version
- Format: `0.MINOR.COMMIT_COUNT` (e.g., `0.1.34`)
- Calculated automatically from `VERSION` file + git commit count
- Bump `VERSION` to `0.2` for breaking changes to sync behavior
- Bump to `1.0` when declared stable

### App versions
- Format: `MAJOR.MINOR.PATCH` (e.g., `1.0.12`)
- Each commit that modifies app code **must** increment PATCH by exactly 1
- **Claude may ONLY increment PATCH** — never change MAJOR or MINOR
- MINOR/MAJOR bumps require explicit user instruction (e.g., "bump to 0.2.0")
- **Do not** use git commit counts—version is manually incremented per commit
- Do not bump version for repo-depot syncs that don't change app logic
- Apps receive `.depot-version` file indicating synced repo-depot version

**Initialization:**
- New apps start at `0.1.0` (pre-release) or `1.0.0` (stable launch)
- Create `VERSION` file in app's root directory containing version as plain text
- Example: `echo "0.1.0" > VERSION`

**Tracking:**
- `VERSION` file lives in app's root directory (e.g., `apps/myapp/VERSION`)
- File contains only the version string, no other content (e.g., `1.0.12`)
- Read version: `cat VERSION`
- **Include VERSION bump in the same commit** as your code changes

**What triggers a version bump:**
- Source code changes → Yes, always
- Config changes that affect behavior → Yes
- Test-only or docs-only changes → No
- Merge commits → Count as 1 commit (bump once, not per merged commit)

## Path-Scoped Rules

Rules in `.claude/rules/` can target specific paths:

```yaml
---
paths: src/api/**/*.ts
---
# Rules here apply only to matching files
```

Common globs: `**/*.ts` (all), `src/**/*` (directory), `*.md` (root only)
