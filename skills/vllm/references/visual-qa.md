# Visual Question Answering

Answer specific questions about image content.

---

## What is Visual QA?

```
┌─────────────┐
│   Image     │────┐
└─────────────┘    │     ┌─────────────┐     ┌─────────────┐
                   ├────▶│    VLM      │────▶│   Answer    │
┌─────────────┐    │     └─────────────┘     └─────────────┘
│  Question   │────┘
└─────────────┘
```

**Core task**: Answer questions grounded in visual content.

---

## Question Types

| Type | Example | Difficulty |
|------|---------|------------|
| **Existence** | "Is there a cat?" | Easy |
| **Counting** | "How many people?" | Medium |
| **Color** | "What color is the car?" | Easy |
| **Location** | "Where is the ball?" | Medium |
| **Comparison** | "Which is larger?" | Medium |
| **Reading** | "What does the sign say?" | Easy |
| **Reasoning** | "Why is she smiling?" | Hard |
| **Temporal** | "What happened before?" | Hard |

---

## Prompting Patterns

### Basic Question

```python
# Simple question
prompt = "How many dogs are in this image?"

# Better: Constrain answer format
prompt = "How many dogs are in this image? Answer with just a number."

# Best: Handle uncertainty
prompt = """How many dogs are in this image?
Answer with just a number.
If you can't determine exactly, give your best estimate and explain."""
```

### Yes/No Questions

```python
prompt = """Is there a stop sign in this image?

Answer exactly: "Yes" or "No"
Then briefly explain what you see."""
```

### Multiple Choice

```python
prompt = """What type of weather is shown in this image?

Options:
A) Sunny
B) Cloudy
C) Rainy
D) Snowy

Answer with just the letter."""
```

### Open-Ended

```python
prompt = """Look at this image and answer: What activity are the people engaged in?

Provide:
1. Your answer (1-2 sentences)
2. Visual evidence supporting your answer"""
```

---

## Advanced Patterns

### Chain-of-Thought Visual Reasoning

```python
prompt = """Look at this image and answer: Is this a safe working environment?

Think step by step:
1. Identify the setting
2. List any safety equipment visible
3. Note any hazards
4. Give your assessment with reasoning

Then provide your final answer: Safe / Unsafe / Cannot determine"""
```

### Grounding (Coordinates)

```python
# Qwen2-VL supports coordinate output
prompt = """Where is the red car in this image?

Return the bounding box coordinates as:
{
  "object": "red car",
  "bbox": [x1, y1, x2, y2],
  "confidence": "high|medium|low"
}

Coordinates should be normalized (0-1) relative to image dimensions."""
```

### Multi-Image Comparison

```python
prompt = """I'm showing you two images of the same room.

Questions:
1. What objects are in Image 1 but not Image 2?
2. What objects are in Image 2 but not Image 1?
3. What has changed position?

List each difference clearly."""
```

### Verification Questions

```python
prompt = """Verify the following statement about this image:
Statement: "There are three blue chairs around a wooden table."

Check each claim:
1. Are there chairs? How many?
2. Are they blue?
3. Is there a table?
4. Is it wooden?
5. Are chairs around it?

Final verdict: TRUE / FALSE / PARTIALLY TRUE"""
```

---

## Domain-Specific Patterns

### E-commerce

```python
prompt = """Answer these product questions based on the image:

1. What is the product category?
2. What color options are visible?
3. What size is shown (if indicated)?
4. Is the product new or used?
5. Are there any visible defects?

Return as JSON."""
```

### Medical (Non-diagnostic)

```python
prompt = """Describe what you observe in this medical image.

Note: This is for documentation only, not diagnosis.

Questions:
1. What type of medical image is this?
2. What anatomical region is shown?
3. What visible features can you describe objectively?

Do NOT provide diagnostic conclusions."""
```

### Technical/Engineering

```python
prompt = """Analyze this technical diagram:

1. What type of diagram is this?
2. What components are labeled?
3. What connections/relationships are shown?
4. Are there any measurements or specifications visible?"""
```

### Quality Control

```python
prompt = """Inspect this product image for quality issues:

1. Are there visible defects? (scratches, dents, discoloration)
2. Is the product properly assembled?
3. Does it match the expected appearance?
4. Quality rating: Pass / Marginal / Fail

Explain your assessment."""
```

---

## Handling Uncertainty

### Explicit Uncertainty

```python
prompt = """Answer this question about the image: {question}

If you're uncertain:
- Say "I'm not certain, but..." and give your best answer
- Explain what makes you uncertain
- Rate confidence: High / Medium / Low"""
```

### Avoid Hallucination

```python
prompt = """Answer based ONLY on what's visible in the image.

Question: {question}

Rules:
- Only state what you can directly observe
- If information isn't visible, say "Cannot determine from image"
- Don't make assumptions about non-visible elements"""
```

---

## Multi-Turn Visual QA

### Follow-up Questions

```python
conversation = [
    {"role": "user", "content": [
        {"type": "image", "image": image_data},
        {"type": "text", "text": "Describe this room."}
    ]},
    {"role": "assistant", "content": "This is a modern living room with..."},
    {"role": "user", "content": "What style of furniture is shown?"},
    {"role": "assistant", "content": "The furniture appears to be..."},
    {"role": "user", "content": "Is there anything on the coffee table?"}
]
```

### Clarifying Questions

```python
prompt = """Answer this question about the image: {question}

If the question is ambiguous:
1. State the ambiguity
2. Provide answers for each interpretation
3. Ask for clarification if needed"""
```

---

## Model Selection for Visual QA

### Local (3090)

| Model | QA Quality | Reasoning | Grounding | VRAM |
|-------|------------|-----------|-----------|------|
| **Qwen2-VL 7B** | Excellent | Good | Yes | 16GB |
| **Qwen2-VL 72B (Q4)** | Excellent | Excellent | Yes | 24GB |
| **LLaVA 7B** | Good | Good | No | 14GB |
| **InternVL2 8B** | Very Good | Good | Limited | 18GB |

### API

| Model | QA Quality | Reasoning | Cost |
|-------|------------|-----------|------|
| **GPT-4o** | Excellent | Excellent | ~$0.02 |
| **Claude 3.5 Sonnet** | Excellent | Excellent | ~$0.02 |
| **Gemini 1.5 Pro** | Excellent | Very Good | ~$0.01 |

### When to Use Each

| Scenario | Recommendation |
|----------|----------------|
| Complex reasoning | GPT-4o, Claude 3.5, or Qwen2-VL 72B |
| Simple counting/color | Local 7B model |
| Need coordinates | Qwen2-VL |
| High volume | Local model |

---

## Implementation Examples

### Basic Visual QA

```python
from openai import OpenAI
import base64

client = OpenAI()

def visual_qa(image_path: str, question: str) -> str:
    """Answer a question about an image."""

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": question},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{image_data}"
                }}
            ]
        }]
    )

    return response.choices[0].message.content
```

### Structured QA

```python
import json

def structured_visual_qa(image_path: str, questions: list) -> dict:
    """Answer multiple questions with structured output."""

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    questions_formatted = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])

    prompt = f"""Answer these questions about the image.

{questions_formatted}

Return as JSON:
{{
  "answers": [
    {{"question": "...", "answer": "...", "confidence": "high|medium|low"}}
  ]
}}"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{image_data}"
                }}
            ]
        }],
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)
```

### Grounding with Qwen2-VL

```python
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
import torch

model = Qwen2VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2-VL-7B-Instruct",
    torch_dtype=torch.float16,
    device_map="auto"
)
processor = AutoProcessor.from_pretrained("Qwen/Qwen2-VL-7B-Instruct")

def find_object(image, object_description: str) -> dict:
    """Find object and return bounding box."""

    prompt = f"""Find the {object_description} in this image.
    Return the bounding box as [x1, y1, x2, y2] normalized coordinates."""

    messages = [
        {"role": "user", "content": [
            {"type": "image", "image": image},
            {"type": "text", "text": prompt}
        ]}
    ]

    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(text=[text], images=[image], return_tensors="pt").to("cuda")

    output = model.generate(**inputs, max_new_tokens=100)
    result = processor.decode(output[0], skip_special_tokens=True)

    return parse_bbox(result)
```

---

## Evaluation Metrics

### Accuracy Types

| Metric | Description | Use For |
|--------|-------------|---------|
| **Exact match** | Answer exactly matches | Yes/No, multiple choice |
| **Contains match** | Answer contains target | Short answers |
| **Semantic match** | Meaning is equivalent | Open-ended |
| **IoU (grounding)** | Bounding box overlap | Coordinate answers |

### Benchmark Datasets

| Dataset | Task | Size |
|---------|------|------|
| VQA v2 | General VQA | 1.1M questions |
| OK-VQA | External knowledge | 14K questions |
| TextVQA | Reading text | 45K questions |
| GQA | Compositional | 22M questions |

---

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Wrong count | Objects occluded/small | Ask for estimate + confidence |
| Hallucinated objects | Model invention | "Only what's visible" |
| Vague answers | Open-ended question | Constrain answer format |
| Spatial confusion | Complex scene | Break into sub-questions |
| Reading errors | Small/stylized text | Higher resolution input |

---

## Checklist

- [ ] Question type identified
- [ ] Answer format specified
- [ ] Uncertainty handling defined
- [ ] Hallucination prevention included
- [ ] Multi-turn support if needed
- [ ] Grounding requirements checked
- [ ] Evaluation metrics selected
- [ ] Edge cases tested

---

## Further Reading

| Resource | Type | URL |
|----------|------|-----|
| VQA Challenge | Benchmark | https://visualqa.org/ |
| Qwen2-VL Grounding | Demo | https://huggingface.co/spaces/Qwen/Qwen2-VL |
| OK-VQA Dataset | Dataset | https://okvqa.allenai.org/ |
| GQA Dataset | Dataset | https://cs.stanford.edu/people/dorarad/gqa/ |
