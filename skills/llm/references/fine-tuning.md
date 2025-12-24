# Fine-Tuning

Customize LLMs for your specific use case.

---

## When to Fine-Tune

### Fine-Tune If:

- Prompting alone isn't enough
- Have hundreds+ of examples
- Need consistent style/format
- Want cheaper inference (smaller fine-tuned model)
- Domain-specific terminology matters

### Don't Fine-Tune If:

- Few-shot prompting works
- Task is general (use bigger model)
- Data changes frequently
- Limited labeled data (<100 examples)
- Just starting (try prompting first)

---

## Fine-Tuning vs Alternatives

| Approach | Data Needed | Effort | Best For |
|----------|-------------|--------|----------|
| **Better prompting** | 0 | Low | First attempt |
| **Few-shot prompting** | 5-20 | Low | Format/style |
| **RAG** | Documents | Medium | Knowledge grounding |
| **Fine-tuning** | 100-10,000 | High | Behavior change |
| **Continued pretraining** | Millions | Very High | Domain adaptation |

---

## Methods Overview

### Full Fine-Tuning

Train all parameters. Needs lots of VRAM.

| Model | VRAM (FP16) | VRAM (FP32) |
|-------|-------------|-------------|
| 7B | 28GB | 56GB |
| 13B | 52GB | 104GB |
| 70B | 280GB | 560GB |

**3090 verdict**: Can't do full fine-tuning on anything useful.

### LoRA (Low-Rank Adaptation)

Train small adapter layers, freeze base model.

| Model | LoRA VRAM | Quality |
|-------|-----------|---------|
| 7B | 8-12GB | 95% of full |
| 13B | 14-18GB | 95% of full |
| 70B | 24GB+ (Q4) | Good |

**3090 verdict**: LoRA on 7-13B is comfortable. 70B needs quantization.

### QLoRA (Quantized LoRA)

LoRA on quantized base model. Most VRAM efficient.

| Model | QLoRA VRAM (4-bit) |
|-------|-------------------|
| 7B | 5-8GB |
| 13B | 8-12GB |
| 70B | 20-24GB |

**3090 verdict**: QLoRA on up to 70B is possible.

---

## 3090 Recommendations

| Use Case | Method | Model |
|----------|--------|-------|
| Quick experiments | QLoRA | Llama 3.1 8B |
| Best quality | QLoRA | Llama 3.1 70B |
| Balanced | LoRA | Qwen 2.5 14B |
| Code | QLoRA | DeepSeek-Coder 33B |

---

## Data Preparation

### Format

```json
{"messages": [
  {"role": "system", "content": "You are a helpful assistant."},
  {"role": "user", "content": "What is the capital of France?"},
  {"role": "assistant", "content": "The capital of France is Paris."}
]}
```

### Data Quality

| Factor | Impact | Fix |
|--------|--------|-----|
| Label quality | Critical | Manual review sample |
| Diversity | High | Cover edge cases |
| Length distribution | Medium | Match expected use |
| Format consistency | High | Standardize structure |

### Data Quantity

| Examples | Result |
|----------|--------|
| 50-100 | Minimal effect |
| 100-500 | Noticeable improvement |
| 500-2000 | Good results |
| 2000-10000 | Excellent |
| 10000+ | Diminishing returns |

### Splitting

```python
# 90/10 train/val split
from sklearn.model_selection import train_test_split

train, val = train_test_split(data, test_size=0.1, random_state=42)
```

---

## Fine-Tuning with Unsloth (Recommended for 3090)

Unsloth is 2x faster and uses 50% less memory.

### Installation

```bash
pip install unsloth
pip install --upgrade trl peft accelerate bitsandbytes
```

### QLoRA Example

```python
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import load_dataset

# Load model with 4-bit quantization
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit",
    max_seq_length=2048,
    load_in_4bit=True,
)

# Add LoRA adapters
model = FastLanguageModel.get_peft_model(
    model,
    r=16,                # LoRA rank
    lora_alpha=16,       # LoRA alpha
    lora_dropout=0,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                   "gate_proj", "up_proj", "down_proj"],
)

# Prepare data
def format_prompt(example):
    return tokenizer.apply_chat_template(
        example["messages"],
        tokenize=False
    )

dataset = load_dataset("json", data_files="train.jsonl")
dataset = dataset.map(lambda x: {"text": format_prompt(x)})

# Train
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset["train"],
    dataset_text_field="text",
    max_seq_length=2048,
    args=TrainingArguments(
        output_dir="./output",
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=10,
        num_train_epochs=3,
        learning_rate=2e-4,
        fp16=True,
        logging_steps=10,
        save_steps=100,
    ),
)

trainer.train()

# Save
model.save_pretrained("./my-model-lora")
```

### Merge and Export

```python
# Merge LoRA into base model
model = model.merge_and_unload()

# Save as GGUF for llama.cpp
model.save_pretrained_gguf("./my-model-gguf", tokenizer, quantization="q5_k_m")

# Or save as safetensors
model.save_pretrained("./my-model-merged")
```

---

## Fine-Tuning with Axolotl

More flexible, supports many configurations.

### Installation

```bash
git clone https://github.com/OpenAccess-AI-Collective/axolotl
cd axolotl
pip install -e .
```

### Config (config.yml)

```yaml
base_model: meta-llama/Meta-Llama-3.1-8B-Instruct
model_type: LlamaForCausalLM

load_in_4bit: true
adapter: qlora
lora_r: 16
lora_alpha: 16
lora_target_modules:
  - q_proj
  - k_proj
  - v_proj
  - o_proj

datasets:
  - path: train.jsonl
    type: sharegpt

sequence_len: 2048
micro_batch_size: 2
gradient_accumulation_steps: 4
num_epochs: 3
learning_rate: 2e-4

output_dir: ./output
```

### Run

```bash
accelerate launch -m axolotl.cli.train config.yml
```

---

## API Fine-Tuning

### OpenAI

```python
from openai import OpenAI
client = OpenAI()

# Upload file
file = client.files.create(
    file=open("train.jsonl", "rb"),
    purpose="fine-tune"
)

# Create fine-tuning job
job = client.fine_tuning.jobs.create(
    training_file=file.id,
    model="gpt-4o-mini-2024-07-18"
)

# Check status
status = client.fine_tuning.jobs.retrieve(job.id)
print(status.status)

# Use fine-tuned model
response = client.chat.completions.create(
    model="ft:gpt-4o-mini-2024-07-18:org:custom:id",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Together.ai

```python
import together

# Upload
file_id = together.Files.upload(file="train.jsonl")

# Fine-tune
job = together.FineTuning.create(
    training_file=file_id,
    model="meta-llama/Meta-Llama-3.1-8B-Instruct",
    n_epochs=3
)

# Use
response = together.Complete.create(
    model=job.output_name,
    prompt="Hello"
)
```

---

## Hyperparameters

| Parameter | Description | Typical Range |
|-----------|-------------|---------------|
| **learning_rate** | Step size | 1e-5 to 2e-4 |
| **epochs** | Full passes through data | 1-5 |
| **batch_size** | Samples per step | 2-8 (limited by VRAM) |
| **grad_accum** | Virtual batch size | 4-16 |
| **lora_r** | LoRA rank | 8, 16, 32, 64 |
| **lora_alpha** | LoRA scaling | Usually = lora_r |
| **max_seq_length** | Context length | 512-4096 |

### 3090 Starting Point

```python
# QLoRA on 8B model
learning_rate = 2e-4
batch_size = 2
gradient_accumulation = 4  # Effective batch = 8
epochs = 3
lora_r = 16
max_seq_length = 2048
```

---

## Evaluation

### Metrics

| Metric | What It Measures |
|--------|------------------|
| **Loss** | Training progress (should decrease) |
| **Perplexity** | Model confidence (lower = better) |
| **Task accuracy** | Correct answers on held-out set |
| **Human eval** | Quality rating by humans |

### Overfitting Signs

- Train loss decreases, val loss increases
- Perfect on training examples, poor on new ones
- Memorization of specific phrasings

### Fixes

- More data
- Fewer epochs
- Lower learning rate
- More regularization (dropout)

---

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| OOM | Model too big | Reduce batch size, use QLoRA |
| Loss doesn't decrease | LR too low or data issue | Increase LR, check data |
| Loss spikes | LR too high | Decrease LR |
| Poor quality | Not enough data | More/better data |
| Format wrong | Template mismatch | Use correct chat template |

---

## Checklist

- [ ] Prompting alone tried first
- [ ] Data quality verified (sample review)
- [ ] Data formatted correctly (chat template)
- [ ] Train/val split created
- [ ] Base model selected
- [ ] VRAM requirements calculated
- [ ] Training completed without OOM
- [ ] Loss curve looks healthy
- [ ] Evaluated on held-out examples
- [ ] Model exported (GGUF or safetensors)

---

## Quick Reference: 3090 Limits

```
Full fine-tune: Not practical (need multi-GPU)

LoRA FP16:
├── 7B:  Comfortable (~12GB)
├── 13B: Tight (~18GB)
└── 70B: No

QLoRA 4-bit:
├── 7B:  Easy (~6GB)
├── 13B: Easy (~10GB)
├── 33B: Comfortable (~18GB)
└── 70B: Tight (~22-24GB)
```

---

## Further Reading

| Resource | Type | URL |
|----------|------|-----|
| Unsloth | Library | https://github.com/unslothai/unsloth |
| Axolotl | Library | https://github.com/OpenAccess-AI-Collective/axolotl |
| LoRA Paper | Paper | https://arxiv.org/abs/2106.09685 |
| QLoRA Paper | Paper | https://arxiv.org/abs/2305.14314 |
| OpenAI Fine-tuning | Docs | https://platform.openai.com/docs/guides/fine-tuning |
