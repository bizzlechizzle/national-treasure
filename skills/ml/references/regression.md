# Regression

Predict continuous numeric values from input features.

---

## When to Use

**You have**:
- Labeled examples (input → numeric value)
- Continuous target variable (price, duration, score, count)
- Relationship between features and target

**You want**:
- Predict numeric values for new inputs
- Understand feature impact on predictions
- Estimate prediction confidence/uncertainty

---

## Regression Types

| Type | Output | Example |
|------|--------|---------|
| **Standard regression** | Single continuous value | House price, salary prediction |
| **Count regression** | Non-negative integers | Number of orders, defect counts |
| **Quantile regression** | Percentiles of distribution | Median + confidence intervals |
| **Censored/survival** | Time-to-event with censoring | Customer lifetime, equipment failure |
| **Multi-output** | Multiple targets simultaneously | Predict latitude and longitude |

---

## Technique Selection

### Tabular Data

| Technique | When to Use | Pros | Cons |
|-----------|-------------|------|------|
| **Linear Regression** | Baseline, interpretability, linear relationships | Fast, interpretable, feature coefficients | Assumes linearity |
| **Ridge/Lasso** | Multicollinearity, feature selection | Regularization prevents overfitting | Still linear |
| **ElasticNet** | Mix of L1/L2 regularization | Balanced approach | Requires tuning alpha ratio |
| **Random Forest Regressor** | Non-linear, robust baseline | Handles non-linearity, feature importance | Slower, can't extrapolate |
| **XGBoost / LightGBM Regressor** | Best performance, complex patterns | SOTA for tabular, fast | Less interpretable |
| **CatBoost Regressor** | Categorical features | Native categorical handling | Slower than LightGBM |

**Default recommendation**: Linear Regression (baseline) → XGBoost/LightGBM (performance)

### Special Cases

| Case | Recommended Approach |
|------|---------------------|
| Target is always positive | Log-transform target, or use Tweedie regression |
| Target is a count (0, 1, 2...) | Poisson regression for low counts, standard for high counts |
| Need uncertainty estimates | Quantile regression, Bayesian methods, or ensemble variance |
| Target has outliers | Huber regression, or robust scaling |
| Heteroscedastic errors | Weighted regression, or model variance separately |

---

## Target Transformation

### When to Transform

| Symptom | Transformation | Implementation |
|---------|----------------|----------------|
| Right-skewed target (prices, counts) | Log transform | `np.log1p(y)`, inverse: `np.expm1(pred)` |
| Bounded target [0, 1] | Logit transform | `np.log(y / (1 - y))` |
| Heavy tails | Box-Cox or Yeo-Johnson | `PowerTransformer` from sklearn |
| Negative values + skew | Yeo-Johnson | Works with negatives |

### sklearn PowerTransformer

```python
from sklearn.compose import TransformedTargetRegressor
from sklearn.preprocessing import PowerTransformer

model = TransformedTargetRegressor(
    regressor=XGBRegressor(),
    transformer=PowerTransformer(method='yeo-johnson')
)
```

---

## Key Hyperparameters

### Linear Models

| Parameter | What It Does | Typical Values |
|-----------|--------------|----------------|
| `alpha` (Ridge/Lasso) | Regularization strength | 0.001, 0.01, 0.1, 1, 10 |
| `l1_ratio` (ElasticNet) | L1 vs L2 balance | 0.1, 0.5, 0.9 |
| `fit_intercept` | Include bias term | True (usually) |

### XGBoost / LightGBM

| Parameter | What It Does | Typical Values |
|-----------|--------------|----------------|
| `n_estimators` | Number of trees | 100-1000 |
| `max_depth` | Tree depth | 3-10 |
| `learning_rate` | Step size | 0.01-0.3 |
| `subsample` | Row sampling | 0.6-1.0 |
| `colsample_bytree` | Column sampling | 0.6-1.0 |
| `reg_alpha` | L1 regularization | 0, 0.1, 1, 10 |
| `reg_lambda` | L2 regularization | 0, 0.1, 1, 10 |

### Objective Functions

| Objective | Use When | XGBoost param |
|-----------|----------|---------------|
| MSE (default) | Standard regression, outliers not severe | `reg:squarederror` |
| MAE | Outliers present, care about median | `reg:absoluteerror` |
| Huber | Balance of MSE and MAE | `reg:pseudohubererror` |
| Poisson | Count data | `count:poisson` |
| Gamma | Positive continuous, right-skewed | `reg:gamma` |
| Tweedie | Insurance claims (many zeros + heavy tail) | `reg:tweedie` |

---

## Evaluation Metrics

| Metric | Use When | Interpretation |
|--------|----------|----------------|
| **MAE** (Mean Absolute Error) | Care about average error magnitude | Average $ off |
| **RMSE** (Root Mean Squared Error) | Large errors are worse | Penalizes outliers more |
| **MAPE** (Mean Absolute % Error) | Relative error matters | Average % off (beware zeros) |
| **R²** (Coefficient of Determination) | Explain variance vs baseline | 1 = perfect, 0 = mean baseline |
| **Adjusted R²** | Compare models with different features | Penalizes extra features |
| **Quantile Loss** | Specific percentile accuracy | For quantile regression |

### Metric Selection Guide

| Scenario | Primary Metric | Notes |
|----------|----------------|-------|
| All errors equally bad | MAE | Robust to outliers |
| Large errors especially bad | RMSE | Penalizes big misses |
| Need % interpretation | MAPE | Avoid if target has zeros |
| Comparing to baseline | R² | Can be negative if model worse |
| Predicting ranges | Quantile loss | For prediction intervals |

### Business-Aligned Metrics

Often better to create custom metrics aligned to business:

```python
def business_cost(y_true, y_pred):
    """Example: underestimating costs 2x as expensive as overestimating"""
    error = y_pred - y_true
    cost = np.where(error < 0, -2 * error, error)  # Penalize under-prediction
    return cost.mean()
```

---

## Feature Engineering Tips

### Numeric Features

| Technique | When to Use | Notes |
|-----------|-------------|-------|
| **Standardization** | Linear models | Mean=0, std=1 |
| **Log transform** | Skewed features | Handle zeros with log1p |
| **Polynomial features** | Non-linear relationships with linear model | Can explode feature space |
| **Binning** | Capture thresholds | Loss of information |
| **Ratios** | When ratio is meaningful | Price per sqft, rate per hour |

### Categorical Features

Same as classification — see `classification.md`.

### Interactions

```python
# Polynomial features with interaction only
from sklearn.preprocessing import PolynomialFeatures
poly = PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)
X_interact = poly.fit_transform(X)
```

### Domain-Specific

| Domain | Common Features |
|--------|-----------------|
| Real estate | Price per sqft, age of building, distance to amenities |
| Pricing | Competitor price ratio, days since last change |
| Finance | Rolling averages, volatility measures |
| Time-related | Day of week, month, holiday indicators |

---

## Handling Outliers

### Detection

```python
import numpy as np

# IQR method
Q1, Q3 = np.percentile(y, [25, 75])
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR
outliers = (y < lower_bound) | (y > upper_bound)

# Z-score method
z_scores = (y - y.mean()) / y.std()
outliers = np.abs(z_scores) > 3
```

### Strategies

| Strategy | When to Use | Notes |
|----------|-------------|-------|
| **Remove** | Outliers are errors | Loses real data |
| **Cap/Winsorize** | Keep observations, limit impact | Set to percentile boundary |
| **Robust scaling** | Preprocessing | Use median/IQR instead of mean/std |
| **Robust loss function** | Training | Huber, MAE instead of MSE |
| **Separate model** | Outliers have different pattern | Predict "is outlier" first |

---

## Prediction Intervals

For uncertainty quantification beyond point predictions.

### Quantile Regression

```python
from sklearn.ensemble import GradientBoostingRegressor

# Predict median
model_50 = GradientBoostingRegressor(loss='quantile', alpha=0.5)
# Predict 10th percentile
model_10 = GradientBoostingRegressor(loss='quantile', alpha=0.1)
# Predict 90th percentile
model_90 = GradientBoostingRegressor(loss='quantile', alpha=0.9)

# 80% prediction interval
lower = model_10.predict(X_test)
median = model_50.predict(X_test)
upper = model_90.predict(X_test)
```

### Ensemble Variance

```python
# With Random Forest
from sklearn.ensemble import RandomForestRegressor
rf = RandomForestRegressor(n_estimators=100)
rf.fit(X_train, y_train)

# Get predictions from each tree
tree_preds = np.array([tree.predict(X_test) for tree in rf.estimators_])
mean_pred = tree_preds.mean(axis=0)
std_pred = tree_preds.std(axis=0)

# Approximate 95% interval
lower = mean_pred - 1.96 * std_pred
upper = mean_pred + 1.96 * std_pred
```

### Conformal Prediction

```python
# pip install mapie
from mapie.regression import MapieRegressor

mapie = MapieRegressor(estimator=model, method='plus', cv=5)
mapie.fit(X_train, y_train)
y_pred, y_intervals = mapie.predict(X_test, alpha=0.1)  # 90% interval
```

---

## Libraries

### Primary

| Library | Use Case | Install |
|---------|----------|---------|
| **scikit-learn** | Linear models, RF, preprocessing | `pip install scikit-learn` |
| **XGBoost** | Gradient boosting | `pip install xgboost` |
| **LightGBM** | Fast gradient boosting | `pip install lightgbm` |
| **CatBoost** | Categorical-heavy data | `pip install catboost` |

### Specialized

| Library | Use Case | Install |
|---------|----------|---------|
| **statsmodels** | Statistical modeling, inference | `pip install statsmodels` |
| **MAPIE** | Conformal prediction intervals | `pip install mapie` |
| **optuna** | Hyperparameter tuning | `pip install optuna` |
| **SHAP** | Model explanation | `pip install shap` |

---

## Production Considerations

### Extrapolation Warning

Tree-based models cannot extrapolate beyond training data range. If target could exceed training range in production, consider:

1. Linear model for extrapolation regions
2. Hybrid approach (tree + linear)
3. Domain constraints post-prediction
4. Monitoring for out-of-range inputs

### Residual Analysis

Before deployment, check residuals:

```python
residuals = y_test - y_pred

# Should be: mean ≈ 0, no pattern vs predicted, normal-ish distribution
plt.scatter(y_pred, residuals)  # Should be random cloud
plt.hist(residuals)  # Should be roughly normal
```

Red flags:
- Residuals increase with prediction (heteroscedasticity)
- Clear pattern in residual plot (missing feature/nonlinearity)
- Heavy tails (outlier handling needed)

### Model Export

Same as classification — see `classification.md`.

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Not transforming skewed target | Poor performance, weird residuals | Log or Box-Cox transform |
| Using R² only | Good R² but bad predictions | Always check MAE/RMSE too |
| Ignoring outliers | Model distorted by extreme values | Robust loss or cap outliers |
| Extrapolation with trees | Wrong predictions outside training range | Use linear for extrapolation |
| Target leakage | Unrealistically good results | Audit feature sources |
| Multicollinearity (linear) | Unstable coefficients | Use Ridge, or remove correlated features |

---

## Checklist Before Production

- [ ] Baseline model (linear regression) trained and documented
- [ ] Target distribution examined, transformed if needed
- [ ] Residual analysis completed (no patterns, reasonable distribution)
- [ ] Outlier handling strategy documented
- [ ] Feature scaling consistent between train and predict
- [ ] Extrapolation behavior understood and handled
- [ ] Prediction interval method chosen if uncertainty needed
- [ ] Model serialization tested (save → load → predict)
- [ ] Business-aligned metric calculated, not just statistical metrics
- [ ] Monitoring plan for production drift

---

## Quick Start Code

```python
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

# Load and split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Transform target if skewed
if y_train.skew() > 1:
    y_train_log = np.log1p(y_train)
    y_test_log = np.log1p(y_test)
    use_log = True
else:
    y_train_log, y_test_log = y_train, y_test
    use_log = False

# Baseline: Ridge Regression
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

ridge = Ridge(alpha=1.0)
ridge.fit(X_train_scaled, y_train_log)
pred_ridge = ridge.predict(X_test_scaled)
if use_log:
    pred_ridge = np.expm1(pred_ridge)
print("Ridge Regression:")
print(f"  MAE: {mean_absolute_error(y_test, pred_ridge):.2f}")
print(f"  RMSE: {np.sqrt(mean_squared_error(y_test, pred_ridge)):.2f}")
print(f"  R²: {r2_score(y_test, pred_ridge):.3f}")

# Better: XGBoost
xgb_model = xgb.XGBRegressor(
    n_estimators=100,
    max_depth=5,
    learning_rate=0.1,
    objective='reg:squarederror'
)
xgb_model.fit(X_train, y_train_log)
pred_xgb = xgb_model.predict(X_test)
if use_log:
    pred_xgb = np.expm1(pred_xgb)
print("\nXGBoost:")
print(f"  MAE: {mean_absolute_error(y_test, pred_xgb):.2f}")
print(f"  RMSE: {np.sqrt(mean_squared_error(y_test, pred_xgb)):.2f}")
print(f"  R²: {r2_score(y_test, pred_xgb):.3f}")
```

---

## Further Reading

| Resource | Type | URL |
|----------|------|-----|
| scikit-learn Regression Guide | Official Docs | https://scikit-learn.org/stable/supervised_learning.html |
| XGBoost Regression | Official Docs | https://xgboost.readthedocs.io/ |
| Prediction Intervals | Tutorial | https://mapie.readthedocs.io/ |
| Target Transformation | Article | https://scikit-learn.org/stable/modules/compose.html#transforming-target-in-regression |
