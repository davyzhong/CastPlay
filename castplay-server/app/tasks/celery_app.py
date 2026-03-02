"""
Celery Configuration
"""
import os

# 检查是否在测试环境
TESTING = os.environ.get('TESTING', 'false').lower() == 'true'

celery = None

if not TESTING:
    try:
        from celery import Celery as RealCelery

        def make_celery(app):
            """创建 Celery 实例"""
            celery_instance = RealCelery(
                app.import_name,
                broker=app.config.get(
                    'CELERY_BROKER_URL', 'redis://localhost:6379/0'),
                backend=app.config.get(
                    'CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
            )

            celery_instance.conf.update(app.config)

            class ContextTask(celery_instance.Task):
                def __call__(self, *args, **kwargs):
                    with app.app_context():
                        return self.run(*args, **kwargs)

            celery_instance.Task = ContextTask
            return celery_instance

        # 创建一个默认的 celery 实例用于任务装饰器
        # Redis URL 从环境变量获取，不硬编码密码
        def _build_redis_url() -> str:
            host = os.environ.get('REDIS_HOST', 'localhost')
            port = os.environ.get('REDIS_PORT', '6379')
            password = os.environ.get('REDIS_PASSWORD', '')
            db = os.environ.get('REDIS_DB', '0')
            if password:
                return f'redis://:{password}@{host}:{port}/{db}'
            return f'redis://{host}:{port}/{db}'

        REDIS_URL = os.environ.get('CELERY_BROKER_URL') or _build_redis_url()
        celery = RealCelery(
            'castplay',
            broker=REDIS_URL,
            backend=REDIS_URL
        )

    except ImportError:
        # Celery 未安装
        celery = None
else:
    # 测试环境中使用 Mock
    from unittest.mock import MagicMock

    class MockCelery:
        """Mock Celery for testing"""
        main = 'castplay'

        def task(self, *args, **kwargs):
            def decorator(func):
                # 返回一个 mock 任务
                mock_task = MagicMock()
                mock_task.__wrapped__ = func
                mock_task.delay = MagicMock(
                    return_value=MagicMock(id='mock-task-id'))
                mock_task.apply_async = MagicMock(
                    return_value=MagicMock(id='mock-task-id'))
                return mock_task
            return decorator

    celery = MockCelery()

    def make_celery(app):
        return celery
