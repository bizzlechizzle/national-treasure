"""National Treasure CLI - Web archiving with adaptive learning."""

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from national_treasure import __version__
from national_treasure.core.config import get_config, Config
from national_treasure.core.database import init_database

# Create CLI app
app = typer.Typer(
    name="nt",
    help="National Treasure - Web archiving with adaptive learning",
    no_args_is_help=True,
)

# Sub-apps
capture_app = typer.Typer(help="Capture web pages")
queue_app = typer.Typer(help="Job queue management")
training_app = typer.Typer(help="Selector training")
learning_app = typer.Typer(help="Domain learning insights")
db_app = typer.Typer(help="Database management")

app.add_typer(capture_app, name="capture")
app.add_typer(queue_app, name="queue")
app.add_typer(training_app, name="training")
app.add_typer(learning_app, name="learning")
app.add_typer(db_app, name="db")

console = Console()


def version_callback(value: bool):
    if value:
        console.print(f"national-treasure v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True,
        help="Show version"
    ),
):
    """National Treasure - Web archiving with adaptive learning."""
    pass


# ============================================================================
# Capture Commands
# ============================================================================

@capture_app.command("url")
def capture_url(
    url: str = typer.Argument(..., help="URL to capture"),
    formats: str = typer.Option(
        "screenshot,html",
        "--formats", "-f",
        help="Comma-separated formats: screenshot,pdf,html,warc"
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o",
        help="Output directory"
    ),
    headless: bool = typer.Option(
        True, "--headless/--visible",
        help="Run in headless mode"
    ),
    behaviors: bool = typer.Option(
        True, "--behaviors/--no-behaviors",
        help="Run page behaviors (scroll, expand, etc.)"
    ),
    timeout: int = typer.Option(
        30000, "--timeout", "-t",
        help="Page load timeout in ms"
    ),
):
    """Capture a single URL in specified formats."""
    from national_treasure.services.capture.service import CaptureService

    format_list = [f.strip() for f in formats.split(",")]

    async def do_capture():
        config = get_config()
        if output:
            config.archive_dir = output

        async with CaptureService(headless=headless, output_dir=output) as service:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Capturing {url}...", total=None)
                result = await service.capture(
                    url,
                    formats=format_list,
                    run_behaviors=behaviors,
                    timeout_ms=timeout,
                )
                progress.remove_task(task)

            return result

    result = asyncio.run(do_capture())

    if result.success:
        console.print(f"[green]Success![/green] Captured: {url}")
        if result.screenshot_path:
            console.print(f"  Screenshot: {result.screenshot_path}")
        if result.pdf_path:
            console.print(f"  PDF: {result.pdf_path}")
        if result.html_path:
            console.print(f"  HTML: {result.html_path}")
        if result.warc_path:
            console.print(f"  WARC: {result.warc_path}")
        console.print(f"  Duration: {result.duration_ms}ms")
    else:
        console.print(f"[red]Failed![/red] {result.error}")
        if result.validation:
            console.print(f"  Blocked: {result.validation.blocked}")
            console.print(f"  Reason: {result.validation.reason}")
        raise typer.Exit(1)


@capture_app.command("batch")
def capture_batch(
    input_file: Path = typer.Argument(..., help="File with URLs (one per line)"),
    formats: str = typer.Option("screenshot,html", "--formats", "-f"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
    concurrent: int = typer.Option(3, "--concurrent", "-c", help="Concurrent captures"),
):
    """Capture multiple URLs from a file."""
    from national_treasure.services.capture.service import CaptureService
    from national_treasure.services.learning.domain import DomainLearner
    from urllib.parse import urlparse

    if not input_file.exists():
        console.print(f"[red]Error:[/red] File not found: {input_file}")
        raise typer.Exit(1)

    urls = [line.strip() for line in input_file.read_text().splitlines() if line.strip()]

    if not urls:
        console.print("[yellow]No URLs found in file[/yellow]")
        raise typer.Exit(0)

    format_list = [f.strip() for f in formats.split(",")]
    results = {"success": 0, "failed": 0}

    async def capture_with_learning(url: str, service: CaptureService, learner: DomainLearner):
        domain = urlparse(url).netloc
        config = await learner.get_best_config(domain)

        result = await service.capture(url, formats=format_list, run_behaviors=True)

        # Record outcome for learning
        await learner.record_outcome(
            domain,
            config,
            result.success,
            {"response_code": result.validation.http_status if result.validation else None},
        )

        return result

    async def do_batch():
        learner = DomainLearner()

        async with CaptureService(headless=True, output_dir=output) as service:
            with Progress(console=console) as progress:
                task = progress.add_task("Capturing URLs...", total=len(urls))

                for url in urls:
                    try:
                        result = await capture_with_learning(url, service, learner)
                        if result.success:
                            results["success"] += 1
                        else:
                            results["failed"] += 1
                            console.print(f"[red]Failed:[/red] {url} - {result.error}")
                    except Exception as e:
                        results["failed"] += 1
                        console.print(f"[red]Error:[/red] {url} - {e}")

                    progress.advance(task)

    asyncio.run(do_batch())

    console.print(f"\n[green]Completed:[/green] {results['success']} succeeded, {results['failed']} failed")


# ============================================================================
# Queue Commands
# ============================================================================

@queue_app.command("add")
def queue_add(
    url: str = typer.Argument(..., help="URL to queue"),
    priority: int = typer.Option(0, "--priority", "-p", help="Job priority"),
):
    """Add a URL to the capture queue."""
    from national_treasure.services.queue.service import JobQueue
    from national_treasure.core.models import JobType

    async def do_add():
        queue = JobQueue()
        job_id = await queue.enqueue(
            JobType.CAPTURE,
            {"url": url, "formats": ["screenshot", "html"]},
            priority=priority,
        )
        return job_id

    job_id = asyncio.run(do_add())
    console.print(f"[green]Queued:[/green] {job_id}")


@queue_app.command("status")
def queue_status():
    """Show queue status."""
    from national_treasure.services.queue.service import JobQueue

    async def do_status():
        queue = JobQueue()
        return await queue.get_queue_stats()

    stats = asyncio.run(do_status())

    table = Table(title="Queue Status")
    table.add_column("Status", style="cyan")
    table.add_column("Count", justify="right")

    for status, count in stats.items():
        table.add_row(status, str(count))

    console.print(table)


@queue_app.command("run")
def queue_run(
    workers: int = typer.Option(3, "--workers", "-w", help="Number of workers"),
):
    """Start processing the queue."""
    from national_treasure.services.queue.service import JobQueue
    from national_treasure.services.capture.service import CaptureService
    from national_treasure.core.models import JobType, Job

    async def handle_capture(job: Job):
        url = job.payload.get("url")
        formats = job.payload.get("formats", ["screenshot", "html"])

        async with CaptureService(headless=True) as service:
            result = await service.capture(url, formats=formats)
            if not result.success:
                raise Exception(result.error)
            return {"url": url, "success": True}

    async def do_run():
        queue = JobQueue()
        queue.register_handler(JobType.CAPTURE, handle_capture)

        console.print(f"[green]Starting queue with {workers} workers...[/green]")
        console.print("Press Ctrl+C to stop\n")

        await queue.start(num_workers=workers)

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping...[/yellow]")
            await queue.stop()

    asyncio.run(do_run())


@queue_app.command("dead-letter")
def queue_dead_letter(
    limit: int = typer.Option(10, "--limit", "-l"),
):
    """Show dead letter queue."""
    from national_treasure.services.queue.service import JobQueue

    async def do_list():
        queue = JobQueue()
        return await queue.get_dead_letter_jobs(limit=limit)

    jobs = asyncio.run(do_list())

    if not jobs:
        console.print("[green]No failed jobs in dead letter queue[/green]")
        return

    table = Table(title="Dead Letter Queue")
    table.add_column("Job ID", style="cyan")
    table.add_column("Type")
    table.add_column("Error", max_width=40)
    table.add_column("Retries")
    table.add_column("Failed At")

    for job in jobs:
        table.add_row(
            job["job_id"][:8] + "...",
            job["job_type"],
            str(job["error"])[:40],
            str(job["retry_count"]),
            job["failed_at"][:19],
        )

    console.print(table)


# ============================================================================
# Training Commands
# ============================================================================

@training_app.command("stats")
def training_stats():
    """Show training statistics."""
    from national_treasure.services.scraper.training import TrainingService

    async def do_stats():
        service = TrainingService()
        return await service.get_training_stats()

    stats = asyncio.run(do_stats())

    console.print("\n[bold]Selector Training Statistics[/bold]")

    sel = stats.get("selectors", {})
    console.print(f"  Total patterns: {sel.get('total_patterns', 0)}")
    console.print(f"  Unique sites: {sel.get('unique_sites', 0)}")
    console.print(f"  Unique fields: {sel.get('unique_fields', 0)}")
    console.print(f"  Total successes: {sel.get('total_successes', 0)}")
    console.print(f"  Total failures: {sel.get('total_failures', 0)}")
    console.print(f"  Avg confidence: {sel.get('avg_confidence', 0):.1%}")

    if stats.get("top_sites"):
        console.print("\n[bold]Top Sites by Patterns:[/bold]")
        for site in stats["top_sites"][:5]:
            console.print(f"  {site['site']}: {site['patterns']} patterns")


@training_app.command("export")
def training_export(
    output: Path = typer.Argument(..., help="Output JSON file"),
    site: Optional[str] = typer.Option(None, "--site", "-s", help="Filter by site"),
):
    """Export training data to JSON."""
    from national_treasure.services.scraper.training import TrainingService

    async def do_export():
        service = TrainingService()
        return await service.export_training_data(site=site)

    data = asyncio.run(do_export())

    output.write_text(json.dumps(data, indent=2))
    console.print(f"[green]Exported to:[/green] {output}")
    console.print(f"  Selectors: {len(data['selectors'])}")
    console.print(f"  URL patterns: {len(data['url_patterns'])}")


@training_app.command("import")
def training_import(
    input_file: Path = typer.Argument(..., help="Input JSON file"),
    merge: bool = typer.Option(True, "--merge/--replace", help="Merge or replace data"),
):
    """Import training data from JSON."""
    from national_treasure.services.scraper.training import TrainingService

    if not input_file.exists():
        console.print(f"[red]Error:[/red] File not found: {input_file}")
        raise typer.Exit(1)

    data = json.loads(input_file.read_text())

    async def do_import():
        service = TrainingService()
        return await service.import_training_data(data, merge=merge)

    counts = asyncio.run(do_import())
    console.print(f"[green]Imported:[/green]")
    console.print(f"  Selectors: {counts['selectors']}")
    console.print(f"  URL patterns: {counts['url_patterns']}")


# ============================================================================
# Learning Commands
# ============================================================================

@learning_app.command("insights")
def learning_insights(
    domain: str = typer.Argument(..., help="Domain to analyze"),
):
    """Get learning insights for a domain."""
    from national_treasure.services.learning.domain import DomainLearner

    async def do_insights():
        learner = DomainLearner()
        return await learner.get_domain_insights(domain)

    insights = asyncio.run(do_insights())

    console.print(f"\n[bold]Insights for {domain}[/bold]")
    console.print(f"  Total attempts: {insights['total_attempts']}")
    console.print(f"  Success rate: {insights['success_rate']:.1%}")

    if insights.get("best_headless_mode"):
        h = insights["best_headless_mode"]
        console.print(f"\n  Best headless mode: {h['mode']} ({h['success_rate']:.1%})")

    if insights.get("best_wait_strategy"):
        w = insights["best_wait_strategy"]
        console.print(f"  Best wait strategy: {w['strategy']} ({w['success_rate']:.1%})")

    if insights.get("best_user_agent"):
        ua = insights["best_user_agent"]
        console.print(f"  Best user agent: {ua['ua_key']} ({ua['success_rate']:.1%})")

    if insights.get("recommendations"):
        console.print("\n[bold]Recommendations:[/bold]")
        for rec in insights["recommendations"]:
            console.print(f"  - {rec}")


@learning_app.command("stats")
def learning_stats():
    """Show global learning statistics."""
    from national_treasure.services.learning.domain import DomainLearner

    async def do_stats():
        learner = DomainLearner()
        return await learner.get_global_stats()

    stats = asyncio.run(do_stats())

    console.print("\n[bold]Global Learning Statistics[/bold]")
    console.print(f"  Total domains: {stats['total_domains']}")
    console.print(f"  Total requests: {stats['total_requests']}")
    console.print(f"  Overall success rate: {stats['overall_success_rate']:.1%}")

    if stats.get("top_performing_configs"):
        console.print("\n[bold]Top Performing Configs:[/bold]")
        for cfg in stats["top_performing_configs"]:
            console.print(f"  {cfg['config']}: {cfg['success_rate']:.1%} ({cfg['attempts']} attempts)")

    if stats.get("problematic_domains"):
        console.print("\n[bold]Problematic Domains:[/bold]")
        for d in stats["problematic_domains"]:
            console.print(f"  {d['domain']}: {d['success_rate']:.1%} ({d['attempts']} attempts)")


# ============================================================================
# Database Commands
# ============================================================================

@db_app.command("init")
def db_init(
    force: bool = typer.Option(False, "--force", "-f", help="Force recreate"),
):
    """Initialize the database."""
    config = get_config()

    if config.database_path.exists() and not force:
        console.print(f"[yellow]Database already exists:[/yellow] {config.database_path}")
        console.print("Use --force to recreate")
        raise typer.Exit(1)

    asyncio.run(init_database(str(config.database_path)))
    console.print(f"[green]Database initialized:[/green] {config.database_path}")


@db_app.command("info")
def db_info():
    """Show database information."""
    import sqlite3

    config = get_config()

    if not config.database_path.exists():
        console.print(f"[red]Database not found:[/red] {config.database_path}")
        console.print("Run: nt db init")
        raise typer.Exit(1)

    conn = sqlite3.connect(config.database_path)
    cursor = conn.cursor()

    # Get tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    table = Table(title=f"Database: {config.database_path}")
    table.add_column("Table", style="cyan")
    table.add_column("Rows", justify="right")

    for tbl in sorted(tables):
        if tbl.startswith("sqlite_"):
            continue
        cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
        count = cursor.fetchone()[0]
        table.add_row(tbl, str(count))

    console.print(table)
    conn.close()


# ============================================================================
# Config Command
# ============================================================================

@app.command("config")
def show_config():
    """Show current configuration."""
    config = get_config()

    console.print("\n[bold]Current Configuration[/bold]")
    console.print(f"  Database: {config.database_path}")
    console.print(f"  Archive dir: {config.archive_dir}")
    console.print(f"  Log level: {config.log_level}")


if __name__ == "__main__":
    app()
