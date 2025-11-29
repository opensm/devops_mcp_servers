#FROM python:3.11-slim
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=devops_mcp_servers.settings
WORKDIR /app

RUN <<EOF
cat > /etc/apt/sources.list.d/debian.sources <<'DEB'
Types: deb
URIs: https://mirrors.aliyun.com/debian
Suites: bookworm bookworm-updates bookworm-backports
Components: main contrib non-free
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg

Types: deb
URIs: https://mirrors.aliyun.com/debian-security
Suites: bookworm-security
Components: main contrib non-free
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
DEB
EOF

RUN apt-get clean && rm -rf /var/lib/apt/lists/* && apt-get update && apt-get install -y default-libmysqlclient-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple && rm -f requirements.txt

COPY . .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && mv devops_mcp_servers/settings_prod.py devops_mcp_servers/settings.py
# ===== 新增：构建时生成迁移文件 =====
RUN python manage.py makemigrations

# 非 root 用户
RUN groupadd -r app && useradd -r -g app -d /home/app -s /sbin/nologin app
RUN chown -R app:app /app
USER app

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]