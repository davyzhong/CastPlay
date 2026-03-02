# CastPlay Admin Frontend Dockerfile
# 生产就绪版本 - 多阶段构建优化

# Build stage
FROM node:18-alpine AS builder

# 构建参数
ARG VITE_API_BASE_URL=http://localhost:5001/api
ARG VITE_WS_URL=ws://localhost:5001

# 设置为环境变量供构建使用
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_WS_URL=${VITE_WS_URL}

WORKDIR /app

# 复制 package 文件
COPY package*.json ./

# 安装依赖（使用 ci 保证依赖版本一致）
RUN npm ci --only=production=false

# 复制源代码
COPY . .

# 构建生产版本
RUN npm run build

# Production stage
FROM nginx:alpine

# 安装 wget 用于健康检查
RUN apk add --no-cache wget

# 创建非 root 用户
RUN addgroup -g 1001 -S nginx-user && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G nginx-user nginx-user

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 设置目录权限
RUN chown -R nginx-user:nginx-user /usr/share/nginx/html && \
    chown -R nginx-user:nginx-user /var/cache/nginx && \
    touch /var/run/nginx.pid && \
    chown -R nginx-user:nginx-user /var/run/nginx.pid

EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:80 || exit 1

CMD ["nginx", "-g", "daemon off;"]
