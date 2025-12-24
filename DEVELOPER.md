# National Treasure Developer Guide

> For developers who want to understand, modify, or extend the codebase.

---

## Quick Start (5 Minutes)

```bash
# 1. Clone and setup
git clone https://github.com/bizzlechizzle/national-treasure.git
cd national-treasure

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install with dev dependencies
pip install -e ".[dev]"

# 4. Install Playwright browser
playwright install chromium

# 5. Initialize database
nt db init

# 6. Verify installation
nt --version  # Should print: national-treasure v0.1.0
pytest tests/unit/ -v  # Should pass 78 tests
```

---

## Project Structure

```
national-treasure/
├── src/national_treasure/
│   ├── __init__.py           # Version from VERSION file
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py           # Typer CLI (all commands)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py         # Pydantic settings
│   │   ├── database.py       # SQLite schema + helpers
│   │   └── models.py         # All Pydantic models
│   └── services/
│       ├── browser/
│       │   ├── service.py    # BrowserService (Playwright)
│       │   ├── validator.py  # ResponseValidator (OPT-122)
│       │   └── behaviors.py  # PageBehaviors (7 behaviors)
│       ├── capture/
│       │   └── service.py    # CaptureService (multi-format)
│       ├── learning/
│       │   └── domain.py     # DomainLearner (Thompson Sampling)
│       ├── queue/
│       │   └── service.py    # JobQueue (SQLite-backed)
│       └── scraper/
│           ├── base.py       # BaseScraper (abstract)
│           └── training.py   # TrainingService (selector confidence)
├── tests/
│   ├── conftest.py           # Pytest fixtures
│   └── unit/                 # Unit tests (78 tests)
├── pyproject.toml            # Project config + dependencies
├── VERSION                   # Version string (0.1.0)
├── README.md                 # User documentation
├── techguide.md              # Technical guide
├── AUDIT.md                  # Implementation audit
└── DEVELOPER.md              # This file
```

---

## Core Concepts

### 1. Async Context Managers

All services use async context managers for proper resource cleanup:

```python
# Browser service
async with BrowserService(headless=True) as browser:
    async with browser.page() as page:
        await page.goto("https://example.com")

# Capture service
async with CaptureService(headless=True) as service:
    result = await service.capture("https://example.com")
```

### 2. Pydantic Models

All data structures use Pydantic for validation:

```python
from national_treasure.core.models import BrowserConfig, CaptureResult

# Models validate on creation
config = BrowserConfig(
    headless_mode=HeadlessMode.SHELL,
    viewport_width=1920,
)

# Access computed properties
print(config.success_rate)  # Calculated from stats
```

### 3. Thompson Sampling

Domain learning uses Multi-Armed Bandit:

```python
from national_treasure.services.learning.domain import DomainLearner

learner = DomainLearner()

# Get best config (samples from Beta distribution)
config = await learner.get_best_config("example.com")

# Record outcome (updates Beta parameters)
await learner.record_outcome("example.com", config, success=True)
```

### 4. Job Queue

SQLite-backed queue with retry logic:

```python
from national_treasure.services.queue.service import JobQueue
from national_treasure.core.models import JobType

queue = JobQueue()

# Enqueue
job_id = await queue.enqueue(JobType.CAPTURE, {"url": "https://..."})

# Register handler
queue.register_handler(JobType.CAPTURE, my_handler)

# Start processing
await queue.start(num_workers=3)
```

---

## Adding New Features

### Adding a New CLI Command

1. Edit `src/national_treasure/cli/main.py`
2. Add command to appropriate sub-app:

```python
@capture_app.command("new-command")
def new_command(
    arg: str = typer.Argument(..., help="Required argument"),
    option: bool = typer.Option(False, "--flag", "-f", help="Optional flag"),
):
    """Description shown in --help."""
    # Implementation
    console.print(f"[green]Done![/green]")
```

### Adding a New Service

1. Create `src/national_treasure/services/myservice/__init__.py`
2. Create `src/national_treasure/services/myservice/service.py`:

```python
class MyService:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or str(get_config().database_path)

    async def do_something(self, param: str) -> Result:
        async with aiosqlite.connect(self.db_path) as db:
            # Implementation
            pass
```

3. Add tests in `tests/unit/test_myservice.py`

### Adding a New Model

1. Edit `src/national_treasure/core/models.py`:

```python
class MyModel(BaseModel):
    """Description."""

    id: str = Field(default_factory=generate_id)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def computed_field(self) -> float:
        return self.some_calculation()
```

### Adding Database Tables

1. Edit `src/national_treasure/core/database.py`
2. Add to `SCHEMA_SQL`:

```sql
-- My new table
CREATE TABLE IF NOT EXISTS my_table (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_my_table_name ON my_table(name);
```

3. Increment `SCHEMA_VERSION`

---

## Testing

### Running Tests

```bash
# All tests
pytest tests/unit/ -v

# Specific file
pytest tests/unit/test_models.py -v

# With coverage
pytest tests/unit/ --cov=national_treasure --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Writing Tests

```python
# tests/unit/test_myservice.py
import pytest
from national_treasure.services.myservice.service import MyService

class TestMyService:
    @pytest.mark.asyncio
    async def test_does_something(self, test_db):
        """Should do something correctly."""
        service = MyService(db_path=test_db)
        result = await service.do_something("input")
        assert result.success is True
```

### Test Fixtures

Available in `tests/conftest.py`:

| Fixture | Type | Purpose |
|---------|------|---------|
| `test_db` | async | Temporary SQLite database |
| `temp_dir` | sync | Temporary directory |
| `sample_urls` | sync | List of test URLs |
| `sample_selectors` | sync | Dict of test selectors |

---

## Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test CLI Commands Locally

```bash
# Run directly without installing
python -m national_treasure.cli.main --help

# With debug output
python -c "
import asyncio
from national_treasure.services.capture.service import CaptureService

async def test():
    async with CaptureService(headless=False) as service:
        result = await service.capture('https://httpbin.org/html')
        print(result)

asyncio.run(test())
"
```

### Inspect Database

```bash
sqlite3 ~/.national-treasure/national-treasure.db
.tables
.schema jobs
SELECT * FROM jobs LIMIT 5;
```

---

## Code Quality

### Linting

```bash
ruff check src/
ruff format src/
```

### Type Checking

```bash
mypy src/national_treasure
```

### Pre-commit (Optional)

```bash
pip install pre-commit
pre-commit install
```

---

## Common Patterns

### Error Handling in Services

```python
async def my_method(self) -> Result:
    try:
        # Happy path
        return Result(success=True, data=data)
    except SomeError as e:
        return Result(success=False, error=str(e))
```

### Database Transactions

```python
async with aiosqlite.connect(self.db_path) as db:
    try:
        await db.execute("INSERT INTO ...")
        await db.execute("UPDATE ...")
        await db.commit()
    except Exception:
        await db.rollback()
        raise
```

### Async Iteration

```python
async with db.execute("SELECT * FROM table") as cursor:
    async for row in cursor:
        yield dict(row)
```

---

## Deployment

### As a Package

```bash
pip install national-treasure
nt --version
```

### As a Service

```bash
# Run queue worker
nt queue run --workers 5

# In systemd/supervisor
[Unit]
Description=National Treasure Queue Worker

[Service]
ExecStart=/path/to/venv/bin/nt queue run --workers 3
Restart=always
```

---

## Getting Help

1. Read the code - it's well-documented
2. Check `techguide.md` for gotchas
3. Check `AUDIT.md` for implementation details
4. Run tests to understand behavior
