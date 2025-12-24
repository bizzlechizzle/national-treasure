# Document AI

Extract structured data from documents, screenshots, and diagrams.

---

## What is Document AI?

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Document   │────▶│    VLM      │────▶│  Structured │
│  (Image/PDF)│     │  Processing │     │    Data     │
└─────────────┘     └─────────────┘     └─────────────┘
```

**VLM = OCR + Layout Understanding + Reasoning**

---

## When to Use Document AI

### Use VLM When

- Need structured extraction (JSON)
- Document has complex layout
- Need to understand relationships
- Tables, forms, multi-column

### Use Pure OCR When

- Just need raw text
- Simple single-column documents
- Speed is critical
- Cost sensitivity at scale

---

## Document Types

| Type | Difficulty | Best Approach |
|------|------------|---------------|
| **Invoices** | Medium | VLM with schema |
| **Receipts** | Medium | VLM with schema |
| **Forms** | Medium-Hard | VLM + validation |
| **Tables** | Medium | VLM or table-specific |
| **Contracts** | Hard | VLM + chunking |
| **Screenshots** | Easy | VLM |
| **Charts** | Medium | VLM |
| **Diagrams** | Hard | VLM with reasoning |
| **Handwritten** | Hard | VLM (quality varies) |

---

## Extraction Patterns

### Invoice Extraction

```python
prompt = """Extract invoice data from this image.

Return JSON only:
{
  "invoice_number": "string or null",
  "date": "YYYY-MM-DD or null",
  "due_date": "YYYY-MM-DD or null",
  "vendor": {
    "name": "string",
    "address": "string or null"
  },
  "customer": {
    "name": "string",
    "address": "string or null"
  },
  "line_items": [
    {
      "description": "string",
      "quantity": number,
      "unit_price": number,
      "total": number
    }
  ],
  "subtotal": number,
  "tax": number or null,
  "total": number
}

Rules:
- Extract only what's visible
- Use null for missing fields
- Prices as numbers without currency symbols"""
```

### Receipt Extraction

```python
prompt = """Extract receipt data from this image.

Return JSON:
{
  "store_name": "string",
  "date": "YYYY-MM-DD",
  "time": "HH:MM or null",
  "items": [
    {"name": "string", "price": number}
  ],
  "subtotal": number or null,
  "tax": number or null,
  "total": number,
  "payment_method": "string or null"
}"""
```

### Form Extraction

```python
prompt = """Extract form fields from this image.

Return JSON with field names as keys and values as entered.
For checkboxes, use true/false.
For empty fields, use null.

Example structure:
{
  "field_name": "value or null",
  "checkbox_field": true/false
}"""
```

### Table Extraction

```python
prompt = """Extract the table from this image.

Return as JSON array of objects, where each object is a row
and keys are column headers.

[
  {"Column1": "value", "Column2": "value"},
  {"Column1": "value", "Column2": "value"}
]

If headers aren't clear, use "col1", "col2", etc."""
```

---

## Chart Understanding

### Read Chart Data

```python
prompt = """Analyze this chart and extract:

1. Chart type (bar, line, pie, etc.)
2. Title and axis labels
3. Data points or values
4. Key insights

Return JSON:
{
  "chart_type": "string",
  "title": "string or null",
  "x_axis": "string or null",
  "y_axis": "string or null",
  "data": [
    {"label": "string", "value": number}
  ],
  "insights": ["string", "string"]
}"""
```

### Interpret Chart

```python
prompt = """Look at this chart and answer:

1. What is the main trend?
2. What's the highest/lowest value?
3. Are there any anomalies?
4. What conclusion can be drawn?

Be specific with numbers when visible."""
```

---

## Screenshot Processing

### UI Extraction

```python
prompt = """Extract information from this screenshot.

Describe:
1. What application/website is shown
2. Key UI elements visible
3. Any data displayed
4. Any error messages or notifications

If there's a form or table, extract the data."""
```

### Error Screenshot

```python
prompt = """Analyze this error screenshot.

Extract:
{
  "error_type": "string (e.g., 404, exception, validation)",
  "error_message": "full error text",
  "application": "identified app/site if visible",
  "possible_cause": "your assessment",
  "suggested_action": "recommendation"
}"""
```

---

## Multi-Page Documents

### Approach

```python
def process_multipage(pages: list, schema: dict):
    """Process multi-page document."""

    # Option 1: Process each page, merge results
    all_data = []
    for page in pages:
        data = extract_page(page, schema)
        all_data.append(data)
    return merge_results(all_data)

    # Option 2: Process key pages only
    # First and last for headers/totals
    first = extract_page(pages[0], schema)
    last = extract_page(pages[-1], schema)
    return combine(first, last)
```

### Prompt for Continuation

```python
prompt = """This is page 2 of a multi-page document.

Previous context:
{previous_page_summary}

Extract data from this page, continuing from previous.
Note any references to previous/next pages."""
```

---

## Preprocessing

### Image Preparation

```python
from PIL import Image
import io

def prepare_document(image_path, max_size=2048, enhance=True):
    """Prepare document image for VLM."""
    img = Image.open(image_path)

    # Convert to RGB
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Resize if too large
    if max(img.size) > max_size:
        ratio = max_size / max(img.size)
        new_size = tuple(int(d * ratio) for d in img.size)
        img = img.resize(new_size, Image.LANCZOS)

    # Optional: Enhance contrast for documents
    if enhance:
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)

    return img
```

### PDF Handling

```python
import fitz  # PyMuPDF

def pdf_to_images(pdf_path, dpi=200):
    """Convert PDF pages to images."""
    doc = fitz.open(pdf_path)
    images = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        mat = fitz.Matrix(dpi/72, dpi/72)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)

    return images
```

---

## Validation

### Schema Validation

```python
from pydantic import BaseModel, validator
from typing import List, Optional

class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    total: float

    @validator('total')
    def validate_total(cls, v, values):
        expected = values.get('quantity', 0) * values.get('unit_price', 0)
        if abs(v - expected) > 0.01:
            # Log discrepancy but don't fail
            pass
        return v

class Invoice(BaseModel):
    invoice_number: Optional[str]
    date: Optional[str]
    vendor: str
    line_items: List[LineItem]
    total: float

    @validator('total')
    def validate_invoice_total(cls, v, values):
        items_total = sum(item.total for item in values.get('line_items', []))
        if abs(v - items_total) > 1:  # Allow for tax/fees
            pass
        return v
```

### Cross-Validation

```python
def validate_extraction(extracted: dict, image) -> dict:
    """Cross-validate extracted data."""
    issues = []

    # Check math
    if 'line_items' in extracted and 'total' in extracted:
        items_sum = sum(item['total'] for item in extracted['line_items'])
        if abs(items_sum - extracted['total']) > 1:
            issues.append(f"Total mismatch: items={items_sum}, stated={extracted['total']}")

    # Re-check with focused prompt if issues
    if issues:
        verification_prompt = f"""
        I extracted this data but found issues: {issues}

        Please re-check the image and correct any errors.
        Current extraction: {extracted}
        """
        # Re-run extraction

    return extracted
```

---

## Model Selection for Documents

### Local (3090)

| Model | OCR Quality | Tables | Forms | Speed |
|-------|-------------|--------|-------|-------|
| **Qwen2-VL 7B** | Excellent | Excellent | Good | Fast |
| **DocOwl 1.5** | Excellent | Very Good | Good | Fast |
| **LLaVA 7B** | Good | Good | Good | Fast |
| **Nougat** | Good (PDF) | — | — | Fast |

### API

| Model | OCR Quality | Tables | Forms | Cost |
|-------|-------------|--------|-------|------|
| **GPT-4o** | Excellent | Excellent | Excellent | $$$ |
| **Claude 3.5** | Excellent | Excellent | Excellent | $$$ |
| **Gemini Pro** | Excellent | Excellent | Very Good | $$ |
| **GPT-4o-mini** | Good | Good | Good | $ |

---

## Batch Processing

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def process_documents(paths: list, schema: dict, concurrency=5):
    """Process multiple documents in parallel."""
    semaphore = asyncio.Semaphore(concurrency)

    async def process_one(path):
        async with semaphore:
            image = prepare_document(path)
            result = await extract_async(image, schema)
            return {"path": path, "data": result}

    results = await asyncio.gather(*[process_one(p) for p in paths])
    return results
```

---

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Missing text | Low resolution | Increase DPI/size |
| Wrong numbers | OCR confusion | Validation + retry |
| Merged cells missed | Layout complexity | Specific table prompt |
| Handwriting errors | Difficult handwriting | Lower expectations, manual review |
| Wrong structure | Ambiguous layout | More specific schema |
| Hallucinated data | Model error | "Only extract visible" |

---

## Checklist

- [ ] Document type identified
- [ ] Schema defined
- [ ] Image preprocessing applied
- [ ] Resolution appropriate
- [ ] Validation logic added
- [ ] Error handling for failures
- [ ] Tested on diverse samples
- [ ] Manual review process for critical data

---

## Full Example

```python
from openai import OpenAI
import base64
import json
from PIL import Image
import io

client = OpenAI()

def extract_invoice(image_path: str) -> dict:
    """Extract invoice data from image."""

    # Prepare image
    img = Image.open(image_path)
    if max(img.size) > 2048:
        ratio = 2048 / max(img.size)
        img = img.resize((int(img.width * ratio), int(img.height * ratio)))

    # Encode
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=90)
    image_data = base64.b64encode(buffer.getvalue()).decode()

    # Extract
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": """Extract invoice data as JSON:
{
  "invoice_number": "string or null",
  "date": "YYYY-MM-DD or null",
  "vendor": "string",
  "total": number,
  "line_items": [{"description": "string", "amount": number}]
}
Only extract visible data. Use null for missing."""},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{image_data}",
                    "detail": "high"
                }}
            ]
        }],
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)

# Use
invoice = extract_invoice("invoice.jpg")
print(json.dumps(invoice, indent=2))
```

---

## Further Reading

| Resource | Type | URL |
|----------|------|-----|
| Qwen2-VL Demo | Interactive | https://huggingface.co/spaces/Qwen/Qwen2-VL |
| DocOwl | Paper | https://arxiv.org/abs/2307.02499 |
| Document AI (Google) | Service | https://cloud.google.com/document-ai |
| Textract (AWS) | Service | https://aws.amazon.com/textract/ |
