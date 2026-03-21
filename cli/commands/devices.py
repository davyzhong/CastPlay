"""
设备管理命令
"""
import typer
from rich.console import Console
from rich.table import Table
from typing import Optional, List
from datetime import datetime

from cli.api_client import api_client, APIError
from cli.config import config_manager

console = Console()


def list_devices(
    status: Optional[str] = typer.Option(
        None, "--status", "-s",
        help="过滤状态: online, offline, disabled"
    ),
    format: str = typer.Option(
        "table", "--format", "-f",
        help="输出格式: table, json"
    ),
    limit: int = typer.Option(50, "--limit", "-l", help="返回数量")
):
    """
    列出所有设备

    示例:
        castplay devices list
        castplay devices list --status online
        castplay devices list --format json
    """
    try:
        # 映射状态过滤
        status_filter = None
        if status:
            status_lower = status.lower()
            if status_lower == "disabled":
                # disabled 设备在 API 中通过 is_disabled 字段过滤
                status_filter = None  # 需要在客户端过滤
            else:
                status_filter = status_lower

        result = api_client.list_devices(status_filter=status_filter, limit=limit)
        devices = result.get("items", [])
        total = result.get("total", 0)

        # 如果指定了 disabled 过滤，在客户端过滤
        if status and status.lower() == "disabled":
            devices = [d for d in devices if d.get("is_disabled", False)]

        if format == "json":
            import json
            console.print_json(json.dumps({"devices": devices, "total": total}))
        else:
            table = Table(title=f"设备列表 (共 {len(devices)} 个)")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("名称", style="green")
            table.add_column("状态", style="bold")
            table.add_column("类型", style="dim")
            table.add_column("禁用", style="red")
            table.add_column("最后在线", style="dim")

            for device in devices:
                # 状态显示
                device_status = device.get("status", "unknown")
                status_style = "green" if device_status == "online" else "red"

                # 禁用状态
                is_disabled = device.get("is_disabled", False)
                disabled_text = "是" if is_disabled else "否"

                # 最后在线时间
                last_online = device.get("last_online")
                if last_online:
                    try:
                        dt = datetime.fromisoformat(last_online.replace("Z", "+00:00"))
                        last_online_str = dt.strftime("%m-%d %H:%M")
                    except Exception:
                        last_online_str = last_online[:16] if len(last_online) > 16 else last_online
                else:
                    last_online_str = "N/A"

                table.add_row(
                    str(device.get("id")),
                    device.get("device_name", "N/A"),
                    f"[{status_style}]{device_status}[/{status_style}]",
                    device.get("device_type", "N/A"),
                    f"[red]{disabled_text}[/red]" if is_disabled else disabled_text,
                    last_online_str
                )

            console.print(table)

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]请求失败: {str(e)}[/red]")
        raise typer.Exit(1)


def get_device(
    device_id: int = typer.Argument(..., help="设备 ID"),
    format: str = typer.Option("table", "--format", "-f", help="输出格式: table, json")
):
    """
    获取设备详情

    示例:
        castplay devices get 1
        castplay devices get 1 --format json
    """
    try:
        device = api_client.get_device(device_id)

        if format == "json":
            import json
            console.print_json(json.dumps(device, indent=2, ensure_ascii=False))
        else:
            console.print(f"\n[bold]设备详情[/bold]")
            console.print(f"  ID: {device.get('id')}")
            console.print(f"  设备 ID: {device.get('device_id')}")
            console.print(f"  名称: {device.get('device_name')}")
            console.print(f"  类型: {device.get('device_type', 'N/A')}")
            console.print(f"  状态: {device.get('status', 'unknown')}")
            console.print(f"  禁用: {'是' if device.get('is_disabled') else '否'}")
            console.print(f"  时区: {device.get('timezone', 'Asia/Shanghai')}")
            console.print(f"  注册码: {device.get('registration_code', 'N/A')}")
            console.print(f"  IP 地址: {device.get('ip_address', 'N/A')}")
            console.print(f"  最后在线: {device.get('last_online', 'N/A')}")
            console.print()

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def disable_device(
    device_id: int = typer.Argument(..., help="设备 ID")
):
    """
    禁用设备

    禁用后的设备只能播放默认播放列表内容

    示例:
        castplay devices disable 1
    """
    try:
        result = api_client.disable_device(device_id, is_disabled=True)
        console.print(f"[green]✓ 设备已禁用: {result.get('device_name')}[/green]")
    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def enable_device(
    device_id: int = typer.Argument(..., help="设备 ID")
):
    """
    启用设备

    示例:
        castplay devices enable 1
    """
    try:
        result = api_client.disable_device(device_id, is_disabled=False)
        console.print(f"[green]✓ 设备已启用: {result.get('device_name')}[/green]")
    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def set_schedule(
    device_id: int = typer.Argument(..., help="设备 ID"),
    on_time: Optional[str] = typer.Option(None, "--on-time", help="开机时间 (HH:MM)"),
    off_time: Optional[str] = typer.Option(None, "--off-time", help="关机时间 (HH:MM)"),
    weekdays: Optional[str] = typer.Option(None, "--weekdays", "-w", help="工作日 (1,2,3,4,5 表示周一到周五)"),
    disable: bool = typer.Option(False, "--disable", help="禁用定时配置")
):
    """
    设置设备定时配置

    示例:
        castplay devices schedule 1 --on-time 08:00 --off-time 22:00 --weekdays 1,2,3,4,5
        castplay devices schedule 1 --disable
    """
    try:
        # 解析工作日
        weekdays_list = None
        if weekdays:
            weekdays_list = [int(d.strip()) for d in weekdays.split(",")]

        result = api_client.set_device_schedule(
            device_id=device_id,
            power_on_time=on_time,
            power_off_time=off_time,
            is_enabled=not disable,
            weekdays=weekdays_list
        )

        console.print(f"[green]✓ 定时配置已设置[/green]")
        console.print(f"  开机时间: {result.get('power_on_time', 'N/A')}")
        console.print(f"  关机时间: {result.get('power_off_time', 'N/A')}")
        console.print(f"  工作日: {result.get('weekdays', [])}")
        console.print(f"  启用: {'是' if result.get('is_enabled') else '否'}")

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def cleanup_devices(
    dry_run: bool = typer.Option(True, "--dry-run", help="仅预览，不实际删除"),
    execute: bool = typer.Option(False, "--execute", help="实际执行清理")
):
    """
    清理无效设备

    默认为预览模式，使用 --execute 参数实际执行清理

    示例:
        castplay devices cleanup --dry-run
        castplay devices cleanup --execute
    """
    if dry_run and not execute:
        console.print("[yellow]预览模式：仅显示将被清理的设备，使用 --execute 实际执行[/yellow]\n")

    try:
        if execute:
            result = api_client.cleanup_devices()
            deleted_count = result.get("deleted_count", 0)
            console.print(f"[green]✓ 已清理 {deleted_count} 个无效设备[/green]")
        else:
            # 获取设备列表并分析
            result = api_client.list_devices(limit=100)
            devices = result.get("items", [])

            # 分析需要清理的设备
            from datetime import datetime, timedelta, timezone
            threshold = datetime.now(timezone.utc) - timedelta(days=7)

            to_cleanup = []
            for device in devices:
                is_test = 'test' in device.get('device_name', '').lower()
                last_online = device.get('last_online')
                if last_online:
                    try:
                        last_online_dt = datetime.fromisoformat(last_online.replace('Z', '+00:00'))
                        is_abandoned = last_online_dt < threshold
                    except Exception:
                        is_abandoned = False
                else:
                    is_abandoned = True

                if is_test or is_abandoned:
                    to_cleanup.append(device)

            if not to_cleanup:
                console.print("[green]没有需要清理的设备[/green]")
                return

            table = Table(title=f"待清理设备 ({len(to_cleanup)} 个)")
            table.add_column("ID", style="cyan")
            table.add_column("名称", style="red")
            table.add_column("原因", style="yellow")

            for device in to_cleanup:
                reasons = []
                if 'test' in device.get('device_name', '').lower():
                    reasons.append("测试设备")
                if device.get('last_online'):
                    reasons.append("长期离线")
                else:
                    reasons.append("无在线记录")

                table.add_row(
                    str(device.get('id')),
                    device.get('device_name'),
                    ", ".join(reasons)
                )

            console.print(table)
            console.print(f"\n使用 [bold]castplay devices cleanup --execute[/bold] 执行清理")

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)
