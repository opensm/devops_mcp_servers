#!/usr/bin/env bash
set -euo pipefail

PORT=${PORT:-8000}
WORKERS=${WORKERS:-2}
BIND=${BIND:-"0.0.0.0:$PORT"}
MODULE=${MODULE:-"devops_mcp_servers.wsgi:application"}

# 1. 等待 sqlite 文件所在目录可写（外挂卷可能延迟挂载）
if [[ ! -w "$(dirname "${SQLITE_PATH:-/data/db.sqlite3}")" ]]; then
    echo ">>> 等待卷挂载可写..."
    sleep 2
fi

# 2. 自动 migrate（sqlite 文件不存在时会自动创建）
echo ">>> 检查并执行 migrate..."
python manage.py migrate --noinput

# 3. 直接启动 gunicorn
echo ">>> 启动 gunicorn (${MODULE}) on ${BIND}"
exec gunicorn ${MODULE} \
    -w ${WORKERS} \
    -b ${BIND} \
    --access-logfile - \
    --error-logfile -