"""
预警系统API路由
提供RESTful API接口
"""
import json
import logging
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from datetime import datetime
from .models import (
    QueryRequest, AlertRule, QueryCondition, LogicalCondition,
    QueryField, QueryOperator, AlertTriggerType, AlertFrequency
)
from .query_engine import QueryEngine
from .alert_manager import AlertManager
from .webhook_client import LarkWebhookClient
from utils.request_utils import RequestIDGenerator, ResponseFormatter, ALERT_FIELD_DESCRIPTIONS

logger = logging.getLogger(__name__)


alerts_bp = Blueprint('alerts', __name__, url_prefix='/api/v1/alerts')

query_engine = QueryEngine()
alert_manager = AlertManager()
webhook_client = LarkWebhookClient()


def extract_request_id(data: dict = None) -> str:
    """从请求数据中提取或生成request_id"""
    if data and 'request_id' in data:
        return data['request_id']
    return RequestIDGenerator.generate()


@alerts_bp.route('/health', methods=['GET'])
async def health_check():
    """预警系统健康检查"""
    try:
        request_id = RequestIDGenerator.generate()
        stats = await alert_manager.get_alert_stats()
        
        return jsonify(
            ResponseFormatter.format_success(
                request_id,
                {
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "stats": stats.dict()
                },
                "预警系统健康检查成功"
            )
        )
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return jsonify(
            ResponseFormatter.format_error(
                "unknown",
                f"健康检查失败: {str(e)}",
                "HEALTH_CHECK_ERROR"
            )
        ), 500


@alerts_bp.route('/query', methods=['POST'])
async def execute_flexible_query():
    """
    执行灵活查询
    
    请求体示例:
    {
        "request_id": "req_123456_abc123", 
        "symbol": "BTC",
        "timeframes": ["1h", "1d"],
        "conditions": {
            "field": "close",
            "operator": "gt", 
            "value": 50000
        },
        "limit": 50,
        "sort_by": "timestamp",
        "sort_order": "desc"
    }
    """
    try:
        data = request.json or {}
        request_id = extract_request_id(data)
        
        query_request = QueryRequest(**data)
        
        result = await query_engine.execute_query(query_request)
        
        return jsonify(
            ResponseFormatter.format_success(
                request_id,
                result.dict(),
                "查询执行成功"
            )
        )
        
    except ValidationError as e:
        return jsonify(
            ResponseFormatter.format_error(
                extract_request_id(data if 'data' in locals() else {}),
                "请求参数验证失败",
                "VALIDATION_ERROR",
                {"validation_errors": e.errors()}
            )
        ), 400
    except Exception as e:
        logger.error(f"查询执行失败: {e}")
        return jsonify(
            ResponseFormatter.format_error(
                extract_request_id(data if 'data' in locals() else {}),
                f"查询执行失败: {str(e)}",
                "QUERY_ERROR"
            )
        ), 500


@alerts_bp.route('/query/signals', methods=['POST'])
async def query_signals():
    """
    
    请求体示例:
    {
        "symbol": "BTC",
        "timeframes": ["1h"],
        "signal_names": ["RSI_OVERSOLD", "MACD_GOLDEN_CROSS"],
        "periods": 24
    }
    """
    try:
        data = request.json
        symbol = data.get("symbol", "BTC")
        timeframes = data.get("timeframes", ["1h"])
        signal_names = data.get("signal_names", [])
        periods = data.get("periods", 24)
        
        if not signal_names:
            return jsonify({"error": "signal_names参数不能为空"}), 400
        
        conditions = LogicalCondition(
            operator="and",
            conditions=[
                QueryCondition(
                    field=QueryField.SIGNALS,
                    operator=QueryOperator.CONTAINS,
                    value=signal_names
                ),
                QueryCondition(
                    field=QueryField.TIMESTAMP,
                    operator=QueryOperator.WITHIN_LAST,
                    value=periods
                )
            ]
        )
        
        query_request = QueryRequest(
            symbol=symbol,
            timeframes=timeframes,
            conditions=conditions,
            limit=100
        )
        
        result = await query_engine.execute_query(query_request)
        
        signal_analysis = _analyze_signal_results(result.data, signal_names)
        
        return jsonify({
            **result.dict(),
            "signal_analysis": signal_analysis
        })
        
    except Exception as e:
        logger.error(f"信号查询失败: {e}")
        return jsonify({"error": str(e)}), 500


@alerts_bp.route('/query/price-analysis', methods=['POST'])
async def price_analysis():
    """

    请求体示例:
    {
        "symbol": "BTC",
        "timeframes": ["1h"],
        "analysis_type": "breakout",
        "price_level": 50000,
        "periods": 48
    }
    """
    try:
        data = request.json
        symbol = data.get("symbol", "BTC")
        timeframes = data.get("timeframes", ["1h"])
        analysis_type = data.get("analysis_type", "breakout")
        price_level = data.get("price_level")
        periods = data.get("periods", 48)
        
        if not price_level:
            return jsonify({"error": "price_level参数不能为空"}), 400
        
        if analysis_type == "breakout":
            conditions = LogicalCondition(
                operator="and",
                conditions=[
                    QueryCondition(
                        field=QueryField.HIGH,
                        operator=QueryOperator.GT,
                        value=price_level
                    ),
                    QueryCondition(
                        field=QueryField.TIMESTAMP,
                        operator=QueryOperator.WITHIN_LAST,
                        value=periods
                    )
                ]
            )
        elif analysis_type == "support":
            conditions = LogicalCondition(
                operator="and",
                conditions=[
                    QueryCondition(
                        field=QueryField.LOW,
                        operator=QueryOperator.LTE,
                        value=price_level
                    ),
                    QueryCondition(
                        field=QueryField.CLOSE,
                        operator=QueryOperator.GT,
                        value=price_level
                    ),
                    QueryCondition(
                        field=QueryField.TIMESTAMP,
                        operator=QueryOperator.WITHIN_LAST,
                        value=periods
                    )
                ]
            )
        else:
            return jsonify({"error": f"不支持的分析类型: {analysis_type}"}), 400
        
        query_request = QueryRequest(
            symbol=symbol,
            timeframes=timeframes,
            conditions=conditions,
            limit=50
        )
        
        result = await query_engine.execute_query(query_request)
        
        price_stats = _analyze_price_results(result.data, price_level, analysis_type)
        
        return jsonify({
            **result.dict(),
            "price_analysis": price_stats
        })
        
    except Exception as e:
        logger.error(f"价格分析失败: {e}")
        return jsonify({"error": str(e)}), 500


@alerts_bp.route('/query/indicator-extremes', methods=['POST'])
async def indicator_extremes():
    """
    请求体示例:
    {
        "symbol": "BTC",
        "timeframes": ["1h"],
        "indicator": "rsi",
        "comparison": "historical_high",
        "lookback_periods": 100
    }
    """
    try:
        data = request.json
        symbol = data.get("symbol", "BTC")
        timeframes = data.get("timeframes", ["1h"])
        indicator = data.get("indicator", "rsi")
        comparison = data.get("comparison", "historical_high")
        lookback_periods = data.get("lookback_periods", 100)
        
        valid_indicators = {
            "rsi": QueryField.RSI,
            "cci": QueryField.CCI,
            "macd_line": QueryField.MACD_LINE,
            "ma_20": QueryField.MA_20
        }
        
        if indicator not in valid_indicators:
            return jsonify({"error": f"不支持的指标: {indicator}"}), 400
        
        indicator_field = valid_indicators[indicator]
        
        stats = await query_engine.get_historical_stats(
            symbol=symbol,
            field=indicator_field, 
            timeframes=timeframes,
            periods=lookback_periods
        )
        
        conditions_list = []
        
        for timeframe in timeframes:
            tf_stats = stats.get(timeframe, {})
            
            if comparison == "historical_high":
                if tf_stats.get("max"):
                    threshold = tf_stats["max"] * 0.95
                    conditions_list.append(
                        LogicalCondition(
                            operator="and",
                            conditions=[
                                QueryCondition(
                                    field=indicator_field,
                                    operator=QueryOperator.GTE,
                                    value=threshold
                                ),
                                QueryCondition(
                                    field=QueryField.TIMEFRAME,
                                    operator=QueryOperator.EQ,
                                    value=timeframe
                                )
                            ]
                        )
                    )
            elif comparison == "historical_low":
                if tf_stats.get("min"):
                    threshold = tf_stats["min"] * 1.05
                    conditions_list.append(
                        LogicalCondition(
                            operator="and",
                            conditions=[
                                QueryCondition(
                                    field=indicator_field,
                                    operator=QueryOperator.LTE,
                                    value=threshold
                                ),
                                QueryCondition(
                                    field=QueryField.TIMEFRAME,
                                    operator=QueryOperator.EQ,
                                    value=timeframe
                                )
                            ]
                        )
                    )
        
        if not conditions_list:
            return jsonify({
                "matched_records": 0,
                "message": "没有足够的历史数据进行比较",
                "stats": stats
            })
        
        if len(conditions_list) == 1:
            final_conditions = conditions_list[0]
        else:
            final_conditions = LogicalCondition(
                operator="or",
                conditions=conditions_list
            )
        
        query_request = QueryRequest(
            symbol=symbol,
            timeframes=timeframes,
            conditions=final_conditions,
            limit=20
        )
        
        result = await query_engine.execute_query(query_request)
        
        return jsonify({
            **result.dict(),
            "historical_stats": stats,
            "comparison_type": comparison,
            "indicator": indicator
        })
        
    except Exception as e:
        logger.error(f"指标极值查询失败: {e}")
        return jsonify({"error": str(e)}), 500


@alerts_bp.route('/rules', methods=['POST'])
async def create_alert_rule():
    """
    创建预警规则
    
    请求体示例:
    {
        "request_id": "req_123456_abc123",
        "name": "BTC价格突破50000",
        "description": "BTC价格突破50000美元时发送预警",
        "symbol": "BTC",
        "timeframes": ["1h"],
        "trigger_type": "price_threshold",
        "trigger_conditions": {
            "field": "close",
            "operator": "gt",
            "value": 50000
        },
        "frequency": "once",
        "webhook_url": "https://...",
        "custom_message": "BTC价格突破$50,000!"
    }
    """
    try:
        data = request.json or {}
        request_id = extract_request_id(data)
        
        # 移除request_id避免Pydantic验证错误
        rule_data = {k: v for k, v in data.items() if k != 'request_id'}
        alert_rule = AlertRule(**rule_data)
        
        rule_id = await alert_manager.create_alert_rule(alert_rule)
        
        # 构建响应数据
        result_data = {
            "rule_id": rule_id,
            "rule_name": alert_rule.name,
            "symbol": alert_rule.symbol,
            "monitoring_status": "active" if alert_rule.is_active else "inactive",
            "created_time": alert_rule.created_at.isoformat() if alert_rule.created_at else datetime.utcnow().isoformat()
        }
        
        return jsonify(
            ResponseFormatter.format_mcp_response(
                request_id,
                result_data,
                ALERT_FIELD_DESCRIPTIONS
            )
        ), 201
        
    except ValidationError as e:
        return jsonify(
            ResponseFormatter.format_error(
                extract_request_id(data if 'data' in locals() else {}),
                "请求参数验证失败",
                "VALIDATION_ERROR",
                {"validation_errors": e.errors()}
            )
        ), 400
    except Exception as e:
        logger.error(f"创建预警规则失败: {e}")
        return jsonify(
            ResponseFormatter.format_error(
                extract_request_id(data if 'data' in locals() else {}),
                f"创建预警规则失败: {str(e)}",
                "CREATE_RULE_ERROR"
            )
        ), 500


@alerts_bp.route('/rules', methods=['GET'])
async def list_alert_rules():
    """列出预警规则"""
    try:
        request_id = RequestIDGenerator.generate()
        symbol = request.args.get('symbol')
        is_active = request.args.get('is_active')
        limit = int(request.args.get('limit', 100))

        if is_active is not None:
            is_active = is_active.lower() in ['true', '1', 'yes']
        
        rules = await alert_manager.list_alert_rules(
            symbol=symbol,
            is_active=is_active,
            limit=limit
        )
        
        result_data = {
            "rules": [rule.dict() for rule in rules],
            "total": len(rules),
            "filter_symbol": symbol,
            "filter_active": is_active
        }
        
        return jsonify(
            ResponseFormatter.format_success(
                request_id,
                result_data,
                "预警规则列表获取成功"
            )
        )
        
    except Exception as e:
        logger.error(f"列出预警规则失败: {e}")
        return jsonify(
            ResponseFormatter.format_error(
                "unknown",
                f"列出预警规则失败: {str(e)}",
                "LIST_RULES_ERROR"
            )
        ), 500


@alerts_bp.route('/rules/<rule_id>', methods=['GET'])
async def get_alert_rule(rule_id):
    """获取预警规则详情"""
    try:
        request_id = RequestIDGenerator.generate()
        rule = await alert_manager.get_alert_rule(rule_id)
        
        if not rule:
            return jsonify(
                ResponseFormatter.format_error(
                    request_id,
                    "预警规则不存在",
                    "RULE_NOT_FOUND"
                )
            ), 404
        
        return jsonify(
            ResponseFormatter.format_mcp_response(
                request_id,
                rule.dict(),
                ALERT_FIELD_DESCRIPTIONS
            )
        )
        
    except Exception as e:
        logger.error(f"获取预警规则失败: {e}")
        return jsonify(
            ResponseFormatter.format_error(
                "unknown",
                f"获取预警规则失败: {str(e)}",
                "GET_RULE_ERROR"
            )
        ), 500


@alerts_bp.route('/rules/<rule_id>', methods=['PUT'])
async def update_alert_rule(rule_id):
    """更新预警规则"""
    try:
        data = request.json or {}
        request_id = extract_request_id(data)
        
        # 移除request_id避免更新到数据库
        update_data = {k: v for k, v in data.items() if k != 'request_id'}
        
        success = await alert_manager.update_alert_rule(rule_id, update_data)
        
        if success:
            result_data = {
                "rule_id": rule_id,
                "updated_fields": list(update_data.keys()),
                "updated_time": datetime.utcnow().isoformat()
            }
            
            return jsonify(
                ResponseFormatter.format_success(
                    request_id,
                    result_data,
                    "预警规则更新成功"
                )
            )
        else:
            return jsonify(
                ResponseFormatter.format_error(
                    request_id,
                    "预警规则不存在",
                    "RULE_NOT_FOUND"
                )
            ), 404
        
    except Exception as e:
        logger.error(f"更新预警规则失败: {e}")
        return jsonify(
            ResponseFormatter.format_error(
                extract_request_id(data if 'data' in locals() else {}),
                f"更新预警规则失败: {str(e)}",
                "UPDATE_RULE_ERROR"
            )
        ), 500


@alerts_bp.route('/rules/<rule_id>', methods=['DELETE'])
async def delete_alert_rule(rule_id):
    """删除预警规则"""
    try:
        request_id = RequestIDGenerator.generate()
        success = await alert_manager.delete_alert_rule(rule_id)
        
        if success:
            result_data = {
                "rule_id": rule_id,
                "deleted_time": datetime.utcnow().isoformat()
            }
            
            return jsonify(
                ResponseFormatter.format_success(
                    request_id,
                    result_data,
                    "预警规则删除成功"
                )
            )
        else:
            return jsonify(
                ResponseFormatter.format_error(
                    request_id,
                    "预警规则不存在",
                    "RULE_NOT_FOUND"
                )
            ), 404
        
    except Exception as e:
        logger.error(f"删除预警规则失败: {e}")
        return jsonify(
            ResponseFormatter.format_error(
                "unknown",
                f"删除预警规则失败: {str(e)}",
                "DELETE_RULE_ERROR"
            )
        ), 500


@alerts_bp.route('/rules/<rule_id>/test', methods=['POST'])
async def test_alert_rule(rule_id):
    """测试预警规则"""
    try:
        result = await alert_manager.test_alert_rule(rule_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"测试预警规则失败: {e}")
        return jsonify({"error": str(e)}), 500


@alerts_bp.route('/webhook/test', methods=['POST'])
async def test_webhook():
    """    
    请求体示例:
    {
        "webhook_url": "https://...",
        "message_type": "text",
        "test_message": "这是一条测试消息"
    }
    """
    try:
        data = request.json
        webhook_url = data.get("webhook_url")
        message_type = data.get("message_type", "text")
        test_message = data.get("test_message", "Webhook测试消息")
        
        if not webhook_url:
            return jsonify({"error": "webhook_url参数不能为空"}), 400
        
        if message_type == "text":
            result = await webhook_client.send_text_message(test_message, webhook_url)
        elif message_type == "card":
            result = await webhook_client.send_card_message(
                header_title="Webhook测试",
                fields={"测试内容": test_message, "测试时间": datetime.utcnow().isoformat()},
                webhook_url=webhook_url
            )
        else:
            return jsonify({"error": f"不支持的消息类型: {message_type}"}), 400
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"测试Webhook失败: {e}")
        return jsonify({"error": str(e)}), 500


@alerts_bp.route('/stats', methods=['GET'])
async def get_alert_stats():
    """获取预警统计信息"""
    try:
        stats = await alert_manager.get_alert_stats()
        return jsonify(stats.dict())
        
    except Exception as e:
        logger.error(f"获取预警统计失败: {e}")
        return jsonify({"error": str(e)}), 500


@alerts_bp.route('/monitoring/start', methods=['POST'])
async def start_monitoring():
    """启动预警监控"""
    try:
        await alert_manager.start_monitoring()
        return jsonify({
            "success": True,
            "message": "预警监控已启动"
        })
        
    except Exception as e:
        logger.error(f"启动预警监控失败: {e}")
        return jsonify({"error": str(e)}), 500


@alerts_bp.route('/monitoring/stop', methods=['POST'])
async def stop_monitoring():
    """停止预警监控"""
    try:
        await alert_manager.stop_monitoring()
        return jsonify({
            "success": True,
            "message": "预警监控已停止"
        })
        
    except Exception as e:
        logger.error(f"停止预警监控失败: {e}")
        return jsonify({"error": str(e)}), 500


@alerts_bp.route('/monitoring/status', methods=['GET'])
async def monitoring_status():
    """获取监控状态"""
    try:
        return jsonify({
            "is_monitoring": alert_manager.is_monitoring,
            "monitor_interval": alert_manager.monitor_interval,
            "stats": (await alert_manager.get_alert_stats()).dict()
        })
        
    except Exception as e:
        logger.error(f"获取监控状态失败: {e}")
        return jsonify({"error": str(e)}), 500


def _analyze_signal_results(data: list, signal_names: list) -> dict:
    """分析信号查询结果"""
    analysis = {
        "total_occurrences": len(data),
        "signal_frequency": {},
        "timeframe_distribution": {},
        "recent_signals": []
    }
    
    for item in data:
        signals = item.get("signals", [])
        timeframe = item.get("timeframe", "unknown")
        
        for signal in signals:
            if signal in signal_names:
                analysis["signal_frequency"][signal] = analysis["signal_frequency"].get(signal, 0) + 1
        
        analysis["timeframe_distribution"][timeframe] = analysis["timeframe_distribution"].get(timeframe, 0) + 1
        
        if len(analysis["recent_signals"]) < 5:
            analysis["recent_signals"].append({
                "timestamp": item.get("timestamp"),
                "timeframe": timeframe,
                "signals": [s for s in signals if s in signal_names]
            })
    
    return analysis


def _analyze_price_results(data: list, price_level: float, analysis_type: str) -> dict:
    """分析价格查询结果"""
    analysis = {
        "total_occurrences": len(data),
        "analysis_type": analysis_type,
        "price_level": price_level,
        "price_stats": {}
    }
    
    if data:
        prices = [item.get("close", 0) for item in data]
        highs = [item.get("high", 0) for item in data]
        lows = [item.get("low", 0) for item in data]
        
        analysis["price_stats"] = {
            "max_close": max(prices) if prices else 0,
            "min_close": min(prices) if prices else 0,
            "avg_close": sum(prices) / len(prices) if prices else 0,
            "max_high": max(highs) if highs else 0,
            "min_low": min(lows) if lows else 0
        }
    
    return analysis 