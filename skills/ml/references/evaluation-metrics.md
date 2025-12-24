# Evaluation Metrics

How to measure model performance correctly.

---

## The Golden Rule

**Use the metric that matches your business goal.**

Optimizing the wrong metric leads to models that look good on paper but fail in production.

---

## Classification Metrics

### Confusion Matrix Foundation

```
                     Predicted
                  Positive  Negative
Actual Positive     TP        FN
Actual Negative     FP        TN

TP = True Positive (correct positive prediction)
TN = True Negative (correct negative prediction)
FP = False Positive (Type I error)
FN = False Negative (Type II error)
```

### Core Metrics

| Metric | Formula | Intuition |
|--------|---------|-----------|
| **Accuracy** | (TP+TN) / Total | % correct overall |
| **Precision** | TP / (TP+FP) | Of predicted positive, % correct |
| **Recall (Sensitivity)** | TP / (TP+FN) | Of actual positive, % caught |
| **Specificity** | TN / (TN+FP) | Of actual negative, % correct |
| **F1 Score** | 2 * (P*R) / (P+R) | Harmonic mean of precision/recall |

### When to Use What

| Metric | Use When | Example |
|--------|----------|---------|
| **Accuracy** | Classes balanced, all errors equal | Generic classification |
| **Precision** | False positives are costly | Spam filter (don't block good email) |
| **Recall** | False negatives are costly | Fraud detection (don't miss fraud) |
| **F1** | Need balance, classes imbalanced | Default for imbalanced |
| **Specificity** | Care about true negatives | Medical screening (don't alarm healthy) |

### Computation

```python
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)

# Basic metrics
accuracy = accuracy_score(y_true, y_pred)
precision = precision_score(y_true, y_pred)
recall = recall_score(y_true, y_pred)
f1 = f1_score(y_true, y_pred)

# Full report
print(classification_report(y_true, y_pred))

# Confusion matrix
cm = confusion_matrix(y_true, y_pred)
```

---

## Threshold-Independent Metrics

Evaluate model quality independent of classification threshold.

### AUC-ROC

Area Under Receiver Operating Characteristic Curve.

```
TPR (Recall) vs FPR (1-Specificity) at various thresholds
```

| AUC Value | Interpretation |
|-----------|----------------|
| 0.5 | Random (useless) |
| 0.6-0.7 | Poor |
| 0.7-0.8 | Fair |
| 0.8-0.9 | Good |
| 0.9-1.0 | Excellent |

**Intuition**: Probability that model ranks a random positive higher than random negative.

```python
from sklearn.metrics import roc_auc_score, roc_curve

# Compute AUC
auc = roc_auc_score(y_true, y_proba)

# Plot ROC curve
fpr, tpr, thresholds = roc_curve(y_true, y_proba)
plt.plot(fpr, tpr)
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate (Recall)')
```

### AUC-PR (Preferred for Imbalanced)

Area Under Precision-Recall Curve.

**Why PR over ROC for imbalanced data?**
- ROC can look good even when precision is terrible
- PR focuses on the positive class
- Better reflects real-world performance with rare events

```python
from sklearn.metrics import average_precision_score, precision_recall_curve

# Compute AP (equivalent to AUC-PR)
ap = average_precision_score(y_true, y_proba)

# Plot PR curve
precision, recall, thresholds = precision_recall_curve(y_true, y_proba)
plt.plot(recall, precision)
plt.xlabel('Recall')
plt.ylabel('Precision')
```

---

## Multiclass Metrics

### Averaging Strategies

| Strategy | How | When |
|----------|-----|------|
| **Micro** | Global TP/FP/FN, then metric | Imbalanced, care about overall |
| **Macro** | Metric per class, then average | Balanced, all classes equal importance |
| **Weighted** | Macro weighted by class frequency | Imbalanced, proportional importance |

```python
# Multiclass F1
f1_micro = f1_score(y_true, y_pred, average='micro')
f1_macro = f1_score(y_true, y_pred, average='macro')
f1_weighted = f1_score(y_true, y_pred, average='weighted')

# Per-class
f1_per_class = f1_score(y_true, y_pred, average=None)
```

### One-vs-Rest AUC

```python
from sklearn.preprocessing import label_binarize
from sklearn.metrics import roc_auc_score

# Binarize labels
y_true_bin = label_binarize(y_true, classes=[0, 1, 2])

# OvR AUC
auc_ovr = roc_auc_score(y_true_bin, y_proba, multi_class='ovr')
```

---

## Regression Metrics

### Core Metrics

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **MAE** | mean(\|y - ŷ\|) | Average absolute error |
| **MSE** | mean((y - ŷ)²) | Average squared error |
| **RMSE** | sqrt(MSE) | Error in same units as target |
| **MAPE** | mean(\|y - ŷ\| / \|y\|) * 100 | Average % error |
| **R²** | 1 - (SS_res / SS_tot) | Variance explained (0-1) |

### When to Use What

| Metric | Use When | Notes |
|--------|----------|-------|
| **MAE** | All errors equally bad | Robust to outliers |
| **RMSE** | Large errors are worse | Penalizes big mistakes |
| **MAPE** | Need % interpretation | Fails if target has zeros |
| **R²** | Compare to baseline | Can be negative if model is worse than mean |

### Computation

```python
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    mean_absolute_percentage_error
)
import numpy as np

mae = mean_absolute_error(y_true, y_pred)
mse = mean_squared_error(y_true, y_pred)
rmse = np.sqrt(mse)
mape = mean_absolute_percentage_error(y_true, y_pred)
r2 = r2_score(y_true, y_pred)
```

### Custom Metrics

```python
def symmetric_mape(y_true, y_pred):
    """sMAPE: handles zeros better than MAPE."""
    return 100 * np.mean(
        2 * np.abs(y_true - y_pred) / (np.abs(y_true) + np.abs(y_pred) + 1e-8)
    )

def business_cost(y_true, y_pred):
    """Example: underestimating costs 2x more than overestimating."""
    error = y_pred - y_true
    cost = np.where(error < 0, -2 * error, error)  # 2x penalty for under
    return cost.mean()
```

---

## Ranking Metrics

### NDCG (Normalized Discounted Cumulative Gain)

```python
def ndcg_at_k(relevance, k):
    """
    relevance: list of relevance scores in predicted order
    k: cutoff
    """
    import numpy as np

    relevance = np.array(relevance)[:k]
    # DCG
    gains = 2 ** relevance - 1
    discounts = np.log2(np.arange(2, len(relevance) + 2))
    dcg = np.sum(gains / discounts)
    # IDCG (ideal DCG)
    ideal = np.sort(relevance)[::-1]
    ideal_gains = 2 ** ideal - 1
    ideal_discounts = np.log2(np.arange(2, len(ideal) + 2))
    idcg = np.sum(ideal_gains / ideal_discounts)

    return dcg / idcg if idcg > 0 else 0
```

### MAP (Mean Average Precision)

```python
def average_precision(y_true, y_scores):
    """AP for a single query."""
    from sklearn.metrics import precision_recall_curve
    precision, recall, _ = precision_recall_curve(y_true, y_scores)
    return np.sum(np.diff(recall) * precision[:-1])

# MAP = mean AP across all queries
```

### MRR (Mean Reciprocal Rank)

```python
def reciprocal_rank(y_true, y_pred_order):
    """RR: 1/rank of first relevant item."""
    for i, item in enumerate(y_pred_order):
        if y_true[item] == 1:
            return 1 / (i + 1)
    return 0

# MRR = mean RR across queries
```

---

## Calibration

**Are predicted probabilities meaningful?**

A model predicting 70% should be correct 70% of the time.

### Checking Calibration

```python
from sklearn.calibration import calibration_curve
import matplotlib.pyplot as plt

# Compute calibration curve
prob_true, prob_pred = calibration_curve(y_true, y_proba, n_bins=10)

# Plot
plt.plot(prob_pred, prob_true, 's-', label='Model')
plt.plot([0, 1], [0, 1], '--', label='Perfect')
plt.xlabel('Mean Predicted Probability')
plt.ylabel('Fraction of Positives')
plt.legend()
```

### Fixing Calibration

```python
from sklearn.calibration import CalibratedClassifierCV

# Isotonic regression (non-parametric)
calibrated = CalibratedClassifierCV(model, method='isotonic', cv=5)
calibrated.fit(X_train, y_train)

# Platt scaling (logistic)
calibrated = CalibratedClassifierCV(model, method='sigmoid', cv=5)
```

### Brier Score

Measures calibration and accuracy together (lower is better).

```python
from sklearn.metrics import brier_score_loss

brier = brier_score_loss(y_true, y_proba)
# 0 = perfect, 0.25 = random guessing (for balanced binary)
```

---

## Cross-Validation

Never evaluate on training data. Use CV for robust estimates.

### Standard K-Fold

```python
from sklearn.model_selection import cross_val_score, KFold

kf = KFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(model, X, y, cv=kf, scoring='f1')
print(f"F1: {scores.mean():.3f} (+/- {scores.std()*2:.3f})")
```

### Stratified K-Fold (Classification)

Maintains class proportions in each fold.

```python
from sklearn.model_selection import StratifiedKFold

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(model, X, y, cv=skf, scoring='f1')
```

### Time Series CV

```python
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5)
scores = cross_val_score(model, X, y, cv=tscv, scoring='neg_mean_absolute_error')
```

### Group K-Fold

When samples belong to groups (e.g., users).

```python
from sklearn.model_selection import GroupKFold

gkf = GroupKFold(n_splits=5)
for train_idx, test_idx in gkf.split(X, y, groups=user_ids):
    # No user appears in both train and test
    pass
```

---

## Metric Selection Guide

### By Problem Type

| Problem | Primary Metric | Secondary |
|---------|----------------|-----------|
| Binary classification (balanced) | Accuracy, F1 | AUC-ROC |
| Binary classification (imbalanced) | F1, AUC-PR | Precision, Recall |
| Multiclass | Macro F1, Weighted F1 | Per-class metrics |
| Regression | RMSE, MAE | R², residual plots |
| Ranking | NDCG, MAP | MRR, Precision@K |
| Recommendation | Recall@K, NDCG | Coverage, Diversity |
| Forecasting | MAE, RMSE | MAPE, MASE |
| Anomaly detection | Precision, Recall, F1 | AUC-PR |

### By Business Context

| Context | Optimize For | Metric Choice |
|---------|--------------|---------------|
| High false positive cost | Precision | High precision, acceptable recall |
| High false negative cost | Recall | High recall, acceptable precision |
| Customer-facing | Calibration | Brier score, calibration curve |
| A/B testing | Business outcome | Conversion rate, revenue, engagement |
| Model comparison | Statistical significance | Paired t-test on CV scores |

---

## Statistical Significance

### Comparing Models

```python
from scipy import stats

# Paired t-test on CV scores
scores_a = cross_val_score(model_a, X, y, cv=10)
scores_b = cross_val_score(model_b, X, y, cv=10)

t_stat, p_value = stats.ttest_rel(scores_a, scores_b)
print(f"p-value: {p_value:.4f}")
# p < 0.05 → statistically significant difference
```

### Confidence Intervals

```python
import numpy as np

def bootstrap_metric(y_true, y_pred, metric_fn, n_bootstrap=1000):
    """Bootstrap confidence interval for a metric."""
    scores = []
    n = len(y_true)
    for _ in range(n_bootstrap):
        idx = np.random.choice(n, n, replace=True)
        score = metric_fn(y_true[idx], y_pred[idx])
        scores.append(score)
    return np.percentile(scores, [2.5, 97.5])

# Example
lower, upper = bootstrap_metric(y_true, y_pred, f1_score)
print(f"F1: {f1_score(y_true, y_pred):.3f} (95% CI: {lower:.3f}-{upper:.3f})")
```

---

## Common Mistakes

| Mistake | Why It's Wrong | Fix |
|---------|----------------|-----|
| Accuracy on imbalanced | Majority class dominates | Use F1, AUC-PR |
| Evaluate on train set | Overestimates performance | Use held-out test or CV |
| Wrong averaging (multi) | Micro vs macro matter | Choose based on goals |
| Ignoring calibration | Probabilities are meaningless | Check calibration |
| Single number focus | Hides failure modes | Look at confusion matrix |
| No statistical test | Could be noise | Test significance |

---

## Checklist

- [ ] Metric matches business goal
- [ ] Appropriate for class balance
- [ ] Cross-validation used (not single split)
- [ ] Confidence intervals computed
- [ ] Calibration checked if probabilities used
- [ ] Confusion matrix reviewed
- [ ] Error analysis on failures
- [ ] Comparison to baseline documented
- [ ] Statistical significance tested

---

## Quick Reference

```python
# Classification
from sklearn.metrics import classification_report, roc_auc_score
print(classification_report(y_true, y_pred))
auc = roc_auc_score(y_true, y_proba)

# Regression
from sklearn.metrics import mean_absolute_error, r2_score
mae = mean_absolute_error(y_true, y_pred)
r2 = r2_score(y_true, y_pred)

# Cross-validation
from sklearn.model_selection import cross_val_score
scores = cross_val_score(model, X, y, cv=5, scoring='f1')
print(f"{scores.mean():.3f} +/- {scores.std()*2:.3f}")
```

---

## Further Reading

| Resource | Type | URL |
|----------|------|-----|
| sklearn Metrics Guide | Docs | https://scikit-learn.org/stable/modules/model_evaluation.html |
| Beyond Accuracy | Paper | https://arxiv.org/abs/2006.16236 |
| Calibration of Probabilities | Article | https://scikit-learn.org/stable/modules/calibration.html |
| Cross-Validation Guide | Docs | https://scikit-learn.org/stable/modules/cross_validation.html |
