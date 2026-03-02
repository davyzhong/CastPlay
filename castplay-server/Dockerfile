# CastPlay Backend Dockerfile
# 生产就绪版本 - 安全优化

FROM python:3.11-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 创建非 root 用户
RUN groupadd -r castplay && useradd -r -g castplay castplay

WORKDIR /app

# 复制依赖文件（利用 Docker 层缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn gevent

# 复制应用代码
COPY --chown=castplay:castplay . .

# 创建存储目录并设置权限
RUN mkdir -p storage/uploads storage/converted storage/thumbnails instance \
    && chown -R castplay:castplay storage instance

# 设置环境变量
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 切换到非 root 用户
USER castplay

# 暴露端口
EXPOSE 5001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

# 使用 gunicorn 运行
CMD ["python", "-m", "gunicorn", "--worker-class", "gevent", "-w", "2", "-b", "0.0.0.0:5001", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "run:app"]
