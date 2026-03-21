"""
播放列表管理命令
"""
import typer
from rich.console import Console
from rich.table import Table
from typing import Optional

from cli.api_client import api_client, APIError

console = Console()


def list_playlists(
    format: str = typer.Option(
        "table", "--format", "-f",
        help="输出格式: table, json"
    ),
    limit: int = typer.Option(50, "--limit", "-l", help="返回数量")
):
    """
    列出所有播放列表

    示例:
        castplay playlists list
        castplay playlists list --format json
    """
    try:
        result = api_client.list_playlists(limit=limit)
        playlists = result.get("items", [])
        total = result.get("total", 0)

        if format == "json":
            import json
            console.print_json(json.dumps({"playlists": playlists, "total": total}))
        else:
            table = Table(title=f"播放列表 (共 {len(playlists)} 个)")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("名称", style="green")
            table.add_column("描述", style="dim")
            table.add_column("媒体数", justify="right")
            table.add_column("设备数", justify="right")
            table.add_column("系统", style="yellow")

            for playlist in playlists:
                is_system = playlist.get("is_system", False)
                system_text = "是" if is_system else "否"

                # Handle None description safely
                description = playlist.get("description") or ""
                description_display = (description[:30] if description else "-")

                table.add_row(
                    str(playlist.get("id")),
                    playlist.get("name", "N/A"),
                    description_display,
                    str(playlist.get("item_count", 0)),
                    str(playlist.get("device_count", 0)),
                    f"[yellow]{system_text}[/yellow]" if is_system else system_text
                )

            console.print(table)

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def get_playlist(
    playlist_id: int = typer.Argument(..., help="播放列表 ID"),
    format: str = typer.Option(
        "table", "--format", "-f",
        help="输出格式: table, json"
    )
):
    """
    获取播放列表详情

    示例:
        castplay playlists get 1
    """
    try:
        playlist = api_client.get_playlist(playlist_id)

        if format == "json":
            import json
            console.print_json(json.dumps(playlist, indent=2, ensure_ascii=False))
        else:
            console.print(f"\n[bold]播放列表详情[/bold]")
            console.print(f"  ID: {playlist.get('id')}")
            console.print(f"  名称: {playlist.get('name')}")
            console.print(f"  描述: {playlist.get('description', 'N/A')}")
            console.print(f"  系统播放列表: {'是' if playlist.get('is_system') else '否'}")
            console.print(f"  创建时间: {playlist.get('created_at', 'N/A')}")
            console.print(f"  更新时间: {playlist.get('updated_at', 'N/A')}")

            # 显示媒体项
            items = playlist.get("items", [])
            if items:
                console.print(f"\n[bold]媒体项 ({len(items)} 个)[/bold]")
                table = Table()
                table.add_column("序号", style="dim")
                table.add_column("媒体 ID", style="cyan")
                table.add_column("文件名", style="green")
                table.add_column("类型", style="yellow")
                table.add_column("时长(s)", justify="right")

                for item in items:
                    table.add_row(
                        str(item.get("display_order", 0)),
                        str(item.get("media_id")),
                        item.get("file_name", "N/A"),
                        item.get("file_type", "N/A"),
                        str(item.get("display_duration", 0))
                    )
                console.print(table)
            else:
                console.print("\n[yellow]暂无媒体项[/yellow]")

            # 显示关联设备
            devices = playlist.get("devices", [])
            if devices:
                console.print(f"\n[bold]关联设备 ({len(devices)} 个)[/bold]")
                table = Table()
                table.add_column("设备 ID", style="cyan")
                table.add_column("设备名称", style="green")
                table.add_column("状态", style="bold")
                table.add_column("激活", style="yellow")

                for device in devices:
                    is_active = device.get("is_active", False)
                    table.add_row(
                        str(device.get("device_id")),
                        device.get("device_name", "N/A"),
                        device.get("device_status", "N/A"),
                        "[green]是[/green]" if is_active else "[red]否[/red]"
                    )
                console.print(table)

            console.print()

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def create_playlist(
    name: str = typer.Argument(..., help="播放列表名称"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="播放列表描述")
):
    """
    创建播放列表

    示例:
        castplay playlists create "大厅展示"
        castplay playlists create "会议室播放列表" --description "用于会议室的播放内容"
    """
    try:
        result = api_client.create_playlist(name=name, description=description)
        console.print(f"[green]✓ 播放列表已创建[/green]")
        console.print(f"  ID: {result.get('id')}")
        console.print(f"  名称: {result.get('name')}")
        if description:
            console.print(f"  描述: {result.get('description', 'N/A')}")

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def delete_playlist(
    playlist_id: int = typer.Argument(..., help="播放列表 ID"),
    force: bool = typer.Option(False, "--force", "-f", help="强制删除（即使有设备关联）")
):
    """
    删除播放列表

    注意：有设备正在使用的播放列表无法删除，除非使用 --force 参数

    示例:
        castplay playlists delete 1
    """
    try:
        # 检查是否有设备关联
        playlist = api_client.get_playlist(playlist_id)
        devices = playlist.get("devices", [])

        if devices and not force:
            console.print(f"[red]✗ 播放列表有 {len(devices)} 个设备关联，无法删除[/red]")
            console.print("使用 --force 参数强制删除，或先取消设备关联")
            raise typer.Exit(1)

        api_client.delete_playlist(playlist_id)
        console.print(f"[green]✓ 播放列表已删除: ID {playlist_id}[/green]")

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def assign_playlist(
    playlist_id: int = typer.Argument(..., help="播放列表 ID"),
    device_id: int = typer.Argument(..., help="设备 ID")
):
    """
    分配播放列表到设备

    示例:
        castplay playlists assign 1 2
    """
    try:
        result = api_client.assign_playlist(playlist_id, device_id)
        console.print(f"[green]✓ 播放列表已分配到设备[/green]")
        console.print(f"  分配 ID: {result.get('id')}")
        console.print(f"  播放列表 ID: {playlist_id}")
        console.print(f"  设备 ID: {device_id}")

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def unassign_playlist(
    playlist_id: int = typer.Argument(..., help="播放列表 ID"),
    device_id: int = typer.Argument(..., help="设备 ID")
):
    """
    取消播放列表分配

    示例:
        castplay playlists unassign 1 2
    """
    try:
        api_client.unassign_playlist(playlist_id, device_id)
        console.print(f"[green]✓ 播放列表分配已取消[/green]")
        console.print(f"  播放列表 ID: {playlist_id}")
        console.print(f"  设备 ID: {device_id}")

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def activate_playlist(
    playlist_id: int = typer.Argument(..., help="播放列表 ID"),
    device_id: int = typer.Argument(..., help="设备 ID")
):
    """
    激活设备上的播放列表

    示例:
        castplay playlists activate 1 2
    """
    try:
        result = api_client.activate_playlist(playlist_id, device_id, is_active=True)
        console.print(f"[green]✓ 播放列表已激活[/green]")
        console.print(f"  播放列表 ID: {playlist_id}")
        console.print(f"  设备 ID: {device_id}")

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def deactivate_playlist(
    playlist_id: int = typer.Argument(..., help="播放列表 ID"),
    device_id: int = typer.Argument(..., help="设备 ID")
):
    """
    停用设备上的播放列表

    示例:
        castplay playlists deactivate 1 2
    """
    try:
        result = api_client.activate_playlist(playlist_id, device_id, is_active=False)
        console.print(f"[green]✓ 播放列表已停用[/green]")
        console.print(f"  播放列表 ID: {playlist_id}")
        console.print(f"  设备 ID: {device_id}")

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


# ==================== 播放列表项管理 ====================

def list_items(
    playlist_id: int = typer.Argument(..., help="播放列表 ID"),
    format: str = typer.Option("table", "--format", "-f", help="输出格式: table, json")
):
    """
    列出播放列表中的媒体项

    示例:
        castplay playlists items 1
        castplay playlists items 1 --format json
    """
    try:
        playlist = api_client.get_playlist(playlist_id)
        items = playlist.get("items", [])

        if format == "json":
            import json
            console.print_json(json.dumps({"items": items, "total": len(items)}, indent=2, ensure_ascii=False))
        else:
            if not items:
                console.print("[yellow]播放列表为空[/yellow]")
                return

            table = Table(title=f"播放列表 '{playlist.get('name')}' 媒体项 (共 {len(items)} 个)")
            table.add_column("序号", style="dim", justify="right")
            table.add_column("项 ID", style="cyan", no_wrap=True)
            table.add_column("媒体 ID", style="green")
            table.add_column("文件名", style="blue")
            table.add_column("类型", style="yellow")
            table.add_column("时长(s)", justify="right")

            for item in items:
                table.add_row(
                    str(item.get("display_order", 0)),
                    str(item.get("id")),
                    str(item.get("media_id")),
                    item.get("file_name", "N/A"),
                    item.get("file_type", "N/A"),
                    str(item.get("display_duration", 0))
                )
            console.print(table)

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def add_item(
    playlist_id: int = typer.Argument(..., help="播放列表 ID"),
    media_id: int = typer.Option(..., "--media-id", "-m", help="媒体 ID"),
    duration: int = typer.Option(10, "--duration", "-d", help="播放时长(秒)"),
    order: Optional[int] = typer.Option(None, "--order", "-o", help="显示顺序")
):
    """
    添加媒体到播放列表

    示例:
        castplay playlists add-item 1 --media-id 5
        castplay playlists add-item 1 --media-id 5 --duration 15 --order 1
    """
    try:
        result = api_client.add_playlist_item(
            playlist_id,
            media_id,
            display_duration=duration,
            display_order=order
        )
        console.print(f"[green]✓ 媒体已添加到播放列表[/green]")
        console.print(f"  播放列表 ID: {playlist_id}")
        console.print(f"  媒体 ID: {media_id}")
        console.print(f"  项 ID: {result.get('id')}")
        console.print(f"  播放时长: {duration} 秒")
        if order:
            console.print(f"  显示顺序: {order}")

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def add_items_batch(
    playlist_id: int = typer.Argument(..., help="播放列表 ID"),
    media_ids: str = typer.Option(..., "--media-ids", "-m", help="媒体 ID 列表，逗号分隔"),
    duration: int = typer.Option(10, "--duration", "-d", help="默认播放时长(秒)")
):
    """
    批量添加媒体到播放列表

    示例:
        castplay playlists add-items 1 --media-ids 5,6,7
        castplay playlists add-items 1 --media-ids 5,6,7 --duration 15
    """
    try:
        ids = [int(x.strip()) for x in media_ids.split(",")]
        result = api_client.add_playlist_items_batch(
            playlist_id,
            ids,
            display_duration=duration
        )
        console.print(f"[green]✓ 批量添加成功[/green]")
        console.print(f"  播放列表 ID: {playlist_id}")
        console.print(f"  添加数量: {result.get('added_count', len(ids))}")
        console.print(f"  默认时长: {duration} 秒")

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def remove_item(
    playlist_id: int = typer.Argument(..., help="播放列表 ID"),
    item_id: int = typer.Argument(..., help="播放列表项 ID")
):
    """
    从播放列表移除媒体项

    示例:
        castplay playlists remove-item 1 3
    """
    try:
        api_client.remove_playlist_item(playlist_id, item_id)
        console.print(f"[green]✓ 媒体项已移除[/green]")
        console.print(f"  播放列表 ID: {playlist_id}")
        console.print(f"  项 ID: {item_id}")

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def update_item(
    playlist_id: int = typer.Argument(..., help="播放列表 ID"),
    item_id: int = typer.Argument(..., help="播放列表项 ID"),
    duration: Optional[int] = typer.Option(None, "--duration", "-d", help="播放时长(秒)"),
    order: Optional[int] = typer.Option(None, "--order", "-o", help="显示顺序")
):
    """
    更新播放列表项

    示例:
        castplay playlists update-item 1 3 --duration 20
        castplay playlists update-item 1 3 --order 5
    """
    try:
        if duration is None and order is None:
            console.print("[yellow]请指定要更新的字段 (--duration 或 --order)[/yellow]")
            return

        result = api_client.update_playlist_item(
            playlist_id,
            item_id,
            display_duration=duration,
            display_order=order
        )
        console.print(f"[green]✓ 播放列表项已更新[/green]")
        console.print(f"  播放列表 ID: {playlist_id}")
        console.print(f"  项 ID: {item_id}")
        if duration:
            console.print(f"  播放时长: {duration} 秒")
        if order:
            console.print(f"  显示顺序: {order}")

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def reorder_items(
    playlist_id: int = typer.Argument(..., help="播放列表 ID"),
    order: str = typer.Option(..., "--order", "-o", help="新的顺序，项 ID 逗号分隔，如 3,1,2,4")
):
    """
    重新排序播放列表项

    示例:
        castplay playlists reorder 1 --order 3,1,2,4
    """
    try:
        item_ids = [int(x.strip()) for x in order.split(",")]
        result = api_client.reorder_playlist_items(playlist_id, item_ids)
        console.print(f"[green]✓ 播放列表顺序已更新[/green]")
        console.print(f"  播放列表 ID: {playlist_id}")
        console.print(f"  新顺序: {order}")

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)
