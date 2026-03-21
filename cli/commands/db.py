"""
数据库管理命令

备份和清理数据库
"""
import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import shutil

from cli.config import config_manager

console = Console()


def backup(
    output: Optional[str] = typer.Option(
        None, "--output", "-o",
        help="备份文件输出路径"
    )
):
    """
    备份数据库

    示例:
        castplay db backup
        castplay db backup --output /path/to/backup.db
    """
    try:
        # 获取数据库路径
        db_path = Path(config_manager.config.server_url.replace("http://", "").replace("https://", ""))
        db_path = Path("data/castplay.db")  # 默认路径

        if not db_path.exists():
            console.print(f"[red]✗ 数据库文件不存在: {db_path}[/red]")
            console.print("[yellow]提示: 如果使用远程服务器，请直接在服务器上执行备份[/yellow]")
            raise typer.Exit(1)

        # 生成备份路径
        if output:
            backup_path = Path(output)
        else:
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"castplay_{timestamp}.db"

        # 复制数据库文件
        shutil.copy2(db_path, backup_path)

        # 获取文件大小
        file_size = backup_path.stat().st_size
        size_str = _format_file_size(file_size)

        console.print(f"[green]✓ 数据库备份成功[/green]")
        console.print(f"  备份文件: {backup_path}")
        console.print(f"  文件大小: {size_str}")
        console.print(f"  备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        console.print(f"[red]✗ 备份失败: {str(e)}[/red]")
        raise typer.Exit(1)


def cleanup_backups(
    days: int = typer.Option(
        7, "--days", "-d",
        help="保留最近 N 天的备份"
    ),
    dry_run: bool = typer.Option(
        True, "--dry-run",
        help="仅预览，不实际删除"
    ),
    execute: bool = typer.Option(
        False, "--execute",
        help="实际执行清理"
    )
):
    """
    清理旧的备份文件

    默认为预览模式，使用 --execute 参数实际执行清理

    示例:
        castplay db cleanup --days 7 --dry-run
        castplay db cleanup --days 7 --execute
    """
    try:
        backup_dir = Path("backups")

        if not backup_dir.exists():
            console.print("[yellow]备份目录不存在[/yellow]")
            return

        # 查找备份文件
        backup_files = list(backup_dir.glob("castplay_*.db"))

        if not backup_files:
            console.print("[green]没有备份文件需要清理[/green]")
            return

        # 计算截止时间
        cutoff_time = datetime.now() - timedelta(days=days)

        # 找出需要删除的文件
        files_to_delete = []
        for backup_file in backup_files:
            file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
            if file_mtime < cutoff_time:
                files_to_delete.append(backup_file)

        if not files_to_delete:
            console.print(f"[green]没有超过 {days} 天的备份文件[/green]")
            return

        if dry_run and not execute:
            console.print(f"[yellow]预览模式: 将删除 {len(files_to_delete)} 个备份文件[/yellow]\n")

            table = Table(title="待删除备份文件")
            table.add_column("文件名", style="red")
            table.add_column("大小", justify="right")
            table.add_column("创建时间", style="dim")

            for backup_file in sorted(files_to_delete):
                file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
                table.add_row(
                    backup_file.name,
                    _format_file_size(backup_file.stat().st_size),
                    file_mtime.strftime("%Y-%m-%d %H:%M")
                )

            console.print(table)
            console.print(f"\n使用 [bold]castplay db cleanup --days {days} --execute[/bold] 执行清理")

        else:
            # 执行删除
            deleted_count = 0
            for backup_file in files_to_delete:
                backup_file.unlink()
                deleted_count += 1

            console.print(f"[green]✓ 已清理 {deleted_count} 个旧备份文件[/green]")

    except Exception as e:
        console.print(f"[red]✗ 清理失败: {str(e)}[/red]")
        raise typer.Exit(1)


def _format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
