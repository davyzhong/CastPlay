"""
GLM5 AI 服务模块
提供与智谱AI GLM5模型的集成
"""
import logging
from typing import Optional, Dict, Any, AsyncGenerator
from openai import AsyncOpenAI
from ..config import settings


logger = logging.getLogger(__name__)


class GLM5Service:
    """
    GLM5模型服务类
    提供与智谱AI GLM5模型交互的功能
    """
    
    def __init__(self):
        """初始化GLM5服务"""
        if not settings.ZHIPU_AI_ENABLED:
            logger.warning("GLM5 AI service is disabled. Set ZHIPU_AI_ENABLED=true to enable.")
        
        self.enabled = settings.ZHIPU_AI_ENABLED
        
        if self.enabled and settings.ZHIPU_API_KEY:
            self.client = AsyncOpenAI(
                api_key=settings.ZHIPU_API_KEY,
                base_url=settings.ZHIPU_BASE_URL
            )
            logger.info("GLM5 AI service initialized successfully")
        else:
            self.client = None
            logger.warning("GLM5 AI service not fully configured. Missing API key or disabled.")
    
    async def chat_completion(
        self, 
        messages: list, 
        model: Optional[str] = None, 
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Any:
        """
        执行聊天补全请求
        
        Args:
            messages: 消息列表，格式为[{"role": "user", "content": "hello"}, ...]
            model: 模型名称，默认使用配置中的模型
            temperature: 温度参数，默认使用配置中的温度
            max_tokens: 最大token数，默认使用配置中的最大值
            stream: 是否流式返回
            **kwargs: 其他传递给API的参数
            
        Returns:
            API响应结果
        """
        if not self.enabled or not self.client:
            raise RuntimeError("GLM5 AI service is not enabled or properly configured")
        
        try:
            params = {
                "model": model or settings.ZHIPU_MODEL_NAME,
                "messages": messages,
                "temperature": temperature or settings.ZHIPU_DEFAULT_TEMPERATURE,
                "max_tokens": max_tokens or settings.ZHIPU_MAX_TOKENS,
                "stream": stream
            }
            
            # 添加额外参数
            params.update(kwargs)
            
            if stream:
                return await self.client.chat.completions.create(**params)
            else:
                response = await self.client.chat.completions.create(**params)
                return response
        
        except Exception as e:
            logger.error(f"GLM5 chat completion error: {str(e)}")
            raise
    
    async def generate_text(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        生成文本内容
        
        Args:
            prompt: 用户输入提示
            system_prompt: 系统提示词
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            生成的文本内容
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = await self.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    async def stream_chat_completion(
        self, 
        messages: list, 
        model: Optional[str] = None, 
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式聊天补全
        
        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            
        Yields:
            生成的文本片段
        """
        if not self.enabled or not self.client:
            raise RuntimeError("GLM5 AI service is not enabled or properly configured")
        
        try:
            async for chunk in await self.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            ):
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"GLM5 stream chat completion error: {str(e)}")
            raise


# 创建全局GLM5服务实例
glm5_service = GLM5Service()


def get_glm5_service() -> GLM5Service:
    """
    获取GLM5服务实例
    
    Returns:
        GLM5Service实例
    """
    return glm5_service