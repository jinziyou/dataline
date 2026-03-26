# 验收 Checklist

## 项目结构与初始化

* [ ] 仓库根目录包含 admin/ 和 ingestor/ 两个顶层项目目录
* [ ] admin 项目使用 pnpm 管理，包含 Next.js + TypeScript + Tailwind CSS + shadcn/ui 完整配置
* [ ] ingestor 项目使用 uv workspace 管理，根目录 pyproject.toml 声明 workspace members
* [ ] ingestor/crawler 以 uv init --lib 方式创建，具备独立 pyproject.toml
* [ ] ingestor/server 以 uv init --app 方式创建，具备独立 pyproject.toml
* [ ] server 的 pyproject.toml 中通过 workspace 依赖引用 crawler 库

## 领域模型

* [ ] source、line、data 数据抽象模型已在 crawler 模块中定义（含类型、字段、关系）
* [ ] crawler、task 执行模型已在 crawler 模块中定义，并与 source、line 建立一一映射
* [ ] 模型定义可覆盖五大类数据源（公开网站、API 接口、文件系统、消息流、外部系统）
* [ ] 模型包含必要的元数据字段（如数据源类型、状态、时间戳等）

## 配置驱动

* [ ] 系统能够根据 source、line 与预设参数自动生成 crawler/task 配置
* [ ] 为常见数据源类型提供预设配置模板（至少覆盖公开网站类型）
* [ ] 预设配置包含典型默认值（请求头、超时、重试策略等）
* [ ] 用户只需提供最小必要参数即可完成数据源接入

## crawler 模块

* [ ] crawler 能为单个 source 管理共享运行上下文（跨 task 共享状态）
* [ ] task 作为最小执行单元，负责单个 line 的数据获取
* [ ] 采集结果以统一 data 结构输出
* [ ] 预留去重策略扩展点（接口已定义，可后续实现）
* [ ] 预留下载器选择扩展点（支持 HTTP 直连，预留 Playwright 等接口）
* [ ] 预留会话管理与限流扩展点
* [ ] 提供稳定的 Python 库调用入口（可 import 使用）
* [ ] 提供命令行入口（可通过 CLI 执行采集任务）

## server 模块

* [ ] FastAPI 应用正常启动并提供 API 文档（/docs）
* [ ] SQLModel 数据库模型与 PostgreSQL 连接正常
* [ ] 提供数据源配置的 CRUD API
* [ ] 提供采集结果的查询 API
* [ ] 提供日志信息的查询 API
* [ ] 集成 Prefect 实现 crawler 编排与调度
* [ ] 提供任务执行状态的查询 API
* [ ] server 通过 crawler 库接口调用采集能力（非子进程/RPC 方式）

## admin 前端

* [ ] Next.js 应用正常启动并可访问
* [ ] 包含基础页面：配置管理、采集结果展示、日志查看
* [ ] 页面导航结构完整可用
* [ ] 通过 API 客户端层调用 server API（不直接访问数据库或 crawler）
* [ ] API 返回数据可正常展示在页面上

## Docker 部署

* [ ] admin 具备独立 Dockerfile，可单独构建镜像
* [ ] server 具备独立 Dockerfile（包含 crawler 依赖），可单独构建镜像
* [ ] docker-compose.yml 可一键启动完整系统（admin + server + PostgreSQL）
* [ ] 提供 .env.example 环境变量模板
* [ ] 各模块通过环境变量与配置文件连接，无硬编码依赖
* [ ] 各容器可独立构建、启动与停止

## 端到端验证

* [ ] admin 可通过 server API 读取并展示数据源配置列表
* [ ] admin 可通过 server API 查看采集结果与日志
* [ ] server 可触发并跟踪 crawler 执行状态
* [ ] crawler 可作为独立 CLI 工具执行采集任务
* [ ] 至少一个真实数据源（如公开网站）完成端到端采集验证
* [ ] 补充必要的测试覆盖（单元测试 + 集成测试）
