"""
播放控制命令

发送播放控制指令到设备
"""
import typer
from rich.console import Console
from typing import Optional

from cli.api_client import api_client, APIError

console = Console()


def _check_device_online(device_id: int) -> bool:
    """检查设备是否在线"""
    try:
        result = api_client.get_player_status(status_filter="online")
        online_devices = result if isinstance(result, list) else result.get("items", [])
        return any(d.get("id") == device_id or d.get("device_id") == str(device_id) for d in online_devices)
    except Exception:
        return True  # 无法确认时假设在线


def pause(
    device_id: int = typer.Argument(..., help="设备 ID")
):
    """
    暂停播放

    示例:
        castplay control pause 1
    """
    try:
        result = api_client.control_pause(device_id)
        console.print(f"[green]✓ 暂停指令已发送到设备 {device_id}[/green]")
        console.print(f"  {result.get('message', 'OK')}")
    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def resume(
    device_id: int = typer.Argument(..., help="设备 ID")
):
    """
    恢复播放

    示例:
        castplay control resume 1
    """
    try:
        result = api_client.control_resume(device_id)
        console.print(f"[green]✓ 恢复播放指令已发送到设备 {device_id}[/green]")
        console.print(f"  {result.get('message', 'OK')}")
    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def volume(
    device_id: int = typer.Argument(..., help="设备 ID"),
    level: int = typer.Argument(..., help="音量级别 (0-100)")
):
    """
    调节音量

    示例:
        castplay control volume 1 80
    """
    if not 0 <= level <= 100:
        console.print("[red]错误: 音量必须在 0-100 之间[/red]")
        raise typer.Exit(1)

    try:
        result = api_client.control_volume(device_id, level)
        console.print(f"[green]✓ 音量调节指令已发送到设备 {device_id}[/green]")
        console.print(f"  音量: {level}%")
        console.print(f"  {result.get('message', 'OK')}")
    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def reload(
    device_id: int = typer.Argument(..., help="设备 ID")
):
    """
    重新加载播放列表

    示例:
        castplay control reload 1
    """
    try:
        result = api_client.control_reload(device_id)
        console.print(f"[green]✓ 重新加载指令已发送到设备 {device_id}[/green]")
        console.print(f"  {result.get('message', 'OK')}")
    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def next_media(
    device_id: int = typer.Argument(..., help="设备 ID")
):
    """
    切换到下一个媒体

    示例:
        castplay control next 1
    """
    try:
        result = api_client.control_next(device_id)
        console.print(f"[green]✓ 下一个指令已发送到设备 {device_id}[/green]")
        console.print(f"  {result.get('message', 'OK')}")
    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def prev_media(
    device_id: int = typer.Argument(..., help="设备 ID")
):
    """
    切换到上一个媒体

    示例:
        castplay control prev 1
    """
    try:
        result = api_client.control_prev(device_id)
        console.print(f"[green]✓ 上一个指令已发送到设备 {device_id}[/green]")
        console.print(f"  {result.get('message', 'OK')}")
    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def switch_playlist(
    device_id: int = typer.Argument(..., help="设备 ID"),
    playlist_id: int = typer.Argument(..., help="目标播放列表 ID")
):
    """
    切换播放列表

    示例:
        castplay control switch 1 2
    """
    try:
        result = api_client.control_switch(device_id, playlist_id)
        console.print(f"[green]✓ 切换播放列表指令已发送到设备 {device_id}[/green]")
        console.print(f"  目标播放列表: {playlist_id}")
        console.print(f"  {result.get('message', 'OK')}")
    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def reboot(
    device_id: int = typer.Argument(..., help="设备 ID"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="确认重启")
):
    """
    重启设备

    注意：此操作需要设备支持重启功能

    示例:
        castplay control reboot 1
        castplay control reboot 1 --yes
    """
    if not confirm:
        console.print("[yellow]警告: 此操作将重启设备[/yellow]")
        confirm = typer.confirm("确定要继续吗？", default=False)
        if not confirm:
            console.print("[dim]已取消[/dim]")
            raise typer.Exit(0)

    try:
        result = api_client.control_reboot(device_id)
        console.print(f"[green]✓ 重启指令已发送到设备 {device_id}[/green]")
        console.print(f"  {result.get('message', 'OK')}")
    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)
