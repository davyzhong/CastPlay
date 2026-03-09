#!/usr/bin/env python3
"""
迁移脚本：将现有设备的注册码和名称更新为新格式

新格式：
- 注册码：6位数字+大写字母（如 A8F392）
- 设备名称：Web-A8F392 或 Android-A8F392

运行方式：
    cd castplay-allinone
    python scripts/migrate_registration_codes.py
"""

import sys
import os
import random
import string

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.device import Device


def generate_new_code(length: int = 6) -> str:
    """生成新的6位注册码"""
    chars = string.ascii_uppercase + string.digits
    # 排除易混淆字符
    chars = chars.replace('0', '').replace('O', '').replace('1', '').replace('I', '').replace('L', '')
    return ''.join(random.choices(chars, k=length))


def determine_device_type(device: Device) -> str:
    """判断设备类型"""
    device_id = device.device_id or ""
    device_name = device.device_name or ""

    # 根据设备 ID 或名称判断
    if device_id.startswith("android-") or device_id.startswith("device-"):
        return "Android"
    if "Android" in device_name:
        return "Android"
    if device.mac_address and device.mac_address != "02:00:00:00:00:00":
        # 有真实 MAC 地址的可能是 Android 设备
        return "Android"
    return "Web"


def migrate():
    """执行迁移"""
    db = SessionLocal()
    try:
        devices = db.query(Device).all()

        if not devices:
            print("没有找到任何设备")
            return

        print(f"找到 {len(devices)} 个设备，开始迁移...\n")
        print("-" * 70)
        print(f"{'原名称':<25} {'新名称':<20} {'原注册码':<20} {'新注册码'}")
        print("-" * 70)

        used_codes = set()

        for device in devices:
            old_name = device.device_name or "N/A"
            old_code = device.registration_code or "N/A"

            # 生成新的唯一注册码
            new_code = generate_new_code()
            while new_code in used_codes:
                new_code = generate_new_code()
            used_codes.add(new_code)

            # 确定设备类型
            device_type = determine_device_type(device)

            # 更新设备
            device.registration_code = new_code
            device.device_name = f"{device_type}-{new_code}"

            print(f"{old_name:<25} {device.device_name:<20} {old_code:<20} {new_code}")

        db.commit()
        print("-" * 70)
        print(f"\n✅ 迁移完成！共更新 {len(devices)} 个设备")

    except Exception as e:
        db.rollback()
        print(f"\n❌ 迁移失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 70)
    print("CastPlay 设备注册码迁移脚本")
    print("新格式：6位注册码，设备名称为 Web-XXXXXX 或 Android-XXXXXX")
    print("=" * 70)
    print()

    confirm = input("确认执行迁移？(yes/no): ")
    if confirm.lower() == "yes":
        migrate()
    else:
        print("已取消")
