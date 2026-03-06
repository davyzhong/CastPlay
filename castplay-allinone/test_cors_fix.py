#!/usr/bin/env python3
"""测试 CORS 配置"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

print("=" * 60)
print(f"Environment: {settings.ENVIRONMENT}")
print(f"CORS_ORIGINS type: {type(settings.CORS_ORIGINS)}")
print(f"CORS_ORIGINS value: {settings.CORS_ORIGINS}")
print(f"CORS length: {len(settings.CORS_ORIGINS)}")
for i, origin in enumerate(settings.CORS_ORIGINS):
    print(f"  [{i}] {origin}")
print("=" * 60)

# 测试 CORS 中间件

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("✅ CORS middleware loaded successfully!")
