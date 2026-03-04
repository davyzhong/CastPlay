#!/usr/bin/env python3
"""下载 Gradle Wrapper JAR 文件"""
import urllib.request
import os
import sys

WRAPPER_DIR = "/Users/Davy/PycharmProjects/CastPlay/android-app/gradle/wrapper"
WRAPPER_JAR = os.path.join(WRAPPER_DIR, "gradle-wrapper.jar")

# Gradle wrapper jar 下载地址 (从 Maven 中央仓库)
URLS = [
    "https://repo1.maven.org/maven2/org/gradle/gradle-wrapper/8.2/gradle-wrapper-8.2.jar",
    "https://plugins.gradle.org/m2/org/gradle/gradle-wrapper/8.2/gradle-wrapper-8.2.jar",
]


def download_wrapper():
    os.makedirs(WRAPPER_DIR, exist_ok=True)

    for url in URLS:
        print(f"尝试下载: {url}")
        try:
            urllib.request.urlretrieve(url, WRAPPER_JAR)
            size = os.path.getsize(WRAPPER_JAR)
            if size > 50000:  # 有效的 jar 文件应该大于 50KB
                print(f"✓ 下载成功! 文件大小: {size} bytes")
                return True
            else:
                print(f"✗ 文件太小 ({size} bytes), 可能下载失败")
                os.remove(WRAPPER_JAR)
        except Exception as e:
            print(f"✗ 下载失败: {e}")

    return False


if __name__ == "__main__":
    if download_wrapper():
        print("\nGradle wrapper 修复成功!")
        sys.exit(0)
    else:
        print("\n下载失败，请手动下载或使用 Android Studio")
        sys.exit(1)
