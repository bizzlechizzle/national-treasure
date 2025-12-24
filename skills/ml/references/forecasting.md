# Forecasting

Predict future values from historical time series data.

---

## When to Use

**You have**:
- Historical observations over time (dates/timestamps)
- Regular or irregular time intervals
- At least 2 complete seasonal cycles (preferably 5+)

**You want**:
- Predict future values (sales, demand, traffic, etc.)
- Understand trend and seasonal patterns
- Plan for capacity, inventory, resources

**Consider Regression instead if**:
- No temporal structure matters
- Predicting based on features, not time

---

## Forecasting Types

| Type | Description | Example |
|------|-------------|---------|
| **Univariate** | Predict from history of single series | Forecast sales from past sales |
| **Multivariate** | Multiple related series together | Forecast sales + inventory together |
| **With exogenous** | Include external drivers | Sales + promotions + holidays |
| **Hierarchical** | Related series at different levels | Store → Region → National |

---

## Technique Selection

### Quick Selector

| Situation | Technique | Why |
|-----------|-----------|-----|
| Quick baseline | Naive (last value), Seasonal Naive | Fast sanity check |
| Strong seasonality + trend | Prophet, ETS | Built for seasonal decomposition |
| Complex patterns, lots of data | N-BEATS, TFT | Deep learning SOTA |
| Multiple series, shared patterns | Global models (LightGBM, TFT) | Learn across series |
| Need uncertainty intervals | Prophet, Quantile regression | Built-in uncertainty |
| Minimal data (< 2 years) | ETS, ARIMA | Statistical, needs less data |
| Real-time, streaming | ETS online, Moving average | Incremental updates |

### Detailed Comparison

| Technique | Data Needed | Handles | Pros | Cons |
|-----------|-------------|---------|------|------|
| **Naive/Seasonal Naive** | Minimal | Baseline only | Always works, sets benchmark | No learning |
| **Moving Average** | Minimal | Level | Simple, interpretable | Lags trend |
| **Exponential Smoothing (ETS)** | 2+ seasons | Trend, seasonality | Statistically grounded | Single series |
| **ARIMA/SARIMA** | 2+ seasons | Trend, seasonality, correlation | Classic, well-understood | Assumes stationarity |
| **Prophet** | 2+ seasons | Trend, multi-seasonality, holidays, outliers | Robust, handles gaps, uncertainty | Facebook dependency |
| **LightGBM (with features)** | Moderate | Complex patterns, exogenous | Fast, handles many features | Feature engineering required |
| **N-BEATS** | Lots (1000+ series or long history) | Complex patterns | SOTA interpretable deep learning | Needs significant data |
| **TFT (Temporal Fusion Transformer)** | Lots | Everything + attention-based interpretability | SOTA with exogenous, uncertainty | Complex, GPU needed |
| **DeepAR** | Lots (many series) | Probabilistic, global | Uncertainty quantification | AWS-oriented |

---

## Baseline: Always Start Here

Before any complex model, establish baselines:

### Naive Methods

```python
import numpy as np

# Naive: predict last observed value
def naive_forecast(y, horizon):
    return np.repeat(y[-1], horizon)

# Seasonal Naive: predict same period last season
def seasonal_naive(y, horizon, season_length=12):
    return np.tile(y[-season_length:], horizon // season_length + 1)[:horizon]

# Moving Average
def moving_average(y, horizon, window=12):
    avg = y[-window:].mean()
    return np.repeat(avg, horizon)
```

### Why Baselines Matter

- If complex model can't beat naive, problem isn't forecastable (or model is wrong)
- Seasonal naive is surprisingly strong for seasonal data
- Sets expectations for what's achievable

---

## Prophet (Recommended for Most Cases)

Facebook's forecasting tool. Handles seasonality, holidays, missing data, outliers.

### When to Use

- Daily/weekly/monthly data with seasonality
- Missing data or irregular intervals
- Need holiday effects
- Want uncertainty intervals
- Don't need cutting-edge accuracy

### Key Components

```
y(t) = trend(t) + seasonality(t) + holidays(t) + error(t)
```

### Basic Usage

```python
from prophet import Prophet
import pandas as pd

# Data must have 'ds' (datestamp) and 'y' (value) columns
df = pd.DataFrame({
    'ds': dates,
    'y': values
})

model = Prophet(
    yearly_seasonality=True,
    weekly_seasonality=True,
    daily_seasonality=False,  # Only if sub-daily data
    changepoint_prior_scale=0.05,  # Trend flexibility
    seasonality_prior_scale=10  # Seasonality flexibility
)

# Add holidays
model.add_country_holidays(country_name='US')

# Add custom regressors (exogenous variables)
model.add_regressor('promotion', mode='multiplicative')

model.fit(df)

# Forecast
future = model.make_future_dataframe(periods=30)
future['promotion'] = promotion_values  # If using regressor
forecast = model.predict(future)

# Uncertainty intervals
forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
```

### Tuning Prophet

| Parameter | What It Does | Tune If |
|-----------|--------------|---------|
| `changepoint_prior_scale` | Trend flexibility | Trend over/underfitting (0.001 - 0.5) |
| `seasonality_prior_scale` | Seasonality strength | Seasonality too strong/weak (0.01 - 10) |
| `holidays_prior_scale` | Holiday effect size | Holiday spikes over/underfitting |
| `seasonality_mode` | Additive vs multiplicative | Series magnitude changes with level |

---

## Gradient Boosting for Time Series

LightGBM/XGBoost with time-based feature engineering. Surprisingly effective.

### Feature Engineering (Critical)

| Category | Features |
|----------|----------|
| **Lag features** | y(t-1), y(t-7), y(t-14), y(t-365) |
| **Rolling stats** | Mean/std/min/max of last 7, 14, 30 days |
| **Date features** | Day of week, month, quarter, year, is_weekend |
| **Cyclical encoding** | sin/cos of day, month (for continuity) |
| **Trend** | Days since start, cumulative count |
| **External** | Holidays, promotions, weather, events |

### Implementation

```python
import lightgbm as lgb
import numpy as np
import pandas as pd

def create_features(df, target_col='y', lags=[1, 7, 14, 28]):
    """Create time series features."""
    df = df.copy()

    # Lag features
    for lag in lags:
        df[f'lag_{lag}'] = df[target_col].shift(lag)

    # Rolling features
    for window in [7, 14, 28]:
        df[f'rolling_mean_{window}'] = df[target_col].shift(1).rolling(window).mean()
        df[f'rolling_std_{window}'] = df[target_col].shift(1).rolling(window).std()

    # Date features
    df['dayofweek'] = df['date'].dt.dayofweek
    df['month'] = df['date'].dt.month
    df['quarter'] = df['date'].dt.quarter
    df['dayofyear'] = df['date'].dt.dayofyear
    df['is_weekend'] = df['dayofweek'].isin([5, 6]).astype(int)

    # Cyclical encoding
    df['dayofweek_sin'] = np.sin(2 * np.pi * df['dayofweek'] / 7)
    df['dayofweek_cos'] = np.cos(2 * np.pi * df['dayofweek'] / 7)
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)

    return df.dropna()

# Train/test split (NEVER shuffle time series!)
train = df[df['date'] < '2024-01-01']
test = df[df['date'] >= '2024-01-01']

# Train model
feature_cols = [c for c in train.columns if c not in ['date', 'y']]
model = lgb.LGBMRegressor(n_estimators=100, learning_rate=0.1)
model.fit(train[feature_cols], train['y'])

# Recursive prediction for multi-step forecast
def recursive_forecast(model, last_data, steps, feature_cols):
    predictions = []
    current = last_data.copy()

    for _ in range(steps):
        pred = model.predict(current[feature_cols].values.reshape(1, -1))[0]
        predictions.append(pred)
        # Update features for next step (simplified)
        # In practice, update lag features with new prediction

    return predictions
```

---

## Deep Learning: N-BEATS and TFT

For when you need maximum accuracy and have data.

### N-BEATS

Neural Basis Expansion Analysis for Time Series. Interpretable deep learning.

```python
# Using darts library
from darts import TimeSeries
from darts.models import NBEATSModel

series = TimeSeries.from_dataframe(df, 'date', 'y')
train, val = series.split_before(0.8)

model = NBEATSModel(
    input_chunk_length=30,   # Look-back window
    output_chunk_length=7,   # Forecast horizon
    n_epochs=100,
    random_state=42
)
model.fit(train, val_series=val)
forecast = model.predict(7)
```

### Temporal Fusion Transformer (TFT)

State-of-the-art for complex forecasting with exogenous variables.

```python
from darts.models import TFTModel

model = TFTModel(
    input_chunk_length=30,
    output_chunk_length=7,
    hidden_size=64,
    attention_head_size=4,
    dropout=0.1,
    n_epochs=100
)
model.fit(train, val_series=val, past_covariates=past_cov, future_covariates=future_cov)
```

---

## Evaluation Metrics

| Metric | Formula Intuition | Use When |
|--------|-------------------|----------|
| **MAE** | Average absolute error | General purpose |
| **RMSE** | Root mean squared error | Large errors worse |
| **MAPE** | Mean absolute percentage error | % interpretation needed |
| **sMAPE** | Symmetric MAPE | Avoids MAPE asymmetry |
| **MASE** | Scaled vs naive baseline | Comparing across series |
| **RMSSE** | Scaled RMSE vs naive | M5 competition standard |

### Metric Selection

| Situation | Metric |
|-----------|--------|
| Single series, same scale | MAE or RMSE |
| Comparing across series | MASE or RMSSE |
| Business wants % error | MAPE (but beware zeros!) |
| Probabilistic forecast | CRPS, quantile loss |

### Cross-Validation for Time Series

**NEVER use random splits for time series!**

```python
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5)
scores = []
for train_idx, test_idx in tscv.split(X):
    # Train on past, test on future
    model.fit(X[train_idx], y[train_idx])
    pred = model.predict(X[test_idx])
    scores.append(metric(y[test_idx], pred))
```

---

## Handling Challenges

### Seasonality

| Pattern | Solution |
|---------|----------|
| Single seasonality (yearly) | Prophet, SARIMA, ETS |
| Multiple (daily + weekly + yearly) | Prophet, Fourier features + ML |
| Complex/irregular | Deep learning (TFT, N-BEATS) |

### Trend

| Pattern | Solution |
|---------|----------|
| Linear trend | Include time feature, Prophet, ETS |
| Changing trend | Prophet with changepoints, piecewise |
| Exponential growth | Log-transform first |

### Missing Data

| Approach | When |
|----------|------|
| Forward fill | Short gaps, stable series |
| Interpolation | Short gaps, smooth series |
| Prophet (native) | Any gaps, handles well |
| Imputation model | Long gaps, complex patterns |

### Outliers

| Approach | When |
|----------|------|
| Winsorize | Extreme but valid values |
| Remove and impute | Clearly erroneous |
| Robust models | Can't identify which are outliers |
| Separate outlier model | Outliers have pattern |

---

## Multiple Time Series

### Global vs Local Models

| Approach | What It Means | Pros | Cons |
|----------|---------------|------|------|
| **Local** | One model per series | Captures individual patterns | Can't learn across series |
| **Global** | One model, all series | Learns shared patterns, data efficient | May miss individual quirks |
| **Hybrid** | Global + local adjustments | Best of both | More complex |

### Global Model Example

```python
# Stack all series, add series identifier as feature
df['series_id'] = series_identifier
# Train single LightGBM on all series
# Learns patterns shared across series
```

### Hierarchical Forecasting

When series have structure (store → region → national):

1. **Bottom-up**: Forecast lowest level, aggregate up
2. **Top-down**: Forecast top level, distribute down
3. **Middle-out**: Forecast middle level, reconcile both ways
4. **Reconciliation**: Forecast all levels, make consistent

```python
# Using hierarchicalforecast library
from hierarchicalforecast.core import HierarchicalReconciliation
from hierarchicalforecast.methods import BottomUp, MinTrace
```

---

## Libraries

### Primary

| Library | Use Case | Install |
|---------|----------|---------|
| **Prophet** | Seasonal forecasting with holidays | `pip install prophet` |
| **statsmodels** | ARIMA, ETS, statistical models | `pip install statsmodels` |
| **darts** | Unified forecasting interface, deep learning | `pip install darts` |
| **sktime** | Scikit-learn compatible forecasting | `pip install sktime` |

### Deep Learning

| Library | Use Case | Install |
|---------|----------|---------|
| **pytorch-forecasting** | TFT, DeepAR | `pip install pytorch-forecasting` |
| **GluonTS** | Probabilistic forecasting | `pip install gluonts` |
| **NeuralProphet** | Prophet + neural network | `pip install neuralprophet` |

### Specialized

| Library | Use Case | Install |
|---------|----------|---------|
| **hierarchicalforecast** | Hierarchical reconciliation | `pip install hierarchicalforecast` |
| **STUMPY** | Matrix profile for patterns | `pip install stumpy` |

---

## Production Considerations

### Forecast Horizon

| Horizon | Accuracy | Use Case |
|---------|----------|----------|
| 1 step (next day) | Highest | Operational decisions |
| Short (1-4 weeks) | High | Inventory, staffing |
| Medium (1-3 months) | Moderate | Budget planning |
| Long (6+ months) | Lower | Strategic planning |

**Rule of thumb**: Accuracy degrades as horizon increases. Don't expect monthly accuracy for year-out forecasts.

### Retraining Cadence

| Data Frequency | Retrain |
|----------------|---------|
| Daily | Weekly or bi-weekly |
| Weekly | Monthly |
| Monthly | Quarterly |

Also retrain when:
- Forecast error increases significantly
- Major external event (pandemic, etc.)
- Business fundamentals change

### Monitoring

| What to Monitor | Why |
|-----------------|-----|
| Forecast error over time | Detect drift |
| Bias (over/under-predicting) | Systematic errors |
| Error by segment | Some products harder to forecast |
| Actual vs predicted distribution | Distribution shift |

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Random train/test split | Overly optimistic results | Time-based splits only |
| Using future data | Unrealistic accuracy | Audit feature creation carefully |
| Ignoring seasonality | Repeated systematic errors | Add seasonal components/features |
| Too long horizon | Low accuracy | Match horizon to business need |
| Single-point forecast only | No uncertainty | Use prediction intervals |
| Forgetting external factors | Miss promotions, holidays | Add exogenous variables |
| Not updating model | Degrading accuracy | Regular retraining |

---

## Checklist Before Production

- [ ] Naive baseline computed and documented
- [ ] Train/test split is time-based (not random)
- [ ] Seasonality patterns identified and modeled
- [ ] External factors (holidays, promotions) included
- [ ] Forecast horizon matches business need
- [ ] Prediction intervals provided, not just point forecast
- [ ] Cross-validation performed with time series splits
- [ ] Error metrics appropriate for use case
- [ ] Retraining schedule defined
- [ ] Monitoring for forecast degradation planned

---

## Quick Start Code

```python
import pandas as pd
import numpy as np
from prophet import Prophet
from sklearn.metrics import mean_absolute_error

# Prepare data
df = pd.DataFrame({
    'ds': dates,
    'y': values
})

# Train/test split (last 30 days for test)
train = df[df['ds'] < df['ds'].max() - pd.Timedelta(days=30)]
test = df[df['ds'] >= df['ds'].max() - pd.Timedelta(days=30)]

# Baseline: Seasonal Naive (same day last week)
seasonal_naive_pred = train.set_index('ds')['y'].shift(7).reindex(test['ds']).values
print(f"Seasonal Naive MAE: {mean_absolute_error(test['y'], seasonal_naive_pred):.2f}")

# Prophet
model = Prophet(yearly_seasonality=True, weekly_seasonality=True)
model.add_country_holidays(country_name='US')
model.fit(train)

future = model.make_future_dataframe(periods=30)
forecast = model.predict(future)

# Evaluate
prophet_pred = forecast.set_index('ds').loc[test['ds'], 'yhat'].values
print(f"Prophet MAE: {mean_absolute_error(test['y'], prophet_pred):.2f}")

# Visualize
fig = model.plot(forecast)
fig2 = model.plot_components(forecast)
```

---

## Further Reading

| Resource | Type | URL |
|----------|------|-----|
| Prophet Documentation | Official Docs | https://facebook.github.io/prophet/ |
| Forecasting: Principles and Practice | Textbook (free) | https://otexts.com/fpp3/ |
| Darts Documentation | Library | https://unit8co.github.io/darts/ |
| M5 Competition | Benchmark | https://www.kaggle.com/c/m5-forecasting-accuracy |
| Temporal Fusion Transformer Paper | Research | https://arxiv.org/abs/1912.09363 |
