"""
启动脚本
用于启动 CastPlay All-in-One 服务
"""
import uvicorn
from pathlib import Path
import sys

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.config import settings


def main():
    """
    主函数 - 启动 FastAPI 服务器
    """
    print("=" * 60)
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print("=" * 60)
    print(f"Host: {settings.HOST}")
    print(f"Port: {settings.PORT}")
    print(f"Debug: {settings.DEBUG}")
    print(f"API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print("=" * 60)

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )


if __name__ == "__main__":
    main()
