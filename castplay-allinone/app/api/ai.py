"""
AI相关API端点
提供GLM5模型调用接口
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from app.services.ai_service import get_glm5_service, GLM5Service
from app.api.auth import get_current_user
from app.models.user import User


router = APIRouter(prefix="/ai", tags=["ai"])


class ChatRequest(BaseModel):
    """聊天请求模型"""
    messages: list
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class TextGenerationRequest(BaseModel):
    """文本生成请求模型"""
    prompt: str
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


@router.post("/chat")
async def ai_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    glm5_service: GLM5Service = Depends(get_glm5_service)
):
    """
    GLM5聊天接口
    """
    if not glm5_service.enabled:
        raise HTTPException(status_code=400, detail="GLM5 AI service is not enabled")
    
    try:
        response = await glm5_service.chat_completion(
            messages=request.messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return {
            "success": True,
            "data": {
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {str(e)}")


@router.post("/generate")
async def ai_generate_text(
    request: TextGenerationRequest,
    current_user: User = Depends(get_current_user),
    glm5_service: GLM5Service = Depends(get_glm5_service)
):
    """
    GLM5文本生成接口
    """
    if not glm5_service.enabled:
        raise HTTPException(status_code=400, detail="GLM5 AI service is not enabled")
    
    try:
        result = await glm5_service.generate_text(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return {
            "success": True,
            "data": {
                "content": result
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text generation failed: {str(e)}")


@router.get("/status")
async def ai_service_status(
    current_user: User = Depends(get_current_user),
    glm5_service: GLM5Service = Depends(get_glm5_service)
):
    """
    GLM5服务状态接口
    """
    return {
        "enabled": glm5_service.enabled,
        "configured": glm5_service.client is not None,
        "model": getattr(glm5_service, 'model_name', 'unknown')
    }