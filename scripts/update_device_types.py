#!/usr/bin/env python3
"""
更新现有设备的 device_type 和名称
- 根据 device_id 前缀判断设备类型
- 更新 device_name 为新格式: Web-XXXXXX 或 Android-XXXXXX
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.device import Device


def determine_device_type(device: Device) -> str:
    """
    根据 device_id 判断设备类型
    - android-xxx 或 android_xxx → android_tv
    - 其他 → web_browser
    """
    device_id = (device.device_id or "").lower()

    if device_id.startswith("android"):
        return "android_tv"
    return "web_browser"


def get_device_prefix(device_type: str) -> str:
    """根据设备类型获取名称前缀"""
    if device_type == "android_tv":
        return "Android"
    return "Web"


def main():
    """更新所有设备的 device_type 和名称"""
    database_url = f"sqlite:///{settings.DATABASE_PATH}"
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        devices = session.query(Device).all()
        updated_count = 0

        print(f"找到 {len(devices)} 个设备")
        print("-" * 60)

        for device in devices:
            # 确定设备类型
            new_device_type = determine_device_type(device)
            prefix = get_device_prefix(new_device_type)

            # 生成新名称（使用注册码）
            if device.registration_code:
                new_name = f"{prefix}-{device.registration_code}"
            else:
                # 没有注册码的设备，跳过或使用旧名称
                print(f"  ⚠️  设备 {device.id} 没有注册码，跳过名称更新")
                new_name = device.device_name

            # 检查是否需要更新
            needs_update = False
            updates = []

            if device.device_type != new_device_type:
                updates.append(f"device_type: {device.device_type} → {new_device_type}")
                device.device_type = new_device_type
                needs_update = True

            if device.device_name != new_name and device.registration_code:
                updates.append(f"device_name: {device.device_name} → {new_name}")
                device.device_name = new_name
                needs_update = True

            if needs_update:
                print(f"设备 {device.id}:")
                for update in updates:
                    print(f"  • {update}")
                updated_count += 1

        print("-" * 60)

        if updated_count > 0:
            session.commit()
            print(f"✅ 已更新 {updated_count} 个设备")
        else:
            print("ℹ️  没有需要更新的设备")

        # 显示更新后的设备列表
        print("\n更新后的设备列表:")
        print("-" * 60)
        devices = session.query(Device).all()
        for device in devices:
            print(f"  {device.id:2d} | {device.device_name:20s} | {device.device_type:15s} | {device.registration_code or 'N/A'}")

    except Exception as e:
        session.rollback()
        print(f"❌ 错误: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
