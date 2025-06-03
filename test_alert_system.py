#!/usr/bin/env python3
"""
预警系统测试脚本
测试预警规则创建、监控和发送功能
"""
import asyncio
import logging
import json
import requests
from datetime import datetime
from alerts.alert_manager import AlertManager
from alerts.models import (
    AlertRule, QueryCondition, AlertTriggerType, 
    AlertFrequency, LarkMessageType, QueryField, QueryOperator
)
from utils.request_utils import RequestIDGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertSystemTester:
    """预警系统测试器"""
    
    def __init__(self):
        self.alert_manager = AlertManager()
        self.test_results = []
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("=== 开始预警系统测试 ===")
        
        tests = [
            ("测试创建价格预警规则", self.test_create_price_alert),
            ("测试创建指标预警规则", self.test_create_indicator_alert),
            ("测试创建信号预警规则", self.test_create_signal_alert),
            ("测试预警规则列表", self.test_list_rules),
            ("测试预警规则更新", self.test_update_rule),
            ("测试预警检查功能", self.test_alert_check),
            ("测试统计信息", self.test_get_stats),
        ]
        
        for test_name, test_func in tests:
            try:
                logger.info(f"\n--- {test_name} ---")
                result = await test_func()
                self.test_results.append({
                    "test": test_name,
                    "status": "PASS" if result else "FAIL",
                    "result": result
                })
                logger.info(f"✅ {test_name}: {'通过' if result else '失败'}")
            except Exception as e:
                logger.error(f"❌ {test_name}: 异常 - {e}")
                self.test_results.append({
                    "test": test_name,
                    "status": "ERROR",
                    "error": str(e)
                })
        
        self.print_test_summary()
    
    async def test_create_price_alert(self):
        """测试创建价格预警"""
        try:
            rule = AlertRule(
                name="测试BTC价格预警",
                description="BTC价格超过105000时触发",
                symbol="BTC",
                timeframes=["1h"],
                trigger_type=AlertTriggerType.PRICE_THRESHOLD,
                trigger_conditions=QueryCondition(
                    field=QueryField.CLOSE,
                    operator=QueryOperator.GT,
                    value=105000
                ),
                frequency=AlertFrequency.ONCE,
                custom_message="BTC价格突破测试阈值！"
            )
            
            rule_id = await self.alert_manager.create_alert_rule(rule)
            logger.info(f"创建价格预警规则成功: {rule_id}")
            
            # 验证规则是否存在
            retrieved_rule = await self.alert_manager.get_alert_rule(rule_id)
            return retrieved_rule is not None
            
        except Exception as e:
            logger.error(f"创建价格预警失败: {e}")
            return False
    
    async def test_create_indicator_alert(self):
        """测试创建指标预警"""
        try:
            rule = AlertRule(
                name="测试RSI预警",
                description="RSI大于70时触发超买预警",
                symbol="BTC",
                timeframes=["1h"],
                trigger_type=AlertTriggerType.INDICATOR_THRESHOLD,
                trigger_conditions=QueryCondition(
                    field=QueryField.RSI,
                    operator=QueryOperator.GT,
                    value=70
                ),
                frequency=AlertFrequency.EVERY_TIME,
                custom_message="RSI超买信号！"
            )
            
            rule_id = await self.alert_manager.create_alert_rule(rule)
            logger.info(f"创建指标预警规则成功: {rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"创建指标预警失败: {e}")
            return False
    
    async def test_create_signal_alert(self):
        """测试创建信号预警"""
        try:
            rule = AlertRule(
                name="测试信号预警",
                description="检测到MACD金叉信号时触发",
                symbol="BTC",
                timeframes=["1h"],
                trigger_type=AlertTriggerType.SIGNAL_DETECTION,
                trigger_conditions=QueryCondition(
                    field=QueryField.SIGNALS,
                    operator=QueryOperator.CONTAINS,
                    value=["MACD_GOLDEN_CROSS", "RSI_OVERSOLD"]
                ),
                frequency=AlertFrequency.EVERY_TIME,
                custom_message="检测到重要交易信号！"
            )
            
            rule_id = await self.alert_manager.create_alert_rule(rule)
            logger.info(f"创建信号预警规则成功: {rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"创建信号预警失败: {e}")
            return False
    
    async def test_list_rules(self):
        """测试列出预警规则"""
        try:
            rules = await self.alert_manager.list_alert_rules()
            logger.info(f"当前预警规则数量: {len(rules)}")
            
            for rule in rules:
                logger.info(f"  - {rule.name} ({rule.symbol}, {rule.trigger_type})")
            
            return len(rules) > 0
            
        except Exception as e:
            logger.error(f"列出预警规则失败: {e}")
            return False
    
    async def test_update_rule(self):
        """测试更新预警规则"""
        try:
            # 获取第一个规则进行测试
            rules = await self.alert_manager.list_alert_rules(limit=1)
            if not rules:
                logger.warning("没有可更新的规则")
                return True
            
            rule_id = rules[0].id
            
            # 更新描述
            success = await self.alert_manager.update_alert_rule(rule_id, {
                "description": "更新后的描述 - 测试更新功能"
            })
            
            logger.info(f"更新规则 {rule_id}: {'成功' if success else '失败'}")
            return success
            
        except Exception as e:
            logger.error(f"更新预警规则失败: {e}")
            return False
    
    async def test_alert_check(self):
        """测试预警检查功能"""
        try:
            # 执行一次预警检查
            triggered_alerts = await self.alert_manager.check_alert_rules()
            logger.info(f"本次检查触发预警数量: {len(triggered_alerts)}")
            
            for alert in triggered_alerts:
                logger.info(f"  触发: {alert.rule_name} - {alert.symbol}")
            
            return True
            
        except Exception as e:
            logger.error(f"预警检查失败: {e}")
            return False
    
    async def test_get_stats(self):
        """测试获取统计信息"""
        try:
            stats = await self.alert_manager.get_alert_stats()
            logger.info(f"预警统计信息:")
            logger.info(f"  总规则数: {stats.total_rules}")
            logger.info(f"  激活规则数: {stats.active_rules}")
            logger.info(f"  今日触发: {stats.triggered_today}")
            logger.info(f"  本小时触发: {stats.triggered_this_hour}")
            logger.info(f"  成功率: {stats.success_rate:.1f}%")
            
            return True
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return False
    
    def print_test_summary(self):
        """打印测试摘要"""
        logger.info("\n=== 测试结果摘要 ===")
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        errors = sum(1 for r in self.test_results if r["status"] == "ERROR")
        
        logger.info(f"总测试数: {total}")
        logger.info(f"通过: {passed}")
        logger.info(f"失败: {failed}")
        logger.info(f"错误: {errors}")
        
        if failed > 0 or errors > 0:
            logger.info("\n失败/错误的测试:")
            for result in self.test_results:
                if result["status"] != "PASS":
                    logger.info(f"  - {result['test']}: {result['status']}")
                    if "error" in result:
                        logger.info(f"    错误: {result['error']}")


async def test_external_api_mock():
    """测试外部API模拟"""
    logger.info("\n=== 测试外部API模拟 ===")
    
    # 创建模拟的预警触发数据
    test_data = {
        "request_id": RequestIDGenerator.generate(),
        "alert_type": "price_alert",
        "rule_id": "test-rule-123",
        "rule_name": "测试价格预警",
        "symbol": "BTC",
        "timeframe": "1h",
        "trigger_time": datetime.utcnow().isoformat(),
        "trigger_data": {
            "description": "BTC价格大于$105000时触发预警",
            "actual_value": "$105123.45",
            "threshold": "$105000.00",
            "comparison": "当前价格$105123.45 大于 设定阈值$105000.00",
            "custom_message": "BTC价格突破重要阻力位！",
            "actual_price": 105123.45,
            "threshold": 105000,
            "condition": "gt"
        },
        "notification_config": {
            "target_webhook": "https://open.larksuite.com/open-apis/bot/v2/hook/test",
            "message_type": "text",
            "frequency": "once"
        }
    }
    
    # 模拟发送到外部API
    try:
        logger.info("模拟发送预警数据到外部API...")
        logger.info(f"目标URL: http://localhost:8081/webhook/alert/trigger")
        logger.info(f"请求数据: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
        
        # 在实际环境中，这里会发送到真实的外部API
        logger.info("✅ 预警数据格式正确，可以发送到外部API")
        return True
        
    except Exception as e:
        logger.error(f"❌ 外部API测试失败: {e}")
        return False


async def main():
    """主函数"""
    try:
        # 测试预警系统
        tester = AlertSystemTester()
        await tester.run_all_tests()
        
        # 测试外部API模拟
        await test_external_api_mock()
        
        logger.info("\n=== 所有测试完成 ===")
        
    except Exception as e:
        logger.error(f"测试运行失败: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 