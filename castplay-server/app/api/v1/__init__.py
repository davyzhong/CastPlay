"""CastPlay Server - API v1 Router"""
from fastapi import APIRouter

from app.api.v1 import auth, device, media, playlist, player, folder

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(device.router, prefix="/devices", tags=["设备管理"])
api_router.include_router(media.router, prefix="/media", tags=["媒体管理"])
api_router.include_router(playlist.router, prefix="/playlists", tags=["播放列表"])
api_router.include_router(player.router, prefix="/player", tags=["播放器"])
api_router.include_router(folder.router, prefix="/folders", tags=["文件夹"])
