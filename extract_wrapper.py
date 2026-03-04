#!/usr/bin/env python3
"""从 Gradle zip 提取 wrapper jar"""
import zipfile
import os
import shutil

ZIP_PATH = "/Users/Davy/PycharmProjects/CastPlay/gradle-8.2.1-bin.zip"
TARGET_DIR = "/Users/Davy/PycharmProjects/CastPlay/android-app/gradle/wrapper"
TARGET_JAR = os.path.join(TARGET_DIR, "gradle-wrapper.jar")


def extract_wrapper():
    print(f"读取: {ZIP_PATH}")

    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        files = z.filelist
        print(f"总文件数: {len(files)}")

        # 查找 wrapper jar
        wrapper_files = [
            f for f in files if 'wrapper' in f.filename and f.filename.endswith('.jar')]
        print(f"找到 {len(wrapper_files)} 个 wrapper 文件:")
        for f in wrapper_files:
            print(f"  - {f.filename} ({f.file_size} bytes)")

        if wrapper_files:
            # 选择第一个
            wrapper_file = wrapper_files[0]
            print(f"\n提取: {wrapper_file.filename}")

            os.makedirs(TARGET_DIR, exist_ok=True)
            with z.open(wrapper_file) as source, open(TARGET_JAR, 'wb') as target:
                shutil.copyfileobj(source, target)

            size = os.path.getsize(TARGET_JAR)
            print(f"✓ 提取成功: {TARGET_JAR} ({size} bytes)")
            return True
        else:
            print("✗ 未找到 wrapper jar")
            return False


if __name__ == "__main__":
    extract_wrapper()
