"""
CORS 中间件配置
"""
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings


class NullOriginCORSMiddleware(BaseHTTPMiddleware):
    """
    处理 null origin 的 CORS 中间件（用于 file:// 协议和 Android WebView）
    """

    async def dispatch(self, request: Request, call_next):
        # 处理预检请求
        if request.method == "OPTIONS":
            origin = request.headers.get("origin", "")
            response = Response()
            # 对于 null origin 或开发环境，允许所有来源
            if origin == "null" or settings.ENVIRONMENT != "production":
                response.headers["Access-Control-Allow-Origin"] = origin or "*"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
                response.headers["Access-Control-Allow-Headers"] = "*"
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Max-Age"] = "86400"
            return response

        # 处理正常请求
        response = await call_next(request)

        # 添加 CORS 头
        origin = request.headers.get("origin", "")
        if origin == "null" or settings.ENVIRONMENT != "production":
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
            response.headers["Access-Control-Allow-Credentials"] = "true"

        return response


def setup_cors(app: FastAPI):
    """
    配置 CORS 中间件

    Args:
        app: FastAPI 应用实例
    """
    # 先添加自定义的 null origin 处理中间件
    app.add_middleware(NullOriginCORSMiddleware)

    # 再添加标准的 CORS 中间件作为备用
    origins = settings.CORS_ORIGINS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"],
        allow_headers=["*"],
    )
