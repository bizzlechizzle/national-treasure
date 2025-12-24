# SME Document Templates

Adapt these structures based on topic and audience. All templates include required metadata and sections.

---

## Technical Decision Document

For evaluating technology choices, vendor selection, architecture decisions.

```markdown
# [Decision]: [Brief Description]

> **Generated**: YYYY-MM-DD  
> **Sources current as of**: YYYY-MM-DD  
> **Scope**: Standard  
> **Version**: 1.0

---

## TLDR

[2-3 sentences: What decision is recommended, primary rationale, key trade-off accepted.]

---

## Context

[Business need. Current state. Why decision needed now. Constraints (budget, timeline, team). 1-2 paragraphs.]

---

## Options Evaluated

### Option A: [Name]

**Description**: [1-2 sentences]

| Dimension | Assessment |
|-----------|------------|
| Capability fit | [Rating + notes] |
| Cost | [Estimate + breakdown] |
| Implementation effort | [Estimate] |
| Risk level | [Low/Medium/High + why] |
| Vendor/community health | [Assessment] |

**Key sources**: [1][2]

### Option B: [Name]

[Same structure]

### Option C: [Name] (if applicable)

[Same structure]

---

## Comparison Matrix

| Criteria | Weight | Option A | Option B | Option C |
|----------|--------|----------|----------|----------|
| [Criterion 1] | X% | Score | Score | Score |
| [Criterion 2] | X% | Score | Score | Score |
| **Weighted Total** | 100% | **X** | **X** | **X** |

---

## Recommendation

**Recommended**: [Option X]

**Rationale**: [2-3 sentences tying to evaluation criteria]

**Trade-offs accepted**: [What we're giving up, why acceptable]

---

## Implementation Considerations

[Key steps, dependencies, timeline estimate, who owns what]

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| [Risk 1] | L/M/H | L/M/H | [Action] |
| [Risk 2] | L/M/H | L/M/H | [Action] |

---

## Limitations & Uncertainties

### Evaluation Gaps
[What couldn't be fully assessed - e.g., "No hands-on POC conducted"]

### Assumptions
[What this recommendation assumes remains true]

### Validity Window
[How long this analysis remains valid before re-evaluation needed]

---

## Source Appendix

| # | Source | Date | Type | Used For |
|---|--------|------|------|----------|
| 1 | [URL] | Date | [Type] | [Usage] |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Date | Initial version |
```

---

## Market/Industry Analysis

For understanding market landscape, competitive dynamics, trends.

```markdown
# [Industry/Market] Analysis: [Specific Focus]

> **Generated**: YYYY-MM-DD  
> **Sources current as of**: YYYY-MM-DD  
> **Scope**: Comprehensive  
> **Version**: 1.0

---

## TLDR

[Market size and growth. Key trend summary. Major players. Outlook. 2-3 paragraphs. This should give executive-level understanding without reading further.]

---

## Market Definition & Scope

**What's included**: [Precise definition of market boundaries]

**What's excluded**: [Adjacent markets not covered]

**Key terms**:
- [Term 1]: [Definition]
- [Term 2]: [Definition]

---

## Market Size & Growth

| Metric | Value | Source | Confidence |
|--------|-------|--------|------------|
| Current market size | $X | [1] | [HIGH/MED] |
| CAGR (period) | X% | [2] | [HIGH/MED] |
| Projected size (year) | $X | [1][3] | [MED] |

**Growth drivers**: [Brief list]

**Growth inhibitors**: [Brief list]

---

## Market Segmentation

### By [Dimension 1 - e.g., Geography]

| Segment | Size | Growth | Notes |
|---------|------|--------|-------|
| [Segment] | $X | X% | [Key insight] |

### By [Dimension 2 - e.g., Customer Type]

[Same structure]

---

## Competitive Landscape

### Major Players

| Company | Est. Share | Positioning | Key Strength | Key Weakness |
|---------|------------|-------------|--------------|--------------|
| [Co 1] | X% | [Position] | [Strength] | [Weakness] |
| [Co 2] | X% | [Position] | [Strength] | [Weakness] |

### Competitive Dynamics

[How companies compete. Basis of competition. Recent moves. 2-3 paragraphs.]

---

## Trends & Drivers

### [Trend 1: Name]
[Description. Evidence. Timeline. Impact. 1-2 paragraphs.]

### [Trend 2: Name]
[Same structure]

---

## Challenges & Barriers

| Challenge | Description | Who It Affects |
|-----------|-------------|----------------|
| [Challenge 1] | [Description] | [Affected parties] |
| [Challenge 2] | [Description] | [Affected parties] |

---

## Outlook

### Short-term (1-2 years)
[Expected developments, confidence level]

### Medium-term (3-5 years)
[Expected developments, confidence level]

### Scenarios
- **Bull case**: [What would drive upside]
- **Bear case**: [What would drive downside]

---

## Implications for [User's Context]

[What this means for their specific situation. Opportunities. Threats. Recommended actions.]

---

## Limitations & Uncertainties

### Data Limitations
[Market size estimates vary widely, methodology differences, etc.]

### Forecasting Uncertainty
[What could change projections]

### Coverage Gaps
[Segments or geographies not fully covered]

---

## Source Appendix

| # | Source | Date | Type | Used For |
|---|--------|------|------|----------|
| 1 | [URL] | Date | Industry Report | Market sizing |
| 2 | [URL] | Date | Company Filing | Revenue data |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Date | Initial version |
```

---

## Technical Implementation Guide

For explaining how to accomplish something technical.

```markdown
# [How to / Implementing] [Topic]

> **Generated**: YYYY-MM-DD  
> **Sources current as of**: YYYY-MM-DD  
> **Scope**: Standard  
> **Version**: 1.0  
> **Tested on**: [Environment/versions]

---

## TLDR

[What this guide covers. Expected outcome. Time estimate. Prerequisites summary. What's NOT covered.]

---

## Prerequisites

| Requirement | Version/Details | Verification |
|-------------|-----------------|--------------|
| [Tool/Access] | [Version] | [How to check] |
| [Knowledge] | [Level] | [Reference if needed] |

---

## Architecture Overview

[High-level diagram or description of how components fit together]

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ Input   │────▶│ Process │────▶│ Output  │
└─────────┘     └─────────┘     └─────────┘
```

---

## Implementation Steps

### Step 1: [Action Verb] [What]

**Goal**: [What this step accomplishes]

**Instructions**:
[Detailed steps with commands/code]

```bash
# Example command
command --flag value
```

**Verification**:
```bash
# How to confirm this step worked
verification-command
# Expected output: [what you should see]
```

**Common issues**:
- [Issue]: [Solution]

---

### Step 2: [Action Verb] [What]

[Same structure]

---

## Configuration Reference

| Setting | Default | Description | When to Change |
|---------|---------|-------------|----------------|
| [Setting] | [Value] | [What it does] | [Guidance] |

---

## Troubleshooting

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| [Error/behavior] | [Cause] | [Fix] |
| [Error/behavior] | [Cause] | [Fix] |

### Diagnostic Commands

```bash
# Check [what]
diagnostic-command

# Check [what else]
another-command
```

---

## Limitations & Uncertainties

### Known Limitations
[What this approach can't do]

### Environment-Specific Issues
[Things that may vary by setup]

### Version Sensitivity
[What might break with updates]

---

## Further Reading

| Resource | What It Covers |
|----------|----------------|
| [Official Docs URL] | [Scope] |
| [Tutorial URL] | [Scope] |

---

## Source Appendix

| # | Source | Date | Type | Used For |
|---|--------|------|------|----------|
| 1 | [URL] | Date | Official Docs | [Usage] |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Date | Initial version |
```

---

## Regulatory/Compliance Overview

For understanding legal or regulatory requirements.

```markdown
# [Regulation/Requirement]: Compliance Overview

> **Generated**: YYYY-MM-DD  
> **Sources current as of**: YYYY-MM-DD  
> **Scope**: Comprehensive  
> **Version**: 1.0

⚠️ **Disclaimer**: This document is informational only and does not constitute legal advice. Consult qualified legal counsel for compliance decisions.

---

## TLDR

[What the regulation requires. Who it applies to. Key deadlines. Penalties. 2-3 paragraphs giving executive understanding.]

---

## Regulation Overview

**Full name**: [Official name]

**Jurisdiction**: [Where it applies]

**Effective date**: [When it took effect]

**Enforcing body**: [Who enforces]

**Official text**: [URL to authoritative source]

---

## Applicability

### Who Must Comply

| Criterion | Threshold | Notes |
|-----------|-----------|-------|
| [Criterion] | [Threshold] | [Clarification] |

### Exemptions

| Exemption | Conditions | Documentation Required |
|-----------|------------|----------------------|
| [Exemption type] | [When it applies] | [What to maintain] |

---

## Key Requirements

### Requirement 1: [Name]

**What's required**: [Description]

**Deadline**: [Date or ongoing]

**Evidence needed**: [What to document/maintain]

**Common approaches**: [How orgs typically comply]

**Sources**: [1][2]

---

### Requirement 2: [Name]

[Same structure]

---

## Compliance Approaches

| Approach | Effort | Cost | Pros | Cons |
|----------|--------|------|------|------|
| [Approach 1] | L/M/H | $Range | [Pros] | [Cons] |
| [Approach 2] | L/M/H | $Range | [Pros] | [Cons] |

---

## Enforcement & Penalties

### Penalty Structure

| Violation Type | Penalty Range | Examples |
|----------------|---------------|----------|
| [Type] | [Range] | [Past cases if available] |

### Recent Enforcement

[Summary of notable enforcement actions, if public]

---

## Timeline & Upcoming Changes

| Date | Event | Impact |
|------|-------|--------|
| [Date] | [What happens] | [What it means] |

### Pending Changes

[Proposed amendments, expected guidance, etc.]

---

## Limitations & Uncertainties

### Interpretation Uncertainty
[Areas where guidance is unclear or evolving]

### Jurisdiction Variations
[How requirements may differ by location]

### Document Currency
[When this should be reviewed for updates]

---

## Source Appendix

| # | Source | Date | Type | Used For |
|---|--------|------|------|----------|
| 1 | [Official regulation URL] | Date | Primary/Regulatory | Requirements text |
| 2 | [Agency guidance URL] | Date | Primary/Guidance | Interpretation |
| 3 | [Law firm analysis URL] | Date | Secondary/Legal | Practical guidance |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Date | Initial version |
```

---

## Research Synthesis / Literature Review

For synthesizing academic or technical research on a topic.

```markdown
# [Topic]: Research Synthesis

> **Generated**: YYYY-MM-DD  
> **Sources current as of**: YYYY-MM-DD  
> **Scope**: Comprehensive  
> **Version**: 1.0

---

## TLDR

[Current scientific/expert consensus. Key debates. Practical implications. Confidence level for main conclusions. 2-3 paragraphs.]

---

## Background

[Why this question matters. Brief history of research. Current relevance. 2-3 paragraphs.]

---

## Methodology

### Search Strategy

| Database/Source | Query | Results |
|-----------------|-------|---------|
| [Source] | [Query used] | [# found, # included] |

### Inclusion Criteria

- [Criterion 1]
- [Criterion 2]

### Exclusion Criteria

- [Criterion 1]

### Limitations of This Review

[What this methodology might miss]

---

## Current Understanding

### [Subtopic 1]: [Question/Area]

**Consensus view**: [What most research supports]

**Confidence**: [HIGH/MEDIUM/LOW]

**Key studies**:
- [Study 1 citation]: [Key finding] [1]
- [Study 2 citation]: [Key finding] [2]

**Nuances/caveats**: [Important qualifications]

---

### [Subtopic 2]: [Question/Area]

[Same structure]

---

## Areas of Debate

### [Debate 1]: [Question]

| Position | Proponents | Key Evidence | Weaknesses |
|----------|------------|--------------|------------|
| [Position A] | [Who] | [Evidence] | [Limitations] |
| [Position B] | [Who] | [Evidence] | [Limitations] |

**What would resolve this**: [Type of evidence needed]

---

## Research Gaps

| Gap | Why It Matters | Barriers to Filling |
|-----|----------------|---------------------|
| [Gap] | [Importance] | [Why unstudied] |

---

## Practical Implications

### What This Means For [Context]

[Translation of findings to practical application. Appropriate confidence level.]

### Recommended Actions

| If you need to... | The evidence suggests... | Confidence |
|-------------------|-------------------------|------------|
| [Action context] | [Guidance] | [Level] |

---

## Limitations & Uncertainties

### Methodological Limitations
[Common issues across studies reviewed]

### Publication Bias Concerns
[If applicable]

### Generalizability
[To what populations/contexts do findings apply?]

### Recency
[How current is the research base?]

---

## Source Appendix

| # | Source | Date | Type | Key Contribution |
|---|--------|------|------|------------------|
| 1 | [Full citation] | Year | Peer-reviewed | [What it showed] |
| 2 | [Full citation] | Year | Preprint | [What it showed] |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Date | Initial version |
```
