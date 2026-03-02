"""
API Request Validators
提供请求数据验证功能
"""
import logging
from functools import wraps
from typing import Dict, Any, List, Optional, Callable, Type, Union

from flask import request, jsonify

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """验证错误异常"""

    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


def validate_json_data(
    required_fields: Optional[List[str]] = None,
    optional_fields: Optional[List[str]] = None,
    field_types: Optional[Dict[str, Type]] = None,
    field_validators: Optional[Dict[str, Callable[[Any], bool]]] = None
) -> Callable:
    """
    JSON数据验证装饰器

    Args:
        required_fields: 必需字段列表
        optional_fields: 可选字段列表
        field_types: 字段类型映射 {field_name: type}
        field_validators: 字段验证函数 {field_name: validator_func}

    Usage:
        @validate_json_data(
            required_fields=['name'],
            field_types={'name': str, 'count': int},
            field_validators={'name': lambda x: len(x) <= 128}
        )
        def create_item():
            ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 检查Content-Type
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400

            data = request.get_json(silent=True)
            if data is None:
                return jsonify({'error': 'Invalid JSON data'}), 400

            # 验证必需字段
            if required_fields:
                missing = [
                    f for f in required_fields if f not in data or data[f] is None]
                if missing:
                    return jsonify({
                        'error': f"Missing required fields: {', '.join(missing)}"
                    }), 400

            # 验证字段类型
            if field_types:
                for field, expected_type in field_types.items():
                    if field in data and data[field] is not None:
                        if not isinstance(data[field], expected_type):
                            return jsonify({
                                'error': f"Field '{field}' must be of type {expected_type.__name__}"
                            }), 400

            # 自定义验证器
            if field_validators:
                for field, validator in field_validators.items():
                    if field in data and data[field] is not None:
                        try:
                            if not validator(data[field]):
                                return jsonify({
                                    'error': f"Field '{field}' validation failed"
                                }), 400
                        except Exception as e:
                            logger.warning(
                                f"Validator error for field '{field}': {e}")
                            return jsonify({
                                'error': f"Field '{field}' validation error"
                            }), 400

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def validate_query_params(
    required_params: Optional[List[str]] = None,
    param_types: Optional[Dict[str, Type]] = None,
    param_validators: Optional[Dict[str, Callable[[Any], bool]]] = None
) -> Callable:
    """
    查询参数验证装饰器

    Args:
        required_params: 必需参数列表
        param_types: 参数类型映射
        param_validators: 参数验证函数
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 验证必需参数
            if required_params:
                missing = [
                    p for p in required_params if request.args.get(p) is None]
                if missing:
                    return jsonify({
                        'error': f"Missing required query parameters: {', '.join(missing)}"
                    }), 400

            # 验证参数类型（主要是数值转换）
            if param_types:
                for param, expected_type in param_types.items():
                    value = request.args.get(param)
                    if value is not None:
                        try:
                            if expected_type == int:
                                int(value)
                            elif expected_type == float:
                                float(value)
                            elif expected_type == bool:
                                if value.lower() not in ('true', 'false', '1', '0'):
                                    raise ValueError("Invalid boolean")
                        except ValueError:
                            return jsonify({
                                'error': f"Parameter '{param}' must be of type {expected_type.__name__}"
                            }), 400

            # 自定义验证
            if param_validators:
                for param, validator in param_validators.items():
                    value = request.args.get(param)
                    if value is not None:
                        try:
                            if not validator(value):
                                return jsonify({
                                    'error': f"Parameter '{param}' validation failed"
                                }), 400
                        except Exception as e:
                            logger.warning(
                                f"Validator error for param '{param}': {e}")
                            return jsonify({
                                'error': f"Parameter '{param}' validation error"
                            }), 400

            return f(*args, **kwargs)
        return decorated_function
    return decorator


# 常用验证器函数
def max_length(max_len: int) -> Callable[[str], bool]:
    """字符串最大长度验证器"""
    return lambda x: isinstance(x, str) and len(x) <= max_len


def min_length(min_len: int) -> Callable[[str], bool]:
    """字符串最小长度验证器"""
    return lambda x: isinstance(x, str) and len(x) >= min_len


def length_between(min_len: int, max_len: int) -> Callable[[str], bool]:
    """字符串长度范围验证器"""
    return lambda x: isinstance(x, str) and min_len <= len(x) <= max_len


def in_range(min_val: Union[int, float], max_val: Union[int, float]) -> Callable[[Union[int, float]], bool]:
    """数值范围验证器"""
    return lambda x: isinstance(x, (int, float)) and min_val <= x <= max_val


def positive_number(x: Union[int, float]) -> bool:
    """正数验证器"""
    return isinstance(x, (int, float)) and x > 0


def non_negative(x: Union[int, float]) -> bool:
    """非负数验证器"""
    return isinstance(x, (int, float)) and x >= 0


def is_in(allowed_values: List[Any]) -> Callable[[Any], bool]:
    """枚举值验证器"""
    return lambda x: x in allowed_values


def is_list_of(item_type: Type) -> Callable[[List], bool]:
    """列表元素类型验证器"""
    return lambda x: isinstance(x, list) and all(isinstance(i, item_type) for i in x)


def non_empty_list(x: List) -> bool:
    """非空列表验证器"""
    return isinstance(x, list) and len(x) > 0
