# Data Requirements

How much data you need, what quality matters, and how to prepare it.

---

## The Fundamental Question

**How much data do I need?**

Short answer: More than you think, less than people claim.

Real answer: It depends on:
- Problem complexity
- Model complexity
- Class balance
- Signal-to-noise ratio
- Acceptable error rate

---

## Data Volume Guidelines

### By Problem Type

| Problem Type | Minimum Viable | Recommended | Ideal |
|--------------|----------------|-------------|-------|
| **Binary Classification** | 100 per class | 1,000 per class | 10,000+ per class |
| **Multiclass (10 classes)** | 50 per class | 500 per class | 5,000+ per class |
| **Regression** | 100 total | 1,000 total | 10,000+ total |
| **Anomaly Detection** | 1,000 normal | 10,000 normal | 100,000+ normal |
| **Time Series Forecasting** | 2 seasonal cycles | 5 cycles | 10+ cycles |
| **Text Classification** | 100 per class | 1,000 per class | 10,000+ per class |
| **Clustering** | 10x features | 100x features | 1,000x features |
| **Recommendations** | 1,000 interactions | 100,000 interactions | 1M+ interactions |
| **Ranking** | 1,000 query-doc pairs | 10,000 pairs | 100,000+ pairs |

### By Model Complexity

| Model | Data Needed | Notes |
|-------|-------------|-------|
| **Linear models** | Least | Can work with 100s |
| **Tree ensembles** | Moderate | 1,000s usually enough |
| **Shallow neural nets** | More | 10,000s typical |
| **Deep neural nets** | Most | 100,000s to millions |
| **Transformers (from scratch)** | Massive | Millions+ |
| **Fine-tuned transformers** | Less | 100s to 1,000s per class |

### Rules of Thumb

```
# Features rule
samples > 10 * features  # Minimum
samples > 50 * features  # Recommended

# Deep learning rule
samples > 5000 * parameters (in millions)  # Very rough

# Classes rule (classification)
samples_per_class > 50  # Minimum
samples_per_class > 500 # Recommended
```

---

## Data Quality Factors

### What Matters Most (Ranked)

1. **Label quality** — Wrong labels hurt more than missing data
2. **Representativeness** — Training must match production distribution
3. **Feature completeness** — Critical features shouldn't be missing
4. **Freshness** — Stale data for dynamic domains is useless
5. **Balance** — Extreme imbalance causes problems

### Label Quality

| Issue | Impact | Detection | Fix |
|-------|--------|-----------|-----|
| Mislabeled data | Model learns wrong patterns | Cross-validation variance, human audit | Clean labels, confident learning |
| Inconsistent labeling | Ceiling on accuracy | Inter-annotator agreement | Clear guidelines, arbitration |
| Noisy labels | Increased variance | Learning curves don't converge | Label smoothing, robust loss |
| Subjective labels | Lower accuracy ceiling | High disagreement | Multiple annotators, soft labels |

**Label audit process:**

```python
# Sample and manually review
sample = df.sample(100)
for idx, row in sample.iterrows():
    print(f"Features: {row['features']}")
    print(f"Current label: {row['label']}")
    # Human review: is label correct?

# Check inter-annotator agreement
from sklearn.metrics import cohen_kappa_score
kappa = cohen_kappa_score(annotator1_labels, annotator2_labels)
# > 0.8: good agreement
# < 0.6: problematic
```

### Representativeness

**Training data must match production data.**

| Mismatch | Example | Symptom |
|----------|---------|---------|
| Temporal | Trained on 2023, deployed 2024 | Degradation over time |
| Geographic | Trained on US, deployed in EU | Poor performance in new region |
| Demographic | Trained on one segment | Biased predictions |
| Distribution | Training has different class ratios | Poor calibration |

**Check distribution:**

```python
# Compare train vs production distributions
from scipy.stats import ks_2samp

for col in features:
    stat, pvalue = ks_2samp(train[col], production[col])
    if pvalue < 0.05:
        print(f"WARNING: {col} distribution differs significantly")
```

---

## Missing Data

### Types of Missingness

| Type | Meaning | Example | Implication |
|------|---------|---------|-------------|
| **MCAR** | Missing completely at random | Random sensor failures | Safe to drop or impute |
| **MAR** | Missing depends on observed data | Higher earners skip income question | Impute with caution |
| **MNAR** | Missing depends on the value itself | Sickest patients miss appointments | Missingness is informative |

### Handling Strategies

| Strategy | When to Use | How |
|----------|-------------|-----|
| **Drop rows** | MCAR, small % missing | `df.dropna()` |
| **Drop columns** | >50% missing, not critical | Remove feature |
| **Mean/median impute** | Numeric, MCAR | `SimpleImputer(strategy='median')` |
| **Mode impute** | Categorical, MCAR | `SimpleImputer(strategy='most_frequent')` |
| **Missing indicator** | Missingness is informative | Add boolean column `is_missing_X` |
| **Model-based** | MAR, complex patterns | `IterativeImputer` (MICE) |
| **Tree native** | Using XGBoost/LightGBM | Let model handle (built-in) |

```python
from sklearn.impute import SimpleImputer
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer

# Simple imputation
imputer = SimpleImputer(strategy='median')
X_imputed = imputer.fit_transform(X)

# Add missing indicator
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

# Pipeline with indicator
imputer = SimpleImputer(strategy='median', add_indicator=True)

# Advanced: MICE (multiple imputation)
mice_imputer = IterativeImputer(random_state=42, max_iter=10)
X_mice = mice_imputer.fit_transform(X)
```

---

## Data Leakage

**The silent model killer.** Your validation looks great, production fails.

### Types of Leakage

| Type | What Happens | Example |
|------|--------------|---------|
| **Target leakage** | Feature contains target info | `account_closed_date` to predict churn |
| **Training-test contamination** | Test info leaks to training | Normalize before split |
| **Future leakage** | Using future info | Features from after event |

### Prevention

```python
# WRONG: fit on all data, then split
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)  # LEAKS TEST INFO
X_train, X_test = train_test_split(X_scaled)

# RIGHT: fit only on train
X_train, X_test = train_test_split(X)
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)  # Fit on train
X_test = scaler.transform(X_test)        # Transform only

# BEST: use Pipeline
from sklearn.pipeline import Pipeline
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('model', LogisticRegression())
])
# Pipeline handles it correctly
pipeline.fit(X_train, y_train)
```

### Leakage Detection

| Symptom | Likely Cause |
|---------|--------------|
| Validation >> production performance | Leakage |
| Feature importance on impossible feature | Target leakage |
| Perfect or near-perfect accuracy | Usually leakage |
| Simple model beats complex | Leaky feature |

```python
# Audit high-importance features
importances = model.feature_importances_
for feat, imp in sorted(zip(features, importances), key=lambda x: -x[1])[:10]:
    print(f"{feat}: {imp:.4f}")
    # Ask: Could this feature be known at prediction time?
    # Ask: Does this feature encode the target?
```

---

## Train/Test Splitting

### Standard Split

```python
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y  # For classification
)
```

### Time Series Split

**Never shuffle time series!**

```python
# Simple temporal split
train = df[df['date'] < '2024-01-01']
test = df[df['date'] >= '2024-01-01']

# Time series cross-validation
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5)
for train_idx, test_idx in tscv.split(X):
    # Train on past, test on future
    X_train, X_test = X[train_idx], X[test_idx]
```

### Group-Based Split

When samples are related (e.g., multiple samples per user).

```python
from sklearn.model_selection import GroupShuffleSplit, GroupKFold

# Don't let same user appear in train and test
gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train_idx, test_idx = next(gss.split(X, y, groups=user_ids))

# Cross-validation with groups
gkf = GroupKFold(n_splits=5)
for train_idx, test_idx in gkf.split(X, y, groups=user_ids):
    pass
```

---

## Class Imbalance

### Measuring Imbalance

```python
import pandas as pd

# Imbalance ratio
counts = y.value_counts()
imbalance_ratio = counts.max() / counts.min()

# Interpretation
# 1:1 to 3:1 - Balanced to mild
# 3:1 to 10:1 - Moderate imbalance
# 10:1 to 100:1 - Severe
# > 100:1 - Extreme
```

### Handling Strategies

| Strategy | When | Implementation |
|----------|------|----------------|
| **Do nothing** | Ratio < 3:1 | Just monitor metrics |
| **Class weights** | Moderate imbalance | `class_weight='balanced'` |
| **Oversample minority** | Need more minority examples | SMOTE, ADASYN |
| **Undersample majority** | Majority is huge | RandomUnderSampler |
| **Threshold tuning** | At inference time | Adjust decision boundary |
| **Change metric** | Accuracy is misleading | Use F1, AUC-PR |

```python
# Class weights
from sklearn.linear_model import LogisticRegression
model = LogisticRegression(class_weight='balanced')

# SMOTE oversampling
from imblearn.over_sampling import SMOTE
smote = SMOTE(random_state=42)
X_resampled, y_resampled = smote.fit_resample(X_train, y_train)

# Combined over+under sampling
from imblearn.combine import SMOTETomek
smt = SMOTETomek(random_state=42)
X_resampled, y_resampled = smt.fit_resample(X_train, y_train)
```

---

## Feature Scaling

### When to Scale

| Model | Scaling Needed |
|-------|----------------|
| Linear models | **Yes** — coefficients depend on scale |
| SVM | **Yes** — distance-based |
| KNN | **Yes** — distance-based |
| Neural networks | **Yes** — optimization stability |
| Tree-based (RF, XGBoost) | **No** — split-based, scale invariant |
| Naive Bayes | **No** — probability-based |

### Scaling Methods

| Method | Formula | When to Use |
|--------|---------|-------------|
| **StandardScaler** | (x - mean) / std | Default for most cases |
| **MinMaxScaler** | (x - min) / (max - min) | Need bounded [0,1] output |
| **RobustScaler** | (x - median) / IQR | Outliers present |
| **MaxAbsScaler** | x / max(abs) | Sparse data |
| **None** | — | Tree-based models |

```python
from sklearn.preprocessing import StandardScaler, RobustScaler

# Fit on train only
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Save scaler for production
import joblib
joblib.dump(scaler, 'scaler.pkl')
```

---

## Categorical Encoding

### Encoding Methods

| Method | When | Notes |
|--------|------|-------|
| **One-hot** | Low cardinality (< 20) | Explodes features |
| **Label encoding** | Tree models, ordinal | Order matters |
| **Target encoding** | High cardinality | Leakage risk |
| **Frequency encoding** | High cardinality | No leakage |
| **Binary encoding** | Medium cardinality | Compact |
| **Hash encoding** | Very high cardinality | Collisions possible |

```python
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from category_encoders import TargetEncoder

# One-hot (low cardinality)
ohe = OneHotEncoder(sparse=False, handle_unknown='ignore')
X_encoded = ohe.fit_transform(X[['category']])

# Target encoding (high cardinality) - use cross-validation
te = TargetEncoder(cols=['category'])
te.fit(X_train, y_train)
X_train_encoded = te.transform(X_train)
X_test_encoded = te.transform(X_test)
```

---

## Data Pipelines

### Why Pipelines

- Prevent leakage (fit only on train)
- Reproducible preprocessing
- Easy to deploy
- Integrate with cross-validation

### sklearn Pipeline

```python
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer

# Define column types
numeric_features = ['age', 'income']
categorical_features = ['category', 'region']

# Numeric pipeline
numeric_transformer = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())
])

# Categorical pipeline
categorical_transformer = Pipeline([
    ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
    ('encoder', OneHotEncoder(handle_unknown='ignore'))
])

# Combine
preprocessor = ColumnTransformer([
    ('num', numeric_transformer, numeric_features),
    ('cat', categorical_transformer, categorical_features)
])

# Full pipeline
pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('model', XGBClassifier())
])

# Fit and predict
pipeline.fit(X_train, y_train)
predictions = pipeline.predict(X_test)

# Save entire pipeline
joblib.dump(pipeline, 'model_pipeline.pkl')
```

---

## Data Validation Checklist

### Before Training

- [ ] No data leakage (future info, target encoding)
- [ ] Train/test split is appropriate (temporal, grouped)
- [ ] Missing values handled
- [ ] Outliers understood and handled
- [ ] Class balance assessed
- [ ] Feature distributions examined
- [ ] Labels audited for quality

### Before Deployment

- [ ] Production data distribution matches training
- [ ] Same preprocessing pipeline used
- [ ] Missing value handling works for production
- [ ] Out-of-range values handled
- [ ] New categories handled (unknown in categorical)

---

## Quick Checklist by Problem

### Classification

- [ ] Enough samples per class (100+ minimum)
- [ ] Labels are correct (audit sample)
- [ ] Class imbalance assessed
- [ ] Stratified train/test split

### Regression

- [ ] Target distribution examined (transform if skewed)
- [ ] Outliers in target handled
- [ ] Feature scaling applied

### Time Series

- [ ] No shuffle in split
- [ ] Enough historical data (2+ cycles minimum)
- [ ] Features don't use future data

### Text

- [ ] Text is clean (encoding issues, noise)
- [ ] Labels are consistent
- [ ] Representative of production text

---

## Common Data Mistakes

| Mistake | Consequence | Prevention |
|---------|-------------|------------|
| Random split for time series | Overfit, fails in production | Use temporal splits |
| Scale before split | Data leakage | Use pipelines |
| Ignore class imbalance | Model predicts majority only | Use appropriate metrics, resampling |
| Use test set for tuning | Overfit to test | Hold out true test set |
| Collect biased sample | Unfair, inaccurate | Audit data collection |
| Assume labels are correct | Ceiling on accuracy | Audit labels |

---

## Further Reading

| Resource | Type | URL |
|----------|------|-----|
| sklearn Preprocessing Guide | Docs | https://scikit-learn.org/stable/modules/preprocessing.html |
| Imbalanced-learn | Library | https://imbalanced-learn.org/ |
| Feature Engine | Library | https://feature-engine.readthedocs.io/ |
| Data Leakage | Article | https://machinelearningmastery.com/data-leakage-machine-learning/ |
