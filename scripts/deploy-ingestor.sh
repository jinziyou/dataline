#!/bin/sh
# 启动 PostgreSQL + ingestor API（ingestor/compose.yaml）
# 用法：在仓库根目录 ./scripts/deploy-ingestor.sh [docker compose 额外参数，如 --build]

set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

exec docker compose -f ingestor/compose.yaml up -d "$@"
