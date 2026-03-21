#!/usr/bin/env python
"""
Web 播放端测试环境启动脚本

启动后端服务器，供 Web 播放端测试使用。

运行方式：
    python scripts/testing/start_web_env.py

环境启动后，可以在另一个终端运行测试：
    python scripts/testing/run_web_tests.py --e2e --headed

或者手动测试：
    打开浏览器访问 http://localhost:8000/player.html
"""
import subprocess
import sys
import os
from pathlib import Path


def main():
    """启动测试环境"""
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)

    print("=" * 60)
    print("Web 播放端测试环境启动脚本")
    print("=" * 60)
    print()
    print("启动后端服务器...")
    print("访问地址: http://localhost:8000")
    print("播放端页面: http://localhost:8000/player.html")
    print()
    print("按 Ctrl+C 停止服务器")
    print("-" * 60)

    # 启动后端服务器
    try:
        # 使用 uvicorn 启动 FastAPI 服务器
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ], cwd=project_root)
    except KeyboardInterrupt:
        print("\n服务器已停止")


if __name__ == "__main__":
    main()
