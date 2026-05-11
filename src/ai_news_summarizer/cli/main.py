"""CLI interface for AI News Summarizer."""

import sys
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from ai_news_summarizer.core.processor import ProcessingResult
from ai_news_summarizer.core.service import AppService


if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


console = Console()


def load_dotenv_if_exists() -> None:
    """Load a local .env file when present."""
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)


@click.group()
@click.version_option(version="1.0.0")
def cli() -> None:
    """AI News Summarizer."""
    load_dotenv_if_exists()


@cli.command()
@click.option("--config", "-c", default="./config/default_config.yaml", help="Path to configuration file")
@click.option("--source", "-s", multiple=True, help="Filter by source name")
@click.option("--model", "-m", type=click.Choice(["openai", "anthropic", "ollama"]), help="Override LLM provider")
@click.option("--max-items", "-n", default=10, help="Maximum items per source")
@click.option("--output", "-o", type=click.Path(), help="Output to file")
@click.option("--format", "-f", type=click.Choice(["table", "html", "json"]), default="table", help="Output format")
def summarize(config: str, source: tuple[str, ...], model: str | None, max_items: int, output: str | None, format: str) -> None:
    """Fetch news and generate summaries."""
    import asyncio

    config_path = Path(config)
    if not config_path.exists():
        console.print(f"[red]Config file not found: {config}[/red]")
        return

    full_config = AppService.load_config(config_path)
    prepared = AppService.build_processor(full_config, provider_override=model, source_names=source or None)
    processor = prepared.processor

    console.print(f"[bold blue]Fetching news with provider {prepared.provider}...[/bold blue]")

    async def run() -> None:
        try:
            result = await processor.process(max_items_per_source=max_items)
            display_results(result, output, format)
        except Exception as exc:
            console.print(f"[red]Error: {exc}[/red]")
        finally:
            await processor.close()

    asyncio.run(run())


@cli.command()
@click.option("--source-type", "-t", type=click.Choice(["rss", "scraper", "api", "local"]))
@click.argument("url_or_path")
def fetch(source_type: str, url_or_path: str) -> None:
    """Fetch news from a single source for testing."""
    import asyncio

    if source_type == "rss":
        from ai_news_summarizer.sources.rss import RSSSource

        source = RSSSource(name="test", url=url_or_path)
        console.print(f"[bold]Testing RSS source:[/bold] {url_or_path}")
    elif source_type == "scraper":
        from ai_news_summarizer.sources.scraper import WebScraperSource

        source = WebScraperSource(name="test", url=url_or_path)
        console.print(f"[bold]Testing scraper source:[/bold] {url_or_path}")
    else:
        console.print("[red]Unsupported source type for direct testing[/red]")
        return

    async def run() -> None:
        try:
            items = await source.fetch()
            console.print(f"[green]Fetched {len(items)} items:[/green]")
            for item in items:
                console.print(f"  - {item.title}")
        except Exception as exc:
            console.print(f"[red]Error: {exc}[/red]")
        finally:
            await source.close()

    asyncio.run(run())


def display_results(result: ProcessingResult, output_path: Optional[str] = None, format: str = "table") -> None:
    """Display structured results in the requested format."""
    summaries = result.summaries

    if format == "html":
        content = generate_html(result)
    elif format == "json":
        import json

        content = json.dumps(
            {
                "total_fetched": result.total_fetched,
                "source_stats": result.source_stats,
                "results": [
                    {
                        "url": str(item.original_url) if item.original_url else None,
                        "summary": item.summary,
                        "model": item.model,
                        "tokens": item.token_usage,
                    }
                    for item in summaries
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    else:
        table = Table(title="News Summaries")
        table.add_column("Source", style="cyan")
        table.add_column("Summary", style="white")
        table.add_column("Model", style="dim")
        table.add_column("Tokens", style="dim")

        for item in summaries:
            url_str = str(item.original_url) if item.original_url else "N/A"
            table.add_row(
                url_str,
                item.summary[:100] + "..." if len(item.summary) > 100 else item.summary,
                item.model,
                str(item.token_usage or "N/A"),
            )

        if any(stat["status"] == "error" for stat in result.source_stats):
            console.print("[yellow]Some sources failed during fetching.[/yellow]")
            for stat in result.source_stats:
                if stat["status"] == "error":
                    console.print(f"  - {stat['name']}: {stat['error']}")

        if output_path:
            with open(output_path, "w", encoding="utf-8") as handle:
                handle.write(str(table))
            console.print(f"[green]Results written to {output_path}[/green]")
        else:
            console.print(table)
        return

    if output_path:
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(content)
        console.print(f"[green]{format.upper()} written to {output_path}[/green]")
    else:
        console.print(content)


def generate_html(result: ProcessingResult) -> str:
    """Generate a lightweight HTML report."""
    from datetime import datetime

    items_html = ""
    for item in result.summaries:
        url_str = str(item.original_url) if item.original_url else "#"
        items_html += f"""
        <div class="card">
            <h3><a href="{url_str}" target="_blank">{item.original_url or 'N/A'}</a></h3>
            <p class="summary">{item.summary.replace(chr(10), '<br>')}</p>
            <div class="meta">
                <span class="model">{item.model}</span>
                <span class="tokens">{item.token_usage} tokens</span>
            </div>
        </div>"""

    status_html = "".join(
        f"<li><strong>{stat['name']}</strong>: {stat['status']} ({stat['count']})"
        f"{' - ' + stat['error'] if stat['error'] else ''}</li>"
        for stat in result.source_stats
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI News Summaries - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ color: #333; margin-bottom: 20px; text-align: center; }}
        .meta-list {{ margin: 0 0 20px 20px; color: #666; }}
        .card {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .card h3 {{ color: #0066cc; margin-bottom: 10px; font-size: 14px; word-break: break-all; }}
        .card h3 a {{ color: inherit; text-decoration: none; }}
        .card h3 a:hover {{ text-decoration: underline; }}
        .summary {{ color: #333; line-height: 1.6; margin-bottom: 12px; }}
        .meta {{ display: flex; gap: 15px; font-size: 12px; color: #888; }}
        .model {{ background: #e8f4ff; padding: 2px 8px; border-radius: 4px; }}
        .tokens {{ background: #f0f0f0; padding: 2px 8px; border-radius: 4px; }}
        .empty {{ text-align: center; color: #888; padding: 40px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>AI News Summaries</h1>
        <ul class="meta-list">
            <li>Total fetched: {result.total_fetched}</li>
            {status_html}
        </ul>
        {items_html if items_html else '<div class="empty">No results found</div>'}
    </div>
</body>
</html>"""


@cli.command(name="web")
@click.option("--host", default="0.0.0.0", help="Host to bind")
@click.option("--port", default=8000, help="Port to bind")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def web(host: str, port: int, reload: bool) -> None:
    """Start the web interface."""
    import uvicorn
    from ai_news_summarizer.web.app import app

    console.print(f"[bold green]Starting web interface at http://localhost:{port}[/bold green]")
    console.print("[dim]Press Ctrl+C to stop[/dim]")
    uvicorn.run(app, host=host, port=port, reload=reload)


if __name__ == "__main__":
    cli()
