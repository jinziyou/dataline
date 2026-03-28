#!/usr/bin/env bash
# 依次部署 ingestor 再部署 admin（等同原根目录一键 compose）
# admin 通过 host.docker.internal 访问已映射到宿主机的 API 端口（见 ingestor compose 中 SERVER_PORT）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"$SCRIPT_DIR/deploy-ingestor.sh" "$@"

: "${ADMIN_BUILD_BACKEND_URL:=http://host.docker.internal:${SERVER_PORT:-8000}}"
export ADMIN_BUILD_BACKEND_URL

"$SCRIPT_DIR/deploy-admin.sh"
