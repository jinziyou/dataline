"""
Crawler 命令行入口

所有命令都通过领域模型驱动：CLI 参数 → Source 对象 → Crawler.from_source() → run()。
支持自动检测选择器、手动指定选择器、从 JSON 配置文件加载等多种模式。
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import uuid

import click
from rich.console import Console
from rich.table import Table

from crawler.crawler.crawler import (
    EXTRACTOR_CONFIG_META_KEY,
    SOURCE_CRAWLER_BUILD_OPTIONS_META_KEY,
    Crawler,
    CrawlerConfig,
    DownloaderType,
)
from crawler.crawler.density import DensityBasedDetector
from crawler.source.line import Line
from crawler.source.presets import list_presets
from crawler.source.source import Source, SourceType

console = Console()


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )


def _build_source(
    url: str,
    *,
    source_type: str = "website",
    name: str | None = None,
    downloader: str | None = None,
    concurrency: int | None = None,
    timeout: float | None = None,
    rate_limit: float | None = None,
    max_items: int | None = None,
    link_selectors: tuple[str, ...] = (),
    title_selector: str | None = None,
    time_selector: str | None = None,
    content_selector: str | None = None,
) -> Source:
    """从 CLI 参数构建 Source 领域对象。"""
    source_id = f"cli-{uuid.uuid4().hex[:8]}"
    source_name = name or url

    crawler_build_options: dict = {}
    if downloader:
        crawler_build_options["downloader"] = downloader
    if concurrency is not None:
        crawler_build_options["concurrency"] = concurrency
    if timeout is not None:
        crawler_build_options["timeout"] = timeout
    if rate_limit is not None:
        crawler_build_options["rate_limit"] = rate_limit

    meta: dict = {}
    if crawler_build_options:
        meta[SOURCE_CRAWLER_BUILD_OPTIONS_META_KEY] = crawler_build_options

    extractor_config: dict = {}
    if link_selectors:
        extractor_config["link_selectors"] = list(link_selectors)
    if title_selector:
        extractor_config["title_selector"] = title_selector
    if time_selector:
        extractor_config["time_selector"] = time_selector
    if content_selector:
        extractor_config["content_selector"] = content_selector

    line_meta: dict = {}
    if extractor_config:
        line_meta[EXTRACTOR_CONFIG_META_KEY] = extractor_config

    line = Line(
        id=f"{source_id}-line",
        source_id=source_id,
        name=source_name,
        url=url,
        item_limit=max_items,
        meta=line_meta,
    )

    return Source(
        id=source_id,
        name=source_name,
        type=SourceType(source_type),
        url=url,
        meta=meta,
        lines=[line],
    )


def _print_source(source: Source) -> None:
    """展示 Source 对象详情。"""
    console.print(f"[bold]Source:[/bold] {source.name} [dim]({source.id})[/dim]")
    console.print(f"  Type: [cyan]{source.type.value}[/cyan]  URL: {source.url}")

    build_opts = source.meta.get(SOURCE_CRAWLER_BUILD_OPTIONS_META_KEY, {})
    if build_opts:
        parts = [f"{k}={v}" for k, v in build_opts.items()]
        console.print(f"  Options: {', '.join(parts)}")

    console.print(f"  Lines: {len(source.lines)}")
    for line in source.lines:
        ext_cfg = line.meta.get(EXTRACTOR_CONFIG_META_KEY, {})
        selectors = []
        if ext_cfg.get("link_selectors"):
            selectors.append(f"links={ext_cfg['link_selectors']}")
        if ext_cfg.get("title_selector"):
            selectors.append(f"title={ext_cfg['title_selector']!r}")
        if ext_cfg.get("content_selector"):
            selectors.append(f"content={ext_cfg['content_selector']!r}")
        sel_str = f"  [{', '.join(selectors)}]" if selectors else ""
        limit_str = f"  max={line.item_limit}" if line.item_limit else ""
        console.print(f"    [dim]→[/dim] {line.name} ({line.url}){limit_str}{sel_str}")


def _print_result(result) -> None:
    """展示 CrawlerResult 摘要。"""
    console.print()
    console.print(f"[bold green]Finished[/bold green] {result.crawler_id}")
    console.print(
        f"  Tasks: {len(result.task_results)} | "
        f"Items: {result.total_items} | "
        f"Success: {result.success_count} | "
        f"Failed: {result.failed_count}"
    )

    if result.started_at and result.finished_at:
        elapsed = (result.finished_at - result.started_at).total_seconds()
        console.print(f"  Elapsed: {elapsed:.1f}s")

    for tr in result.task_results:
        status_style = "green" if tr.status.value == "success" else "red"
        console.print(
            f"\n  [{status_style}]{tr.status.value.upper()}[/{status_style}] "
            f"Task {tr.task_id} ({tr.item_count} items)"
        )
        if tr.error:
            console.print(f"    [red]Error: {tr.error}[/red]")
        for item in tr.items[:5]:
            title = item.title[:60] if item.title else "(no title)"
            console.print(f"    • {title}  [dim]{item.url}[/dim]")
        if tr.item_count > 5:
            console.print(f"    [dim]... and {tr.item_count - 5} more[/dim]")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="启用详细日志")
def main(verbose: bool) -> None:
    """Crawler - 多源异类数据采集引擎 CLI"""
    _setup_logging(verbose)


@main.command()
@click.argument("url")
@click.option("-t", "--type", "source_type", type=click.Choice([t.value for t in SourceType]), default="website", help="数据源类型")
@click.option("-d", "--downloader", type=click.Choice(["http", "playwright"]), default=None, help="下载器类型（默认随 source-type 预设）")
@click.option("-n", "--max-items", type=int, default=None, help="最大采集条数")
@click.option("--concurrency", type=int, default=None, help="并发数")
@click.option("--timeout", type=float, default=None, help="请求超时（秒）")
@click.option("--rate-limit", type=float, default=None, help="请求速率限制（次/秒）")
@click.option("--link-selector", "link_selectors", multiple=True, help="链接 CSS 选择器（可多次指定，按层级）")
@click.option("--title-selector", default=None, help="标题 CSS 选择器")
@click.option("--time-selector", default=None, help="时间 CSS 选择器")
@click.option("--content-selector", default=None, help="正文 CSS 选择器")
@click.option("--auto-detect", is_flag=True, help="自动检测选择器（信息密度算法）")
@click.option("-o", "--output", type=click.Path(), default=None, help="结果输出 JSON 路径（默认 stdout）")
def run(
    url: str,
    source_type: str,
    downloader: str | None,
    max_items: int | None,
    concurrency: int | None,
    timeout: float | None,
    rate_limit: float | None,
    link_selectors: tuple[str, ...],
    title_selector: str | None,
    time_selector: str | None,
    content_selector: str | None,
    auto_detect: bool,
    output: str | None,
) -> None:
    """从 URL 构建 Source 并执行采集。

    示例：

    \b
      crawler run https://example.com
      crawler run https://example.com -d playwright --auto-detect -n 10
      crawler run https://example.com --link-selector "a.title" --content-selector "article"
    """
    source = _build_source(
        url,
        source_type=source_type,
        downloader=downloader,
        concurrency=concurrency,
        timeout=timeout,
        rate_limit=rate_limit,
        max_items=max_items,
        link_selectors=link_selectors,
        title_selector=title_selector,
        time_selector=time_selector,
        content_selector=content_selector,
    )

    if auto_detect:
        source = asyncio.run(_auto_detect_and_update(source, downloader))

    _print_source(source)
    console.print()

    crawler = Crawler.from_source(source)
    console.print(f"[bold]Crawler:[/bold] {crawler.config.crawler_id}")
    console.print(
        f"  Downloader: [cyan]{crawler.config.downloader.value}[/cyan] | "
        f"Tasks: {len(crawler.config.tasks)} | "
        f"Concurrency: {crawler.config.concurrency}"
    )

    result = asyncio.run(crawler.run())

    _print_result(result)

    result_data = result.model_dump(mode="json")
    if output:
        with open(output, "w") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        console.print(f"\n[green]Results written to {output}[/green]")
    else:
        console.print()
        click.echo(json.dumps(result_data, ensure_ascii=False, indent=2))


@main.command()
@click.argument("url")
@click.option("-d", "--downloader", type=click.Choice(["http", "playwright"]), default=None, help="下载页面使用的下载器")
def detect(url: str, downloader: str | None) -> None:
    """分析页面结构，自动检测 CSS 选择器。

    下载目标 URL 的 HTML 页面，使用 DensityBasedDetector 分析信息密度，
    输出推荐的链接选择器和数据选择器。

    \b
      crawler detect https://example.com/news
      crawler detect https://36kr.com -d playwright
    """
    detected = asyncio.run(_detect_selectors(url, downloader))

    console.print(f"[bold]Detected selectors for[/bold] {url}\n")

    table = Table(title="链接选择器（列表页）")
    table.add_column("选择器", style="cyan")
    if detected["link_selectors"]:
        for sel in detected["link_selectors"]:
            table.add_row(sel)
    else:
        table.add_row("[dim]未检测到[/dim]")
    console.print(table)

    console.print()

    table2 = Table(title="数据选择器（详情页）")
    table2.add_column("字段", style="green")
    table2.add_column("选择器", style="cyan")
    table2.add_row("标题", detected.get("title_selector") or "[dim]未检测到[/dim]")
    table2.add_row("时间", detected.get("time_selector") or "[dim]未检测到[/dim]")
    table2.add_row("正文", detected.get("content_selector") or "[dim]未检测到[/dim]")
    console.print(table2)

    if detected["link_selectors"] or any(detected.get(k) for k in ("title_selector", "time_selector", "content_selector")):
        console.print("\n[bold]推荐命令：[/bold]")
        parts = [f"crawler run {url}"]
        if downloader:
            parts.append(f"-d {downloader}")
        for sel in detected["link_selectors"]:
            parts.append(f'--link-selector "{sel}"')
        if detected.get("title_selector"):
            parts.append(f'--title-selector "{detected["title_selector"]}"')
        if detected.get("content_selector"):
            parts.append(f'--content-selector "{detected["content_selector"]}"')
        console.print(f"  [green]{' '.join(parts)}[/green]")


@main.command("from-config")
@click.argument("config_file", type=click.Path(exists=True))
@click.option("-o", "--output", type=click.Path(), default=None, help="结果输出 JSON 路径")
def from_config(config_file: str, output: str | None) -> None:
    """从 CrawlerConfig JSON 文件直接执行采集。

    \b
      crawler from-config crawl.json
      crawler from-config crawl.json -o result.json
    """
    with open(config_file) as f:
        raw = json.load(f)
    config = CrawlerConfig.model_validate(raw)
    crawler = Crawler(config)

    console.print(f"[bold]Crawler:[/bold] {config.crawler_id}")
    console.print(
        f"  Source: {config.source_id} ({config.source_name}) | "
        f"Downloader: [cyan]{config.downloader.value}[/cyan] | "
        f"Tasks: {len(config.tasks)}"
    )

    result = asyncio.run(crawler.run())

    _print_result(result)

    result_data = result.model_dump(mode="json")
    if output:
        with open(output, "w") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        console.print(f"\n[green]Results written to {output}[/green]")
    else:
        console.print()
        click.echo(json.dumps(result_data, ensure_ascii=False, indent=2))


@main.command("from-source")
@click.argument("source_file", type=click.Path(exists=True))
@click.option("-o", "--output", type=click.Path(), default=None, help="结果输出 JSON 路径")
def from_source(source_file: str, output: str | None) -> None:
    """从 Source JSON 文件构建 Crawler 并执行。

    Source JSON 示例：

    \b
      {
        "id": "my-site", "name": "示例", "type": "website",
        "url": "https://example.com",
        "lines": [{"id": "l1", "source_id": "my-site", "name": "首页", "url": "..."}]
      }
    """
    with open(source_file) as f:
        raw = json.load(f)
    source = Source.model_validate(raw)

    _print_source(source)
    console.print()

    crawler = Crawler.from_source(source)
    console.print(f"[bold]Crawler:[/bold] {crawler.config.crawler_id}")

    result = asyncio.run(crawler.run())

    _print_result(result)

    result_data = result.model_dump(mode="json")
    if output:
        with open(output, "w") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        console.print(f"\n[green]Results written to {output}[/green]")
    else:
        console.print()
        click.echo(json.dumps(result_data, ensure_ascii=False, indent=2))


@main.command()
def presets() -> None:
    """列出所有数据源类型的预设配置。"""
    table = Table(title="数据源预设配置")
    table.add_column("类型", style="cyan")
    table.add_column("下载器", style="green")
    table.add_column("并发数")
    table.add_column("超时(s)")
    table.add_column("限速(req/s)")
    table.add_column("说明")

    for _, preset in list_presets().items():
        table.add_row(
            preset.source_type.value,
            str(preset.downloader),
            str(preset.concurrency),
            str(preset.timeout),
            str(preset.rate_limit or "无"),
            preset.description,
        )

    console.print(table)


@main.command()
@click.argument("config_file", type=click.Path(exists=True))
def show(config_file: str) -> None:
    """展示 CrawlerConfig JSON 的详情。"""
    with open(config_file) as f:
        raw = json.load(f)
    config = CrawlerConfig.model_validate(raw)

    console.print(f"[bold]Crawler:[/bold] {config.crawler_id}")
    console.print(f"  Source: {config.source_id} ({config.source_name})")
    console.print(f"  Downloader: {config.downloader.value}")
    console.print(f"  Concurrency: {config.concurrency}")
    console.print(f"  Tasks: {len(config.tasks)}")

    table = Table(title="Tasks")
    table.add_column("Task ID", style="cyan")
    table.add_column("Line ID")
    table.add_column("URL")
    for task in config.tasks:
        table.add_row(task.task_id, task.line_id, task.url or "-")
    console.print(table)


# ---------------------------------------------------------------------------
# Async helpers
# ---------------------------------------------------------------------------


async def _download_page(url: str, downloader_type: str | None) -> str:
    """下载页面 HTML，返回文本内容。"""
    if downloader_type == "playwright":
        from crawler.crawler.downloaders.playwright import PlaywrightDownloader

        dl = PlaywrightDownloader()
    else:
        from crawler.crawler.downloaders.http import HttpDownloader

        dl = HttpDownloader(
            default_headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
            },
        )
    try:
        response = await dl.download(url)
        return response.text
    finally:
        await dl.close()


async def _detect_selectors(url: str, downloader_type: str | None) -> dict:
    """下载页面并运行 DensityBasedDetector。"""
    console.print(f"[dim]Downloading {url} ...[/dim]")
    html = await _download_page(url, downloader_type)
    console.print(f"[dim]Downloaded {len(html)} chars, analyzing ...[/dim]")

    detector = DensityBasedDetector()
    link_selectors = detector.detect_from_listing(html)
    detail = detector.detect_from_detail(html)

    return {
        "link_selectors": link_selectors,
        "title_selector": detail.title_selector,
        "time_selector": detail.time_selector,
        "content_selector": detail.content_selector,
    }


async def _auto_detect_and_update(source: Source, downloader_type: str | None) -> Source:
    """下载 Source URL，自动检测选择器，更新到 Line.meta 中。"""
    if not source.url:
        console.print("[yellow]Source 无 URL，跳过自动检测[/yellow]")
        return source

    detected = await _detect_selectors(source.url, downloader_type)

    if not detected["link_selectors"] and not any(
        detected.get(k) for k in ("title_selector", "time_selector", "content_selector")
    ):
        console.print("[yellow]未检测到有效选择器，使用默认整页提取模式[/yellow]")
        return source

    console.print("[green]自动检测选择器：[/green]")
    if detected["link_selectors"]:
        console.print(f"  links: {detected['link_selectors']}")
    for key in ("title_selector", "time_selector", "content_selector"):
        if detected.get(key):
            console.print(f"  {key}: {detected[key]}")

    ext_config: dict = {}
    if detected["link_selectors"]:
        ext_config["link_selectors"] = detected["link_selectors"]
    if detected.get("title_selector"):
        ext_config["title_selector"] = detected["title_selector"]
    if detected.get("time_selector"):
        ext_config["time_selector"] = detected["time_selector"]
    if detected.get("content_selector"):
        ext_config["content_selector"] = detected["content_selector"]

    updated_lines = []
    for line in source.lines:
        existing = line.meta.get(EXTRACTOR_CONFIG_META_KEY, {})
        if not existing:
            new_meta = {**line.meta, EXTRACTOR_CONFIG_META_KEY: ext_config}
            updated_lines.append(line.model_copy(update={"meta": new_meta}))
        else:
            updated_lines.append(line)

    return source.model_copy(update={"lines": updated_lines})


if __name__ == "__main__":
    main()
