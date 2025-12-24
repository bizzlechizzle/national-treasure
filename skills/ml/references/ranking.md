# Ranking (Learning to Rank)

Order items by relevance to a query or context.

---

## When to Use

**You have**:
- Items to rank (search results, candidates, feed items)
- Relevance signals (clicks, ratings, conversions)
- Contextual information (query, user, session)

**You want**:
- Order items by predicted relevance
- Optimize for engagement/conversion
- Personalize ordering

**Consider Recommendation instead if**:
- No query/context, just "items for this user"
- Pure collaborative filtering scenario

---

## Ranking vs Classification/Regression

| Aspect | Classification/Regression | Ranking |
|--------|--------------------------|---------|
| Output | Score per item | Relative order of items |
| Loss | Per-item error | Order/position error |
| Optimization | Individual predictions | Pairwise/listwise comparisons |
| Metric | Accuracy, RMSE | NDCG, MAP, MRR |

---

## Ranking Approaches

| Approach | How It Works | Pros | Cons |
|----------|--------------|------|------|
| **Pointwise** | Predict relevance score per item | Simple, use any regressor | Ignores position |
| **Pairwise** | Learn which of two items ranks higher | Captures relative order | O(n²) pairs |
| **Listwise** | Optimize ranking metric directly | Best alignment with metrics | Complex |

### When to Use Each

| Approach | Best For |
|----------|----------|
| Pointwise | Quick baseline, simple setup |
| Pairwise | When you have pairwise labels (A > B) |
| Listwise | Production systems, best metrics |

---

## Technique Selection

### Quick Selector

| Situation | Technique | Why |
|-----------|-----------|-----|
| Quick baseline | Pointwise (XGBoost) | Simple, effective |
| Best performance | LambdaMART (LightGBM) | SOTA for tabular |
| Neural features | RankNet, ListNet | Handles embeddings |
| Large scale | Two-tower + ANN | Scalable retrieval |
| Sparse features | GBDT-based LTR | Handles missing well |

### Detailed Comparison

| Technique | Type | Approach | Implementation |
|-----------|------|----------|----------------|
| **XGBoost Regressor** | Pointwise | Predict relevance | Standard XGBoost |
| **RankNet** | Pairwise | Learn pairwise prefs | Neural net |
| **LambdaRank** | Listwise | Optimize NDCG | Gradient-based |
| **LambdaMART** | Listwise | LambdaRank + GBDT | LightGBM `lambdarank` |
| **ListNet** | Listwise | Permutation probs | Neural net |
| **Two-Tower** | Pointwise (embedding) | Query-doc similarity | Neural retrieval |

---

## Pointwise Baseline

Treat ranking as regression: predict relevance score, sort by score.

```python
import xgboost as xgb
from sklearn.model_selection import GroupShuffleSplit

# Data format:
# - features: query-document feature vector
# - labels: relevance score (0, 1, 2, 3, 4 or 0-1)
# - groups: query_id (for proper train/test split)

# Group-aware split (don't leak queries)
splitter = GroupShuffleSplit(n_splits=1, test_size=0.2)
train_idx, test_idx = next(splitter.split(X, y, groups=query_ids))

X_train, X_test = X[train_idx], X[test_idx]
y_train, y_test = y[train_idx], y[test_idx]

# Train regressor
model = xgb.XGBRegressor(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1
)
model.fit(X_train, y_train)

# Predict and rank
scores = model.predict(X_test)
# Sort documents within each query by score
```

### Limitations

- Ignores that we care about ORDER, not absolute scores
- Equal weight to all positions
- Doesn't optimize NDCG/MAP directly

---

## LambdaMART (Recommended)

State-of-the-art for tabular ranking. Optimizes NDCG directly.

### How It Works

1. Uses gradient boosted trees
2. Gradients ("lambdas") incorporate position-based metric
3. Items that would most improve NDCG get higher gradients
4. Implicitly pairwise but optimizes listwise metric

### LightGBM Implementation

```python
import lightgbm as lgb

# Data format: features, labels, query groups
# Groups define which documents belong to same query
# e.g., [3, 5, 2] means first 3 docs are query 1, next 5 are query 2, etc.

train_data = lgb.Dataset(
    X_train,
    label=y_train,
    group=train_groups  # [n_docs_query1, n_docs_query2, ...]
)
valid_data = lgb.Dataset(
    X_valid,
    label=y_valid,
    group=valid_groups,
    reference=train_data
)

params = {
    'objective': 'lambdarank',
    'metric': 'ndcg',
    'ndcg_eval_at': [1, 3, 5, 10],  # Evaluate NDCG@K
    'boosting_type': 'gbdt',
    'num_leaves': 31,
    'learning_rate': 0.05,
    'feature_fraction': 0.9,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'verbose': -1
}

model = lgb.train(
    params,
    train_data,
    num_boost_round=1000,
    valid_sets=[valid_data],
    callbacks=[lgb.early_stopping(50)]
)

# Predict relevance scores
scores = model.predict(X_test)
# Higher score = more relevant, sort descending
```

### XGBoost Implementation

```python
import xgboost as xgb

# Convert to DMatrix with query groups
dtrain = xgb.DMatrix(X_train, label=y_train)
dtrain.set_group(train_groups)

dvalid = xgb.DMatrix(X_valid, label=y_valid)
dvalid.set_group(valid_groups)

params = {
    'objective': 'rank:ndcg',  # or 'rank:pairwise'
    'eval_metric': 'ndcg@10',
    'eta': 0.1,
    'max_depth': 6,
    'min_child_weight': 1
}

model = xgb.train(
    params,
    dtrain,
    num_boost_round=500,
    evals=[(dvalid, 'valid')],
    early_stopping_rounds=50
)

dtest = xgb.DMatrix(X_test)
scores = model.predict(dtest)
```

---

## Feature Engineering for Ranking

### Feature Categories

| Category | Examples |
|----------|----------|
| **Query features** | Query length, query type, query popularity |
| **Document features** | Doc length, age, quality score, category |
| **Query-Document** | BM25 score, TF-IDF similarity, semantic similarity |
| **User features** | User history, preferences, segment |
| **Context features** | Time of day, device, location |
| **Historical** | CTR of this doc, position bias correction |

### Common Features

```python
def extract_ranking_features(query, doc, user=None):
    features = {}

    # Text matching
    features['bm25'] = bm25_score(query, doc)
    features['tfidf_sim'] = tfidf_similarity(query, doc)
    features['exact_match'] = int(query in doc.title)

    # Document quality
    features['doc_length'] = len(doc.text)
    features['doc_age_days'] = (now - doc.created_at).days
    features['doc_popularity'] = doc.view_count

    # Semantic similarity (embeddings)
    features['semantic_sim'] = cosine_similarity(
        embed(query), embed(doc.text)
    )

    # Query features
    features['query_length'] = len(query.split())
    features['query_is_question'] = int(query.endswith('?'))

    # User personalization (if available)
    if user:
        features['user_category_affinity'] = user.category_scores.get(doc.category, 0)
        features['user_has_interacted'] = int(doc.id in user.history)

    return features
```

### Position Bias Correction

Users click more on higher positions regardless of relevance.

```python
# Method 1: Position as feature (learn bias)
features['displayed_position'] = position  # During training

# Method 2: Inverse propensity weighting
# Weight by 1 / P(click | position)
position_ctr = clicks_by_position / impressions_by_position
propensity_weight = 1 / position_ctr[position]
```

---

## Evaluation Metrics

### NDCG (Normalized Discounted Cumulative Gain)

Most common ranking metric. Rewards relevant items at top.

```python
import numpy as np

def dcg_at_k(relevance, k):
    """Discounted Cumulative Gain."""
    relevance = np.asarray(relevance)[:k]
    gains = 2 ** relevance - 1
    discounts = np.log2(np.arange(2, len(relevance) + 2))
    return np.sum(gains / discounts)

def ndcg_at_k(relevance, k):
    """Normalized DCG."""
    dcg = dcg_at_k(relevance, k)
    ideal_relevance = sorted(relevance, reverse=True)
    idcg = dcg_at_k(ideal_relevance, k)
    return dcg / idcg if idcg > 0 else 0

# Example
predicted_order_relevance = [3, 2, 1, 0, 0]  # Relevance of items in predicted order
ndcg = ndcg_at_k(predicted_order_relevance, k=5)
```

### Other Metrics

| Metric | What It Measures | Formula Intuition |
|--------|------------------|-------------------|
| **MRR** (Mean Reciprocal Rank) | Position of first relevant | 1/rank of first hit |
| **MAP** (Mean Average Precision) | Precision at each relevant item | Average P@k for each relevant |
| **Precision@K** | Relevant in top K | % relevant in top K |
| **Recall@K** | Coverage of relevant | % of relevant in top K |

### Metric Selection

| Use Case | Primary Metric |
|----------|----------------|
| Web search | NDCG@10, MRR |
| E-commerce search | NDCG, Revenue@K |
| Content feed | NDCG, Engagement |
| One right answer | MRR |

---

## Handling Position Bias

### The Problem

Click data is biased: top positions get more clicks regardless of relevance.

### Solutions

| Approach | Implementation |
|----------|----------------|
| **Position as feature** | Include displayed position, let model learn |
| **IPW (Inverse Propensity)** | Weight clicks by 1/P(examine) |
| **Dual learning** | Jointly learn relevance + examination |
| **Randomization** | Random ranking for subset (exploration) |
| **Interleaving** | Mix rankings to reduce bias |

```python
# IPW example
def compute_ipw_weight(position, examination_probs):
    """Inverse propensity weight for click data."""
    return 1 / examination_probs[position]

# examination_probs estimated from eye-tracking or click experiments
examination_probs = [1.0, 0.8, 0.6, 0.5, 0.4, 0.3, 0.2, 0.15, 0.1, 0.05]
```

---

## Online Evaluation

Offline metrics don't always match online performance. A/B test.

### Interleaving

Compare two rankers without full A/B test.

```python
def team_draft_interleave(ranking_a, ranking_b):
    """Interleave two rankings fairly."""
    interleaved = []
    team_a, team_b = [], []
    idx_a, idx_b = 0, 0

    while len(interleaved) < len(ranking_a):
        if len(team_a) <= len(team_b) and idx_a < len(ranking_a):
            item = ranking_a[idx_a]
            idx_a += 1
            if item not in interleaved:
                interleaved.append(item)
                team_a.append(item)
        elif idx_b < len(ranking_b):
            item = ranking_b[idx_b]
            idx_b += 1
            if item not in interleaved:
                interleaved.append(item)
                team_b.append(item)

    return interleaved, team_a, team_b

# Attribution: clicks on team_a items → ranker A wins that query
```

### Online Metrics

| Metric | What It Measures |
|--------|------------------|
| CTR | Click-through rate |
| Conversion rate | Purchases / impressions |
| Time to click | User satisfaction |
| Abandonment rate | Query without click |
| Reformulation rate | User rephrased query |

---

## Libraries

### GBDT-based LTR

| Library | Use Case | Install |
|---------|----------|---------|
| **LightGBM** | LambdaMART, fast | `pip install lightgbm` |
| **XGBoost** | Pairwise/listwise ranking | `pip install xgboost` |
| **CatBoost** | Ranking with categoricals | `pip install catboost` |

### Neural LTR

| Library | Use Case | Install |
|---------|----------|---------|
| **TensorFlow Ranking** | Neural LTR | `pip install tensorflow-ranking` |
| **PyTorch-based** | Custom neural rankers | `pip install torch` |
| **allRank** | Neural LTR library | `pip install allrank` |

### Evaluation

| Library | Use Case | Install |
|---------|----------|---------|
| **ranx** | Ranking evaluation | `pip install ranx` |
| **ir-measures** | IR metrics | `pip install ir-measures` |

---

## Production Architecture

### Two-Stage System

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Retrieval  │────▶│   Ranking   │────▶│  Re-ranking │
│  (10000s)   │     │   (100s)    │     │   (10s)     │
└─────────────┘     └─────────────┘     └─────────────┘
   - BM25              - LambdaMART       - Business rules
   - Embedding ANN     - Neural ranker    - Diversity
   - Inverted index    - Feature-rich     - Personalization
```

### Retrieval (Stage 1)

Fast, recall-focused. Get candidates from index.

```python
# BM25 retrieval
from rank_bm25 import BM25Okapi

bm25 = BM25Okapi(corpus_tokenized)
scores = bm25.get_scores(query_tokenized)
top_candidates = np.argsort(scores)[::-1][:1000]

# Embedding retrieval (semantic)
query_embedding = encode(query)
distances, indices = faiss_index.search(query_embedding, k=1000)
```

### Ranking (Stage 2)

Feature-rich model. Score and reorder candidates.

```python
# Extract features for query-candidate pairs
features = [extract_features(query, doc) for doc in candidates]

# Score with ranking model
scores = ranking_model.predict(features)

# Sort by score
ranked_indices = np.argsort(scores)[::-1]
ranked_docs = [candidates[i] for i in ranked_indices]
```

### Re-ranking (Stage 3)

Apply business logic, diversify.

```python
def rerank(docs, scores, diversify=True, max_per_category=3):
    """Apply business rules to final ranking."""
    final = []
    category_counts = {}

    for doc, score in sorted(zip(docs, scores), key=lambda x: -x[1]):
        # Diversity: limit items per category
        if diversify:
            cat = doc.category
            if category_counts.get(cat, 0) >= max_per_category:
                continue
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Business rules
        if not doc.is_available:
            continue

        final.append(doc)
        if len(final) >= 10:
            break

    return final
```

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Data leakage from position | Unrealistic offline metrics | Remove position from features, or use IPW |
| Random train/test split | Queries leak across splits | Group-aware splits by query |
| Ignoring ties | Inconsistent ranking | Define tie-breaking rule |
| Training on clicks only | Popularity bias | Add exploration, IPW |
| No position bias correction | Learn to rank by position | Position debiasing techniques |
| Metric mismatch | Optimize RMSE, measure NDCG | Use ranking objectives |

---

## Checklist Before Production

- [ ] Pointwise baseline established
- [ ] Proper group-aware train/test splits
- [ ] LambdaMART or listwise model trained
- [ ] Position bias addressed
- [ ] Offline metrics computed (NDCG, MRR)
- [ ] Feature importance analyzed
- [ ] Two-stage architecture designed (retrieval + ranking)
- [ ] Business rules / re-ranking layer added
- [ ] Online A/B test or interleaving planned
- [ ] Latency requirements met

---

## Quick Start Code

```python
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import GroupShuffleSplit

# Data preparation
# X: features (n_samples, n_features)
# y: relevance labels (0-4 or 0-1)
# query_ids: which query each sample belongs to

# Group-aware split
groups = [query_ids[query_ids == q].shape[0] for q in np.unique(query_ids)]
# groups = [n_docs_query1, n_docs_query2, ...]

# Split queries, not individual samples
gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train_idx, test_idx = next(gss.split(X, y, query_ids))

X_train, X_test = X[train_idx], X[test_idx]
y_train, y_test = y[train_idx], y[test_idx]

# Compute groups for train/test
train_queries = query_ids[train_idx]
test_queries = query_ids[test_idx]
train_groups = [np.sum(train_queries == q) for q in np.unique(train_queries)]
test_groups = [np.sum(test_queries == q) for q in np.unique(test_queries)]

# Create datasets
train_data = lgb.Dataset(X_train, label=y_train, group=train_groups)
test_data = lgb.Dataset(X_test, label=y_test, group=test_groups, reference=train_data)

# Train LambdaMART
params = {
    'objective': 'lambdarank',
    'metric': 'ndcg',
    'ndcg_eval_at': [1, 3, 5, 10],
    'num_leaves': 31,
    'learning_rate': 0.05,
}

model = lgb.train(
    params,
    train_data,
    num_boost_round=500,
    valid_sets=[test_data],
    callbacks=[lgb.early_stopping(50), lgb.log_evaluation(100)]
)

# Predict
scores = model.predict(X_test)
print(f"Sample scores: {scores[:10]}")

# Evaluate NDCG manually for one query
query_mask = test_queries == test_queries[0]
query_scores = scores[query_mask]
query_labels = y_test[query_mask]
ranked_order = np.argsort(-query_scores)
relevances = query_labels[ranked_order]
print(f"NDCG@5 for query: {ndcg_at_k(relevances, 5):.3f}")
```

---

## Further Reading

| Resource | Type | URL |
|----------|------|-----|
| LightGBM LambdaRank | Official Docs | https://lightgbm.readthedocs.io/en/latest/Parameters.html |
| XGBoost Ranking | Official Docs | https://xgboost.readthedocs.io/en/latest/tutorials/learning_to_rank.html |
| TensorFlow Ranking | Library | https://www.tensorflow.org/ranking |
| Learning to Rank Survey | Paper | https://arxiv.org/abs/1904.06813 |
| Microsoft LTR Datasets | Benchmark | https://www.microsoft.com/en-us/research/project/mslr/ |
