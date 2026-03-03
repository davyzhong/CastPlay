"""
Prometheus Metrics for CastPlay Server

提供应用级监控指标，支持 Prometheus 抓取。

指标类型：
- Counter: 累计计数（请求数、错误数）
- Gauge: 瞬时值（连接数、队列长度）
- Histogram: 分布统计（响应时间）
- Summary: 摘要统计（百分位数）
"""
import time
from functools import wraps
from typing import Callable

from flask import Flask, request, g
from prometheus_client import Counter, Gauge, Histogram, Summary, generate_latest, CONTENT_TYPE_LATEST


# ==================== Metrics Definitions ====================

# HTTP 请求计数
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# HTTP 请求耗时
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# 活跃连接数
active_connections = Gauge(
    'active_connections',
    'Number of active connections',
    ['type']  # websocket, http
)

# WebSocket 连接数
websocket_connections = Gauge(
    'websocket_connections_total',
    'Total WebSocket connections'
)

# 设备在线数
devices_online = Gauge(
    'devices_online_total',
    'Number of online devices'
)

# 媒体文件数
media_files_total = Gauge(
    'media_files_total',
    'Total media files',
    ['type', 'status']  # type: image/video/ppt, status: ready/processing/error
)

# Celery 任务计数
celery_tasks_total = Counter(
    'celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status']  # status: success/failure
)

# Celery 任务耗时
celery_task_duration_seconds = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name'],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0)
)

# 数据库查询计数
db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['operation']  # select/insert/update/delete
)


# ==================== Helper Functions ====================

def track_request_metrics(response):
    """
    追踪 HTTP 请求指标（在 after_request 中调用）
    """
    # 获取端点名称
    endpoint = request.endpoint or 'unknown'
    method = request.method
    status = str(response.status_code)

    # 计算请求耗时
    duration = getattr(g, 'request_duration', 0) / 1000  # 转换为秒

    # 更新指标
    http_requests_total.labels(
        method=method, endpoint=endpoint, status=status).inc()
    http_request_duration_seconds.labels(
        method=method, endpoint=endpoint).observe(duration)

    return response


def track_celery_task(task_name: str) -> Callable:
    """
    装饰器：追踪 Celery 任务指标

    Usage:
        @track_celery_task('convert_ppt')
        def convert_ppt_task(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'failure'
                raise
            finally:
                duration = time.time() - start_time
                celery_tasks_total.labels(
                    task_name=task_name, status=status).inc()
                celery_task_duration_seconds.labels(
                    task_name=task_name).observe(duration)
        return wrapper
    return decorator


def update_device_count(count: int) -> None:
    """更新设备在线数"""
    devices_online.set(count)


def update_media_count(media_type: str, status: str, count: int) -> None:
    """更新媒体文件数"""
    media_files_total.labels(type=media_type, status=status).set(count)


def increment_websocket_connections() -> None:
    """WebSocket 连接数 +1"""
    websocket_connections.inc()
    active_connections.labels(type='websocket').inc()


def decrement_websocket_connections() -> None:
    """WebSocket 连接数 -1"""
    websocket_connections.dec()
    active_connections.labels(type='websocket').dec()


# ==================== Flask Integration ====================

def init_metrics(app: Flask) -> None:
    """
    初始化 Prometheus 指标端点

    Args:
        app: Flask 应用实例
    """
    @app.route('/metrics')
    def metrics():
        """Prometheus 指标端点"""
        return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

    @app.after_request
    def after_request(response):
        """追踪请求指标"""
        # 跳过 metrics 端点自身
        if request.endpoint != 'metrics':
            track_request_metrics(response)
        return response

    app.logger.info("Prometheus metrics initialized at /metrics")
