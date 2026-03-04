#!/usr/bin/env python3
"""
修复数据库中媒体文件路径的脚本
将错误的 CasePlay 路径修正为正确的 CastPlay 路径
"""

import sqlite3
import os

# 数据库路径
DB_PATH = '/Users/Davy/PycharmProjects/CastPlay/castplay-server/instance/castplay.db'


def fix_media_paths():
    """修复媒体文件路径"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 查询所有媒体文件
    cursor.execute("SELECT id, file_path, thumbnail_path FROM media_file")
    rows = cursor.fetchall()

    print(f"发现 {len(rows)} 个媒体文件")

    updated_count = 0

    for row in rows:
        media_id, file_path, thumbnail_path = row

        # 修复文件路径
        if file_path and 'CasePlay' in file_path:
            new_file_path = file_path.replace('CasePlay', 'CastPlay')
            # 验证新路径是否存在
            if os.path.exists(new_file_path):
                cursor.execute(
                    "UPDATE media_file SET file_path = ? WHERE id = ?",
                    (new_file_path, media_id)
                )
                print(f"✓ 修复文件路径: ID {media_id}")
                updated_count += 1
            else:
                print(f"✗ 文件不存在: {new_file_path}")

        # 修复缩略图路径
        if thumbnail_path and 'CasePlay' in thumbnail_path:
            new_thumbnail_path = thumbnail_path.replace('CasePlay', 'CastPlay')
            # 验证新路径是否存在
            if os.path.exists(new_thumbnail_path):
                cursor.execute(
                    "UPDATE media_file SET thumbnail_path = ? WHERE id = ?",
                    (new_thumbnail_path, media_id)
                )
                print(f"✓ 修复缩略图路径: ID {media_id}")
                updated_count += 1
            else:
                print(f"✗ 缩略图不存在: {new_thumbnail_path}")

    # 提交更改
    conn.commit()
    conn.close()

    print(f"\n总共修复了 {updated_count} 个路径")


if __name__ == '__main__':
    fix_media_paths()
