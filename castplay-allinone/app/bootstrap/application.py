"""
应用引导模块
负责所有初始化逻辑，避免 main.py 膨胀
"""
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from app.config import settings
from app.database import init_database
from app.scheduler import start as start_scheduler, stop as stop_scheduler
from app.middleware.cors import setup_cors
from app.utils.logger import logger


# 前端 dist 目录
_FRONTEND_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"


class ApplicationBootstrap:
    """应用引导类"""

    def __init__(self):
        self.app = FastAPI(
            title=settings.APP_NAME,
            version=settings.APP_VERSION,
            description="一体化数字标牌管理系统",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        # 配置中间件和路由必须在应用启动前完成
        self._setup_middleware()
        self._register_routes()
        self._mount_static_files()
        self._setup_spa_routes()  # SPA 路由必须最后设置

    async def startup(self):
        """启动流程"""
        logger.info("=" * 50)
        logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} starting...")
        logger.info("=" * 50)

        # 1. 初始化数据库（测试模式下跳过）
        import os
        is_testing = os.environ.get("TESTING")
        if not is_testing:
            init_database()

        # 2. 创建必要目录
        self._create_directories()

        # 3. 启动后台任务调度器（测试模式下跳过）
        if not is_testing:
            start_scheduler()

        logger.info(f"✅ {settings.APP_NAME} started successfully")

    async def shutdown(self):
        """关闭流程"""
        logger.info("Shutting down...")
        stop_scheduler()

    def _create_directories(self):
        """创建必要的存储目录"""
        directories = [
            settings.UPLOADS_DIR,
            settings.CONVERTED_DIR,
            settings.THUMBNAILS_DIR,
            settings.BACKUPS_DIR,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _setup_middleware(self):
        """配置中间件"""
        setup_cors(self.app)

    def _register_routes(self):
        """注册 API 路由"""
        from app.api import auth, devices, media, playlists, player

        self.app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
        self.app.include_router(
            devices.router, prefix="/api/devices", tags=["设备"])
        self.app.include_router(media.router, prefix="/api/media", tags=["媒体"])
        self.app.include_router(
            playlists.router, prefix="/api/playlists", tags=["播放列表"])
        self.app.include_router(
            player.router, prefix="/api/player", tags=["播放端"])

    def _setup_spa_routes(self):
        """设置 SPA 路由（在所有 API 路由之后）"""
        from starlette.responses import FileResponse

        # 首页
        @self.app.get("/", include_in_schema=False)
        async def serve_index():
            index_html = _FRONTEND_DIST / "index.html"
            if index_html.exists():
                return FileResponse(str(index_html), media_type="text/html")
            return {"detail": "Not found"}

        # player.html
        @self.app.get("/player.html", include_in_schema=False)
        async def serve_player():
            player_html = _FRONTEND_DIST / "player.html"
            if player_html.exists():
                return FileResponse(str(player_html), media_type="text/html")
            return {"detail": "Not found"}

        # favicon
        @self.app.get("/favicon.svg", include_in_schema=False)
        async def serve_favicon():
            favicon = _FRONTEND_DIST / "favicon.svg"
            if favicon.exists():
                return FileResponse(str(favicon))
            return {"detail": "Not found"}

        # SPA fallback - 只处理非 API/静态文件路由
        @self.app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str):
            """SPA fallback: 处理前端路由"""
            # 跳过 API、docs、media 等路径
            if (full_path.startswith("api/") or
                full_path.startswith("docs") or
                full_path.startswith("redoc") or
                full_path.startswith("openapi") or
                full_path.startswith("media/") or
                full_path == "media"):
                return {"detail": "Not found"}

            if _FRONTEND_DIST.exists():
                # 处理 assets 目录下的静态文件
                if full_path.startswith("assets/"):
                    asset_file = _FRONTEND_DIST / full_path
                    if asset_file.exists() and asset_file.is_file():
                        return FileResponse(str(asset_file))

                # 处理其他静态文件
                static_file = _FRONTEND_DIST / full_path
                if static_file.exists() and static_file.is_file():
                    return FileResponse(str(static_file))

                # SPA fallback: 返回 index.html
                index_html = _FRONTEND_DIST / "index.html"
                if index_html.exists():
                    return FileResponse(str(index_html), media_type="text/html")

            return {"detail": "Not found"}

    def _mount_static_files(self):
        """挂载静态文件目录"""
        from fastapi.staticfiles import StaticFiles

        # 挂载媒体文件目录（缩略图、上传文件、转换文件）
        media_base = Path(__file__).parent.parent.parent / "data"
        if media_base.exists():
            self.app.mount("/media", StaticFiles(directory=str(media_base)), name="media")
            logger.info(f"✅ Mounted media files: {media_base}")

        # 挂载前端静态文件
        logger.info(f"🔍 Checking frontend dist: {_FRONTEND_DIST}")

        if not _FRONTEND_DIST.exists():
            logger.warning(f"⚠️ Frontend dist not found: {_FRONTEND_DIST}")
            return

        logger.info(f"✅ Frontend dist found: {_FRONTEND_DIST}")

        # 挂载 assets 目录
        assets_dir = _FRONTEND_DIST / "assets"
        if assets_dir.exists():
            self.app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
            logger.info(f"✅ Mounted assets: {assets_dir}")

    def get_app(self) -> FastAPI:
        """获取 FastAPI 实例"""
        return self.app


# 创建全局实例
bootstrap = ApplicationBootstrap()
