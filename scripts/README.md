# CastPlay 脚本工具集

本目录包含 CastPlay 项目的所有工具脚本，按功能分类组织。

## 📂 目录结构

```
scripts/
├── server/       # 服务器启动脚本
├── db/           # 数据库管理脚本
├── migration/    # 数据迁移脚本
├── testing/      # 测试相关脚本
└── dev/          # 开发工具脚本
```

## 📖 脚本索引

### 服务器脚本 (server/)

| 脚本 | 说明 |
|------|------|
| `start.py` | 启动 CastPlay 服务器 |

**使用方式：**
```bash
python scripts/server/start.py
```

### 数据库脚本 (db/)

| 脚本 | 说明 |
|------|------|
| `init.py` | 初始化数据库，创建表和默认用户 |
| `backup.py` | 备份数据库 |
| `init_default_playlist.py` | 初始化默认播放列表 |

**使用方式：**
```bash
# 初始化数据库
python scripts/db/init.py

# 备份数据库
python scripts/db/backup.py
```

### 迁移脚本 (migration/)

| 脚本 | 说明 |
|------|------|
| `enhancements.py` | 设备增强功能迁移 |
| `player_status.py` | 播放状态字段迁移 |
| `registration_codes.py` | 注册码功能迁移 |
| `update_device_types.py` | 更新设备类型 |

### 测试脚本 (testing/)

| 脚本 | 说明 |
|------|------|
| `run_web_tests.py` | 运行 Web 播放端测试 |
| `run_android_tests.py` | 运行 Android 播放端测试 |
| `start_web_env.py` | 启动 Web 测试环境 |
| `start_android_env.py` | 启动 Android 测试环境 |
| `android-test.sh` | Android 集成测试脚本 |
| `setup_android_emulator.sh` | 配置 Android 模拟器 |
| `start_emulator.sh` | 启动 Android 模拟器 |
| `test_glm5.py` | GLM5 集成测试 |
| `test_playlist_push.py` | 播放列表推送测试 |

**使用方式：**
```bash
# 启动测试环境
python scripts/testing/start_web_env.py

# 运行 Web 播放端测试
python scripts/testing/run_web_tests.py --e2e --headed

# 运行 Android 测试
python scripts/testing/run_android_tests.py
```

## 🔗 相关链接

- [返回项目主页](../README.md)
- [测试文档](../docs/testing/)
