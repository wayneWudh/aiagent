"""
Lark Webhook客户端
用于发送预警消息到飞书群聊
"""
import aiohttp
import asyncio
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class LarkWebhookClient:
    """飞书Webhook客户端"""
    
    def __init__(self, default_webhook_url: str = None):
        """
        初始化客户端
        
        Args:
            default_webhook_url: 默认的webhook URL
        """
        self.default_webhook_url = default_webhook_url or "https://open.larksuite.com/open-apis/bot/v2/hook/2691e416-0374-4181-b195-9e1de11968da"
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP客户端会话"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def send_text_message(
        self, 
        text: str, 
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发送文本消息
        
        Args:
            text: 消息内容
            webhook_url: Webhook URL，为空则使用默认URL
            
        Returns:
            Dict: 发送结果
        """
        url = webhook_url or self.default_webhook_url
        
        payload = {
            "msg_type": "text",
            "content": {
                "text": text
            }
        }
        
        return await self._send_message(url, payload)
    
    async def send_rich_text_message(
        self,
        title: str,
        content: str,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发送富文本消息
        
        Args:
            title: 消息标题
            content: 消息内容
            webhook_url: Webhook URL
            
        Returns:
            Dict: 发送结果
        """
        url = webhook_url or self.default_webhook_url
        
        payload = {
            "msg_type": "rich_text",
            "content": {
                "rich_text": {
                    "elements": [
                        {
                            "tag": "text",
                            "text": title,
                            "style": {
                                "bold": True
                            }
                        },
                        {
                            "tag": "br"
                        },
                        {
                            "tag": "text", 
                            "text": content
                        }
                    ]
                }
            }
        }
        
        return await self._send_message(url, payload)
    
    async def send_card_message(
        self,
        header_title: str,
        fields: Dict[str, Any],
        webhook_url: Optional[str] = None,
        header_color: str = "blue"
    ) -> Dict[str, Any]:
        """
        发送卡片消息
        
        Args:
            header_title: 卡片标题
            fields: 字段内容
            webhook_url: Webhook URL
            header_color: 标题颜色
            
        Returns:
            Dict: 发送结果
        """
        url = webhook_url or self.default_webhook_url
        
        # 构建卡片内容
        elements = []
        
        for key, value in fields.items():
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**{key}:** {value}"
                }
            })
        
        payload = {
            "msg_type": "interactive",
            "card": {
                "elements": elements,
                "header": {
                    "title": {
                        "content": header_title,
                        "tag": "plain_text"
                    },
                    "template": header_color
                }
            }
        }
        
        return await self._send_message(url, payload)
    
    async def send_crypto_alert(
        self,
        alert_rule_name: str,
        alert_rule_description: str,
        alert_type: str,
        symbol: str,
        timeframe: str,
        trigger_condition: str,
        actual_value: str,
        threshold_value: Optional[str] = None,
        comparison_result: Optional[str] = None,
        price: Optional[float] = None,
        indicator_name: Optional[str] = None,
        indicator_value: Optional[float] = None,
        signal_names: Optional[List[str]] = None,
        trigger_time: Optional[datetime] = None,
        custom_message: Optional[str] = None,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发送详细的加密货币预警消息
        
        Args:
            alert_rule_name: 预警规则名称
            alert_rule_description: 预警规则描述
            alert_type: 预警类型
            symbol: 币种符号
            timeframe: 时间周期
            trigger_condition: 触发条件描述
            actual_value: 实际值
            threshold_value: 阈值（如果适用）
            comparison_result: 对比结果描述
            price: 当前价格
            indicator_name: 指标名称
            indicator_value: 指标值
            signal_names: 检测到的信号列表
            trigger_time: 触发时间
            custom_message: 自定义消息
            webhook_url: Webhook URL
            
        Returns:
            Dict: 发送结果
        """
        trigger_time = trigger_time or datetime.utcnow()
        
        # 构建预警消息标题
        title = f"🚨 {symbol} 预警触发：{alert_rule_name}"
        
        # 构建详细的预警信息
        fields = {
            "预警规则": alert_rule_name,
            "规则描述": alert_rule_description or "无描述",
            "预警类型": alert_type,
            "监控币种": symbol,
            "监控周期": timeframe,
            "触发时间": trigger_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "触发条件": trigger_condition
        }
        
        # 添加具体的数值信息
        if actual_value:
            fields["实际值"] = actual_value
            
        if threshold_value:
            fields["阈值设置"] = threshold_value
            
        if comparison_result:
            fields["对比结果"] = comparison_result
        
        # 添加当前市场价格
        if price is not None:
            fields["当前价格"] = f"${price:,.2f}"
        
        # 添加技术指标信息
        if indicator_name and indicator_value is not None:
            fields[f"{indicator_name}当前值"] = f"{indicator_value:.4f}"
        
        # 添加检测到的信号
        if signal_names:
            fields["检测信号"] = ", ".join(signal_names)
        
        # 添加自定义消息
        if custom_message:
            fields["备注信息"] = custom_message
        
        # 添加操作建议
        suggestion = self._generate_action_suggestion(alert_type, symbol, comparison_result)
        if suggestion:
            fields["操作建议"] = suggestion
        
        # 根据预警类型选择颜色和图标
        color_mapping = {
            "价格突破": "red",
            "价格跌破": "red",
            "指标超买": "orange", 
            "指标超卖": "green",
            "指标突破": "blue",
            "信号检测": "blue",
            "模式匹配": "purple",
            "自定义查询": "grey"
        }
        
        header_color = color_mapping.get(alert_type, "blue")
        
        return await self.send_card_message(
            header_title=title,
            fields=fields,
            webhook_url=webhook_url,
            header_color=header_color
        )
    
    def _generate_action_suggestion(self, alert_type: str, symbol: str, comparison_result: Optional[str]) -> Optional[str]:
        """根据预警类型生成操作建议"""
        suggestions = {
            "价格突破": f"🔥 {symbol}价格突破关键阻力位，可能继续上涨，建议关注趋势延续",
            "价格跌破": f"⚠️ {symbol}价格跌破关键支撑位，注意风险控制",
            "指标超买": f"📈 {symbol}技术指标显示超买状态，可能面临回调压力",
            "指标超卖": f"📉 {symbol}技术指标显示超卖状态，可能存在反弹机会",
            "指标突破": f"📊 {symbol}技术指标出现重要突破，关注趋势变化",
            "信号检测": f"🎯 {symbol}出现重要技术信号，建议结合其他指标确认",
            "模式匹配": f"🔍 {symbol}出现特定技术形态，关注后续发展"
        }
        
        base_suggestion = suggestions.get(alert_type, f"📱 {symbol}触发预警，请关注市场变化")
        
        # 添加基于对比结果的具体建议
        if comparison_result and "大于" in comparison_result:
            base_suggestion += "，当前值已超过设定阈值"
        elif comparison_result and "小于" in comparison_result:
            base_suggestion += "，当前值已低于设定阈值"
            
        return base_suggestion

    # 保持原有的简化版本作为兼容性方法
    async def send_simple_crypto_alert(
        self,
        alert_type: str,
        symbol: str,
        timeframe: str,
        price: Optional[float] = None,
        indicator_name: Optional[str] = None,
        indicator_value: Optional[float] = None,
        threshold_value: Optional[float] = None,
        signal_name: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发送简化的加密货币预警消息（向后兼容）
        """
        timestamp = timestamp or datetime.utcnow()
        
        # 构建基础信息
        trigger_condition = f"{alert_type}预警"
        actual_value = "见详细信息"
        
        if price is not None and "价格" in alert_type:
            actual_value = f"${price:,.2f}"
            if threshold_value:
                trigger_condition = f"价格{('突破' if price > threshold_value else '跌破')}${threshold_value:,.2f}"
        elif indicator_value is not None and indicator_name:
            actual_value = f"{indicator_value:.4f}"
            if threshold_value:
                trigger_condition = f"{indicator_name}{('超过' if indicator_value > threshold_value else '低于')}{threshold_value:.4f}"
        elif signal_name:
            actual_value = signal_name
            trigger_condition = f"检测到{signal_name}信号"
        
        return await self.send_crypto_alert(
            alert_rule_name="系统预警",
            alert_rule_description="自动生成的预警",
            alert_type=alert_type,
            symbol=symbol,
            timeframe=timeframe,
            trigger_condition=trigger_condition,
            actual_value=actual_value,
            threshold_value=f"{threshold_value:.4f}" if threshold_value else None,
            price=price,
            indicator_name=indicator_name,
            indicator_value=indicator_value,
            signal_names=[signal_name] if signal_name else None,
            trigger_time=timestamp,
            webhook_url=webhook_url
        )
    
    async def _send_message(self, webhook_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送消息的内部方法
        
        Args:
            webhook_url: Webhook URL
            payload: 消息载荷
            
        Returns:
            Dict: 发送结果
        """
        try:
            session = await self._get_session()
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            logger.debug(f"发送Lark消息到: {webhook_url}")
            logger.debug(f"消息内容: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            
            async with session.post(webhook_url, json=payload, headers=headers) as response:
                response_text = await response.text()
                
                try:
                    response_data = json.loads(response_text)
                except json.JSONDecodeError:
                    response_data = {"raw_response": response_text}
                
                result = {
                    "success": response.status == 200,
                    "status_code": response.status,
                    "response": response_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                if response.status == 200:
                    logger.info("Lark消息发送成功")
                else:
                    logger.error(f"Lark消息发送失败: {response.status} - {response_text}")
                
                return result
                
        except asyncio.TimeoutError:
            logger.error("发送Lark消息超时")
            return {
                "success": False,
                "error": "发送超时",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"发送Lark消息异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def test_webhook(self, webhook_url: Optional[str] = None) -> Dict[str, Any]:
        """
        测试Webhook连接
        
        Args:
            webhook_url: 要测试的Webhook URL
            
        Returns:
            Dict: 测试结果
        """
        url = webhook_url or self.default_webhook_url
        
        test_message = f"🔧 Webhook测试消息 - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        
        result = await self.send_text_message(test_message, url)
        
        if result.get("success"):
            logger.info("Webhook测试成功")
        else:
            logger.error("Webhook测试失败")
        
        return result
    
    async def close(self):
        """关闭HTTP会话"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None 