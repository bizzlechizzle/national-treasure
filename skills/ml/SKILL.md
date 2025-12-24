---
name: ml
description: Machine learning decision support for adding ML capabilities to applications. Problem-first guidance that helps you select the right technique, understand data requirements, avoid common pitfalls, and integrate ML into production systems. Covers classification, regression, anomaly detection, forecasting, text classification, clustering, recommendation, and ranking. Non-generative ML only (no LLMs).
---

# Machine Learning Integration Guide v0.1.0

Add the right ML capability to your application—or decide not to.

## Purpose

This skill helps you:

1. **Decide IF** ML is the right approach (often it isn't)
2. **Select WHICH** technique fits your problem
3. **Understand WHAT** data you need
4. **Avoid HOW** common implementation pitfalls
5. **Integrate WHERE** ML fits in your architecture

## Quick Start

```
┌─────────────────────────────────────────────────────────────────┐
│                    ML DECISION WORKFLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. FEASIBILITY   →  Can ML solve this? Should it?              │
│     └─► See: Feasibility Checklist (below)                      │
│                                                                 │
│  2. PROBLEM TYPE  →  What kind of prediction do you need?       │
│     └─► See: references/decision-tree.md                        │
│                                                                 │
│  3. TECHNIQUE     →  Which algorithm/approach fits?             │
│     └─► See: references/[problem-type].md                       │
│                                                                 │
│  4. DATA          →  Do you have enough? Is it clean?           │
│     └─► See: references/data-requirements.md                    │
│                                                                 │
│  5. INTEGRATION   →  How does it fit in your app?               │
│     └─► See: references/integration-patterns.md                 │
│                                                                 │
│  6. EVALUATION    →  How do you measure success?                │
│     └─► See: references/evaluation-metrics.md                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Feasibility Checklist

**Complete this BEFORE selecting any technique.** If you can't check most boxes, ML may not be the right approach.

### Hard Requirements (Must Have ALL)

- [ ] **Clear success metric exists** — You can define what "better" means numerically
- [ ] **Historical data available** — You have examples of inputs AND correct outputs
- [ ] **Pattern exists in data** — A human could (theoretically) learn to do this task given the same data
- [ ] **Tolerance for errors** — Some wrong predictions are acceptable; not safety-critical without human review

### Soft Requirements (Need MOST)

- [ ] **Sufficient data volume** — Hundreds of examples minimum; thousands preferred
- [ ] **Labels are reliable** — Your "correct answers" are actually correct
- [ ] **Input data is available at prediction time** — Features you train on can be computed when making predictions
- [ ] **Problem is relatively stable** — Patterns don't change faster than you can retrain
- [ ] **Maintenance capacity** — Someone will monitor, retrain, and fix the model over time

### Red Flags (Any = Reconsider)

- [ ] Rules could solve this with 90%+ accuracy
- [ ] Data contains protected attributes you can't legally use
- [ ] Predictions must be 100% explainable for compliance
- [ ] Less than 100 labeled examples available
- [ ] Ground truth takes months/years to obtain
- [ ] Adversarial users will actively try to game the model

### Feasibility Verdict

| Checkboxes | Verdict |
|------------|---------|
| All Hard + Most Soft + No Red Flags | **Proceed with ML** |
| All Hard + Some Soft + No Red Flags | **Proceed cautiously**, start simple |
| Missing Hard requirements | **Do not use ML** — fix gaps first |
| Multiple Red Flags | **Reconsider** — see `when-not-to-use-ml.md` |

---

## Problem Type Quick Reference

| You want to... | Problem Type | Reference |
|----------------|--------------|-----------|
| Predict a category (yes/no, A/B/C) | Classification | `references/classification.md` |
| Predict a number (price, count, score) | Regression | `references/regression.md` |
| Find unusual items (fraud, defects) | Anomaly Detection | `references/anomaly-detection.md` |
| Predict future values over time | Forecasting | `references/forecasting.md` |
| Categorize text (spam, sentiment, topic) | Text Classification | `references/text-classification.md` |
| Group similar items together | Clustering | `references/clustering.md` |
| Suggest items users might like | Recommendation | `references/recommendation.md` |
| Order items by relevance | Ranking | `references/ranking.md` |

---

## Data Requirements Overview

| Problem Type | Minimum Viable | Recommended | Ideal |
|--------------|----------------|-------------|-------|
| Classification (binary) | 100+ per class | 1,000+ per class | 10,000+ per class |
| Classification (multiclass) | 50+ per class | 500+ per class | 5,000+ per class |
| Regression | 100+ total | 1,000+ total | 10,000+ total |
| Anomaly Detection | 1,000+ normal | 10,000+ normal | 100,000+ normal |
| Forecasting | 2+ seasonal cycles | 5+ seasonal cycles | 10+ seasonal cycles |
| Text Classification | 100+ per class | 1,000+ per class | 10,000+ per class |
| Clustering | 10x features | 100x features | 1,000x features |
| Recommendation | 1,000+ interactions | 100,000+ interactions | 1M+ interactions |
| Ranking | 1,000+ comparisons | 10,000+ comparisons | 100,000+ comparisons |

See `references/data-requirements.md` for detailed guidance.

---

## Technique Selection Principles

### Start Simple

```
Rule-based → Linear model → Tree ensemble → Neural network
   ↑                                              ↓
   └──────── Can you get there? Stay here! ───────┘
```

**Why**: Simpler models are faster to train, easier to debug, more interpretable, and often perform nearly as well. Complexity should be earned by demonstrated performance gains.

### Match Technique to Constraints

| Constraint | Favored Techniques |
|------------|-------------------|
| Must explain predictions | Linear models, decision trees, SHAP on any model |
| Very low latency (<10ms) | Linear models, small trees, distilled models |
| Limited training data | Transfer learning, regularized models, Bayesian |
| No GPU available | Tree ensembles, linear models, classical ML |
| Streaming/online learning | SGD-based models, online forests |
| Edge deployment | ONNX, TensorFlow Lite, quantized models |

### When to Go Complex

Move to more complex techniques when:

1. Simple baseline established and documented
2. Performance gap is meaningful for business
3. You have enough data to avoid overfitting
4. You have infrastructure to support it
5. Maintenance burden is acceptable

---

## Integration Patterns Overview

| Pattern | Latency | Complexity | Best For |
|---------|---------|------------|----------|
| **Batch prediction** | Hours | Low | Periodic scoring, reports |
| **Synchronous API** | <100ms | Medium | Real-time features, user-facing |
| **Async queue** | Seconds-minutes | Medium | Background processing |
| **Embedded model** | <10ms | High | Edge, mobile, IoT |
| **Feature store** | Varies | High | Shared features across models |

See `references/integration-patterns.md` for implementation details.

---

## Common Pitfalls (Preview)

**Data Pitfalls**
- Data leakage (using future info to predict past)
- Training/serving skew (features differ in production)
- Label leakage (target encoded in features)

**Modeling Pitfalls**
- Overfitting (model memorizes, doesn't generalize)
- Class imbalance (rare events get ignored)
- Feature scaling mismatch

**Production Pitfalls**
- Model drift (world changes, model doesn't)
- Silent failures (wrong predictions, no alerts)
- Feedback loops (model influences its own training data)

See `references/common-pitfalls.md` for detection and prevention.

---

## Reference Documents

### Decision Support
| Document | Purpose |
|----------|---------|
| `decision-tree.md` | Problem type selector with examples |
| `when-not-to-use-ml.md` | Alternatives to ML, when rules win |

### Problem Types
| Document | Purpose |
|----------|---------|
| `classification.md` | Binary and multiclass prediction |
| `regression.md` | Continuous value prediction |
| `anomaly-detection.md` | Outlier and fraud detection |
| `forecasting.md` | Time series prediction |
| `text-classification.md` | NLP classification (non-generative) |
| `clustering.md` | Unsupervised grouping |
| `recommendation.md` | Collaborative and content-based filtering |
| `ranking.md` | Learning to rank |

### Cross-Cutting
| Document | Purpose |
|----------|---------|
| `data-requirements.md` | Data quality, quantity, and preparation |
| `integration-patterns.md` | Production deployment patterns |
| `evaluation-metrics.md` | Measuring model performance |
| `common-pitfalls.md` | Mistakes and how to avoid them |

---

## Usage Examples

### Example 1: "Should I use ML for this?"

**Situation**: User wants to filter spam comments on their blog.

**Process**:
1. Run Feasibility Checklist
   - Clear metric: spam/not-spam accuracy ✓
   - Historical data: existing comments with spam flags ✓
   - Pattern exists: humans can identify spam ✓
   - Error tolerance: false positives go to moderation queue ✓
   - Volume: 500 spam, 10,000 ham ✓

2. Check Red Flags
   - Could rules work? Keyword blocklist gets ~70% — ML could improve ✓

3. **Verdict**: Proceed → Classification problem → See `classification.md`

### Example 2: "What technique should I use?"

**Situation**: User has 50,000 rows of tabular data, wants to predict customer churn (yes/no).

**Process**:
1. Problem type: Binary classification
2. Data type: Tabular (structured)
3. Data volume: 50,000 rows — solid
4. Constraints: Must explain to business stakeholders

**Recommendation**: Start with logistic regression (interpretable), compare against XGBoost with SHAP explanations. See `classification.md` → Tabular section.

### Example 3: "ML is overkill here"

**Situation**: User wants to categorize support tickets into 5 departments based on keywords.

**Process**:
1. Run Feasibility Checklist
2. Red Flag triggered: Rules could solve with 90%+ accuracy
   - Department keywords are predictable ("billing" → Billing, "password reset" → IT)

**Recommendation**: Start with keyword rules. Add ML only if rules plateau below acceptable accuracy. See `when-not-to-use-ml.md`.

---

## Quality Standards

### What Makes Good ML Integration

| Quality | Indicator |
|---------|-----------|
| **Justified** | Clear reason why ML over alternatives |
| **Baselined** | Simple approach tried first |
| **Measured** | Success metric defined and tracked |
| **Monitored** | Drift and errors detected |
| **Maintainable** | Retraining process documented |
| **Graceful** | Fallback when model fails |

### Red Flags in ML Projects

- No baseline comparison
- "We need deep learning" without justification
- No plan for model updates
- Accuracy-only evaluation (no precision/recall/business metrics)
- Training data not versioned
- No monitoring in production

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2025-01-XX | Initial version — problem-first structure, no vision |
