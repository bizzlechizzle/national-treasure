# Classification & Extraction

Use LLMs for structured outputs: categories, entities, JSON.

---

## When to Use LLMs

### Use LLM If:

- Few or no training examples
- Categories/schema may change
- Need to handle diverse inputs
- Extraction is context-dependent

### Use Traditional ML If:

- Have 1000+ labeled examples
- Categories are fixed
- Need high throughput (millions/day)
- Cost sensitivity at scale

---

## Classification

### Zero-Shot Classification

```python
prompt = """Classify this support ticket into exactly one category.

Categories:
- Technical: Software bugs, errors, performance issues
- Billing: Payments, invoices, subscriptions
- Account: Login, profile, permissions
- Feature: Requests for new functionality
- Other: Anything else

Ticket: "I can't log in to my account. It says my password is wrong but I just reset it."

Category:"""

# Response: "Account"
```

### Few-Shot Classification

```python
prompt = """Classify the sentiment of product reviews.

Review: "This is the best purchase I've ever made!"
Sentiment: Positive

Review: "Arrived broken and customer service was unhelpful."
Sentiment: Negative

Review: "It works as expected, nothing special."
Sentiment: Neutral

Review: "I've been using this for 3 months and it still works great!"
Sentiment:"""

# Response: "Positive"
```

### Multi-Label Classification

```python
prompt = """Assign all applicable tags to this article.
Return tags as a JSON array.

Available tags:
- Technology
- Business
- Health
- Science
- Politics
- Entertainment
- Sports

Article: "Apple announced new AI health features for Apple Watch that can detect early signs of diabetes using machine learning algorithms."

Tags (JSON array):"""

# Response: ["Technology", "Health", "Business"]
```

### Confidence Scores

```python
prompt = """Classify this email and provide confidence.

Categories: Spam, Marketing, Personal, Work

Email: "Meeting tomorrow at 3pm to discuss Q4 projections."

Respond in JSON:
{
  "category": "string",
  "confidence": "high|medium|low",
  "reasoning": "brief explanation"
}"""
```

---

## Entity Extraction

### Named Entity Recognition

```python
prompt = """Extract all named entities from this text.

Text: "John Smith, CEO of Acme Corp, announced the merger with TechStart Inc. at their New York headquarters on March 15, 2024."

Return JSON:
{
  "people": ["name", ...],
  "organizations": ["org", ...],
  "locations": ["location", ...],
  "dates": ["date", ...]
}"""
```

### Custom Entity Extraction

```python
prompt = """Extract product information from this description.

Description: "iPhone 15 Pro Max, 256GB, Natural Titanium, unlocked. Asking $1,100. Minor scratch on back, battery health at 95%. Located in Brooklyn, can ship."

Extract:
{
  "product_name": "string",
  "storage": "string or null",
  "color": "string or null",
  "price": number,
  "condition": "new|like_new|good|fair|poor",
  "location": "string or null"
}"""
```

### Structured Output (OpenAI)

```python
from openai import OpenAI
from pydantic import BaseModel

class ProductInfo(BaseModel):
    product_name: str
    price: float
    condition: str
    storage: str | None = None
    color: str | None = None

client = OpenAI()

response = client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "Extract product information."},
        {"role": "user", "content": description}
    ],
    response_format=ProductInfo
)

product = response.choices[0].message.parsed
```

---

## JSON Mode

### OpenAI JSON Mode

```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
    response_format={"type": "json_object"},
    messages=[
        {"role": "system", "content": "Respond only in JSON."},
        {"role": "user", "content": "Extract: John is 25, works at Google."}
    ]
)

data = json.loads(response.choices[0].message.content)
```

### Anthropic JSON Mode

```python
from anthropic import Anthropic

client = Anthropic()

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{
        "role": "user",
        "content": """Extract person info as JSON only, no other text.

Text: John Smith, 32, software engineer at Acme Corp.

JSON:"""
    }]
)

# Parse the response
data = json.loads(response.content[0].text)
```

### Local Models

```python
# Use grammar/schema with llama.cpp or Outlines
from outlines import models, generate

model = models.transformers("meta-llama/Llama-3.1-8B-Instruct")

schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"}
    },
    "required": ["name", "age"]
}

generator = generate.json(model, schema)
result = generator(prompt)
```

---

## Document Processing

### Invoice Extraction

```python
prompt = """Extract invoice details from this text.

Invoice Text:
'''
INVOICE #12345
Date: 2024-01-15

Bill To:
Acme Corporation
123 Main St, NYC

Items:
- Widget Pro x10 @ $50.00 = $500.00
- Service Fee = $75.00

Subtotal: $575.00
Tax (8%): $46.00
Total: $621.00

Payment Due: 2024-02-15
'''

Extract as JSON:
{
  "invoice_number": "string",
  "date": "YYYY-MM-DD",
  "vendor": "string",
  "customer": "string",
  "line_items": [{"description": "string", "quantity": number, "unit_price": number, "total": number}],
  "subtotal": number,
  "tax": number,
  "total": number,
  "due_date": "YYYY-MM-DD"
}"""
```

### Resume Parsing

```python
prompt = """Parse this resume into structured data.

Resume:
'''
Jane Doe
jane.doe@email.com | (555) 123-4567 | linkedin.com/in/janedoe

EXPERIENCE

Senior Software Engineer | Google | 2020-Present
- Led team of 5 engineers on search ranking improvements
- Increased query performance by 40%

Software Engineer | Facebook | 2017-2020
- Built recommendation system for Marketplace

EDUCATION

BS Computer Science | MIT | 2017
'''

Extract:
{
  "name": "string",
  "email": "string",
  "phone": "string",
  "experience": [{
    "title": "string",
    "company": "string",
    "start_year": number,
    "end_year": number or null,
    "highlights": ["string"]
  }],
  "education": [{
    "degree": "string",
    "institution": "string",
    "year": number
  }]
}"""
```

---

## Batch Processing

### Efficient Batch Extraction

```python
import asyncio
from openai import AsyncOpenAI

client = AsyncOpenAI()

async def extract_one(text):
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Extract entities as JSON."},
            {"role": "user", "content": text}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

async def extract_batch(texts, concurrency=10):
    semaphore = asyncio.Semaphore(concurrency)

    async def limited_extract(text):
        async with semaphore:
            return await extract_one(text)

    return await asyncio.gather(*[limited_extract(t) for t in texts])

# Use
results = asyncio.run(extract_batch(documents))
```

### Cost Optimization

```python
# Batch multiple items in one call
prompt = """Extract entities from each text below.
Return a JSON array with one object per text.

Texts:
1. "John Smith works at Google in NYC."
2. "Apple announced new products yesterday."
3. "The FDA approved a new drug from Pfizer."

JSON array:"""

# One API call instead of three
```

---

## Validation

### Schema Validation

```python
from pydantic import BaseModel, validator
from typing import List, Optional

class ExtractedPerson(BaseModel):
    name: str
    age: Optional[int] = None
    company: Optional[str] = None

    @validator('age')
    def age_must_be_positive(cls, v):
        if v is not None and v < 0:
            raise ValueError('Age must be positive')
        return v

def extract_with_validation(text):
    response = llm.generate(extraction_prompt + text)

    try:
        data = json.loads(response)
        return ExtractedPerson(**data)
    except (json.JSONDecodeError, ValueError) as e:
        # Retry or handle error
        return None
```

### Retry on Failure

```python
def extract_with_retry(text, max_retries=3):
    for attempt in range(max_retries):
        response = llm.generate(prompt + text)

        try:
            data = json.loads(response)
            validated = Schema(**data)
            return validated
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            # Add error feedback for retry
            prompt += f"\n\nPrevious error: {e}. Please fix."
```

---

## Local Models (3090)

### Recommended

| Model | VRAM | JSON Ability | Speed |
|-------|------|--------------|-------|
| Llama 3.1 8B | 5GB | Good | Fast |
| Qwen 2.5 14B | 8GB | Excellent | Medium |
| Mistral 7B | 4GB | Good | Fast |

### With Outlines (Guaranteed JSON)

```python
from outlines import models, generate

model = models.llamacpp("path/to/model.gguf")

schema = {
    "type": "object",
    "properties": {
        "category": {"enum": ["Technical", "Billing", "Account"]},
        "urgency": {"enum": ["low", "medium", "high"]}
    }
}

generator = generate.json(model, schema)
result = generator(f"Classify this ticket: {ticket_text}")
# Guaranteed valid JSON matching schema
```

---

## Evaluation

### Metrics

| Task | Metric |
|------|--------|
| Classification | Accuracy, F1, Precision, Recall |
| Extraction | Exact match, Token-level F1 |
| JSON validity | % valid JSON responses |

### Testing

```python
test_cases = [
    {
        "input": "I can't log in",
        "expected_category": "Account"
    },
    {
        "input": "When is my invoice due?",
        "expected_category": "Billing"
    }
]

correct = 0
for case in test_cases:
    result = classify(case["input"])
    if result == case["expected_category"]:
        correct += 1

accuracy = correct / len(test_cases)
```

---

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Invalid JSON | Model doesn't follow format | Use structured output API |
| Wrong categories | Ambiguous definitions | Better category descriptions |
| Missing fields | Optional confusion | Specify "null if not found" |
| Hallucinated values | Over-extraction | "Only extract if explicitly stated" |
| Inconsistent format | No examples | Add few-shot examples |

---

## Checklist

- [ ] Schema defined clearly
- [ ] Few-shot examples added (if needed)
- [ ] JSON validation implemented
- [ ] Error handling for invalid responses
- [ ] Retry logic for failures
- [ ] Batch processing for volume
- [ ] Evaluation on test set
- [ ] Cost estimated for volume

---

## Further Reading

| Resource | Type | URL |
|----------|------|-----|
| OpenAI Structured Outputs | Docs | https://platform.openai.com/docs/guides/structured-outputs |
| Outlines | Library | https://github.com/outlines-dev/outlines |
| Instructor | Library | https://github.com/jxnl/instructor |
| Pydantic | Library | https://docs.pydantic.dev/ |
