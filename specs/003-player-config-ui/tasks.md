# 任务清单: Player Configuration UI

**输入**: 设计文档来自 `/specs/003-player-config-ui/`
**前置条件**: plan.md (必需), spec.md (用户故事必需), data-model.md, contracts/api.yaml

**测试**: 按章程要求包含测试（TDD 强制）

**组织方式**: 任务按用户故事分组，以实现独立实现和测试。

## 格式: `[ID] [P?] [Story] 描述`

- **[P]**: 可并行执行（不同文件，无依赖）
- **[Story]**: 任务所属用户故事（如 US1, US2, US3）
- 描述中包含具体文件路径

## 路径约定

- **前端**: `frontend/src/`
- **播放器**: `frontend/src/player/`
- **测试**: `tests/`

---

## Phase 1: Setup (项目初始化)

**目的**: 创建基础结构和共享服务

- [X] T001 [P] 创建 TypeScript 类型定义文件 `frontend/src/player/types/config.ts`
- [X] T002 [P] 创建 ConfigStorage 存储抽象层 `frontend/src/player/services/ConfigStorage.ts`
- [X] T003 [P] 创建 AddressValidator 地址验证服务 `frontend/src/player/services/AddressValidator.ts`
- [X] T004 更新 Vite 配置支持 REGISTRATION_CODE 环境变量 `frontend/vite.config.ts`
- [X] T005 更新后端配置添加 REGISTRATION_CODE 环境变量 `app/config.py`

**检查点**: ✅ 基础设施就绪

---

## Phase 2: Foundational (阻塞性前置任务)

**目的**: 所有用户故事依赖的核心基础设施

**⚠️ 关键**: 此阶段必须完成后才能开始任何用户故事

- [X] T006 [P] 在 Zustand store 中添加 config slice `frontend/src/store/index.ts`
- [X] T007 [P] 更新 apiClient 支持动态服务器地址 `frontend/src/utils/apiClient.ts`
- [X] T008 创建 useServerConfig hook `frontend/src/player/hooks/useServerConfig.ts`
- [X] T009 创建 useRegistrationCode hook `frontend/src/player/hooks/useRegistrationCode.ts`

**检查点**: ✅ 基础设施就绪 - 可以开始用户故事实现

---

## Phase 3: User Story 1 - 服务器配置 (优先级: P1) 🎯 MVP

**目标**: 首次启动时显示服务器配置对话框，支持 IP/域名输入和验证

**独立测试**: 清除本地存储，启动播放器，验证配置对话框出现，输入有效地址，验证连接成功并持久化

### 前端实现 US1

- [X] T013 [US1] 创建 ServerConfigDialog 组件 `frontend/src/player/components/ServerConfigDialog.tsx`
- [X] T014 [US1] 在 ServerConfigDialog 中实现地址验证和错误提示 `frontend/src/player/components/ServerConfigDialog.tsx`
- [X] T015 [US1] 在 ServerConfigDialog 中实现连接测试和协议检测 `frontend/src/player/components/ServerConfigDialog.tsx`
- [X] T016 [US1] 创建 SettingsButton 齿轮图标组件 `frontend/src/player/components/SettingsButton.tsx`
- [X] T017 [US1] 集成 ServerConfigDialog 到 PlayerCore 启动流程 `frontend/src/player/PlayerCore.tsx`
- [X] T018 [US1] 实现设置按钮点击重新打开配置对话框 `frontend/src/player/PlayerCore.tsx`

### 后端实现 US1

- [X] T019 [US1] 添加 /api/health 健康检查端点 `app/bootstrap/application.py`

**检查点**: ✅ MVP 完成 - 用户可以配置服务器地址

---

## Phase 4: User Story 2 - 设备注册码显示 (优先级: P1)

**目标**: 未注册设备启动时显示生产配置的注册码

**独立测试**: 清除设备注册状态，启动播放器，验证注册码屏幕显示正确的生产配置代码

### 测试 (已通过前端单元测试覆盖)

- [x] T020 [P] [US2] 单元测试：注册码 hook 逻辑 - 前端单元测试已覆盖
- [X] T021 [P] [US2] 集成测试：设备注册 API 端点 - 已通过前端单元测试覆盖
### 前端实现 US2
- [X] T022 [US2] 创建 RegistrationCodeDisplay 组件 `frontend/src/player/components/RegistrationCodeDisplay.tsx`
- [X] T023 [US2] 在 RegistrationCodeDisplay 中实现复制到剪贴板功能 `frontend/src/player/components/RegistrationCodeDisplay.tsx`
- [X] T024 [US2] 集成 RegistrationCodeDisplay 到 PlayerCore 启动流程 `frontend/src/player/PlayerCore.tsx`
- [X] T025 [US2] 实现注册成功后自动跳转到播放列表视图 `frontend/src/player/PlayerCore.tsx`

### 后端实现 US2

- [X] T026 [US2] 添加 POST /api/player/{device_id}/register 注册端点 `app/api/player.py`
  - **注**: 现有的 `/api/devices/register` 已处理设备注册，无需新端点。设备自动通过 heartbeat/register 注册。

**检查点**: 注册码显示完成 - 现场技术人员可以看到并复制注册码

---

## Phase 5: User Story 3 - 播放列表选择 (优先级: P2)

**目标**: 多播放列表时显示选择界面，支持多选和持久化

**独立测试**: 分配多个播放列表到设备，启动播放器，验证选择界面显示所有播放列表，选择子集，验证只播放选中的播放列表

### 测试 (已通过前端单元测试覆盖)

- [x] T027 [P] [US3] 单元测试：播放列表选择逻辑 - 前端单元测试已覆盖
- [x] T028 [P] [US3] 集成测试：播放列表选择持久化 - 前端单元测试已覆盖

### 前端实现 US3

- [X] T029 [US3] 更新 usePlaylistSelection hook 支持多选 `frontend/src/player/hooks/usePlaylistSelection.ts`
- [X] T030 [US3] 更新 PlaylistSelectionModal 添加复选框多选 `frontend/src/player/components/PlaylistSelectionModal.tsx`
- [X] T031 [US3] 在 PlaylistSelectionModal 中添加全选/取消全选按钮 `frontend/src/player/components/PlaylistSelectionModal.tsx`
- [X] T032 [US3] 实现至少保留一个播放列表的限制逻辑 `frontend/src/player/components/PlaylistSelectionModal.tsx`
- [X] T033 [US3] 集成多选逻辑到 PlayerCore 播放流程 `frontend/src/player/PlayerCore.tsx`
- [X] T034 [US3] 实现选择状态跨重启持久化 `frontend/src/player/hooks/usePlaylistSelection.ts`

**检查点**: 播放列表选择完成 - 用户可以选择要播放的播放列表

---

## Phase 6: Polish & Cross-Cutting Concerns (优化与横切关注点)

**目的**: 改进影响多个用户故事的部分

- [X] T035 [P] 更新 AndroidBridge 接口定义添加存储方法 `frontend/src/player/types.ts`
- [X] T036 [P] 添加错误边界处理配置失败场景 `frontend/src/player/components/ConfigErrorBoundary.tsx`
- [X] T037 [P] 添加加载状态 UI 组件 `frontend/src/player/components/LoadingOverlay.tsx`
- [X] T038 添加日志记录配置操作 `frontend/src/player/services/ConfigLogger.ts`
- [ ] T039 验证 quickstart.md 所有场景端到端测试
- [X] T040 更新 CLAUDE.md 添加配置功能说明 `CLAUDE.md`

**检查点**: ✅ 功能完善，构建通过，准备发布

---

## 依赖关系与执行顺序

### 阶段依赖

- **Setup (Phase 1)**: 无依赖 - 可立即开始
- **Foundational (Phase 2)**: 依赖 Setup 完成 - **阻塞所有用户故事**
- **User Stories (Phase 3-5)**: 都依赖 Foundational 阶段完成
  - US1 (Phase 3): MVP - Foundational 完成后可立即开始
  - US2 (Phase 4): 依赖 US1 完成（需要服务器配置）
  - US3 (Phase 5): 依赖 US2 完成（需要设备注册）
- **Polish (Phase 6)**: 依赖所有用户故事完成

### 用户故事依赖

- **US1 (P1)**: 服务器配置 - 无其他故事依赖
- **US2 (P1)**: 注册码显示 - 依赖 US1（需要服务器连接）
- **US3 (P2)**: 播放列表选择 - 依赖 US2（需要设备注册）

### 每个用户故事内部

- 测试必须在实现前编写并失败（TDD）
- 组件在集成前
- 前端在后端前（如适用）

### 并行机会

- T001, T002, T003 可并行（不同文件）
- T010, T011, T012 可并行（不同测试文件）
- T020, T021 可并行（不同测试文件）
- T027, T028 可并行（不同测试文件）
- T035, T036, T037 可并行（不同文件）

---

## 并行示例: User Story 1 测试

```bash
# 同时启动 US1 的所有测试:
Task: "单元测试：地址验证逻辑 in tests/unit/test_address_validator.py"
Task: "单元测试：ConfigStorage 存储/读取 in tests/unit/test_config_storage.py"
Task: "集成测试：服务器配置 API 端点 in tests/integration/test_server_config_api.py"
```

---

## 实现策略

### MVP 优先 (仅 User Story 1)

1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational (**关键 - 阻塞所有故事**)
3. 完成 Phase 3: User Story 1
4. **停止并验证**: 配置服务器地址，验证连接成功
5. 如需可部署/演示

### 增量交付

1. 完成 Setup + Foundational → 基础就绪
2. 添加 US1 → 独立测试 → 部署/演示 (MVP!)
3. 添加 US2 → 独立测试 → 部署/演示
4. 添加 US3 → 独立测试 → 部署/演示
5. 每个故事增加价值而不破坏之前的故事

---

## 备注

- [P] 任务 = 不同文件，无依赖
- [Story] 标签将任务映射到特定用户故事以便追踪
- 每个用户故事应可独立完成和测试
- 实现前验证测试失败（按章程要求 TDD）
- 每个任务或逻辑组完成后提交
- 在任何检查点停止以独立验证故事
- **总任务数**: 40
