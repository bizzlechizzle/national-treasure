# Anomaly Detection

Find unusual patterns, outliers, fraud, and defects.

---

## When to Use

**You have**:
- Mostly "normal" data (ideally 95%+ normal)
- Few or no labeled anomaly examples
- Need to find unusual patterns, not known categories

**You want**:
- Flag items that deviate from normal behavior
- Detect fraud, defects, intrusions, errors
- Prioritize items for human review

**Consider Classification instead if**:
- You have many labeled anomaly examples (100+)
- Anomaly types are well-defined and known
- Predicting known categories, not "unusual"

---

## Anomaly Detection Types

| Type | Description | Example |
|------|-------------|---------|
| **Point anomaly** | Individual data point is unusual | Single fraudulent transaction |
| **Contextual anomaly** | Unusual in specific context | High AC usage in winter |
| **Collective anomaly** | Group of points unusual together | Sequence of micro-transactions |

---

## Technique Selection

### Tabular Data

| Technique | When to Use | Pros | Cons |
|-----------|-------------|------|------|
| **Isolation Forest** | General purpose, first try | Fast, handles high dimensions, no assumptions | Less effective on local anomalies |
| **Local Outlier Factor (LOF)** | Dense clusters with sparse anomalies | Detects local anomalies | Slow on large data, sensitive to k |
| **One-Class SVM** | Known normal boundary | Works with limited normal data | Sensitive to kernel choice, slower |
| **DBSCAN** | Cluster-based, density varies | Finds clusters and outliers | Sensitive to eps parameter |
| **Autoencoders** | Complex patterns, deep learning | Learns complex representations | Needs more data, GPU helpful |
| **Statistical (Z-score, IQR)** | Simple univariate detection | Fast, interpretable | Only works per-feature |

### Time Series

| Technique | When to Use | Pros | Cons |
|-----------|-------------|------|------|
| **Moving average + threshold** | Simple baseline | Interpretable, fast | Misses complex patterns |
| **Exponential smoothing** | Trending/seasonal data | Adapts to level changes | Needs seasonal adjustment |
| **Prophet anomaly** | Seasonal, missing data OK | Handles seasonality, robust | Facebook dependency |
| **LSTM Autoencoder** | Complex temporal patterns | Captures sequences | Needs significant data, GPU |
| **Matrix Profile (STUMPY)** | Subsequence anomalies | Fast, finds motifs too | Newer, specific use case |

### Choosing Approach

```
Do you have labeled anomalies?
│
├─► Many (100+) → Use Classification instead
│
├─► Few (10-100) → Semi-supervised
│   └─► Train on normal only, validate on labeled anomalies
│
└─► None → Unsupervised
    │
    ├─► Tabular → Isolation Forest (first), LOF (local), Autoencoder (complex)
    │
    └─► Time Series → Statistical baseline → LSTM Autoencoder (complex)
```

---

## Isolation Forest (Recommended First)

Works by isolating observations using random splits. Anomalies are easier to isolate (fewer splits needed).

### How It Works

1. Build random trees with random split points
2. Count path length to isolate each point
3. Anomalies have shorter average paths
4. Score based on average path length across trees

### Key Parameters

| Parameter | What It Does | Typical Values |
|-----------|--------------|----------------|
| `n_estimators` | Number of trees | 100-300 |
| `max_samples` | Samples per tree | 'auto' or 256 |
| `contamination` | Expected anomaly fraction | 0.01-0.1 or 'auto' |
| `max_features` | Features per tree | 1.0 (all) |

### Usage

```python
from sklearn.ensemble import IsolationForest

# Fit on normal data (or all data if unsupervised)
iso = IsolationForest(
    n_estimators=100,
    contamination=0.05,  # Expect 5% anomalies
    random_state=42
)
iso.fit(X_train)

# Predict: -1 = anomaly, 1 = normal
predictions = iso.predict(X_test)

# Anomaly scores (lower = more anomalous)
scores = iso.score_samples(X_test)
```

---

## Autoencoder for Anomaly Detection

Neural network trained to reconstruct normal data. High reconstruction error = anomaly.

### Architecture

```
Input → Encoder → Bottleneck (compressed) → Decoder → Output
                       ↓
              (low-dim representation)

Anomaly score = ||Input - Output||
```

### When to Use

- Complex, high-dimensional data
- Need to learn abstract "normal" pattern
- Have enough normal data (10,000+)
- GPU available

### Implementation

```python
import torch
import torch.nn as nn

class Autoencoder(nn.Module):
    def __init__(self, input_dim, encoding_dim=32):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, encoding_dim),
            nn.ReLU()
        )
        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, 64),
            nn.ReLU(),
            nn.Linear(64, input_dim)
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

# Training
model = Autoencoder(input_dim=X_train.shape[1])
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters())

for epoch in range(100):
    output = model(X_train_tensor)
    loss = criterion(output, X_train_tensor)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

# Anomaly detection
with torch.no_grad():
    reconstructed = model(X_test_tensor)
    mse = ((X_test_tensor - reconstructed) ** 2).mean(dim=1)
    threshold = mse.quantile(0.95)  # Top 5% are anomalies
    anomalies = mse > threshold
```

---

## Threshold Selection

Critical decision: How do you decide what's "anomalous enough"?

### Approaches

| Approach | When to Use | How |
|----------|-------------|-----|
| **Percentile** | No labels, general exploration | Top X% of scores are anomalies |
| **Statistical** | Known distribution | Beyond N standard deviations |
| **Validation-based** | Some labeled anomalies | Maximize F1 on validation set |
| **Business-driven** | Capacity constraint | "Can only review 50 items/day" |
| **Precision-focused** | False positives expensive | Choose threshold for desired precision |

### Percentile Example

```python
# Isolation Forest scores (lower = more anomalous)
scores = iso.score_samples(X)

# Top 1% most anomalous
threshold = np.percentile(scores, 1)
anomalies = scores < threshold

# Or dynamically based on investigation capacity
n_to_review = 50
threshold = np.percentile(scores, 100 * n_to_review / len(scores))
```

### With Labeled Validation Data

```python
from sklearn.metrics import precision_recall_curve

scores = -iso.score_samples(X_val)  # Negate so higher = more anomalous
precision, recall, thresholds = precision_recall_curve(y_val, scores)

# Choose threshold for 80% precision
idx = np.argmax(precision >= 0.8)
threshold = thresholds[idx]
```

---

## Evaluation Metrics

Anomaly detection evaluation is tricky due to class imbalance.

### With Labels (Preferred)

| Metric | Use When | Notes |
|--------|----------|-------|
| **Precision** | Cost of false alarms high | Of flagged items, how many truly anomalous? |
| **Recall** | Missing anomalies is costly | Of actual anomalies, how many caught? |
| **F1** | Balance of both | Harmonic mean |
| **AUC-PR** | Threshold-independent, imbalanced | Area under precision-recall curve |
| **Precision@K** | Review capacity limited | Precision in top K ranked items |

### Without Labels

| Metric | Use | Notes |
|--------|-----|-------|
| **Stability** | Consistent across runs | Re-run with different seeds |
| **Separation** | Score distribution | Gap between normal and flagged |
| **Human validation** | Sample and review | Check if flagged items make sense |
| **Downstream impact** | Business metric | Did flagging improve fraud loss, etc.? |

---

## Feature Engineering for Anomaly Detection

### General Principles

- Normalize features (anomalies shouldn't be driven by scale)
- Create ratio features (deviations from expected)
- Aggregate features (rolling statistics, patterns)
- Behavioral features (deviation from user's own history)

### Fraud Detection Features

| Category | Examples |
|----------|----------|
| **Transaction** | Amount, merchant category, time of day |
| **Behavioral** | Deviation from user's average, velocity (transactions/hour) |
| **Historical** | Days since last transaction, typical transaction size |
| **Network** | Shared device fingerprint, IP geolocation |
| **Aggregates** | Total in last 24h, distinct merchants this week |

### Time Series Features

| Category | Examples |
|----------|----------|
| **Rolling stats** | Moving average, moving std, min/max in window |
| **Lag features** | Value at t-1, t-7, t-30 |
| **Difference** | Change from previous period |
| **Seasonal** | Ratio to same period last year |

---

## Handling Imbalanced Feedback

### The Feedback Loop Problem

```
Anomalies flagged → Human reviews → Label collected → Model retrained
       ↑                                                    |
       └────────────────────────────────────────────────────┘

Problem: You only get labels for flagged items!
```

### Solutions

| Solution | How | Trade-off |
|----------|-----|-----------|
| **Random sampling** | Label some random unflagged items | Human effort on "boring" items |
| **Uncertainty sampling** | Label items near decision boundary | More representative feedback |
| **Periodic baseline** | Randomly flag 1% regardless of score | Ensures calibration |
| **Synthetic anomalies** | Generate fake anomalies to test recall | May not match real anomalies |

---

## Libraries

### Primary

| Library | Use Case | Install |
|---------|----------|---------|
| **scikit-learn** | Isolation Forest, LOF, One-Class SVM | `pip install scikit-learn` |
| **PyOD** | Comprehensive anomaly detection toolkit | `pip install pyod` |
| **Prophet** | Time series anomaly with seasonality | `pip install prophet` |

### Deep Learning

| Library | Use Case | Install |
|---------|----------|---------|
| **PyTorch** | Autoencoders, custom models | `pip install torch` |
| **alibi-detect** | Drift and anomaly detection | `pip install alibi-detect` |

### Time Series

| Library | Use Case | Install |
|---------|----------|---------|
| **STUMPY** | Matrix Profile for subsequence anomalies | `pip install stumpy` |
| **ADTK** | Anomaly Detection Toolkit for time series | `pip install adtk` |

---

## Production Considerations

### Online vs Batch

| Mode | When | Implementation |
|------|------|----------------|
| **Batch** | Periodic review, not time-critical | Daily job, score all records |
| **Near real-time** | Minutes acceptable | Streaming aggregation, periodic scoring |
| **Real-time** | Immediate action needed | Pre-computed features, fast model |

### Monitoring the Detector

| What to Monitor | Why | Alert If |
|-----------------|-----|----------|
| Anomaly rate | Drift detection | Rate changes significantly |
| Score distribution | Model stability | Distribution shifts |
| Precision (sampled) | Model quality | Drops below threshold |
| Feature values | Data quality | Out-of-range values |

### Model Updates

- Retrain periodically as "normal" evolves
- Exclude known anomalies from "normal" training data
- Version models and enable rollback
- A/B test new models before full rollout

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Training on contaminated data | Normal class includes anomalies | Clean training data, or use robust methods |
| Scaling issues | One feature dominates scores | Normalize all features |
| Static threshold | Too many/few alerts over time | Dynamic threshold or percentile-based |
| Ignoring temporal patterns | Miss time-based anomalies | Add time features, rolling stats |
| No human validation | Don't know if model works | Sample and review flagged items |
| Feedback loop bias | Only labeled flagged items | Random sampling of unflagged |

---

## Checklist Before Production

- [ ] Defined what "anomaly" means for this use case
- [ ] Confirmed anomalies are rare (<10% of data)
- [ ] Simple baseline (Z-score, IQR) tested first
- [ ] Threshold selection method chosen and documented
- [ ] Validation performed (human review or labeled holdout)
- [ ] Feature scaling applied consistently
- [ ] Feedback collection process designed
- [ ] Monitoring for score/rate drift planned
- [ ] Retraining cadence determined
- [ ] False positive handling process defined (who reviews, how to dismiss)

---

## Quick Start Code

```python
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score

# Prepare data
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train Isolation Forest
iso = IsolationForest(
    n_estimators=100,
    contamination=0.05,  # Expected 5% anomalies
    random_state=42,
    n_jobs=-1
)
iso.fit(X_train_scaled)

# Get anomaly scores (lower = more anomalous)
scores = iso.score_samples(X_test_scaled)

# Threshold: flag top 5% as anomalies
threshold = np.percentile(scores, 5)
predictions = (scores < threshold).astype(int)  # 1 = anomaly

# If you have labels
if y_test is not None:
    print(f"Precision: {precision_score(y_test, predictions):.3f}")
    print(f"Recall: {recall_score(y_test, predictions):.3f}")
    print(f"F1: {f1_score(y_test, predictions):.3f}")

# View most anomalous items
anomaly_df = pd.DataFrame({
    'score': scores,
    'is_anomaly': predictions
})
most_anomalous = anomaly_df.nsmallest(10, 'score')
print(most_anomalous)
```

---

## Further Reading

| Resource | Type | URL |
|----------|------|-----|
| Isolation Forest Paper | Research | https://cs.nju.edu.cn/zhouzh/zhouzh.files/publication/icdm08b.pdf |
| PyOD Documentation | Library | https://pyod.readthedocs.io/ |
| Anomaly Detection Survey | Survey | https://arxiv.org/abs/1901.03407 |
| ADTK for Time Series | Library | https://adtk.readthedocs.io/ |
