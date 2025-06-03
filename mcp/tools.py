"""
MCP工具定义
将技术信号查询功能和预警系统功能封装为MCP工具供AI Agent调用
"""
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests
from api.services import signal_service
from alerts.mcp_tools import AlertMCPTools
from utils.request_utils import RequestIDGenerator, ResponseFormatter, QUERY_FIELD_DESCRIPTIONS

logger = logging.getLogger(__name__)


class CryptoSignalTools:
    """加密货币技术信号查询工具集"""
    
    def __init__(self, api_base_url: str = "http://localhost:5000"):
        """
        初始化工具集
        
        Args:
            api_base_url: API服务的基础URL
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.signal_service = signal_service
        
        # 初始化预警系统工具
        self.alert_tools = AlertMCPTools()
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        获取所有工具的定义
        
        Returns:
            List[Dict]: MCP工具定义列表
        """
        # 获取原有的技术信号工具，添加request_id参数
        signal_tools = [
            {
                "name": "query_crypto_signals",
                "description": "查询指定加密货币在最近两个交易时段的技术信号数据，包括价格信息和技术指标信号",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "request_id": {
                            "type": "string",
                            "description": "请求唯一标识符，用于追踪请求",
                            "default": "auto_generated"
                        },
                        "symbol": {
                            "type": "string",
                            "description": "加密货币符号，如BTC或ETH",
                            "enum": ["BTC", "ETH"]
                        },
                        "timeframes": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["5m", "15m", "1h", "1d"]
                            },
                            "description": "时间周期列表，不指定则查询所有周期",
                            "default": ["5m", "15m", "1h", "1d"]
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_supported_symbols",
                "description": "获取系统支持的所有加密货币符号和时间周期列表",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "request_id": {
                            "type": "string",
                            "description": "请求唯一标识符，用于追踪请求",
                            "default": "auto_generated"
                        }
                    },
                    "additionalProperties": False
                }
            },
            {
                "name": "check_system_health",
                "description": "检查技术信号系统的健康状态，包括数据库连接和数据统计信息",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "request_id": {
                            "type": "string",
                            "description": "请求唯一标识符，用于追踪请求",
                            "default": "auto_generated"
                        }
                    },
                    "additionalProperties": False
                }
            },
            {
                "name": "analyze_signal_patterns",
                "description": "分析指定币种的技术信号模式，提供信号频率统计和趋势分析",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "request_id": {
                            "type": "string",
                            "description": "请求唯一标识符，用于追踪请求",
                            "default": "auto_generated"
                        },
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
                            "description": "要分析的时间周期",
                            "default": ["1h", "1d"]
                        }
                    },
                    "required": ["symbol"]
                }
            }
        ]
        
        # 获取预警系统工具
        alert_tools = self.alert_tools.get_tool_definitions()
        
        # 合并所有工具
        return signal_tools + alert_tools
    
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
            
            # 检查是否是原有的技术信号工具
            if tool_name in ["query_crypto_signals", "get_supported_symbols", "check_system_health", "analyze_signal_patterns"]:
                result = await self._execute_signal_tool(tool_name, arguments)
                
                # 使用ResponseFormatter格式化响应
                return ResponseFormatter.format_mcp_response(
                    request_id,
                    result,
                    QUERY_FIELD_DESCRIPTIONS
                )
            else:
                # 交给预警系统工具处理（预警工具内部已处理request_id）
                return await self.alert_tools.execute_tool(tool_name, arguments)
                
        except Exception as e:
            logger.error(f"执行工具 {tool_name} 失败: {e}")
            request_id = arguments.get("request_id", "unknown")
            return ResponseFormatter.format_error(
                request_id,
                f"工具执行失败: {str(e)}",
                "TOOL_EXECUTION_ERROR",
                {"tool_name": tool_name, "arguments": arguments}
            )
    
    async def _execute_signal_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行原有的技术信号工具"""
        # 移除request_id，避免传递给内部方法
        tool_arguments = {k: v for k, v in arguments.items() if k != "request_id"}
        
        if tool_name == "query_crypto_signals":
            return await self._query_crypto_signals(tool_arguments)
        elif tool_name == "get_supported_symbols":
            return await self._get_supported_symbols()
        elif tool_name == "check_system_health":
            return await self._check_system_health()
        elif tool_name == "analyze_signal_patterns":
            return await self._analyze_signal_patterns(tool_arguments)
        else:
            raise ValueError(f"未知的技术信号工具: {tool_name}")
    
    async def _query_crypto_signals(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """查询加密货币技术信号"""
        symbol = arguments.get("symbol")
        timeframes = arguments.get("timeframes")
        
        try:
            # 直接调用服务层，避免HTTP开销
            result = self.signal_service.get_recent_signals(symbol, timeframes)
            
            # 格式化响应数据
            formatted_result = {
                "success": True,
                "data": result,
                "summary": {
                    "symbol": result["symbol"],
                    "query_time": result["query_time"].isoformat() if isinstance(result["query_time"], datetime) else result["query_time"],
                    "total_timeframes": len(result["timeframes"]),
                    "has_signals": result["summary"]["has_signals"],
                    "total_signals": result["summary"]["total_signals"],
                    "popular_signals": result["summary"]["popular_signals"][:5]  # 只返回前5个热门信号
                }
            }
            
            # 添加AI友好的解释
            if result["summary"]["has_signals"]:
                signal_analysis = self._analyze_signals_for_ai(result)
                formatted_result["ai_analysis"] = signal_analysis
            
            return formatted_result
            
        except Exception as e:
            logger.error(f"查询技术信号失败: {e}")
            raise
    
    async def _get_supported_symbols(self) -> Dict[str, Any]:
        """获取支持的币种列表"""
        try:
            return {
                "success": True,
                "symbols": self.signal_service.supported_symbols,
                "timeframes": self.signal_service.supported_timeframes,
                "total_symbols": len(self.signal_service.supported_symbols),
                "total_timeframes": len(self.signal_service.supported_timeframes),
                "description": "系统当前支持BTC和ETH的技术信号分析，包含4种时间周期"
            }
        except Exception as e:
            logger.error(f"获取支持币种失败: {e}")
            raise
    
    async def _check_system_health(self) -> Dict[str, Any]:
        """检查系统健康状态"""
        try:
            health_info = self.signal_service.check_health()
            
            return {
                "success": True,
                "health_status": health_info,
                "description": f"系统状态: {health_info['status']}, 数据库: {health_info['database']['status']}"
            }
        except Exception as e:
            logger.error(f"检查系统健康状态失败: {e}")
            raise
    
    async def _analyze_signal_patterns(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """分析信号模式"""
        symbol = arguments.get("symbol")
        timeframes = arguments.get("timeframes", ["1h", "1d"])
        
        try:
            # 获取技术信号数据
            result = self.signal_service.get_recent_signals(symbol, timeframes)
            
            # 进行模式分析
            pattern_analysis = {
                "symbol": symbol,
                "analysis_timeframes": timeframes,
                "signal_frequency": result["summary"]["signal_frequency"],
                "timeframe_analysis": {},
                "recommendations": []
            }
            
            # 分析各时间周期的信号特点
            for tf_data in result["timeframes"]:
                tf = tf_data["timeframe"]
                signals_in_tf = []
                for period in tf_data["recent_periods"]:
                    signals_in_tf.extend(period.get("signals", []))
                
                pattern_analysis["timeframe_analysis"][tf] = {
                    "signal_count": len(signals_in_tf),
                    "unique_signals": list(set(signals_in_tf)),
                    "dominant_signal_type": self._get_dominant_signal_type(signals_in_tf)
                }
            
            # 生成AI建议
            pattern_analysis["recommendations"] = self._generate_recommendations(result)
            
            return {
                "success": True,
                "pattern_analysis": pattern_analysis,
                "description": f"{symbol} 技术信号模式分析完成"
            }
            
        except Exception as e:
            logger.error(f"分析信号模式失败: {e}")
            raise
    
    def _analyze_signals_for_ai(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """为AI提供友好的信号分析"""
        summary = result["summary"]
        analysis = {
            "market_sentiment": "neutral",
            "key_signals": [],
            "risk_level": "medium",
            "trading_suggestion": "观望"
        }
        
        # 分析热门信号
        popular_signals = summary.get("popular_signals", [])
        if popular_signals:
            # 根据信号类型判断市场情绪
            bullish_signals = []
            bearish_signals = []
            neutral_signals = []
            
            for signal_info in popular_signals:
                signal = signal_info["signal"]
                if any(keyword in signal for keyword in ["GOLDEN_CROSS", "BULLISH", "ABOVE"]):
                    bullish_signals.append(signal)
                elif any(keyword in signal for keyword in ["DEATH_CROSS", "BEARISH", "BELOW", "OVERSOLD"]):
                    bearish_signals.append(signal)
                else:
                    neutral_signals.append(signal)
            
            # 判断整体情绪
            if len(bullish_signals) > len(bearish_signals):
                analysis["market_sentiment"] = "bullish"
                analysis["trading_suggestion"] = "考虑买入"
            elif len(bearish_signals) > len(bullish_signals):
                analysis["market_sentiment"] = "bearish"
                analysis["trading_suggestion"] = "考虑卖出"
            
            analysis["key_signals"] = [s["signal"] for s in popular_signals[:3]]
        
        return analysis
    
    def _get_dominant_signal_type(self, signals: List[str]) -> str:
        """获取主导信号类型"""
        if not signals:
            return "无信号"
        
        signal_types = {
            "RSI": len([s for s in signals if "RSI" in s]),
            "MACD": len([s for s in signals if "MACD" in s]),
            "MA": len([s for s in signals if "MA" in s and "MACD" not in s]),
            "BB": len([s for s in signals if "BB" in s]),
            "KDJ": len([s for s in signals if "KDJ" in s]),
            "CCI": len([s for s in signals if "CCI" in s])
        }
        
        dominant_type = max(signal_types, key=signal_types.get)
        return dominant_type if signal_types[dominant_type] > 0 else "混合信号"
    
    def _generate_recommendations(self, result: Dict[str, Any]) -> List[str]:
        """生成交易建议"""
        recommendations = []
        summary = result["summary"]
        
        if not summary.get("has_signals"):
            recommendations.append("当前无明显技术信号，建议继续观望")
            return recommendations
        
        # 基于信号频率生成建议
        signal_freq = summary.get("signal_frequency", {})
        
        if "RSI_OVERSOLD" in signal_freq:
            recommendations.append("检测到RSI超卖信号，可能存在反弹机会")
        
        if "RSI_OVERBOUGHT" in signal_freq:
            recommendations.append("检测到RSI超买信号，注意回调风险")
        
        if "MACD_GOLDEN_CROSS" in signal_freq:
            recommendations.append("MACD金叉信号，趋势可能转为看多")
        
        if "MACD_DEATH_CROSS" in signal_freq:
            recommendations.append("MACD死叉信号，趋势可能转为看空")
        
        if not recommendations:
            recommendations.append("技术信号较为复杂，建议结合其他分析方法")
        
        return recommendations 