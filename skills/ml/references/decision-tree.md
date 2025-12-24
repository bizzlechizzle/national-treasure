# ML Problem Type Decision Tree

Navigate from your goal to the right ML approach.

---

## Quick Decision Flow

```
What do you want to predict?
│
├─► A CATEGORY (discrete outcome)
│   │
│   ├─► Known categories, labeled examples exist
│   │   └─► CLASSIFICATION → classification.md
│   │
│   └─► Unknown groups, find structure in data
│       └─► CLUSTERING → clustering.md
│
├─► A NUMBER (continuous value)
│   │
│   ├─► Single point prediction
│   │   └─► REGRESSION → regression.md
│   │
│   └─► Future values over time
│       └─► FORECASTING → forecasting.md
│
├─► UNUSUAL ITEMS (outliers, fraud, defects)
│   └─► ANOMALY DETECTION → anomaly-detection.md
│
├─► RELEVANCE ORDER (ranked list)
│   │
│   ├─► Items for a specific user
│   │   └─► RECOMMENDATION → recommendation.md
│   │
│   └─► Items for a query/context
│       └─► RANKING → ranking.md
│
└─► TEXT CATEGORY (sentiment, topic, intent)
    └─► TEXT CLASSIFICATION → text-classification.md
```

---

## Detailed Decision Matrix

### By Goal

| I want to... | Examples | Problem Type |
|--------------|----------|--------------|
| Predict yes/no | Churn, fraud, click, spam | Binary Classification |
| Predict one of N categories | Product category, department, priority | Multiclass Classification |
| Predict multiple labels per item | Article tags, symptoms, genres | Multilabel Classification |
| Predict a numeric value | Price, duration, score | Regression |
| Predict future values | Sales next month, stock price, demand | Forecasting |
| Find outliers/anomalies | Fraud detection, defect detection, intrusion | Anomaly Detection |
| Group similar items | Customer segments, document clusters | Clustering |
| Suggest items to users | Product recommendations, content personalization | Recommendation |
| Order items by relevance | Search ranking, feed ordering | Ranking |
| Categorize text | Sentiment, intent, topic | Text Classification |

### By Data Type

| Data Type | Common Problems | Recommended Approaches |
|-----------|-----------------|----------------------|
| **Tabular** (rows/columns) | Classification, Regression, Anomaly | Tree ensembles, Linear models |
| **Time series** (sequential, temporal) | Forecasting, Anomaly | ARIMA, Prophet, TFT, N-BEATS |
| **Text** (unstructured) | Classification, Clustering | Transformers, TF-IDF + classical ML |
| **User-item interactions** | Recommendation, Ranking | Collaborative filtering, Matrix factorization |
| **Graph/network** | Node classification, Link prediction | GNNs (if needed), Feature engineering + classical |

---

## Common Confusion Points

### Classification vs Regression

| Question | Classification | Regression |
|----------|---------------|------------|
| Output type | Discrete categories | Continuous number |
| Example | Will customer churn? (yes/no) | How much will customer spend? ($X.XX) |
| Evaluation | Accuracy, F1, AUC | MAE, RMSE, R² |

**Edge case**: Predicting a count (0, 1, 2, 3...) — Usually regression, but classification if counts are few and meaningful categories.

### Regression vs Forecasting

| Question | Regression | Forecasting |
|----------|------------|-------------|
| Time involved? | No temporal component | Predicting future based on past |
| Input features | Arbitrary features | Historical values + time features |
| Example | Predict house price from features | Predict next month's sales from history |
| Special concerns | Feature engineering | Seasonality, trend, stationarity |

### Classification vs Anomaly Detection

| Question | Classification | Anomaly Detection |
|----------|---------------|-------------------|
| Labeled anomalies? | Yes, many examples | Few or no labeled anomalies |
| Class balance | Can be imbalanced but workable | Extreme imbalance (99%+ normal) |
| Anomaly types | Known, defined categories | Unknown, novel patterns |
| Example | Classify fraud by type | Detect previously unseen fraud patterns |

**Decision**: If you have many labeled anomaly examples → Classification. If anomalies are rare/unknown → Anomaly Detection.

### Clustering vs Classification

| Question | Clustering | Classification |
|----------|------------|----------------|
| Labels exist? | No predefined categories | Yes, labeled training data |
| Goal | Discover structure | Predict known categories |
| Example | Find customer segments | Assign customers to segments |
| Output | Group assignments (learned) | Category predictions (predefined) |

### Recommendation vs Ranking

| Question | Recommendation | Ranking |
|----------|----------------|---------|
| User-specific? | Yes, personalized | Not necessarily |
| Cold start issue? | Yes (new users/items) | Less common |
| Example | "You might like..." | Search results ordering |
| Key signal | User-item interactions | Query-item relevance |

---

## By Business Domain

### E-commerce / Retail

| Use Case | Problem Type | Notes |
|----------|--------------|-------|
| Product recommendations | Recommendation | Collaborative + content-based hybrid |
| Demand forecasting | Forecasting | Seasonal, promotional effects |
| Customer churn | Classification | Define churn window carefully |
| Customer lifetime value | Regression | Often better as classification into tiers |
| Fraud detection | Anomaly Detection or Classification | Depends on labeled fraud data |
| Price optimization | Regression + Optimization | Often rule-based is sufficient |
| Search ranking | Ranking | Click data, purchase data |
| Customer segmentation | Clustering | RFM features often enough |

### SaaS / Software

| Use Case | Problem Type | Notes |
|----------|--------------|-------|
| User churn prediction | Classification | Define churn = no login in X days |
| Feature adoption prediction | Classification | Which users will adopt feature X |
| Usage forecasting | Forecasting | For capacity planning |
| Anomaly detection | Anomaly Detection | Error rates, latency, abuse |
| Support ticket routing | Text Classification | Or keyword rules first |
| Lead scoring | Classification or Regression | Classification often clearer |

### Finance

| Use Case | Problem Type | Notes |
|----------|--------------|-------|
| Credit scoring | Classification | Regulatory requirements for explainability |
| Fraud detection | Anomaly Detection | Few labeled examples typically |
| Stock prediction | Forecasting | Extremely difficult, beware overfitting |
| Customer segmentation | Clustering | Risk-based grouping |
| Churn prediction | Classification | High value, interpretability important |

### Healthcare (Non-diagnostic)

| Use Case | Problem Type | Notes |
|----------|--------------|-------|
| Patient no-show | Classification | Calendar, history features |
| Length of stay | Regression | Censored data considerations |
| Readmission risk | Classification | 30-day readmission common target |
| Demand forecasting | Forecasting | ER visits, bed demand |

### Manufacturing / IoT

| Use Case | Problem Type | Notes |
|----------|--------------|-------|
| Predictive maintenance | Classification or Anomaly | Classification if labeled failures |
| Quality defect detection | Anomaly Detection | Few defect examples typically |
| Demand forecasting | Forecasting | Supply chain planning |
| Sensor anomaly | Anomaly Detection | Multivariate time series |

---

## Decision Checklist

Before proceeding to technique selection:

- [ ] I can clearly state what I'm predicting
- [ ] I know the output type (category, number, ranking, groups)
- [ ] I understand if this involves time/sequence
- [ ] I know if I have labeled examples
- [ ] I've considered if rules/heuristics might work first

---

## Next Steps by Problem Type

| Problem Type | Next Document | Key Questions to Answer |
|--------------|---------------|------------------------|
| Classification | `classification.md` | Binary vs multiclass? Tabular vs text? Interpretability needed? |
| Regression | `regression.md` | Target distribution? Feature types? Real-time needed? |
| Anomaly Detection | `anomaly-detection.md` | Labeled anomalies? Point vs collective? Domain constraints? |
| Forecasting | `forecasting.md` | Horizon length? Seasonality? Multiple series? Exogenous variables? |
| Text Classification | `text-classification.md` | Sentiment vs intent vs topic? Labeled data volume? Languages? |
| Clustering | `clustering.md` | Number of clusters known? Interpretability needed? Hierarchical? |
| Recommendation | `recommendation.md` | Implicit vs explicit feedback? Cold start? Content available? |
| Ranking | `ranking.md` | Pointwise vs pairwise vs listwise? Position bias? |
