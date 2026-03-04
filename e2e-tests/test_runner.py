#!/usr/bin/env python3
"""
E2E 测试执行器 - 纯 Python 实现
自动化执行完整的 E2E 测试流程
"""

import subprocess
import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

# 配置
CONFIG = {
    "android_home": "/Users/Davy/PycharmProjects/CastPlay/android-sdk",
    "java_home": "/Users/Davy/Library/Java/JavaVirtualMachines/jbr-17.0.14/Contents/Home",
    "project_dir": "/Users/Davy/PycharmProjects/CastPlay",
    "appium_port": 4723,
    "backend_port": 5000,
}


class TestRunner:
    def __init__(self):
        self.results = {
            "start_time": datetime.now().isoformat(),
            "steps": [],
            "test_results": [],
            "errors": []
        }
        self.android_home = CONFIG["android_home"]
        self.java_home = CONFIG["java_home"]
        self.project_dir = CONFIG["project_dir"]

        # 设置环境变量
        os.environ["ANDROID_HOME"] = self.android_home
        os.environ["JAVA_HOME"] = self.java_home
        os.environ["PATH"] = f"{self.java_home}/bin:{self.android_home}/platform-tools:{self.android_home}/emulator:" + \
            os.environ.get("PATH", "")

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        self.results["steps"].append({
            "time": timestamp,
            "level": level,
            "message": message
        })

    def run_command(self, cmd, timeout=60, check=True):
        """运行命令并返回结果"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=os.environ
            )
            return {
                "success": result.returncode == 0 if check else True,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def check_environment(self):
        """检查环境"""
        self.log("=" * 50)
        self.log("步骤 1: 检查环境")
        self.log("=" * 50)

        checks = []

        # Java
        result = self.run_command(
            f"{self.java_home}/bin/java -version 2>&1 | head -1")
        self.log(f"Java: {result.get('stdout', result.get('stderr', 'N/A'))}")
        checks.append(("Java", result["success"]))

        # ADB
        adb = f"{self.android_home}/platform-tools/adb"
        result = self.run_command(f"{adb} --version | head -1")
        self.log(f"ADB: {result.get('stdout', 'N/A')}")
        checks.append(("ADB", result["success"]))

        # Appium
        result = self.run_command("which appium && appium --version")
        if result["success"]:
            self.log(
                f"Appium: {result['stdout'].split()[-1] if result['stdout'] else 'N/A'}")
        else:
            self.log("Appium: 未找到", "WARNING")
        checks.append(("Appium", result["success"]))

        # Gradle wrapper
        wrapper = f"{self.project_dir}/android-app/gradle/wrapper/gradle-wrapper.jar"
        exists = os.path.exists(wrapper)
        self.log(f"Gradle Wrapper: {'存在' if exists else '不存在'}")
        checks.append(("Gradle Wrapper", exists))

        return all(c[1] for c in checks)

    def start_appium(self):
        """启动 Appium 服务器"""
        self.log("=" * 50)
        self.log("步骤 2: 启动 Appium 服务器")
        self.log("=" * 50)

        # 停止现有 Appium
        self.run_command("pkill -f appium", check=False)
        time.sleep(2)

        # 启动 Appium
        subprocess.Popen(
            "appium --port 4723",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        self.log("Appium 启动中...")
        time.sleep(5)

        # 验证
        try:
            import requests
            resp = requests.get(
                f"http://127.0.0.1:{CONFIG['appium_port']}/status", timeout=5)
            if resp.status_code == 200:
                self.log("Appium 服务器已就绪")
                return True
        except:
            pass

        self.log("Appium 可能未就绪，继续...", "WARNING")
        return True

    def start_emulator(self):
        """启动模拟器"""
        self.log("=" * 50)
        self.log("步骤 3: 启动 Android 模拟器")
        self.log("=" * 50)

        adb = f"{self.android_home}/platform-tools/adb"
        emulator = f"{self.android_home}/emulator/emulator"

        # 检查是否已运行
        result = self.run_command(f"{adb} devices")
        if "emulator" in result.get("stdout", ""):
            self.log("模拟器已运行")
            return True

        # 启动模拟器
        self.log("启动模拟器 Pixel_4_API_30...")
        subprocess.Popen(
            f"{emulator} -avd Pixel_4_API_30 -no-snapshot-save -no-audio",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # 等待启动
        self.log("等待模拟器启动...")
        self.run_command(f"{adb} wait-for-device", timeout=120)

        for i in range(60):
            result = self.run_command(
                f"{adb} shell getprop sys.boot_completed 2>/dev/null")
            if result.get("stdout", "").strip() == "1":
                self.log("模拟器启动完成")
                return True
            time.sleep(2)

        self.log("模拟器启动超时", "WARNING")
        return False

    def build_apk(self):
        """构建 APK"""
        self.log("=" * 50)
        self.log("步骤 4: 构建 Android APK")
        self.log("=" * 50)

        apk_path = f"{self.project_dir}/android-app/app/build/outputs/apk/debug/app-debug.apk"

        if os.path.exists(apk_path):
            self.log(f"APK 已存在: {apk_path}")
            return apk_path

        self.log("构建 Debug APK...")
        os.chdir(f"{self.project_dir}/android-app")

        result = self.run_command("./gradlew assembleDebug", timeout=600)
        if result["success"] and os.path.exists(apk_path):
            self.log("APK 构建成功")
            return apk_path
        else:
            self.log(f"APK 构建失败: {result.get('stderr', '')}", "ERROR")
            self.results["errors"].append(f"APK 构建失败: {result}")
            return None

    def install_apk(self, apk_path):
        """安装 APK"""
        self.log("=" * 50)
        self.log("步骤 5: 安装 APK")
        self.log("=" * 50)

        if not apk_path:
            self.log("无 APK 可安装", "ERROR")
            return False

        adb = f"{self.android_home}/platform-tools/adb"
        result = self.run_command(f"{adb} install -r {apk_path}", timeout=60)

        if result["success"]:
            self.log("APK 安装成功")
            return True
        else:
            self.log(f"APK 安装失败: {result.get('stderr', '')}", "ERROR")
            return False

    def start_backend(self):
        """启动后端服务器"""
        self.log("=" * 50)
        self.log("步骤 6: 启动后端服务器")
        self.log("=" * 50)

        # 停止现有进程
        self.run_command("pkill -f 'run.py'", check=False)
        time.sleep(2)

        os.chdir(f"{self.project_dir}/castplay-server")
        subprocess.Popen(
            "python run.py",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        self.log("后端服务器启动中...")
        time.sleep(5)

        # 验证
        try:
            import requests
            resp = requests.get(
                f"http://127.0.0.1:{CONFIG['backend_port']}/api/devices", timeout=5)
            self.log("后端服务器已就绪")
            return True
        except:
            self.log("后端服务器可能未就绪", "WARNING")
            return True

    def run_tests(self):
        """运行测试"""
        self.log("=" * 50)
        self.log("步骤 7: 运行 E2E 测试")
        self.log("=" * 50)

        os.chdir(f"{self.project_dir}/e2e-tests")

        # 环境验证测试
        self.log("运行环境验证测试...")
        result = self.run_command(
            "python -m pytest tests/test_environment_validation.py -v --tb=short 2>&1",
            timeout=120
        )
        self.results["test_results"].append({
            "name": "environment_validation",
            "output": result.get("stdout", ""),
            "success": result["success"]
        })

        # 解析测试结果
        output = result.get("stdout", "")
        passed = output.count(" PASSED")
        failed = output.count(" FAILED")
        self.log(f"环境验证: {passed} passed, {failed} failed")

        # CastPlay E2E 测试 (如果环境验证通过)
        if passed > 0:
            self.log("运行 CastPlay E2E 测试...")
            result = self.run_command(
                "python -m pytest tests/test_castplay_e2e.py -v --tb=short 2>&1",
                timeout=300
            )
            self.results["test_results"].append({
                "name": "castplay_e2e",
                "output": result.get("stdout", ""),
                "success": result["success"]
            })

            output = result.get("stdout", "")
            passed = output.count(" PASSED")
            failed = output.count(" FAILED")
            skipped = output.count(" SKIPPED")
            self.log(
                f"CastPlay E2E: {passed} passed, {failed} failed, {skipped} skipped")

        return True

    def generate_report(self):
        """生成测试报告"""
        self.results["end_time"] = datetime.now().isoformat()

        report_path = f"{self.project_dir}/e2e-tests/reports/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)

        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        self.log(f"报告已生成: {report_path}")
        return report_path

    def run(self):
        """运行完整测试流程"""
        try:
            self.check_environment()
            self.start_appium()
            self.start_emulator()
            apk_path = self.build_apk()
            self.install_apk(apk_path)
            self.start_backend()
            self.run_tests()
        except Exception as e:
            self.log(f"执行出错: {e}", "ERROR")
            self.results["errors"].append(str(e))
        finally:
            report_path = self.generate_report()
            self.log("=" * 50)
            self.log("测试完成")
            self.log("=" * 50)
            return report_path


if __name__ == "__main__":
    runner = TestRunner()
    runner.run()
