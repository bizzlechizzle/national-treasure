---
name: audit
description: Audit any document for correctness against an SME reference document. Produces quantitative scores for accuracy, coverage, currency, and citation quality. Use when user asks to "audit", "verify", "check correctness", or "validate" a document against an SME source. Requires both a document to audit and an SME reference document. Outputs detailed audit report with per-claim scoring and overall grades.
---

# Audit Skill v0.1.0

**Trust but verify.** Every claim must trace to a cited source that exists and supports the assertion.

Systematically verify document correctness by:
1. Confirming cited sources actually exist (URLs resolve, documents accessible)
2. Verifying claims match what cited sources actually say
3. Cross-referencing against authoritative SME reference documents

## Core Philosophy

```
Claim → Citation → Source Exists → Source Supports Claim → VERIFIED
         ↓              ↓                    ↓
     Missing?      Dead link?         Misrepresented?
         ↓              ↓                    ↓
    UNSUPPORTED    BROKEN           MISATTRIBUTED
```

**No citation = unverified claim. Broken citation = broken trust.**

## Workflow Overview

1. **Intake** - Identify audit target and reference SME document
2. **Citation Verification** - Verify every cited source exists and is accessible
3. **Claim-to-Source Audit** - Verify claims match what sources actually say
4. **Cross-Reference Audit** - Match claims against SME reference
5. **Gap Analysis** - Identify missing coverage
6. **Currency Check** - Flag outdated information
7. **Scoring** - Calculate quantitative grades
8. **Report Generation** - Produce actionable audit report

---

## Step 1: Intake

### Required Inputs

| Input | Description | Required |
|-------|-------------|----------|
| **Audit Target** | The document being audited | Yes |
| **SME Reference** | Authoritative SME document to audit against | Yes |
| **Audit Scope** | Full audit or specific sections | Optional |
| **Strictness Level** | Lenient / Standard / Strict | Optional (default: Standard) |

### Strictness Levels

| Level | Description | Threshold |
|-------|-------------|-----------|
| **Lenient** | Accept paraphrasing, approximate figures (±10%) | Pass: 60%+ |
| **Standard** | Accept minor variations, exact figures required | Pass: 75%+ |
| **Strict** | Exact alignment required, full citation tracing | Pass: 90%+ |

### Pre-Audit Validation

Before proceeding, verify:

- [ ] **Not circular**: Audit target ≠ SME reference (abort if same)
- [ ] SME reference document is accessible and readable
- [ ] Audit target document is accessible and readable
- [ ] SME document contains structured claims (not just prose)
- [ ] Documents cover overlapping subject matter (>30% topic overlap)
- [ ] **Meta-audit passed**: Spot-check 3-5 SME citations still resolve

If SME reference fails meta-audit, warn user:
> ⚠️ SME reference has broken citations. Audit proceeding with reduced confidence.

If SME reference is missing structured claims, warn user that audit accuracy will be limited.

---

## Step 2: Citation Verification

**This is the foundation of trust.** Before evaluating content, verify citations are real.

### Citation Inventory

Extract all citations from audit target:

```yaml
citations:
  - id: 1
    url: "https://kubernetes.io/docs/concepts/..."
    type: URL
    claimed_content: "Kubernetes pod lifecycle"

  - id: 2
    text: "Smith et al., 2023"
    type: ACADEMIC
    doi: "10.1234/..."

  - id: 3
    text: "Internal doc ref"
    type: INTERNAL
    accessible: false  # Can't verify externally
```

### Verification Process

For each citation:

| Citation Type | Verification Method | Pass Criteria |
|---------------|---------------------|---------------|
| **URL** | HTTP HEAD/GET request | 200 status, content loads |
| **DOI** | Resolve via doi.org | DOI resolves to paper |
| **Academic** | Search title + authors | Paper exists in index |
| **Book** | ISBN lookup | ISBN valid, book exists |
| **Internal** | Mark as UNVERIFIABLE | Note limitation |
| **Archive** | Check archive.org | Snapshot exists |

### URL Verification

```yaml
url_checks:
  - url: "https://kubernetes.io/docs/..."
    status: 200
    content_type: "text/html"
    title: "Pod Lifecycle | Kubernetes"
    verified: true
    last_checked: "2024-01-15T10:30:00Z"

  - url: "https://example.com/deleted-page"
    status: 404
    verified: false
    resolution: "Check archive.org for snapshot"
    archive_url: "https://web.archive.org/web/..."
```

### Citation Verification Scoring

| Status | Score | Count As |
|--------|-------|----------|
| **Verified** | 100% | Exists, accessible |
| **Archived** | 80% | Dead link but archive exists |
| **Unverifiable** | 50% | Internal docs, can't check |
| **Broken** | 0% | Dead link, no archive |
| **Fake** | -50% | Citation invented/wrong |

### Citation Report

```markdown
## Citation Verification Summary

| Status | Count | Percentage |
|--------|-------|------------|
| Verified | 12 | 80% |
| Archived | 2 | 13% |
| Broken | 1 | 7% |

### Broken Citations
| # | URL | Status | Recommendation |
|---|-----|--------|----------------|
| 7 | https://... | 404 | Remove or find archive |
```

---

## Step 3: Claim-to-Source Verification

**Trust but verify: Does the source actually say what the document claims?**

For each claim with a citation, fetch the source and verify the claim.

### Verification Process

1. **Fetch source content** (WebFetch or document read)
2. **Locate relevant passage** in source
3. **Compare claim to source** - Does source support claim?

### Verification Classifications

| Result | Description | Score |
|--------|-------------|-------|
| **VERIFIED** | Source directly supports claim | 100% |
| **SUPPORTED** | Source implies/partially supports | 85% |
| **OVERSTATED** | Claim exaggerates source | 60% |
| **CHERRY-PICKED** | True but missing context | 50% |
| **MISATTRIBUTED** | Source says something different | 0% |
| **FABRICATED** | Source says opposite | -25% |

### Verification Log

```yaml
claim_verification:
  - claim_id: C001
    claim_text: "Kubernetes handles 10,000 pods per cluster"
    citation_id: 1
    source_quote: "tested up to 5,000 pods, theoretical limit higher"
    result: OVERSTATED
    score: 60
    notes: "Claim inflates tested numbers"

  - claim_id: C002
    claim_text: "OAuth2 uses refresh tokens for..."
    citation_id: 3
    source_quote: "Refresh tokens allow obtaining new access tokens..."
    result: VERIFIED
    score: 100
```

### Red Flags

Automatic audit flags:

| Pattern | Concern | Action |
|---------|---------|--------|
| Numeric claim, no source quote | Possible fabrication | Verify exact number |
| "Studies show" without citation | Weasel words | Flag as unsupported |
| Very old source for current claim | Currency issue | Check for updates |
| Source is another aggregator | Circular sourcing | Find primary |

---

## Step 4: SME Claim Extraction

Extract verifiable assertions from both documents for cross-reference.

### Claim Types

| Type | Example | Verification Method |
|------|---------|---------------------|
| **Factual** | "Kubernetes 1.28 added..." | Direct match |
| **Quantitative** | "Response time under 100ms" | Numeric comparison |
| **Definitional** | "OAuth2 is a..." | Semantic alignment |
| **Procedural** | "To configure X, first..." | Step comparison |
| **Comparative** | "X is faster than Y" | Relationship check |
| **Temporal** | "As of 2024..." | Date validation |

### Extraction Format

For each document, build claim inventory:

```yaml
claims:
  - id: C001
    text: "Kubernetes supports horizontal pod autoscaling"
    type: factual
    source_section: "Architecture Overview"
    source_line: 42
    confidence: HIGH  # If present in SME
    citations: [1, 3]  # Reference numbers from SME

  - id: C002
    text: "Cold starts average 200-400ms"
    type: quantitative
    value: "200-400"
    unit: "ms"
    source_section: "Performance"
    source_line: 87
```

### Claim Normalization

Before comparison, normalize claims:

1. **Expand acronyms** - Match "K8s" to "Kubernetes"
2. **Standardize units** - Convert to base units (ms, bytes, etc.)
3. **Extract numeric ranges** - Parse "200-400ms" as range object
4. **Identify synonyms** - "container" / "pod" context matching
5. **Resolve references** - "it", "this feature" → actual subject

---

## Step 5: Cross-Reference Audit

Match audit target claims against SME reference.

### Matching Algorithm

For each claim in audit target:

1. **Exact Match** - Identical claim exists in SME → Score 100%
2. **Semantic Match** - Equivalent meaning, different wording → Score 90%
3. **Partial Match** - Related but incomplete/different scope → Score 50-80%
4. **Contradiction** - Opposite assertion in SME → Score 0%, flag critical
5. **Unsupported** - No corresponding claim in SME → Score varies by type

### Match Classification Table

| Audit Claim | SME Reference | Classification | Score |
|-------------|---------------|----------------|-------|
| "X is Y" | "X is Y" | EXACT | 100% |
| "X is Y" | "X equals Y" | SEMANTIC | 90% |
| "X is ~100" | "X is 98" | APPROXIMATE | 85% |
| "X supports A,B" | "X supports A,B,C" | SUBSET | 75% |
| "X is Y" | "X is Z" | CONTRADICTION | 0% |
| "X is Y" | (not found) | UNSUPPORTED | varies |

### Contradiction Severity

| Severity | Definition | Impact |
|----------|------------|--------|
| **Critical** | Core fact incorrect, could cause harm | -20 points overall, mandatory flag |
| **Major** | Significant error affecting understanding | -10 points overall |
| **Minor** | Technical inaccuracy, limited impact | -5 points overall |
| **Trivial** | Style/wording, no semantic difference | -0 points |

### Cross-Reference Log

Document every comparison:

```yaml
cross_references:
  - audit_claim: C001
    sme_claim: S003
    match_type: SEMANTIC
    score: 90
    notes: "Wording differs but meaning equivalent"

  - audit_claim: C002
    sme_claim: S015
    match_type: CONTRADICTION
    severity: MAJOR
    score: 0
    notes: "Audit says 200-400ms, SME says 100-150ms"
    evidence: "SME cites primary benchmark study"
```

---

## Step 6: Gap Analysis

Identify what the audit target is missing.

### Coverage Matrix

| Category | Description | Weight |
|----------|-------------|--------|
| **Core Coverage** | Essential topics from SME present in target | 40% |
| **Detail Coverage** | Supporting details and nuances | 25% |
| **Edge Cases** | Limitations, exceptions, caveats | 20% |
| **Recency** | Current/updated information | 15% |

### Gap Classification

| Gap Type | Impact | Recommendation |
|----------|--------|----------------|
| **Critical Gap** | Missing essential concept | Must address |
| **Significant Gap** | Missing important detail | Should address |
| **Minor Gap** | Missing nice-to-have info | Consider addressing |
| **Acceptable Omission** | Out of scope for target | Document scope |

### Gap Report Format

```yaml
gaps:
  critical:
    - topic: "Security considerations"
      sme_section: "Security"
      severity: critical
      recommendation: "Add security section covering auth, encryption"

  significant:
    - topic: "Error handling patterns"
      sme_section: "Best Practices > Error Handling"
      severity: significant
      recommendation: "Expand error handling beyond basic try/catch"
```

---

## Step 7: Currency Check

Verify information is current and not outdated.

### Currency Verification

| Check | Method | Impact |
|-------|--------|--------|
| **Version numbers** | Compare stated versions to current releases | Major if outdated |
| **Dates** | Verify "as of X" claims | Minor to major |
| **API/syntax** | Compare to current documentation | Critical if deprecated |
| **Best practices** | Check against current recommendations | Major if obsolete |
| **Statistics** | Verify against recent data | Medium if stale |

### Currency Scoring

| Status | Score Modifier | Threshold |
|--------|----------------|-----------|
| **Current** | +0% | Within 6 months or current version |
| **Aging** | -5% | 6-12 months old |
| **Stale** | -15% | 1-2 years old |
| **Obsolete** | -30% | 2+ years or deprecated |

### Currency Log

```yaml
currency_checks:
  - claim: "React 18 introduces..."
    current_version: "React 19"
    status: AGING
    modifier: -5
    notes: "Content valid but newer version available"

  - claim: "Use componentWillMount..."
    current_status: DEPRECATED
    status: OBSOLETE
    modifier: -30
    notes: "Method deprecated in React 16.3, removed in 18"
```

---

## Step 8: Scoring

Calculate quantitative grades across dimensions.

### Scoring Dimensions

| Dimension | Weight | Measures |
|-----------|--------|----------|
| **Citation Integrity** | 30% | Do citations exist and support claims? |
| **Accuracy** | 30% | Correctness of claims vs SME |
| **Coverage** | 20% | Completeness vs SME scope |
| **Currency** | 20% | How current the information is |

**Citation Integrity is foundational** - a document with broken or misrepresented citations cannot be trusted regardless of other scores.

### Dimension Calculations

#### Citation Integrity Score
```
citation_integrity = (
  # Citation existence (50% of score)
  (verified_urls × 1.0 +
   archived_urls × 0.8 +
   unverifiable × 0.5 +
   broken_urls × 0.0 +
   fake_citations × -0.5
  ) / total_citations × 50

  +

  # Claim-to-source accuracy (50% of score)
  (verified_claims × 1.0 +
   supported_claims × 0.85 +
   overstated_claims × 0.6 +
   cherry_picked × 0.5 +
   misattributed × 0.0 +
   fabricated × -0.25
  ) / cited_claims × 50
)
```

**Automatic Failure**: If citation_integrity < 50%, overall grade capped at D.

#### Accuracy Score
```
accuracy = (
  (exact_matches × 1.0) +
  (semantic_matches × 0.9) +
  (partial_matches × 0.7) +
  (unsupported_neutral × 0.5) +
  (contradictions × 0.0)
) / total_claims × 100

# Apply severity penalties
accuracy -= critical_contradictions × 5
accuracy -= major_contradictions × 3
accuracy -= minor_contradictions × 1
```

#### Coverage Score
```
coverage = (
  (core_topics_covered / core_topics_in_sme × 0.4) +
  (details_covered / details_in_sme × 0.25) +
  (edge_cases_covered / edge_cases_in_sme × 0.2) +
  (recency_addressed × 0.15)
) × 100
```

#### Currency Score
```
currency = 100 - sum(currency_penalties)
# Cap penalties at -50 (floor of 50%)
```

### Overall Grade

```
overall = (
  citation_integrity × 0.30 +
  accuracy × 0.30 +
  coverage × 0.20 +
  currency × 0.20
)

# Apply citation integrity floor
if citation_integrity < 50:
  overall = min(overall, 65)  # Cap at D
```

### Grade Thresholds

| Grade | Score Range | Interpretation |
|-------|-------------|----------------|
| **A** | 90-100 | Excellent - Ready for use as reference |
| **B** | 80-89 | Good - Minor improvements recommended |
| **C** | 70-79 | Acceptable - Notable gaps, review needed |
| **D** | 60-69 | Below Standard - Significant revision required |
| **F** | <60 | Failing - Major rework or rejection |

---

## Step 9: Report Generation

### Audit Report Structure

```markdown
# SME Audit Report

> **Audit Date**: [YYYY-MM-DD]
> **Audit Target**: [Document name/path]
> **SME Reference**: [Reference document name/path]
> **Auditor**: Claude (sme-audit skill v1.0)
> **Strictness**: [Lenient/Standard/Strict]

---

## Executive Summary

**Overall Grade: [A-F]** ([Score]%)

| Dimension | Score | Grade |
|-----------|-------|-------|
| Citation Integrity | XX% | X |
| Accuracy | XX% | X |
| Coverage | XX% | X |
| Currency | XX% | X |

### Trust Verification

| Metric | Value |
|--------|-------|
| Citations verified to exist | X/Y (Z%) |
| Claims verified against sources | X/Y (Z%) |
| Broken/dead links | X |
| Misrepresented sources | X |

### Verdict

[2-3 sentences: Is this document trustworthy against the SME? Key concerns?]

### Critical Issues (if any)

[Bullet list of contradictions or critical gaps that must be addressed]

---

## Detailed Findings

### Citation Integrity Analysis

**Score: XX%**

#### Citation Existence Verification
| # | Citation | Type | Status | Notes |
|---|----------|------|--------|-------|
| 1 | [URL] | URL | VERIFIED | 200 OK |
| 2 | [URL] | URL | BROKEN | 404 Not Found |

#### Claim-to-Source Verification
| Claim | Citation | Source Quote | Result |
|-------|----------|--------------|--------|
| "X is Y" | [1] | "X equals Y..." | VERIFIED |
| "Z is 100%" | [2] | "Z is around 80%" | OVERSTATED |

#### Citation Issues Found
| Issue | Count | Impact |
|-------|-------|--------|
| Broken links | X | -Y points |
| Misrepresented | X | -Y points |
| Fabricated | X | -Y points |

---

### Accuracy Analysis

**Score: XX%** (X matches / Y claims)

#### Verified Claims
| Claim | Match Type | Score | Notes |
|-------|------------|-------|-------|
| ... | ... | ... | ... |

#### Contradictions Found
| Claim | SME Says | Severity | Resolution |
|-------|----------|----------|------------|
| ... | ... | ... | ... |

#### Unsupported Claims
| Claim | Status | Risk | Recommendation |
|-------|--------|------|----------------|
| ... | ... | ... | ... |

### Coverage Analysis

**Score: XX%**

#### Topics Covered
[Checklist of SME topics present in audit target]

#### Gaps Identified

| Gap | Severity | SME Section | Recommendation |
|-----|----------|-------------|----------------|
| ... | ... | ... | ... |

### Currency Analysis

**Score: XX%**

| Issue | Current State | Impact | Recommendation |
|-------|---------------|--------|----------------|
| ... | ... | ... | ... |

### Citation Quality Analysis

**Score: XX%**

- Claims with citations: X/Y (Z%)
- Primary sources: X/Y (Z%)
- Verifiable links: X/Y (Z%)

---

## Recommendations

### Must Fix (Critical)
1. [Specific action items]

### Should Fix (Important)
1. [Specific action items]

### Consider (Minor)
1. [Specific action items]

---

## Audit Metadata

### Methodology
[Brief description of audit approach]

### Scope Limitations
[What was NOT audited]

### Confidence in Audit
[Self-assessment of audit quality]

---

## Audit Appendix

### Claim Inventory
[Full list of extracted claims]

### Cross-Reference Matrix
[Complete matching log]

### Score Calculations
[Show work for transparency]
```

---

## Audit Output Location

Save audit reports to `sme/audits/`:

```
project/
├── sme/
│   ├── kubernetes-security.md        # Original SME doc
│   ├── audits/                        # Audit reports go here
│   │   ├── doc-vs-kubernetes-security-2024-01-15.md
│   │   └── ...
```

### Naming Convention

`[target-doc-name]-vs-[sme-name]-[YYYY-MM-DD].md`

---

## Self-Audit: Audit Accountability

The audit itself must be auditable. Include these accountability features:

### Audit Quality Self-Assessment

| Metric | Value | Acceptable |
|--------|-------|------------|
| Claims extracted from target | X | >10 for meaningful audit |
| Claims extracted from SME | X | >10 for meaningful audit |
| Cross-reference coverage | X% | >90% |
| Ambiguous matches | X | <10% of total |
| Manual judgment calls | X | Document each |

### Reproducibility Checklist

- [ ] Claim extraction methodology documented
- [ ] Match criteria explicit and consistent
- [ ] Scoring calculations shown
- [ ] Subjective judgments flagged
- [ ] Limitations acknowledged

### Audit Confidence Score

Rate audit reliability:

| Confidence | Criteria |
|------------|----------|
| **HIGH** | Clear claims, unambiguous matching, consistent SME |
| **MEDIUM** | Some interpretation needed, minor ambiguity |
| **LOW** | Significant interpretation, incomplete SME, scope mismatch |

---

## Checks and Balances

### Guard Rails

| Risk | Mitigation |
|------|------------|
| **Circular Reference** | Audit target cannot be the SME reference - abort if same document |
| **Gaming via Vague Sources** | OVERSTATED/CHERRY-PICKED classifications catch this |
| **Auditor Bias** | Self-audit section requires documenting judgment calls |
| **Stale Audit** | Re-audit triggered by: SME update, 6 months elapsed, or critical dependency change |
| **SME Itself Flawed** | Audit the SME against its own citations first (meta-audit) |

### Re-Audit Triggers

Re-run audit when:

- [ ] SME reference document updated (version change)
- [ ] 6+ months since last audit
- [ ] Critical external change (API deprecation, security vulnerability)
- [ ] User reports inaccuracy
- [ ] Audit target significantly revised

### Feedback Loop: Audit → SME

When audit identifies issues, generate remediation ticket:

```yaml
remediation:
  sme_document: "kubernetes-security.md"
  audit_date: "2024-01-15"
  issues:
    - type: BROKEN_CITATION
      citation_id: 7
      action: "Find current URL or archive"
      priority: HIGH

    - type: CONTRADICTION
      claim: "Max 5000 pods"
      current_truth: "Max 10000 pods as of K8s 1.28"
      action: "Update SME with new limit"
      priority: CRITICAL

    - type: GAP
      missing: "Security hardening section"
      action: "Research and add to SME"
      priority: MEDIUM
```

### Meta-Audit: Auditing the SME Reference

Before trusting an SME as reference, quick-verify:

1. **Citation spot-check**: Verify 3-5 random citations still resolve
2. **Currency check**: Is SME dated within acceptable window?
3. **Self-consistency**: Does SME claim audit-ready status?

If SME fails meta-audit, flag and proceed with caution.

---

## Edge Cases

### SME Document Incomplete
- Note gap in audit limitations
- Score based on available content
- Recommend SME enhancement

### Target Document Out of Scope
- If <30% topic overlap, abort with warning
- Suggest appropriate SME document

### Multiple SME References Needed
- Allow composite reference
- Weight sources by authority
- Document multi-source methodology

### Ambiguous Claims
- Flag for human review
- Don't guess - mark "REQUIRES CLARIFICATION"
- Include in audit uncertainty

### Audit Disputes
If user disputes findings:
1. Show specific claim-to-claim comparison
2. Cite exact text from both documents
3. Explain matching logic
4. Allow override with documentation
