"""
API路由定义
定义所有的API端点和路由处理函数
"""
import logging
from typing import Dict, Any
from datetime import datetime
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from .schemas import SignalQueryRequest, SignalQueryResponse, ErrorResponse, HealthCheckResponse
from .services import signal_service

logger = logging.getLogger(__name__)

# 创建蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')


@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    健康检查端点
    
    Returns:
        JSON: 服务健康状态
    """
    try:
        health_info = signal_service.check_health()
        return jsonify(health_info), 200
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        error_response = {
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }
        return jsonify(error_response), 500


@api_bp.route('/signals', methods=['POST'])
def query_signals():
    """
    查询技术信号端点
    
    Request Body:
        {
            "symbol": "BTC",
            "timeframes": ["5m", "15m", "1h", "1d"]  // 可选
        }
    
    Returns:
        JSON: 技术信号查询结果
    """
    try:
        # 解析请求数据
        request_data = request.get_json()
        if not request_data:
            return jsonify({
                'success': False,
                'message': '请求体不能为空',
                'error_code': 'INVALID_REQUEST_BODY',
                'details': {'received': 'empty'}
            }), 400
        
        # 验证请求数据
        try:
            query_request = SignalQueryRequest(**request_data)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'message': '请求参数验证失败',
                'error_code': 'VALIDATION_ERROR',
                'details': {'errors': e.errors()}
            }), 400
        
        # 调用服务查询信号
        signal_data = signal_service.get_recent_signals(
            symbol=query_request.symbol,
            timeframes=query_request.timeframes
        )
        
        # 构建响应
        response = {
            'success': True,
            'message': '查询成功',
            'data': signal_data
        }
        
        return jsonify(response), 200
        
    except ValueError as e:
        # 业务逻辑错误（如不支持的币种）
        logger.warning(f"查询参数错误: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'error_code': 'INVALID_PARAMETER',
            'details': {'symbol': request_data.get('symbol') if request_data else None}
        }), 400
        
    except Exception as e:
        # 服务器内部错误
        logger.error(f"查询技术信号时发生错误: {e}")
        return jsonify({
            'success': False,
            'message': '服务器内部错误',
            'error_code': 'INTERNAL_SERVER_ERROR',
            'details': {'error': str(e)}
        }), 500


@api_bp.route('/signals/<symbol>', methods=['GET'])
def query_signals_by_symbol(symbol: str):
    """
    通过URL参数查询技术信号的GET端点
    
    URL Parameters:
        symbol (str): 币种符号
        
    Query Parameters:
        timeframes (str): 逗号分隔的时间周期列表，如 "5m,15m,1h"
    
    Returns:
        JSON: 技术信号查询结果
    """
    try:
        # 获取查询参数
        timeframes_param = request.args.get('timeframes')
        timeframes = None
        if timeframes_param:
            timeframes = [tf.strip() for tf in timeframes_param.split(',') if tf.strip()]
        
        # 验证请求数据
        try:
            query_request = SignalQueryRequest(symbol=symbol, timeframes=timeframes)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'message': '请求参数验证失败',
                'error_code': 'VALIDATION_ERROR',
                'details': {'errors': e.errors()}
            }), 400
        
        # 调用服务查询信号
        signal_data = signal_service.get_recent_signals(
            symbol=query_request.symbol,
            timeframes=query_request.timeframes
        )
        
        # 构建响应
        response = {
            'success': True,
            'message': '查询成功',
            'data': signal_data
        }
        
        return jsonify(response), 200
        
    except ValueError as e:
        # 业务逻辑错误
        logger.warning(f"查询参数错误: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'error_code': 'INVALID_PARAMETER',
            'details': {'symbol': symbol, 'timeframes': timeframes_param}
        }), 400
        
    except Exception as e:
        # 服务器内部错误
        logger.error(f"查询技术信号时发生错误: {e}")
        return jsonify({
            'success': False,
            'message': '服务器内部错误',
            'error_code': 'INTERNAL_SERVER_ERROR',
            'details': {'error': str(e)}
        }), 500


@api_bp.route('/symbols', methods=['GET'])
def get_supported_symbols():
    """
    获取支持的币种列表
    
    Returns:
        JSON: 支持的币种列表
    """
    try:
        response = {
            'success': True,
            'message': '获取支持的币种列表成功',
            'data': {
                'symbols': signal_service.supported_symbols,
                'timeframes': signal_service.supported_timeframes,
                'total_symbols': len(signal_service.supported_symbols),
                'total_timeframes': len(signal_service.supported_timeframes)
            }
        }
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"获取支持币种列表失败: {e}")
        return jsonify({
            'success': False,
            'message': '获取支持币种列表失败',
            'error_code': 'INTERNAL_SERVER_ERROR',
            'details': {'error': str(e)}
        }), 500


@api_bp.route('/docs', methods=['GET'])
def api_documentation():
    """
    API文档端点
    
    Returns:
        JSON: API使用文档
    """
    docs = {
        'api_version': 'v1',
        'title': '加密货币技术信号查询API',
        'description': '提供加密货币技术分析信号的查询服务',
        'endpoints': {
            'health_check': {
                'method': 'GET',
                'path': '/api/v1/health',
                'description': '检查API服务健康状态',
                'response': 'HealthCheckResponse'
            },
            'query_signals_post': {
                'method': 'POST',
                'path': '/api/v1/signals',
                'description': '查询指定币种的技术信号（POST方式）',
                'request_body': {
                    'symbol': 'str (必填) - 币种符号，如BTC、ETH',
                    'timeframes': 'List[str] (可选) - 时间周期列表，如["5m", "15m", "1h", "1d"]'
                },
                'response': 'SignalQueryResponse'
            },
            'query_signals_get': {
                'method': 'GET',
                'path': '/api/v1/signals/<symbol>',
                'description': '查询指定币种的技术信号（GET方式）',
                'parameters': {
                    'symbol': 'str (路径参数) - 币种符号',
                    'timeframes': 'str (查询参数) - 逗号分隔的时间周期，如"5m,15m,1h"'
                },
                'response': 'SignalQueryResponse'
            },
            'supported_symbols': {
                'method': 'GET',
                'path': '/api/v1/symbols',
                'description': '获取支持的币种和时间周期列表',
                'response': 'SupportedDataResponse'
            }
        },
        'supported_symbols': signal_service.supported_symbols,
        'supported_timeframes': signal_service.supported_timeframes,
        'example_requests': {
            'post_example': {
                'url': '/api/v1/signals',
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'},
                'body': {
                    'symbol': 'BTC',
                    'timeframes': ['5m', '1h']
                }
            },
            'get_example': {
                'url': '/api/v1/signals/BTC?timeframes=5m,1h',
                'method': 'GET'
            }
        }
    }
    
    return jsonify(docs), 200


# 错误处理器
@api_bp.errorhandler(404)
def not_found_error(error):
    """处理404错误"""
    return jsonify({
        'success': False,
        'message': '请求的资源不存在',
        'error_code': 'NOT_FOUND',
        'details': {'path': request.path}
    }), 404


@api_bp.errorhandler(405)
def method_not_allowed_error(error):
    """处理405错误"""
    return jsonify({
        'success': False,
        'message': '请求方法不被允许',
        'error_code': 'METHOD_NOT_ALLOWED',
        'details': {'method': request.method, 'path': request.path}
    }), 405


@api_bp.errorhandler(500)
def internal_error(error):
    """处理500错误"""
    return jsonify({
        'success': False,
        'message': '服务器内部错误',
        'error_code': 'INTERNAL_SERVER_ERROR',
        'details': {'error': str(error)}
    }), 500 