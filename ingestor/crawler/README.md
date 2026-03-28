# crawler

多源异类数据采集引擎（Python 库 + CLI）。用统一的领域模型描述「采什么」，用 `Crawler` 作为执行入口完成「怎么采」。

## 核心概念

### 数据抽象：`Source` → `Line` → `Data`

| 层级 | 含义 | 示例 |
|------|------|------|
| **Source** | 一个数据源整体 | 某站点、某 API 服务 |
| **Line** | 源下的一条采集通道 | 某栏目入口 URL、某 API 路径 |
| **Data** | 通道下的一条具体数据 | 某页正文、某条记录 |

`Source` **必须**带至少一条 `Line`。若构造时未传 `lines`（或传空列表），会自动创建 **默认 Line**：`id` 为 `{source.id}-default-line`，**`url` 与 `Source.url` 一致**。

### 执行抽象：`Crawler` → `Task` → `Data`

| 层级 | 含义 |
|------|------|
| **Crawler** | 单次采集运行容器：共享去重、下载器、限流、并发 |
| **Task** | 最小执行单元，对应一条 `Line` |
| **Data** | 单次下载 + 抽取后的结果条目 |

对应关系：**Source ↔ Crawler 配置**，**Line ↔ Task**；一个 Source 多条 Line，一次运行多个 Task；一条 Line 可对应多条 `Data`（由 Extractor 决定，默认整页一条）。

## 推荐用法（库）

主入口是 **`Crawler`**，传入带 `lines` 的 **`Source`**（或依赖默认 Line）即可：

```python
from crawler import Crawler, Source, SourceType

source = Source(
    id="my-site",
    name="示例站",
    type=SourceType.WEBSITE,
    url="https://example.com",
    # lines 可省略，将自动得到 url 与上面一致的默认 Line
)

result = await Crawler.run_source(source)
# result.task_results[*].items[*] 为 Data
```

### 默认与覆盖参数

- **`Source.crawl_defaults`**：字典，键与 `CrawlerBuildOptions` 一致（如 `timeout`、`headers`、`downloader` 等），相对 **按 `Source.type` 的预设**（`config/presets.py`）做默认覆盖。
- 单次运行可再传 **`options`**（`CrawlerBuildOptions`）或 **`overrides`**（字典）。

**合并优先级（从低到高）：** 类型预设 → `crawl_defaults` → 本次 `options` → 本次 `overrides`。  
其中 **`headers` 在 `crawl_defaults` 与 `options` 之间按 key 合并**，不是整表覆盖。

### 已有 `CrawlerConfig`（如 JSON）

```python
from crawler import Crawler, CrawlerConfig

config = CrawlerConfig.model_validate(data)
result = await Crawler(config).run()
```

测试或自定义网络层可注入假下载器：`Crawler(..., downloader=stub)` / `Crawler.run_source(..., downloader=stub)`。

## 命令行

安装后入口为 `crawler`：

```bash
# 快捷：仅 URL（内部构造 Source + 默认 Line）
crawler run --source-url https://example.com

# 使用序列化好的 CrawlerConfig JSON
crawler run --config crawl.json

# 查看类型预设
crawler presets
```

## 包结构（概要）

| 路径 | 职责 |
|------|------|
| `crawler.source` | `Source`、`Line` 领域模型 |
| `crawler.crawler` | `Crawler`、`CrawlerConfig`、`TaskExecutor`、`Data`、`Extractor` 等 |
| `crawler.config.presets` | 按 `SourceType` 的默认采集参数模板 |
| `crawler.downloaders` | HTTP 等下载器实现 |
| `crawler.cli` | Click CLI |

`Line.meta` 中若含整数 **`max_items`**，生成 `TaskConfig` 时会写入 **`max_items`** 且不会进入 `params`。

## 测试目录

`tests/` 下按 **`SourceType`** 分子目录（与 `SourceType` 枚举一致），便于按数据源类型扩展用例：

| 目录 | 说明 |
|------|------|
| `tests/core/` | 不依赖具体类型的逻辑（`CrawlerConfig` 直跑、Task、Extractor、校验等） |
| `tests/website/` | `WEBSITE` 预设与相关 Source / 配置 |
| `tests/api/` | `API` 预设与相关 Source / 配置 |
| `tests/file/`、`stream/`、`external/` | 预留，与 `FILE` / `STREAM` / `EXTERNAL` 对齐 |

共享 fixtures 仍在 `tests/conftest.py`，桩实现见 `tests/stubs.py`。

## 开发

要求 **Python ≥ 3.13**。

```bash
cd ingestor/crawler
uv sync --group dev
uv run pytest
```

## 依赖

`pydantic`、`httpx`、`click`、`rich`（详见 `pyproject.toml`）。
