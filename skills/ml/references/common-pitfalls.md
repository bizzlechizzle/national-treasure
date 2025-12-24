# Common ML Pitfalls

Mistakes that sink ML projects—and how to avoid them.

---

## Data Pitfalls

### 1. Data Leakage

**What**: Information from the future or target leaks into features.

**Symptoms**:
- Unrealistically high validation scores
- Model fails in production
- One feature dominates importance

**Examples**:
```python
# WRONG: Feature derived from target
df['will_churn'] = ...  # target
df['churn_reason'] = ...  # Only exists AFTER churn → LEAK

# WRONG: Future information
df['next_month_purchases'] = ...  # Not available at prediction time

# WRONG: Target-encoded without CV
df['category_target_mean'] = df.groupby('category')['target'].transform('mean')
# Leaks test target means into features
```

**Prevention**:
- Ask "Would this feature be available at prediction time?"
- Use pipelines (fit preprocessing on train only)
- Audit suspiciously important features

---

### 2. Training-Serving Skew

**What**: Features computed differently in training vs production.

**Examples**:
- Different library versions
- Different aggregation windows
- Different missing value handling
- Different feature definitions

**Prevention**:
```python
# Use same preprocessing pipeline
pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('model', model)
])
joblib.dump(pipeline, 'full_pipeline.pkl')

# In production
pipeline = joblib.load('full_pipeline.pkl')
predictions = pipeline.predict(new_data)
```

---

### 3. Label Quality Issues

**What**: Labels are noisy, inconsistent, or wrong.

**Impact**: Model learns wrong patterns, accuracy ceiling.

**Detection**:
```python
# Check inter-annotator agreement
from sklearn.metrics import cohen_kappa_score
kappa = cohen_kappa_score(annotator1, annotator2)
# < 0.6 is problematic

# Sample and manually audit
sample = df.sample(100)
# Review each: is the label correct?
```

**Prevention**:
- Clear labeling guidelines
- Multiple annotators with arbitration
- Audit samples before training
- Consider "confident learning" to detect mislabels

---

### 4. Sample Selection Bias

**What**: Training data doesn't represent production.

**Examples**:
- Only successful outcomes (survivorship bias)
- Over-represented demographics
- Only labeled easy cases
- Historical data from different era

**Detection**:
```python
# Compare distributions
from scipy.stats import ks_2samp
for col in features:
    stat, p = ks_2samp(train[col], production[col])
    if p < 0.05:
        print(f"Distribution shift: {col}")
```

**Prevention**:
- Stratified sampling
- Time-based validation
- Regular distribution monitoring

---

## Modeling Pitfalls

### 5. Overfitting

**What**: Model memorizes training data, doesn't generalize.

**Symptoms**:
- Training accuracy >> validation accuracy
- Model complexity increases without validation improvement
- Learning curves diverge

**Detection**:
```python
# Learning curve
from sklearn.model_selection import learning_curve

train_sizes, train_scores, val_scores = learning_curve(
    model, X, y, cv=5, train_sizes=[0.2, 0.4, 0.6, 0.8, 1.0]
)

# Plot: if train >> val, overfitting
plt.plot(train_sizes, train_scores.mean(axis=1), label='Train')
plt.plot(train_sizes, val_scores.mean(axis=1), label='Validation')
```

**Prevention**:
- Regularization (L1, L2, dropout)
- Early stopping
- More training data
- Simpler model
- Cross-validation

---

### 6. Underfitting

**What**: Model is too simple to capture patterns.

**Symptoms**:
- Training accuracy is low
- Both train and validation are similar but poor
- Model doesn't beat simple baseline

**Prevention**:
- More complex model
- Better features
- Less regularization
- Ensure data has signal

---

### 7. Class Imbalance Ignored

**What**: Rare class gets poor predictions.

**Symptoms**:
- High accuracy (all predict majority class)
- Near-zero recall for minority class
- Model predicts same class always

**Prevention**:
```python
# Check imbalance
print(y.value_counts(normalize=True))

# Use appropriate metrics
from sklearn.metrics import classification_report
print(classification_report(y_true, y_pred))
# Look at per-class metrics, not just accuracy

# Handle imbalance
model = XGBClassifier(scale_pos_weight=imbalance_ratio)
# Or SMOTE, class weights, etc.
```

---

### 8. Wrong Metric

**What**: Optimizing metric that doesn't match business goal.

**Examples**:
- Accuracy on imbalanced data (should use F1, AUC-PR)
- RMSE when business cares about % error (should use MAPE)
- Global metrics when per-segment matters

**Prevention**:
- Define business metric FIRST
- Map to technical metric
- Always check confusion matrix / error distribution

---

### 9. Not Having a Baseline

**What**: No comparison point for model performance.

**Why It Matters**:
- Can't tell if ML adds value
- May be worse than simple rules
- Wasted effort on marginal improvements

**Baselines to Always Compute**:
| Problem | Baseline |
|---------|----------|
| Classification | Predict majority class |
| Regression | Predict mean/median |
| Time series | Naive (last value), seasonal naive |
| Ranking | Random, popularity-based |
| Recommendations | Most popular items |

---

## Validation Pitfalls

### 10. Random Split for Time Series

**What**: Shuffling time series data for train/test split.

**Why It's Wrong**: Leaks future information to training.

**Correct Approach**:
```python
# WRONG
X_train, X_test = train_test_split(X, shuffle=True)

# RIGHT
train = df[df['date'] < '2024-01-01']
test = df[df['date'] >= '2024-01-01']

# Or TimeSeriesSplit for CV
from sklearn.model_selection import TimeSeriesSplit
tscv = TimeSeriesSplit(n_splits=5)
```

---

### 11. Leaking Through Groups

**What**: Same user/entity in train and test.

**Why It's Wrong**: Model learns user-specific patterns, not generalizable ones.

**Correct Approach**:
```python
from sklearn.model_selection import GroupKFold

gkf = GroupKFold(n_splits=5)
for train_idx, test_idx in gkf.split(X, y, groups=user_ids):
    # Users are completely separated
    pass
```

---

### 12. Using Test Set for Tuning

**What**: Using test set to select hyperparameters.

**Why It's Wrong**: Overfits to test set, optimistic estimates.

**Correct Approach**:
```
Data = Train + Validation + Test

1. Train models on Train
2. Select best on Validation
3. Final evaluation on Test (once!)
```

Or use nested cross-validation.

---

## Production Pitfalls

### 13. No Monitoring

**What**: Model deployed but not tracked.

**Consequences**:
- Silent failures
- Undetected drift
- Degrading performance

**What to Monitor**:
```python
# Input distribution
for feature in features:
    log_distribution_stats(feature, X)

# Prediction distribution
log_prediction_distribution(predictions)

# Performance (if labels available)
log_metrics(y_true, y_pred)

# Latency
log_inference_time(duration)
```

---

### 14. Model Drift

**What**: Model performance degrades over time.

**Types**:
- **Data drift**: Input distribution changes
- **Concept drift**: Relationship between inputs and target changes

**Detection**:
```python
# PSI (Population Stability Index)
def calculate_psi(expected, actual, bins=10):
    expected_perc = np.histogram(expected, bins=bins)[0] / len(expected)
    actual_perc = np.histogram(actual, bins=bins)[0] / len(actual)
    psi = np.sum((actual_perc - expected_perc) * np.log(actual_perc / expected_perc + 1e-10))
    return psi
# PSI > 0.2 indicates significant drift
```

**Prevention**:
- Monitor continuously
- Scheduled retraining
- Automatic alerts on drift

---

### 15. No Fallback

**What**: System fails completely when model fails.

**Prevention**:
```python
def predict_with_fallback(features):
    try:
        prediction = model.predict(features)
        if prediction is None or np.isnan(prediction):
            raise ValueError("Invalid prediction")
        return prediction
    except Exception as e:
        log_error(e)
        return default_prediction  # Fallback: mean, popular, rule-based
```

---

### 16. Ignoring Latency

**What**: Model too slow for production requirements.

**Prevention**:
- Profile inference time during development
- Test under load
- Use appropriate model complexity
- Consider ONNX, quantization

```python
import time

# Measure latency
start = time.time()
for _ in range(1000):
    model.predict(X_sample)
latency_ms = (time.time() - start)
print(f"Average latency: {latency_ms:.2f}ms")
```

---

## Process Pitfalls

### 17. Scope Creep

**What**: Project grows beyond original goals.

**Signs**:
- "Let's also add..."
- "While we're at it..."
- "Can the model also predict..."

**Prevention**:
- Define success criteria upfront
- Stick to scope
- Phase 2 is a separate project

---

### 18. Premature Optimization

**What**: Optimizing before understanding the problem.

**Signs**:
- Jump straight to neural networks
- Complex feature engineering without baseline
- Tuning hyperparameters before data is clean

**Correct Order**:
1. Understand the problem
2. Get clean data
3. Simple baseline
4. Simple ML model
5. Complex model (if needed)
6. Optimization (if needed)

---

### 19. Not Versioning

**What**: Can't reproduce results or roll back.

**What to Version**:
- Code (git)
- Data (DVC, Delta Lake)
- Models (MLflow, W&B)
- Experiments (MLflow, Comet)

```python
import mlflow

with mlflow.start_run():
    mlflow.log_params(params)
    mlflow.log_metrics(metrics)
    mlflow.sklearn.log_model(model, "model")
```

---

### 20. Poor Communication

**What**: Stakeholders don't understand limitations.

**Common Miscommunications**:
- "100% accuracy" expectations
- Not explaining confidence/uncertainty
- Overpromising timelines
- Not clarifying what the model CAN'T do

**Prevention**:
- Set realistic expectations early
- Explain model limitations
- Report confidence intervals
- Define failure modes

---

## Quick Checklist

### Before Training
- [ ] Data leakage audited
- [ ] Label quality checked
- [ ] Class balance examined
- [ ] Baseline computed

### During Training
- [ ] Train/val/test properly split
- [ ] Correct metric for problem
- [ ] Cross-validation used
- [ ] Overfitting monitored

### Before Deployment
- [ ] Preprocessing pipeline saved with model
- [ ] Latency tested
- [ ] Fallback implemented
- [ ] Monitoring configured

### After Deployment
- [ ] Input distribution monitored
- [ ] Prediction distribution monitored
- [ ] Performance tracked (if labels available)
- [ ] Retraining schedule defined

---

## Pitfall Severity Matrix

| Pitfall | Likelihood | Impact | Priority |
|---------|------------|--------|----------|
| Data leakage | High | Critical | Fix immediately |
| No baseline | Very High | High | Always compute |
| Wrong metric | High | High | Define early |
| Class imbalance ignored | High | High | Check always |
| No monitoring | High | Critical | Add before deploy |
| Random time series split | Medium | Critical | Never do |
| Overfitting | High | Medium | Use regularization |
| Training-serving skew | Medium | High | Use pipelines |

---

## Further Reading

| Resource | Type | Notes |
|----------|------|-------|
| Reliable ML (Google) | Book | Production ML patterns |
| ML Test Score (Google) | Paper | ML system testing |
| Hidden Technical Debt | Paper | ML systems debt |
| Sculley et al. | Paper | ML anti-patterns |
