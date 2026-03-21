# CastPlay 文档中心

本目录包含 CastPlay 项目的所有文档，按类别组织。

## 目录结构

```
docs/
├── architecture/    # 架构设计文档
├── api/            # API 参考文档
├── deployment/      # 部署相关文档
├── development/     # 开发指南
├── features/        # 功能文档
├── android/         # Android 相关文档
├── testing/         # 测试文档
├── reports/         # 测试报告
└── configuration.md # 配置参考文档
```

## 文档索引

### 核心参考文档

| 文档 | 说明 |
|------|------|
| [配置参考](./configuration.md) | 所有环境变量和配置项说明 |
| [API 参考](./api/README.md) | REST API 端点完整文档 |
| [WebSocket 协议](./api/websocket.md) | 实时通信协议说明 |

### 架构设计

| 文档 | 说明 |
|------|------|
| [项目说明书](./architecture/README.md) | 项目概述和核心概念 |
| [项目架构](./architecture/project_architecture.md) | 系统架构设计 |
| [播放器客户端设计](./architecture/player_client_design.md) | 客户端架构说明 |

### 部署指南

| 文档 | 说明 |
|------|------|
| [部署指南](./deployment/guide.md) | 生产环境部署 |
| [使用指南](./deployment/usage_guide.md) | 系统使用说明 |
| [数据迁移](./deployment/migration.md) | 数据迁移指南 |

### 开发指南

| 文档 | 说明 |
|------|------|
| [开发手册](./development/guide.md) | 开发环境配置 |
| [Git 提交规范](./development/git_commit_guide.md) | 提交消息规范 |

### 功能文档

| 文档 | 说明 |
|------|------|
| [Web 播放器模拟器](./features/web_player_simulator.md) | 浏览器端播放器 |
| [GLM5 集成](./features/glm5_integration.md) | AI 能力集成 |

### Android 相关

| 文档 | 说明 |
|------|------|
| [部署与测试指南](./android/deployment_testing_guide.md) | Android 部署和测试 |
| [模拟器配置](./android/emulator_setup.md) | Android 模拟器配置 |
| [播放器实现](./android/player_implementation.md) | Android 播放器代码说明 |

### 测试文档

| 文档 | 说明 |
|------|------|
| [播放列表推送测试](./testing/playlist_push_guide.md) | 推送功能测试 |
| [播放列表切换测试](./testing/playlist_switch_checklist.md) | 切换功能测试清单 |

### 测试报告

| 文档 | 说明 |
|------|------|
| [项目完整性 Review](./reports/PROJECT_REVIEW_REPORT.md) | **推荐阅读** |
| [最终测试报告](./reports/FINAL_REPORT.md) | 完整测试结果 |
| [Phase 4 测试报告](./reports/PHASE4_TEST_REPORT.md) | 阶段测试结果 |
| [完整测试计划](./reports/COMPLETE_REVIEW_AND_TEST_PLAN.md) | 测试规划 |

## 快速链接

### 在线资源

- [返回项目主页](../README.md)
- [Swagger API 文档](http://localhost:8000/docs) (需启动服务)
- [ReDoc API 文档](http://localhost:8000/redoc) (需启动服务)

### 快速开始

1. **初次部署**：查看 [部署指南](./deployment/guide.md)
2. **配置系统**：查看 [配置参考](./configuration.md)
3. **开发调试**：查看 [开发手册](./development/guide.md)
4. **API 集成**：查看 [API 参考](./api/README.md)

### API 概览

```
认证:
  POST /api/auth/login          - 用户登录
  POST /api/auth/register      - 用户注册

设备:
  POST /api/devices/register   - 注册设备
  GET  /api/devices            - 获取设备列表
  PUT  /api/devices/{id}       - 更新设备

媒体:
  POST /api/media/upload       - 上传媒体文件
  GET  /api/media              - 获取媒体列表

播放列表:
  POST /api/playlists          - 创建播放列表
  GET  /api/playlists          - 获取播放列表
  PUT  /api/playlists/{id}/items/reorder - 重新排序

调度:
  POST /api/schedules          - 创建调度规则
  GET  /api/schedules/active  - 获取当前激活调度

控制:
  POST /api/control/{device_id}/pause  - 暂停播放
  POST /api/control/{device_id}/resume - 恢复播放

WebSocket:
  WS /ws/{device_id}          - 设备实时通信
```

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| 设备无法连接 | 检查服务器地址和端口配置 |
| 上传文件失败 | 检查 `data/uploads` 目录权限 |
| 登录失败 | 检查 `SECRET_KEY` 配置 |
| WebSocket 断开 | 检查防火墙和心跳配置 |

## 贡献指南

欢迎贡献文档！请遵循以下规范：

1. 文档使用 Markdown 格式
2. 代码示例必须经过测试
3. 保持文档与代码同步更新
4. 使用中文编写，保持术语一致

## 文档维护

- 核心 API 文档：每次 API 变更时更新
- 配置文档：每次配置项变更时更新
- 功能文档：功能发布时同步更新
- 测试报告：测试完成后归档
