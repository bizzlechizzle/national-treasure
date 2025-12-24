# National Treasure Technical Guide

## Project Overview

National Treasure is a production-grade browser automation toolkit with adaptive machine learning. It learns optimal configurations per domain using Thompson Sampling and provides reliable web archiving with bot detection bypass.

## Commands

### Build & Install

```bash
# Install in development mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Install Playwright browsers
playwright install chromium
```

### Test

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=national_treasure --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_models.py

# Run with verbose output
pytest -v

# Run async tests only
pytest -m asyncio
```

### Lint & Type Check

```bash
# Ruff linting
ruff check src/

# Ruff formatting
ruff format src/

# Type checking
mypy src/national_treasure
```

### Run

```bash
# CLI entry point
nt --help

# Or via Python
python -m national_treasure.cli.main --help
```

## Gotchas & Troubleshooting

### Playwright Browser Not Installed

```
Error: Browser not installed
```

**Fix**: Run `playwright install chromium`

### Database Not Initialized

```
Error: Database not found
```

**Fix**: Run `nt db init`

### PDF Capture Fails in Headless=False

PDF capture only works in headless mode (Playwright limitation).

**Fix**: Use `--headless` for PDF capture.

### WARC Capture Size

Simplified WARC implementation captures HTML only. For full WARC with resources, use external tools like `wget --warc-file`.

### Rate Limiting

If you hit rate limits:
1. Reduce `--concurrent` in batch capture
2. Add delays between requests
3. Use different browser profiles

### Thompson Sampling Cold Start

New domains have no learning data, so configurations are chosen randomly at first. After 10-20 requests, the learner converges on optimal settings.

## Architecture Details

### Core Models

Located in `src/national_treasure/core/models.py`:

| Model | Purpose |
|-------|---------|
| `BrowserConfig` | Browser configuration with success tracking |
| `CaptureResult` | Result of page capture with paths and metadata |
| `ValidationResult` | Response validation result (blocked, reason) |
| `Job` | Background job with status and payload |
| `SelectorPattern` | CSS selector with confidence scoring |
| `UrlPattern` | URL transformation pattern |

### Services

| Service | Location | Purpose |
|---------|----------|---------|
| `BrowserService` | `services/browser/service.py` | Playwright browser lifecycle |
| `ResponseValidator` | `services/browser/validator.py` | Bot detection checks |
| `PageBehaviors` | `services/browser/behaviors.py` | 7 page interaction behaviors |
| `CaptureService` | `services/capture/service.py` | Multi-format page capture |
| `JobQueue` | `services/queue/service.py` | SQLite-backed job queue |
| `TrainingService` | `services/scraper/training.py` | Selector confidence tracking |
| `DomainLearner` | `services/learning/domain.py` | Thompson Sampling MAB |

### Database Schema

Tables defined in `src/national_treasure/core/database.py`:

| Table | Purpose |
|-------|---------|
| `browser_configs` | Stored browser configurations |
| `domain_configs` | Per-domain learned configurations |
| `request_outcomes` | Request history for learning |
| `domain_similarity` | Similar domain mappings |
| `jobs` | Active job queue |
| `job_dead_letter` | Failed jobs for retry |
| `selector_patterns` | CSS selector training data |
| `url_patterns` | URL transformation patterns |
| `web_sources` | Archived web source metadata |
| `web_source_images` | Image metadata from sources |

## Key Patterns

### Async Context Manager

```python
async with CaptureService() as service:
    result = await service.capture(url)
```

### Page Context Manager

```python
async with browser_service.page() as page:
    await page.goto(url)
```

### Thompson Sampling

```python
# Beta distribution sampling
alpha = successes + 1
beta = failures + 1
sample = random.betavariate(alpha, beta)
```

### Selector Fallback Chain

```python
for selector in fallback_selectors:
    element = await page.query_selector(selector)
    if element:
        value = await element.inner_text()
        # Record success
        break
```

## Testing Strategy

### Unit Tests

Test individual components in isolation with mocks:
- Models: Field validation, computed properties
- Services: Core logic without real browser/network
- Queue: Job lifecycle, state transitions

### Integration Tests

Test component interactions:
- Database initialization and queries
- Browser service with real pages
- End-to-end capture workflow

### Test Fixtures

Common fixtures in `tests/conftest.py`:
- `test_db`: Temporary SQLite database
- `temp_dir`: Temporary directory for output
- `sample_urls`: Test URLs
- `sample_selectors`: Test selectors

## Performance Considerations

### Concurrent Captures

Use `--concurrent` flag wisely:
- 1-3 for rate-limited sites
- 5-10 for tolerant sites
- Monitor memory with many tabs

### Database Size

SQLite scales well but:
- Vacuum periodically: `VACUUM;`
- Archive old request_outcomes
- Export/import training data

### Memory Management

Playwright holds pages in memory:
- Close pages promptly
- Use context managers
- Limit concurrent captures

## Extending

### Custom Scraper

```python
from national_treasure.services.scraper.base import BaseScraper

class MyScraper(BaseScraper):
    SITE_PATTERNS = [r"mysite\.com"]
    SELECTORS = {
        "title": ["h1", ".title"],
        "content": [".content", "article"],
    }

    async def extract(self, page, url):
        title = await self.extract_text(page, "title")
        content = await self.extract_text(page, "content")
        return {"title": title, "content": content}
```

### Custom Job Type

```python
from national_treasure.core.models import JobType

# Add to JobType enum in models.py
class JobType(str, Enum):
    CAPTURE = "capture"
    SCRAPE = "scrape"
    MY_CUSTOM = "my_custom"  # Add here

# Register handler
queue.register_handler(JobType.MY_CUSTOM, my_handler)
```

### Custom Validation Pattern

```python
validator = ResponseValidator(
    custom_block_patterns=["site maintenance", "access denied"],
    custom_success_patterns=["content loaded successfully"],
)
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2025-01 | Initial release |

## Dependencies

Core:
- `playwright>=1.40.0` - Browser automation
- `typer[all]>=0.9.0` - CLI framework
- `pydantic>=2.5.0` - Data validation
- `aiosqlite>=0.19.0` - Async SQLite
- `python-ulid>=2.2.0` - ULID generation

Dev:
- `pytest>=7.4.0` - Testing
- `pytest-asyncio>=0.21.0` - Async test support
- `pytest-cov>=4.1.0` - Coverage
- `ruff>=0.1.0` - Linting
- `mypy>=1.7.0` - Type checking
