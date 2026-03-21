#!/usr/bin/env python3
"""
CastPlay CLI - 命令行管理工具

用于 AI 助手和高级用户管理 CastPlay 系统的命令行接口

使用方法:
    castplay --help
    castplay devices list
    castplay control pause <device_id>
    castplay status
"""
import typer
from rich.console import Console
from typing import Optional

from cli import __version__
from cli.config import config_manager

# 创建主应用
app = typer.Typer(
    name="castplay",
    help="CastPlay 数字标牌管理系统命令行工具",
    no_args_is_help=True
)

# Rich 控制台
console = Console()

# 子命令应用
config_app = typer.Typer(help="配置管理")
devices_app = typer.Typer(help="设备管理")
playlists_app = typer.Typer(help="播放列表管理")
control_app = typer.Typer(help="播放控制")
status_app = typer.Typer(help="状态查询")
media_app = typer.Typer(help="媒体管理")
db_app = typer.Typer(help="数据库管理")
schedules_app = typer.Typer(help="排程管理")
server_app = typer.Typer(help="服务器管理")

# 注册子命令
app.add_typer(config_app, name="config")
app.add_typer(devices_app, name="devices")
app.add_typer(playlists_app, name="playlists")
app.add_typer(control_app, name="control")
app.add_typer(status_app, name="status")
app.add_typer(media_app, name="media")
app.add_typer(db_app, name="db")
app.add_typer(schedules_app, name="schedules")
app.add_typer(server_app, name="server")


# ==================== 配置命令 ====================

@config_app.command("set")
def config_set(
    server: Optional[str] = typer.Option(None, "--server", "-s", help="服务器地址"),
    token: Optional[str] = typer.Option(None, "--token", "-t", help="认证令牌"),
    timeout: Optional[int] = typer.Option(None, "--timeout", help="请求超时时间（秒）")
):
    """设置配置项"""
    if server:
        config_manager.set_server(server)
        console.print(f"[green]✓[/green] 服务器地址已设置为: {server}")

    if token:
        config_manager.set_token(token)
        console.print("[green]✓[/green] 认证令牌已设置")

    if timeout:
        config_manager.set_timeout(timeout)
        console.print(f"[green]✓[/green] 请求超时时间已设置为: {timeout} 秒")

    if not any([server, token, timeout]):
        console.print("[yellow]请指定要设置的配置项[/yellow]")
        console.print("示例: castplay config set --server http://localhost:8000")


@config_app.command("show")
def config_show():
    """显示当前配置"""
    config = config_manager.config
    console.print("\n[bold]CastPlay CLI 配置[/bold]")
    console.print(f"  配置文件: {config_manager.get_config_path()}")
    console.print(f"  服务器地址: {config.server_url}")
    console.print(f"  认证令牌: {'已设置' if config.token else '未设置'}")
    console.print(f"  请求超时: {config.timeout} 秒\n")


@config_app.command("login")
def config_login(
    username: str = typer.Option(..., "--username", "-u", prompt=True, help="用户名"),
    password: str = typer.Option(..., "--password", "-p", prompt=True, hide_input=True, help="密码"),
    server: Optional[str] = typer.Option(None, "--server", "-s", help="服务器地址")
):
    """登录并保存认证令牌"""
    from cli.api_client import APIClient, APIError

    # 如果指定了服务器地址，先设置
    if server:
        config_manager.set_server(server)

    client = APIClient()
    try:
        result = client.login(username, password)
        token = result.get("access_token")
        if token:
            config_manager.set_token(token)
            user = result.get("user", {})
            console.print(f"\n[green]✓ 登录成功[/green]")
            console.print(f"  用户: {user.get('username', 'N/A')}")
            console.print(f"  令牌已保存到: {config_manager.get_config_path()}\n")
        else:
            console.print("[red]✗ 登录失败：未获取到令牌[/red]")
            raise typer.Exit(1)
    except APIError as e:
        console.print(f"[red]✗ 登录失败: {e.detail}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗ 连接失败: {str(e)}[/red]")
        raise typer.Exit(1)


@config_app.command("logout")
def config_logout():
    """清除认证令牌"""
    config_manager.clear_token()
    console.print("[green]✓ 认证令牌已清除[/green]")


# ==================== 版本命令 ====================

@app.command("version")
def show_version():
    """显示版本信息"""
    console.print(f"CastPlay CLI v{__version__}")


# ==================== 注册设备命令 ====================

# 设备命令
@devices_app.command("list")
def devices_list(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="过滤状态: online, offline, disabled"),
    format: str = typer.Option("table", "--format", "-f", help="输出格式: table, json"),
    limit: int = typer.Option(50, "--limit", "-l", help="返回数量")
):
    """列出所有设备"""
    from cli.commands.devices import list_devices
    list_devices(status=status, format=format, limit=limit)


@devices_app.command("get")
def devices_get(
    device_id: int = typer.Argument(..., help="设备 ID")
):
    """获取设备详情"""
    from cli.commands.devices import get_device
    get_device(device_id=device_id)


@devices_app.command("disable")
def devices_disable(
    device_id: int = typer.Argument(..., help="设备 ID")
):
    """禁用设备"""
    from cli.commands.devices import disable_device
    disable_device(device_id=device_id)


@devices_app.command("enable")
def devices_enable(
    device_id: int = typer.Argument(..., help="设备 ID")
):
    """启用设备"""
    from cli.commands.devices import enable_device
    enable_device(device_id=device_id)


@devices_app.command("schedule")
def devices_schedule(
    device_id: int = typer.Argument(..., help="设备 ID"),
    on_time: Optional[str] = typer.Option(None, "--on-time", help="开机时间 (HH:MM)"),
    off_time: Optional[str] = typer.Option(None, "--off-time", help="关机时间 (HH:MM)"),
    weekdays: Optional[str] = typer.Option(None, "--weekdays", "-w", help="工作日 (1,2,3,4,5 表示周一到周五)"),
    disable: bool = typer.Option(False, "--disable", help="禁用定时配置")
):
    """设置设备定时配置"""
    from cli.commands.devices import set_schedule
    set_schedule(device_id=device_id, on_time=on_time, off_time=off_time, weekdays=weekdays, disable=disable)


@devices_app.command("cleanup")
def devices_cleanup(
    dry_run: bool = typer.Option(True, "--dry-run", help="仅预览，不实际删除"),
    execute: bool = typer.Option(False, "--execute", help="实际执行清理")
):
    """清理无效设备"""
    from cli.commands.devices import cleanup_devices
    cleanup_devices(dry_run=dry_run, execute=execute)


# ==================== 注册播放列表命令 ====================

@playlists_app.command("list")
def playlists_list(
    format: str = typer.Option("table", "--format", "-f", help="输出格式: table, json"),
    limit: int = typer.Option(50, "--limit", "-l", help="返回数量")
):
    """列出所有播放列表"""
    from cli.commands.playlists import list_playlists
    list_playlists(format=format, limit=limit)


@playlists_app.command("get")
def playlists_get(
    playlist_id: int = typer.Argument(..., help="播放列表 ID"),
    format: str = typer.Option("table", "--format", "-f", help="输出格式: table, json")
):
    """获取播放列表详情"""
    from cli.commands.playlists import get_playlist
    get_playlist(playlist_id=playlist_id, format=format)


@playlists_app.command("create")
def playlists_create(
    name: str = typer.Argument(..., help="播放列表名称"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="播放列表描述")
):
    """创建播放列表"""
    from cli.commands.playlists import create_playlist
    create_playlist(name=name, description=description)


@playlists_app.command("delete")
def playlists_delete(
    playlist_id: int = typer.Argument(..., help="播放列表 ID"),
    force: bool = typer.Option(False, "--force", "-f", help="强制删除（即使有设备关联）")
):
    """删除播放列表"""
    from cli.commands.playlists import delete_playlist
    delete_playlist(playlist_id=playlist_id, force=force)


@playlists_app.command("assign")
def playlists_assign(
    playlist_id: int = typer.Argument(..., help="播放列表 ID"),
    device_id: int = typer.Argument(..., help="设备 ID")
):
    """分配播放列表到设备"""
    from cli.commands.playlists import assign_playlist
    assign_playlist(playlist_id=playlist_id, device_id=device_id)


@playlists_app.command("unassign")
def playlists_unassign(
    playlist_id: int = typer.Argument(..., help="播放列表 ID"),
    device_id: int = typer.Argument(..., help="设备 ID")
):
    """取消播放列表分配"""
    from cli.commands.playlists import unassign_playlist
    unassign_playlist(playlist_id=playlist_id, device_id=device_id)


@playlists_app.command("activate")
def playlists_activate(
    playlist_id: int = typer.Argument(..., help="播放列表 ID"),
    device_id: int = typer.Argument(..., help="设备 ID")
):
    """激活设备上的播放列表"""
    from cli.commands.playlists import activate_playlist
    activate_playlist(playlist_id=playlist_id, device_id=device_id)


@playlists_app.command("deactivate")
def playlists_deactivate(
    playlist_id: int = typer.Argument(..., help="播放列表 ID"),
    device_id: int = typer.Argument(..., help="设备 ID")
):
    """停用设备上的播放列表"""
    from cli.commands.playlists import deactivate_playlist
    deactivate_playlist(playlist_id=playlist_id, device_id=device_id)


@playlists_app.command("items")
def playlists_items(
    playlist_id: int = typer.Argument(..., help="播放列表 ID"),
    format: str = typer.Option("table", "--format", "-f", help="输出格式: table, json")
):
    """列出播放列表中的媒体项"""
    from cli.commands.playlists import list_items
    list_items(playlist_id=playlist_id, format=format)


@playlists_app.command("add-item")
def playlists_add_item(
    playlist_id: int = typer.Argument(..., help="播放列表 ID"),
    media_id: int = typer.Option(..., "--media-id", "-m", help="媒体 ID"),
    duration: int = typer.Option(10, "--duration", "-d", help="播放时长(秒)"),
    order: Optional[int] = typer.Option(None, "--order", "-o", help="显示顺序")
):
    """添加媒体到播放列表"""
    from cli.commands.playlists import add_item
    add_item(playlist_id=playlist_id, media_id=media_id, duration=duration, order=order)


@playlists_app.command("add-items")
def playlists_add_items(
    playlist_id: int = typer.Argument(..., help="播放列表 ID"),
    media_ids: str = typer.Option(..., "--media-ids", "-m", help="媒体 ID 列表，逗号分隔"),
    duration: int = typer.Option(10, "--duration", "-d", help="默认播放时长(秒)")
):
    """批量添加媒体到播放列表"""
    from cli.commands.playlists import add_items_batch
    add_items_batch(playlist_id=playlist_id, media_ids=media_ids, duration=duration)


@playlists_app.command("remove-item")
def playlists_remove_item(
    playlist_id: int = typer.Argument(..., help="播放列表 ID"),
    item_id: int = typer.Argument(..., help="播放列表项 ID")
):
    """从播放列表移除媒体项"""
    from cli.commands.playlists import remove_item
    remove_item(playlist_id=playlist_id, item_id=item_id)


@playlists_app.command("update-item")
def playlists_update_item(
    playlist_id: int = typer.Argument(..., help="播放列表 ID"),
    item_id: int = typer.Argument(..., help="播放列表项 ID"),
    duration: Optional[int] = typer.Option(None, "--duration", "-d", help="播放时长(秒)"),
    order: Optional[int] = typer.Option(None, "--order", "-o", help="显示顺序")
):
    """更新播放列表项"""
    from cli.commands.playlists import update_item
    update_item(playlist_id=playlist_id, item_id=item_id, duration=duration, order=order)


@playlists_app.command("reorder")
def playlists_reorder(
    playlist_id: int = typer.Argument(..., help="播放列表 ID"),
    order: str = typer.Option(..., "--order", "-o", help="新的顺序，项 ID 逗号分隔")
):
    """重新排序播放列表项"""
    from cli.commands.playlists import reorder_items
    reorder_items(playlist_id=playlist_id, order=order)


# ==================== 注册控制命令 ====================

@control_app.command("pause")
def control_pause_cmd(
    device_id: int = typer.Argument(..., help="设备 ID")
):
    """暂停播放"""
    from cli.commands.control import pause
    pause(device_id=device_id)


@control_app.command("resume")
def control_resume_cmd(
    device_id: int = typer.Argument(..., help="设备 ID")
):
    """恢复播放"""
    from cli.commands.control import resume
    resume(device_id=device_id)


@control_app.command("volume")
def control_volume_cmd(
    device_id: int = typer.Argument(..., help="设备 ID"),
    level: int = typer.Argument(..., help="音量级别 (0-100)")
):
    """调节音量"""
    from cli.commands.control import volume
    volume(device_id=device_id, level=level)


@control_app.command("reload")
def control_reload_cmd(
    device_id: int = typer.Argument(..., help="设备 ID")
):
    """重新加载播放列表"""
    from cli.commands.control import reload as reload_func
    reload_func(device_id=device_id)


@control_app.command("next")
def control_next_cmd(
    device_id: int = typer.Argument(..., help="设备 ID")
):
    """切换到下一个媒体"""
    from cli.commands.control import next_media
    next_media(device_id=device_id)


@control_app.command("prev")
def control_prev_cmd(
    device_id: int = typer.Argument(..., help="设备 ID")
):
    """切换到上一个媒体"""
    from cli.commands.control import prev_media
    prev_media(device_id=device_id)


@control_app.command("switch")
def control_switch_cmd(
    device_id: int = typer.Argument(..., help="设备 ID"),
    playlist_id: int = typer.Argument(..., help="目标播放列表 ID")
):
    """切换播放列表"""
    from cli.commands.control import switch_playlist
    switch_playlist(device_id=device_id, playlist_id=playlist_id)


@control_app.command("reboot")
def control_reboot_cmd(
    device_id: int = typer.Argument(..., help="设备 ID"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="确认重启")
):
    """重启设备"""
    from cli.commands.control import reboot
    reboot(device_id=device_id, confirm=confirm)


# ==================== 注册状态命令 ====================

@status_app.callback(invoke_without_command=True)
def status_main(
    ctx: typer.Context,
    format: str = typer.Option("table", "--format", "-f", help="输出格式: table, json")
):
    """系统概览（默认命令）"""
    if ctx.invoked_subcommand is None:
        from cli.commands.status import overview
        overview(format=format)


@status_app.command("device")
def status_device(
    device_id: int = typer.Argument(..., help="设备 ID"),
    format: str = typer.Option("table", "--format", "-f", help="输出格式: table, json")
):
    """查询设备播放状态"""
    from cli.commands.status import device_status
    device_status(device_id=device_id, format=format)


@status_app.command("online")
def status_online(
    format: str = typer.Option("table", "--format", "-f", help="输出格式: table, json")
):
    """显示在线设备列表"""
    from cli.commands.status import online_devices
    online_devices(format=format)


# ==================== 注册媒体命令 ====================

@media_app.command("list")
def media_list(
    type: Optional[str] = typer.Option(None, "--type", "-t", help="过滤类型: image, video, ppt"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="过滤状态: ready, processing, failed"),
    format: str = typer.Option("table", "--format", "-f", help="输出格式: table, json"),
    limit: int = typer.Option(50, "--limit", "-l", help="返回数量")
):
    """列出媒体文件"""
    from cli.commands.media import list_media
    list_media(type=type, status=status, format=format, limit=limit)


@media_app.command("get")
def media_get(
    media_id: int = typer.Argument(..., help="媒体文件 ID"),
    format: str = typer.Option("table", "--format", "-f", help="输出格式: table, json")
):
    """获取媒体文件详情"""
    from cli.commands.media import get_media
    get_media(media_id=media_id, format=format)


@media_app.command("delete")
def media_delete(
    media_id: int = typer.Argument(..., help="媒体文件 ID"),
    force: bool = typer.Option(False, "--force", "-f", help="强制删除（不确认）")
):
    """删除媒体文件"""
    from cli.commands.media import delete_media
    delete_media(media_id=media_id, force=force)


@media_app.command("upload")
def media_upload(
    file_path: str = typer.Argument(..., help="要上传的文件路径"),
    file_type: Optional[str] = typer.Option(None, "--type", "-t", help="文件类型: image, video, ppt (自动检测)"),
    slide_duration: int = typer.Option(5, "--duration", "-d", help="PPT 幻灯片间隔时长(秒)")
):
    """上传媒体文件"""
    from cli.commands.media import upload_media
    upload_media(file_path=file_path, file_type=file_type, slide_duration=slide_duration)


# ==================== 注册数据库命令 ====================

@db_app.command("backup")
def db_backup(
    output: Optional[str] = typer.Option(None, "--output", "-o", help="备份文件输出路径")
):
    """备份数据库"""
    from cli.commands.db import backup
    backup(output=output)


@db_app.command("cleanup")
def db_cleanup(
    days: int = typer.Option(7, "--days", "-d", help="保留最近 N 天的备份"),
    dry_run: bool = typer.Option(True, "--dry-run", help="仅预览，不实际删除"),
    execute: bool = typer.Option(False, "--execute", help="实际执行清理")
):
    """清理旧的备份文件"""
    from cli.commands.db import cleanup_backups
    cleanup_backups(days=days, dry_run=dry_run, execute=execute)


# ==================== 注册排程命令 ====================

@schedules_app.command("list")
def schedules_list(
    device_id: Optional[int] = typer.Option(None, "--device-id", "-d", help="按设备 ID 过滤"),
    format: str = typer.Option("table", "--format", "-f", help="输出格式: table, json"),
    limit: int = typer.Option(50, "--limit", "-l", help="返回数量")
):
    """列出排程规则"""
    from cli.commands.schedules import list_schedules
    list_schedules(device_id=device_id, format=format, limit=limit)


@schedules_app.command("get")
def schedules_get(
    schedule_id: int = typer.Argument(..., help="排程 ID")
):
    """获取排程详情"""
    from cli.commands.schedules import get_schedule
    get_schedule(schedule_id=schedule_id)


@schedules_app.command("create")
def schedules_create(
    device_id: int = typer.Option(..., "--device-id", "-d", help="设备 ID"),
    playlist_id: int = typer.Option(..., "--playlist-id", "-p", help="播放列表 ID"),
    start_time: str = typer.Option(..., "--start-time", "-s", help="开始时间 (HH:MM)"),
    end_time: str = typer.Option(..., "--end-time", "-e", help="结束时间 (HH:MM)"),
    weekdays: Optional[str] = typer.Option(None, "--weekdays", "-w", help="工作日 (0-6, 逗号分隔)")
):
    """创建排程规则"""
    from cli.commands.schedules import create_schedule
    create_schedule(
        device_id=device_id,
        playlist_id=playlist_id,
        start_time=start_time,
        end_time=end_time,
        weekdays=weekdays
    )


@schedules_app.command("update")
def schedules_update(
    schedule_id: int = typer.Argument(..., help="排程 ID"),
    start_time: Optional[str] = typer.Option(None, "--start-time", "-s", help="开始时间 (HH:MM)"),
    end_time: Optional[str] = typer.Option(None, "--end-time", "-e", help="结束时间 (HH:MM)"),
    weekdays: Optional[str] = typer.Option(None, "--weekdays", "-w", help="工作日 (0-6, 逗号分隔)"),
    playlist_id: Optional[int] = typer.Option(None, "--playlist-id", "-p", help="播放列表 ID")
):
    """更新排程规则"""
    from cli.commands.schedules import update_schedule
    update_schedule(
        schedule_id=schedule_id,
        start_time=start_time,
        end_time=end_time,
        weekdays=weekdays,
        playlist_id=playlist_id
    )


@schedules_app.command("delete")
def schedules_delete(
    schedule_id: int = typer.Argument(..., help="排程 ID"),
    force: bool = typer.Option(False, "--force", "-f", help="强制删除，不确认")
):
    """删除排程规则"""
    from cli.commands.schedules import delete_schedule
    delete_schedule(schedule_id=schedule_id, force=force)


@schedules_app.command("active")
def schedules_active(
    device_id: int = typer.Option(..., "--device-id", "-d", help="设备 ID")
):
    """查看设备当前激活的排程"""
    from cli.commands.schedules import get_active_schedule
    get_active_schedule(device_id=device_id)


@schedules_app.command("enable")
def schedules_enable(
    schedule_id: int = typer.Argument(..., help="排程 ID")
):
    """启用排程"""
    from cli.commands.schedules import enable_schedule
    enable_schedule(schedule_id=schedule_id)


@schedules_app.command("disable")
def schedules_disable(
    schedule_id: int = typer.Argument(..., help="排程 ID")
):
    """禁用排程"""
    from cli.commands.schedules import disable_schedule
    disable_schedule(schedule_id=schedule_id)


# ==================== 注册服务器命令 ====================

@server_app.command("status")
def server_status():
    """显示服务器状态"""
    from cli.commands.server import status
    status()


@server_app.command("start")
def server_start(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="监听地址"),
    port: int = typer.Option(8000, "--port", "-p", help="监听端口"),
    reload: bool = typer.Option(False, "--reload", "-r", help="开发模式（自动重载）"),
    background: bool = typer.Option(False, "--background", "-b", help="后台运行"),
    open_browser: bool = typer.Option(False, "--open", "-o", help="打开浏览器")
):
    """启动 CastPlay 服务器"""
    from cli.commands.server import start
    start(host=host, port=port, reload=reload, background=background, open_browser=open_browser)


@server_app.command("stop")
def server_stop(
    force: bool = typer.Option(False, "--force", "-f", help="强制停止")
):
    """停止 CastPlay 服务器"""
    from cli.commands.server import stop
    stop(force=force)


@server_app.command("logs")
def server_logs(
    lines: int = typer.Option(50, "--lines", "-n", help="显示行数"),
    follow: bool = typer.Option(False, "--follow", "-f", help="实时跟踪日志")
):
    """查看服务器日志"""
    from cli.commands.server import logs
    logs(lines=lines, follow=follow)


def main():
    """入口函数"""
    app()


if __name__ == "__main__":
    main()
