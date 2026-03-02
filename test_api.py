#!/usr/bin/env python3
"""
CastPlay API 功能测试脚本
分阶段执行 API 测试
"""

import requests
import json
import os
import sys
from datetime import datetime

# 配置
BASE_URL = "http://localhost:5001/api"
TEST_FILES_DIR = os.path.dirname(os.path.abspath(__file__))

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log_pass(msg):
    print(f"{Colors.GREEN}✓ PASS{Colors.END}: {msg}")

def log_fail(msg):
    print(f"{Colors.RED}✗ FAIL{Colors.END}: {msg}")

def log_info(msg):
    print(f"{Colors.BLUE}ℹ INFO{Colors.END}: {msg}")

def log_section(msg):
    print(f"\n{Colors.YELLOW}{'='*50}")
    print(f"  {msg}")
    print(f"{'='*50}{Colors.END}\n")


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def add(self, name, passed, detail=""):
        self.tests.append({"name": name, "passed": passed, "detail": detail})
        if passed:
            self.passed += 1
            log_pass(name)
        else:
            self.failed += 1
            log_fail(f"{name} - {detail}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*50}")
        print(f"  测试结果: {self.passed}/{total} 通过")
        print(f"{'='*50}")
        if self.failed > 0:
            print(f"\n失败的测试:")
            for t in self.tests:
                if not t["passed"]:
                    print(f"  - {t['name']}: {t['detail']}")


# ===========================================
# 阶段一: 环境健康检查
# ===========================================
def test_phase1_health(result: TestResult):
    log_section("阶段一: 环境健康检查")
    
    # 1.1 后端健康检查
    try:
        resp = requests.get("http://localhost:5001/health", timeout=5)
        result.add("后端服务健康检查", resp.status_code == 200, 
                   f"status={resp.status_code}")
    except Exception as e:
        result.add("后端服务健康检查", False, str(e))
    
    # 1.2 API 基础连接
    try:
        resp = requests.get(f"{BASE_URL}/devices", timeout=5)
        result.add("API 基础连接", resp.status_code == 200,
                   f"status={resp.status_code}")
    except Exception as e:
        result.add("API 基础连接", False, str(e))


# ===========================================
# 阶段二: 设备管理功能测试
# ===========================================
def test_phase2_device(result: TestResult):
    log_section("阶段二: 设备管理功能测试")
    
    test_device_id = f"test-device-{datetime.now().strftime('%H%M%S')}"
    created_device = None
    
    # 2.1 设备注册
    try:
        resp = requests.post(f"{BASE_URL}/devices/register", json={
            "device_id": test_device_id,
            "device_name": "测试设备",
            "timezone": "Asia/Shanghai"
        })
        result.add("设备注册", resp.status_code == 200, 
                   f"status={resp.status_code}")
        if resp.status_code == 200:
            created_device = resp.json().get("device", {})
    except Exception as e:
        result.add("设备注册", False, str(e))
    
    # 2.2 设备列表查询
    try:
        resp = requests.get(f"{BASE_URL}/devices")
        data = resp.json()
        has_devices = len(data.get("devices", [])) > 0
        result.add("设备列表查询", resp.status_code == 200 and has_devices,
                   f"设备数量: {len(data.get('devices', []))}")
    except Exception as e:
        result.add("设备列表查询", False, str(e))
    
    # 2.3 设备详情查询
    if created_device:
        try:
            device_id = created_device.get("id")
            resp = requests.get(f"{BASE_URL}/devices/{device_id}")
            result.add("设备详情查询", resp.status_code == 200,
                       f"status={resp.status_code}")
        except Exception as e:
            result.add("设备详情查询", False, str(e))
    
    # 2.4 设备定时配置
    if created_device:
        try:
            device_id = created_device.get("id")
            resp = requests.post(f"{BASE_URL}/devices/{device_id}/schedule", json={
                "power_on_time": "08:00",
                "power_off_time": "22:00",
                "weekdays": [1, 2, 3, 4, 5],
                "is_enabled": True
            })
            result.add("设备定时配置", resp.status_code == 200,
                       f"status={resp.status_code}")
        except Exception as e:
            result.add("设备定时配置", False, str(e))
    
    # 2.5 设备删除
    if created_device:
        try:
            device_id = created_device.get("id")
            resp = requests.delete(f"{BASE_URL}/devices/{device_id}")
            result.add("设备删除", resp.status_code == 200,
                       f"status={resp.status_code}")
        except Exception as e:
            result.add("设备删除", False, str(e))
    
    return created_device


# ===========================================
# 阶段三: 媒体管理功能测试
# ===========================================
def test_phase3_media(result: TestResult):
    log_section("阶段三: 媒体管理功能测试")
    
    created_media = None
    
    # 3.1 创建测试图片文件
    test_image_path = "/tmp/test_image.jpg"
    try:
        # 创建一个简单的测试图片 (1x1 红色像素的JPEG)
        import struct
        jpeg_data = bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
            0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
            0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
            0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
            0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
            0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
            0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
            0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
            0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00,
            0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
            0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
            0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D,
            0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06,
            0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08,
            0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
            0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28,
            0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45,
            0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
            0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75,
            0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89,
            0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
            0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6,
            0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9,
            0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2,
            0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4,
            0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01,
            0x00, 0x00, 0x3F, 0x00, 0xFB, 0xD5, 0xDB, 0x20, 0xA8, 0xA2, 0x80, 0x3F,
            0xFF, 0xD9
        ])
        with open(test_image_path, 'wb') as f:
            f.write(jpeg_data)
        log_info(f"创建测试图片: {test_image_path}")
    except Exception as e:
        log_fail(f"创建测试图片失败: {e}")
    
    # 3.2 上传媒体文件
    try:
        with open(test_image_path, 'rb') as f:
            files = {'file': ('test_image.jpg', f, 'image/jpeg')}
            data = {'file_type': 'image'}
            resp = requests.post(f"{BASE_URL}/media/upload", files=files, data=data)
        
        result.add("媒体文件上传", resp.status_code == 201,
                   f"status={resp.status_code}")
        if resp.status_code == 201:
            created_media = resp.json().get("media", {})
    except Exception as e:
        result.add("媒体文件上传", False, str(e))
    
    # 3.3 媒体列表查询
    try:
        resp = requests.get(f"{BASE_URL}/media")
        data = resp.json()
        result.add("媒体列表查询", resp.status_code == 200,
                   f"媒体数量: {data.get('total', 0)}")
    except Exception as e:
        result.add("媒体列表查询", False, str(e))
    
    # 3.4 媒体详情查询
    if created_media:
        try:
            media_id = created_media.get("id")
            resp = requests.get(f"{BASE_URL}/media/{media_id}")
            result.add("媒体详情查询", resp.status_code == 200,
                       f"status={resp.status_code}")
        except Exception as e:
            result.add("媒体详情查询", False, str(e))
    
    # 3.5 按类型筛选媒体
    try:
        resp = requests.get(f"{BASE_URL}/media", params={"file_type": "image"})
        result.add("按类型筛选媒体", resp.status_code == 200,
                   f"status={resp.status_code}")
    except Exception as e:
        result.add("按类型筛选媒体", False, str(e))
    
    # 清理测试文件
    if os.path.exists(test_image_path):
        os.remove(test_image_path)
    
    return created_media


# ===========================================
# 阶段四: 播放列表管理功能测试
# ===========================================
def test_phase4_playlist(result: TestResult, media_id=None):
    log_section("阶段四: 播放列表管理功能测试")
    
    created_playlist = None
    
    # 4.1 创建播放列表
    try:
        resp = requests.post(f"{BASE_URL}/playlists", json={
            "name": f"测试播放列表-{datetime.now().strftime('%H%M%S')}",
            "description": "自动化测试创建"
        })
        result.add("创建播放列表", resp.status_code == 201,
                   f"status={resp.status_code}")
        if resp.status_code == 201:
            created_playlist = resp.json().get("playlist", {})
    except Exception as e:
        result.add("创建播放列表", False, str(e))
    
    # 4.2 播放列表查询
    try:
        resp = requests.get(f"{BASE_URL}/playlists")
        data = resp.json()
        result.add("播放列表查询", resp.status_code == 200,
                   f"列表数量: {data.get('total', 0)}")
    except Exception as e:
        result.add("播放列表查询", False, str(e))
    
    # 4.3 播放列表详情
    if created_playlist:
        try:
            playlist_id = created_playlist.get("id")
            resp = requests.get(f"{BASE_URL}/playlists/{playlist_id}")
            result.add("播放列表详情", resp.status_code == 200,
                       f"status={resp.status_code}")
        except Exception as e:
            result.add("播放列表详情", False, str(e))
    
    # 4.4 添加媒体到播放列表
    if created_playlist and media_id:
        try:
            playlist_id = created_playlist.get("id")
            resp = requests.post(f"{BASE_URL}/playlists/{playlist_id}/items", json={
                "media_id": media_id,
                "display_duration": 10
            })
            result.add("添加媒体到播放列表", resp.status_code == 201,
                       f"status={resp.status_code}")
        except Exception as e:
            result.add("添加媒体到播放列表", False, str(e))
    
    # 4.5 更新播放列表
    if created_playlist:
        try:
            playlist_id = created_playlist.get("id")
            resp = requests.put(f"{BASE_URL}/playlists/{playlist_id}", json={
                "name": "更新后的播放列表名称",
                "description": "更新后的描述"
            })
            result.add("更新播放列表", resp.status_code == 200,
                       f"status={resp.status_code}")
        except Exception as e:
            result.add("更新播放列表", False, str(e))
    
    return created_playlist


# ===========================================
# 阶段五: 清理测试数据
# ===========================================
def test_phase5_cleanup(result: TestResult, media_id=None, playlist_id=None):
    log_section("阶段五: 清理测试数据")
    
    # 5.1 删除播放列表
    if playlist_id:
        try:
            resp = requests.delete(f"{BASE_URL}/playlists/{playlist_id}")
            result.add("删除测试播放列表", resp.status_code == 200,
                       f"status={resp.status_code}")
        except Exception as e:
            result.add("删除测试播放列表", False, str(e))
    
    # 5.2 删除媒体文件
    if media_id:
        try:
            resp = requests.delete(f"{BASE_URL}/media/{media_id}")
            result.add("删除测试媒体文件", resp.status_code == 200,
                       f"status={resp.status_code}")
        except Exception as e:
            result.add("删除测试媒体文件", False, str(e))


# ===========================================
# 主函数
# ===========================================
def main():
    print("""
╔═══════════════════════════════════════════════════╗
║         CastPlay API 功能测试                     ║
║         分阶段自动化测试脚本                      ║
╚═══════════════════════════════════════════════════╝
    """)
    
    result = TestResult()
    
    # 阶段一: 环境检查
    test_phase1_health(result)
    if result.failed > 0:
        print(f"\n{Colors.RED}环境检查失败，请先启动服务！{Colors.END}")
        print("运行: ./start_test.sh")
        sys.exit(1)
    
    # 阶段二: 设备管理
    test_phase2_device(result)
    
    # 阶段三: 媒体管理
    media = test_phase3_media(result)
    media_id = media.get("id") if media else None
    
    # 阶段四: 播放列表管理
    playlist = test_phase4_playlist(result, media_id)
    playlist_id = playlist.get("id") if playlist else None
    
    # 阶段五: 清理
    test_phase5_cleanup(result, media_id, playlist_id)
    
    # 输出结果
    result.summary()
    
    sys.exit(0 if result.failed == 0 else 1)


if __name__ == "__main__":
    main()
