# CastPlay Backend Dockerfile
# FastAPI 生产就绪版本 - 异步高性能

FROM python:3.11-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 创建非 root 用户
RUN groupadd -r castplay && useradd -r -g castplay castplay

WORKDIR /app

# 复制依赖文件（利用 Docker 层缓存）
COPY requirements-fastapi.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY --chown=castplay:castplay . .

# 创建存储目录并设置权限
RUN mkdir -p storage/uploads storage/converted storage/thumbnails instance \
    && chown -R castplay:castplay storage instance

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production

# 切换到非 root 用户
USER castplay

# 暴露端口
EXPOSE 5001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

# 使用 uvicorn 运行 FastAPI (异步)
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5001", "--workers", "4"]
