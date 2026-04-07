"""
Crawler 命令行入口

支持从配置文件加载参数并执行采集任务，输出结果或执行状态。
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys

import click
from rich.console import Console
from rich.table import Table

from crawler.source.presets import list_presets
from crawler.crawler import Crawler, CrawlerConfig
from crawler.source import Source, SourceType

console = Console()


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="启用详细日志")
def main(verbose: bool) -> None:
    """Crawler - 多源异类数据采集引擎 CLI"""
    _setup_logging(verbose)


@main.command()
@click.option("--config", "-c", "config_file", type=click.Path(exists=True), help="采集配置 JSON 文件路径")
@click.option("--source-url", help="数据源 URL（快捷模式）")
@click.option("--source-type", type=click.Choice([t.value for t in SourceType]), default="website", help="数据源类型")
@click.option("--output", "-o", type=click.Path(), help="结果输出文件路径（默认输出到 stdout）")
def run(
    config_file: str | None,
    source_url: str | None,
    source_type: str,
    output: str | None,
) -> None:
    """执行采集任务"""
    if config_file:
        with open(config_file) as f:
            raw = json.load(f)
        crawler_inst = Crawler(CrawlerConfig.model_validate(raw))
    elif source_url:
        crawler_inst = Crawler.from_source(
            Source(
                id="cli-source",
                name=source_url,
                type=SourceType(source_type),
                url=source_url,
            )
        )
    else:
        console.print("[red]请提供 --config 或 --source-url 参数[/red]")
        raise SystemExit(1)

    cc = crawler_inst.config
    console.print(f"[bold]Starting crawler:[/bold] {cc.crawler_id}")
    console.print(f"  Source: {cc.source_id} ({len(cc.tasks)} tasks)")

    result = asyncio.run(crawler_inst.run())

    result_data = result.model_dump(mode="json")
    if output:
        with open(output, "w") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        console.print(f"[green]Results written to {output}[/green]")
    else:
        click.echo(json.dumps(result_data, ensure_ascii=False, indent=2))


@main.command()
def presets() -> None:
    """列出所有预设配置模板"""
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
@click.option("--config", "-c", "config_file", type=click.Path(exists=True), required=True, help="采集配置 JSON 文件路径")
def show(config_file: str) -> None:
    """展示采集配置详情"""
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


if __name__ == "__main__":
    main()
