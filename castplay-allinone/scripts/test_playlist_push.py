#!/usr/bin/env python3
"""
播放列表推送功能测试脚本

测试步骤:
1. 检查设备是否在线
2. 分配播放列表到设备
3. 观察推送通知是否发送成功
4. 更新播放列表
5. 观察增量更新通知

使用方法:
    python scripts/test_playlist_push.py --device-id web-player-test-01 --playlist-id 1
"""
import asyncio
import argparse
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.notification import NotificationService
from app.websocket.handler import manager as ws_manager
from loguru import logger


class PlaylistPushTester:
    """播放列表推送测试器"""

    def __init__(self, device_id: str, playlist_id: int):
        self.device_id = device_id
        self.playlist_id = playlist_id
        self.test_results = []

    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = f"{status} | {test_name}"
        if message:
            result += f" | {message}"
        self.test_results.append((test_name, passed, message))
        print(result)

    async def test_1_check_device_online(self):
        """测试1: 检查设备是否在线"""
        print("\n" + "=" * 60)
        print("测试 1: 检查设备在线状态")
        print("=" * 60)

        is_online = ws_manager.is_connected(self.device_id)
        online_devices = ws_manager.get_connected_devices()

        print(f"所有在线设备: {online_devices}")
        print(f"目标设备 {self.device_id}: {'在线' if is_online else '离线'}")

        self.log_result(
            "设备在线检查",
            is_online,
            f"设备 {'已连接' if is_online else '未连接，请先打开测试页面'}"
        )
        return is_online

    async def test_2_playlist_assigned(self):
        """测试2: 发送播放列表分配通知"""
        print("\n" + "=" * 60)
        print("测试 2: 播放列表分配通知")
        print("=" * 60)

        if not ws_manager.is_connected(self.device_id):
            self.log_result("播放列表分配", False, "设备未连接")
            return False

        try:
            await NotificationService.notify_playlist_assigned(
                device_id=self.device_id,
                playlist_id=self.playlist_id,
                playlist_name=f"测试播放列表-{self.playlist_id}",
                version="1.0.0",
                item_count=5,
                total_size=50000000
            )
            self.log_result("播放列表分配", True, "通知已发送")
            return True
        except Exception as e:
            self.log_result("播放列表分配", False, str(e))
            return False

    async def test_3_playlist_updated(self):
        """测试3: 发送播放列表更新通知"""
        print("\n" + "=" * 60)
        print("测试 3: 播放列表更新通知（增量更新）")
        print("=" * 60)

        if not ws_manager.is_connected(self.device_id):
            self.log_result("播放列表更新", False, "设备未连接")
            return False

        try:
            await NotificationService.notify_playlist_updated(
                device_id=self.device_id,
                playlist_id=self.playlist_id,
                playlist_name=f"测试播放列表-{self.playlist_id}",
                version="1.0.1",
                changes={
                    "added": [101, 102],
                    "removed": [50],
                    "reordered": False
                },
                item_count=6,
                total_size=60000000
            )
            self.log_result("播放列表更新", True, "增量更新通知已发送")
            return True
        except Exception as e:
            self.log_result("播放列表更新", False, str(e))
            return False

    async def test_4_playlist_activated(self):
        """测试4: 发送播放列表激活通知"""
        print("\n" + "=" * 60)
        print("测试 4: 播放列表激活/停用通知")
        print("=" * 60)

        if not ws_manager.is_connected(self.device_id):
            self.log_result("播放列表激活", False, "设备未连接")
            return False

        try:
            # 测试激活
            await NotificationService.notify_playlist_activated(
                device_id=self.device_id,
                playlist_id=self.playlist_id,
                is_active=True
            )
            print("  → 激活通知已发送")

            await asyncio.sleep(0.5)

            # 测试停用
            await NotificationService.notify_playlist_activated(
                device_id=self.device_id,
                playlist_id=self.playlist_id,
                is_active=False
            )
            print("  → 停用通知已发送")

            self.log_result("播放列表激活", True, "激活/停用通知已发送")
            return True
        except Exception as e:
            self.log_result("播放列表激活", False, str(e))
            return False

    async def test_5_playlist_removed(self):
        """测试5: 发送播放列表移除通知"""
        print("\n" + "=" * 60)
        print("测试 5: 播放列表移除通知")
        print("=" * 60)

        if not ws_manager.is_connected(self.device_id):
            self.log_result("播放列表移除", False, "设备未连接")
            return False

        try:
            await NotificationService.notify_playlist_removed(
                device_id=self.device_id,
                playlist_id=self.playlist_id
            )
            self.log_result("播放列表移除", True, "通知已发送")
            return True
        except Exception as e:
            self.log_result("播放列表移除", False, str(e))
            return False

    async def test_6_force_sync(self):
        """测试6: 发送强制同步通知"""
        print("\n" + "=" * 60)
        print("测试 6: 强制同步通知")
        print("=" * 60)

        if not ws_manager.is_connected(self.device_id):
            self.log_result("强制同步", False, "设备未连接")
            return False

        try:
            await NotificationService.notify_force_sync(
                device_id=self.device_id
            )
            self.log_result("强制同步", True, "通知已发送")
            return True
        except Exception as e:
            self.log_result("强制同步", False, str(e))
            return False

    async def test_7_control_commands(self):
        """测试7: 发送控制命令"""
        print("\n" + "=" * 60)
        print("测试 7: 播放控制命令")
        print("=" * 60)

        if not ws_manager.is_connected(self.device_id):
            self.log_result("控制命令", False, "设备未连接")
            return False

        try:
            # 测试暂停
            await NotificationService.send_pause(self.device_id)
            print("  → 暂停命令已发送")
            await asyncio.sleep(0.3)

            # 测试恢复
            await NotificationService.send_resume(self.device_id)
            print("  → 恢复命令已发送")
            await asyncio.sleep(0.3)

            # 测试音量
            await NotificationService.send_volume(self.device_id, 80)
            print("  → 音量命令已发送 (80%)")
            await asyncio.sleep(0.3)

            # 测试重新加载
            await NotificationService.send_reload(self.device_id)
            print("  → 重新加载命令已发送")

            self.log_result("控制命令", True, "所有控制命令已发送")
            return True
        except Exception as e:
            self.log_result("控制命令", False, str(e))
            return False

    async def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "=" * 60)
        print("   播放列表推送功能测试")
        print("=" * 60)
        print(f"设备 ID: {self.device_id}")
        print(f"播放列表 ID: {self.playlist_id}")

        tests = [
            ("检查设备在线", self.test_1_check_device_online),
            ("播放列表分配", self.test_2_playlist_assigned),
            ("播放列表更新", self.test_3_playlist_updated),
            ("播放列表激活", self.test_4_playlist_activated),
            ("强制同步", self.test_6_force_sync),
            ("控制命令", self.test_7_control_commands),
            # ("播放列表移除", self.test_5_playlist_removed),  # 可选，会影响后续测试
        ]

        for name, test_func in tests:
            try:
                await test_func()
                await asyncio.sleep(1)  # 测试间隔
            except Exception as e:
                self.log_result(name, False, f"异常: {str(e)}")

        # 打印测试总结
        self.print_summary()

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("   测试总结")
        print("=" * 60)

        passed = sum(1 for _, p, _ in self.test_results if p)
        failed = sum(1 for _, p, _ in self.test_results if not p)
        total = len(self.test_results)

        for name, passed, msg in self.test_results:
            status = "✅" if passed else "❌"
            print(f"  {status} {name}: {msg}")

        print("-" * 60)
        print(f"  通过: {passed}/{total}")
        print(f"  失败: {failed}/{total}")

        if failed == 0:
            print("\n  🎉 所有测试通过!")
        else:
            print("\n  ⚠️ 部分测试失败，请检查")


async def main():
    parser = argparse.ArgumentParser(description="播放列表推送功能测试")
    parser.add_argument(
        "--device-id",
        default="web-player-test-01",
        help="目标设备 ID (默认: web-player-test-01)"
    )
    parser.add_argument(
        "--playlist-id",
        type=int,
        default=1,
        help="测试播放列表 ID (默认: 1)"
    )

    args = parser.parse_args()

    tester = PlaylistPushTester(args.device_id, args.playlist_id)
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
