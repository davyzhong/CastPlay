"""
排程管理命令

提供设备播放列表时间排程的 CLI 管理功能
"""
import typer
from rich.console import Console
from rich.table import Table
from typing import Optional, List
from datetime import datetime

from cli.api_client import api_client, APIError
from cli.config import config_manager

console = Console()

# 创建 schedules 命令组
app = typer.Typer(name="schedules", help="排程管理命令")


def parse_weekdays(weekdays_str: str) -> List[int]:
    """解析星期字符串为列表"""
    if not weekdays_str:
        return []
    return [int(d.strip()) for d in weekdays_str.split(",")]


def format_weekdays(weekdays: List[int]) -> str:
    """格式化星期列表为可读字符串"""
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    if not weekdays:
        return "每天"
    return ", ".join([weekday_names[i] for i in weekdays if 0 <= i <= 6])


def format_time(time_str: str) -> str:
    """格式化时间为 HH:MM:SS 格式（API 需要）"""
    if not time_str:
        return time_str
    # 如果只有 HH:MM，补充秒数
    if len(time_str) == 5 and ":" in time_str:
        return f"{time_str}:00"
    return time_str


# ==================== 导出函数（供 main.py 使用）====================

def list_schedules(device_id: Optional[int] = None, format: str = "table", limit: int = 50):
    """列出排程规则（供 main.py 调用）"""
    try:
        # API requires device_id, if not provided show all devices first
        if device_id is None:
            console.print("[yellow]提示: 需要指定设备 ID 才能查看排程[/yellow]")
            console.print("示例: castplay schedules list --device-id 121")
            console.print("\n可用设备:")
            devices = api_client.list_devices(limit=10)
            for device in devices.get("items", devices)[:5]:
                console.print(f"  - ID {device.get('id')}: {device.get('name', 'N/A')}")
            return

        result = api_client.list_schedules(device_id=device_id, skip=0, limit=limit)
        schedules = result if isinstance(result, list) else result.get("schedules", result.get("items", []))
        total = len(schedules)

        if format == "json":
            import json
            console.print_json(json.dumps({"schedules": schedules, "total": total}))
        else:
            table = Table(title=f"排程列表 (共 {total} 条)")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("设备", style="green")
            table.add_column("播放列表", style="blue")
            table.add_column("时间", style="yellow")
            table.add_column("星期", style="magenta")
            table.add_column("状态", style="bold")

            for schedule in schedules:
                device_name = schedule.get("device_name") or f"设备 {schedule.get('device_id', 'N/A')}"
                playlist_name = schedule.get("playlist_name") or f"播放列表 {schedule.get('playlist_id', 'N/A')}"
                start_time = schedule.get("start_time", "N/A")
                end_time = schedule.get("end_time", "N/A")
                time_str = f"{start_time} - {end_time}"
                weekdays = schedule.get("weekdays", [])
                weekdays_str = format_weekdays(weekdays)
                is_active = schedule.get("is_active", True)
                status = "[green]激活[/green]" if is_active else "[dim]未激活[/dim]"

                table.add_row(
                    str(schedule.get("id")),
                    device_name,
                    playlist_name,
                    time_str,
                    weekdays_str,
                    status
                )

            console.print(table)

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]请求失败: {str(e)}[/red]")
        raise typer.Exit(1)


def get_schedule(schedule_id: int):
    """获取排程详情（供 main.py 调用）"""
    try:
        schedule = api_client.get_schedule(schedule_id)
        console.print(f"\n[bold]排程详情[/bold]")
        console.print(f"  ID: {schedule.get('id')}")
        console.print(f"  设备: {schedule.get('device_name', 'N/A')} (ID: {schedule.get('device_id')})")
        console.print(f"  播放列表: {schedule.get('playlist_name', 'N/A')} (ID: {schedule.get('playlist_id')})")
        console.print(f"  开始时间: {schedule.get('start_time', 'N/A')}")
        console.print(f"  结束时间: {schedule.get('end_time', 'N/A')}")
        console.print(f"  星期: {format_weekdays(schedule.get('weekdays', []))}")
        console.print(f"  状态: {'激活' if schedule.get('is_active') else '未激活'}")
        console.print(f"  创建时间: {schedule.get('created_at', 'N/A')}")
        console.print()
    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def create_schedule(
    device_id: int,
    playlist_id: int,
    start_time: str,
    end_time: str,
    weekdays: Optional[str] = None
):
    """创建排程规则（供 main.py 调用）"""
    try:
        weekdays_list = parse_weekdays(weekdays) if weekdays else None
        result = api_client.create_schedule(
            device_id, playlist_id,
            format_time(start_time), format_time(end_time),
            weekdays_list
        )
        console.print(f"[green]✓ 排程创建成功[/green]")
        console.print(f"  ID: {result.get('id')}")
        console.print(f"  设备 ID: {device_id}")
        console.print(f"  播放列表 ID: {playlist_id}")
        console.print(f"  时间: {start_time} - {end_time}")
        if weekdays_list:
            console.print(f"  星期: {format_weekdays(weekdays_list)}")
    except APIError as e:
        console.print(f"[red]创建失败: {e.detail}[/red]")
        raise typer.Exit(1)


def update_schedule(
    schedule_id: int,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    weekdays: Optional[str] = None,
    playlist_id: Optional[int] = None
):
    """更新排程规则（供 main.py 调用）"""
    try:
        weekdays_list = parse_weekdays(weekdays) if weekdays else None

        if not any([start_time, end_time, playlist_id, weekdays]):
            console.print("[yellow]没有指定要更新的字段[/yellow]")
            return

        result = api_client.update_schedule(
            schedule_id,
            format_time(start_time) if start_time else None,
            format_time(end_time) if end_time else None,
            weekdays_list,
            playlist_id
        )
        console.print(f"[green]✓ 排程 {schedule_id} 更新成功[/green]")
    except APIError as e:
        console.print(f"[red]更新失败: {e.detail}[/red]")
        raise typer.Exit(1)


def delete_schedule(schedule_id: int, force: bool = False):
    """删除排程规则（供 main.py 调用）"""
    try:
        if not force:
            schedule = api_client.get_schedule(schedule_id)
            console.print(f"即将删除排程:")
            console.print(f"  ID: {schedule_id}")
            console.print(f"  设备: {schedule.get('device_name', 'N/A')}")
            console.print(f"  时间: {schedule.get('start_time')} - {schedule.get('end_time')}")
            confirm = typer.confirm("确认删除?")
            if not confirm:
                console.print("[yellow]已取消[/yellow]")
                return

        api_client.delete_schedule(schedule_id)
        console.print(f"[green]✓ 排程 {schedule_id} 已删除[/green]")
    except APIError as e:
        console.print(f"[red]删除失败: {e.detail}[/red]")
        raise typer.Exit(1)


def get_active_schedule(device_id: int):
    """查看设备当前激活的排程（供 main.py 调用）"""
    try:
        result = api_client.get_active_schedule(device_id)
        if not result:
            console.print(f"[dim]设备 {device_id} 当前没有激活的排程[/dim]")
            return

        schedule = result if isinstance(result, dict) else result[0] if result else None
        if not schedule:
            console.print(f"[dim]设备 {device_id} 当前没有激活的排程[/dim]")
            return

        console.print(f"\n[bold]设备 {device_id} 当前激活的排程[/bold]")
        console.print(f"  排程 ID: {schedule.get('id')}")
        console.print(f"  播放列表: {schedule.get('playlist_name', 'N/A')}")
        console.print(f"  时间: {schedule.get('start_time')} - {schedule.get('end_time')}")
        console.print(f"  星期: {format_weekdays(schedule.get('weekdays', []))}")
        console.print()
    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


def enable_schedule(schedule_id: int):
    """启用排程（供 main.py 调用）"""
    try:
        result = api_client.update_schedule(schedule_id, is_active=True)
        console.print(f"[green]✓ 排程 {schedule_id} 已启用[/green]")
    except APIError as e:
        console.print(f"[red]启用失败: {e.detail}[/red]")
        raise typer.Exit(1)


def disable_schedule(schedule_id: int):
    """禁用排程（供 main.py 调用）"""
    try:
        result = api_client.update_schedule(schedule_id, is_active=False)
        console.print(f"[green]✓ 排程 {schedule_id} 已禁用[/green]")
    except APIError as e:
        console.print(f"[red]禁用失败: {e.detail}[/red]")
        raise typer.Exit(1)


# ==================== CLI 命令定义 ====================

@app.command("list")
def list_schedules_cmd(
    device_id: Optional[int] = typer.Option(None, "--device-id", "-d", help="按设备 ID 过滤"),
    format: str = typer.Option("table", "--format", "-f", help="输出格式: table, json"),
    limit: int = typer.Option(50, "--limit", "-l", help="返回数量")
):
    """
    列出排程规则

    示例:
        castplay schedules list --device-id 1
        castplay schedules list -d 1 --format json
    """
    try:
        # API requires device_id
        if device_id is None:
            console.print("[yellow]提示: 需要指定设备 ID[/yellow]")
            console.print("示例: castplay schedules list --device-id 121")
            console.print("\n可用设备:")
            devices = api_client.list_devices(limit=10)
            for device in devices.get("items", devices)[:5]:
                console.print(f"  - ID {device.get('id')}: {device.get('name', 'N/A')}")
            return

        result = api_client.list_schedules(device_id=device_id, skip=0, limit=limit)
        schedules = result if isinstance(result, list) else result.get("schedules", result.get("items", []))
        total = len(schedules)

        if format == "json":
            import json
            console.print_json(json.dumps({"schedules": schedules, "total": total}))
        else:
            table = Table(title=f"排程列表 (共 {total} 条)")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("设备", style="green")
            table.add_column("播放列表", style="blue")
            table.add_column("时间", style="yellow")
            table.add_column("星期", style="magenta")
            table.add_column("状态", style="bold")

            for schedule in schedules:
                # 设备和播放列表
                device_name = schedule.get("device_name") or f"设备 {schedule.get('device_id', 'N/A')}"
                playlist_name = schedule.get("playlist_name") or f"播放列表 {schedule.get('playlist_id', 'N/A')}"

                # 时间
                start_time = schedule.get("start_time", "N/A")
                end_time = schedule.get("end_time", "N/A")
                time_str = f"{start_time} - {end_time}"

                # 星期
                weekdays = schedule.get("weekdays", [])
                weekdays_str = format_weekdays(weekdays)

                # 状态
                is_active = schedule.get("is_active", True)
                status = "[green]激活[/green]" if is_active else "[dim]未激活[/dim]"

                table.add_row(
                    str(schedule.get("id")),
                    device_name,
                    playlist_name,
                    time_str,
                    weekdays_str,
                    status
                )

            console.print(table)

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]请求失败: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command("get")
def get_schedule_cmd(
    schedule_id: int = typer.Argument(..., help="排程 ID"),
    format: str = typer.Option("table", "--format", "-f", help="输出格式: table, json")
):
    """
    获取排程详情

    示例:
        castplay schedules get 1
        castplay schedules get 1 --format json
    """
    try:
        schedule = api_client.get_schedule(schedule_id)

        if format == "json":
            import json
            console.print_json(json.dumps(schedule, indent=2, ensure_ascii=False))
        else:
            console.print(f"\n[bold]排程详情[/bold]")
            console.print(f"  ID: {schedule.get('id')}")
            console.print(f"  设备: {schedule.get('device_name', 'N/A')} (ID: {schedule.get('device_id')})")
            console.print(f"  播放列表: {schedule.get('playlist_name', 'N/A')} (ID: {schedule.get('playlist_id')})")
            console.print(f"  开始时间: {schedule.get('start_time', 'N/A')}")
            console.print(f"  结束时间: {schedule.get('end_time', 'N/A')}")
            console.print(f"  星期: {format_weekdays(schedule.get('weekdays', []))}")
            console.print(f"  状态: {'激活' if schedule.get('is_active') else '未激活'}")
            console.print(f"  创建时间: {schedule.get('created_at', 'N/A')}")
            console.print()

    except APIError as e:
        if "not found" in str(e.detail).lower():
            console.print(f"[red]错误: 排程 {schedule_id} 不存在[/red]")
        else:
            console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


@app.command("create")
def create_schedule_cmd(
    device_id: int = typer.Option(..., "--device-id", "-d", help="设备 ID"),
    playlist_id: int = typer.Option(..., "--playlist-id", "-p", help="播放列表 ID"),
    start_time: str = typer.Option(..., "--start-time", "-s", help="开始时间 (HH:MM)"),
    end_time: str = typer.Option(..., "--end-time", "-e", help="结束时间 (HH:MM)"),
    weekdays: Optional[str] = typer.Option(
        None, "--weekdays", "-w",
        help="工作日 (0=周一, 1=周二, ..., 6=周日)，逗号分隔，如 0,1,2,3,4 表示工作日"
    )
):
    """
    创建排程规则

    示例:
        castplay schedules create -d 1 -p 2 -s 08:00 -e 18:00 -w 0,1,2,3,4
        castplay schedules create --device-id 1 --playlist-id 2 --start-time 08:00 --end-time 18:00
    """
    try:
        # 解析星期
        weekdays_list = parse_weekdays(weekdays) if weekdays else None
        result = api_client.create_schedule(
            device_id, playlist_id,
            format_time(start_time), format_time(end_time),
            weekdays_list
        )

        console.print(f"[green]✓ 排程创建成功[/green]")
        console.print(f"  ID: {result.get('id')}")
        console.print(f"  设备 ID: {device_id}")
        console.print(f"  播放列表 ID: {playlist_id}")
        console.print(f"  时间: {start_time} - {end_time}")
        if weekdays_list:
            console.print(f"  星期: {format_weekdays(weekdays_list)}")

    except APIError as e:
        console.print(f"[red]创建失败: {e.detail}[/red]")
        raise typer.Exit(1)


@app.command("update")
def update_schedule_cmd(
    schedule_id: int = typer.Argument(..., help="排程 ID"),
    start_time: Optional[str] = typer.Option(None, "--start-time", "-s", help="开始时间 (HH:MM)"),
    end_time: Optional[str] = typer.Option(None, "--end-time", "-e", help="结束时间 (HH:MM)"),
    weekdays: Optional[str] = typer.Option(None, "--weekdays", "-w", help="工作日 (0-6, 逗号分隔)"),
    playlist_id: Optional[int] = typer.Option(None, "--playlist-id", "-p", help="播放列表 ID")
):
    """
    更新排程规则

    示例:
        castplay schedules update 1 --start-time 09:00
        castplay schedules update 1 --end-time 20:00 --weekdays 0,1,2,3,4,5,6
    """
    try:
        weekdays_list = parse_weekdays(weekdays) if weekdays else None

        if not any([start_time, end_time, playlist_id, weekdays]):
            console.print("[yellow]没有指定要更新的字段[/yellow]")
            return

        result = api_client.update_schedule(
            schedule_id,
            format_time(start_time) if start_time else None,
            format_time(end_time) if end_time else None,
            weekdays_list,
            playlist_id
        )

        console.print(f"[green]✓ 排程 {schedule_id} 更新成功[/green]")
        if start_time:
            console.print(f"  开始时间: {start_time}")
        if end_time:
            console.print(f"  结束时间: {end_time}")
        if weekdays:
            console.print(f"  星期: {format_weekdays(parse_weekdays(weekdays))}")

    except APIError as e:
        console.print(f"[red]更新失败: {e.detail}[/red]")
        raise typer.Exit(1)


@app.command("delete")
def delete_schedule_cmd(
    schedule_id: int = typer.Argument(..., help="排程 ID"),
    force: bool = typer.Option(False, "--force", "-f", help="强制删除，不确认")
):
    """
    删除排程规则

    示例:
        castplay schedules delete 1
        castplay schedules delete 1 --force
    """
    try:
        # 先获取排程信息用于确认
        if not force:
            schedule = api_client.get_schedule(schedule_id)
            console.print(f"即将删除排程:")
            console.print(f"  ID: {schedule_id}")
            console.print(f"  设备: {schedule.get('device_name', 'N/A')}")
            console.print(f"  时间: {schedule.get('start_time')} - {schedule.get('end_time')}")

            confirm = typer.confirm("确认删除?")
            if not confirm:
                console.print("[yellow]已取消[/yellow]")
                return

        api_client.delete_schedule(schedule_id)
        console.print(f"[green]✓ 排程 {schedule_id} 已删除[/green]")

    except APIError as e:
        console.print(f"[red]删除失败: {e.detail}[/red]")
        raise typer.Exit(1)


@app.command("active")
def get_active_schedule_cmd(
    device_id: int = typer.Option(..., "--device-id", "-d", help="设备 ID")
):
    """
    查看设备当前激活的排程

    示例:
        castplay schedules active --device-id 1
    """
    try:
        result = api_client.get_active_schedule(device_id)

        if not result:
            console.print(f"[dim]设备 {device_id} 当前没有激活的排程[/dim]")
            return

        schedule = result if isinstance(result, dict) else result[0] if result else None
        if not schedule:
            console.print(f"[dim]设备 {device_id} 当前没有激活的排程[/dim]")
            return

        console.print(f"\n[bold]设备 {device_id} 当前激活的排程[/bold]")
        console.print(f"  排程 ID: {schedule.get('id')}")
        console.print(f"  播放列表: {schedule.get('playlist_name', 'N/A')}")
        console.print(f"  时间: {schedule.get('start_time')} - {schedule.get('end_time')}")
        console.print(f"  星期: {format_weekdays(schedule.get('weekdays', []))}")
        console.print()

    except APIError as e:
        console.print(f"[red]错误: {e.detail}[/red]")
        raise typer.Exit(1)


@app.command("enable")
def enable_schedule_cmd(
    schedule_id: int = typer.Argument(..., help="排程 ID")
):
    """
    启用排程

    示例:
        castplay schedules enable 1
    """
    try:
        result = api_client.update_schedule(schedule_id, is_active=True)
        console.print(f"[green]✓ 排程 {schedule_id} 已启用[/green]")
    except APIError as e:
        console.print(f"[red]启用失败: {e.detail}[/red]")
        raise typer.Exit(1)


@app.command("disable")
def disable_schedule_cmd(
    schedule_id: int = typer.Argument(..., help="排程 ID")
):
    """
    禁用排程

    示例:
        castplay schedules disable 1
    """
    try:
        result = api_client.update_schedule(schedule_id, is_active=False)
        console.print(f"[green]✓ 排程 {schedule_id} 已禁用[/green]")
    except APIError as e:
        console.print(f"[red]禁用失败: {e.detail}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
