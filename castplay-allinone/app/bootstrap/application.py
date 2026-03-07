"""
应用引导模块
负责所有初始化逻辑，避免 main.py 膨胀
"""
from pathlib import Path
from fastapi import FastAPI
from app.config import settings
from app.database import init_database
from app.scheduler import start as start_scheduler, stop as stop_scheduler
from app.middleware.cors import setup_cors
from app.utils.logger import logger


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

        # 3. 配置中间件
        self._setup_middleware()

        # 4. 注册路由
        self._register_routes()

        # 5. 启动后台任务调度器（测试模式下跳过）
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
        # 其他中间件可以在这里添加

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

        # 挂载静态文件（前端）
        frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
        if frontend_dist.exists():
            from fastapi.staticfiles import StaticFiles
            self.app.mount(
                "/", StaticFiles(directory=str(frontend_dist), html=True), name="static")

    def get_app(self) -> FastAPI:
        """获取 FastAPI 实例"""
        return self.app


# 创建全局实例
bootstrap = ApplicationBootstrap()
