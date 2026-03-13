"""
GLM5服务测试脚本
用于测试GLM5 AI服务的集成
"""
import asyncio
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from app.config import settings
from app.services.ai_service import GLM5Service


async def test_glm5_connection():
    """测试GLM5连接"""
    print("Testing GLM5 AI Service Integration...")
    print(f"ZHIPU_AI_ENABLED: {settings.ZHIPU_AI_ENABLED}")
    print(f"ZHIPU_API_KEY: {'Set' if settings.ZHIPU_API_KEY else 'Not set'}")
    print(f"ZHIPU_MODEL_NAME: {settings.ZHIPU_MODEL_NAME}")
    
    # 创建GLM5服务实例
    glm5_service = GLM5Service()
    
    if not glm5_service.enabled:
        print("❌ GLM5 service is not enabled. Please set ZHIPU_AI_ENABLED=true in your environment.")
        return False
    
    if not glm5_service.client:
        print("❌ GLM5 service is not properly configured. Please set ZHIPU_API_KEY.")
        return False
    
    print("✅ GLM5 service initialized successfully")
    
    try:
        # 测试简单的文本生成
        print("\nTesting text generation...")
        result = await glm5_service.generate_text(
            prompt="你好，请简单介绍一下自己。",
            system_prompt="你是一个有用的AI助手。",
            max_tokens=200
        )
        print(f"✅ Text generation successful:")
        print(f"Response: {result[:100]}{'...' if len(result) > 100 else ''}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during GLM5 test: {str(e)}")
        return False


async def test_glm5_chat():
    """测试GLM5聊天功能"""
    print("\nTesting GLM5 chat completion...")
    
    glm5_service = GLM5Service()
    
    if not glm5_service.enabled or not glm5_service.client:
        print("❌ GLM5 service not available for chat test")
        return False
    
    try:
        messages = [
            {"role": "system", "content": "你是一个有用的AI助手"},
            {"role": "user", "content": "今天天气怎么样？"}
        ]
        
        response = await glm5_service.chat_completion(messages=messages)
        content = response.choices[0].message.content
        print(f"✅ Chat completion successful:")
        print(f"Response: {content[:100]}{'...' if len(content) > 100 else ''}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during GLM5 chat test: {str(e)}")
        return False


async def main():
    """主测试函数"""
    print("="*60)
    print("CastPlay GLM5 AI Integration Test")
    print("="*60)
    
    success1 = await test_glm5_connection()
    success2 = await test_glm5_chat()
    
    print("\n" + "="*60)
    if success1 and success2:
        print("🎉 All GLM5 integration tests passed!")
        print("✅ You can now use GLM5 AI features in your CastPlay application")
        print("\nTo enable GLM5 features:")
        print("- Set ZHIPU_AI_ENABLED=true in your .env file")
        print("- Add your ZHIPU_API_KEY")
        print("- Restart the application")
    else:
        print("⚠️  GLM5 integration tests partially failed or skipped")
        print("💡 Make sure to set proper environment variables to enable GLM5 features")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())