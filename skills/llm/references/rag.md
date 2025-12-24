# RAG (Retrieval Augmented Generation)

Answer questions from your own documents.

---

## What is RAG?

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Query     │────▶│  Retrieve   │────▶│  Generate   │
│             │     │  Relevant   │     │  Answer     │
│             │     │  Documents  │     │  with LLM   │
└─────────────┘     └─────────────┘     └─────────────┘
                          │
                    ┌─────────────┐
                    │   Vector    │
                    │   Store     │
                    └─────────────┘
```

**Why RAG?**
- LLMs don't know your private data
- LLMs have knowledge cutoffs
- RAG grounds responses in sources (less hallucination)
- Cheaper than fine-tuning

---

## When to Use RAG

**Good for:**
- Q&A over documentation
- Customer support from knowledge base
- Research over internal documents
- Search with natural language

**Not good for:**
- Real-time data (use tools/APIs instead)
- Computation (use code)
- Pure generation (no retrieval needed)
- Very small document sets (just put in context)

---

## RAG Architecture

### Simple RAG

```python
def simple_rag(question, collection, llm):
    # 1. Retrieve
    results = collection.query(query_texts=[question], n_results=5)
    context = "\n\n".join(results['documents'][0])

    # 2. Generate
    prompt = f"""Answer based on the context below.
    If not in context, say "I don't know."

    Context: {context}

    Question: {question}

    Answer:"""

    return llm.generate(prompt)
```

### Advanced RAG

```
Query
  │
  ├─► Query Rewriting (optional)
  │
  ├─► Hybrid Retrieval (dense + sparse)
  │
  ├─► Reranking (cross-encoder)
  │
  ├─► Context Compression (optional)
  │
  └─► Generation with Citations
```

---

## Chunking Strategies

### Methods

| Method | How | Best For |
|--------|-----|----------|
| **Fixed size** | Split every N tokens | Simple, general |
| **Recursive** | Try larger splits first | General purpose |
| **Semantic** | Cluster by meaning | Quality-critical |
| **Document-aware** | Respect headers/sections | Markdown, HTML |

### Chunk Size

| Size | Tokens | Pros | Cons |
|------|--------|------|------|
| Small | 100-300 | Precise retrieval | Loses context |
| Medium | 300-500 | Balanced | Most common |
| Large | 500-1000 | More context | Less precise |

### Implementation

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " ", ""]
)
chunks = splitter.split_text(document)
```

---

## Embedding Models (3090)

### Local

| Model | Dims | VRAM | Quality |
|-------|------|------|---------|
| **bge-large-en-v1.5** | 1024 | 2GB | Excellent |
| **nomic-embed-text** | 768 | 1GB | Very Good |
| **gte-large** | 1024 | 2GB | Excellent |

### Implementation

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('BAAI/bge-large-en-v1.5')
embeddings = model.encode(chunks, show_progress_bar=True)
```

---

## Vector Stores

### Local Options

| Store | Setup | Best For |
|-------|-------|----------|
| **ChromaDB** | `pip install chromadb` | Getting started |
| **LanceDB** | `pip install lancedb` | Simple, fast |
| **Qdrant** | Docker | Production |
| **FAISS** | `pip install faiss-gpu` | Pure Python |

### ChromaDB Example

```python
import chromadb
from chromadb.utils import embedding_functions

client = chromadb.PersistentClient(path="./chroma_db")

ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-large-en-v1.5"
)

collection = client.create_collection("docs", embedding_function=ef)

# Add documents
collection.add(
    documents=chunks,
    ids=[f"chunk_{i}" for i in range(len(chunks))],
    metadatas=[{"source": "doc.pdf"} for _ in chunks]
)

# Query
results = collection.query(
    query_texts=["What is the return policy?"],
    n_results=5
)
```

---

## Retrieval Strategies

### Top-K (Basic)

```python
results = collection.query(query, n_results=5)
```

### MMR (Diversity)

```python
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 5, "lambda_mult": 0.7}
)
```

### Hybrid (Dense + Sparse)

```python
from rank_bm25 import BM25Okapi

bm25 = BM25Okapi([c.split() for c in chunks])
bm25_scores = bm25.get_scores(query.split())
final = 0.7 * dense_scores + 0.3 * bm25_scores
```

### Reranking

```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')
pairs = [[query, doc] for doc in initial_results]
scores = reranker.predict(pairs)
```

---

## Generation Prompts

### Basic

```python
prompt = f"""Answer based on the context below.
If not in context, say "I don't have that information."

Context:
{context}

Question: {question}

Answer:"""
```

### With Citations

```python
prompt = f"""Answer using the numbered sources below.
Cite sources like [1], [2].

Sources:
[1] {chunk_1}
[2] {chunk_2}
[3] {chunk_3}

Question: {question}

Answer:"""
```

### Conversational

```python
prompt = f"""You are a helpful assistant.

Chat history:
{history}

Context from knowledge base:
{context}

User: {question}
Assistant:"""
```

---

## Evaluation Metrics

| Metric | What It Measures |
|--------|------------------|
| **Retrieval Precision** | % of retrieved chunks that are relevant |
| **Retrieval Recall** | % of relevant chunks that were retrieved |
| **Answer Accuracy** | Is the answer correct? |
| **Faithfulness** | Is answer grounded in context? |
| **Hallucination Rate** | % of claims not in context |

### RAGAS Framework

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy

result = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy]
)
```

---

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Wrong answers | Poor retrieval | Better chunking, reranking |
| "I don't know" too often | Chunks too small | Larger chunks, more k |
| Hallucinations | Ignoring context | Stronger prompt constraints |
| Slow | Large context | Fewer chunks, compression |
| Irrelevant results | Embedding mismatch | Try different embeddings |

---

## Production Checklist

- [ ] Chunking strategy chosen and tested
- [ ] Embedding model selected
- [ ] Vector store deployed and persisted
- [ ] Retrieval strategy tuned (k, reranking)
- [ ] Generation prompt tested
- [ ] Evaluation dataset created
- [ ] Hallucination rate measured
- [ ] Latency acceptable
- [ ] Update pipeline for new documents

---

## Full Example

```python
import chromadb
from sentence_transformers import SentenceTransformer
from openai import OpenAI

# Setup
embed_model = SentenceTransformer('BAAI/bge-large-en-v1.5')
client = chromadb.PersistentClient("./db")
collection = client.get_or_create_collection("docs")
llm = OpenAI()

# Ingest (one-time)
def ingest(documents):
    for i, doc in enumerate(documents):
        chunks = chunk_document(doc)
        embeddings = embed_model.encode(chunks)
        collection.add(
            ids=[f"{i}_{j}" for j in range(len(chunks))],
            documents=chunks,
            embeddings=embeddings.tolist()
        )

# Query
def ask(question):
    # Retrieve
    query_emb = embed_model.encode([question])
    results = collection.query(
        query_embeddings=query_emb.tolist(),
        n_results=5
    )
    context = "\n\n".join(results['documents'][0])

    # Generate
    response = llm.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"""Answer from context. Say "I don't know" if not found.

Context: {context}

Question: {question}"""
        }]
    )
    return response.choices[0].message.content

# Use
answer = ask("What is the return policy?")
```

---

## Further Reading

| Resource | Type | URL |
|----------|------|-----|
| LangChain RAG | Docs | https://python.langchain.com/docs/use_cases/question_answering/ |
| LlamaIndex | Library | https://docs.llamaindex.ai/ |
| ChromaDB | Docs | https://docs.trychroma.com/ |
| RAGAS | Evaluation | https://docs.ragas.io/ |
