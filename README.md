多源异类数据采集汇聚系统，系统采用docker部署和功能分离架构，现系统分层如下：​admin项目(nextjs项目)基于pnpm+Next.js+shadcn+tailwindcss等技术栈，用于可视化展示和管理采集配置、采集结果和日志等信息；ingestor​项目提供多源异类数据采集汇聚核心功能，项目可细分为两个模块（采用uv workspace）：​crawler模块（uv init --lib crawler）实现对单个资源（地址或域名）进行自动化采集,将多源异类数据统一抽象为source->line->data模型(如公开网站对应于网站->导航页->某个链接对应的资源数据)，将数据爬取抽象crawler->task->data，source和line需要事先给定,然后根据配置的参数，自动生成爬取配置（source和crawler对应，task和line对应，跟一个source对应多个line相同，一个crawler也对应多个task，一个line包含多条数据链接，一个task也会获取多条数据），crawler为数据获取的实际运行容器，管理着单个数据源所有爬取上下文（用于去重、指定下载器如playWright等），task为数据获取的最小执行单元，项目对外以命令行工具或者以库的方式提供给其它程序调用;​server项目（uv init --app server）基于uv+python+fastapi+prefect+sqlmodel+postgre技术栈，主要用于管理数据源相关配置、爬取的配置和结果、日志信息和编排多个crawler，并对外提供api给admin项目调用。系统基于配置和数据驱动（为了可用性，系统会尽可能预设配置），实现对多源异类数据源（如公开网站和网络资源、api接口和订阅服务、文件和存储系统、消息与流数据、外部结构和第三方系统）的统一接入。

## 快速开始

### Docker 部署（推荐）

```bash
cp .env.example .env
docker compose up -d
```

启动后访问：
- admin 前端：http://localhost:3000
- server API 文档：http://localhost:8000/docs

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
