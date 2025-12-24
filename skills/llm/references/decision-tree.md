# LLM Problem Type Decision Tree

Navigate from your goal to the right approach.

---

## Quick Decision Flow

```
What do you want the LLM to do?
│
├─► GENERATE text from scratch
│   └─► generation.md
│
├─► TRANSFORM existing text
│   ├─► Shorten → summarization.md
│   ├─► Translate → generation.md (with prompt)
│   ├─► Rewrite/rephrase → generation.md
│   └─► Extract structure → classification-extraction.md
│
├─► ANSWER questions
│   ├─► From provided context → question-answering.md
│   ├─► From your documents → rag.md
│   └─► General knowledge → generation.md (careful: hallucination)
│
├─► CLASSIFY or EXTRACT
│   ├─► Categorize text → classification-extraction.md
│   ├─► Extract entities → classification-extraction.md
│   └─► Parse to JSON → classification-extraction.md
│
├─► WRITE or EXPLAIN code
│   └─► code-generation.md
│
├─► REASON with tools/actions
│   └─► agents.md
│
└─► ADAPT to your domain
    └─► fine-tuning.md
```

---

## Detailed Decision Matrix

### By Task

| I want to... | Problem Type | Notes |
|--------------|--------------|-------|
| Write marketing copy | Generation | Style in system prompt |
| Draft emails | Generation | Few-shot for tone |
| Create stories | Generation | Temperature for creativity |
| Summarize documents | Summarization | Control length explicitly |
| Create meeting notes | Summarization | Extractive or abstractive |
| TL;DR for articles | Summarization | Short summarization |
| Answer from a PDF | RAG | Chunk and embed first |
| Build a knowledge base bot | RAG | Vector DB + retrieval |
| Customer support bot | RAG + Generation | Combine retrieval with generation |
| Categorize tickets | Classification | Few-shot or fine-tune |
| Extract names/dates | Extraction | Structured output |
| Parse invoices | Extraction | JSON mode |
| Write Python functions | Code Generation | Code-specialized model |
| Explain code | Code Generation | Include code in context |
| Debug errors | Code Generation | Error + stack trace |
| Multi-step tasks | Agents | Tool use |
| Research + synthesis | Agents | Multiple tool calls |

### By Input/Output

| Input | Output | Approach |
|-------|--------|----------|
| Short prompt | Long text | Generation |
| Long document | Short summary | Summarization |
| Question + context | Answer | QA |
| Question + docs | Answer | RAG |
| Text | Category/label | Classification |
| Text | Structured JSON | Extraction |
| Description | Code | Code generation |
| Code | Explanation | Code generation |
| Goal + tools | Actions + result | Agents |

---

## Common Confusion Points

### Generation vs Summarization

| | Generation | Summarization |
|---|------------|---------------|
| Input length | Short prompt | Long document |
| Output length | Variable, often long | Shorter than input |
| Goal | Create new content | Compress existing |
| Hallucination risk | Higher | Lower (grounded in source) |

### QA vs RAG vs Generation

| | QA | RAG | Generation |
|---|---|-----|------------|
| Context provided? | Yes, in prompt | Retrieved | No |
| Source of truth | Given context | Your documents | Model knowledge |
| Hallucination risk | Low | Medium | High |
| Use case | Reading comprehension | Knowledge base | Creative/open |

### Classification vs Extraction

| | Classification | Extraction |
|---|----------------|------------|
| Output | Category/label | Specific values |
| Example | "This is spam" | "Email: john@example.com" |
| Structured? | Single value | Multiple fields |

### Fine-tuning vs Prompting

| | Prompting | Fine-tuning |
|---|-----------|-------------|
| Effort | Minutes | Hours-days |
| Flexibility | High (change anytime) | Low (retrain) |
| Quality | Good | Better (on your data) |
| Cost | Per-call | Upfront + cheaper calls |
| Data needed | Few examples | Hundreds-thousands |
| When | First approach | Prompting isn't enough |

---

## By Use Case Domain

### Customer Support

| Task | Approach |
|------|----------|
| Answer FAQs | RAG on knowledge base |
| Route tickets | Classification |
| Draft responses | Generation with templates |
| Summarize conversations | Summarization |

### Content Creation

| Task | Approach |
|------|----------|
| Blog posts | Generation |
| Social media | Generation (short) |
| Email campaigns | Generation + few-shot |
| Product descriptions | Generation with structure |

### Data Processing

| Task | Approach |
|------|----------|
| Parse documents | Extraction |
| Categorize content | Classification |
| Standardize formats | Extraction + Generation |
| Entity recognition | Extraction |

### Developer Tools

| Task | Approach |
|------|----------|
| Code completion | Code Generation |
| Code review | Code Generation + Analysis |
| Documentation | Generation from code |
| Bug diagnosis | Code Generation + Agents |

### Research & Analysis

| Task | Approach |
|------|----------|
| Literature review | RAG + Summarization |
| Competitive analysis | Agents (web tools) |
| Report generation | RAG + Generation |
| Data synthesis | Summarization |

---

## Decision Checklist

Before proceeding:

- [ ] I can clearly state what the LLM should do
- [ ] I know the input format (short prompt, long doc, structured)
- [ ] I know the output format (text, JSON, categories)
- [ ] I've considered if simpler methods work
- [ ] I understand the hallucination risk for this task

---

## Next Steps by Problem Type

| Problem Type | Next Document | Key Questions |
|--------------|---------------|---------------|
| Generation | `generation.md` | Creativity? Format? Length? |
| Summarization | `summarization.md` | Ratio? Extractive/abstractive? |
| Question Answering | `question-answering.md` | Context length? Multi-hop? |
| RAG | `rag.md` | Corpus size? Update frequency? |
| Classification/Extraction | `classification-extraction.md` | Schema? Multi-label? |
| Code Generation | `code-generation.md` | Language? Complexity? |
| Agents | `agents.md` | Tools needed? Safety? |
| Fine-tuning | `fine-tuning.md` | Data available? Budget? |
