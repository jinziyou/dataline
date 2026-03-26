# 多源异类数据采集汇聚系统基础架构 Spec

## Why
当前仓库仅描述了目标系统的分层与技术选型，但尚未形成可执行、可验证的统一规格。
需要先明确各子系统职责、核心数据抽象、部署边界与协作方式，才能支撑后续按模块落地开发。

## What Changes
- 定义 admin 与 ingestor 两大项目的职责边界与协作关系
- 定义 ingestor 作为 uv workspace 的内部结构：crawler 模块（库）与 server 模块（应用）
- 定义 source -> line -> data 与 crawler -> task -> data 两套核心领域模型及映射规则
- 定义基于配置和数据驱动的统一接入能力，覆盖五大类数据源
- 定义 crawler 模块的库与命令行双重调用方式
- 定义 server 对配置、结果、日志与编排的统一管理能力，以及对 admin 提供 API 的职责
- 定义基于 Docker 的整体部署约束与模块解耦原则
- 定义各子项目的技术栈与项目目录结构

## Impact
- Affected specs: admin 可视化管理、ingestor 采集核心（crawler + server）、Docker 部署
- Affected code: admin 前端工程、ingestor workspace（crawler 库与 CLI、server FastAPI 应用）、共享配置与部署清单

---

## 系统总览

### 项目结构

```
dataline/                         # 仓库根目录
├── admin/                        # 前端管理项目（Next.js）
│   ├── package.json              # pnpm 管理
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── components.json           # shadcn/ui 配置
│   ├── src/
│   │   ├── app/                  # Next.js App Router 页面
│   │   ├── components/           # UI 组件（含 shadcn 组件）
│   │   ├── lib/                  # 工具函数与 API 客户端
│   │   └── types/                # TypeScript 类型定义
│   └── public/
├── ingestor/                     # 数据采集核心项目（uv workspace）
│   ├── pyproject.toml            # workspace 级配置
│   ├── crawler/                  # 采集引擎库模块（uv init --lib crawler）
│   │   ├── pyproject.toml
│   │   └── src/
│   │       └── crawler/
│   │           ├── __init__.py
│   │           ├── models/       # source, line, data, crawler, task 领域模型
│   │           ├── engine/       # crawler 运行时与 task 执行引擎
│   │           ├── downloaders/  # 下载器实现（HTTP、Playwright 等）
│   │           ├── config/       # 预设配置与配置生成
│   │           └── cli.py        # 命令行入口
│   └── server/                   # 管理与编排服务（uv init --app server）
│       ├── pyproject.toml
│       └── src/
│           └── server/
│               ├── __init__.py
│               ├── api/          # FastAPI 路由
│               ├── models/       # SQLModel 数据库模型
│               ├── services/     # 业务逻辑与 crawler 编排
│               ├── schemas/      # Pydantic 请求/响应 schema
│               └── core/         # 配置、依赖注入、日志
├── docker-compose.yml            # 容器编排
├── .env.example                  # 环境变量模板
└── README.md
```

### 技术栈

| 子项目 | 技术栈 | 初始化方式 |
|--------|--------|------------|
| admin | pnpm + Next.js + shadcn/ui + Tailwind CSS + TypeScript | pnpm create next-app |
| ingestor (workspace) | uv + Python | uv init (workspace) |
| ingestor/crawler | Python（库 + CLI） | uv init --lib crawler |
| ingestor/server | uv + Python + FastAPI + Prefect + SQLModel + PostgreSQL | uv init --app server |

### 架构层级

系统采用 **admin + ingestor** 两大项目、**功能分离** 架构：

```
┌──────────────────────────────────────────────────────────┐
│                        admin                             │
│          Next.js 可视化管理前端                            │
│   (配置管理 / 采集结果展示 / 日志查看)                      │
└──────────────────┬───────────────────────────────────────┘
                   │ HTTP API
┌──────────────────▼───────────────────────────────────────┐
│                  ingestor (uv workspace)                 │
│  ┌────────────────────────┐  ┌────────────────────────┐  │
│  │       server            │  │       crawler          │  │
│  │  FastAPI + Prefect      │  │  采集引擎库 + CLI      │  │
│  │  + SQLModel + PostgreSQL│  │  source->line->data    │  │
│  │                         │  │  crawler->task->data   │  │
│  │  · 配置管理              │  │                        │  │
│  │  · 采集结果管理          │  │  · 单源采集执行         │  │
│  │  · 日志管理              │  │  · 上下文与去重管理     │  │
│  │  · crawler 编排         │  │  · 下载器策略           │  │
│  │  · 对外 API             │  │  · 配置驱动生成         │  │
│  └───────────┬────────────┘  └────────────▲───────────┘  │
│              │          调用（库接口）       │              │
│              └──────────────────────────────┘              │
└──────────────────────────────────────────────────────────┘
```

- **admin**：纯前端项目，仅通过 server API 获取和提交数据，不直接调用 crawler。
- **ingestor**：uv workspace，包含 crawler（库模块）和 server（应用模块）两个子包。
  - **crawler**：数据采集引擎核心，以库或 CLI 方式对外提供采集能力。
  - **server**：管理与编排后端，依赖 crawler 库完成采集调度，并对 admin 暴露 API。

---

## 核心领域模型

### 数据抽象模型：source -> line -> data

将多源异类数据统一抽象为三层结构：

| 概念 | 含义 | 示例（公开网站） |
|------|------|-----------------|
| **source** | 一个数据源整体 | 某个网站 |
| **line** | 数据源下的一条数据通道/导航路径 | 网站的一个导航页/栏目 |
| **data** | 通道下的具体数据条目 | 导航页下某个链接对应的资源数据 |

关系：一个 source 包含多个 line，一个 line 包含多条 data 链接。
source 和 line 需要事先给定（由用户或预设配置提供）。

### 执行模型：crawler -> task -> data

将数据采集过程抽象为三层执行结构，与数据抽象模型一一映射：

| 执行概念 | 映射 | 职责 |
|----------|------|------|
| **crawler** | 对应 source | 数据获取的实际运行容器，管理单个数据源的所有爬取上下文（去重、会话、下载器选择、限流） |
| **task** | 对应 line | 数据获取的最小执行单元，负责获取单个 line 下的多条数据 |
| **data** | 对应 data | 采集输出的统一数据结构 |

关系：一个 crawler 包含多个 task，与一个 source 对应多个 line 相同。

### 模型映射规则

```
source  ←1:1→  crawler     (一个数据源对应一个采集运行容器)
  │                │
  ├── line₁ ←1:1→ task₁    (一条数据通道对应一个采集任务)
  ├── line₂ ←1:1→ task₂
  └── lineₙ ←1:1→ taskₙ
       │              │
       └── data[] ←→ data[]  (采集输出统一数据结构)
```

系统根据已给定的 source 和 line，加上配置参数，自动生成对应的 crawler 和 task 配置。

---

## 数据源分类

系统基于配置和数据驱动（为了可用性，系统会尽可能预设配置），实现对以下五大类数据源的统一接入：

| 分类 | 说明 | 典型场景 |
|------|------|---------|
| **公开网站和网络资源** | 可公开访问的网页、文档、媒体资源 | 新闻站点、政府公开数据、论坛 |
| **API 接口和订阅服务** | RESTful/GraphQL API、RSS/Atom、Webhook | 第三方数据平台 API、RSS 订阅源 |
| **文件和存储系统** | 本地或远程文件系统、对象存储、FTP | CSV/JSON/XML 文件、S3 存储桶、FTP 站点 |
| **消息与流数据** | 消息队列、实时流、WebSocket | Kafka 消费、WebSocket 实时推送 |
| **外部结构和第三方系统** | 数据库、SaaS 平台、遗留系统 | 外部数据库同步、SaaS 数据导出 |

每种数据源类型均可映射到 source -> line -> data 模型。系统应为常见数据源类型提供预设配置模板，降低接入成本。

---

## ADDED Requirements

### Requirement: 系统架构与模块划分
系统 SHALL 采用 admin（前端）+ ingestor（后端 workspace，含 crawler 与 server 两个模块）的功能分离架构。

#### Scenario: admin 与 server 的协作边界
- **WHEN** 管理员在 admin 中查看或管理采集配置、结果或日志
- **THEN** admin 仅通过 server 暴露的 HTTP API 获取或提交数据
- **THEN** admin 不直接调用 crawler 执行逻辑或访问数据库

#### Scenario: server 与 crawler 的协作边界
- **WHEN** server 需要触发采集任务
- **THEN** server 通过 crawler 的 Python 库接口调用采集能力
- **THEN** server 负责编排和调度，crawler 负责实际采集执行
- **THEN** crawler 不直接处理 HTTP 请求或管理持久化存储

#### Scenario: 采集引擎独立运行
- **WHEN** 其它程序需要以库或命令行方式触发单个数据源采集
- **THEN** crawler 可在不依赖 admin 和 server 的前提下独立运行
- **THEN** server 依赖 crawler 库但 crawler 不反向依赖 server

### Requirement: 统一数据抽象模型
系统 SHALL 将多源异类数据统一抽象为 source -> line -> data 模型，并以 crawler -> task -> data 作为执行模型。

#### Scenario: 资源结构映射为统一模型
- **WHEN** 接入一个公开网站、API、文件系统或消息流数据源
- **THEN** 系统必须先确定 source 与一个或多个 line
- **THEN** 每个 line 可映射出多条待采集的数据链接或数据入口
- **THEN** 最终采集结果以统一 data 结构输出，供后续处理与展示

#### Scenario: 执行模型映射到领域模型
- **WHEN** 系统根据 source 与 line 生成采集配置
- **THEN** 一个 source 对应一个 crawler 运行上下文
- **THEN** 一个 crawler 可包含多个 task
- **THEN** 每个 task 与单个 line 对应，并负责获取该 line 下的多条数据

#### Scenario: 模型在不同数据源类型下的一致性
- **WHEN** 分别接入公开网站与 API 接口两种不同类型的数据源
- **THEN** 两者均须映射到相同的 source -> line -> data 结构
- **THEN** 执行层均通过 crawler -> task -> data 完成采集
- **THEN** 数据输出格式保持一致，与数据源类型无关

### Requirement: 配置驱动的采集配置生成
系统 SHALL 基于预设配置与输入元数据自动生成采集执行配置，以降低接入成本并提升可用性。

#### Scenario: 使用预设生成采集配置
- **WHEN** 用户登记新的数据源并提供必要参数（如数据源地址、类型）
- **THEN** 系统优先使用内置预设补齐通用配置（如请求头、超时、重试策略）
- **THEN** 系统自动生成 crawler 级与 task 级配置
- **THEN** 用户只需补充无法推断的最小必要参数

#### Scenario: 预设配置覆盖五大类数据源
- **WHEN** 系统需要接入不同类型的数据源
- **THEN** 应为公开网站、API 接口、文件系统、消息流、外部系统分别提供预设配置模板
- **THEN** 每种预设模板应包含该类数据源的典型采集参数与默认值

### Requirement: crawler 运行上下文管理
系统 SHALL 由 crawler 统一管理单个数据源采集过程中的上下文、去重与下载器策略。

#### Scenario: 采集过程共享上下文
- **WHEN** 同一 source 下存在多个 line 需要采集
- **THEN** 这些 line 对应的 task 共享同一个 crawler 运行上下文
- **THEN** crawler 可以统一执行去重、会话管理、限流与下载器选择
- **THEN** task 只负责最小执行单元的采集逻辑

#### Scenario: 选择执行下载器
- **WHEN** 某个数据源需要浏览器自动化或其它特定下载方式
- **THEN** crawler 可根据配置选择 Playwright 等下载器
- **THEN** task 无需感知下载器实现细节

### Requirement: ingestor 项目结构与交付形态
ingestor SHALL 采用 uv workspace 管理，包含 crawler（uv init --lib）和 server（uv init --app）两个模块。crawler 支持库调用和命令行调用两种交付形态。

#### Scenario: 作为库被调用
- **WHEN** server 或其它 Python 程序需要复用采集能力
- **THEN** crawler 提供稳定的 Python 库接口
- **THEN** 调用方可按 source 或 crawler 配置触发采集流程

#### Scenario: 作为命令行工具被调用
- **WHEN** 运维或开发者需要单独执行某个采集任务
- **THEN** crawler 提供明确的命令行入口
- **THEN** 命令行入口支持加载配置并输出采集结果或执行状态

#### Scenario: ingestor workspace 内部依赖
- **WHEN** server 需要调用采集能力
- **THEN** server 通过 workspace 内部依赖引用 crawler 库
- **THEN** crawler 不依赖 server，保持库的独立性

### Requirement: server 编排与管理能力
server SHALL 提供配置管理、结果管理、日志管理、crawler 编排与对外 API 能力。

#### Scenario: 管理采集生命周期
- **WHEN** 管理员创建、修改或停用数据源与采集配置
- **THEN** server 负责持久化相关配置到 PostgreSQL
- **THEN** server 负责记录采集结果与日志
- **THEN** server 通过 Prefect 调度或编排多个 crawler 的执行

#### Scenario: 对 admin 暴露统一接口
- **WHEN** admin 需要展示配置、结果、日志或任务状态
- **THEN** server 通过 FastAPI 提供统一 RESTful API
- **THEN** API 返回的数据结构应与统一领域模型保持一致或可映射

### Requirement: Docker 部署与模块隔离
系统 SHALL 以 Docker 为标准部署方式，并保持各模块可独立构建、部署与扩缩容。

#### Scenario: 独立部署模块
- **WHEN** 系统在开发、测试或生产环境中部署
- **THEN** admin、server 与采集执行组件（含 Playwright 等依赖）应支持独立容器化
- **THEN** 各模块通过环境变量与配置文件连接，而非硬编码依赖彼此运行环境
- **THEN** 使用 docker-compose 统一编排各容器与 PostgreSQL 等基础设施

#### Scenario: 按负载扩展采集能力
- **WHEN** 某类数据源采集需求增长
- **THEN** 系统可单独扩展 server 编排能力或 crawler 执行能力
- **THEN** 不要求同步扩展 admin 前端服务
