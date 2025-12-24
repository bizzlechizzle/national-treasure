# Multimodal Prompting

Effectively combine images and text for VLM inputs.

---

## Core Principles

```
┌──────────────────────────────────────────────────────────────┐
│                    MULTIMODAL PROMPT                         │
├──────────────────────────────────────────────────────────────┤
│  ┌─────────┐   ┌─────────────────────────────────────────┐  │
│  │  IMAGE  │ + │              TEXT PROMPT                │  │
│  │         │   │  - Context                              │  │
│  │         │   │  - Instructions                         │  │
│  │         │   │  - Output format                        │  │
│  └─────────┘   └─────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

**Key insight**: Text tells the model HOW to look at the image.

---

## Prompt Structure

### Basic Structure

```
[Context] — What is this image? Why are we analyzing it?
[Task] — What should the model do?
[Constraints] — Limitations, format, length
[Output format] — How to structure the response
```

### Example

```python
prompt = """You are analyzing product images for an e-commerce catalog.

Look at this product image and:
1. Identify the product type
2. List key visible features
3. Describe colors and materials
4. Note any brand markings

Respond in JSON format:
{
  "product_type": "string",
  "features": ["list"],
  "colors": ["list"],
  "materials": ["list"],
  "brand": "string or null"
}"""
```

---

## Image Positioning

### Text Before Image

```python
# OpenAI format
messages = [{
    "role": "user",
    "content": [
        {"type": "text", "text": "Describe this image:"},
        {"type": "image_url", "image_url": {"url": "..."}}
    ]
}]
```

**Use when**: Prompt sets context before seeing image.

### Image Before Text

```python
# Some tasks work better with image first
messages = [{
    "role": "user",
    "content": [
        {"type": "image_url", "image_url": {"url": "..."}},
        {"type": "text", "text": "What is shown in the image above?"}
    ]
}]
```

**Use when**: Image is the primary focus, text is simple question.

### Interleaved

```python
# For comparison or multi-step analysis
messages = [{
    "role": "user",
    "content": [
        {"type": "text", "text": "Compare these two images:"},
        {"type": "text", "text": "Image 1:"},
        {"type": "image_url", "image_url": {"url": "..."}},
        {"type": "text", "text": "Image 2:"},
        {"type": "image_url", "image_url": {"url": "..."}},
        {"type": "text", "text": "What are the differences?"}
    ]
}]
```

---

## Specificity Levels

### Vague (Avoid)

```python
# Too vague
prompt = "Look at this image."
```

### General

```python
# Acceptable for exploration
prompt = "Describe what you see in this image."
```

### Specific (Preferred)

```python
# Clear task with output format
prompt = """Analyze this product image.

List:
1. Product category
2. Color(s)
3. Visible text/labels
4. Estimated condition (new/used)

Keep descriptions under 20 words each."""
```

### Highly Specific (For Production)

```python
prompt = """Extract product information from this e-commerce image.

Requirements:
- Identify the main product (ignore backgrounds, watermarks)
- Extract exact text from any labels
- Note the dominant and accent colors
- Assess image quality (excellent/good/poor)

Return as JSON:
{
  "product_name": "string (your best guess)",
  "category": "one of: electronics, clothing, home, other",
  "colors": {
    "dominant": "string",
    "accent": ["list"] or null
  },
  "text_visible": ["list of text strings"] or null,
  "image_quality": "excellent|good|poor",
  "confidence": "high|medium|low"
}

Only extract what is clearly visible. Use null for uncertain fields."""
```

---

## Output Format Control

### Free Text

```python
prompt = "Describe this image in 2-3 sentences."
```

### Structured Text

```python
prompt = """Describe this image using this format:

**Subject**: [main subject]
**Setting**: [location/environment]
**Action**: [what's happening]
**Mood**: [overall feeling]"""
```

### JSON (Recommended for Processing)

```python
prompt = """Analyze this image and return JSON only.

{
  "objects": ["list", "of", "objects"],
  "scene_type": "indoor|outdoor|abstract",
  "people_count": number,
  "description": "one sentence summary"
}

Return ONLY valid JSON, no other text."""
```

### Markdown

```python
prompt = """Analyze this diagram and explain it in markdown format.

Use:
- Headers for sections
- Bullet points for lists
- Code blocks for any code/technical content
- Bold for emphasis"""
```

---

## Task-Specific Patterns

### Classification

```python
prompt = """Classify this image into one of these categories:
- product_photo
- lifestyle_image
- infographic
- screenshot
- other

Answer with just the category name."""
```

### Comparison

```python
prompt = """Compare the two images shown.

For each of these aspects, note which image is better (1, 2, or tie):
1. Image quality
2. Composition
3. Lighting
4. Subject visibility

Then provide overall recommendation."""
```

### Extraction

```python
prompt = """Extract all text visible in this image.

Return as a JSON array of strings.
Include text from labels, signs, documents, screens.
Preserve original formatting where possible.
If no text is visible, return []."""
```

### Verification

```python
prompt = """Verify this claim about the image:
Claim: "{claim}"

Check the image and respond:
- VERIFIED: If the claim is true
- REFUTED: If the claim is false
- UNVERIFIABLE: If the image doesn't contain enough information

Then explain your reasoning in one sentence."""
```

### Generation from Image

```python
prompt = """Based on this product image, write:

1. A product title (max 80 characters)
2. A short description (2-3 sentences)
3. 5 relevant keywords

Format as:
Title: [title]
Description: [description]
Keywords: [comma-separated keywords]"""
```

---

## Multi-Image Patterns

### Sequential Analysis

```python
prompt = """These images show a process in order.

For each image:
1. Describe what step is shown
2. Note any tools/materials visible
3. Describe the action being performed

Then summarize the overall process."""
```

### Find Differences

```python
prompt = """Compare these two images carefully.

List every difference you can find:
1. Objects present in one but not the other
2. Position changes
3. Color differences
4. Text changes

Be thorough and specific."""
```

### Best Selection

```python
prompt = """I'm showing you {n} images of the same subject.

Select the best one for use as a product photo.

Consider:
- Image clarity
- Lighting
- Subject prominence
- Background cleanliness

Respond with:
Best: [image number 1-{n}]
Reason: [brief explanation]"""
```

---

## Handling Edge Cases

### Unclear Images

```python
prompt = """Analyze this image to the best of your ability.

If any aspect is unclear or uncertain:
- State what you can determine
- Note what's unclear and why
- Provide your best guess with "possibly" or "appears to be"

Do not invent details that aren't visible."""
```

### Potentially Sensitive Content

```python
prompt = """Analyze this image professionally.

Guidelines:
- Describe content objectively
- Flag any potentially sensitive elements
- If content appears inappropriate, note this and limit description
- Maintain professional, neutral tone"""
```

### Low Quality Images

```python
prompt = """This image may be low quality (blurry, dark, etc.).

Describe what you can discern:
- Main subject (if identifiable)
- General scene type
- Any readable text

Rate image quality: poor/acceptable/good
Note any specific quality issues."""
```

---

## Provider-Specific Syntax

### OpenAI (GPT-4o)

```python
from openai import OpenAI
client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Your prompt here"},
            {"type": "image_url", "image_url": {
                "url": f"data:image/jpeg;base64,{base64_data}",
                "detail": "high"  # or "low", "auto"
            }}
        ]
    }],
    max_tokens=1000
)
```

### Anthropic (Claude)

```python
from anthropic import Anthropic
client = Anthropic()

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {"type": "image", "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": base64_data
            }},
            {"type": "text", "text": "Your prompt here"}
        ]
    }]
)
```

### Google (Gemini)

```python
import google.generativeai as genai
from PIL import Image

genai.configure(api_key="...")
model = genai.GenerativeModel('gemini-1.5-flash')

image = Image.open("image.jpg")
response = model.generate_content([
    "Your prompt here",
    image
])
```

### Ollama (Local)

```python
import ollama
import base64

with open("image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

response = ollama.chat(
    model='llava:7b',
    messages=[{
        'role': 'user',
        'content': 'Your prompt here',
        'images': [image_data]
    }]
)
```

---

## System Prompts for VLMs

### General Assistant

```python
system = """You are a visual analysis assistant.
You analyze images accurately and thoroughly.
You only describe what you can see, never invent details.
When uncertain, you say so."""
```

### Domain Expert

```python
system = """You are an expert product photographer assistant.
You analyze images with attention to:
- Composition and framing
- Lighting quality
- Color accuracy
- Commercial viability
You provide professional feedback."""
```

### Data Extractor

```python
system = """You are a precise data extraction system.
You extract structured information from images.
You return only valid JSON.
You use null for fields that cannot be determined.
You never hallucinate data."""
```

---

## Prompt Templates

### Reusable Template Pattern

```python
class VLMPromptTemplate:
    def __init__(self, task: str, output_format: str, constraints: list = None):
        self.task = task
        self.output_format = output_format
        self.constraints = constraints or []

    def build(self, **kwargs) -> str:
        prompt = f"{self.task.format(**kwargs)}\n"

        if self.constraints:
            prompt += "\nConstraints:\n"
            for c in self.constraints:
                prompt += f"- {c}\n"

        prompt += f"\nOutput format:\n{self.output_format}"
        return prompt

# Usage
product_template = VLMPromptTemplate(
    task="Analyze this {product_type} product image.",
    output_format='{"name": "string", "features": ["list"]}',
    constraints=["Only visible features", "Use null for unknowns"]
)

prompt = product_template.build(product_type="electronics")
```

---

## Best Practices Checklist

- [ ] Task is clearly stated
- [ ] Output format is specified
- [ ] Edge cases are handled
- [ ] Hallucination prevention included ("only what's visible")
- [ ] Length/detail level specified
- [ ] Appropriate specificity for use case
- [ ] Tested with diverse images
- [ ] Consistent output format

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Vague prompts | Be specific about task and format |
| No output format | Specify JSON, text, or structured |
| No length guidance | Add word/sentence limits |
| Assumes image content | Add "if visible" or "if applicable" |
| Ignores edge cases | Add uncertainty handling |
| Overly complex prompt | Break into steps or simplify |

---

## Further Reading

| Resource | Type | URL |
|----------|------|-----|
| OpenAI Vision Guide | Docs | https://platform.openai.com/docs/guides/vision |
| Claude Vision | Docs | https://docs.anthropic.com/en/docs/build-with-claude/vision |
| Gemini Vision | Docs | https://ai.google.dev/gemini-api/docs/vision |
| Prompt Engineering Guide | Guide | https://www.promptingguide.ai/techniques/multimodal |
