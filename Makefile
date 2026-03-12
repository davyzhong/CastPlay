# CastPlay All-in-One Makefile
# 提供便捷的测试和开发命令

.PHONY: help install dev test clean lint coverage e2e performance security all

# 默认目标
.DEFAULT_GOAL := help

# ==================== 帮助 ====================
help:
	@echo "CastPlay All-in-One 可用命令:"
	@echo ""
	@echo "  make install          - 安装所有依赖"
	@echo "  make install-dev       - 安装开发依赖"
	@echo "  make dev              - 启动开发服务器"
	@echo "  make dev-backend      - 启动后端开发服务器"
	@echo "  make dev-frontend     - 启动前端开发服务器"
	@echo ""
	@echo "测试命令:"
	@echo "  make test             - 运行所有测试"
	@echo "  make test-unit       - 运行单元测试"
	@echo "  make test-integration  - 运行集成测试"
	@echo "  make test-e2e         - 运行 E2E 测试"
	@echo "  make test-coverage    - 运行测试并生成覆盖率报告"
	@echo ""
	@echo "代码质量:"
	@echo "  make lint             - 检查代码格式和质量"
	@echo "  make lint-black       - 检查 Black 格式"
	@echo "  make lint-isort      - 检查 isort 导入排序"
	@echo "  make lint-mypy       - 检查 mypy 类型"
	@echo "  make lint-pylint     - 检查 pylint 代码质量"
	@echo "  make format           - 自动格式化代码"
	@echo ""
	@echo "性能和安全:"
	@echo "  make test-performance  - 运行性能测试"
	@echo "  make test-security    - 运行安全扫描"
	@echo "  make test-safety      - 检查依赖安全漏洞"
	@echo ""
	@echo "数据库:"
	@echo "  make db-init          - 初始化数据库"
	@echo "  make db-reset         - 重置数据库"
	@echo "  make db-backup        - 备份数据库"
	@echo "  make db-restore       - 恢复数据库"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     - 构建 Docker 镜像"
	@echo "  make docker-run       - 运行 Docker 容器"
	@echo "  make docker-stop       - 停止 Docker 容器"
	@echo "  make docker-clean      - 清理 Docker 资源"

# ==================== 安装 ====================
install:
	@echo "安装生产依赖..."
	pip install -r requirements.txt
	cd frontend && npm install

install-dev:
	@echo "安装开发依赖..."
	pip install -r requirements.txt
	pip install pytest pytest-cov pytest-asyncio pytest-xdist black isort mypy pylint bandit safety
	cd frontend && npm install

# ==================== 开发 ====================
dev:
	@echo "启动开发服务器..."
	@make -j2 dev-backend dev-frontend

dev-backend:
	@echo "启动后端开发服务器 (端口 8000)..."
	python scripts/run.py

dev-frontend:
	@echo "启动前端开发服务器 (端口 5173)..."
	cd frontend && npm run dev

# ==================== 测试 ====================
test:
	@echo "运行所有测试..."
	pytest tests/ -v

test-unit:
	@echo "运行单元测试..."
	pytest tests/ -v -m "unit" --cov=app --cov-report=html

test-integration:
	@echo "运行集成测试..."
	pytest tests/integration/ -v --cov=app --cov-append

test-e2e:
	@echo "运行 E2E 测试..."
	cd frontend && npm run test:e2e

test-coverage:
	@echo "运行测试并生成覆盖率报告..."
	pytest tests/ -v --cov=app --cov-report=html --cov-report=xml --cov-report=term
	@echo "覆盖率报告已生成: htmlcov/index.html"

test-quick:
	@echo "运行快速测试（跳过慢速测试）..."
	pytest tests/ -v -m "not slow" --maxfail=5

test-watch:
	@echo "监听文件变化自动运行测试..."
	pytest tests/ -v -f

test-parallel:
	@echo "并行运行测试..."
	pytest tests/ -v -n auto --dist=loadscope

# ==================== 代码质量 ====================
lint:
	@echo "运行所有代码检查..."
	@make lint-black
	@make lint-isort
	@make lint-mypy
	@make lint-pylint

lint-black:
	@echo "检查 Black 格式..."
	black --check app/ tests/ || black app/ tests/

lint-isort:
	@echo "检查 isort 导入排序..."
	isort --check-only app/ tests/ || isort app/ tests/

lint-mypy:
	@echo "检查 mypy 类型..."
	mypy app/ --ignore-missing-imports

lint-pylint:
	@echo "检查 pylint 代码质量..."
	pylint app/ --rcfile=.pylintrc || true

format:
	@echo "格式化代码..."
	black app/ tests/
	isort app/ tests/

# ==================== 性能测试 ====================
test-performance:
	@echo "运行性能测试..."
	locust -f tests/performance/locustfile.py \
		--host http://localhost:8000 \
		--users 100 \
		--spawn-rate 10 \
		--run-time 60s \
		--headless \
		--html tests/reports/performance-report.html

test-performance-normal:
	@echo "运行正常负载测试..."
	locust -f tests/performance/locustfile.py \
		--host http://localhost:8000 \
		--users 100 \
		--spawn-rate 10 \
		--run-time 10m \
		--headless

test-performance-stress:
	@echo "运行压力测试..."
	locust -f tests/performance/locustfile.py \
		--host http://localhost:8000 \
		--users 500 \
		--spawn-rate 50 \
		--run-time 5m \
		--headless

# ==================== 安全测试 ====================
test-security:
	@echo "运行安全扫描..."
	bandit -r app/ -f json -o tests/reports/bandit-report.json

test-safety:
	@echo "检查依赖安全漏洞..."
	safety check --json --output tests/reports/safety-report.json

test-dependencies:
	@echo "检查过期依赖..."
	pip list --outdated

# ==================== 数据库 ====================
db-init:
	@echo "初始化数据库..."
	python scripts/init_db.py

db-reset:
	@echo "重置数据库..."
	python scripts/reset_db.py

db-backup:
	@echo "备份数据库..."
	python scripts/backup_db.py

db-restore:
	@echo "恢复数据库..."
	@echo "请指定备份文件: make db-restore FILE=backup.db"

# ==================== Docker ====================
docker-build:
	@echo "构建 Docker 镜像..."
	docker build -t castplay:latest .

docker-run:
	@echo "运行 Docker 容器..."
	docker-compose up -d

docker-stop:
	@echo "停止 Docker 容器..."
	docker-compose down

docker-clean:
	@echo "清理 Docker 资源..."
	docker-compose down -v
	docker system prune -f

# ==================== 清理 ====================
clean:
	@echo "清理临时文件..."
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type d -name '.pytest_cache' -exec rm -rf {} +
	find . -type d -name 'htmlcov' -exec rm -rf {} +
	find . -type d -name '.mypy_cache' -exec rm -rf {} +
	rm -rf .coverage coverage.xml
	cd frontend && rm -rf dist node_modules/.vite

clean-all:
	@echo "清理所有生成文件..."
	@make clean
	rm -rf venv/ frontend/node_modules/
	rm -f data/castplay.db data/castplay.db-*

# ==================== 文档 ====================
docs:
	@echo "生成 API 文档..."
	redocly bundle app/main.html -o docs/api-reference.html

docs-test:
	@echo "生成测试报告..."
	@make test-coverage
	@echo "测试报告: file://$$(pwd)/htmlcov/index.html"

# ==================== 快捷命令 ====================
ci: install-dev lint test-coverage
	@echo "CI 流程: 安装依赖 -> 检查代码 -> 运行测试"

dev-setup: install-dev db-init
	@echo "开发环境设置完成！"

ready-check:
	@echo "检查开发环境..."
	@which python3 || echo "❌ Python3 未安装"
	@which node || echo "❌ Node.js 未安装"
	@which docker || echo "⚠️ Docker 未安装（生产环境需要）"
	@echo "✅ 开发环境检查完成"
