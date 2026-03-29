多源异类数据采集汇聚系统，系统采用docker部署和功能分离架构，现系统分层如下：​admin项目(nextjs项目)基于pnpm+Next.js+shadcn+tailwindcss等技术栈，用于可视化展示和管理采集配置、采集结果和日志等信息；ingestor​项目提供多源异类数据采集汇聚核心功能，项目可细分为两个模块（采用uv workspace）：​crawler模块（uv init --lib crawler）实现对单个资源（地址或域名）进行自动化采集,将多源异类数据统一抽象为source->line->data模型(如公开网站对应于网站->导航页->某个链接对应的资源数据)，将数据爬取抽象crawler->task->data，source和line需要事先给定,然后根据配置的参数，自动生成爬取配置（source和crawler对应，task和line对应，跟一个source对应多个line相同，一个crawler也对应多个task，一个line包含多条数据链接，一个task也会获取多条数据），crawler为数据获取的实际运行容器，管理着单个数据源所有爬取上下文（用于去重、指定下载器如playWright等），task为数据获取的最小执行单元，项目对外以命令行工具或者以库的方式提供给其它程序调用;​server项目（uv init --app server）基于uv+python+fastapi+prefect+sqlmodel+postgre技术栈，主要用于管理数据源相关配置、爬取的配置和结果、日志信息和编排多个crawler，并对外提供api给admin项目调用。系统基于配置和数据驱动（为了可用性，系统会尽可能预设配置），实现对多源异类数据源（如公开网站和网络资源、api接口和订阅服务、文件和存储系统、消息与流数据、外部结构和第三方系统）的统一接入。

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
