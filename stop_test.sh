#!/bin/bash
# CastPlay 测试停止脚本

echo "停止 CastPlay 测试服务..."

# 停止后端
if [ -f /tmp/castplay_backend.pid ]; then
    BACKEND_PID=$(cat /tmp/castplay_backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID
        echo "✓ 后端服务已停止 (PID: $BACKEND_PID)"
    fi
    rm /tmp/castplay_backend.pid
fi

# 停止前端
if [ -f /tmp/castplay_frontend.pid ]; then
    FRONTEND_PID=$(cat /tmp/castplay_frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID
        echo "✓ 前端服务已停止 (PID: $FRONTEND_PID)"
    fi
    rm /tmp/castplay_frontend.pid
fi

# 清理可能残留的进程
pkill -f "python run.py" 2>/dev/null
pkill -f "vite" 2>/dev/null

echo "测试服务已全部停止"
