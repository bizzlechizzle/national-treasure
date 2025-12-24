# Classification

Predict discrete categories from input features.

---

## When to Use

**You have**:
- Labeled examples (input → category)
- Discrete, predefined outcome categories
- Enough examples per category (50+ minimum, 500+ preferred)

**You want**:
- Predict which category new inputs belong to
- Probability estimates for each category
- Understand what drives predictions

---

## Classification Types

| Type | Output | Example |
|------|--------|---------|
| **Binary** | Yes/No, 0/1 | Churn prediction, spam detection, fraud |
| **Multiclass** | One of N categories | Product categorization, intent classification |
| **Multilabel** | Multiple categories per item | Article tags, symptoms, movie genres |
| **Ordinal** | Ordered categories | Rating (1-5), severity (Low/Med/High) |

---

## Technique Selection

### Tabular Data (Structured, Rows/Columns)

| Technique | When to Use | Pros | Cons |
|-----------|-------------|------|------|
| **Logistic Regression** | Baseline, interpretability required, linear relationships | Fast, interpretable, probabilistic | Limited to linear boundaries |
| **Random Forest** | General purpose, feature importance needed | Robust, handles missing data, interpretable | Slower inference than linear |
| **XGBoost / LightGBM** | Best performance needed, tabular data | SOTA for tabular, fast training | Less interpretable, requires tuning |
| **CatBoost** | Categorical features, minimal preprocessing | Native categorical handling, robust | Slower than LightGBM |
| **TabNet** | Want deep learning on tabular, built-in feature selection | Attention-based interpretability | Needs more data, GPU helpful |
| **FT-Transformer** | Large datasets, complex patterns | SOTA on some tabular benchmarks | Requires significant data, GPU |

**Default recommendation**: Start with Logistic Regression (baseline) → XGBoost/LightGBM (performance)

### Text Data

See `text-classification.md` for detailed guidance.

| Technique | When to Use | Pros | Cons |
|-----------|-------------|------|------|
| **TF-IDF + Logistic Regression** | Baseline, limited compute | Fast, interpretable, works with little data | Misses semantics |
| **TF-IDF + XGBoost** | Better performance, still simple | Handles feature interactions | Misses semantics |
| **DistilBERT fine-tuned** | Semantic understanding needed | Captures meaning, transfer learning | GPU needed, slower |
| **SetFit** | Few labeled examples | Few-shot learning, efficient | Newer, less established |

**Default recommendation**: TF-IDF + Logistic Regression (baseline) → DistilBERT if semantics matter

---

## Handling Class Imbalance

Common in fraud detection, rare disease diagnosis, churn prediction.

### Diagnosis

```python
# Check imbalance ratio
value_counts = y.value_counts()
imbalance_ratio = value_counts.max() / value_counts.min()
# Ratio > 10:1 = significant imbalance
# Ratio > 100:1 = severe imbalance
```

### Strategies

| Strategy | When to Use | Implementation |
|----------|-------------|----------------|
| **Class weights** | Moderate imbalance, want simplicity | `class_weight='balanced'` in sklearn |
| **Stratified sampling** | Always for train/test split | `stratify=y` in train_test_split |
| **SMOTE oversampling** | Need more minority samples, tabular data | `imblearn.over_sampling.SMOTE` |
| **Undersampling** | Majority class is huge, speed matters | `imblearn.under_sampling.RandomUnderSampler` |
| **Threshold adjustment** | Tune precision/recall tradeoff | Adjust decision threshold post-training |
| **Ensemble resampling** | Best results, more complex | Train multiple models on balanced subsets |

**Do NOT use accuracy as metric with imbalanced data** — use precision, recall, F1, or AUC.

---

## Key Hyperparameters

### Logistic Regression

| Parameter | What It Does | Typical Values |
|-----------|--------------|----------------|
| `C` | Inverse regularization strength | 0.001, 0.01, 0.1, 1, 10 |
| `penalty` | Regularization type | 'l1', 'l2', 'elasticnet' |
| `class_weight` | Handle imbalance | 'balanced' or dict |

### XGBoost / LightGBM

| Parameter | What It Does | Typical Values |
|-----------|--------------|----------------|
| `n_estimators` | Number of trees | 100-1000 |
| `max_depth` | Tree depth | 3-10 |
| `learning_rate` | Step size | 0.01-0.3 |
| `subsample` | Row sampling | 0.6-1.0 |
| `colsample_bytree` | Column sampling | 0.6-1.0 |
| `scale_pos_weight` | Imbalance handling | n_negative / n_positive |

### Tuning Strategy

1. Start with defaults
2. Tune `n_estimators` and `learning_rate` together
3. Tune `max_depth` and `min_child_weight`
4. Tune `subsample` and `colsample_bytree`
5. Use `early_stopping_rounds` to prevent overfitting

**Tool recommendation**: `optuna` for Bayesian optimization, `sklearn.model_selection.RandomizedSearchCV` for quick tuning.

---

## Evaluation Metrics

| Metric | Use When | Formula Intuition |
|--------|----------|-------------------|
| **Accuracy** | Balanced classes only | % correct predictions |
| **Precision** | False positives are costly (spam filter) | Of predicted positive, how many correct? |
| **Recall** | False negatives are costly (fraud, disease) | Of actual positive, how many caught? |
| **F1 Score** | Balance precision and recall | Harmonic mean of precision/recall |
| **AUC-ROC** | Ranking quality, threshold-independent | Probability of ranking positive higher |
| **AUC-PR** | Imbalanced data, focus on positive class | Area under precision-recall curve |
| **Log Loss** | Probability calibration matters | Penalizes confident wrong predictions |

### Metric Selection Guide

| Scenario | Primary Metric | Secondary |
|----------|----------------|-----------|
| Balanced classes | Accuracy or F1 | Confusion matrix |
| Imbalanced classes | F1 or AUC-PR | Precision, Recall |
| Ranking matters | AUC-ROC | Precision@K |
| Probabilities used downstream | Log Loss | Calibration plot |
| Business cost known | Custom cost function | Confusion matrix |

See `evaluation-metrics.md` for detailed guidance.

---

## Feature Engineering Tips

### Categorical Features

| Technique | When to Use | Notes |
|-----------|-------------|-------|
| **One-hot encoding** | Low cardinality (<20 values) | Can explode feature space |
| **Target encoding** | High cardinality, tree models | Risk of leakage, use cross-validated |
| **Frequency encoding** | Simple alternative to target | Less prone to overfitting |
| **CatBoost native** | Using CatBoost | Best for high cardinality |

### Numeric Features

| Technique | When to Use | Notes |
|-----------|-------------|-------|
| **Standardization** | Linear models, distance-based | Mean=0, std=1 |
| **Min-max scaling** | Neural networks, bounded output needed | Range [0,1] |
| **Log transform** | Skewed distributions | Handle after removing zeros |
| **Binning** | Non-linear relationships with linear model | Loses information |

### Missing Values

| Technique | When to Use | Notes |
|-----------|-------------|-------|
| **Mean/median imputation** | Quick, few missing | Can distort distribution |
| **Missing indicator** | Missingness is informative | Add boolean feature |
| **XGBoost native** | Using tree models | Learns optimal direction |
| **Multiple imputation** | Statistical rigor needed | More complex |

---

## Libraries

### Primary

| Library | Use Case | Install |
|---------|----------|---------|
| **scikit-learn** | General ML, baselines, preprocessing | `pip install scikit-learn` |
| **XGBoost** | Gradient boosting | `pip install xgboost` |
| **LightGBM** | Fast gradient boosting | `pip install lightgbm` |
| **CatBoost** | Categorical-heavy data | `pip install catboost` |

### Supporting

| Library | Use Case | Install |
|---------|----------|---------|
| **imbalanced-learn** | Resampling for imbalanced data | `pip install imbalanced-learn` |
| **optuna** | Hyperparameter tuning | `pip install optuna` |
| **SHAP** | Model explanation | `pip install shap` |
| **pandas** | Data manipulation | `pip install pandas` |

---

## Production Considerations

### Threshold Selection

Default threshold (0.5) rarely optimal. Select based on:

1. **Precision-recall tradeoff** — Plot PR curve, choose point
2. **Business cost** — If FP costs $1 and FN costs $100, optimize accordingly
3. **F1 maximization** — Find threshold that maximizes F1

```python
from sklearn.metrics import precision_recall_curve
precision, recall, thresholds = precision_recall_curve(y_true, y_proba)
# Choose threshold based on requirements
```

### Calibration

Predicted probabilities should match true frequencies. Check and fix:

```python
from sklearn.calibration import calibration_curve, CalibratedClassifierCV

# Check calibration
prob_true, prob_pred = calibration_curve(y_true, y_proba, n_bins=10)

# Fix with isotonic regression or Platt scaling
calibrated = CalibratedClassifierCV(model, method='isotonic')
```

### Model Export

| Format | Use Case | Library |
|--------|----------|---------|
| **joblib/pickle** | Same Python environment | `joblib.dump(model, 'model.pkl')` |
| **ONNX** | Cross-platform, fast inference | `skl2onnx` |
| **PMML** | Enterprise systems | `sklearn2pmml` |

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Data leakage | Unrealistically good validation scores | Check feature sources, temporal ordering |
| Fitting on test data | Preprocessing before split | Create pipeline, fit on train only |
| Ignoring imbalance | High accuracy, low minority recall | Use appropriate metrics, resampling |
| Over-tuning | Great validation, poor production | Hold out true test set, cross-validate |
| Ignoring calibration | Probabilities used but not calibrated | Check calibration curve, calibrate |

---

## Checklist Before Production

- [ ] Baseline model (logistic regression) trained and documented
- [ ] Best model outperforms baseline meaningfully
- [ ] Evaluation metrics appropriate for problem (not just accuracy)
- [ ] Class imbalance addressed if present
- [ ] Feature pipeline reproducible and tested
- [ ] Model predictions validated against business logic
- [ ] Calibration checked if probabilities used downstream
- [ ] Threshold selected intentionally, not defaulted
- [ ] Model serialization tested (save → load → predict)
- [ ] Monitoring plan for production drift

---

## Quick Start Code

```python
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score
import xgboost as xgb

# Load and split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Baseline: Logistic Regression
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

lr = LogisticRegression(class_weight='balanced', max_iter=1000)
lr.fit(X_train_scaled, y_train)
print("Logistic Regression:")
print(classification_report(y_test, lr.predict(X_test_scaled)))

# Better: XGBoost
xgb_model = xgb.XGBClassifier(
    n_estimators=100,
    max_depth=5,
    learning_rate=0.1,
    scale_pos_weight=(y_train == 0).sum() / (y_train == 1).sum(),
    eval_metric='auc',
    use_label_encoder=False
)
xgb_model.fit(X_train, y_train)
print("\nXGBoost:")
print(classification_report(y_test, xgb_model.predict(X_test)))
print(f"AUC: {roc_auc_score(y_test, xgb_model.predict_proba(X_test)[:, 1]):.3f}")
```

---

## Further Reading

| Resource | Type | URL |
|----------|------|-----|
| scikit-learn Classification Guide | Official Docs | https://scikit-learn.org/stable/supervised_learning.html |
| XGBoost Documentation | Official Docs | https://xgboost.readthedocs.io/ |
| Imbalanced Classification | Tutorial | https://machinelearningmastery.com/tactics-to-combat-imbalanced-classes-in-your-machine-learning-dataset/ |
| SHAP Values Explained | Paper | https://arxiv.org/abs/1705.07874 |
