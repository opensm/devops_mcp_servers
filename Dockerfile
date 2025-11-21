FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=devops_mcp_servers.settings
WORKDIR /app

RUN sed -i 's@deb.debian.org@mirrors.aliyun.com@g; s@security.debian.org@mirrors.aliyun.com@g' /etc/apt/sources.list && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* \

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ===== 新增：构建时生成迁移文件 =====
RUN python manage.py makemigrations

# 非 root 用户
RUN groupadd -r app && useradd -r -g app -d /home/app -s /sbin/nologin app
RUN chown -R app:app /app
USER app

EXPOSE 8000
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]