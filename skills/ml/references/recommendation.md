# Recommendation Systems

Suggest items users might like based on behavior and preferences.

---

## When to Use

**You have**:
- User-item interaction data (views, clicks, purchases, ratings)
- Enough users and items (100+ users, 50+ items minimum)
- Repeat interactions (users interact with multiple items)

**You want**:
- Personalized suggestions per user
- "Users like you also liked..."
- Increase engagement, conversion, discovery

**Consider Ranking instead if**:
- Context/query matters more than user history
- Showing relevance to a search term

---

## Recommendation Types

| Type | Based On | Example |
|------|----------|---------|
| **Collaborative filtering** | User behavior patterns | "Users who bought X also bought Y" |
| **Content-based** | Item attributes | "Because you liked action movies..." |
| **Hybrid** | Both behavior + content | Netflix, Spotify |
| **Knowledge-based** | Explicit constraints | "Flights under $500" |
| **Session-based** | Current session only | Anonymous users |

---

## Interaction Types

| Type | Signal Strength | Examples |
|------|-----------------|----------|
| **Explicit** | Strong | Ratings (1-5 stars), likes/dislikes |
| **Implicit** | Weaker but abundant | Views, clicks, time spent, purchases |

Most systems use implicit feedback (more data available).

### Implicit vs Explicit

| Aspect | Explicit | Implicit |
|--------|----------|----------|
| Data volume | Low | High |
| Signal clarity | High | Low |
| Missing = dislike? | Maybe | No (just not seen) |
| Typical algorithm | Matrix factorization | ALS, BPR |

---

## Technique Selection

### Quick Selector

| Situation | Technique | Why |
|-----------|-----------|-----|
| Quick baseline | Popularity-based | Always works, sets benchmark |
| User-item interactions only | Collaborative filtering (ALS, BPR) | Learns from behavior |
| Have item attributes | Content-based or hybrid | Uses item metadata |
| Cold start for new users | Content-based, popularity | No history available |
| Cold start for new items | Content-based | No interaction history |
| Large scale (millions) | ALS, neural (Two-Tower) | Efficient |
| Real-time personalization | Two-Tower with ANN | Fast retrieval |

### Detailed Comparison

| Technique | Data Needed | Cold Start | Pros | Cons |
|-----------|-------------|------------|------|------|
| **Popularity** | Interactions | N/A | Simple baseline | Not personalized |
| **User-User CF** | Interactions | User: Yes | Intuitive | Doesn't scale |
| **Item-Item CF** | Interactions | Item: Yes | Scalable, stable | Less personalized |
| **Matrix Factorization (ALS)** | Interactions | Both: Yes | Good accuracy | Cold start |
| **BPR** | Implicit interactions | Both: Yes | Designed for implicit | Requires negative sampling |
| **Content-based** | Item features | User: Yes | Handles new items | Filter bubble |
| **Two-Tower Neural** | Interactions + features | Partial | Scales, flexible | Complex |
| **Graph Neural Networks** | Graph structure | Partial | Captures relations | Complex |

---

## Baseline: Popularity

Always start here. Surprisingly effective.

```python
import pandas as pd

# Global popularity
popularity = interactions.groupby('item_id').size().sort_values(ascending=False)
top_items = popularity.head(10).index.tolist()

# Time-decayed popularity
def time_weighted_popularity(interactions, decay=0.1):
    """Recent interactions weighted more."""
    now = interactions['timestamp'].max()
    interactions['weight'] = np.exp(-decay * (now - interactions['timestamp']).dt.days)
    return interactions.groupby('item_id')['weight'].sum().sort_values(ascending=False)

# Segment-based popularity
segment_popularity = interactions.groupby(['user_segment', 'item_id']).size()
```

---

## Collaborative Filtering

### Matrix Factorization (ALS)

Decomposes user-item matrix into user factors and item factors.

```python
from implicit.als import AlternatingLeastSquares
from scipy.sparse import csr_matrix

# Create sparse user-item matrix
# Rows = users, Columns = items, Values = interaction strength
user_item_matrix = csr_matrix((
    interactions['value'],  # Rating or interaction count
    (interactions['user_idx'], interactions['item_idx'])
))

# Train ALS model
model = AlternatingLeastSquares(
    factors=50,           # Embedding dimension
    regularization=0.1,   # L2 regularization
    iterations=20,        # Training iterations
    use_gpu=False
)
model.fit(user_item_matrix)

# Get recommendations for a user
user_idx = 42
item_ids, scores = model.recommend(
    user_idx,
    user_item_matrix[user_idx],
    N=10,                 # Top 10 recommendations
    filter_already_liked_items=True
)

# Get similar items
similar_items = model.similar_items(item_idx, N=10)
```

### Key Parameters

| Parameter | What It Does | Typical Values |
|-----------|--------------|----------------|
| `factors` | Embedding dimension | 32-200 |
| `regularization` | Prevent overfitting | 0.01-0.1 |
| `iterations` | Training passes | 15-50 |
| `alpha` (for implicit) | Confidence scaling | 40 |

### BPR (Bayesian Personalized Ranking)

Optimized for implicit feedback. Learns to rank items.

```python
from implicit.bpr import BayesianPersonalizedRanking

model = BayesianPersonalizedRanking(
    factors=50,
    learning_rate=0.1,
    regularization=0.01,
    iterations=100
)
model.fit(user_item_matrix)
```

---

## Content-Based Filtering

When you have item attributes (description, category, tags).

### TF-IDF Similarity

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Create item content matrix
tfidf = TfidfVectorizer(max_features=5000)
item_vectors = tfidf.fit_transform(items['description'])

# Find similar items
def get_similar_items(item_idx, n=10):
    similarities = cosine_similarity(item_vectors[item_idx], item_vectors)[0]
    similar_indices = similarities.argsort()[::-1][1:n+1]  # Exclude self
    return similar_indices, similarities[similar_indices]

# User profile from history
def get_user_recommendations(user_history_items, n=10):
    user_profile = item_vectors[user_history_items].mean(axis=0)
    similarities = cosine_similarity(user_profile, item_vectors)[0]
    # Exclude already interacted
    similarities[user_history_items] = -1
    top_indices = similarities.argsort()[::-1][:n]
    return top_indices
```

### Embedding-Based

```python
from sentence_transformers import SentenceTransformer

# Use pre-trained embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')
item_embeddings = model.encode(items['description'].tolist())

# Find similar via cosine similarity or ANN (Approximate Nearest Neighbors)
from sklearn.neighbors import NearestNeighbors
nn = NearestNeighbors(n_neighbors=10, metric='cosine')
nn.fit(item_embeddings)
distances, indices = nn.kneighbors([item_embeddings[query_item_idx]])
```

---

## Hybrid Systems

Combine collaborative and content-based.

### Weighted Hybrid

```python
def hybrid_recommend(user_idx, alpha=0.7):
    """Combine CF and content-based scores."""
    cf_scores = get_cf_scores(user_idx)        # Collaborative filtering
    cb_scores = get_content_scores(user_idx)   # Content-based

    # Normalize to same scale
    cf_norm = (cf_scores - cf_scores.min()) / (cf_scores.max() - cf_scores.min())
    cb_norm = (cb_scores - cb_scores.min()) / (cb_scores.max() - cb_scores.min())

    # Weighted combination
    hybrid = alpha * cf_norm + (1 - alpha) * cb_norm
    return hybrid.argsort()[::-1][:10]
```

### Switching Hybrid

```python
def switching_recommend(user_idx):
    """Use CF if enough history, else content-based."""
    user_interactions = len(get_user_history(user_idx))

    if user_interactions >= 5:
        return cf_recommend(user_idx)
    else:
        return content_recommend(user_idx)  # Or popularity
```

---

## Handling Cold Start

### New Users (No History)

| Strategy | Implementation |
|----------|----------------|
| Popularity-based | Show globally popular items |
| Segment-based | Use demographics if available |
| Onboarding | Ask preferences, show genre picks |
| Content-based | If they viewed one item, find similar |
| Exploration | Random diverse sample |

### New Items (No Interactions)

| Strategy | Implementation |
|----------|----------------|
| Content similarity | Recommend with similar existing items |
| Attribute-based | Match user preferences to item attributes |
| Boost exposure | Deliberately show to subset of users |
| Editorial | Human curation for launch period |

---

## Evaluation Metrics

### Offline Metrics

| Metric | What It Measures | Notes |
|--------|------------------|-------|
| **Precision@K** | % of top-K relevant | Higher = more relevant recs |
| **Recall@K** | % of relevant in top-K | Higher = more coverage |
| **NDCG@K** | Ranking quality (position-aware) | Higher = better ranking |
| **MAP** | Mean Average Precision | Ranking quality |
| **Hit Rate@K** | Did user interact with any top-K? | Binary per user |
| **MRR** | Mean Reciprocal Rank | Where does first hit appear? |

### Offline Evaluation Setup

```python
from sklearn.model_selection import train_test_split

# Time-based split (important!)
train = interactions[interactions['timestamp'] < cutoff_date]
test = interactions[interactions['timestamp'] >= cutoff_date]

# Or leave-one-out
def leave_one_out_split(interactions):
    """Hold out last interaction per user."""
    test = interactions.groupby('user_id').last()
    train = interactions.drop(test.index)
    return train, test
```

### Metric Calculation

```python
def precision_at_k(recommended, relevant, k=10):
    """Precision of top-K recommendations."""
    rec_set = set(recommended[:k])
    rel_set = set(relevant)
    return len(rec_set & rel_set) / k

def recall_at_k(recommended, relevant, k=10):
    """Recall of top-K recommendations."""
    rec_set = set(recommended[:k])
    rel_set = set(relevant)
    return len(rec_set & rel_set) / len(rel_set) if rel_set else 0

def ndcg_at_k(recommended, relevant, k=10):
    """Normalized Discounted Cumulative Gain."""
    dcg = 0
    for i, item in enumerate(recommended[:k]):
        if item in relevant:
            dcg += 1 / np.log2(i + 2)  # Position is 1-indexed

    # Ideal DCG
    idcg = sum(1 / np.log2(i + 2) for i in range(min(len(relevant), k)))
    return dcg / idcg if idcg > 0 else 0
```

### Beyond Accuracy

| Metric | What It Measures |
|--------|------------------|
| **Coverage** | % of items ever recommended |
| **Diversity** | How different are recommendations? |
| **Novelty** | Are recommendations non-obvious? |
| **Serendipity** | Surprising yet relevant? |

---

## Libraries

### Primary

| Library | Use Case | Install |
|---------|----------|---------|
| **implicit** | ALS, BPR for implicit feedback | `pip install implicit` |
| **surprise** | Traditional CF, explicit ratings | `pip install scikit-surprise` |
| **LightFM** | Hybrid (CF + content) | `pip install lightfm` |
| **RecBole** | Comprehensive rec framework | `pip install recbole` |

### Deep Learning

| Library | Use Case | Install |
|---------|----------|---------|
| **pytorch** | Neural recommendations | `pip install torch` |
| **TensorFlow Recommenders** | Two-tower, retrieval | `pip install tensorflow-recommenders` |

### Nearest Neighbors

| Library | Use Case | Install |
|---------|----------|---------|
| **faiss** | Fast ANN search (Facebook) | `pip install faiss-cpu` |
| **annoy** | Approximate NN (Spotify) | `pip install annoy` |
| **hnswlib** | Fast ANN | `pip install hnswlib` |

---

## Production Architecture

### Two-Stage System

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Candidate  │────▶│   Ranking   │────▶│   Final     │
│  Generation │     │   Model     │     │   Results   │
│  (1000s)    │     │   (100s)    │     │   (10s)     │
└─────────────┘     └─────────────┘     └─────────────┘
   - ALS recall        - LTR model        - Diversity
   - Content NN        - CTR prediction   - Business rules
   - Popularity        - Personalization  - Filtering
```

### Candidate Generation

Fast, recall-focused. Get thousands of candidates.

```python
# Multiple sources
candidates = set()
candidates.update(als_recommendations(user, n=500))
candidates.update(content_similar_to_history(user, n=300))
candidates.update(popular_in_segment(user, n=200))
```

### Ranking

Slower, precision-focused. Score and rank candidates.

```python
# Feature engineering for ranking
features = []
for item in candidates:
    f = {
        'als_score': als_model.score(user, item),
        'content_sim': content_similarity(user, item),
        'item_popularity': popularity[item],
        'user_preference_match': preference_match(user, item),
        'recency': item_recency[item],
    }
    features.append(f)

# Rank with learned model (XGBoost, NN)
scores = ranking_model.predict(features)
ranked_items = sorted(zip(candidates, scores), key=lambda x: -x[1])
```

### Real-Time Serving

```python
# Pre-compute and cache
# 1. User embeddings (update periodically)
# 2. Item embeddings (update on new items)
# 3. Popular items (update daily)

# At serving time:
# 1. Retrieve user embedding from cache
# 2. ANN search for similar items
# 3. Apply business rules
# 4. Return top-K
```

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Popularity bias | Always recommending popular | Normalize by popularity, diversify |
| Filter bubble | Narrow recommendations | Add exploration, diversity metrics |
| Cold start ignored | New users get garbage | Implement fallback strategies |
| Data leakage | Overestimated offline metrics | Proper time-based splits |
| Ignoring implicit negative | Can't distinguish dislike vs not seen | Use confidence weighting |
| Stale recommendations | Same recs for months | Retrain regularly, add recency |

---

## Checklist Before Production

- [ ] Popularity baseline established
- [ ] Offline metrics computed on held-out data
- [ ] Cold start strategy for new users
- [ ] Cold start strategy for new items
- [ ] Candidate generation is fast enough
- [ ] Ranking model trained
- [ ] Business rules applied (filter inappropriate, boost new)
- [ ] Diversity ensured (not all same category)
- [ ] A/B testing framework ready
- [ ] Monitoring for engagement metrics

---

## Quick Start Code

```python
import numpy as np
import pandas as pd
from implicit.als import AlternatingLeastSquares
from scipy.sparse import csr_matrix

# Prepare data
# interactions: user_id, item_id, value (implicit: count or binary)

# Create user/item mappings
user_ids = interactions['user_id'].unique()
item_ids = interactions['item_id'].unique()
user_to_idx = {u: i for i, u in enumerate(user_ids)}
item_to_idx = {i: j for j, i in enumerate(item_ids)}
idx_to_item = {j: i for i, j in item_to_idx.items()}

interactions['user_idx'] = interactions['user_id'].map(user_to_idx)
interactions['item_idx'] = interactions['item_id'].map(item_to_idx)

# Create sparse matrix
user_item_matrix = csr_matrix((
    interactions['value'],
    (interactions['user_idx'], interactions['item_idx'])
), shape=(len(user_ids), len(item_ids)))

# Train model
model = AlternatingLeastSquares(
    factors=50,
    regularization=0.1,
    iterations=20
)
model.fit(user_item_matrix)

# Get recommendations
def recommend_for_user(user_id, n=10):
    if user_id not in user_to_idx:
        # Cold start: return popular
        return interactions['item_id'].value_counts().head(n).index.tolist()

    user_idx = user_to_idx[user_id]
    item_indices, scores = model.recommend(
        user_idx,
        user_item_matrix[user_idx],
        N=n,
        filter_already_liked_items=True
    )
    return [idx_to_item[i] for i in item_indices]

# Example
recs = recommend_for_user(user_id=123, n=10)
print(f"Recommendations: {recs}")
```

---

## Further Reading

| Resource | Type | URL |
|----------|------|-----|
| Implicit Library Docs | Library | https://implicit.readthedocs.io/ |
| Google Rec Systems Course | Course | https://developers.google.com/machine-learning/recommendation |
| LightFM Documentation | Library | https://making.lyst.com/lightfm/docs/ |
| Two-Tower Architecture | Paper | https://arxiv.org/abs/1906.00091 |
| Netflix Prize | Case Study | https://www.netflixprize.com/ |
