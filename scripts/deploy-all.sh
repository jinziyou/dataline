#!/bin/sh
# 依次部署 ingestor 再部署 admin
# admin 通过 host.docker.internal 访问宿主机上映射的 API 端口（ingestor 中 SERVER_PORT）

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

"$SCRIPT_DIR/deploy-ingestor.sh" "$@"

ADMIN_BUILD_BACKEND_URL="${ADMIN_BUILD_BACKEND_URL:-http://host.docker.internal:${SERVER_PORT:-8000}}"
export ADMIN_BUILD_BACKEND_URL

"$SCRIPT_DIR/deploy-admin.sh"
