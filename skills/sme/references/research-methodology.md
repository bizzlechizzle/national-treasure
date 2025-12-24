# Research Methodology Reference

Detailed guidance for systematic research execution.

---

## Query Construction Patterns

### By Topic Type

| Topic Type | Query Pattern | Example |
|------------|---------------|---------|
| **Technology** | `[tech] vs [alternative]`, `[tech] best practices 2024`, `[tech] limitations` | "kubernetes vs docker swarm", "kubernetes security best practices 2024" |
| **Market/Business** | `[market] market size`, `[market] growth forecast`, `[company] revenue` | "cloud storage market size 2024", "AWS revenue growth" |
| **Regulatory** | `[regulation] requirements`, `[regulation] compliance guide`, `[regulation] enforcement` | "GDPR requirements", "CCPA compliance guide" |
| **Scientific** | `[topic] research`, `[topic] meta-analysis`, `[topic] systematic review` | "intermittent fasting research", "sleep deprivation meta-analysis" |
| **How-to** | `[task] tutorial`, `[task] step by step`, `[task] troubleshooting` | "nginx reverse proxy tutorial", "SSL certificate troubleshooting" |

### Query Sequencing Strategy

**Phase 1: Orientation (1-2 queries)**
```
[topic]
[topic] overview
```
Purpose: Understand landscape, discover terminology, identify subtopics.

**Phase 2: Definition & Scope (1-2 queries)**
```
[topic] definition
[topic] vs [related concept]
```
Purpose: Ensure precise understanding, clarify boundaries.

**Phase 3: Core Research (3-8 queries)**
```
[subtopic 1] [specifics]
[subtopic 2] [specifics]
[topic] statistics data
[topic] case study
```
Purpose: Gather substantive content for each section.

**Phase 4: Verification (2-3 queries)**
```
[specific claim] source
[statistic] original study
```
Purpose: Trace claims to primary sources.

**Phase 5: Contrary Evidence (1-2 queries)**
```
[topic] criticism
[topic] problems limitations
[topic] failed
```
Purpose: Find counterarguments, limitations, failures.

**Phase 6: Recency (1-2 queries)**
```
[topic] 2024
[topic] latest news
[topic] recent developments
```
Purpose: Ensure current information, catch recent changes.

---

## Source Evaluation Criteria

### Authority Indicators

| Indicator | High Authority | Low Authority |
|-----------|---------------|---------------|
| **Domain** | .gov, .edu, major .org | Unknown domains, URL shorteners |
| **Author** | Named experts, institutional affiliation | Anonymous, no credentials |
| **Publication** | Peer-reviewed, major outlets | Self-published, content farms |
| **Citations** | Cites primary sources | No citations, circular |
| **Date** | Current for topic type | Undated or stale |

### Source Type Classification

| Type | Examples | Authority Level | Best Used For |
|------|----------|-----------------|---------------|
| **Primary** | Original research, official specs, regulatory text, company announcements | Highest | Definitive facts, official positions |
| **Peer-reviewed** | Academic journals, conference proceedings | Very High | Scientific claims, methodology |
| **Institutional** | Government reports, think tank research, industry associations | High | Statistics, policy, standards |
| **Major news** | Reuters, AP, WSJ, NYT, domain-specific trade press | Medium-High | Current events, verified reporting |
| **Corporate** | Company blogs, press releases | Medium | Company-specific info (with skepticism) |
| **Expert blogs** | Known practitioners with track record | Medium | Practical insights, opinions |
| **General secondary** | Smaller publications, aggregators | Low-Medium | Background, leads to primary |
| **User-generated** | Stack Overflow, Reddit, forums | Low | Troubleshooting, common issues |
| **Tertiary** | Wikipedia, general encyclopedias | Reference Only | Orientation, finding primary sources |

### Red Flags

Downgrade or exclude sources with:

- No author attribution
- No publication date
- Obvious SEO optimization (keyword stuffing, thin content)
- Affiliate links dominating content
- Claims without any citations
- Conflicts of interest not disclosed
- Outdated information presented as current
- Factual errors on verifiable claims
- Sensationalist headlines contradicted by content

---

## Cross-Reference Requirements

### Minimum Sourcing by Claim Type

| Claim Type | Minimum Sources | Source Quality |
|------------|-----------------|----------------|
| Central thesis | 3+ | At least 1 primary |
| Statistics/numbers | 2+ | Primary preferred |
| Consensus claims | 2+ | Independent sources |
| Controversial claims | 3+ | Multiple perspectives |
| Definitions | 1 | Authoritative |
| Historical facts | 1-2 | Established sources |
| Quotes | 1 | Original source required |

### Independence Check

Sources are NOT independent if:
- One cites the other
- Both cite same original source (find the original)
- Same author/organization
- Same press release origin
- Same dataset

---

## Conflict Detection & Resolution

### Detection Methods

1. **Direct contradiction**: Source A says X, Source B says not-X
2. **Numeric discrepancy**: Different figures for same metric
3. **Temporal conflict**: Sources from different time periods
4. **Scope confusion**: Sources discussing different subsets
5. **Interpretation divergence**: Same facts, different conclusions

### Resolution Decision Tree

```
Conflict detected
    │
    ├─► Same time period?
    │   ├─► No → Prefer more recent, note change
    │   └─► Yes ↓
    │
    ├─► Same scope/definition?
    │   ├─► No → Clarify what each covers, may not be conflict
    │   └─► Yes ↓
    │
    ├─► One source primary, other secondary?
    │   ├─► Yes → Prefer primary, note discrepancy
    │   └─► No ↓
    │
    ├─► Clear methodology difference?
    │   ├─► Yes → Note methodology, explain difference
    │   └─► No ↓
    │
    └─► True conflict → Present both with attribution
                       Document in Limitations section
                       Apply [LOW] or [UNVERIFIED] confidence
```

### Documentation Format

In Limitations section:

```markdown
### Source Conflicts

**[Topic of conflict]**
- Source [1] states: [claim]
- Source [2] states: [contradicting claim]
- Resolution: [How handled / why one preferred / both presented]
- Remaining uncertainty: [What's still unclear]
```

---

## Research Stopping Criteria

Stop researching when:

### Sufficient Condition (all must be true)
- [ ] All key questions from intake have answers
- [ ] Source count meets scope level target
- [ ] At least one primary source for critical claims
- [ ] Contrary perspectives found and documented
- [ ] Recent sources included for time-sensitive topics

### Diminishing Returns Indicators
- New queries returning same sources
- New sources repeating same information
- Unable to find higher-quality sources
- Time investment exceeding value

### Never Stop If
- Central claim has only single source
- No primary sources for statistics
- No contrary/limitation perspective found
- Key intake question unanswered

---

## Research Log Template

Maintain during research:

```markdown
## Research Log: [Topic]

### Queries Executed
| # | Query | Results | Notes |
|---|-------|---------|-------|
| 1 | [query] | [# useful] | [what found] |
| 2 | [query] | [# useful] | [what found] |

### Sources Collected
| # | URL | Type | Key Content | Quality | Used |
|---|-----|------|-------------|---------|------|
| 1 | [url] | [type] | [summary] | [H/M/L] | [Y/N] |

### Gaps Remaining
- [ ] [Unanswered question]
- [ ] [Missing perspective]

### Conflicts Found
- [Description of conflict, sources involved]

### Research Quality Self-Check
- [ ] Primary sources for key claims
- [ ] Multiple independent sources for central thesis
- [ ] Contrary evidence searched
- [ ] Recency appropriate
- [ ] Source types diverse
```
