# National Treasure

**Ultimate browser automation with ML-powered learning.**

National Treasure is a production-grade web archiving and scraping toolkit that learns from its successes and failures. It uses Thompson Sampling (Multi-Armed Bandit) to adaptively select optimal browser configurations per domain, Playwright for bot-detection-resistant automation, and a SQLite-backed job queue for reliable background processing.

## Features

- **Adaptive Learning**: Thompson Sampling learns optimal browser configurations per domain
- **Bot Detection Bypass**: Stealth mode with anti-fingerprinting techniques
- **Response Validation (OPT-122)**: Detects CloudFront, Cloudflare, CAPTCHA, and other blocks
- **7 Browsertrix-Level Behaviors**: Scroll, expand, dismiss overlays, and more
- **Multi-Format Capture**: Screenshot, PDF, HTML, WARC
- **Selector Training**: Learn and track CSS selector success rates
- **Job Queue**: Priority-based queue with retry and dead letter support
- **SQLite Backend**: Fully offline-capable, portable database

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/national-treasure.git
cd national-treasure

# Install with pip
pip install -e .

# Install Playwright browsers
playwright install chromium
```

### Requirements

- Python 3.11+
- Playwright
- SQLite (included in Python)

## Quick Start

```bash
# Initialize database
nt db init

# Capture a URL
nt capture url https://example.com

# Capture with specific formats
nt capture url https://example.com --formats screenshot,pdf,html

# Capture in visible mode (for debugging)
nt capture url https://example.com --visible
```

## CLI Commands

### Capture Commands

```bash
# Capture single URL
nt capture url <URL> [OPTIONS]
  --formats, -f    Comma-separated: screenshot,pdf,html,warc (default: screenshot,html)
  --output, -o     Output directory
  --headless       Run headless (default: true)
  --visible        Run with visible browser
  --behaviors      Run page behaviors (default: true)
  --timeout, -t    Page load timeout in ms (default: 30000)

# Batch capture from file
nt capture batch <FILE> [OPTIONS]
  --formats, -f    Capture formats
  --output, -o     Output directory
  --concurrent, -c Number of concurrent captures (default: 3)
```

### Queue Commands

```bash
# Add URL to queue
nt queue add <URL> [OPTIONS]
  --priority, -p   Job priority (higher = first)

# Show queue status
nt queue status

# Start processing queue
nt queue run [OPTIONS]
  --workers, -w    Number of workers (default: 3)

# Show dead letter queue (failed jobs)
nt queue dead-letter [OPTIONS]
  --limit, -l      Max jobs to show (default: 10)
```

### Training Commands

```bash
# Show training statistics
nt training stats

# Export training data
nt training export <OUTPUT_FILE> [OPTIONS]
  --site, -s       Filter by site

# Import training data
nt training import <INPUT_FILE> [OPTIONS]
  --merge          Merge with existing (default)
  --replace        Replace existing data
```

### Learning Commands

```bash
# Get insights for a domain
nt learning insights <DOMAIN>

# Show global learning statistics
nt learning stats
```

### Database Commands

```bash
# Initialize database
nt db init [OPTIONS]
  --force, -f      Force recreate

# Show database info
nt db info
```

### Other Commands

```bash
# Show version
nt --version

# Show configuration
nt config
```

## Python API

### Basic Capture

```python
import asyncio
from national_treasure.services.capture.service import CaptureService

async def main():
    async with CaptureService(headless=True) as service:
        result = await service.capture(
            "https://example.com",
            formats=["screenshot", "html"],
        )
        print(f"Success: {result.success}")
        print(f"Screenshot: {result.screenshot_path}")

asyncio.run(main())
```

### With Learning

```python
from urllib.parse import urlparse
from national_treasure.services.capture.service import CaptureService
from national_treasure.services.learning.domain import DomainLearner

async def capture_with_learning(url: str):
    domain = urlparse(url).netloc
    learner = DomainLearner()

    # Get learned best config for this domain
    config = await learner.get_best_config(domain)

    async with CaptureService(config=config) as service:
        result = await service.capture(url)

        # Record outcome for future learning
        await learner.record_outcome(
            domain,
            config,
            result.success,
            {"response_code": result.validation.http_status if result.validation else None}
        )

    return result
```

### Job Queue

```python
from national_treasure.services.queue.service import JobQueue
from national_treasure.core.models import JobType, Job

async def main():
    queue = JobQueue()

    # Enqueue a job
    job_id = await queue.enqueue(
        JobType.CAPTURE,
        {"url": "https://example.com"},
        priority=5,
    )

    # Register handler
    async def handle_capture(job: Job):
        url = job.payload["url"]
        # ... process job
        return {"status": "completed"}

    queue.register_handler(JobType.CAPTURE, handle_capture)

    # Start processing
    await queue.start(num_workers=3)
```

### Selector Training

```python
from national_treasure.services.scraper.training import TrainingService

async def main():
    service = TrainingService()

    # Record selector outcome
    await service.record_selector_outcome(
        site="example.com",
        field="title",
        selector="h1.main-title",
        success=True,
        extracted_value="Example Title",
    )

    # Get best selector for a field
    pattern = await service.get_best_selector("example.com", "title")
    if pattern:
        print(f"Best selector: {pattern.selector} ({pattern.confidence:.0%})")
```

## Architecture

```
national-treasure/
├── src/national_treasure/
│   ├── cli/                    # Typer CLI
│   │   └── main.py
│   ├── core/
│   │   ├── config.py           # Configuration
│   │   ├── database.py         # SQLite schema
│   │   └── models.py           # Pydantic models
│   └── services/
│       ├── browser/
│       │   ├── service.py      # BrowserService
│       │   ├── validator.py    # Response validation
│       │   └── behaviors.py    # Page behaviors
│       ├── capture/
│       │   └── service.py      # Multi-format capture
│       ├── learning/
│       │   └── domain.py       # Thompson Sampling
│       ├── queue/
│       │   └── service.py      # Job queue
│       └── scraper/
│           ├── training.py     # Selector training
│           └── base.py         # Base scraper
└── tests/
    ├── unit/
    └── integration/
```

## Configuration

Configuration is loaded from environment variables or `.env` file:

```bash
# Database location
NT_DATABASE_PATH=~/.national-treasure/national_treasure.db

# Archive output directory
NT_ARCHIVE_DIR=~/.national-treasure/archive

# Log level
NT_LOG_LEVEL=INFO
```

## How Learning Works

National Treasure uses **Thompson Sampling** to learn optimal browser configurations per domain:

1. **Arms**: Different configurations (headless modes, wait strategies, user agents)
2. **Rewards**: Success/failure of requests
3. **Beta Distribution**: Tracks successes and failures per arm
4. **Exploration vs Exploitation**: Automatically balances trying new options with using what works

After each request, the outcome is recorded:
- Domain
- Configuration used
- Success/failure

Over time, the learner identifies which configurations work best for each domain.

## Bot Detection Bypass

National Treasure includes several anti-detection techniques:

1. **Shell Headless Mode**: Chrome 129+ undetectable headless
2. **Stealth Scripts**: Remove `navigator.webdriver`, mock plugins
3. **Realistic User Agent**: Chrome on macOS by default
4. **Disable Automation Flags**: `--disable-blink-features=AutomationControlled`

## Response Validation (OPT-122)

Automatic detection of:
- **CloudFront blocks**: "generated by cloudfront"
- **Cloudflare challenges**: "Just a moment...", "Checking your browser"
- **CAPTCHAs**: reCAPTCHA, hCaptcha, Turnstile
- **Rate limiting**: "Too many requests"
- **Login walls**: "Please sign in"

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=national_treasure

# Type checking
mypy src/national_treasure

# Linting
ruff check src/
```

## License

MIT License - see LICENSE file.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## Credits

Built on:
- [Playwright](https://playwright.dev/) - Browser automation
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Pydantic](https://pydantic.dev/) - Data validation
- [aiosqlite](https://github.com/omnilib/aiosqlite) - Async SQLite
