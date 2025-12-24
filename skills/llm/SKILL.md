---
name: llm
description: Large Language Model integration guide for adding LLM capabilities to applications. Problem-first guidance for text generation, summarization, question answering, RAG, agents, code generation, and fine-tuning. Covers local deployment (optimized for RTX 3090/24GB VRAM), API usage, prompting strategies, and production patterns. Focuses on practical application, not research.
---

# Large Language Model Integration Guide v0.1.0

Add LLM capabilities to your applications—locally or via API.

## Hardware Context

This guide is optimized for **RTX 3090 (24GB VRAM)**. Model recommendations account for this constraint.

| VRAM | What Fits (FP16) | What Fits (Quantized) |
|------|------------------|----------------------|
| 24GB | 7-13B models | 70B models (4-bit) |
| 24GB | Full fine-tune 7B | LoRA fine-tune 13B |

---

## Purpose

This skill helps you:

1. **Decide IF** an LLM is the right approach (often overkill)
2. **Choose HOW** to access LLMs (local vs API)
3. **Select WHICH** model fits your constraints
4. **Implement WHAT** pattern solves your problem
5. **Optimize FOR** cost, latency, and quality

---

## Quick Start

```
┌─────────────────────────────────────────────────────────────────┐
│                    LLM DECISION WORKFLOW                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. FEASIBILITY   →  Is an LLM the right tool?                  │
│     └─► See: Feasibility Checklist (below)                      │
│                                                                 │
│  2. PROBLEM TYPE  →  What are you trying to do?                 │
│     └─► See: references/decision-tree.md                        │
│                                                                 │
│  3. ACCESS MODE   →  Local or API?                              │
│     └─► See: references/model-selection.md                      │
│                                                                 │
│  4. MODEL         →  Which model fits?                          │
│     └─► See: references/model-selection.md                      │
│                                                                 │
│  5. PROMPTING     →  How to get good outputs?                   │
│     └─► See: references/prompting.md                            │
│                                                                 │
│  6. DEPLOYMENT    →  How to serve in production?                │
│     └─► See: references/deployment.md                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Feasibility Checklist

**Complete this BEFORE choosing a model.**

### Hard Requirements (Must Have ALL)

- [ ] **Task is language-based** — Text in, text out (or structured output)
- [ ] **Acceptable latency** — Can tolerate 100ms-10s response times
- [ ] **Error tolerance** — Some wrong/hallucinated outputs are acceptable
- [ ] **No real-time data needed** — Or you can provide it via RAG/tools

### Soft Requirements (Need MOST)

- [ ] **Task is hard to specify with rules** — If rules work, use rules
- [ ] **Diverse inputs expected** — Not the same query repeated
- [ ] **Output quality > determinism** — Same input may give different outputs
- [ ] **Have examples for evaluation** — Can measure quality somehow
- [ ] **Budget allows** — API costs or GPU infrastructure

### Red Flags (Any = Reconsider)

- [ ] Need 100% accuracy (LLMs hallucinate)
- [ ] Task is purely computational (use code instead)
- [ ] Latency must be <50ms (LLMs are slow)
- [ ] Must be deterministic (LLMs are stochastic)
- [ ] Data is highly sensitive + can't use local models
- [ ] Simple classification with training data (use traditional ML)

### Feasibility Verdict

| Checkboxes | Verdict |
|------------|---------|
| All Hard + Most Soft + No Red Flags | **Proceed with LLM** |
| All Hard + Some Soft + No Red Flags | **Proceed cautiously**, start simple |
| Missing Hard requirements | **Do not use LLM** — wrong tool |
| Multiple Red Flags | **Reconsider** — see `when-not-to-use-llm.md` |

---

## Problem Type Quick Reference

| You want to... | Problem Type | Reference |
|----------------|--------------|-----------|
| Generate text from a prompt | Generation | `references/generation.md` |
| Condense long text to short | Summarization | `references/summarization.md` |
| Answer questions from context | Question Answering | `references/question-answering.md` |
| Answer from your documents | RAG | `references/rag.md` |
| Write or explain code | Code Generation | `references/code-generation.md` |
| Categorize or extract from text | Classification/Extraction | `references/classification-extraction.md` |
| Perform multi-step reasoning with tools | Agents | `references/agents.md` |
| Customize model for your domain | Fine-tuning | `references/fine-tuning.md` |

---

## Local vs API Decision

### Quick Selector

| Factor | Local (3090) | API (OpenAI, Anthropic, etc.) |
|--------|--------------|-------------------------------|
| **Privacy** | Data stays on your machine | Data sent to provider |
| **Cost at scale** | Fixed (electricity) | Per-token, adds up |
| **Cost to start** | High (GPU) | Low (pay as you go) |
| **Latency** | Lower (no network) | Higher (network + queue) |
| **Model quality** | Good (7-70B) | Best (GPT-4, Claude) |
| **Maintenance** | You manage | Provider manages |
| **Offline capable** | Yes | No |

### Recommendation

| Scenario | Recommendation |
|----------|----------------|
| Prototyping | API (faster to start) |
| Privacy-critical | Local |
| High volume (>1M tokens/day) | Local (cost effective) |
| Need best quality | API (GPT-4, Claude 3.5) |
| Offline/edge deployment | Local |
| Unpredictable volume | API (scales automatically) |

---

## Model Selection Overview (3090 Focus)

### Local Models That Fit 24GB VRAM

| Model | Size | VRAM (FP16) | VRAM (Q4) | Quality | Speed |
|-------|------|-------------|-----------|---------|-------|
| **Llama 3.1 8B** | 8B | 16GB | 5GB | Good | Fast |
| **Mistral 7B** | 7B | 14GB | 4GB | Good | Fast |
| **Llama 3.1 70B** | 70B | — | 20-24GB | Excellent | Slow |
| **Qwen 2.5 14B** | 14B | — | 8GB | Very Good | Medium |
| **Qwen 2.5 72B** | 72B | — | 22-24GB | Excellent | Slow |
| **DeepSeek-Coder 33B** | 33B | — | 18GB | Excellent (code) | Medium |
| **Phi-3 Medium 14B** | 14B | — | 8GB | Very Good | Medium |

### Quantization Guide

| Quantization | Quality Loss | VRAM Reduction | When to Use |
|--------------|--------------|----------------|-------------|
| **FP16** | None | Baseline | Fits in VRAM |
| **Q8** | Minimal | ~50% | Slight squeeze |
| **Q6_K** | Very small | ~60% | Good balance |
| **Q5_K_M** | Small | ~65% | Most common |
| **Q4_K_M** | Noticeable | ~75% | Larger models |
| **Q3** | Significant | ~80% | Last resort |

### API Models

| Provider | Model | Quality | Cost (1M tokens) |
|----------|-------|---------|------------------|
| **Anthropic** | Claude 3.5 Sonnet | Excellent | ~$15 |
| **OpenAI** | GPT-4o | Excellent | ~$15 |
| **OpenAI** | GPT-4o-mini | Very Good | ~$0.60 |
| **Anthropic** | Claude 3 Haiku | Good | ~$1 |
| **Google** | Gemini 1.5 Pro | Excellent | ~$7 |
| **Google** | Gemini 1.5 Flash | Good | ~$0.30 |

---

## Prompting Principles Overview

### Core Techniques

| Technique | When | Example |
|-----------|------|---------|
| **Zero-shot** | Simple tasks | "Summarize this text:" |
| **Few-shot** | Need format/style | "Here are examples... Now do:" |
| **Chain-of-thought** | Reasoning needed | "Think step by step" |
| **System prompts** | Set behavior/persona | "You are a helpful assistant that..." |
| **Structured output** | Need JSON/schema | "Respond in JSON with fields..." |

### Prompt Structure

```
[System: Role and constraints]
[Context: Background information]
[Examples: Few-shot demonstrations]
[Task: What to do]
[Format: How to respond]
```

See `references/prompting.md` for detailed patterns.

---

## Integration Patterns Overview

| Pattern | Complexity | Use Case |
|---------|------------|----------|
| **Single prompt** | Low | One-off generation |
| **Prompt chain** | Medium | Multi-step processing |
| **RAG** | Medium | Answer from documents |
| **Agent loop** | High | Tool use, multi-step reasoning |
| **Fine-tuned model** | High | Domain adaptation |

---

## Reference Documents

### Decision Support
| Document | Purpose |
|----------|---------|
| `decision-tree.md` | Problem type selector |
| `when-not-to-use-llm.md` | Alternatives to LLMs |

### Problem Types
| Document | Purpose |
|----------|---------|
| `generation.md` | Text generation patterns |
| `summarization.md` | Document summarization |
| `question-answering.md` | Q&A from context |
| `rag.md` | Retrieval Augmented Generation |
| `code-generation.md` | Code writing and explanation |
| `classification-extraction.md` | Structured extraction |
| `agents.md` | Tool use and multi-step reasoning |
| `fine-tuning.md` | Model customization |

### Cross-Cutting
| Document | Purpose |
|----------|---------|
| `model-selection.md` | Choosing the right model |
| `prompting.md` | Prompt engineering patterns |
| `deployment.md` | Local and API deployment |
| `evaluation.md` | Measuring LLM quality |
| `cost-optimization.md` | Reducing costs |

---

## Usage Examples

### Example 1: "Should I use an LLM for this?"

**Situation**: Categorize support tickets into 5 departments.

**Analysis**:
- Have 10,000 labeled tickets? → Use traditional ML classifier
- Only 50 examples? → LLM with few-shot might work
- Categories well-defined? → Try rules first

**Verdict**: If you have training data, traditional ML is faster and cheaper. LLM is fallback.

### Example 2: "Which model should I use?"

**Situation**: Build a coding assistant, running locally.

**Requirements**:
- Code generation quality matters
- 24GB VRAM available
- Low latency preferred

**Recommendation**:
1. Start with DeepSeek-Coder-V2-Lite (16B) or Qwen2.5-Coder-14B
2. Use Q5_K_M quantization if needed
3. Fallback to API for complex cases

### Example 3: "How do I add chat to my app?"

**Situation**: Add conversational AI to customer support app.

**Process**:
1. Define scope (what can/can't the bot do)
2. Choose RAG if needs to reference docs
3. Use system prompt to set behavior
4. Add human escalation for failures
5. Monitor and iterate on prompts

---

## Quality Standards

### What Makes Good LLM Integration

| Quality | Indicator |
|---------|-----------|
| **Scoped** | Clear boundaries on what LLM does |
| **Fallback-ready** | Graceful handling of failures |
| **Evaluated** | Metrics to measure quality |
| **Monitored** | Logging of inputs/outputs |
| **Cost-aware** | Tracking token usage |
| **Iterative** | Prompt improvement process |

### Red Flags in LLM Projects

- No evaluation dataset
- "Just call GPT-4" without prompting thought
- No fallback for API failures
- Unbounded context windows (cost explosion)
- No rate limiting
- Trusting outputs without validation

---

## 3090 Quick Reference

### What Fits

```
FP16 (full precision):
├── Llama 3.1 8B      ✓ (16GB)
├── Mistral 7B        ✓ (14GB)
├── Phi-3 Medium      ✓ (14GB)
└── Qwen 2.5 14B      ✗ (needs 28GB)

Q4 Quantized:
├── Llama 3.1 70B     ✓ (20-24GB, tight)
├── Qwen 2.5 72B      ✓ (22-24GB, tight)
├── DeepSeek 33B      ✓ (18GB)
└── Mixtral 8x7B      ✓ (22GB)
```

### Recommended Stack

```
Inference: vLLM, llama.cpp, or Ollama
Quantization: GGUF format (llama.cpp compatible)
API wrapper: LiteLLM (unified interface)
Framework: LangChain or direct API calls
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2025-01 | Initial version — 3090 optimized |
