# crawler

请参考@ingestor/crawler/README.md 需求，优化@ingestor/crawler 中代码：1、采用TDD开发模式，编写各个场景下的测试用例；2、采用DDD设计模式，将爬取相关代码统一放入crawler和source域中，要求面向对象，source是信息源的抽象，crawler是爬取的执行者抽象，通过创建对象来组织功能和逻辑，有配置的概念（通过用户输入的参数，实列化对应source，然后程序通过信息密度算法，得出链接页面中的链接选择器和数据页面的标题、时间和内容等选择，组合生成cralwer，然后通过crawler执行相关数据获取操作）；3、source和crawler域中对象的对应关系：source->line->data,crawler->task->extractor(跟line中数据层级对应，最少拥有一个或多个链接extractor和一个数据extractor)，完成任务后请更新文档


多源异类数据采集引擎（Python 库 + CLI）。用统一的领域模型描述「采什么」，用 `Crawler` 作为执行入口完成「怎么采」。
采用 TDD 与 DDD：两个有界上下文——**`source`（采什么）** 与 **`crawler`（怎么采）**；`config` 不作为独立领域包。

## 核心概念

### 数据抽象：`Source` → `Line` → `Data`

| 层级 | 含义 | 示例 |
|------|------|------|
| **Source** | 一个数据源整体 | 某站点、某 API 服务 |
| **Line** | 源下的一条采集通道 | 某栏目入口 URL、某 API 路径 |
| **Data** | 通道下的一条具体数据 | 某页正文、某条记录 |

`Source` **必须**带至少一条 `Line`。若构造时未传 `lines`（或传空列表），会自动创建 **默认 Line**：`id` 为 `{source.id}-default-line`，**`url` 与 `Source.url` 一致**。

### 执行抽象：`Crawler` → `Task` → `Extractor`

| 层级 | 含义 |
|------|------|
| **Crawler** | 单次采集运行容器：共享去重、下载器、限流、并发 |
| **Task** | 最小执行单元，对应一条 `Line` |
| **Extractor** | 数据提取器，跟 Line 中数据层级对应 |

对应关系：**Source ↔ Crawler 配置**，**Line ↔ Task**，**Data ↔ Extractor 产出**；一个 Source 多条 Line，一次运行多个 Task；每个 Task 拥有至少一个或多个 **LinkExtractor**（链接发现层）和一个 **DataExtractor**（数据提取层）。

### Extractor 管线

```
列表页 URL ──LinkExtractor──→ 详情页 URL 列表 ──DataExtractor──→ Data[]
                                      ↑
                              可多级串联（分类页→子列表→详情页）
```

| 提取器 | 职责 | 输入 → 输出 |
|--------|------|-------------|
| **LinkExtractor** | 从列表/导航页提取下一级 URL | `DownloadResponse` → `list[str]`（URL 列表） |
| **DataExtractor** | 从详情页提取结构化数据（标题、时间、正文） | `DownloadResponse` → `list[Data]` |
| **PageExtractor** | 默认整页提取器（无选择器时兼容回退） | `DownloadResponse` → `list[Data]`（整页为一条） |

### 信息密度检测：`DensityBasedDetector`

通过分析页面 HTML 结构自动推导选择器，无需手动编写 CSS 选择器：

```python
from crawler import DensityBasedDetector

detector = DensityBasedDetector()

# 从列表页自动检测链接选择器
link_selectors = detector.detect_from_listing(listing_html)
# => [".news-list a[href]"]

# 从详情页自动检测标题/时间/正文选择器
selectors = detector.detect_from_detail(detail_html)
# => DetectedSelectors(title_selector="h1", time_selector="time", content_selector="article")
```

## 推荐用法（库）

### 基础用法（直接提取）

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

### 带选择器配置（链接发现 + 数据提取管线）

通过 `Line.meta["extractor_config"]` 配置提取管线：

```python
from crawler import Crawler, Source, SourceType, Line, EXTRACTOR_CONFIG_META_KEY

source = Source(
    id="news-site",
    name="新闻站",
    type=SourceType.WEBSITE,
    url="https://news.example.com",
    lines=[
        Line(
            id="tech-news",
            source_id="news-site",
            name="科技新闻",
            url="https://news.example.com/tech",
            meta={
                EXTRACTOR_CONFIG_META_KEY: {
                    "link_selectors": [".article-list a"],
                    "title_selector": "h1.title",
                    "time_selector": ".publish-date",
                    "content_selector": ".article-body",
                }
            },
        )
    ],
)

result = await Crawler.run_source(source)
for task_result in result.task_results:
    for item in task_result.items:
        print(f"{item.title}: {item.content[:100]}...")
```

### 自动检测选择器（信息密度算法）

```python
from crawler import Crawler, Source, SourceType, DensityBasedDetector, EXTRACTOR_CONFIG_META_KEY

source = Source(
    id="auto-site",
    name="自动检测站",
    type=SourceType.WEBSITE,
    url="https://example.com/news",
)

# 1. 下载样本页面进行分析
# 2. 用密度检测器推导选择器
detector = DensityBasedDetector()
link_selectors = detector.detect_from_listing(sample_listing_html)
data_selectors = detector.detect_from_detail(sample_detail_html)

# 3. 将检测结果写入 Line.meta
for line in source.lines:
    line.meta[EXTRACTOR_CONFIG_META_KEY] = {
        "link_selectors": link_selectors,
        "title_selector": data_selectors.title_selector,
        "time_selector": data_selectors.time_selector,
        "content_selector": data_selectors.content_selector,
    }

# 4. 运行
result = await Crawler.run_source(source)
```

### 默认与覆盖参数

- **数据源级采集默认项**：放在 `Source.meta` 的 **`SOURCE_CRAWLER_BUILD_OPTIONS_META_KEY`**（字面量键名 `"crawler_build_options"`；值为字典，字段与 `CrawlerBuildOptions` 一致，如 `timeout`、`headers`、`downloader`），相对 **按 `Source.type` 的类型预设**（`crawler.source.presets`）再覆盖。
- 单次运行可再传 **`options`**（`CrawlerBuildOptions`）或 **`overrides`**（字典）。

**合并优先级（从低到高）：** 类型预设 → `meta[SOURCE_CRAWLER_BUILD_OPTIONS_META_KEY]` → 本次 `options` → 本次 `overrides`。  
其中 **`headers` 在 meta 块与 `options` 之间按 key 合并**，不是整表覆盖。

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
| `crawler.source` | `Source`、`Line`、按 `SourceType` 的 **类型预设**（`presets`） |
| `crawler.crawler` | `Crawler`、`CrawlerConfig`、`TaskExecutor`、`Data`、Extractor 层级等 |
| `crawler.crawler.extractor` | `LinkExtractor`、`DataExtractor`、`PageExtractor`、`Extractor` 协议 |
| `crawler.crawler.density` | `DensityBasedDetector`、`SelectorDetector` 协议、`DetectedSelectors` |
| `crawler.crawler.downloaders` | HTTP 等下载器实现（执行子域内） |
| `crawler.cli` | 应用层 CLI |

### 域对象对应关系

```
Source 域（采什么）          Crawler 域（怎么采）
─────────────────          ────────────────────
Source ──────────────────── Crawler（配置 + 运行容器）
  └─ Line ──────────────── Task（最小执行单元）
      └─ Data ◄──────────── Extractor（提取管线）
                               ├─ LinkExtractor（链接发现，1..N）
                               └─ DataExtractor（数据提取，1）
```

`Line.meta["extractor_config"]` 中的选择器映射为 `TaskConfig.extractors`（`ExtractorConfig`），由 `TaskExecutor` 构建对应的 `LinkExtractor` 和 `DataExtractor` 实例。  
`Line.item_limit` 映射为 `TaskConfig.max_items`；`Line.meta` 中除 `extractor_config` 外的字段进入 `TaskConfig.params`。

## 测试目录

`tests/` 下按 **`SourceType`** 分子目录（与 `SourceType` 枚举一致），便于按数据源类型扩展用例：

| 目录 | 说明 |
|------|------|
| `tests/core/` | 不依赖具体类型的逻辑（Extractor、管线、TaskExecutor、Density、CrawlerConfig 等） |
| `tests/website/` | `WEBSITE` 预设与相关 Source / 配置 |
| `tests/api/` | `API` 预设与相关 Source / 配置 |
| `tests/file/`、`stream/`、`external/` | 预留，与 `FILE` / `STREAM` / `EXTERNAL` 对齐 |

共享 fixtures 仍在 `tests/conftest.py`，桩实现见 `tests/stubs.py`（含 `StubDownloader` 和 `MappedStubDownloader`）。

### 核心测试文件

| 文件 | 覆盖场景 |
|------|----------|
| `test_link_extractor.py` | CSS 选择器、相对/绝对 URL、去重、异常处理 |
| `test_data_extractor.py` | 标题/时间/正文选择器、回退策略、空页面 |
| `test_extractor_config.py` | 配置模型验证、`has_data_selectors` |
| `test_task_pipeline.py` | 单级/多级链接管线、去重、max_items、注入式提取器 |
| `test_density.py` | 信息密度检测：链接模式、标题/时间/正文选择器 |
| `test_task_executor.py` | 基础执行：无 URL、下载+提取、max_items、错误处理 |
| `test_task_config_from_line.py` | Line → TaskConfig 映射、extractor_config 消费 |

## 开发

要求 **Python ≥ 3.13**。

```bash
cd ingestor/crawler
uv sync --group dev
uv run pytest
```

## 依赖

`pydantic`、`httpx`、`click`、`rich`、`beautifulsoup4`（详见 `pyproject.toml`）。
