"""CastPlay Server Application Factory"""
import os
import logging
from typing import Optional

from flask import Flask, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_socketio import SocketIO
from werkzeug.exceptions import HTTPException

from config import config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Extensions
db = SQLAlchemy()
migrate = Migrate()
# SocketIO 初始化时不设置 cors_allowed_origins，在 init_app 时配置
socketio = SocketIO()


def create_app(config_name: str = 'default') -> Flask:
    """Application factory pattern

    Args:
        config_name: 配置名称 (development/production/testing/default)

    Returns:
        Flask 应用实例
    """
    app = Flask(__name__)

    # 加载配置
    config_class = config[config_name]
    app.config.from_object(config_class)

    # 调用配置类的初始化钩子
    if hasattr(config_class, 'init_app'):
        config_class.init_app(app)

    # 配置日志级别
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    logging.getLogger().setLevel(getattr(logging, log_level))

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # CORS 配置 - 使用配置的源列表，而非 '*'
    cors_origins = app.config.get('CORS_ORIGINS', [])
    CORS(app, resources={
        r"/api/*": {
            "origins": cors_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # SocketIO 配置 - 使用配置的源列表
    socketio.init_app(
        app,
        cors_allowed_origins=cors_origins,
        message_queue=app.config.get('SOCKETIO_MESSAGE_QUEUE'),
        logger=True,
        engineio_logger=True if app.config.get('DEBUG') else False
    )

    # 注册全局异常处理器
    _register_error_handlers(app)

    # Register blueprints
    from app.api import device, media, playlist, player, folder
    app.register_blueprint(device.bp, url_prefix='/api/devices')
    app.register_blueprint(media.bp, url_prefix='/api/media')
    app.register_blueprint(playlist.bp, url_prefix='/api/playlists')
    app.register_blueprint(player.bp, url_prefix='/api/player')
    app.register_blueprint(folder.bp, url_prefix='/api/folders')

    # Import WebSocket handlers (auto-registered via decorators)
    from app.websocket import handler  # noqa: F401

    # Create storage directories
    for folder_path in [
        app.config['UPLOAD_FOLDER'],
        app.config['CONVERTED_FOLDER'],
        app.config['THUMBNAIL_FOLDER']
    ]:
        os.makedirs(folder_path, exist_ok=True)

    # Create database tables if not exist
    with app.app_context():
        db.create_all()

    @app.route('/health')
    def health_check():
        """健康检查端点"""
        return {'status': 'ok', 'service': 'castplay-server'}, 200

    # 网页播放器测试页面
    @app.route('/player')
    def web_player():
        static_dir = os.path.join(os.path.dirname(
            os.path.dirname(__file__)), 'static')
        return send_from_directory(static_dir, 'player.html')

    logger.info(f"CastPlay Server initialized with config: {config_name}")

    return app


def _register_error_handlers(app: Flask) -> None:
    """注册全局异常处理器

    Args:
        app: Flask 应用实例
    """

    @app.errorhandler(400)
    def bad_request(error):
        """处理 400 Bad Request"""
        return jsonify({
            'error': 'Bad Request',
            'message': str(error.description) if hasattr(error, 'description') else '请求参数错误'
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        """处理 401 Unauthorized"""
        return jsonify({
            'error': 'Unauthorized',
            'message': '未授权访问，请先登录'
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        """处理 403 Forbidden"""
        return jsonify({
            'error': 'Forbidden',
            'message': '没有权限访问此资源'
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        """处理 404 Not Found"""
        return jsonify({
            'error': 'Not Found',
            'message': '请求的资源不存在'
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        """处理 405 Method Not Allowed"""
        return jsonify({
            'error': 'Method Not Allowed',
            'message': '不支持的请求方法'
        }), 405

    @app.errorhandler(422)
    def unprocessable_entity(error):
        """处理 422 Unprocessable Entity"""
        return jsonify({
            'error': 'Unprocessable Entity',
            'message': str(error.description) if hasattr(error, 'description') else '无法处理的请求数据'
        }), 422

    @app.errorhandler(500)
    def internal_server_error(error):
        """处理 500 Internal Server Error"""
        logger.error(f"Internal Server Error: {error}", exc_info=True)
        return jsonify({
            'error': 'Internal Server Error',
            'message': '服务器内部错误，请稍后重试'
        }), 500

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """处理其他 HTTP 异常"""
        return jsonify({
            'error': error.name,
            'message': error.description
        }), error.code

    @app.errorhandler(Exception)
    def handle_exception(error):
        """处理未捕获的异常"""
        logger.error(f"Unhandled Exception: {error}", exc_info=True)
        # 生产环境不暴露详细错误信息
        if app.config.get('DEBUG'):
            message = str(error)
        else:
            message = '服务器内部错误，请稍后重试'
        return jsonify({
            'error': 'Internal Server Error',
            'message': message
        }), 500
