# DataLine — 多源异类数据采集汇聚系统

> 配置驱动、统一接入、可视化管理的多源异类数据采集平台。

## 系统简介

DataLine 是一套面向**多源异类数据采集汇聚**的完整解决方案，采用 Docker 容器化部署与功能分离架构。系统基于**配置和数据驱动**（为了可用性，系统会尽可能预设配置），实现对五大类数据源的统一接入：

| 数据源类型 | 说明 | 示例场景 |
|-----------|------|---------|
| **公开网站** (website) | 网页、文档、媒体资源 | 新闻站采集、政务公开数据 |
| **API 接口** (api) | RESTful/GraphQL API、RSS/Atom、Webhook | 第三方数据订阅、开放数据 API |
| **文件系统** (file) | 本地/远程文件、对象存储、FTP | 文件批量采集、存储同步 |
| **消息流** (stream) | 消息队列、实时流、WebSocket | 实时数据接入、事件流采集 |
| **外部系统** (external) | 数据库、SaaS 平台、遗留系统 | 异构系统数据对接 |

## 系统架构

```
┌──────────────────────────────────────────────────────────────────────┐
│                        DataLine 系统架构                             │
├─────────────────────────┬────────────────────────────────────────────┤
│       admin (前端)       │              ingestor (后端)               │
│  Next.js + shadcn/ui    │                                            │
│  ┌───────────────────┐  │  ┌──────────────┐    ┌──────────────────┐  │
│  │ 控制台 (首页)      │  │  │   server     │    │    crawler       │  │
│  │ 数据源管理         │◄─┼─►│  FastAPI +   │───►│  采集引擎库      │  │
│  │ 采集结果           │  │  │  SQLModel +  │    │  Source→Line→Data│  │
│  │ 运行日志           │  │  │  Prefect     │    │  Crawler→Task    │  │
│  └───────────────────┘  │  └──────┬───────┘    │  →Extractor      │  │
│                         │         │            └──────────────────┘  │
│                         │  ┌──────▼───────┐                          │
│                         │  │  PostgreSQL  │                          │
│                         │  │  数据持久化   │                          │
│                         │  └──────────────┘                          │
└─────────────────────────┴────────────────────────────────────────────┘
```

### 项目结构

```
dataline/
├── admin/                    # 前端管理界面（Next.js 应用）
│   ├── src/
│   │   ├── app/              # 页面路由（首页、数据源、采集结果、日志）
│   │   ├── components/       # UI 组件（shadcn/ui + 自定义布局）
│   │   ├── lib/              # API 客户端、工具函数
│   │   └── types/            # TypeScript 类型定义
│   ├── compose.yaml          # admin Docker 编排
│   └── Dockerfile
├── ingestor/                 # 数据采集核心（uv workspace）
│   ├── crawler/              # 采集引擎库（Python 库 + CLI）
│   │   ├── src/crawler/
│   │   │   ├── source/       # Source 域：数据源建模、类型预设
│   │   │   ├── crawler/      # Crawler 域：执行容器、任务、提取器、下载器
│   │   │   └── cli.py        # 命令行入口
│   │   └── tests/            # 按 SourceType 分目录的测试套件
│   ├── server/               # 管理编排服务（FastAPI 应用）
│   │   └── src/server/
│   │       ├── api/          # REST API（sources、tasks、logs）
│   │       ├── models/       # 数据库模型（SQLModel）
│   │       ├── schemas/      # 请求/响应 Schema（Pydantic）
│   │       ├── services/     # 业务服务（Crawler 编排）
│   │       └── core/         # 配置、数据库连接
│   ├── compose.yaml          # ingestor Docker 编排（含 PostgreSQL）
│   └── Dockerfile
├── scripts/                  # 部署脚本（POSIX sh）
│   ├── deploy-all.sh         # 一键完整部署
│   ├── deploy-ingestor.sh    # 仅部署 ingestor
│   └── deploy-admin.sh       # 仅部署 admin
└── .env.example              # 环境变量模板
```

## 核心能力

### 1. 统一数据建模：Source → Line → Data

将多源异类数据统一抽象为三层模型：

| 层级 | 含义 | 示例 |
|------|------|------|
| **Source** | 一个数据源整体 | 某新闻站、某 API 服务 |
| **Line** | 源下的一条采集通道 | 某栏目入口 URL、某 API 路径 |
| **Data** | 通道下的一条具体数据 | 某页正文、某条记录 |

`Source` 必须带至少一条 `Line`。若构造时未传 `lines`，会自动创建**默认 Line**（`url` 与 `Source.url` 一致）。

### 2. 执行引擎：Crawler → Task → Extractor

| 层级 | 含义 |
|------|------|
| **Crawler** | 单次采集运行容器：共享去重、下载器、限流、并发 |
| **Task** | 最小执行单元，对应一条 `Line` |
| **Extractor** | 数据提取器，跟 Line 中数据层级对应 |

#### 提取管线（Pipeline）

```
列表页 URL ──LinkExtractor──→ 详情页 URL 列表 ──DataExtractor──→ Data[]
                                      ↑
                              可多级串联（分类页→子列表→详情页）
```

| 提取器 | 职责 | 输入 → 输出 |
|--------|------|-------------|
| **LinkExtractor** | 从列表/导航页提取下一级 URL | `DownloadResponse` → `list[str]` |
| **DataExtractor** | 从详情页提取结构化数据 | `DownloadResponse` → `list[Data]` |
| **PageExtractor** | 整页提取器（无选择器时回退） | `DownloadResponse` → `list[Data]` |

### 3. 信息密度自动检测

`DensityBasedDetector` 通过分析页面 HTML 结构自动推导 CSS 选择器，无需手动编写：

- **列表页检测**：自动发现链接选择器（如 `.news-list a[href]`）
- **详情页检测**：自动推导标题、时间、正文选择器

### 4. 配置驱动与多级预设

系统为每种数据源类型预设了推荐采集参数（下载器、并发数、超时、限速、重试策略等），用户只需提供数据源 URL 即可开始采集。

**参数合并优先级（从低到高）：**
类型预设 → `Source.meta` 中的引擎默认项 → 本次 `options` → 本次 `overrides`

### 5. 运行时能力

- **URL 去重**：基于 MD5 哈希的自动去重，避免重复采集
- **令牌桶限流**：可配置请求速率限制，保护目标站点
- **并发控制**：信号量限制并发请求数
- **重试策略**：可配置最大重试次数与间隔
- **多种下载器**：HTTP（默认）/ Playwright（动态渲染页面支持）

### 6. REST API 服务

Server 基于 FastAPI 对外提供完整 REST API：

| 模块 | 端点 | 功能 |
|------|------|------|
| **数据源** | `GET/POST/PATCH/DELETE /api/sources` | 数据源 CRUD |
| **数据通道** | `GET/POST/PATCH/DELETE /api/sources/{id}/lines` | Line CRUD |
| **采集任务** | `POST /api/tasks` | 触发采集任务 |
| **任务查询** | `GET /api/tasks` | 查询任务列表（支持按数据源、状态筛选） |
| **采集数据** | `GET /api/tasks/{id}/data` | 获取某任务的采集结果 |
| **运行日志** | `GET /api/logs` | 查询采集日志（支持按任务、数据源、级别筛选） |
| **健康检查** | `GET /health` | 服务健康状态 |

### 7. 可视化管理后台

Admin 前端提供直观的 Web 管理界面：

- **控制台首页**：系统概览与快捷导航
- **数据源管理**：数据源列表展示（名称、类型、地址、启用状态），支持新增数据源
- **采集结果**：任务列表（ID、数据源、状态、采集统计、时间），实时状态展示
- **运行日志**：日志查看（级别、消息、关联任务与数据源、时间）

### 8. 命令行工具

Crawler 提供独立 CLI，可脱离 Server 直接使用：

```bash
crawler run --source-url https://example.com       # 快捷采集
crawler run --config crawl.json                     # 从配置文件采集
crawler run --source-url https://example.com -o result.json  # 结果输出到文件
crawler presets                                     # 查看类型预设
crawler show --config crawl.json                    # 查看配置详情
```

### 9. 库级调用

Crawler 同时提供 Python 库接口，可嵌入其他应用：

```python
from crawler import Crawler, Source, SourceType

source = Source(id="my-site", name="示例站", type=SourceType.WEBSITE, url="https://example.com")
result = await Crawler.run_source(source)
```

## 技术栈

| 组件 | 技术 |
|------|------|
| **前端** | Next.js 16 + React 19 + shadcn/ui + Tailwind CSS 4 + TypeScript |
| **后端 API** | Python 3.13+ + FastAPI + SQLModel + Pydantic |
| **采集引擎** | httpx + BeautifulSoup4 + Playwright（可选） |
| **任务编排** | Prefect |
| **数据库** | PostgreSQL 17 |
| **包管理** | uv（Python workspace）+ pnpm（前端） |
| **部署** | Docker Compose |

## 快速开始

### Docker 部署（推荐）

编排文件位于各子项目内：`ingestor/compose.yaml`、`admin/compose.yaml`。仓库根目录 **不再提供** 合并用的 `docker-compose.yml`，请用脚本或直接 `docker compose -f` 部署。

**一键完整栈（ingestor + admin + PostgreSQL）：**

```bash
cp .env.example .env   # 可选：按需编辑端口与密码
./scripts/deploy-all.sh
```

或手动两步：

```bash
./scripts/deploy-ingestor.sh
./scripts/deploy-admin.sh
```

启动后访问：
- admin 前端：http://localhost:3000
- server API 文档：http://localhost:8000/docs

`deploy-all.sh` / `deploy-admin.sh` 默认令 admin 构建时访问 `http://host.docker.internal:${SERVER_PORT:-8000}`（ingestor 需已把 API 映射到宿主机端口；`admin/compose.yaml` 已配置 `extra_hosts`）。

**分开部署：**

1. **仅 ingestor**
   ```bash
   ./scripts/deploy-ingestor.sh
   # 或：docker compose -f ingestor/compose.yaml up -d
   # 或在 ingestor/ 目录：docker compose up -d
   ```

2. **仅 admin**（构建期需能访问 ingestor API）
   ```bash
   ./scripts/deploy-admin.sh
   # 或：ADMIN_BUILD_BACKEND_URL=https://api.example.com docker compose -f admin/compose.yaml up -d --build
   ```

admin 镜像在 **构建阶段** 读取 `BACKEND_URL`（`admin/Dockerfile` 的 `ARG`），与 `next.config.ts` 中 `/api` 反代一致；**更换 API 地址后需重新 build admin**。

脚本为 **POSIX sh**（`#!/bin/sh`，`set -eu`），在**仓库根目录**执行：`sh scripts/deploy-all.sh` 或 `./scripts/deploy-all.sh`（后者需 `chmod +x scripts/*.sh`）。仓库已用 `.gitattributes` 要求 `*.sh` 使用 **LF**；若在 Windows 编辑后仍出现 `set: Illegal option` 或 `: not found`，多为 **CRLF 行尾**，可执行 `sed -i 's/\r$//' scripts/*.sh` 修复。

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `POSTGRES_USER` | `dataline` | PostgreSQL 用户名 |
| `POSTGRES_PASSWORD` | `dataline` | PostgreSQL 密码 |
| `POSTGRES_DB` | `dataline` | 数据库名称 |
| `POSTGRES_PORT` | `5432` | PostgreSQL 端口 |
| `SERVER_PORT` | `8000` | Server API 端口 |
| `ADMIN_PORT` | `3000` | Admin 前端端口 |
| `DATALINE_CORS_ORIGINS` | `["http://localhost:3000"]` | CORS 允许来源 |
| `ADMIN_BUILD_BACKEND_URL` | `http://host.docker.internal:8000` | Admin 构建期 API 地址 |

### 本地开发

**ingestor（crawler + server）：**

```bash
cd ingestor
uv sync --all-packages

# 使用 crawler CLI
uv run crawler presets          # 查看预设配置
uv run crawler run --source-url https://example.com  # 快捷采集

# 启动 server（需要 PostgreSQL）
uv run fastapi dev server/src/server/main.py
```

**admin 前端：**

```bash
cd admin
pnpm install
pnpm dev
```

### 运行测试

```bash
cd ingestor/crawler
uv sync --group dev
uv run pytest
```

测试按 `SourceType` 分目录组织（`tests/core/`、`tests/website/`、`tests/api/`、`tests/file/`、`tests/stream/`、`tests/external/`），采用 TDD 开发模式，覆盖提取器、管线、密度检测、任务执行等核心场景。
