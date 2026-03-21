"""
媒体管理命令

查询和管理媒体文件
"""
import typer
from rich.console import Console
from rich.table import Table
from typing import Optional
from datetime import datetime

from cli.api_client import api_client, APIError

console = Console()


def _format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes is None:
        return "N/A"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def list_media(
    type: Optional[str] = typer.Option(
        None, "--type", "-t",
        help="过滤类型: image, video, ppt"
    ),
    status: Optional[str] = typer.Option(
        None, "--status", "-s",
        help="过滤状态: ready, processing, failed"
    ),
    format: str = typer.Option(
        "table", "--format", "-f",
        help="输出格式: table, json"
    ),
    limit: int = typer.Option(50, "--limit", "-l", help="返回数量")
):
    """
    列出媒体文件

    示例:
        castplay media list
        castplay media list --type video
        castplay media list --status ready
        castplay media list --format json
    """
    try:
        result = api_client.list_media(
            file_type=type,
            status_filter=status,
            limit=limit
        )
        media_list = result.get("items", [])
        total = result.get("total", 0)

        if format == "json":
            import json
            console.print_json(json.dumps({"media": media_list, "total": total}, indent=2, ensure_ascii=False))
        else:
            table = Table(title=f"媒体文件 (共 {len(media_list)} 个)")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("文件名", style="green", max_width=40)
            table.add_column("类型", style="yellow")
            table.add_column("大小", justify="right")
            table.add_column("状态", style="bold")
            table.add_column("上传时间", style="dim")

            for media in media_list:
                # 文件类型
                file_type = media.get("file_type", "N/A")
                type_style = {
                    "image": "[blue]",
                    "video": "[magenta]",
                    "ppt": "[yellow]"
                }.get(file_type, "")

                # 文件大小
                file_size = media.get("file_size", 0)
                size_str = _format_file_size(file_size)

                # 状态
                media_status = media.get("status", "ready")
                status_style = {
                    "ready": "[green]",
                    "processing": "[yellow]",
                    "failed": "[red]"
                }.get(media_status, "")
                status_text = f"{status_style}{media_status}[/]"

                # 上传时间
                created_at = media.get("created_at", "")
                if created_at:
                    try:
                        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        created_str = dt.strftime("%m-%d %H:%M")
                    except Exception:
                        created_str = created_at[:16] if len(created_at) > 16 else created_at
                else:
                    created_str = "N/A"

                table.add_row(
                    str(media.get("id")),
                    media.get("file_name", "N/A"),
                    f"{type_style}{file_type}[/]",
                    size_str,
                    status_text,
                    created_str
                )

            console.print(table)

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def get_media(
    media_id: int = typer.Argument(..., help="媒体文件 ID"),
    format: str = typer.Option(
        "table", "--format", "-f",
        help="输出格式: table, json"
    )
):
    """
    获取媒体文件详情

    示例:
        castplay media get 1
        castplay media get 1 --format json
    """
    try:
        media = api_client.get_media(media_id)

        if format == "json":
            import json
            console.print_json(json.dumps(media, indent=2, ensure_ascii=False))
        else:
            console.print(f"\n[bold]媒体文件详情[/bold]")
            console.print(f"  ID: {media.get('id')}")
            console.print(f"  文件名: {media.get('file_name')}")
            console.print(f"  类型: {media.get('file_type', 'N/A')}")
            console.print(f"  大小: {_format_file_size(media.get('file_size', 0))}")
            console.print(f"  状态: {media.get('status', 'N/A')}")
            console.print(f"  MD5: {media.get('md5_hash', 'N/A')}")
            console.print(f"  存储路径: {media.get('file_path', 'N/A')}")

            if media.get("converted_path"):
                console.print(f"  转换后路径: {media.get('converted_path')}")

            if media.get("thumbnail_path"):
                console.print(f"  缩略图路径: {media.get('thumbnail_path')}")

            if media.get("slide_duration"):
                console.print(f"  PPT 幻灯片时长: {media.get('slide_duration')} 秒")

            console.print(f"  上传时间: {media.get('created_at', 'N/A')}")
            console.print(f"  更新时间: {media.get('updated_at', 'N/A')}")
            console.print()

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def delete_media(
    media_id: int = typer.Argument(..., help="媒体文件 ID"),
    force: bool = typer.Option(False, "--force", "-f", help="强制删除（不确认）")
):
    """
    删除媒体文件

    注意：删除媒体文件会同时删除所有播放列表中的引用

    示例:
        castplay media delete 1
        castplay media delete 1 --force
    """
    try:
        # 获取媒体信息用于确认
        media = api_client.get_media(media_id)

        if not force:
            console.print(f"[yellow]警告: 即将删除媒体文件[/yellow]")
            console.print(f"  ID: {media_id}")
            console.print(f"  文件名: {media.get('file_name')}")
            console.print(f"  类型: {media.get('file_type')}")
            console.print(f"  大小: {_format_file_size(media.get('file_size', 0))}")

            confirm = typer.confirm("确定要删除吗？", default=False)
            if not confirm:
                console.print("[dim]已取消[/dim]")
                raise typer.Exit(0)

        api_client.delete_media(media_id)
        console.print(f"[green]✓ 媒体文件已删除: {media.get('file_name')}[/green]")

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def upload_media(
    file_path: str = typer.Argument(..., help="要上传的文件路径"),
    file_type: str = typer.Option(
        None, "--type", "-t",
        help="文件类型: image, video, ppt (自动检测，可手动指定)"
    ),
    slide_duration: int = typer.Option(
        5, "--duration", "-d",
        help="PPT 幻灯片间隔时长(秒)"
    )
):
    """
    上传媒体文件

    示例:
        castplay media upload /path/to/image.jpg
        castplay media upload /path/to/video.mp4 --type video
        castplay media upload /path/to/slides.pptx --duration 10
    """
    from pathlib import Path

    try:
        path = Path(file_path)
        if not path.exists():
            console.print(f"[red]错误: 文件不存在 - {file_path}[/red]")
            raise typer.Exit(1)

        # 自动检测文件类型
        detected_type = file_type
        if detected_type is None:
            ext = path.suffix.lower()
            if ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"]:
                detected_type = "image"
            elif ext in [".mp4", ".avi", ".mov", ".mkv", ".webm"]:
                detected_type = "video"
            elif ext in [".ppt", ".pptx"]:
                detected_type = "ppt"
            else:
                console.print(f"[red]错误: 无法识别的文件类型 '{ext}'[/red]")
                console.print("请使用 --type 参数指定类型: image, video, ppt")
                raise typer.Exit(1)

        console.print(f"[dim]正在上传: {path.name}[/dim]")
        console.print(f"[dim]文件类型: {detected_type}[/dim]")

        result = api_client.upload_media(
            file_path=str(path),
            file_type=detected_type,
            slide_duration=slide_duration if detected_type == "ppt" else None
        )

        # API returns {"message": "...", "media": {...}}
        media = result.get("media", result)

        console.print(f"[green]✓ 媒体文件上传成功[/green]")
        console.print(f"  ID: {media.get('id')}")
        console.print(f"  文件名: {media.get('file_name')}")
        console.print(f"  类型: {media.get('file_type')}")
        console.print(f"  大小: {_format_file_size(media.get('file_size', 0))}")
        if media.get('file_type') == 'ppt':
            console.print(f"  幻灯片时长: {slide_duration} 秒")

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]错误: {str(e)}[/red]")
        raise typer.Exit(1)
