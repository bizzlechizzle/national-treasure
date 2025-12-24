---
name: sme
description: Generate comprehensive, research-backed Subject Matter Expert (SME) documents on any topic. Triggers when user requests an "SME document", "expert report", "research document", "comprehensive guide", "knowledge base article", or asks for a well-researched document with citations and verification. Accepts user-provided documents as source material, performs web research, cross-references claims, audits for accuracy, and produces structured output with executive summary/TLDR, cited sources, and confidence indicators. Supports markdown, docx, HTML, and PDF output.
---

# SME Document Generator v0.1.0

Create authoritative, well-researched documents that synthesize user-provided materials with web research into a single comprehensive reference.

## Workflow Overview

1. **Topic Intake** - Understand scope, audience, constraints, and document type
2. **Source Inventory** - Catalog user docs, establish source hierarchy
3. **Research Execution** - Systematic web research with query strategy
4. **Synthesis & Drafting** - Build document with inline citations
5. **Conflict Resolution** - Reconcile contradictions across sources
6. **Verification Pass** - Audit claims, flag uncertainties
7. **Output & Iteration** - Produce final document, support refinement

---

## Step 1: Topic Intake

Gather requirements before any research. Ask:

| Question | Why It Matters |
|----------|----------------|
| **Topic** | Core subject to cover |
| **Scope** | Depth level (see table below) |
| **Audience** | Technical depth, assumed knowledge |
| **Purpose** | Decision support? Training? Reference? |
| **Source constraints** | Prioritize/exclude specific sources? |
| **Recency requirements** | How current must information be? |
| **Output format** | Markdown, docx, HTML, PDF? |
| **Visuals needed?** | Diagrams, charts, screenshots? |

### Scope Levels

| Level | Description | Word Count | Sources | Research Time |
|-------|-------------|------------|---------|---------------|
| **Brief** | Quick reference, single question | 500-1,000 | 3-5 | Light |
| **Standard** | Balanced coverage, most use cases | 1,500-3,000 | 8-12 | Moderate |
| **Comprehensive** | Deep dive, authoritative reference | 4,000-8,000 | 15-25 | Heavy |
| **Exhaustive** | Definitive resource, all angles | 10,000+ | 25+ | Extensive |

Default to **Standard** if user doesn't specify.

---

## Step 2: Source Inventory

Before web research, catalog all inputs and establish hierarchy.

### User-Provided Document Processing

For each uploaded document:

1. **Extract content** using appropriate tools (view, pandoc, etc.)
2. **Classify document type**:
   - `INTERNAL` - Proprietary data, internal docs (highest authority for internal facts)
   - `PRIMARY` - Official specs, contracts, regulatory text
   - `SECONDARY` - Reports, analysis, journalism
   - `TERTIARY` - Summaries, Wikipedia, general reference
3. **Extract claims** - List specific facts, figures, assertions
4. **Note gaps** - What questions remain unanswered?
5. **Flag contradictions** - Any internal inconsistencies?

### Source Hierarchy (Authority Order)

When sources conflict, defer to higher-ranked source unless clear error:

1. **User INTERNAL docs** - Treated as ground truth for internal/proprietary info
2. **Official primary sources** - Specs, regulatory text, company announcements
3. **Peer-reviewed/academic** - Published research with methodology
4. **Authoritative secondary** - Major news orgs, industry analysts
5. **General secondary** - Blogs, smaller publications
6. **Tertiary/aggregated** - Wikipedia, forums (verify independently)

Document the source inventory before proceeding:

```
## Source Inventory
### User-Provided (X documents)
- [filename]: [type], [key claims extracted], [gaps noted]

### Research Needed
- [list of questions/gaps to fill via web research]
```

---

## Step 3: Research Execution

Systematic research process. Do not skip steps.

### Query Construction Strategy

**Start broad, then narrow:**

1. **Orienting query**: `[topic]` - Get landscape, identify terminology
2. **Definition query**: `[topic] definition explained` - Ensure shared understanding  
3. **Subtopic queries**: Break topic into components, search each
4. **Specific fact queries**: `[specific claim] statistics 2024` - Verify numbers
5. **Contrary query**: `[topic] criticism problems limitations` - Find counterarguments
6. **Recent query**: `[topic] 2024` or `[topic] latest` - Get current state

**Query construction rules:**
- 1-6 words per query
- No operators unless specifically needed
- Include year for time-sensitive topics
- Use terminology discovered in earlier searches

### Research Execution Checklist

For each major claim or section:

- [ ] At least 2 independent sources (not citing each other)
- [ ] At least 1 primary source where possible
- [ ] Checked publication date
- [ ] Noted source type in tracking

### Source Tracking Format

Maintain running log during research:

```
[1] URL | Date | Type | Key facts | Notes
[2] URL | Date | Type | Key facts | Notes
```

### When to Stop Researching

- Key questions answered with 2+ sources
- Diminishing returns (new searches repeat same info)
- Source count appropriate for scope level
- Contrary/limitation perspectives found

---

## Step 4: Synthesis & Drafting

### Document Structure (Required Sections)

```markdown
# [Document Title]

> **Generated**: [YYYY-MM-DD]  
> **Sources current as of**: [Date of most recent source]  
> **Scope**: [Brief/Standard/Comprehensive/Exhaustive]  
> **Version**: 1.0

---

## Executive Summary / TLDR

[2-4 paragraphs max. Key findings, main conclusions, critical caveats.
Reader should get 80% of value from this section alone.
Write this LAST after all other sections complete.]

---

## Background & Context

[Why this topic matters. Historical context if relevant.
Define key terms for target audience. 1-3 paragraphs.]

---

## [Core Section 1: Descriptive Title]

[Main content. Each major claim includes inline citation.
Confidence markers on disputed/uncertain claims.]

## [Core Section 2: Descriptive Title]

[Continue as needed. Number of sections scales with scope level.]

---

## Analysis & Implications

[Synthesis across sources. Patterns. Supported conclusions.
What this means for the reader's context.]

---

## Limitations & Uncertainties

[REQUIRED. Never omit this section.]

### What This Document Does NOT Cover
[Explicit scope boundaries]

### Unverified Claims
[Claims with single source or low confidence]

### Source Conflicts
[Where sources disagreed, how resolved]

### Knowledge Gaps
[Questions that couldn't be answered]

### Recency Limitations
[What may have changed since sources published]

---

## Recommendations

[If applicable. Actionable takeaways. Numbered list.
Each recommendation tied to findings above.]

---

## Source Appendix

[Numbered list. All sources. Full URLs. Access dates.]

| # | Source | Date | Type | Used For |
|---|--------|------|------|----------|
| 1 | [URL] | YYYY-MM-DD | Primary | [What claims it supports] |
| 2 | [URL] | YYYY-MM-DD | Secondary | [What claims it supports] |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | [Date] | Initial version |
```

### Citation Style

Inline numbered citations: `[1]`, `[2]`, `[1][3]` for multiple.

### Confidence Markers

Apply to claims, not sources:

| Marker | Meaning | When to Use |
|--------|---------|-------------|
| `[HIGH]` | High confidence | 2+ authoritative sources agree, no contradictions |
| `[MEDIUM]` | Moderate confidence | Single authoritative source OR multiple secondary |
| `[LOW]` | Low confidence | Limited sourcing, conflicts, or rapidly changing |
| `[UNVERIFIED]` | Could not verify | Single non-authoritative source, user-provided only |

**Usage**: "The market grew 15% in 2024 [1][HIGH], though regional variations were significant [2][MEDIUM]."

---

## Step 5: Conflict Resolution

When sources contradict, follow this process:

### 1. Identify Conflict Type

| Type | Example | Resolution |
|------|---------|------------|
| **Factual** | Source A says 15%, Source B says 20% | Check primary source, note discrepancy |
| **Interpretive** | Source A says positive trend, B says negative | Present both with attribution |
| **Temporal** | Source A outdated, B current | Prefer recent, note change |
| **Scope** | Sources discussing different subsets | Clarify what each covers |

### 2. Resolution Process

1. Check if sources are discussing same thing (scope conflict)
2. Check publication dates (temporal conflict)
3. Check source authority level (defer to higher)
4. If true conflict remains: present both positions explicitly

### 3. Document Resolution

In Limitations section, note:
- What conflicted
- How resolved
- Remaining uncertainty

---

## Step 6: Verification Pass

Complete ALL checks before finalizing.

### Factual Audit
- [ ] Every statistic has citation
- [ ] Dates and figures cross-checked against primary source where possible
- [ ] No orphan claims (assertions without any source)
- [ ] Numbers are plausible (sanity check)

### Source Quality Audit
- [ ] Primary sources used where available
- [ ] No section relies on single source (except proprietary data)
- [ ] Source recency appropriate for topic
- [ ] No circular sourcing (A cites B cites A)

### Consistency Audit
- [ ] TLDR accurately reflects document content
- [ ] No contradictions between sections
- [ ] Confidence markers consistent with sourcing
- [ ] Scope claims match actual coverage

### Completeness Audit
- [ ] All intake questions addressed
- [ ] User-provided doc content incorporated
- [ ] Limitations section complete
- [ ] Source appendix has all citations

### Structural Audit
- [ ] Document metadata present (date, version, scope)
- [ ] All required sections present
- [ ] Logical flow between sections
- [ ] Appropriate length for scope level

---

## Step 7: Output & Iteration

### Output Location

**All SME documents MUST be saved to the `sme/` folder** in the project root:

1. **Create folder if needed**: If `sme/` doesn't exist, create it
2. **Save all outputs there**: Main document, research notes, any supporting files
3. **Keeps repos organized**: SME docs won't clutter root or mix with source code

```
project/
├── sme/                          # All SME documents go here
│   ├── kubernetes-security.md    # Main document
│   ├── api-design-patterns.md    # Another document
│   └── ...
├── src/
└── ...
```

### File Naming Convention

Use **clean, descriptive, kebab-case filenames**:

| Rule | Example |
|------|---------|
| Lowercase | `kubernetes-security.md` not `Kubernetes-Security.md` |
| Kebab-case | `api-design-patterns.md` not `api_design_patterns.md` |
| Descriptive | `react-state-management.md` not `sme-doc-1.md` |
| No dates in name | Use document metadata for dates, not filename |
| Topic-focused | `oauth2-implementation.md` not `security-research-oauth.md` |

**Naming formula**: `[primary-topic][-subtopic].md`

Examples:
- `kubernetes-networking.md`
- `graphql-best-practices.md`
- `python-async-patterns.md`
- `aws-lambda-cold-starts.md`

### Output Formats

| Format | Tool/Method | Use Case |
|--------|-------------|----------|
| **Markdown** | Direct output | Default, maximum portability, version control friendly |
| **DOCX** | Use docx skill | Formal distribution, editing by others |
| **HTML** | Wrap in HTML template | Web publishing, intranet |
| **PDF** | Convert from docx/HTML via soffice | Final distribution, printing |

### Final Deliverables

1. **Main document** in requested format
2. **Research summary** (brief): Sources consulted, search strategy, total sources by type
3. **Offer iteration options** (see below)

### Iteration Support

After initial delivery, support these refinement modes:

| Request | Action |
|---------|--------|
| "Go deeper on [section]" | Expand that section with additional research, bump scope level for that section |
| "Add section on [topic]" | Research and add new section, update TLDR |
| "Update sources" | Re-run research queries, update stale sources, note changes |
| "Convert to [format]" | Reformat using appropriate tool |
| "Simplify for [audience]" | Reduce jargon, add definitions, shorten |
| "Add visuals" | See visual guidelines below |

When iterating:
- Increment version number
- Add entry to Document History
- Update "Generated" date
- Preserve all citations

---

## Visual Content Guidelines

### When to Include Visuals

| Content Type | Visual Approach |
|--------------|-----------------|
| Process/workflow | Flowchart or numbered diagram |
| Comparison | Table (preferred) or comparison chart |
| Hierarchy/taxonomy | Tree diagram |
| Timeline | Horizontal timeline |
| Architecture | Block diagram |
| Data trends | Simple line/bar chart |

### Visual Creation

1. **Prefer tables** - Render in all formats, no tooling needed
2. **Mermaid diagrams** - For flowcharts, sequences, hierarchies (renders in markdown)
3. **ASCII diagrams** - For simple visuals that must work everywhere
4. **Describe for creation** - If complex visual needed, describe in detail for user to create or use image generation

### Visual Standards

- Every visual has caption explaining what it shows
- Reference visuals in body text
- Keep visuals simple - one concept each
- Tables preferred over diagrams when data is tabular

---

## Quality Standards

### What Makes a Good SME Document

| Quality | Indicator |
|---------|-----------|
| **Authoritative** | Primary sources, official docs, peer-reviewed research |
| **Verifiable** | Every claim cited, reader can trace to source |
| **Honest** | Uncertainty acknowledged, limitations explicit |
| **Scoped** | Covers what it claims, notes what's excluded |
| **Current** | Sources dated, recency appropriate to topic |
| **Actionable** | Reader knows what to do with information |

### Red Flags (Never Do These)

- Weasel words without attribution ("experts say", "studies show")
- Outdated information presented as current
- Single-source sections for contested topics
- Missing context that changes interpretation
- Overconfident tone on uncertain topics
- Omitting Limitations section
- Claiming completeness without exhaustive research

---

## Auditability Requirements

SME documents should be structured for verification by the `audit` skill. **Trust but verify** - every claim should trace to a cited source that exists.

### Citation Integrity Standards

| Requirement | Implementation |
|-------------|----------------|
| **Every factual claim has citation** | No orphan assertions |
| **URLs must be full and resolvable** | `https://...` not `[link]` |
| **Include access date** | URLs can go stale |
| **Quote key passages** | Enable verification without fetching |

### Structured Claims Format

For high-auditability documents, include a claims appendix:

```yaml
## Claims Appendix

claims:
  - id: C001
    text: "Kubernetes supports up to 5,000 nodes per cluster"
    type: quantitative
    citations: [3]
    confidence: HIGH
    source_quote: "tested configurations with 5,000 nodes"

  - id: C002
    text: "OAuth2 refresh tokens expire after 30 days by default"
    type: factual
    citations: [7]
    confidence: MEDIUM
    source_quote: "default expiration is implementation-dependent"
    note: "varies by provider"
```

### Source Verification Checklist

Before finalizing, verify:

- [ ] All URLs resolve (HTTP 200)
- [ ] Quotes match source content
- [ ] No dead links
- [ ] Archive.org backup for critical sources
- [ ] Primary sources preferred over aggregators

### Audit-Ready Output Flag

Add to document metadata when claims appendix is included:

```markdown
> **Audit-Ready**: Yes
> **Claims Count**: X verifiable assertions
> **Citation Verification**: [Date last verified]
```

---

## Edge Cases

### Topic Too Broad
1. Acknowledge scope concern
2. Propose breakdown: overview + deep dive on one aspect, OR multiple documents
3. Get user confirmation before proceeding

### Insufficient Quality Sources
1. State limitation explicitly upfront
2. Note in Limitations section
3. Suggest alternatives: expert consultation, primary research, waiting for more information
4. Proceed with available sources, mark confidence LOW/UNVERIFIED

### User Docs Contradict Web Research
1. Flag discrepancy to user
2. Ask: Is user doc internal/proprietary (takes precedence) or should web research view prevail?
3. Document resolution in Limitations

### Topic Too New/Fast-Changing
1. State knowledge cutoff explicitly in document metadata
2. Mark relevant claims as potentially outdated
3. Recommend verification before acting
4. Offer to re-research specific aspects on request

### Controversial/Political Topics
1. Present multiple perspectives with attribution
2. Note where consensus exists vs. where contested
3. Avoid taking positions; present what sources say
4. Extra emphasis on source quality and balance
