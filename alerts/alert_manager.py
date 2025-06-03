"""
预警管理器模块
管理预警规则和实时监控
"""
import asyncio
import logging
import uuid
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.collection import Collection
from .models import (
    AlertRule, AlertTriggerResult, AlertStats, QueryRequest,
    AlertTriggerType, AlertFrequency, QueryField, QueryOperator
)
from .query_engine import QueryEngine
from .webhook_client import LarkWebhookClient
from database.mongo_client import mongodb_client
from utils.request_utils import RequestIDGenerator

logger = logging.getLogger(__name__)


class AlertManager:
    """预警管理器"""
    
    def __init__(self, external_alert_api_url: str = "http://localhost:8081"):
        """初始化预警管理器"""
        self.query_engine = QueryEngine()
        self.webhook_client = LarkWebhookClient()
        self.db_client = mongodb_client
        
        # 外部预警接收API的URL
        self.external_alert_api_url = external_alert_api_url.rstrip('/')
        
        # 预警规则集合
        self.alerts_collection = self.db_client.database["alert_rules"]
        # 预警历史记录集合
        self.alert_history_collection = self.db_client.database["alert_history"]
        
        # 运行状态
        self.is_monitoring = False
        self.monitor_task = None
        
        # 监控间隔（秒）
        self.monitor_interval = 60
        
    async def create_alert_rule(self, alert_rule: AlertRule) -> str:
        """
        创建预警规则
        
        Args:
            alert_rule: 预警规则对象
            
        Returns:
            str: 预警规则ID
        """
        try:
            # 生成规则ID
            rule_id = str(uuid.uuid4())
            alert_rule.id = rule_id
            alert_rule.created_at = datetime.utcnow()
            alert_rule.updated_at = datetime.utcnow()
            
            # 保存到数据库
            rule_dict = alert_rule.dict()
            self.alerts_collection.insert_one(rule_dict)
            
            logger.info(f"创建预警规则成功: {rule_id} - {alert_rule.name}")
            return rule_id
            
        except Exception as e:
            logger.error(f"创建预警规则失败: {e}")
            raise
    
    async def update_alert_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新预警规则
        
        Args:
            rule_id: 规则ID
            updates: 更新字段
            
        Returns:
            bool: 是否更新成功
        """
        try:
            updates["updated_at"] = datetime.utcnow()
            
            result = self.alerts_collection.update_one(
                {"id": rule_id},
                {"$set": updates}
            )
            
            if result.modified_count > 0:
                logger.info(f"更新预警规则成功: {rule_id}")
                return True
            else:
                logger.warning(f"预警规则不存在或无需更新: {rule_id}")
                return False
                
        except Exception as e:
            logger.error(f"更新预警规则失败: {e}")
            raise
    
    async def delete_alert_rule(self, rule_id: str) -> bool:
        """
        删除预警规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            result = self.alerts_collection.delete_one({"id": rule_id})
            
            if result.deleted_count > 0:
                logger.info(f"删除预警规则成功: {rule_id}")
                return True
            else:
                logger.warning(f"预警规则不存在: {rule_id}")
                return False
                
        except Exception as e:
            logger.error(f"删除预警规则失败: {e}")
            raise
    
    async def get_alert_rule(self, rule_id: str) -> Optional[AlertRule]:
        """
        获取预警规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            Optional[AlertRule]: 预警规则对象
        """
        try:
            rule_data = self.alerts_collection.find_one({"id": rule_id})
            
            if rule_data:
                # 移除MongoDB的_id字段
                rule_data.pop("_id", None)
                return AlertRule(**rule_data)
            else:
                return None
                
        except Exception as e:
            logger.error(f"获取预警规则失败: {e}")
            raise
    
    async def list_alert_rules(
        self, 
        symbol: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100
    ) -> List[AlertRule]:
        """
        列出预警规则
        
        Args:
            symbol: 过滤币种
            is_active: 过滤激活状态
            limit: 返回数量限制
            
        Returns:
            List[AlertRule]: 预警规则列表
        """
        try:
            filter_query = {}
            
            if symbol:
                filter_query["symbol"] = symbol.upper()
            
            if is_active is not None:
                filter_query["is_active"] = is_active
            
            cursor = self.alerts_collection.find(filter_query).limit(limit)
            rules = []
            
            for rule_data in cursor:
                rule_data.pop("_id", None)
                rules.append(AlertRule(**rule_data))
            
            return rules
            
        except Exception as e:
            logger.error(f"列出预警规则失败: {e}")
            raise
    
    async def check_alert_rules(self) -> List[AlertTriggerResult]:
        """
        检查所有预警规则
        
        Returns:
            List[AlertTriggerResult]: 触发的预警结果
        """
        triggered_alerts = []
        
        try:
            # 获取所有激活的预警规则
            active_rules = await self.list_alert_rules(is_active=True)
            
            for rule in active_rules:
                try:
                    # 检查是否应该触发
                    if await self._should_check_rule(rule):
                        trigger_result = await self._check_single_rule(rule)
                        if trigger_result:
                            triggered_alerts.append(trigger_result)
                            
                except Exception as e:
                    logger.error(f"检查预警规则失败 {rule.id}: {e}")
                    continue
            
            return triggered_alerts
            
        except Exception as e:
            logger.error(f"检查预警规则失败: {e}")
            return []
    
    async def _should_check_rule(self, rule: AlertRule) -> bool:
        """检查规则是否应该被检查"""
        now = datetime.utcnow()
        
        # 如果规则是只触发一次且已经触发过，则跳过
        if rule.frequency == AlertFrequency.ONCE and rule.trigger_count > 0:
            return False
        
        # 检查频率限制
        if rule.last_triggered_at:
            time_since_last = now - rule.last_triggered_at
            
            if rule.frequency == AlertFrequency.HOURLY and time_since_last < timedelta(hours=1):
                return False
            elif rule.frequency == AlertFrequency.DAILY and time_since_last < timedelta(days=1):
                return False
        
        return True
    
    async def _check_single_rule(self, rule: AlertRule) -> Optional[AlertTriggerResult]:
        """检查单个预警规则"""
        try:
            # 构建查询请求
            query_request = QueryRequest(
                symbol=rule.symbol,
                timeframes=rule.timeframes,
                conditions=rule.trigger_conditions,
                limit=1,  # 只需要最新的数据
                sort_order="desc"
            )
            
            # 执行查询
            query_result = await self.query_engine.execute_query(query_request)
            
            # 检查是否有匹配的数据
            if query_result.matched_records > 0:
                # 有匹配数据，触发预警
                return await self._trigger_alert(rule, query_result.data[0])
            
            return None
            
        except Exception as e:
            logger.error(f"检查预警规则失败 {rule.id}: {e}")
            return None
    
    async def _trigger_alert(self, rule: AlertRule, trigger_data: Dict[str, Any]) -> AlertTriggerResult:
        """触发预警 - 发送POST请求到外部API"""
        try:
            now = datetime.utcnow()
            request_id = RequestIDGenerator.generate()
            
            # 构建详细的预警信息
            alert_info = self._build_detailed_alert_info(rule, trigger_data)
            
            # 确定预警类型
            alert_type = self._get_alert_type_from_rule(rule)
            
            # 构建发送到外部API的请求数据
            api_request = {
                "request_id": request_id,
                "alert_type": alert_type,
                "rule_id": rule.id,
                "rule_name": rule.name,
                "symbol": rule.symbol,
                "timeframe": trigger_data.get("timeframe", "1h"),
                "trigger_time": now.isoformat(),
                "trigger_data": {
                    "description": alert_info["trigger_condition"],
                    "actual_value": alert_info["actual_value"],
                    "threshold": alert_info.get("threshold_value"),
                    "comparison": alert_info.get("comparison_result"),
                    "custom_message": rule.custom_message,
                    **self._build_type_specific_data(alert_type, rule, trigger_data, alert_info)
                },
                "notification_config": {
                    "target_webhook": rule.webhook_url,
                    "message_type": rule.message_type.value if rule.message_type else "text",
                    "frequency": rule.frequency.value if rule.frequency else "once"
                }
            }
            
            # 发送到外部预警API
            message_sent = False
            webhook_response = None
            
            try:
                # 发送POST请求到外部API
                api_url = f"{self.external_alert_api_url}/webhook/alert/trigger"
                response = requests.post(
                    api_url,
                    json=api_request,
                    timeout=30,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    webhook_response = response.json()
                    message_sent = webhook_response.get("success", False)
                    logger.info(f"预警发送成功: {rule.name}, response: {webhook_response}")
                else:
                    webhook_response = {
                        "error": f"外部API响应错误: {response.status_code}",
                        "response": response.text[:500]  # 限制响应长度
                    }
                    logger.error(f"外部API响应错误: {response.status_code} - {response.text}")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"预警API请求异常: {e}")
                webhook_response = {"error": f"网络请求异常: {str(e)}"}
            except Exception as e:
                logger.error(f"发送预警失败: {e}")
                webhook_response = {"error": f"发送异常: {str(e)}"}
            
            # 更新规则状态
            await self.update_alert_rule(rule.id, {
                "last_triggered_at": now,
                "trigger_count": rule.trigger_count + 1
            })
            
            # 创建触发结果
            trigger_result = AlertTriggerResult(
                rule_id=rule.id,
                rule_name=rule.name,
                symbol=rule.symbol,
                timeframe=trigger_data.get("timeframe", "1h"),
                trigger_time=now,
                trigger_data=trigger_data,
                message_sent=message_sent,
                webhook_response=webhook_response
            )
            
            # 保存到历史记录
            result_dict = trigger_result.dict()
            result_dict["request_id"] = request_id  # 添加request_id到历史记录
            self.alert_history_collection.insert_one(result_dict)
            
            logger.info(f"预警触发记录: {rule.name} ({rule.id}), request_id: {request_id}, 发送状态: {message_sent}")
            
            return trigger_result
            
        except Exception as e:
            logger.error(f"触发预警失败: {e}")
            raise
    
    def _get_alert_type_from_rule(self, rule: AlertRule) -> str:
        """根据规则确定预警类型"""
        trigger_type = rule.trigger_type
        
        if trigger_type == AlertTriggerType.PRICE_THRESHOLD:
            return "price_alert"
        elif trigger_type == AlertTriggerType.INDICATOR_THRESHOLD:
            return "indicator_alert"
        elif trigger_type == AlertTriggerType.SIGNAL_DETECTION:
            return "signal_alert"
        elif trigger_type == AlertTriggerType.PATTERN_MATCH:
            return "pattern_alert"
        elif trigger_type == AlertTriggerType.CUSTOM_QUERY:
            return "custom_alert"
        else:
            return "unknown_alert"
    
    def _get_condition_value(self, trigger_conditions):
        """安全获取trigger_conditions的value值"""
        if hasattr(trigger_conditions, 'value'):
            return trigger_conditions.value
        elif hasattr(trigger_conditions, 'dict'):
            # 如果是Pydantic对象，转换为字典后取值
            conditions_dict = trigger_conditions.dict()
            return conditions_dict.get('value')
        else:
            return None
    
    def _get_condition_field(self, trigger_conditions):
        """安全获取trigger_conditions的field值"""
        if hasattr(trigger_conditions, 'field'):
            return trigger_conditions.field
        elif hasattr(trigger_conditions, 'dict'):
            conditions_dict = trigger_conditions.dict()
            return conditions_dict.get('field')
        else:
            return None
    
    def _get_condition_operator(self, trigger_conditions):
        """安全获取trigger_conditions的operator值"""
        if hasattr(trigger_conditions, 'operator'):
            return trigger_conditions.operator
        elif hasattr(trigger_conditions, 'dict'):
            conditions_dict = trigger_conditions.dict()
            return conditions_dict.get('operator')
        else:
            return None
    
    def _build_type_specific_data(
        self, 
        alert_type: str, 
        rule: AlertRule, 
        trigger_data: Dict[str, Any], 
        alert_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """构建特定类型的预警数据"""
        type_data = {}
        
        if alert_type == "price_alert":
            # 安全获取operator值
            operator_value = self._get_operator_value(self._get_condition_operator(rule.trigger_conditions))
            threshold_value = self._get_condition_value(rule.trigger_conditions)
            
            type_data = {
                "actual_price": trigger_data.get("close", 0),
                "threshold": threshold_value if threshold_value is not None else 0,
                "condition": operator_value
            }
        
        elif alert_type == "signal_alert":
            signals = trigger_data.get("signals", [])
            target_signals_value = self._get_condition_value(rule.trigger_conditions)
            target_signals = target_signals_value if isinstance(target_signals_value, list) else [target_signals_value] if target_signals_value else []
            detected_signals = [s for s in signals if s in target_signals]
            
            type_data = {
                "detected_signals": detected_signals,
                "target_signals": target_signals,
                "signal_context": f"检测到 {len(detected_signals)} 个目标信号",
                "signal_strength": "高" if len(detected_signals) > 1 else "中"
            }
        
        elif alert_type == "indicator_alert":
            field = self._get_condition_field(rule.trigger_conditions)
            indicator_value = self._extract_field_value(field, trigger_data)
            indicator_name = self._get_field_display_name(field)
            operator_value = self._get_operator_value(self._get_condition_operator(rule.trigger_conditions))
            threshold_value = self._get_condition_value(rule.trigger_conditions)
            
            type_data = {
                "indicator": indicator_name,
                "current_value": indicator_value,
                "threshold": threshold_value if threshold_value is not None else 0,
                "condition": operator_value
            }
        
        return type_data
    
    def _get_operator_value(self, operator) -> str:
        """安全获取操作符值"""
        if hasattr(operator, 'value'):
            return operator.value
        elif isinstance(operator, str):
            return operator
        else:
            return str(operator)
    
    def _build_detailed_alert_info(self, rule: AlertRule, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """构建详细的预警信息"""
        alert_info = {
            "alert_type": self._get_alert_type_display(rule.trigger_type),
            "trigger_condition": "预警条件触发",
            "actual_value": "数据异常",
            "signal_names": []
        }
        
        try:
            if rule.trigger_type == AlertTriggerType.PRICE_THRESHOLD:
                # 价格阈值预警
                price = trigger_data.get("close", 0)
                threshold = self._get_condition_value(rule.trigger_conditions)
                condition_op = self._get_condition_operator(rule.trigger_conditions)
                
                # 构建触发条件描述 - 支持字符串和枚举
                operator_text = self._get_operator_display_text(condition_op)
                
                alert_info.update({
                    "alert_type": "价格突破" if self._is_greater_operator(condition_op) else "价格跌破",
                    "trigger_condition": f"{rule.symbol}价格{operator_text}${threshold:,.2f}时触发预警",
                    "actual_value": f"${price:,.2f}",
                    "threshold_value": f"${threshold:,.2f}",
                    "comparison_result": f"当前价格${price:,.2f} {operator_text} 设定阈值${threshold:,.2f}"
                })
                
            elif rule.trigger_type == AlertTriggerType.INDICATOR_THRESHOLD:
                # 指标阈值预警
                field = self._get_condition_field(rule.trigger_conditions)
                threshold = self._get_condition_value(rule.trigger_conditions)
                condition_op = self._get_condition_operator(rule.trigger_conditions)
                
                # 获取实际指标值
                indicator_value = self._extract_field_value(field, trigger_data)
                indicator_name = self._get_field_display_name(field)
                
                operator_text = self._get_operator_display_text(condition_op)
                
                alert_type = "指标超买" if self._is_greater_operator(condition_op) else "指标超卖"
                if field == QueryField.RSI:
                    if self._is_greater_operator(condition_op) and threshold >= 70:
                        alert_type = "RSI超买"
                    elif self._is_less_operator(condition_op) and threshold <= 30:
                        alert_type = "RSI超卖"
                
                alert_info.update({
                    "alert_type": alert_type,
                    "trigger_condition": f"{indicator_name}{operator_text}{threshold:.4f}时触发预警",
                    "actual_value": f"{indicator_value:.4f}" if indicator_value is not None else "无数据",
                    "threshold_value": f"{threshold:.4f}",
                    "comparison_result": f"当前{indicator_name}值{indicator_value:.4f} {operator_text} 设定阈值{threshold:.4f}" if indicator_value is not None else "无法获取指标数据",
                    "indicator_name": indicator_name,
                    "indicator_value": indicator_value
                })
                
            elif rule.trigger_type == AlertTriggerType.SIGNAL_DETECTION:
                # 信号检测预警
                signals = trigger_data.get("signals", [])
                target_signals_value = self._get_condition_value(rule.trigger_conditions)
                target_signals = target_signals_value if isinstance(target_signals_value, list) else [target_signals_value] if target_signals_value else []
                
                detected_signals = [s for s in signals if s in target_signals]
                
                alert_info.update({
                    "alert_type": "信号检测",
                    "trigger_condition": f"检测到以下信号时触发预警: {', '.join(target_signals)}",
                    "actual_value": f"检测到: {', '.join(detected_signals)}" if detected_signals else "无信号",
                    "signal_names": detected_signals,
                    "comparison_result": f"目标信号: {', '.join(target_signals)}, 检测到: {', '.join(detected_signals)}"
                })
                
            elif rule.trigger_type == AlertTriggerType.CUSTOM_QUERY:
                # 自定义查询预警
                alert_info.update({
                    "alert_type": "自定义查询",
                    "trigger_condition": f"满足自定义查询条件: {rule.trigger_conditions}",
                    "actual_value": "查询条件匹配",
                    "comparison_result": "当前数据符合预设的自定义查询条件"
                })
                
        except Exception as e:
            logger.error(f"构建预警信息失败: {e}")
            alert_info["trigger_condition"] = f"预警规则 '{rule.name}' 触发，但详细信息构建失败"
            alert_info["actual_value"] = f"错误: {str(e)}"
        
        return alert_info
    
    def _get_operator_display_text(self, operator) -> str:
        """获取操作符的显示文本"""
        operator_text_mapping = {
            "gt": "大于",
            "gte": "大于等于", 
            "lt": "小于",
            "lte": "小于等于",
            "eq": "等于",
            QueryOperator.GT: "大于",
            QueryOperator.GTE: "大于等于",
            QueryOperator.LT: "小于",
            QueryOperator.LTE: "小于等于",
            QueryOperator.EQ: "等于"
        }
        
        return operator_text_mapping.get(operator, str(operator))
    
    def _is_greater_operator(self, operator) -> bool:
        """判断是否为大于类操作符"""
        greater_ops = ["gt", "gte", QueryOperator.GT, QueryOperator.GTE]
        return operator in greater_ops
    
    def _is_less_operator(self, operator) -> bool:
        """判断是否为小于类操作符"""
        less_ops = ["lt", "lte", QueryOperator.LT, QueryOperator.LTE]
        return operator in less_ops
    
    def _extract_field_value(self, field: QueryField, trigger_data: Dict[str, Any]) -> Optional[float]:
        """从触发数据中提取字段值"""
        try:
            # 安全获取field值
            field_value = field.value if hasattr(field, 'value') else str(field)
            
            if field == QueryField.CLOSE or field_value == "close":
                return trigger_data.get("close")
            elif field == QueryField.RSI or field_value == "rsi":
                return trigger_data.get("rsi")
            elif field == QueryField.CCI or field_value == "cci":
                return trigger_data.get("cci")
            elif field_value.startswith("macd."):
                macd_data = trigger_data.get("macd", {})
                macd_field = field_value.split(".", 1)[1]
                return macd_data.get(macd_field)
            elif field_value.startswith("ma."):
                ma_data = trigger_data.get("ma", {})
                ma_field = field_value.split(".", 1)[1] 
                return ma_data.get(ma_field)
            elif field_value.startswith("bollinger."):
                bb_data = trigger_data.get("bollinger", {})
                bb_field = field_value.split(".", 1)[1]
                return bb_data.get(bb_field)
            elif field_value.startswith("kdj."):
                kdj_data = trigger_data.get("kdj", {})
                kdj_field = field_value.split(".", 1)[1]
                return kdj_data.get(kdj_field)
            else:
                return trigger_data.get(field_value)
        except Exception as e:
            logger.error(f"提取字段值失败 {field}: {e}")
            return None
    
    def _get_field_display_name(self, field: QueryField) -> str:
        """获取字段的显示名称"""
        field_names = {
            QueryField.CLOSE: "收盘价",
            QueryField.RSI: "RSI指标",
            QueryField.CCI: "CCI指标",
            QueryField.MACD_LINE: "MACD线",
            QueryField.MACD_SIGNAL: "MACD信号线",
            QueryField.MACD_HISTOGRAM: "MACD柱状图",
            QueryField.MA_5: "MA5",
            QueryField.MA_10: "MA10", 
            QueryField.MA_20: "MA20",
            QueryField.MA_50: "MA50",
            QueryField.BB_UPPER: "布林带上轨",
            QueryField.BB_MIDDLE: "布林带中轨",
            QueryField.BB_LOWER: "布林带下轨",
            QueryField.KDJ_K: "KDJ K值",
            QueryField.KDJ_D: "KDJ D值",
            QueryField.KDJ_J: "KDJ J值"
        }
        
        # 直接匹配枚举值
        display_name = field_names.get(field)
        if display_name:
            return display_name
        
        # 如果没有匹配，使用字符串值
        field_value = field.value if hasattr(field, 'value') else str(field)
        return field_value
    
    def _get_alert_type_display(self, trigger_type: AlertTriggerType) -> str:
        """获取预警类型显示名称"""
        type_mapping = {
            AlertTriggerType.PRICE_THRESHOLD: "价格突破",
            AlertTriggerType.INDICATOR_THRESHOLD: "指标阈值",
            AlertTriggerType.SIGNAL_DETECTION: "信号检测",
            AlertTriggerType.PATTERN_MATCH: "模式匹配",
            AlertTriggerType.CUSTOM_QUERY: "自定义查询"
        }
        return type_mapping.get(trigger_type, str(trigger_type))
    
    async def get_alert_stats(self) -> AlertStats:
        """获取预警统计信息"""
        try:
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            hour_start = now.replace(minute=0, second=0, microsecond=0)
            
            # 总规则数
            total_rules = self.alerts_collection.count_documents({})
            
            # 激活规则数
            active_rules = self.alerts_collection.count_documents({"is_active": True})
            
            # 今日触发次数
            triggered_today = self.alert_history_collection.count_documents({
                "trigger_time": {"$gte": today_start}
            })
            
            # 本小时触发次数
            triggered_this_hour = self.alert_history_collection.count_documents({
                "trigger_time": {"$gte": hour_start}
            })
            
            # 成功率计算
            recent_triggers = self.alert_history_collection.count_documents({
                "trigger_time": {"$gte": today_start}
            })
            
            successful_triggers = self.alert_history_collection.count_documents({
                "trigger_time": {"$gte": today_start},
                "message_sent": True
            })
            
            success_rate = (successful_triggers / recent_triggers * 100) if recent_triggers > 0 else 0
            
            return AlertStats(
                total_rules=total_rules,
                active_rules=active_rules,
                triggered_today=triggered_today,
                triggered_this_hour=triggered_this_hour,
                success_rate=success_rate,
                last_check_time=now
            )
            
        except Exception as e:
            logger.error(f"获取预警统计失败: {e}")
            raise
    
    async def start_monitoring(self):
        """启动监控"""
        if self.is_monitoring:
            logger.warning("监控已经在运行中")
            return
        
        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("预警监控已启动")
    
    async def stop_monitoring(self):
        """停止监控"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("预警监控已停止")
    
    async def _monitor_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 检查预警规则
                triggered_alerts = await self.check_alert_rules()
                
                if triggered_alerts:
                    logger.info(f"触发了 {len(triggered_alerts)} 个预警")
                
                # 等待下一次检查
                await asyncio.sleep(self.monitor_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
                await asyncio.sleep(10)  # 错误时短暂等待
    
    async def test_alert_rule(self, rule_id: str) -> Dict[str, Any]:
        """
        测试预警规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            Dict: 测试结果
        """
        try:
            rule = await self.get_alert_rule(rule_id)
            if not rule:
                return {"success": False, "error": "预警规则不存在"}
            
            # 测试Webhook
            webhook_result = await self.webhook_client.test_webhook(rule.webhook_url)
            
            # 测试查询条件
            query_request = QueryRequest(
                symbol=rule.symbol,
                timeframes=rule.timeframes,
                conditions=rule.trigger_conditions,
                limit=5
            )
            
            query_result = await self.query_engine.execute_query(query_request)
            
            return {
                "success": True,
                "rule_info": {
                    "id": rule.id,
                    "name": rule.name,
                    "symbol": rule.symbol,
                    "timeframes": rule.timeframes
                },
                "webhook_test": webhook_result,
                "query_test": {
                    "matched_records": query_result.matched_records,
                    "execution_time_ms": query_result.execution_time_ms
                }
            }
            
        except Exception as e:
            logger.error(f"测试预警规则失败: {e}")
            return {"success": False, "error": str(e)} 