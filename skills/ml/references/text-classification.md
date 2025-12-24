# Text Classification

Categorize text into predefined classes (non-generative NLP).

---

## When to Use

**You have**:
- Text data (documents, comments, messages, tickets)
- Labeled examples (text → category)
- Predefined categories to predict

**You want**:
- Categorize new text automatically
- Route, filter, or prioritize by content
- Understand what topics/sentiments are present

**This is NOT for**:
- Generating new text (use LLMs)
- Free-form question answering (use LLMs)
- Extracting specific entities (use NER)

---

## Text Classification Types

| Type | Description | Example |
|------|-------------|---------|
| **Binary** | Two classes | Spam vs not spam |
| **Multiclass** | One of N classes | Ticket routing (Sales/Support/Billing) |
| **Multilabel** | Multiple classes per text | Article tags (Politics AND Economy) |
| **Sentiment** | Positive/negative/neutral | Review sentiment analysis |
| **Intent** | User's goal | Chatbot intent classification |

---

## Technique Selection

### Quick Selector

| Situation | Technique | Why |
|-----------|-----------|-----|
| Quick baseline, any data size | TF-IDF + Logistic Regression | Fast, interpretable, works |
| Limited labels (< 1000) | SetFit, TF-IDF + SVM | Few-shot capable |
| Semantic understanding needed | DistilBERT fine-tuned | Captures meaning |
| Multilingual | mBERT, XLM-RoBERTa | Cross-lingual transfer |
| Production, low latency | TF-IDF + LR, or distilled model | Fast inference |
| Best accuracy, have GPU | RoBERTa, DeBERTa fine-tuned | SOTA transformers |

### Detailed Comparison

| Technique | Data Needed | Accuracy | Speed | Interpretable |
|-----------|-------------|----------|-------|---------------|
| **TF-IDF + Logistic Regression** | 100+ per class | Good | Very fast | Yes |
| **TF-IDF + XGBoost** | 100+ per class | Better | Fast | Partial |
| **FastText** | 1000+ per class | Good | Fast | Partial |
| **DistilBERT** | 500+ per class | Very good | Medium | No |
| **RoBERTa/DeBERTa** | 1000+ per class | Excellent | Slow | No |
| **SetFit** | 8+ per class | Very good | Medium | No |

---

## Traditional ML Approach (Start Here)

### TF-IDF + Logistic Regression

Best baseline. Surprisingly effective. Always try first.

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Create pipeline
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(
        max_features=10000,
        ngram_range=(1, 2),  # Unigrams and bigrams
        min_df=2,            # Ignore rare terms
        max_df=0.95          # Ignore too common terms
    )),
    ('clf', LogisticRegression(
        class_weight='balanced',
        max_iter=1000,
        C=1.0
    ))
])

# Train
X_train, X_test, y_train, y_test = train_test_split(
    texts, labels, test_size=0.2, stratify=labels, random_state=42
)
pipeline.fit(X_train, y_train)

# Evaluate
y_pred = pipeline.predict(X_test)
print(classification_report(y_test, y_pred))

# Predict with probabilities
probs = pipeline.predict_proba(X_test)
```

### TF-IDF Tuning

| Parameter | What It Does | Guidance |
|-----------|--------------|----------|
| `max_features` | Vocabulary size | 5000-20000 typical |
| `ngram_range` | Word sequences | (1,2) usually optimal |
| `min_df` | Minimum document frequency | 2-5 removes rare noise |
| `max_df` | Maximum document frequency | 0.9-0.95 removes too common |
| `sublinear_tf` | Log scaling | True often helps |
| `use_idf` | Inverse document frequency | True (default) |

---

## Transformer Approach (When Needed)

### When to Use Transformers

- TF-IDF baseline isn't good enough
- Need semantic understanding (synonyms, context)
- Have enough data (500+ per class minimum)
- Have GPU access
- Accuracy is critical

### DistilBERT Fine-tuning

Smaller, faster BERT variant. Good balance of speed and accuracy.

```python
from transformers import (
    DistilBertTokenizer,
    DistilBertForSequenceClassification,
    Trainer,
    TrainingArguments
)
from datasets import Dataset
import numpy as np
from sklearn.metrics import accuracy_score, f1_score

# Prepare data
tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')

def tokenize_function(examples):
    return tokenizer(
        examples['text'],
        padding='max_length',
        truncation=True,
        max_length=256
    )

train_dataset = Dataset.from_dict({'text': X_train, 'label': y_train})
test_dataset = Dataset.from_dict({'text': X_test, 'label': y_test})

train_dataset = train_dataset.map(tokenize_function, batched=True)
test_dataset = test_dataset.map(tokenize_function, batched=True)

# Load model
model = DistilBertForSequenceClassification.from_pretrained(
    'distilbert-base-uncased',
    num_labels=len(set(labels))
)

# Training arguments
training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=64,
    warmup_steps=500,
    weight_decay=0.01,
    logging_dir='./logs',
    evaluation_strategy='epoch',
    save_strategy='epoch',
    load_best_model_at_end=True
)

# Metrics
def compute_metrics(pred):
    labels = pred.label_ids
    preds = np.argmax(pred.predictions, axis=1)
    return {
        'accuracy': accuracy_score(labels, preds),
        'f1': f1_score(labels, preds, average='weighted')
    }

# Train
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
    compute_metrics=compute_metrics
)
trainer.train()
```

### SetFit (Few-Shot Learning)

When you have very few labeled examples (8-100 per class).

```python
from setfit import SetFitModel, SetFitTrainer
from datasets import Dataset

# Prepare data
train_dataset = Dataset.from_dict({'text': X_train, 'label': y_train})
test_dataset = Dataset.from_dict({'text': X_test, 'label': y_test})

# Load pre-trained SetFit model
model = SetFitModel.from_pretrained('sentence-transformers/paraphrase-mpnet-base-v2')

# Create trainer
trainer = SetFitTrainer(
    model=model,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
    num_iterations=20,  # Number of text pairs to generate
    num_epochs=1
)

# Train
trainer.train()

# Evaluate
metrics = trainer.evaluate()
print(metrics)
```

---

## Text Preprocessing

### Basic Cleaning

```python
import re

def clean_text(text):
    # Lowercase
    text = text.lower()

    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)

    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)

    # Remove special characters (keep letters, numbers, spaces)
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)

    # Remove extra whitespace
    text = ' '.join(text.split())

    return text
```

### What NOT to Remove

| Keep | Why |
|------|-----|
| Punctuation (for transformers) | BERT/etc. use punctuation |
| Case (for transformers) | Some models are case-sensitive |
| Numbers (often) | Can be meaningful (prices, dates) |
| Stopwords (usually) | TF-IDF handles; transformers need them |

### Preprocessing by Technique

| Technique | Preprocessing |
|-----------|---------------|
| TF-IDF | Lower, remove URLs/emails, optional stopwords |
| FastText | Lower, minimal cleaning |
| BERT/Transformers | Minimal—tokenizer handles it |

---

## Handling Class Imbalance

Same principles as classification. Text-specific notes:

### Data Augmentation

| Technique | How | Library |
|-----------|-----|---------|
| **Synonym replacement** | Replace words with synonyms | `nlpaug` |
| **Back translation** | Translate to another language and back | `googletrans` |
| **Random insertion/deletion** | Add/remove random words | `nlpaug` |
| **Paraphrase generation** | Use model to rephrase | `transformers` |

```python
import nlpaug.augmenter.word as naw

# Synonym augmentation
aug = naw.SynonymAug(aug_src='wordnet')
augmented_text = aug.augment(original_text)
```

### Class Weights

```python
from sklearn.utils.class_weight import compute_class_weight

class_weights = compute_class_weight('balanced', classes=np.unique(y), y=y)
# Pass to model training
```

---

## Multilabel Classification

When text can have multiple labels simultaneously.

### Approach

```python
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.multiclass import OneVsRestClassifier

# Convert labels to binary matrix
mlb = MultiLabelBinarizer()
y_train_bin = mlb.fit_transform(y_train)  # y_train is list of lists
y_test_bin = mlb.transform(y_test)

# Wrap classifier
model = OneVsRestClassifier(
    Pipeline([
        ('tfidf', TfidfVectorizer(max_features=10000)),
        ('clf', LogisticRegression())
    ])
)
model.fit(X_train, y_train_bin)

# Predict
y_pred = model.predict(X_test)

# Metrics for multilabel
from sklearn.metrics import hamming_loss, f1_score
print(f"Hamming Loss: {hamming_loss(y_test_bin, y_pred):.3f}")
print(f"F1 (micro): {f1_score(y_test_bin, y_pred, average='micro'):.3f}")
```

### Threshold Tuning

Default 0.5 threshold may not be optimal per label.

```python
# Get probabilities
probs = model.predict_proba(X_test)

# Find optimal threshold per label
from sklearn.metrics import f1_score
for i, label in enumerate(mlb.classes_):
    best_threshold = 0.5
    best_f1 = 0
    for t in np.arange(0.1, 0.9, 0.05):
        pred = (probs[:, i] > t).astype(int)
        f1 = f1_score(y_test_bin[:, i], pred)
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = t
    print(f"{label}: threshold={best_threshold:.2f}, F1={best_f1:.3f}")
```

---

## Evaluation Metrics

| Metric | Use When | Notes |
|--------|----------|-------|
| **Accuracy** | Balanced classes | Can be misleading |
| **Precision/Recall/F1** | Imbalanced, care about specific class | Per-class and averaged |
| **Macro F1** | All classes equally important | Unweighted average |
| **Weighted F1** | Account for class frequency | Weighted by support |
| **Hamming Loss** | Multilabel | Fraction of wrong labels |
| **Confusion Matrix** | Understand errors | Where is model confused |

### Error Analysis

Beyond metrics, manually review errors:

```python
# Find misclassified examples
errors = X_test[y_pred != y_test]
error_true = y_test[y_pred != y_test]
error_pred = y_pred[y_pred != y_test]

# Create error analysis dataframe
error_df = pd.DataFrame({
    'text': errors,
    'true_label': error_true,
    'predicted': error_pred
})

# Look for patterns
print(error_df.groupby(['true_label', 'predicted']).size())
```

---

## Libraries

### Traditional ML

| Library | Use Case | Install |
|---------|----------|---------|
| **scikit-learn** | TF-IDF, classifiers | `pip install scikit-learn` |
| **nlpaug** | Data augmentation | `pip install nlpaug` |
| **nltk** | Preprocessing, stopwords | `pip install nltk` |
| **spaCy** | Preprocessing, fast tokenization | `pip install spacy` |

### Deep Learning

| Library | Use Case | Install |
|---------|----------|---------|
| **transformers** | BERT, RoBERTa, etc. | `pip install transformers` |
| **datasets** | HuggingFace datasets | `pip install datasets` |
| **setfit** | Few-shot learning | `pip install setfit` |
| **sentence-transformers** | Embeddings | `pip install sentence-transformers` |

---

## Production Considerations

### Latency Comparison

| Technique | Typical Latency | Batch Throughput |
|-----------|-----------------|------------------|
| TF-IDF + LR | <1ms | 10,000+/sec |
| FastText | <1ms | 10,000+/sec |
| DistilBERT | 10-50ms | 100-500/sec (GPU) |
| RoBERTa | 50-100ms | 50-200/sec (GPU) |
| SetFit | 10-30ms | 200-500/sec (GPU) |

### Optimization Strategies

| Strategy | How | Speedup |
|----------|-----|---------|
| **Quantization** | Reduce precision | 2-4x |
| **Distillation** | Train smaller model on larger | 2-10x |
| **ONNX export** | Optimize inference | 2-3x |
| **Batch inference** | Process multiple texts | Linear |
| **Caching** | Cache frequent inputs | Variable |

```python
# ONNX export for transformers
from transformers import AutoTokenizer
from optimum.onnxruntime import ORTModelForSequenceClassification

model = ORTModelForSequenceClassification.from_pretrained(
    "model_path",
    export=True
)
# Faster inference with ONNX runtime
```

### Model Serving

| Option | Best For |
|--------|----------|
| **REST API (FastAPI)** | Low-medium volume |
| **gRPC** | High performance |
| **Triton Inference Server** | GPU, high scale |
| **TensorFlow Serving** | TF models |
| **HuggingFace Inference Endpoints** | Managed, quick deploy |

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Overfitting on training text | Great train, poor test | More data, regularization, augmentation |
| Data leakage from preprocessing | Unrealistic accuracy | Fit TF-IDF on train only |
| Label noise | Inconsistent predictions | Audit labels, use confident learning |
| Domain mismatch | Model fails on real data | Fine-tune on domain data |
| Ignoring class imbalance | Majority class always predicted | Class weights, resampling |
| Over-preprocessing | Lose important signal | Minimal preprocessing for transformers |

---

## Checklist Before Production

- [ ] TF-IDF + Logistic Regression baseline established
- [ ] Transformer only if baseline insufficient
- [ ] Text preprocessing consistent train/inference
- [ ] Class imbalance handled
- [ ] Error analysis performed (understand failure modes)
- [ ] Latency requirements met
- [ ] Confidence threshold set (reject low-confidence)
- [ ] Model export format chosen (ONNX, etc.)
- [ ] Human review process for edge cases
- [ ] Monitoring for distribution drift planned

---

## Quick Start Code

```python
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report
import re

# Basic cleaning
def clean_text(text):
    text = text.lower()
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return ' '.join(text.split())

# Prepare data
texts = [clean_text(t) for t in raw_texts]
X_train, X_test, y_train, y_test = train_test_split(
    texts, labels, test_size=0.2, stratify=labels, random_state=42
)

# Build pipeline
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(
        max_features=10000,
        ngram_range=(1, 2),
        min_df=2
    )),
    ('clf', LogisticRegression(
        class_weight='balanced',
        max_iter=1000
    ))
])

# Cross-validation
cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='f1_weighted')
print(f"CV F1: {cv_scores.mean():.3f} (+/- {cv_scores.std()*2:.3f})")

# Final training
pipeline.fit(X_train, y_train)

# Evaluate
y_pred = pipeline.predict(X_test)
print(classification_report(y_test, y_pred))

# Example prediction
new_text = clean_text("This is a new text to classify")
prediction = pipeline.predict([new_text])[0]
probabilities = pipeline.predict_proba([new_text])[0]
print(f"Predicted: {prediction}")
print(f"Confidence: {max(probabilities):.3f}")
```

---

## Further Reading

| Resource | Type | URL |
|----------|------|-----|
| HuggingFace Text Classification | Tutorial | https://huggingface.co/docs/transformers/tasks/sequence_classification |
| SetFit Documentation | Library | https://huggingface.co/docs/setfit |
| Text Classification with scikit-learn | Tutorial | https://scikit-learn.org/stable/tutorial/text_analytics/working_with_text_data.html |
| NLP Course (HuggingFace) | Course | https://huggingface.co/learn/nlp-course |
