"""
服务器管理命令

管理 CastPlay 后端服务器
"""
import typer
from rich.console import Console
from rich.table import Table
import httpx
import os
import signal
import subprocess
import sys
from typing import Optional
from datetime import datetime

console = Console()


def _check_server_status(server_url: str) -> dict:
    """检查服务器状态"""
    try:
        with httpx.Client(timeout=3.0) as client:
            # 尝试获取 API 文档或健康检查
            resp = client.get(f"{server_url}/docs")
            if resp.status_code == 200:
                return {
                    "running": True,
                    "url": server_url,
                    "status": "online"
                }
    except Exception:
        pass
    return {"running": False, "url": server_url, "status": "offline"}


def _find_server_process():
    """查找运行中的服务器进程"""
    try:
        # 查找 uvicorn 进程
        result = subprocess.run(
            ["pgrep", "-f", "uvicorn.*app.main:app"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split("\n")
            return pids
    except Exception:
        pass
    return []


def status():
    """
    显示服务器状态

    示例:
        castplay server status
    """
    from cli.config import config_manager

    config = config_manager.config
    server_url = config.server_url

    # 检查服务器状态
    server_status = _check_server_status(server_url)

    console.print(f"\n[bold]CastPlay 服务器状态[/bold]")
    console.print(f"  服务器地址: {server_url}")
    console.print(f"  运行状态: ", end="")

    if server_status["running"]:
        console.print("[green]● 在线[/green]")

        # 获取更多信息
        try:
            with httpx.Client(timeout=3.0) as client:
                # 尝试获取设备数量
                resp = client.get(f"{server_url}/api/devices/", params={"limit": 1})
                if resp.status_code == 200:
                    data = resp.json()
                    total_devices = data.get("total", 0)
                    console.print(f"  设备总数: {total_devices}")

                # 尝试获取在线设备
                resp = client.get(f"{server_url}/api/player/status", params={"status_filter": "online"})
                if resp.status_code == 200:
                    online = resp.json()
                    console.print(f"  在线设备: {len(online)}")
        except Exception:
            pass
    else:
        console.print("[red]○ 离线[/red]")
        console.print("\n[yellow]提示: 使用以下命令启动服务器:[/yellow]")
        console.print(f"  python scripts/server/start.py")
        console.print(f"  或者")
        console.print(f"  uvicorn app.main:app --host 0.0.0.0 --port 8000")

    # 检查进程
    pids = _find_server_process()
    if pids:
        console.print(f"\n[dim]运行中的进程 PID: {', '.join(pids)}[/dim]")

    console.print()


def start(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="监听地址"),
    port: int = typer.Option(8000, "--port", "-p", help="监听端口"),
    reload: bool = typer.Option(False, "--reload", "-r", help="开发模式（自动重载）"),
    background: bool = typer.Option(False, "--background", "-b", help="后台运行"),
    open_browser: bool = typer.Option(False, "--open", "-o", help="打开浏览器")
):
    """
    启动 CastPlay 服务器

    示例:
        castplay server start
        castplay server start --port 8080
        castplay server start --reload  # 开发模式
        castplay server start --background  # 后台运行
    """
    server_url = f"http://{host}:{port}"

    # 检查是否已经在运行
    if _check_server_status(server_url)["running"]:
        console.print(f"[yellow]服务器已在运行: {server_url}[/yellow]")
        return

    console.print(f"[bold]启动 CastPlay 服务器[/bold]")
    console.print(f"  地址: {server_url}")
    console.print(f"  API 文档: {server_url}/docs")
    console.print(f"  管理面板: {server_url}/")
    console.print()

    # 构建 uvicorn 命令
    cmd = [
        sys.executable,
        "-m", "uvicorn",
        "app.main:app",
        "--host", host,
        "--port", str(port)
    ]

    if reload:
        cmd.append("--reload")

    if background:
        # 后台运行
        console.print("[dim]后台启动中...[/dim]")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        console.print(f"[green]✓ 服务器已在后台启动 (PID: {process.pid})[/green]")

        # 等待并检查
        import time
        time.sleep(2)
        if _check_server_status(server_url)["running"]:
            console.print(f"[green]✓ 服务器运行正常: {server_url}[/green]")
        else:
            console.print("[yellow]⚠ 服务器可能启动失败，请检查日志[/yellow]")
    else:
        # 前台运行
        console.print("[dim]按 Ctrl+C 停止服务器[/dim]")
        console.print()
        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            console.print("\n[yellow]服务器已停止[/yellow]")

    if open_browser:
        import webbrowser
        webbrowser.open(server_url)


def stop(
    force: bool = typer.Option(False, "--force", "-f", help="强制停止")
):
    """
    停止 CastPlay 服务器

    示例:
        castplay server stop
        castplay server stop --force  # 强制停止所有进程
    """
    pids = _find_server_process()

    if not pids:
        console.print("[yellow]没有找到运行中的服务器进程[/yellow]")
        return

    console.print(f"[bold]停止服务器[/bold]")
    console.print(f"  找到 {len(pids)} 个进程: {', '.join(pids)}")

    if not force:
        confirm = typer.confirm("确认停止?", default=True)
        if not confirm:
            console.print("[dim]已取消[/dim]")
            return

    stopped = 0
    for pid in pids:
        try:
            os.kill(int(pid), signal.SIGTERM)
            stopped += 1
            console.print(f"  [green]✓[/green] 已发送停止信号到 PID {pid}")
        except ProcessLookupError:
            console.print(f"  [yellow]![/yellow] 进程 {pid} 不存在")
        except PermissionError:
            console.print(f"  [red]✗[/red] 无权限停止进程 {pid}")

    if stopped > 0:
        console.print(f"\n[green]✓ 已停止 {stopped} 个进程[/green]")
    else:
        console.print("\n[red]✗ 未能停止任何进程[/red]")


def logs(
    lines: int = typer.Option(50, "--lines", "-n", help="显示行数"),
    follow: bool = typer.Option(False, "--follow", "-f", help="实时跟踪日志")
):
    """
    查看服务器日志

    示例:
        castplay server logs
        castplay server logs -n 100  # 显示 100 行
        castplay server logs -f      # 实时跟踪
    """
    import pathlib

    # 查找日志文件
    log_paths = [
        pathlib.Path("logs/castplay.log"),
        pathlib.Path("data/logs/castplay.log"),
        pathlib.Path("/var/log/castplay/castplay.log")
    ]

    log_file = None
    for path in log_paths:
        if path.exists():
            log_file = path
            break

    if not log_file:
        console.print("[yellow]未找到日志文件[/yellow]")
        console.print("日志可能输出到控制台，请使用 'castplay server start' 查看实时日志")
        return

    if follow:
        # 实时跟踪
        console.print(f"[dim]跟踪日志: {log_file} (Ctrl+C 停止)[/dim]")
        console.print()
        try:
            subprocess.run(["tail", "-f", str(log_file)])
        except KeyboardInterrupt:
            console.print("\n[dim]已停止跟踪[/dim]")
    else:
        # 显示最近日志
        console.print(f"[dim]最近 {lines} 行日志: {log_file}[/dim]")
        console.print()
        subprocess.run(["tail", f"-n{lines}", str(log_file)])
