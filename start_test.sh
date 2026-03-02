#!/bin/bash
# CastPlay 测试启动脚本
# 用于快速启动本地测试环境

set -e

echo "========================================="
echo "  CastPlay 本地测试环境启动"
echo "========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

# 检查 Python 环境
check_python() {
    echo -e "\n${YELLOW}[1/4] 检查 Python 环境...${NC}"
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        echo -e "${GREEN}✓ $PYTHON_VERSION${NC}"
    else
        echo -e "${RED}✗ Python3 未安装${NC}"
        exit 1
    fi
}

# 检查 Node.js 环境
check_node() {
    echo -e "\n${YELLOW}[2/4] 检查 Node.js 环境...${NC}"
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        echo -e "${GREEN}✓ Node.js $NODE_VERSION${NC}"
    else
        echo -e "${RED}✗ Node.js 未安装${NC}"
        exit 1
    fi
}

# 启动后端服务
start_backend() {
    echo -e "\n${YELLOW}[3/4] 启动后端服务...${NC}"
    cd "$PROJECT_ROOT/castplay-server"
    
    # 创建虚拟环境（如果不存在）
    if [ ! -d "venv" ]; then
        echo "创建 Python 虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境并安装依赖
    source venv/bin/activate
    pip install -q -r requirements.txt
    
    # 初始化数据库
    export FLASK_APP=run.py
    export FLASK_ENV=development
    
    if [ ! -f "instance/castplay.db" ]; then
        echo "初始化数据库..."
        flask db upgrade 2>/dev/null || flask db init && flask db migrate && flask db upgrade
    fi
    
    # 启动后端（后台运行）
    echo "启动后端服务 (端口 5001)..."
    python run.py &
    BACKEND_PID=$!
    echo $BACKEND_PID > /tmp/castplay_backend.pid
    
    # 等待后端启动
    sleep 3
    if curl -s http://localhost:5001/health > /dev/null; then
        echo -e "${GREEN}✓ 后端服务已启动 (PID: $BACKEND_PID)${NC}"
    else
        echo -e "${RED}✗ 后端服务启动失败${NC}"
        exit 1
    fi
}

# 启动前端服务
start_frontend() {
    echo -e "\n${YELLOW}[4/4] 启动前端服务...${NC}"
    cd "$PROJECT_ROOT/castplay-admin"
    
    # 安装依赖（如果需要）
    if [ ! -d "node_modules" ]; then
        echo "安装前端依赖..."
        npm install
    fi
    
    # 启动前端（后台运行）
    echo "启动前端服务 (端口 5173)..."
    npm run dev &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > /tmp/castplay_frontend.pid
    
    sleep 3
    echo -e "${GREEN}✓ 前端服务已启动 (PID: $FRONTEND_PID)${NC}"
}

# 显示访问信息
show_info() {
    echo -e "\n========================================="
    echo -e "${GREEN}  测试环境启动成功！${NC}"
    echo "========================================="
    echo ""
    echo "  前端管理后台: http://localhost:3000"
    echo "  后端API地址:  http://localhost:5001/api"
    echo "  健康检查:     http://localhost:5001/health"
    echo ""
    echo "  停止服务: ./stop_test.sh"
    echo "========================================="
}

# 主流程
main() {
    check_python
    check_node
    start_backend
    start_frontend
    show_info
}

main
