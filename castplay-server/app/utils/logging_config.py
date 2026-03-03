"""
Structured Logging Configuration

使用 python-json-logger 实现 JSON 格式的结构化日志，便于日志收集和分析。

特性：
- JSON 格式输出（生产环境）
- 自动添加请求上下文（trace_id, user_id, device_id）
- 支持日志级别配置
- 兼容 ELK/Loki 等日志系统
"""
import logging
import sys
import uuid
from datetime import datetime
from typing import Optional
from flask import Flask, g, request, has_request_context

try:
    from pythonjsonlogger import jsonlogger
    JSON_LOGGER_AVAILABLE = True
except ImportError:
    JSON_LOGGER_AVAILABLE = False


class RequestContextFilter(logging.Filter):
    """
    日志过滤器：自动添加请求上下文信息
    """

    def filter(self, record):
        if has_request_context():
            record.trace_id = getattr(g, 'trace_id', '-')
            record.user_id = getattr(g, 'user_id', '-')
            record.device_id = request.args.get('device_id', '-')
            record.method = request.method
            record.path = request.path
            record.remote_addr = request.remote_addr
        else:
            record.trace_id = '-'
            record.user_id = '-'
            record.device_id = '-'
            record.method = '-'
            record.path = '-'
            record.remote_addr = '-'
        return True


class CustomJsonFormatter(jsonlogger.JsonFormatter if JSON_LOGGER_AVAILABLE else logging.Formatter):
    """
    自定义 JSON 格式化器
    """

    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(
            log_record, record, message_dict)

        # 添加时间戳
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        log_record['level'] = record.levelname
        log_record['logger'] = record.name

        # 添加服务标识
        log_record['service'] = 'castplay-server'

        # 添加请求上下文
        if hasattr(record, 'trace_id'):
            log_record['trace_id'] = record.trace_id
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        if hasattr(record, 'device_id'):
            log_record['device_id'] = record.device_id


def setup_logging(app: Flask) -> None:
    """
    配置应用日志系统

    Args:
        app: Flask 应用实例
    """
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    is_production = not app.config.get('DEBUG', False)

    # 创建根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))

    # 移除默认处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))

    # 添加请求上下文过滤器
    console_handler.addFilter(RequestContextFilter())

    # 根据环境选择格式
    if is_production and JSON_LOGGER_AVAILABLE:
        # 生产环境：JSON 格式
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        # 开发环境：可读格式
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s [%(trace_id)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 配置 Werkzeug 日志（Flask 内置服务器）
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(
        logging.WARNING if is_production else logging.INFO)

    # 配置 SQLAlchemy 日志
    sqlalchemy_logger = logging.getLogger('sqlalchemy.engine')
    sqlalchemy_logger.setLevel(logging.WARNING)

    app.logger.info(
        f"Logging configured: level={log_level}, json={is_production and JSON_LOGGER_AVAILABLE}")


def init_request_context() -> None:
    """
    初始化请求上下文（在 before_request 中调用）
    """
    g.trace_id = request.headers.get('X-Trace-ID', str(uuid.uuid4())[:8])


def log_request_info(response):
    """
    记录请求信息（在 after_request 中调用）
    """
    logger = logging.getLogger('access')

    # 计算请求耗时
    duration = getattr(g, 'request_duration', 0)

    logger.info(
        'Request completed',
        extra={
            'status_code': response.status_code,
            'duration_ms': duration,
            'content_length': response.content_length,
        }
    )

    return response


def register_logging_hooks(app: Flask) -> None:
    """
    注册日志钩子
    """
    import time

    @app.before_request
    def before_request():
        g.request_start_time = time.time()
        init_request_context()

    @app.after_request
    def after_request(response):
        if hasattr(g, 'request_start_time'):
            g.request_duration = round(
                (time.time() - g.request_start_time) * 1000, 2)
        return log_request_info(response)
