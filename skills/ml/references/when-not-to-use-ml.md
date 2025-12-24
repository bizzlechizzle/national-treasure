# When NOT to Use ML

The most important ML skill is knowing when not to use it.

---

## The Default Position

**Start without ML. Add it only when simpler approaches fail.**

ML adds complexity, maintenance burden, and failure modes. If rules work, use rules.

---

## Red Flags: Don't Use ML

### 1. Rules Can Solve It

If domain experts can articulate the logic, encode it directly.

| Scenario | Rule-Based Approach |
|----------|---------------------|
| "Flag orders over $10,000" | Simple threshold |
| "Route tickets with 'billing' to Finance" | Keyword matching |
| "Reject emails from blocked domains" | Blocklist |
| "Calculate shipping based on weight/distance" | Formula |
| "Show premium features to paid users" | Boolean check |

**Test**: Can you write if/else statements that get 80-90% accuracy? Start there.

### 2. No Historical Data

ML learns from examples. No examples = no learning.

| Situation | Alternative |
|-----------|-------------|
| New product, no usage data | Launch with rules, collect data |
| No labeled outcomes | Design labeling process first |
| Privacy prevents data collection | Rule-based or external service |
| One-time decision | Human judgment |

### 3. Problem Changes Faster Than You Can Retrain

| Situation | Why ML Fails |
|-----------|--------------|
| Stock day trading | Patterns expire in hours |
| Breaking news classification | New topics constantly |
| Adversarial fraud | Attackers adapt quickly |
| Regulatory changes | Rules change overnight |

**Alternative**: Rule engines with human-in-the-loop updates.

### 4. Consequences Are Too High

| Domain | Why Not ML |
|--------|------------|
| Medical diagnosis (final) | Requires human oversight |
| Criminal sentencing | Explainability legally required |
| Autonomous weapons | Ethical prohibition |
| Nuclear safety | Human verification mandatory |

**ML can assist but not decide** in high-stakes domains.

### 5. Need 100% Accuracy

ML is probabilistic. Some errors are inherent.

| Requirement | Use Instead |
|-------------|-------------|
| No false positives ever | Rules + manual review |
| Every case must be correct | Human decision |
| Deterministic output | Algorithms, not ML |

### 6. Simpler Methods Work

| "ML Problem" | Simpler Solution |
|--------------|------------------|
| Recommend most popular items | Sort by sales |
| Predict next day's weather | Yesterday's weather |
| Segment customers | RFM analysis |
| Detect obvious spam | Keyword blocklist |
| Predict sales growth | Moving average |

**Always compute baseline**. If simple beats complex, stay simple.

---

## Decision Framework

```
┌──────────────────────────────────────────────────────┐
│ Can rules solve with 90%+ accuracy?                  │
│    YES → Use rules                                   │
│    NO ↓                                              │
├──────────────────────────────────────────────────────┤
│ Do you have enough labeled data?                     │
│    NO → Collect data first, use rules meanwhile      │
│    YES ↓                                             │
├──────────────────────────────────────────────────────┤
│ Is the pattern stable over time?                     │
│    NO → Rules + rapid human updates                  │
│    YES ↓                                             │
├──────────────────────────────────────────────────────┤
│ Are some errors acceptable?                          │
│    NO → Human decision required                      │
│    YES ↓                                             │
├──────────────────────────────────────────────────────┤
│ Does simple baseline get you 80% of the way?         │
│    YES → Consider if extra complexity is worth it    │
│    NO → ML likely appropriate                        │
└──────────────────────────────────────────────────────┘
```

---

## Alternatives to ML

### Rule Engines

For complex business logic that changes frequently.

```python
# Example: Drools-style rules in Python
class Rule:
    def __init__(self, condition, action, priority=0):
        self.condition = condition
        self.action = action
        self.priority = priority

rules = [
    Rule(
        lambda order: order.total > 10000,
        lambda order: order.flag('high_value'),
        priority=1
    ),
    Rule(
        lambda order: order.country in HIGH_RISK_COUNTRIES,
        lambda order: order.flag('geo_risk'),
        priority=2
    ),
]

def apply_rules(order, rules):
    for rule in sorted(rules, key=lambda r: -r.priority):
        if rule.condition(order):
            rule.action(order)
```

**Tools**: Drools, Easy Rules, custom engine

### Heuristics

Capture expert knowledge directly.

```python
def fraud_score(transaction):
    """Heuristic fraud scoring."""
    score = 0

    # Amount-based
    if transaction.amount > transaction.user.avg_amount * 3:
        score += 30
    if transaction.amount > 5000:
        score += 20

    # Velocity
    if transaction.user.transactions_last_hour > 5:
        score += 25

    # Geography
    if transaction.country != transaction.user.usual_country:
        score += 15

    # Time
    if transaction.hour in [2, 3, 4]:  # Late night
        score += 10

    return min(score, 100)
```

### Statistical Methods

Classical statistics often suffice.

| Task | Statistical Approach |
|------|---------------------|
| Detect outliers | Z-score, IQR |
| A/B test | t-test, chi-square |
| Trend analysis | Linear regression |
| Forecasting (simple) | Moving average, exponential smoothing |
| Correlation | Pearson/Spearman correlation |
| Grouping | Percentiles, quartiles |

### Human-in-the-Loop

ML assists, human decides.

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   ML Model    │────▶│   Human       │────▶│   Final       │
│   Suggests    │     │   Reviews     │     │   Decision    │
└───────────────┘     └───────────────┘     └───────────────┘
```

**When**: High stakes, need explainability, low volume.

### Lookup Tables

For known mappings.

```python
# Instead of ML to predict shipping cost
SHIPPING_RATES = {
    ('US', 'standard'): 5.99,
    ('US', 'express'): 12.99,
    ('CA', 'standard'): 9.99,
    # ...
}

def get_shipping(country, method):
    return SHIPPING_RATES.get((country, method), DEFAULT_RATE)
```

### Search and Ranking

For matching problems.

```python
# Instead of ML to "recommend similar products"
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# TF-IDF similarity (not ML, just math)
tfidf = TfidfVectorizer()
vectors = tfidf.fit_transform(product_descriptions)
similarity_matrix = cosine_similarity(vectors)
```

---

## The "ML Is Easy" Trap

### What ML Requires (Hidden Costs)

| Requirement | Effort |
|-------------|--------|
| Data collection and labeling | Weeks to months |
| Data cleaning and preprocessing | 60-80% of project time |
| Feature engineering | Iterative, requires domain knowledge |
| Model training and tuning | Days to weeks |
| Evaluation infrastructure | Proper metrics, A/B testing |
| Deployment infrastructure | APIs, serving, scaling |
| Monitoring and alerting | Drift detection, error tracking |
| Retraining pipeline | Periodic updates |
| Maintenance | Ongoing, indefinite |

### What Rules Require

| Requirement | Effort |
|-------------|--------|
| Domain expert interview | Hours |
| Implementation | Days |
| Testing | Days |
| Maintenance | On business logic change |

---

## Hybrid Approaches

Use ML where it helps, rules where they work.

### Cascade

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   Rules       │────▶│   ML Model    │────▶│   Human       │
│   (Fast, Cheap│     │   (Uncertain  │     │   (Complex    │
│    Clear)     │     │    Cases)     │     │    Cases)     │
└───────────────┘     └───────────────┘     └───────────────┘
```

Example:
1. Rules: Flag obvious spam (known bad words) → Reject
2. ML: Score uncertain emails → Accept/Reject if confident
3. Human: Review emails ML is unsure about

### ML-Assisted Rules

```python
def process_transaction(tx):
    # Rule: Clearly good
    if tx.amount < 10 and tx.user.verified:
        return 'approve'

    # Rule: Clearly bad
    if tx.user.account_age_days < 1 and tx.amount > 1000:
        return 'reject'

    # ML: Uncertain cases
    risk_score = ml_model.predict(tx)
    if risk_score < 0.3:
        return 'approve'
    elif risk_score > 0.8:
        return 'reject'
    else:
        return 'manual_review'
```

---

## Checklist: Should I Use ML?

### Use Rules If:
- [ ] Business logic is well-defined
- [ ] Expert can explain the decision
- [ ] Rules achieve 80%+ of target accuracy
- [ ] Need deterministic, explainable output
- [ ] Low data volume
- [ ] Patterns change faster than retraining

### Use ML If:
- [ ] Pattern is complex and data-driven
- [ ] Have sufficient labeled examples
- [ ] Some errors are acceptable
- [ ] Pattern is stable enough
- [ ] Can afford ongoing maintenance
- [ ] Rules are insufficient

### Start Simple Either Way:
- [ ] Try rule-based first
- [ ] Compute simple baselines
- [ ] Only add ML if measurably better
- [ ] Use simplest ML that works

---

## Case Studies

### Case 1: Email Spam

**Attempt**: Train ML classifier on spam/ham.

**Better Approach**:
1. Blocklist known bad domains (rule)
2. Keyword filter for known spam phrases (rule)
3. Sender reputation score (heuristic)
4. ML only for remaining uncertain emails

**Why**: 80% of spam is obvious. ML adds marginal value at high complexity.

### Case 2: Product Recommendations

**Attempt**: Build collaborative filtering system.

**Better Approach**:
1. Show best sellers (popularity)
2. Show recently viewed (recency)
3. Show same category (attribute match)
4. Only use ML for "you might also like"

**Why**: Users often want obvious recommendations. ML handles exploration.

### Case 3: Fraud Detection

**Attempt**: Anomaly detection ML model.

**Better Approach**:
1. Rules for known fraud patterns (velocity, geography, amount)
2. ML for novel pattern detection
3. Human review for borderline cases

**Why**: Known fraud patterns are well-defined. ML catches new patterns.

---

## Summary

| Situation | Recommendation |
|-----------|----------------|
| Rules work | Don't use ML |
| No data | Collect data, use rules meanwhile |
| Pattern unstable | Rules + rapid updates |
| Zero error tolerance | Human decision |
| Simple baseline wins | Stay simple |
| Complex, stable, data-rich, error-tolerant | ML appropriate |

---

## Further Reading

| Resource | Type | Notes |
|----------|------|-------|
| Rules of Machine Learning (Google) | Guide | When (not) to ML |
| No Free Lunch Theorem | Theory | No universal best model |
| KISS Principle | Philosophy | Keep It Simple, Stupid |
