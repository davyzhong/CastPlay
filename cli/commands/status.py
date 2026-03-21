"""
状态查询命令

查询系统状态、设备状态等
"""
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import Optional
from datetime import datetime

from cli.api_client import api_client, APIError

console = Console()


def overview(
    format: str = typer.Option(
        "table", "--format", "-f",
        help="输出格式: table, json"
    )
):
    """
    系统概览

    显示设备数量、播放列表数量、在线状态等概要信息

    示例:
        castplay status
        castplay status --format json
    """
    try:
        # 获取设备列表
        devices_result = api_client.list_devices(limit=100)
        devices = devices_result.get("items", [])
        total_devices = devices_result.get("total", 0)

        # 如果总数超过100，再获取剩余的（仅用于统计）
        if total_devices > 100:
            remaining = api_client.list_devices(skip=100, limit=100)
            devices.extend(remaining.get("items", []))

        # 获取播放列表
        playlists_result = api_client.list_playlists(limit=100)
        playlists = playlists_result.get("items", [])
        playlists = playlists_result.get("items", [])

        # 统计设备状态
        online_count = sum(1 for d in devices if d.get("status") == "online")
        offline_count = len(devices) - online_count
        disabled_count = sum(1 for d in devices if d.get("is_disabled"))

        # 统计播放列表
        system_playlists = sum(1 for p in playlists if p.get("is_system"))
        total_media_items = sum(p.get("item_count", 0) for p in playlists)

        if format == "json":
            import json
            data = {
                "devices": {
                    "total": len(devices),
                    "online": online_count,
                    "offline": offline_count,
                    "disabled": disabled_count
                },
                "playlists": {
                    "total": len(playlists),
                    "system": system_playlists,
                    "total_media_items": total_media_items
                }
            }
            console.print_json(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            # 设备统计面板
            device_stats = (
                f"[bold]设备总数:[/bold] {len(devices)}\n"
                f"[green]在线:[/green] {online_count}\n"
                f"[red]离线:[/red] {offline_count}\n"
                f"[yellow]禁用:[/yellow] {disabled_count}"
            )

            # 播放列表面板
            playlist_stats = (
                f"[bold]播放列表总数:[/bold] {len(playlists)}\n"
                f"[yellow]系统播放列表:[/yellow] {system_playlists}\n"
                f"[dim]媒体项总数:[/dim] {total_media_items}"
            )

            console.print()
            console.print(Panel.fit(
                "[bold cyan]CastPlay 系统概览[/bold cyan]",
                border_style="cyan"
            ))
            console.print()

            # 使用表格并排显示
            table = Table(show_header=False, box=None)
            table.add_column(ratio=1)
            table.add_column(ratio=1)

            table.add_row(
                Panel(device_stats, title="[bold]设备[/bold]", border_style="blue"),
                Panel(playlist_stats, title="[bold]播放列表[/bold]", border_style="green")
            )

            console.print(table)
            console.print()

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def device_status(
    device_id: int = typer.Argument(..., help="设备 ID"),
    format: str = typer.Option("table", "--format", "-f", help="输出格式: table, json")
):
    """
    查询设备播放状态

    示例:
        castplay status device 1
        castplay status device 1 --format json
    """
    try:
        # 获取设备基本信息
        device = api_client.get_device(device_id)

        if format == "json":
            import json
            console.print_json(json.dumps(device, indent=2, ensure_ascii=False))
        else:
            console.print(f"\n[bold]设备状态[/bold]")
            console.print(f"  ID: {device.get('id')}")
            console.print(f"  名称: {device.get('device_name')}")
            console.print(f"  UUID: {device.get('device_id')}")
            console.print(f"  类型: {device.get('device_type', 'N/A')}")
            console.print(f"  在线状态: {'[green]在线[/green]' if device.get('status') == 'online' else '[red]离线[/red]'}")
            console.print(f"  禁用状态: {'[red]已禁用[/red]' if device.get('is_disabled') else '[green]正常[/green]'}")
            console.print(f"  最后在线: {device.get('last_online', 'N/A')}")
            console.print(f"  IP 地址: {device.get('ip_address', 'N/A')}")
            console.print()

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def online_devices(
    format: str = typer.Option("table", "--format", "-f", help="输出格式: table, json")
):
    """
    显示在线设备列表

    示例:
        castplay status online
        castplay status online --format json
    """
    try:
        # 获取在线设备
        result = api_client.get_online_devices()
        devices = result if isinstance(result, list) else result.get("items", [])

        if format == "json":
            import json
            console.print_json(json.dumps({"devices": devices}, indent=2, ensure_ascii=False))
        else:
            if not devices:
                console.print("[yellow]当前没有在线设备[/yellow]")
                return

            table = Table(title=f"在线设备 ({len(devices)} 个)")
            table.add_column("ID", style="cyan")
            table.add_column("设备 ID", style="dim")
            table.add_column("名称", style="green")
            table.add_column("类型", style="yellow")
            table.add_column("当前播放列表", style="blue")
            table.add_column("最后在线", style="dim")

            for device in devices:
                # 当前播放列表
                playlist_info = device.get("current_playlist", {})
                playlist_name = playlist_info.get("name", "-") if playlist_info else "-"

                # 最后在线时间
                last_online = device.get("last_online", "")
                if last_online:
                    try:
                        dt = datetime.fromisoformat(last_online.replace("Z", "+00:00"))
                        last_online_str = dt.strftime("%m-%d %H:%M")
                    except Exception:
                        last_online_str = last_online[:16] if len(last_online) > 16 else last_online
                else:
                    last_online_str = "N/A"

                table.add_row(
                    str(device.get("id", "")),
                    device.get("device_id", "")[:8] + "...",
                    device.get("device_name", "N/A"),
                    device.get("device_type", "N/A"),
                    playlist_name,
                    last_online_str
                )

            console.print(table)

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)
