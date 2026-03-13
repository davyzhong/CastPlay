# CastPlay GLM5 AI 集成指南

本文档介绍如何在 CastPlay 项目中配置和使用 GLM5 大语言模型。

## 配置 GLM5

### 1. 获取智谱AI API Key

1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
2. 注册账号并登录
3. 在控制台创建新的应用，获取 API Key

### 2. 配置环境变量

复制 `.env.example` 文件为 `.env`，然后修改以下配置：

```bash
# 启用GLM5 AI服务
ZHIPU_AI_ENABLED=true

# 智谱AI API密钥
ZHIPU_API_KEY=your-actual-api-key-here

# 使用的模型名称（可选，默认为 glm-5-plus）
ZHIPU_MODEL_NAME=glm-5-plus

# API基础URL（可选，默认为官方地址）
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4/

# 默认温度参数（可选，默认为0.7）
ZHIPU_DEFAULT_TEMPERATURE=0.7

# 最大Token数（可选，默认为2048）
ZHIPU_MAX_TOKENS=2048
```

## API 接口

启用GLM5服务后，可以通过以下API接口使用AI功能：

### 1. 聊天接口

```
POST /api/ai/chat
```

请求体：
```json
{
  "messages": [
    {"role": "system", "content": "你是AI助手"},
    {"role": "user", "content": "你好"}
  ],
  "model": "glm-5-plus",
  "temperature": 0.7,
  "max_tokens": 1024
}
```

### 2. 文本生成接口

```
POST /api/ai/generate
```

请求体：
```json
{
  "prompt": "写一段关于春天的描述",
  "system_prompt": "你是一个写作助手",
  "model": "glm-5-plus",
  "temperature": 0.8,
  "max_tokens": 512
}
```

### 3. 服务状态接口

```
GET /api/ai/status
```

返回当前AI服务的状态信息。

## 服务状态

启动应用后，可以访问 `/api/ai/status` 来检查GLM5服务的状态。

## 使用示例

### Python 客户端示例

```python
import asyncio
from app.services.ai_service import get_glm5_service

async def example_usage():
    service = get_glm5_service()
    
    # 简单文本生成
    result = await service.generate_text(
        prompt="解释一下什么是人工智能",
        system_prompt="你是一个知识科普助手",
        max_tokens=500
    )
    
    print(result)

# 运行示例
asyncio.run(example_usage())
```

## 错误处理

- 如果API Key无效或配额耗尽，会返回HTTP 500错误
- 如果服务未启用，会返回HTTP 400错误
- 确保网络连接正常，能够访问智谱AI API

## 安全注意事项

- 保护好你的API Key，不要将其提交到版本控制系统
- 在生产环境中使用强密码和安全的API Key
- 监控API使用量，避免超出配额

## 故障排除

1. **服务显示未配置**：检查环境变量是否正确设置
2. **API调用失败**：确认API Key有效且有足够的配额
3. **网络问题**：确保服务器可以访问智谱AI API地址