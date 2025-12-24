# Clustering

Group similar items together without predefined labels.

---

## When to Use

**You have**:
- Unlabeled data
- Belief that natural groups exist
- Features that capture meaningful similarity

**You want**:
- Discover segments or groups
- Explore data structure
- Reduce data for downstream tasks
- Find representative examples

**Consider Classification instead if**:
- You have labeled examples of the groups you want
- Groups are predefined, not discovered

---

## Clustering Types

| Type | Description | Example |
|------|-------------|---------|
| **Partitioning** | Divide into K non-overlapping groups | K-Means, K-Medoids |
| **Hierarchical** | Build tree of clusters | Agglomerative, Divisive |
| **Density-based** | Groups are dense regions | DBSCAN, HDBSCAN |
| **Model-based** | Assume statistical model | Gaussian Mixture Models |
| **Soft clustering** | Probabilistic membership | GMM, Fuzzy C-Means |

---

## Technique Selection

### Quick Selector

| Situation | Technique | Why |
|-----------|-----------|-----|
| Know number of clusters | K-Means | Fast, scalable |
| Unknown clusters, varying density | HDBSCAN | Discovers K, handles noise |
| Want hierarchy/dendrograms | Agglomerative | Interpretable structure |
| Spherical clusters, simple | K-Means | Works well, fast |
| Non-spherical, complex shapes | DBSCAN, HDBSCAN | Arbitrary shapes |
| Want probabilistic membership | GMM | Soft assignments |
| Very large data | Mini-batch K-Means | Scales to millions |
| Need to label new data | K-Means (with `predict`) | Assigns new points |

### Detailed Comparison

| Technique | Cluster Shape | Handles Noise | Finds K | Scalability |
|-----------|---------------|---------------|---------|-------------|
| **K-Means** | Spherical | No | No | Excellent |
| **K-Medoids** | Spherical | Better | No | Moderate |
| **Agglomerative** | Any (depends on linkage) | No | No | Poor (O(n²)) |
| **DBSCAN** | Arbitrary | Yes | Yes | Good |
| **HDBSCAN** | Arbitrary | Yes | Yes | Good |
| **GMM** | Elliptical | No | No | Good |
| **Spectral** | Complex | No | No | Poor (dense) |

---

## K-Means (Most Common)

### How It Works

1. Initialize K centroids
2. Assign each point to nearest centroid
3. Update centroids to mean of assigned points
4. Repeat until convergence

### When It Works Well

- Clusters are roughly spherical
- Clusters are similar size
- K is known or can be estimated
- Data is numeric and scaled

### Implementation

```python
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Scale features (important for K-Means!)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Fit K-Means
kmeans = KMeans(
    n_clusters=5,
    init='k-means++',  # Smart initialization
    n_init=10,         # Run 10 times, keep best
    max_iter=300,
    random_state=42
)
kmeans.fit(X_scaled)

# Get cluster assignments
labels = kmeans.labels_

# Get centroids
centroids = kmeans.cluster_centers_

# Assign new data
new_labels = kmeans.predict(X_new_scaled)

# Distance to cluster center (for confidence)
distances = kmeans.transform(X_scaled)  # Distance to each centroid
```

### Key Parameters

| Parameter | What It Does | Guidance |
|-----------|--------------|----------|
| `n_clusters` | Number of clusters | Use elbow method or silhouette |
| `init` | Initialization method | 'k-means++' (default, use this) |
| `n_init` | Number of runs | 10 (default), higher for robustness |
| `max_iter` | Max iterations | 300 (default) usually enough |

---

## HDBSCAN (Recommended for Discovery)

Hierarchical DBSCAN. Finds clusters of varying density, identifies noise.

### When to Use

- Don't know K
- Clusters may have different densities
- Expect noise/outliers
- Want robust results

### Implementation

```python
import hdbscan

clusterer = hdbscan.HDBSCAN(
    min_cluster_size=50,     # Minimum points for a cluster
    min_samples=5,           # Core point density threshold
    cluster_selection_epsilon=0.0,
    metric='euclidean'
)
labels = clusterer.fit_predict(X_scaled)

# -1 means noise (not assigned to any cluster)
n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
n_noise = (labels == -1).sum()
print(f"Clusters: {n_clusters}, Noise points: {n_noise}")

# Cluster membership probabilities
probabilities = clusterer.probabilities_

# Outlier scores
outlier_scores = clusterer.outlier_scores_
```

### Key Parameters

| Parameter | What It Does | Guidance |
|-----------|--------------|----------|
| `min_cluster_size` | Minimum cluster members | Domain knowledge, 50-500 |
| `min_samples` | Density threshold | 5-15 typical, higher = stricter |
| `cluster_selection_epsilon` | Merge close clusters | 0 for fine-grained |
| `metric` | Distance metric | 'euclidean', 'manhattan', 'cosine' |

---

## Choosing Number of Clusters (K)

### Elbow Method

Look for "elbow" in inertia (within-cluster sum of squares).

```python
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

inertias = []
K_range = range(2, 11)
for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(X_scaled)
    inertias.append(kmeans.inertia_)

plt.plot(K_range, inertias, 'bo-')
plt.xlabel('Number of clusters (K)')
plt.ylabel('Inertia')
plt.title('Elbow Method')
plt.show()
```

### Silhouette Score

Measures how similar points are to own cluster vs other clusters.

```python
from sklearn.metrics import silhouette_score, silhouette_samples

silhouette_scores = []
for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42)
    labels = kmeans.fit_predict(X_scaled)
    score = silhouette_score(X_scaled, labels)
    silhouette_scores.append(score)
    print(f"K={k}: Silhouette={score:.3f}")

# Higher is better, range [-1, 1]
# > 0.5: reasonable structure
# > 0.7: strong structure
# < 0.25: weak or artificial structure
```

### Gap Statistic

Compares inertia to expected under null reference distribution.

```python
from sklearn.cluster import KMeans
import numpy as np

def gap_statistic(X, K_range, n_refs=10):
    """Calculate gap statistic for K selection."""
    gaps = []
    for k in K_range:
        # Fit on real data
        kmeans = KMeans(n_clusters=k, random_state=42)
        kmeans.fit(X)
        inertia = kmeans.inertia_

        # Fit on reference data (uniform random)
        ref_inertias = []
        for _ in range(n_refs):
            X_ref = np.random.uniform(X.min(axis=0), X.max(axis=0), X.shape)
            kmeans_ref = KMeans(n_clusters=k, random_state=42)
            kmeans_ref.fit(X_ref)
            ref_inertias.append(kmeans_ref.inertia_)

        gap = np.mean(np.log(ref_inertias)) - np.log(inertia)
        gaps.append(gap)

    return gaps

# Choose K where gap is maximized
```

### Domain Knowledge

Often the best guide:
- Customer segments: 3-7 typically meaningful
- Document topics: Depends on corpus breadth
- Anomaly detection: 2 (normal + anomaly)

---

## Evaluation Metrics

### With Ground Truth (Rare)

| Metric | What It Measures | Range |
|--------|------------------|-------|
| **Adjusted Rand Index** | Agreement with true labels | [-1, 1], 1=perfect |
| **Normalized Mutual Information** | Shared information | [0, 1], 1=perfect |
| **Homogeneity** | Each cluster has one class | [0, 1] |
| **Completeness** | Each class in one cluster | [0, 1] |

### Without Ground Truth (Common)

| Metric | What It Measures | Range |
|--------|------------------|-------|
| **Silhouette Score** | Cluster cohesion vs separation | [-1, 1] |
| **Calinski-Harabasz** | Ratio of between/within variance | Higher=better |
| **Davies-Bouldin** | Average similarity between clusters | Lower=better |

```python
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score

print(f"Silhouette: {silhouette_score(X_scaled, labels):.3f}")
print(f"Calinski-Harabasz: {calinski_harabasz_score(X_scaled, labels):.1f}")
print(f"Davies-Bouldin: {davies_bouldin_score(X_scaled, labels):.3f}")
```

### Business Validation

Metrics aren't everything. Validate:
- Do clusters make business sense?
- Can domain experts interpret them?
- Are they actionable?

---

## Feature Engineering for Clustering

### Scaling (Critical!)

Distance-based methods are sensitive to scale.

```python
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler

# StandardScaler: mean=0, std=1 (most common)
scaler = StandardScaler()

# MinMaxScaler: range [0,1] (when bounds matter)
scaler = MinMaxScaler()

# RobustScaler: uses median/IQR (outlier robust)
scaler = RobustScaler()

X_scaled = scaler.fit_transform(X)
```

### Dimensionality Reduction

High dimensions can hurt clustering (curse of dimensionality).

```python
from sklearn.decomposition import PCA
from umap import UMAP

# PCA: Linear reduction
pca = PCA(n_components=50)  # Or 0.95 for 95% variance
X_pca = pca.fit_transform(X_scaled)

# UMAP: Non-linear, preserves local structure (better for clustering)
reducer = UMAP(n_components=10, random_state=42)
X_umap = reducer.fit_transform(X_scaled)
```

### Feature Selection

Remove irrelevant features before clustering:

```python
from sklearn.feature_selection import VarianceThreshold

# Remove low-variance features
selector = VarianceThreshold(threshold=0.1)
X_selected = selector.fit_transform(X_scaled)
```

---

## Cluster Interpretation

### Centroid Analysis

```python
# For K-Means: examine centroids
centroid_df = pd.DataFrame(
    scaler.inverse_transform(kmeans.cluster_centers_),
    columns=feature_names
)
print(centroid_df)

# Compare to overall mean
overall_mean = X.mean()
for i, row in centroid_df.iterrows():
    print(f"\nCluster {i}:")
    diff = (row - overall_mean) / X.std()
    notable = diff[abs(diff) > 0.5].sort_values()
    print(notable)
```

### Cluster Profiling

```python
# Add cluster labels to data
df['cluster'] = labels

# Profile each cluster
for cluster in df['cluster'].unique():
    print(f"\n=== Cluster {cluster} ===")
    cluster_data = df[df['cluster'] == cluster]
    print(f"Size: {len(cluster_data)}")
    print(cluster_data.describe())
```

### Representative Samples

```python
# Find examples closest to centroid
from sklearn.metrics import pairwise_distances

for i in range(n_clusters):
    cluster_mask = labels == i
    cluster_points = X_scaled[cluster_mask]
    centroid = kmeans.cluster_centers_[i]

    distances = pairwise_distances([centroid], cluster_points)[0]
    closest_idx = distances.argsort()[:5]

    print(f"\nCluster {i} representatives:")
    print(df[cluster_mask].iloc[closest_idx])
```

---

## Libraries

### Primary

| Library | Use Case | Install |
|---------|----------|---------|
| **scikit-learn** | K-Means, Agglomerative, DBSCAN, GMM | `pip install scikit-learn` |
| **hdbscan** | HDBSCAN (density-based) | `pip install hdbscan` |
| **umap-learn** | UMAP dimensionality reduction | `pip install umap-learn` |

### Visualization

| Library | Use Case | Install |
|---------|----------|---------|
| **matplotlib** | Basic plots | `pip install matplotlib` |
| **seaborn** | Statistical plots | `pip install seaborn` |
| **plotly** | Interactive plots | `pip install plotly` |

---

## Production Considerations

### Assigning New Data

| Technique | New Data Assignment |
|-----------|---------------------|
| K-Means | `kmeans.predict(X_new)` — assigns to nearest centroid |
| HDBSCAN | `hdbscan.approximate_predict()` — approximates |
| GMM | `gmm.predict(X_new)` — probabilistic |
| Agglomerative | Must re-fit or use approximate method |

### Cluster Stability

Test if clusters are stable across:
- Different random seeds
- Bootstrap samples
- Subsets of features

```python
# Bootstrap stability
from sklearn.utils import resample

all_labels = []
for _ in range(100):
    X_boot = resample(X_scaled, random_state=None)
    kmeans_boot = KMeans(n_clusters=5, random_state=42)
    labels_boot = kmeans_boot.fit_predict(X_boot)
    all_labels.append(labels_boot)

# Compare using Adjusted Rand Index
```

### Updating Clusters

- **Refit periodically**: Monthly/quarterly full refit
- **Online update**: Mini-batch K-Means for streaming
- **Monitor drift**: Track cluster sizes, centroid movement

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Not scaling features | One feature dominates | StandardScaler before clustering |
| Too many features | Poor clusters | PCA/UMAP reduction |
| Wrong K | Forced groupings | Use elbow, silhouette, domain knowledge |
| K-Means on non-spherical | Bad fit | Use DBSCAN, HDBSCAN |
| Ignoring noise | Noise assigned to clusters | HDBSCAN identifies noise |
| Over-interpreting | Clusters may be artifacts | Validate with domain experts |

---

## Checklist Before Production

- [ ] Features scaled appropriately
- [ ] Dimensionality reasonable (reduced if needed)
- [ ] Multiple K values tested
- [ ] Silhouette/metrics computed
- [ ] Clusters validated with domain experts
- [ ] Representative examples reviewed per cluster
- [ ] Cluster profiles documented (interpretable names)
- [ ] Method for assigning new data defined
- [ ] Monitoring plan for cluster drift
- [ ] Retraining cadence determined

---

## Quick Start Code

```python
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt

# Prepare data
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Find optimal K
K_range = range(2, 11)
silhouettes = []
inertias = []

for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)
    silhouettes.append(silhouette_score(X_scaled, labels))
    inertias.append(kmeans.inertia_)

# Plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
ax1.plot(K_range, inertias, 'bo-')
ax1.set_xlabel('K')
ax1.set_ylabel('Inertia')
ax1.set_title('Elbow Method')

ax2.plot(K_range, silhouettes, 'go-')
ax2.set_xlabel('K')
ax2.set_ylabel('Silhouette Score')
ax2.set_title('Silhouette Analysis')
plt.show()

# Fit final model
k_optimal = 5  # Choose based on plots
kmeans = KMeans(n_clusters=k_optimal, random_state=42)
labels = kmeans.fit_predict(X_scaled)

print(f"Silhouette Score: {silhouette_score(X_scaled, labels):.3f}")
print(f"Cluster sizes: {np.bincount(labels)}")

# Profile clusters
df['cluster'] = labels
print(df.groupby('cluster').mean())
```

---

## Further Reading

| Resource | Type | URL |
|----------|------|-----|
| scikit-learn Clustering Guide | Official Docs | https://scikit-learn.org/stable/modules/clustering.html |
| HDBSCAN Documentation | Library | https://hdbscan.readthedocs.io/ |
| Clustering Comparison | Visual | https://scikit-learn.org/stable/auto_examples/cluster/plot_cluster_comparison.html |
| How to Choose K | Tutorial | https://towardsdatascience.com/how-to-determine-the-optimal-k-for-k-means-clustering-8c14f1e4d9be |
