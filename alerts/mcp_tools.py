"""
预警系统MCP工具封装
将预警查询功能封装为MCP工具供AI Agent调用
"""
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from .models import (
    AlertRule, AlertTriggerResult, AlertStats, QueryRequest, QueryCondition, LogicalCondition,
    AlertTriggerType, AlertFrequency, QueryField, QueryOperator, LarkMessageType
)
from .query_engine import QueryEngine
from .alert_manager import AlertManager
from .webhook_client import LarkWebhookClient
from utils.request_utils import RequestIDGenerator, ResponseFormatter, ALERT_FIELD_DESCRIPTIONS, QUERY_FIELD_DESCRIPTIONS

logger = logging.getLogger(__name__)


class AlertMCPTools:
    """预警系统MCP工具集"""
    
    def __init__(self):
        """初始化工具集"""
        self.query_engine = QueryEngine()
        self.alert_manager = AlertManager()
        self.webhook_client = LarkWebhookClient()
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        获取所有MCP工具定义
        
        Returns:
            List[Dict]: MCP工具定义列表
        """
        return [
            {
                "name": "flexible_crypto_query",
                "description": "执行灵活的加密货币K线数据查询，支持复杂的条件组合和多种操作符",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "加密货币符号",
                            "enum": ["BTC", "ETH"]
                        },
                        "timeframes": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["5m", "15m", "1h", "1d"]
                            },
                            "description": "时间周期列表",
                            "default": ["1h"]
                        },
                        "conditions": {
                            "type": "object",
                            "description": "查询条件，可以是单个条件或逻辑组合条件",
                            "properties": {
                                "field": {
                                    "type": "string",
                                    "enum": ["open", "high", "low", "close", "volume", "rsi", "cci", "signals", "timestamp"],
                                    "description": "查询字段"
                                },
                                "operator": {
                                    "type": "string", 
                                    "enum": ["eq", "ne", "gt", "gte", "lt", "lte", "in", "nin", "between", "contains", "within_last"],
                                    "description": "查询操作符"
                                },
                                "value": {
                                    "description": "查询值，可以是数字、字符串或数组"
                                },
                                "operator_logical": {
                                    "type": "string",
                                    "enum": ["and", "or", "not"],
                                    "description": "逻辑操作符（用于组合条件）"
                                },
                                "conditions": {
                                    "type": "array",
                                    "description": "子条件列表（用于逻辑组合）"
                                }
                            }
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回记录数量限制",
                            "default": 50,
                            "minimum": 1,
                            "maximum": 1000
                        },
                        "sort_order": {
                            "type": "string",
                            "enum": ["asc", "desc"],
                            "description": "排序方向",
                            "default": "desc"
                        }
                    },
                    "required": ["symbol", "conditions"]
                }
            },
            {
                "name": "query_trading_signals",
                "description": "查询过去N个时段内的特定交易信号出现情况",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "加密货币符号",
                            "enum": ["BTC", "ETH"]
                        },
                        "timeframes": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["5m", "15m", "1h", "1d"]
                            },
                            "description": "时间周期列表",
                            "default": ["1h"]
                        },
                        "signal_names": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "要查询的信号名称列表，如['RSI_OVERSOLD', 'MACD_GOLDEN_CROSS']"
                        },
                        "periods": {
                            "type": "integer",
                            "description": "查询过去多少个时段",
                            "default": 24,
                            "minimum": 1,
                            "maximum": 1000
                        }
                    },
                    "required": ["symbol", "signal_names"]
                }
            },
            {
                "name": "analyze_price_levels",
                "description": "分析价格水平和突破情况，支持支撑位、阻力位等分析",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "加密货币符号",
                            "enum": ["BTC", "ETH"]
                        },
                        "timeframes": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["5m", "15m", "1h", "1d"]
                            },
                            "description": "时间周期列表",
                            "default": ["1h"]
                        },
                        "price_level": {
                            "type": "number",
                            "description": "要分析的价格水平"
                        },
                        "analysis_type": {
                            "type": "string",
                            "enum": ["breakout", "support", "resistance"],
                            "description": "分析类型：突破、支撑、阻力",
                            "default": "breakout"
                        },
                        "periods": {
                            "type": "integer",
                            "description": "分析时间范围（时段数）",
                            "default": 48,
                            "minimum": 1,
                            "maximum": 1000
                        }
                    },
                    "required": ["symbol", "price_level"]
                }
            },
            {
                "name": "analyze_indicator_extremes",
                "description": "分析技术指标的极值情况，检测是否超过历史高点或低点",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "加密货币符号",
                            "enum": ["BTC", "ETH"]
                        },
                        "timeframes": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["5m", "15m", "1h", "1d"]
                            },
                            "description": "时间周期列表",
                            "default": ["1h"]
                        },
                        "indicator": {
                            "type": "string",
                            "enum": ["rsi", "cci", "macd_line", "ma_20"],
                            "description": "技术指标名称"
                        },
                        "comparison": {
                            "type": "string",
                            "enum": ["historical_high", "historical_low"],
                            "description": "比较类型：历史高点或低点",
                            "default": "historical_high"
                        },
                        "lookback_periods": {
                            "type": "integer",
                            "description": "历史数据回看时段数",
                            "default": 100,
                            "minimum": 10,
                            "maximum": 1000
                        }
                    },
                    "required": ["symbol", "indicator"]
                }
            },
            {
                "name": "create_price_alert",
                "description": "创建价格预警规则，当价格达到指定条件时发送Lark消息",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "预警规则名称"
                        },
                        "symbol": {
                            "type": "string",
                            "description": "加密货币符号",
                            "enum": ["BTC", "ETH"]
                        },
                        "price_threshold": {
                            "type": "number",
                            "description": "价格阈值"
                        },
                        "condition": {
                            "type": "string",
                            "enum": ["above", "below", "equals"],
                            "description": "触发条件：高于、低于、等于",
                            "default": "above"
                        },
                        "timeframes": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["5m", "15m", "1h", "1d"]
                            },
                            "description": "监控的时间周期",
                            "default": ["1h"]
                        },
                        "frequency": {
                            "type": "string",
                            "enum": ["once", "every_time", "hourly", "daily"],
                            "description": "触发频率",
                            "default": "once"
                        },
                        "custom_message": {
                            "type": "string",
                            "description": "自定义预警消息模板",
                            "default": ""
                        }
                    },
                    "required": ["name", "symbol", "price_threshold"]
                }
            },
            {
                "name": "create_indicator_alert",
                "description": "创建技术指标预警规则，当指标值超过指定条件时发送Lark消息",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "预警规则名称"
                        },
                        "symbol": {
                            "type": "string",
                            "description": "加密货币符号",
                            "enum": ["BTC", "ETH"]
                        },
                        "indicator": {
                            "type": "string",
                            "enum": ["rsi", "cci", "macd_line", "ma_20"],
                            "description": "技术指标名称"
                        },
                        "threshold_value": {
                            "type": "number",
                            "description": "指标阈值"
                        },
                        "condition": {
                            "type": "string",
                            "enum": ["above", "below", "equals"],
                            "description": "触发条件：高于、低于、等于",
                            "default": "above"
                        },
                        "timeframes": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["5m", "15m", "1h", "1d"]
                            },
                            "description": "监控的时间周期",
                            "default": ["1h"]
                        },
                        "frequency": {
                            "type": "string",
                            "enum": ["once", "every_time", "hourly", "daily"],
                            "description": "触发频率",
                            "default": "once"
                        },
                        "custom_message": {
                            "type": "string",
                            "description": "自定义预警消息模板",
                            "default": ""
                        }
                    },
                    "required": ["name", "symbol", "indicator", "threshold_value"]
                }
            },
            {
                "name": "create_signal_alert",
                "description": "创建交易信号预警规则，当检测到特定信号时发送Lark消息",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "预警规则名称"
                        },
                        "symbol": {
                            "type": "string",
                            "description": "加密货币符号",
                            "enum": ["BTC", "ETH"]
                        },
                        "signal_names": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "要监控的信号名称列表"
                        },
                        "timeframes": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["5m", "15m", "1h", "1d"]
                            },
                            "description": "监控的时间周期",
                            "default": ["1h"]
                        },
                        "frequency": {
                            "type": "string",
                            "enum": ["once", "every_time", "hourly", "daily"],
                            "description": "触发频率",
                            "default": "every_time"
                        },
                        "custom_message": {
                            "type": "string",
                            "description": "自定义预警消息模板",
                            "default": ""
                        }
                    },
                    "required": ["name", "symbol", "signal_names"]
                }
            },
            {
                "name": "manage_alert_rules",
                "description": "管理预警规则：列出、获取详情、更新、删除预警规则",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["list", "get", "update", "delete", "test"],
                            "description": "管理操作类型"
                        },
                        "rule_id": {
                            "type": "string",
                            "description": "预警规则ID（get、update、delete、test操作需要）"
                        },
                        "symbol": {
                            "type": "string",
                            "description": "按币种过滤（list操作可选）"
                        },
                        "is_active": {
                            "type": "boolean",
                            "description": "按激活状态过滤（list操作可选）"
                        },
                        "updates": {
                            "type": "object",
                            "description": "更新的字段（update操作需要）"
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "test_webhook",
                "description": "测试Lark Webhook连接，发送测试消息",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "webhook_url": {
                            "type": "string",
                            "description": "Webhook URL，为空则使用默认URL"
                        },
                        "message_type": {
                            "type": "string",
                            "enum": ["text", "card"],
                            "description": "消息类型",
                            "default": "text"
                        },
                        "test_message": {
                            "type": "string",
                            "description": "测试消息内容",
                            "default": "MCP预警系统测试消息"
                        }
                    }
                }
            },
            {
                "name": "get_alert_statistics",
                "description": "获取预警系统统计信息和运行状态",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            }
        ]
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行指定的工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            Dict: 工具执行结果
        """
        try:
            # 提取或生成request_id
            request_id = arguments.get("request_id", RequestIDGenerator.generate())
            
            # 移除request_id避免传递给具体的工具方法
            tool_arguments = {k: v for k, v in arguments.items() if k != "request_id"}
            
            # 执行对应的工具方法
            if tool_name == "flexible_crypto_query":
                result = await self._flexible_crypto_query(tool_arguments)
            elif tool_name == "query_trading_signals":
                result = await self._query_trading_signals(tool_arguments)
            elif tool_name == "analyze_price_levels":
                result = await self._analyze_price_levels(tool_arguments)
            elif tool_name == "analyze_indicator_extremes":
                result = await self._analyze_indicator_extremes(tool_arguments)
            elif tool_name == "create_price_alert":
                result = await self._create_price_alert(tool_arguments)
            elif tool_name == "create_indicator_alert":
                result = await self._create_indicator_alert(tool_arguments)
            elif tool_name == "create_signal_alert":
                result = await self._create_signal_alert(tool_arguments)
            elif tool_name == "manage_alert_rules":
                result = await self._manage_alert_rules(tool_arguments)
            elif tool_name == "test_webhook":
                result = await self._test_webhook(tool_arguments)
            elif tool_name == "get_alert_statistics":
                result = await self._get_alert_statistics()
            else:
                raise ValueError(f"未知的工具: {tool_name}")
            
            # 如果工具返回了success标志，按照该结果格式化响应
            if isinstance(result, dict) and "success" in result:
                if result["success"]:
                    return ResponseFormatter.format_mcp_response(
                        request_id,
                        result.get("data", result),
                        ALERT_FIELD_DESCRIPTIONS
                    )
                else:
                    return ResponseFormatter.format_error(
                        request_id,
                        result.get("error", "工具执行失败"),
                        "TOOL_EXECUTION_ERROR"
                    )
            else:
                # 对于查询类工具，使用查询字段描述
                field_descriptions = QUERY_FIELD_DESCRIPTIONS if tool_name.startswith(('flexible_crypto_query', 'query_', 'analyze_')) else ALERT_FIELD_DESCRIPTIONS
                return ResponseFormatter.format_mcp_response(
                    request_id,
                    result,
                    field_descriptions
                )
                
        except Exception as e:
            logger.error(f"执行工具 {tool_name} 失败: {e}")
            request_id = arguments.get("request_id", "unknown")
            return ResponseFormatter.format_error(
                request_id,
                f"工具执行失败: {str(e)}",
                "TOOL_EXECUTION_ERROR",
                {"tool_name": tool_name, "arguments": arguments}
            )
    
    async def _flexible_crypto_query(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行灵活的加密货币查询"""
        try:
            # 构建查询请求
            query_request = QueryRequest(**arguments)
            
            # 执行查询
            result = await self.query_engine.execute_query(query_request)
            
            return {
                "success": True,
                "query_result": result.dict(),
                "summary": {
                    "matched_records": result.matched_records,
                    "execution_time_ms": result.execution_time_ms,
                    "query_conditions": str(arguments.get("conditions", {}))
                }
            }
            
        except Exception as e:
            logger.error(f"灵活查询失败: {e}")
            raise
    
    async def _query_trading_signals(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """查询交易信号"""
        try:
            symbol = arguments.get("symbol", "BTC")
            timeframes = arguments.get("timeframes", ["1h"])
            signal_names = arguments.get("signal_names", [])
            periods = arguments.get("periods", 24)
            
            # 构建查询条件
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
            
            result = await self.query_engine.execute_query(query_request)
            
            # 分析信号结果
            signal_analysis = self._analyze_signal_results(result.data, signal_names)
            
            return {
                "success": True,
                "signal_query_result": result.dict(),
                "signal_analysis": signal_analysis,
                "ai_insights": self._generate_signal_insights(signal_analysis, signal_names)
            }
            
        except Exception as e:
            logger.error(f"查询交易信号失败: {e}")
            raise
    
    async def _analyze_price_levels(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """分析价格水平"""
        try:
            symbol = arguments.get("symbol", "BTC")
            timeframes = arguments.get("timeframes", ["1h"])
            price_level = arguments.get("price_level")
            analysis_type = arguments.get("analysis_type", "breakout")
            periods = arguments.get("periods", 48)
            
            # 根据分析类型构建条件
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
                raise ValueError(f"不支持的分析类型: {analysis_type}")
            
            query_request = QueryRequest(
                symbol=symbol,
                timeframes=timeframes,
                conditions=conditions,
                limit=50
            )
            
            result = await self.query_engine.execute_query(query_request)
            
            # 分析价格结果
            price_analysis = self._analyze_price_results(result.data, price_level, analysis_type)
            
            return {
                "success": True,
                "price_analysis_result": result.dict(),
                "price_analysis": price_analysis,
                "ai_insights": self._generate_price_insights(price_analysis, price_level, analysis_type)
            }
            
        except Exception as e:
            logger.error(f"分析价格水平失败: {e}")
            raise
    
    async def _analyze_indicator_extremes(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """分析技术指标极值"""
        try:
            symbol = arguments.get("symbol", "BTC")
            timeframes = arguments.get("timeframes", ["1h"])
            indicator = arguments.get("indicator", "rsi")
            comparison = arguments.get("comparison", "historical_high")
            lookback_periods = arguments.get("lookback_periods", 100)
            
            # 映射指标字段
            indicator_mapping = {
                "rsi": QueryField.RSI,
                "cci": QueryField.CCI,
                "macd_line": QueryField.MACD_LINE,
                "ma_20": QueryField.MA_20
            }
            
            if indicator not in indicator_mapping:
                raise ValueError(f"不支持的指标: {indicator}")
            
            indicator_field = indicator_mapping[indicator]
            
            # 获取历史统计数据
            stats = await self.query_engine.get_historical_stats(
                symbol=symbol,
                field=indicator_field,
                timeframes=timeframes,
                periods=lookback_periods
            )
            
            return {
                "success": True,
                "indicator": indicator,
                "comparison_type": comparison,
                "historical_stats": stats,
                "ai_insights": self._generate_indicator_insights(stats, indicator, comparison)
            }
            
        except Exception as e:
            logger.error(f"分析指标极值失败: {e}")
            raise
    
    async def _create_price_alert(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """创建价格预警"""
        try:
            name = arguments.get("name")
            symbol = arguments.get("symbol")
            price_threshold = arguments.get("price_threshold")
            condition = arguments.get("condition", "above")
            timeframes = arguments.get("timeframes", ["1h"])
            frequency = arguments.get("frequency", "once")
            custom_message = arguments.get("custom_message", "")
            
            # 构建触发条件
            operator_mapping = {
                "above": QueryOperator.GT,
                "below": QueryOperator.LT,
                "equals": QueryOperator.EQ
            }
            
            # 构建触发条件描述
            condition_text = {
                "above": f"高于${price_threshold:,.2f}",
                "below": f"低于${price_threshold:,.2f}",
                "equals": f"等于${price_threshold:,.2f}"
            }
            
            # 构建预警规则描述
            description = f"当{symbol}价格{condition_text[condition]}时触发预警"
            if custom_message:
                description += f"。备注: {custom_message}"
            
            # 创建预警规则
            alert_rule = AlertRule(
                name=name,
                description=description,
                symbol=symbol.upper(),
                trigger_type=AlertTriggerType.PRICE_THRESHOLD,
                trigger_conditions=QueryCondition(
                    field=QueryField.CLOSE,
                    operator=operator_mapping[condition],
                    value=price_threshold
                ),
                timeframes=timeframes or ["1h"],
                frequency=AlertFrequency.ONCE if frequency == "once" else 
                         AlertFrequency.EVERY_TIME if frequency == "every_time" else 
                         AlertFrequency.HOURLY if frequency == "hourly" else 
                         AlertFrequency.DAILY,
                custom_message=custom_message,
                is_active=True
            )
            
            # 保存到数据库
            rule_id = await self.alert_manager.create_alert_rule(alert_rule)
            
            return {
                "success": True,
                "message": "价格预警创建成功",
                "data": {
                    "rule_id": rule_id,
                    "rule_name": name,
                    "description": description,
                    "symbol": symbol.upper(),
                    "trigger_condition": f"{symbol.upper()}价格{condition_text[condition]}",
                    "threshold_value": f"${price_threshold:,.2f}",
                    "monitoring_timeframes": timeframes,
                    "alert_frequency": frequency,
                    "custom_message": custom_message or "无",
                    "is_active": True,
                    "monitoring_status": "active",
                    "created_time": datetime.utcnow().isoformat(),
                    "trigger_count": 0,
                    "expected_message_preview": f"🚨 {symbol.upper()} 预警触发：{name}\\n" +
                                               f"触发条件: {symbol.upper()}价格{condition_text[condition]}时触发预警\\n" +
                                               f"实际值: $X,XXX.XX\\n" +
                                               f"阈值设置: ${price_threshold:,.2f}"
                }
            }
            
        except Exception as e:
            logger.error(f"创建价格预警失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_indicator_alert(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """创建指标预警"""
        try:
            name = arguments.get("name")
            symbol = arguments.get("symbol")
            indicator = arguments.get("indicator")
            threshold_value = arguments.get("threshold_value")
            condition = arguments.get("condition", "above")
            timeframes = arguments.get("timeframes", ["1h"])
            frequency = arguments.get("frequency", "once")
            custom_message = arguments.get("custom_message", "")
            
            # 映射指标字段
            indicator_mapping = {
                "rsi": QueryField.RSI,
                "cci": QueryField.CCI,
                "macd_line": QueryField.MACD_LINE,
                "macd_signal": QueryField.MACD_SIGNAL,
                "macd_histogram": QueryField.MACD_HISTOGRAM,
                "ma_5": QueryField.MA_5,
                "ma_10": QueryField.MA_10,
                "ma_20": QueryField.MA_20,
                "ma_50": QueryField.MA_50,
                "bb_upper": QueryField.BB_UPPER,
                "bb_middle": QueryField.BB_MIDDLE,
                "bb_lower": QueryField.BB_LOWER,
                "kdj_k": QueryField.KDJ_K,
                "kdj_d": QueryField.KDJ_D,
                "kdj_j": QueryField.KDJ_J
            }
            
            if indicator not in indicator_mapping:
                return {"success": False, "error": f"不支持的指标: {indicator}"}
            
            # 构建操作符
            operator_mapping = {
                "above": QueryOperator.GT,
                "below": QueryOperator.LT,
                "equals": QueryOperator.EQ
            }
            
            # 构建指标显示名称
            indicator_names = {
                "rsi": "RSI指标",
                "cci": "CCI指标",
                "macd_line": "MACD线",
                "macd_signal": "MACD信号线",
                "macd_histogram": "MACD柱状图",
                "ma_5": "MA5",
                "ma_10": "MA10",
                "ma_20": "MA20",
                "ma_50": "MA50",
                "bb_upper": "布林带上轨",
                "bb_middle": "布林带中轨",
                "bb_lower": "布林带下轨",
                "kdj_k": "KDJ K值",
                "kdj_d": "KDJ D值",
                "kdj_j": "KDJ J值"
            }
            
            indicator_display = indicator_names[indicator]
            
            # 构建触发条件描述
            condition_text = {
                "above": f"高于{threshold_value:.4f}",
                "below": f"低于{threshold_value:.4f}",
                "equals": f"等于{threshold_value:.4f}"
            }
            
            # 构建预警规则描述
            description = f"当{symbol}{indicator_display}{condition_text[condition]}时触发预警"
            if custom_message:
                description += f"。备注: {custom_message}"
            
            # 创建预警规则
            alert_rule = AlertRule(
                name=name,
                description=description,
                symbol=symbol.upper(),
                trigger_type=AlertTriggerType.INDICATOR_THRESHOLD,
                trigger_conditions=QueryCondition(
                    field=indicator_mapping[indicator],
                    operator=operator_mapping[condition],
                    value=threshold_value
                ),
                timeframes=timeframes,
                frequency=AlertFrequency.ONCE if frequency == "once" else 
                         AlertFrequency.EVERY_TIME if frequency == "every_time" else 
                         AlertFrequency.HOURLY if frequency == "hourly" else 
                         AlertFrequency.DAILY,
                custom_message=custom_message,
                is_active=True
            )
            
            # 保存到数据库
            rule_id = await self.alert_manager.create_alert_rule(alert_rule)
            
            return {
                "success": True,
                "message": "指标预警创建成功",
                "data": {
                    "rule_id": rule_id,
                    "rule_name": name,
                    "description": description,
                    "symbol": symbol.upper(),
                    "indicator_name": indicator_display,
                    "trigger_condition": f"{indicator_display}{condition_text[condition]}",
                    "threshold_value": f"{threshold_value:.4f}",
                    "monitoring_timeframes": timeframes,
                    "alert_frequency": frequency,
                    "custom_message": custom_message or "无",
                    "is_active": True,
                    "monitoring_status": "active",
                    "created_time": datetime.utcnow().isoformat(),
                    "trigger_count": 0,
                    "expected_message_preview": f"🚨 {symbol.upper()} 预警触发：{name}\\n" +
                                               f"触发条件: {indicator_display}{condition_text[condition]}时触发预警\\n" +
                                               f"实际值: X.XXXX\\n" +
                                               f"阈值设置: {threshold_value:.4f}"
                }
            }
            
        except Exception as e:
            logger.error(f"创建指标预警失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_signal_alert(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """创建信号预警"""
        try:
            name = arguments.get("name")
            symbol = arguments.get("symbol")
            signal_names = arguments.get("signal_names")
            timeframes = arguments.get("timeframes", ["1h"])
            frequency = arguments.get("frequency", "every_time")
            custom_message = arguments.get("custom_message", "")
            
            # 验证参数
            if symbol.upper() not in ["BTC", "ETH"]:
                return {"success": False, "error": f"不支持的币种: {symbol}"}
            
            if not signal_names:
                return {"success": False, "error": "至少需要指定一个信号"}
            
            # 验证信号名称
            valid_signals = [
                "RSI_OVERSOLD", "RSI_OVERBOUGHT", "RSI_BULLISH_DIVERGENCE", "RSI_BEARISH_DIVERGENCE",
                "MACD_GOLDEN_CROSS", "MACD_DEATH_CROSS", "MACD_ABOVE_ZERO", "MACD_BELOW_ZERO",
                "MA_GOLDEN_CROSS", "MA_DEATH_CROSS", "MA_BULLISH_ARRANGEMENT", "MA_BEARISH_ARRANGEMENT",
                "PRICE_ABOVE_MA50", "PRICE_BELOW_MA50",
                "BB_UPPER_TOUCH", "BB_LOWER_TOUCH", "BB_MIDDLE_CROSS_UP", "BB_MIDDLE_CROSS_DOWN",
                "BB_SQUEEZE", "BB_EXPANSION",
                "KDJ_GOLDEN_CROSS", "KDJ_DEATH_CROSS", "KDJ_OVERBOUGHT", "KDJ_OVERSOLD",
                "STOCH_OVERBOUGHT", "STOCH_OVERSOLD",
                "CCI_OVERBOUGHT", "CCI_OVERSOLD",
                "VOLUME_SPIKE"
            ]
            
            invalid_signals = [s for s in signal_names if s not in valid_signals]
            if invalid_signals:
                return {"success": False, "error": f"不支持的信号: {', '.join(invalid_signals)}"}
            
            # 构建信号显示名称映射
            signal_display_names = {
                "RSI_OVERSOLD": "RSI超卖",
                "RSI_OVERBOUGHT": "RSI超买",
                "RSI_BULLISH_DIVERGENCE": "RSI看涨背离",
                "RSI_BEARISH_DIVERGENCE": "RSI看跌背离",
                "MACD_GOLDEN_CROSS": "MACD金叉",
                "MACD_DEATH_CROSS": "MACD死叉",
                "MACD_ABOVE_ZERO": "MACD上穿零轴",
                "MACD_BELOW_ZERO": "MACD下穿零轴",
                "MA_GOLDEN_CROSS": "均线金叉",
                "MA_DEATH_CROSS": "均线死叉",
                "MA_BULLISH_ARRANGEMENT": "多头排列",
                "MA_BEARISH_ARRANGEMENT": "空头排列",
                "PRICE_ABOVE_MA50": "价格突破MA50",
                "PRICE_BELOW_MA50": "价格跌破MA50",
                "BB_UPPER_TOUCH": "触及布林带上轨",
                "BB_LOWER_TOUCH": "触及布林带下轨",
                "BB_MIDDLE_CROSS_UP": "上穿布林带中轨",
                "BB_MIDDLE_CROSS_DOWN": "下穿布林带中轨",
                "BB_SQUEEZE": "布林带收缩",
                "BB_EXPANSION": "布林带扩张",
                "KDJ_GOLDEN_CROSS": "KDJ金叉",
                "KDJ_DEATH_CROSS": "KDJ死叉",
                "KDJ_OVERBOUGHT": "KDJ超买",
                "KDJ_OVERSOLD": "KDJ超卖",
                "STOCH_OVERBOUGHT": "随机指标超买",
                "STOCH_OVERSOLD": "随机指标超卖",
                "CCI_OVERBOUGHT": "CCI超买",
                "CCI_OVERSOLD": "CCI超卖",
                "VOLUME_SPIKE": "成交量激增"
            }
            
            # 构建信号描述
            signal_descriptions = [signal_display_names.get(s, s) for s in signal_names]
            
            # 构建预警规则描述
            description = f"当{symbol}出现以下信号时触发预警: {', '.join(signal_descriptions)}"
            if custom_message:
                description += f"。备注: {custom_message}"
            
            # 创建预警规则
            alert_rule = AlertRule(
                name=name,
                description=description,
                symbol=symbol.upper(),
                trigger_type=AlertTriggerType.SIGNAL_DETECTION,
                trigger_conditions=QueryCondition(
                    field=QueryField.SIGNALS,
                    operator=QueryOperator.CONTAINS,
                    value=signal_names
                ),
                timeframes=timeframes,
                frequency=AlertFrequency.ONCE if frequency == "once" else 
                         AlertFrequency.EVERY_TIME if frequency == "every_time" else 
                         AlertFrequency.HOURLY if frequency == "hourly" else 
                         AlertFrequency.DAILY,
                custom_message=custom_message,
                is_active=True
            )
            
            # 保存到数据库
            rule_id = await self.alert_manager.create_alert_rule(alert_rule)
            
            return {
                "success": True,
                "message": "信号预警创建成功",
                "data": {
                    "rule_id": rule_id,
                    "rule_name": name,
                    "description": description,
                    "symbol": symbol.upper(),
                    "target_signals": signal_names,
                    "target_signals_display": signal_descriptions,
                    "trigger_condition": f"检测到以下信号时触发预警: {', '.join(signal_descriptions)}",
                    "monitoring_timeframes": timeframes,
                    "alert_frequency": frequency,
                    "custom_message": custom_message or "无",
                    "is_active": True,
                    "monitoring_status": "active",
                    "created_time": datetime.utcnow().isoformat(),
                    "trigger_count": 0,
                    "expected_message_preview": f"🚨 {symbol.upper()} 预警触发：{name}\\n" +
                                               f"触发条件: 检测到以下信号时触发预警: {', '.join(signal_descriptions)}\\n" +
                                               f"实际值: 检测到: [具体信号名称]\\n" +
                                               f"目标信号: {', '.join(signal_descriptions)}"
                }
            }
            
        except Exception as e:
            logger.error(f"创建信号预警失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _manage_alert_rules(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """管理预警规则"""
        try:
            action = arguments.get("action")
            
            if action == "list":
                symbol = arguments.get("symbol")
                is_active = arguments.get("is_active")
                rules = await self.alert_manager.list_alert_rules(
                    symbol=symbol,
                    is_active=is_active,
                    limit=100
                )
                
                return {
                    "success": True,
                    "action": "list",
                    "rules": [rule.dict() for rule in rules],
                    "total": len(rules)
                }
                
            elif action == "get":
                rule_id = arguments.get("rule_id")
                if not rule_id:
                    raise ValueError("rule_id参数是必需的")
                
                rule = await self.alert_manager.get_alert_rule(rule_id)
                if not rule:
                    return {"success": False, "error": "预警规则不存在"}
                
                return {
                    "success": True,
                    "action": "get",
                    "rule": rule.dict()
                }
                
            elif action == "update":
                rule_id = arguments.get("rule_id")
                updates = arguments.get("updates", {})
                
                if not rule_id:
                    raise ValueError("rule_id参数是必需的")
                
                success = await self.alert_manager.update_alert_rule(rule_id, updates)
                
                return {
                    "success": success,
                    "action": "update",
                    "message": "预警规则更新成功" if success else "预警规则不存在"
                }
                
            elif action == "delete":
                rule_id = arguments.get("rule_id")
                
                if not rule_id:
                    raise ValueError("rule_id参数是必需的")
                
                success = await self.alert_manager.delete_alert_rule(rule_id)
                
                return {
                    "success": success,
                    "action": "delete",
                    "message": "预警规则删除成功" if success else "预警规则不存在"
                }
                
            elif action == "test":
                rule_id = arguments.get("rule_id")
                
                if not rule_id:
                    raise ValueError("rule_id参数是必需的")
                
                result = await self.alert_manager.test_alert_rule(rule_id)
                
                return {
                    "success": True,
                    "action": "test",
                    "test_result": result
                }
                
            else:
                raise ValueError(f"不支持的操作: {action}")
                
        except Exception as e:
            logger.error(f"管理预警规则失败: {e}")
            raise
    
    async def _test_webhook(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """测试Webhook"""
        try:
            webhook_url = arguments.get("webhook_url")
            message_type = arguments.get("message_type", "text")
            test_message = arguments.get("test_message", "MCP预警系统测试消息")
            
            if message_type == "text":
                result = await self.webhook_client.send_text_message(test_message, webhook_url)
            elif message_type == "card":
                result = await self.webhook_client.send_card_message(
                    header_title="MCP预警系统测试",
                    fields={
                        "测试内容": test_message,
                        "测试时间": datetime.utcnow().isoformat(),
                        "消息来源": "MCP预警系统"
                    },
                    webhook_url=webhook_url
                )
            else:
                raise ValueError(f"不支持的消息类型: {message_type}")
            
            return {
                "success": True,
                "webhook_test_result": result,
                "message": "Webhook测试完成"
            }
            
        except Exception as e:
            logger.error(f"测试Webhook失败: {e}")
            raise
    
    async def _get_alert_statistics(self) -> Dict[str, Any]:
        """获取预警统计"""
        try:
            stats = await self.alert_manager.get_alert_stats()
            
            return {
                "success": True,
                "statistics": stats.dict(),
                "monitoring_status": {
                    "is_monitoring": self.alert_manager.is_monitoring,
                    "monitor_interval": self.alert_manager.monitor_interval
                }
            }
            
        except Exception as e:
            logger.error(f"获取预警统计失败: {e}")
            raise
    
    # 辅助方法
    
    def _analyze_signal_results(self, data: list, signal_names: list) -> dict:
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
            
            # 信号频率统计
            for signal in signals:
                if signal in signal_names:
                    analysis["signal_frequency"][signal] = analysis["signal_frequency"].get(signal, 0) + 1
            
            # 时间周期分布
            analysis["timeframe_distribution"][timeframe] = analysis["timeframe_distribution"].get(timeframe, 0) + 1
            
            # 最近的信号
            if len(analysis["recent_signals"]) < 5:
                analysis["recent_signals"].append({
                    "timestamp": item.get("timestamp"),
                    "timeframe": timeframe,
                    "signals": [s for s in signals if s in signal_names]
                })
        
        return analysis
    
    def _analyze_price_results(self, data: list, price_level: float, analysis_type: str) -> dict:
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
    
    def _generate_signal_insights(self, analysis: dict, signal_names: list) -> dict:
        """生成信号分析洞察"""
        insights = {
            "summary": "",
            "recommendations": [],
            "risk_level": "medium"
        }
        
        total_occurrences = analysis.get("total_occurrences", 0)
        signal_frequency = analysis.get("signal_frequency", {})
        
        if total_occurrences == 0:
            insights["summary"] = f"在查询时间范围内未检测到指定信号 {signal_names}"
            insights["recommendations"].append("继续监控市场动态")
            insights["risk_level"] = "low"
        else:
            most_frequent = max(signal_frequency.items(), key=lambda x: x[1]) if signal_frequency else None
            
            if most_frequent:
                insights["summary"] = f"检测到{total_occurrences}次信号出现，'{most_frequent[0]}'出现最频繁({most_frequent[1]}次)"
                
                if "OVERSOLD" in most_frequent[0] or "SUPPORT" in most_frequent[0]:
                    insights["recommendations"].append("可能存在反弹机会，但需谨慎观察")
                    insights["risk_level"] = "medium"
                elif "OVERBOUGHT" in most_frequent[0] or "RESISTANCE" in most_frequent[0]:
                    insights["recommendations"].append("注意回调风险，考虑获利了结")
                    insights["risk_level"] = "high"
        
        return insights
    
    def _generate_price_insights(self, analysis: dict, price_level: float, analysis_type: str) -> dict:
        """生成价格分析洞察"""
        insights = {
            "summary": "",
            "recommendations": [],
            "significance": "medium"
        }
        
        total_occurrences = analysis.get("total_occurrences", 0)
        price_stats = analysis.get("price_stats", {})
        
        if total_occurrences == 0:
            insights["summary"] = f"价格未{analysis_type}关键水平 ${price_level:,.2f}"
            insights["recommendations"].append("继续监控该价格水平")
            insights["significance"] = "low"
        else:
            if analysis_type == "breakout":
                insights["summary"] = f"价格在{total_occurrences}个时段突破了 ${price_level:,.2f}"
                insights["recommendations"].append("突破确认，可能继续上涨")
                insights["significance"] = "high"
            elif analysis_type == "support":
                insights["summary"] = f"价格在{total_occurrences}个时段测试支撑位 ${price_level:,.2f}"
                insights["recommendations"].append("支撑位有效，关注反弹机会")
                insights["significance"] = "medium"
        
        return insights
    
    def _generate_indicator_insights(self, stats: dict, indicator: str, comparison: str) -> dict:
        """生成指标分析洞察"""
        insights = {
            "summary": "",
            "recommendations": [],
            "extremes_detected": False
        }
        
        # 分析各时间周期的极值情况
        extremes_count = 0
        for timeframe, tf_stats in stats.items():
            current = tf_stats.get("current")
            max_val = tf_stats.get("max")
            min_val = tf_stats.get("min")
            
            if current is not None and max_val is not None and min_val is not None:
                if comparison == "historical_high" and current >= max_val * 0.95:
                    extremes_count += 1
                elif comparison == "historical_low" and current <= min_val * 1.05:
                    extremes_count += 1
        
        if extremes_count > 0:
            insights["extremes_detected"] = True
            insights["summary"] = f"{indicator.upper()}在{extremes_count}个时间周期接近{comparison.replace('_', ' ')}"
            
            if comparison == "historical_high":
                if indicator == "rsi":
                    insights["recommendations"].append("RSI接近历史高位，市场可能超买")
                elif indicator == "cci":
                    insights["recommendations"].append("CCI达到极值，注意趋势反转信号")
            elif comparison == "historical_low":
                if indicator == "rsi":
                    insights["recommendations"].append("RSI接近历史低位，市场可能超卖")
                elif indicator == "cci":
                    insights["recommendations"].append("CCI达到极值，可能存在反弹机会")
        else:
            insights["summary"] = f"{indicator.upper()}当前值处于正常范围内"
            insights["recommendations"].append("指标值正常，继续观察")
        
        return insights 