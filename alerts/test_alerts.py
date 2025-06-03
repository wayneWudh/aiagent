#!/usr/bin/env python3
"""
预警系统测试脚本
测试预警系统的各项功能
"""
import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, '..')

from alerts.models import (
    QueryRequest, AlertRule, QueryCondition, LogicalCondition,
    QueryField, QueryOperator, AlertTriggerType, AlertFrequency
)
from alerts.query_engine import QueryEngine
from alerts.alert_manager import AlertManager
from alerts.webhook_client import LarkWebhookClient
from alerts.mcp_tools import AlertMCPTools

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AlertSystemTester:
    """预警系统测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.query_engine = QueryEngine()
        self.alert_manager = AlertManager()
        self.webhook_client = LarkWebhookClient()
        self.mcp_tools = AlertMCPTools()
        
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始预警系统测试...")
        print("=" * 60)
        
        # 测试查询引擎
        await self._test_query_engine()
        
        # 测试Webhook客户端
        await self._test_webhook_client()
        
        # 测试预警管理器
        await self._test_alert_manager()
        
        # 测试MCP工具
        await self._test_mcp_tools()
        
        # 显示测试结果
        self._show_results()
    
    async def _test_query_engine(self):
        """测试查询引擎"""
        print("\n🔍 测试查询引擎...")
        
        try:
            # 测试基础查询
            print("  测试基础价格查询...")
            query_request = QueryRequest(
                symbol="BTC",
                timeframes=["1h"],
                conditions=QueryCondition(
                    field=QueryField.CLOSE,
                    operator=QueryOperator.GT,
                    value=40000
                ),
                limit=10
            )
            
            result = await self.query_engine.execute_query(query_request)
            
            if result.symbol == "BTC":
                self._pass_test("基础价格查询")
            else:
                self._fail_test("基础价格查询", "返回的符号不正确")
            
            # 测试信号查询
            print("  测试信号查询...")
            signal_query = QueryRequest(
                symbol="BTC",
                timeframes=["1h"],
                conditions=QueryCondition(
                    field=QueryField.SIGNALS,
                    operator=QueryOperator.CONTAINS,
                    value="RSI_OVERSOLD"
                ),
                limit=5
            )
            
            signal_result = await self.query_engine.execute_query(signal_query)
            
            if signal_result.symbol == "BTC":
                self._pass_test("信号查询")
            else:
                self._fail_test("信号查询", "查询失败")
            
            # 测试复合条件查询
            print("  测试复合条件查询...")
            complex_query = QueryRequest(
                symbol="BTC",
                timeframes=["1h"],
                conditions=LogicalCondition(
                    operator="and",
                    conditions=[
                        QueryCondition(
                            field=QueryField.CLOSE,
                            operator=QueryOperator.GT,
                            value=45000
                        ),
                        QueryCondition(
                            field=QueryField.RSI,
                            operator=QueryOperator.LT,
                            value=30
                        )
                    ]
                ),
                limit=5
            )
            
            complex_result = await self.query_engine.execute_query(complex_query)
            
            if complex_result.symbol == "BTC":
                self._pass_test("复合条件查询")
            else:
                self._fail_test("复合条件查询", "查询失败")
            
        except Exception as e:
            self._fail_test("查询引擎测试", str(e))
    
    async def _test_webhook_client(self):
        """测试Webhook客户端"""
        print("\n📨 测试Webhook客户端...")
        
        try:
            # 测试文本消息
            print("  测试Lark文本消息...")
            result = await self.webhook_client.send_text_message(
                "📊 预警系统测试消息 - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            
            if result.get("success"):
                self._pass_test("Lark文本消息发送")
            else:
                self._fail_test("Lark文本消息发送", result.get("error", "未知错误"))
            
            # 测试卡片消息
            print("  测试Lark卡片消息...")
            card_result = await self.webhook_client.send_card_message(
                header_title="🧪 预警系统功能测试",
                fields={
                    "测试时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "测试内容": "卡片消息发送测试",
                    "系统状态": "正常运行"
                }
            )
            
            if card_result.get("success"):
                self._pass_test("Lark卡片消息发送")
            else:
                self._fail_test("Lark卡片消息发送", card_result.get("error", "未知错误"))
            
            # 测试加密货币预警消息
            print("  测试加密货币预警消息...")
            crypto_result = await self.webhook_client.send_crypto_alert(
                alert_type="测试预警",
                symbol="BTC",
                timeframe="1h",
                price=50000.0,
                indicator_name="RSI",
                indicator_value=25.5,
                signal_name="RSI_OVERSOLD"
            )
            
            if crypto_result.get("success"):
                self._pass_test("加密货币预警消息")
            else:
                self._fail_test("加密货币预警消息", crypto_result.get("error", "未知错误"))
            
        except Exception as e:
            self._fail_test("Webhook客户端测试", str(e))
    
    async def _test_alert_manager(self):
        """测试预警管理器"""
        print("\n⚠️ 测试预警管理器...")
        
        try:
            # 创建测试预警规则
            print("  测试创建预警规则...")
            test_rule = AlertRule(
                name="测试BTC价格预警",
                description="BTC价格超过60000时的测试预警",
                symbol="BTC",
                timeframes=["1h"],
                trigger_type=AlertTriggerType.PRICE_THRESHOLD,
                trigger_conditions=QueryCondition(
                    field=QueryField.CLOSE,
                    operator=QueryOperator.GT,
                    value=60000
                ),
                frequency=AlertFrequency.ONCE,
                webhook_url=self.webhook_client.default_webhook_url,
                message_template="BTC价格突破$60,000测试预警"
            )
            
            rule_id = await self.alert_manager.create_alert_rule(test_rule)
            
            if rule_id:
                self._pass_test("创建预警规则")
            else:
                self._fail_test("创建预警规则", "未返回规则ID")
            
            # 测试获取预警规则
            print("  测试获取预警规则...")
            retrieved_rule = await self.alert_manager.get_alert_rule(rule_id)
            
            if retrieved_rule and retrieved_rule.name == "测试BTC价格预警":
                self._pass_test("获取预警规则")
            else:
                self._fail_test("获取预警规则", "规则不存在或内容不匹配")
            
            # 测试列出预警规则
            print("  测试列出预警规则...")
            rules = await self.alert_manager.list_alert_rules(symbol="BTC")
            
            if any(rule.id == rule_id for rule in rules):
                self._pass_test("列出预警规则")
            else:
                self._fail_test("列出预警规则", "找不到刚创建的规则")
            
            # 测试更新预警规则
            print("  测试更新预警规则...")
            update_success = await self.alert_manager.update_alert_rule(
                rule_id, 
                {"description": "更新后的测试描述"}
            )
            
            if update_success:
                self._pass_test("更新预警规则")
            else:
                self._fail_test("更新预警规则", "更新失败")
            
            # 测试预警规则
            print("  测试预警规则测试功能...")
            test_result = await self.alert_manager.test_alert_rule(rule_id)
            
            if test_result.get("success"):
                self._pass_test("预警规则测试")
            else:
                self._fail_test("预警规则测试", test_result.get("error", "测试失败"))
            
            # 测试获取统计信息
            print("  测试获取预警统计...")
            stats = await self.alert_manager.get_alert_stats()
            
            if stats.total_rules > 0:
                self._pass_test("获取预警统计")
            else:
                self._fail_test("获取预警统计", "统计信息为空")
            
            # 清理测试数据
            print("  清理测试数据...")
            delete_success = await self.alert_manager.delete_alert_rule(rule_id)
            
            if delete_success:
                self._pass_test("删除预警规则")
            else:
                self._fail_test("删除预警规则", "删除失败")
            
        except Exception as e:
            self._fail_test("预警管理器测试", str(e))
    
    async def _test_mcp_tools(self):
        """测试MCP工具"""
        print("\n🔧 测试MCP工具...")
        
        try:
            # 测试灵活查询工具
            print("  测试灵活查询工具...")
            query_result = await self.mcp_tools.execute_tool(
                "flexible_crypto_query",
                {
                    "symbol": "BTC",
                    "timeframes": ["1h"],
                    "conditions": {
                        "field": "close",
                        "operator": "gt",
                        "value": 40000
                    },
                    "limit": 5
                }
            )
            
            if query_result.get("success"):
                self._pass_test("灵活查询工具")
            else:
                self._fail_test("灵活查询工具", query_result.get("message", "查询失败"))
            
            # 测试交易信号查询工具
            print("  测试交易信号查询工具...")
            signal_result = await self.mcp_tools.execute_tool(
                "query_trading_signals",
                {
                    "symbol": "BTC",
                    "timeframes": ["1h"],
                    "signal_names": ["RSI_OVERSOLD", "MACD_GOLDEN_CROSS"],
                    "periods": 24
                }
            )
            
            if signal_result.get("success"):
                self._pass_test("交易信号查询工具")
            else:
                self._fail_test("交易信号查询工具", signal_result.get("message", "查询失败"))
            
            # 测试价格分析工具
            print("  测试价格分析工具...")
            price_result = await self.mcp_tools.execute_tool(
                "analyze_price_levels",
                {
                    "symbol": "BTC",
                    "timeframes": ["1h"],
                    "price_level": 50000,
                    "analysis_type": "breakout",
                    "periods": 48
                }
            )
            
            if price_result.get("success"):
                self._pass_test("价格分析工具")
            else:
                self._fail_test("价格分析工具", price_result.get("message", "分析失败"))
            
            # 测试指标极值分析工具
            print("  测试指标极值分析工具...")
            indicator_result = await self.mcp_tools.execute_tool(
                "analyze_indicator_extremes",
                {
                    "symbol": "BTC",
                    "timeframes": ["1h"],
                    "indicator": "rsi",
                    "comparison": "historical_high",
                    "lookback_periods": 100
                }
            )
            
            if indicator_result.get("success"):
                self._pass_test("指标极值分析工具")
            else:
                self._fail_test("指标极值分析工具", indicator_result.get("message", "分析失败"))
            
            # 测试创建价格预警工具
            print("  测试创建价格预警工具...")
            alert_result = await self.mcp_tools.execute_tool(
                "create_price_alert",
                {
                    "name": "MCP测试价格预警",
                    "symbol": "BTC",
                    "price_threshold": 65000,
                    "condition": "above",
                    "timeframes": ["1h"],
                    "frequency": "once",
                    "custom_message": "MCP测试：BTC价格突破$65,000"
                }
            )
            
            if alert_result.get("success"):
                self._pass_test("创建价格预警工具")
                
                # 清理创建的预警规则
                rule_id = alert_result.get("rule_id")
                if rule_id:
                    await self.alert_manager.delete_alert_rule(rule_id)
            else:
                self._fail_test("创建价格预警工具", alert_result.get("message", "创建失败"))
            
            # 测试Webhook测试工具
            print("  测试Webhook测试工具...")
            webhook_result = await self.mcp_tools.execute_tool(
                "test_webhook",
                {
                    "message_type": "text",
                    "test_message": "MCP工具Webhook测试消息"
                }
            )
            
            if webhook_result.get("success"):
                self._pass_test("Webhook测试工具")
            else:
                self._fail_test("Webhook测试工具", webhook_result.get("message", "测试失败"))
            
            # 测试获取统计工具
            print("  测试获取统计工具...")
            stats_result = await self.mcp_tools.execute_tool(
                "get_alert_statistics",
                {}
            )
            
            if stats_result.get("success"):
                self._pass_test("获取统计工具")
            else:
                self._fail_test("获取统计工具", stats_result.get("message", "获取失败"))
            
        except Exception as e:
            self._fail_test("MCP工具测试", str(e))
    
    def _pass_test(self, test_name: str):
        """标记测试通过"""
        self.test_results["passed"] += 1
        print(f"    ✅ {test_name}: 通过")
    
    def _fail_test(self, test_name: str, error: str):
        """标记测试失败"""
        self.test_results["failed"] += 1
        self.test_results["errors"].append(f"{test_name}: {error}")
        print(f"    ❌ {test_name}: 失败 - {error}")
    
    def _show_results(self):
        """显示测试结果"""
        print("\n" + "=" * 60)
        print("📊 测试结果汇总")
        print(f"总测试数: {self.test_results['passed'] + self.test_results['failed']}")
        print(f"通过: {self.test_results['passed']}")
        print(f"失败: {self.test_results['failed']}")
        
        success_rate = (self.test_results["passed"] / (self.test_results['passed'] + self.test_results['failed'])) * 100
        print(f"成功率: {success_rate:.1f}%")
        
        if self.test_results["errors"]:
            print("\n❌ 失败的测试:")
            for error in self.test_results["errors"]:
                print(f"  - {error}")
        
        if success_rate >= 80:
            print("\n🎉 预警系统测试总体通过！")
        else:
            print("\n⚠️ 预警系统测试存在问题，请检查上述错误")


async def main():
    """主函数"""
    try:
        tester = AlertSystemTester()
        await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生严重错误: {e}")
        logger.error(f"测试异常: {e}", exc_info=True)


if __name__ == '__main__':
    asyncio.run(main()) 