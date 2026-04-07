#!/bin/sh
# 启动 admin 前端（admin/compose.yaml）
# 默认通过宿主机端口访问 ingestor：ADMIN_BUILD_BACKEND_URL=http://host.docker.internal:端口
# 用法：./scripts/deploy-admin.sh [docker compose 额外参数]

set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ADMIN_BUILD_BACKEND_URL="${ADMIN_BUILD_BACKEND_URL:-http://host.docker.internal:${SERVER_PORT:-8000}}"
export ADMIN_BUILD_BACKEND_URL

exec docker compose -f admin/compose.yaml up -d --build "$@"
