# Tasks

- [ ] Task 1: 初始化 admin 前端项目骨架
  - [ ] 使用 pnpm 创建 Next.js 应用（App Router + TypeScript）
  - [ ] 集成 Tailwind CSS 并配置 shadcn/ui 组件库
  - [ ] 建立基础页面布局与导航结构（配置管理、采集结果、日志展示）
  - [ ] 建立 API 客户端层（封装对 server API 的调用），预留类型定义
  - [ ] 配置开发环境（环境变量、代理配置指向 server）

- [ ] Task 2: 初始化 ingestor workspace 与 crawler 领域模型
  - [ ] 使用 uv init 创建 ingestor workspace 级 pyproject.toml
  - [ ] 使用 uv init --lib crawler 创建 crawler 库模块
  - [ ] 定义 source、line、data 数据抽象模型（Pydantic/dataclass）
  - [ ] 定义 crawler、task 执行模型及其与数据抽象模型的映射关系
  - [ ] 建立预设配置结构，支持五大类数据源的配置模板
  - [ ] 实现根据 source、line 与预设参数自动生成 crawler/task 配置的基础逻辑

- [ ] Task 3: 实现 crawler 运行时上下文与执行管线
  - [ ] 实现 crawler 运行上下文容器（管理单个 source 级别的共享状态）
  - [ ] 实现 task 执行器（最小执行单元，处理单个 line 的数据获取）
  - [ ] 实现统一的 data 输出结构与结果收集机制
  - [ ] 预留去重策略扩展点（基于 URL/内容哈希等）
  - [ ] 预留下载器选择扩展点（HTTP 直连、Playwright 浏览器自动化等）
  - [ ] 预留会话管理与限流扩展点
  - [ ] 提供 crawler 的 Python 库调用入口（稳定 API）
  - [ ] 提供 crawler 的命令行入口（cli.py，支持加载配置并输出结果/状态）

- [ ] Task 4: 初始化 server 应用并建立管理与编排服务
  - [ ] 使用 uv init --app server 在 ingestor workspace 下创建 server 模块
  - [ ] 配置 FastAPI 应用骨架（路由、中间件、异常处理）
  - [ ] 集成 SQLModel 并配置 PostgreSQL 连接
  - [ ] 定义数据库模型：数据源配置、采集配置、采集结果、日志
  - [ ] 实现数据源配置 CRUD API
  - [ ] 实现采集结果与日志的查询 API
  - [ ] 集成 Prefect 实现 crawler 编排与调度
  - [ ] 实现任务执行状态管理与查询 API
  - [ ] 通过 workspace 内部依赖引用 crawler 库，实现采集调用

- [ ] Task 5: 建立 Docker 化部署与环境配置
  - [ ] 编写 admin Dockerfile（Node.js 多阶段构建）
  - [ ] 编写 server Dockerfile（Python 多阶段构建，包含 crawler 依赖）
  - [ ] 编写 docker-compose.yml 编排 admin、server、PostgreSQL 等服务
  - [ ] 建立 .env.example 环境变量模板（数据库连接、API 地址等）
  - [ ] 配置模块间网络连接与健康检查
  - [ ] 验证各模块可独立构建与启动

- [ ] Task 6: 完成端到端联调与基础验证
  - [ ] 验证 admin 可通过 server API 读取数据源配置列表
  - [ ] 验证 admin 可通过 server API 查看采集结果与日志
  - [ ] 验证 server 可通过 Prefect 编排触发 crawler 执行
  - [ ] 验证 crawler 可作为独立 CLI 工具运行采集任务
  - [ ] 验证统一领域模型可覆盖至少一种真实数据源接入场景（如公开网站）
  - [ ] 补充必要的单元测试与集成测试
  - [ ] 补充示例配置文件与快速启动说明

# Task Dependencies

```
Task 1 (admin 骨架)  ──────────────────────────┐
                                                │
Task 2 (领域模型) ──→ Task 3 (crawler 引擎)  ──┤──→ Task 5 (Docker) ──→ Task 6 (联调)
                  ──→ Task 4 (server 服务)   ──┘
```

- Task 1 可与 Task 2 并行启动（无依赖）
- Task 3 depends on Task 2（crawler 引擎依赖领域模型定义）
- Task 4 depends on Task 2（server 数据库模型需要与领域模型一致）
- Task 5 depends on Task 1, Task 3, and Task 4（容器化需要各模块就绪）
- Task 6 depends on Task 1, Task 3, Task 4, and Task 5（端到端验证需要全部就绪）
