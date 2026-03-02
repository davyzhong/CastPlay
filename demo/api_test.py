#!/usr/bin/env python3
"""CastPlay API 测试脚本"""

import requests
import json
import io

BASE_URL = 'http://127.0.0.1:5001'


def print_result(name, response):
    """打印测试结果"""
    print(f"\n{'='*50}")
    print(f"测试: {name}")
    print(f"{'='*50}")
    print(f"状态码: {response.status_code}")
    try:
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"响应: {response.text[:200]}")


def test_health():
    """测试健康检查"""
    r = requests.get(f'{BASE_URL}/health')
    print_result("健康检查", r)
    return r.status_code == 200


def test_device_register():
    """测试设备注册"""
    r = requests.post(f'{BASE_URL}/api/devices/register', json={
        'device_id': 'TEST-001',
        'device_name': '测试设备1',
        'timezone': 'Asia/Shanghai'
    })
    print_result("设备注册", r)
    return r.status_code in [200, 201]


def test_device_list():
    """测试设备列表"""
    r = requests.get(f'{BASE_URL}/api/devices')
    print_result("设备列表", r)
    return r.status_code == 200


def test_device_heartbeat():
    """测试设备心跳"""
    # 使用数据库中的数字ID（假设第一个设备是1）
    r = requests.put(f'{BASE_URL}/api/devices/1/heartbeat', json={
        'status': 'playing',
        'current_media': 'test.jpg'
    })
    print_result("设备心跳", r)
    return r.status_code == 200


def test_media_upload():
    """测试媒体上传"""
    # 创建假图片数据
    fake_image = io.BytesIO(b'fake image content for testing')
    files = {'file': ('test.jpg', fake_image, 'image/jpeg')}
    data = {'file_type': 'image'}

    r = requests.post(f'{BASE_URL}/api/media/upload', files=files, data=data)
    print_result("媒体上传", r)
    return r.status_code in [200, 201]


def test_media_list():
    """测试媒体列表"""
    r = requests.get(f'{BASE_URL}/api/media')
    print_result("媒体列表", r)
    return r.status_code == 200


def test_playlist_create():
    """测试创建播放列表"""
    r = requests.post(f'{BASE_URL}/api/playlists', json={
        'name': '测试播放列表',
        'description': '这是一个测试播放列表'
    })
    print_result("创建播放列表", r)
    return r.status_code in [200, 201]


def test_playlist_list():
    """测试播放列表"""
    r = requests.get(f'{BASE_URL}/api/playlists')
    print_result("播放列表", r)
    return r.status_code == 200


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("   CastPlay API 测试")
    print("   服务器地址: " + BASE_URL)
    print("="*60)

    tests = [
        ("健康检查", test_health),
        ("设备注册", test_device_register),
        ("设备列表", test_device_list),
        ("设备心跳", test_device_heartbeat),
        ("媒体上传", test_media_upload),
        ("媒体列表", test_media_list),
        ("创建播放列表", test_playlist_create),
        ("播放列表", test_playlist_list),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n测试 {name} 发生异常: {e}")
            results.append((name, False))

    # 打印测试报告
    print("\n" + "="*60)
    print("   测试报告")
    print("="*60)

    passed = 0
    failed = 0
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {name}: {status}")
        if success:
            passed += 1
        else:
            failed += 1

    print("\n" + "-"*60)
    print(f"  总计: {len(results)} 个测试")
    print(f"  通过: {passed} 个 ({100*passed//len(results)}%)")
    print(f"  失败: {failed} 个")
    print("="*60)

    return failed == 0


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
