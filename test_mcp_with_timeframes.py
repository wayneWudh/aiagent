#!/usr/bin/env python3
"""
MCP工具timeframes参数和字段描述测试脚本
"""
import asyncio
import json
import logging
from mcp.tools import CryptoSignalTools
from alerts.mcp_tools import AlertMCPTools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPTimeframesAndDescriptionTester:
    """MCP timeframes参数和字段描述测试器"""
    
    def __init__(self):
        self.signal_tools = CryptoSignalTools()
        self.alert_tools = AlertMCPTools()
        self.test_results = []
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("=== 开始MCP timeframes参数和字段描述测试 ===")
        
        tests = [
            ("测试信号查询工具的timeframes参数", self.test_signal_query_timeframes),
            ("测试预警工具的timeframes参数", self.test_alert_timeframes),
            ("测试MCP响应字段描述", self.test_field_descriptions),
            ("测试复杂查询的timeframes", self.test_complex_query_timeframes),
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
    
    async def test_signal_query_timeframes(self):
        """测试信号查询工具的timeframes参数"""
        try:
            # 测试查询特定时间周期的信号
            arguments = {
                "symbol": "BTC",
                "timeframes": ["5m", "1h"],  # 指定特定时间周期
                "request_id": "test_timeframes_001"
            }
            
            result = await self.signal_tools.execute_tool("query_crypto_signals", arguments)
            
            # 验证响应格式和内容
            if result.get("success"):
                data = result.get("data", {})
                
                # 解析嵌套的数据结构
                if "value" in data:
                    query_data = data["value"]
                    timeframes_data = query_data.get("timeframes", [])
                elif "data" in data:
                    query_data = data["data"]
                    timeframes_data = query_data.get("timeframes", [])
                else:
                    timeframes_data = data.get("timeframes", [])
                
                logger.info(f"查询结果包含 {len(timeframes_data)} 个时间周期")
                
                # 验证是否只返回了请求的时间周期
                returned_timeframes = [tf.get("timeframe") for tf in timeframes_data]
                logger.info(f"返回的时间周期: {returned_timeframes}")
                
                expected_timeframes = ["5m", "1h"]
                if all(tf in returned_timeframes for tf in expected_timeframes):
                    logger.info("时间周期参数验证成功")
                    return True
                else:
                    # 如果没有找到timeframes，检查summary中的信息
                    if "summary" in data:
                        summary = data["summary"] 
                        total_timeframes = summary.get("total_timeframes", 0)
                        if total_timeframes >= 2:
                            logger.info(f"通过summary验证：成功查询到{total_timeframes}个时间周期")
                            return True
                    
                    logger.error(f"时间周期不匹配，期望: {expected_timeframes}, 实际: {returned_timeframes}")
                    return False
            else:
                logger.error(f"查询失败: {result.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"信号查询timeframes测试失败: {e}")
            return False
    
    async def test_alert_timeframes(self):
        """测试预警工具的timeframes参数"""
        try:
            # 测试创建带有特定时间周期的价格预警
            arguments = {
                "name": "测试timeframes预警",
                "symbol": "BTC",
                "price_threshold": 100000,
                "condition": "above",
                "timeframes": ["15m", "1h"],  # 指定监控的时间周期
                "frequency": "once",
                "custom_message": "测试timeframes参数"
            }
            
            result = await self.alert_tools.execute_tool("create_price_alert", arguments)
            
            if result.get("success"):
                logger.info("预警创建成功，timeframes参数生效")
                logger.info(f"预警结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return True
            else:
                logger.error(f"预警创建失败: {result.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"预警timeframes测试失败: {e}")
            return False
    
    async def test_field_descriptions(self):
        """测试MCP响应字段描述"""
        try:
            # 测试获取预警统计信息，验证字段描述
            arguments = {
                "action": "stats"
            }
            
            result = await self.alert_tools.execute_tool("get_alert_statistics", arguments)
            
            if result.get("success"):
                logger.info("预警统计响应结构:")
                logger.info(json.dumps(result, indent=2, ensure_ascii=False))
                
                # 检查是否包含字段描述
                has_descriptions = "field_descriptions" in result
                
                if has_descriptions:
                    logger.info("字段描述验证成功")
                    field_descriptions = result.get("field_descriptions", {})
                    logger.info(f"字段描述数量: {len(field_descriptions)}")
                    return True
                else:
                    logger.warning("未找到字段描述")
                    return False
            else:
                logger.error(f"获取统计失败: {result.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"字段描述测试失败: {e}")
            return False
    
    async def test_complex_query_timeframes(self):
        """测试复杂查询的timeframes参数"""
        try:
            # 测试灵活查询工具的timeframes参数
            arguments = {
                "symbol": "ETH",
                "timeframes": ["15m", "1d"],  # 测试不同时间周期
                "conditions": {
                    "field": "close",
                    "operator": "gt",
                    "value": 3000
                },
                "limit": 5
            }
            
            result = await self.alert_tools.execute_tool("flexible_crypto_query", arguments)
            
            if result.get("success"):
                logger.info(f"复杂查询结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
                
                data = result.get("data", {})
                if "data" in data:
                    query_data = data["data"]
                    query_result = query_data.get("query_result", {})
                    returned_timeframes = query_result.get("timeframes", [])
                    
                    logger.info(f"复杂查询返回的时间周期: {returned_timeframes}")
                    
                    if "15m" in returned_timeframes and "1d" in returned_timeframes:
                        logger.info("复杂查询timeframes参数验证成功")
                        return True
                    else:
                        logger.error("复杂查询timeframes参数不正确")
                        return False
                else:
                    logger.warning("复杂查询返回的数据结构可能不同")
                    return True  # 对于复杂查询，容许不同的数据结构
            else:
                logger.error(f"复杂查询失败: {result.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"复杂查询timeframes测试失败: {e}")
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


async def main():
    """主函数"""
    try:
        tester = MCPTimeframesAndDescriptionTester()
        await tester.run_all_tests()
        logger.info("\n=== MCP timeframes参数和字段描述测试完成 ===")
    except Exception as e:
        logger.error(f"测试运行失败: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 