#!/usr/bin/env python3
"""
完整系统端到端测试脚本
测试从K线数据获取到Lark消息发送的完整流程

测试流程:
1. 基础模块导入测试
2. 数据库连接测试  
3. 数据采集系统测试
4. 技术指标计算测试
5. 技术信号检测测试
6. API服务测试
7. MCP服务测试
8. 预警系统测试
9. Webhook消息发送测试
10. 完整流程集成测试
"""

import sys
import os
import asyncio
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class SystemTestRunner:
    """系统测试运行器"""
    
    def __init__(self):
        self.test_results = []
        self.api_base_url = "http://localhost:5001"
        self.mcp_ws_url = "ws://localhost:8080"
        self.mcp_health_url = "http://localhost:8081"
        
    def log_test(self, test_name: str, success: bool, message: str = "", details: Any = None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
        if message:
            print(f"   {message}")
        if details and isinstance(details, dict) and not success:
            print(f"   详情: {details}")
    
    def test_1_module_imports(self) -> bool:
        """测试1: 基础模块导入"""
        print("\n🔍 测试1: 模块导入测试")
        
        modules_to_test = [
            ("utils.logger", "日志模块"),
            ("config.settings", "配置模块"),
            ("database.mongo_client", "数据库模块"),
            ("data_collector.ccxt_collector", "数据采集模块"),
            ("indicators.calculator", "技术指标模块"),
            ("indicators.signals", "信号检测模块"),
            ("scheduler.tasks", "任务调度模块"),
            ("api.app", "API模块"),
            ("alerts.models", "预警模型模块"),
            ("alerts.query_engine", "查询引擎模块"),
            ("alerts.webhook_client", "Webhook客户端模块"),
            ("alerts.alert_manager", "预警管理器模块"),
            ("alerts.mcp_tools", "MCP工具模块")
        ]
        
        success_count = 0
        
        for module_name, display_name in modules_to_test:
            try:
                __import__(module_name)
                self.log_test(f"导入{display_name}", True)
                success_count += 1
            except Exception as e:
                self.log_test(f"导入{display_name}", False, str(e))
        
        overall_success = success_count == len(modules_to_test)
        self.log_test("模块导入测试总结", overall_success, f"{success_count}/{len(modules_to_test)}个模块导入成功")
        
        return overall_success
    
    def test_2_database_connection(self) -> bool:
        """测试2: 数据库连接"""
        print("\n🔍 测试2: 数据库连接测试")
        
        try:
            from database.mongo_client import mongodb_client
            
            # 测试数据库连接
            db_info = mongodb_client.get_database_info()
            self.log_test("数据库连接", True, f"连接成功，文档数: {db_info.get('documents', 0)}")
            
            # 测试数据查询
            collection = mongodb_client.get_collection()
            sample_data = list(collection.find().limit(1))
            
            if sample_data:
                self.log_test("数据查询", True, f"查询到数据: {sample_data[0].get('symbol', 'unknown')}")
            else:
                self.log_test("数据查询", False, "数据库中无数据")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("数据库连接", False, str(e))
            return False
    
    def test_3_data_collection(self) -> bool:
        """测试3: 数据采集系统"""
        print("\n🔍 测试3: 数据采集系统测试")
        
        try:
            from data_collector.ccxt_collector import data_collector
            
            # 测试交易所连接
            if not data_collector.exchange:
                self.log_test("交易所连接", False, "交易所未初始化")
                return False
            
            self.log_test("交易所连接", True, f"连接到: {data_collector.exchange.name}")
            
            # 测试市场数据获取
            market_info = data_collector.get_market_info()
            if market_info:
                for symbol, info in market_info.items():
                    self.log_test(f"获取{symbol}市场数据", True, f"价格: ${info['last_price']:.2f}")
            else:
                self.log_test("市场数据获取", False, "无法获取市场数据")
                return False
            
            # 测试K线数据采集
            from config.settings import SYMBOLS, TIMEFRAMES
            
            for symbol in SYMBOLS[:1]:  # 只测试第一个币种
                for timeframe in TIMEFRAMES[:2]:  # 只测试前两个时间周期
                    try:
                        data = data_collector.fetch_ohlcv_data(symbol, timeframe)
                        if data:
                            self.log_test(f"采集{symbol} {timeframe}数据", True, f"获取{len(data)}条记录")
                        else:
                            self.log_test(f"采集{symbol} {timeframe}数据", False, "无数据返回")
                    except Exception as e:
                        self.log_test(f"采集{symbol} {timeframe}数据", False, str(e))
            
            return True
            
        except Exception as e:
            self.log_test("数据采集系统", False, str(e))
            return False
    
    def test_4_technical_indicators(self) -> bool:
        """测试4: 技术指标计算"""
        print("\n🔍 测试4: 技术指标计算测试")
        
        try:
            from indicators.calculator import indicator_calculator
            from database.mongo_client import mongodb_client
            
            # 获取一些样本数据
            collection = mongodb_client.get_collection()
            sample_data = list(collection.find({"symbol": "BTC", "timeframe": "1h"}).limit(60))
            
            if not sample_data:
                self.log_test("技术指标测试数据", False, "没有足够的历史数据用于测试")
                return False
            
            self.log_test("技术指标测试数据", True, f"获取{len(sample_data)}条历史数据")
            
            # 测试指标计算
            indicators_to_test = [
                ("RSI", "rsi"),
                ("MACD", "macd"),
                ("移动平均线", "ma"),
                ("布林带", "bollinger"),
                ("随机振荡器", "stochastic"),
                ("CCI", "cci"),
                ("KDJ", "kdj")
            ]
            
            for indicator_name, indicator_key in indicators_to_test:
                try:
                    # 检查最近的记录是否包含该指标
                    recent_data = collection.find_one(
                        {"symbol": "BTC", "timeframe": "1h", indicator_key: {"$exists": True}},
                        sort=[("timestamp", -1)]
                    )
                    
                    if recent_data and indicator_key in recent_data:
                        self.log_test(f"{indicator_name}计算", True, f"计算成功")
                    else:
                        self.log_test(f"{indicator_name}计算", False, f"未找到{indicator_name}数据")
                except Exception as e:
                    self.log_test(f"{indicator_name}计算", False, str(e))
            
            return True
            
        except Exception as e:
            self.log_test("技术指标计算", False, str(e))
            return False
    
    def test_5_signal_detection(self) -> bool:
        """测试5: 技术信号检测"""
        print("\n🔍 测试5: 技术信号检测测试")
        
        try:
            from indicators.signals import signal_detector
            from database.mongo_client import mongodb_client
            
            # 获取包含信号的数据
            collection = mongodb_client.get_collection()
            signal_data = list(collection.find(
                {"symbol": "BTC", "signals": {"$exists": True, "$ne": []}},
                sort=[("timestamp", -1)]
            ).limit(10))
            
            if signal_data:
                self.log_test("信号检测数据", True, f"找到{len(signal_data)}条包含信号的记录")
                
                # 统计信号类型
                all_signals = []
                for record in signal_data:
                    all_signals.extend(record.get("signals", []))
                
                unique_signals = list(set(all_signals))
                self.log_test("信号类型统计", True, f"检测到{len(unique_signals)}种信号类型")
                
                # 展示前几种信号
                for signal in unique_signals[:5]:
                    self.log_test(f"信号: {signal}", True, "信号检测正常")
                
            else:
                self.log_test("信号检测数据", False, "未找到包含信号的数据")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("技术信号检测", False, str(e))
            return False
    
    def test_6_api_service(self) -> bool:
        """测试6: API服务"""
        print("\n🔍 测试6: API服务测试")
        
        try:
            # 测试健康检查端点
            try:
                response = requests.get(f"{self.api_base_url}/api/v1/health", timeout=10)
                if response.status_code == 200:
                    health_data = response.json()
                    self.log_test("API健康检查", True, f"状态: {health_data.get('status', 'unknown')}")
                else:
                    self.log_test("API健康检查", False, f"HTTP {response.status_code}")
                    return False
            except requests.exceptions.ConnectionError:
                self.log_test("API健康检查", False, "API服务未启动")
                return False
            
            # 测试币种列表端点
            try:
                response = requests.get(f"{self.api_base_url}/api/v1/symbols", timeout=10)
                if response.status_code == 200:
                    symbols_data = response.json()
                    symbols = symbols_data.get("data", {}).get("symbols", [])
                    self.log_test("API币种列表", True, f"支持币种: {symbols}")
                else:
                    self.log_test("API币种列表", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test("API币种列表", False, str(e))
            
            # 测试信号查询端点
            try:
                test_payload = {
                    "symbol": "BTC",
                    "timeframes": ["1h"]
                }
                response = requests.post(
                    f"{self.api_base_url}/api/v1/signals",
                    json=test_payload,
                    timeout=10
                )
                if response.status_code == 200:
                    signals_data = response.json()
                    total_periods = signals_data.get("data", {}).get("summary", {}).get("total_periods", 0)
                    self.log_test("API信号查询", True, f"返回{total_periods}个时段数据")
                else:
                    self.log_test("API信号查询", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test("API信号查询", False, str(e))
            
            return True
            
        except Exception as e:
            self.log_test("API服务", False, str(e))
            return False
    
    def test_7_mcp_service(self) -> bool:
        """测试7: MCP服务"""
        print("\n🔍 测试7: MCP服务测试")
        
        try:
            # 测试MCP健康检查
            try:
                response = requests.get(f"{self.mcp_health_url}/health", timeout=10)
                if response.status_code == 200:
                    health_data = response.json()
                    self.log_test("MCP健康检查", True, f"状态: {health_data.get('status', 'unknown')}")
                else:
                    self.log_test("MCP健康检查", False, f"HTTP {response.status_code}")
                    return False
            except requests.exceptions.ConnectionError:
                self.log_test("MCP健康检查", False, "MCP服务未启动")
                return False
            
            # 测试MCP工具
            try:
                from alerts.mcp_tools import AlertMCPTools
                
                mcp_tools = AlertMCPTools()
                tool_definitions = mcp_tools.get_tool_definitions()
                
                self.log_test("MCP工具定义", True, f"定义了{len(tool_definitions)}个工具")
                
                # 测试每个工具的定义
                for tool in tool_definitions:
                    tool_name = tool.get("name", "unknown")
                    self.log_test(f"MCP工具: {tool_name}", True, "定义正常")
                
            except Exception as e:
                self.log_test("MCP工具", False, str(e))
            
            return True
            
        except Exception as e:
            self.log_test("MCP服务", False, str(e))
            return False
    
    async def test_8_alert_system(self) -> bool:
        """测试8: 预警系统"""
        print("\n🔍 测试8: 预警系统测试")
        
        try:
            from alerts.alert_manager import AlertManager
            from alerts.query_engine import QueryEngine
            from alerts.models import AlertRule, QueryCondition, QueryOperator, QueryField, AlertTriggerType
            
            # 初始化预警管理器
            alert_manager = AlertManager()
            query_engine = QueryEngine()
            
            # 测试查询引擎
            try:
                from alerts.models import QueryRequest
                
                test_query = QueryRequest(
                    symbol="BTC",
                    timeframes=["1h"],
                    conditions=QueryCondition(
                        field=QueryField.CLOSE,
                        operator=QueryOperator.GT,
                        value=0
                    ),
                    limit=5
                )
                
                result = await query_engine.execute_query(test_query)
                if result.matched_records > 0:
                    self.log_test("查询引擎", True, f"查询到{result.matched_records}条记录")
                else:
                    self.log_test("查询引擎", False, "查询无结果")
                    
            except Exception as e:
                self.log_test("查询引擎", False, str(e))
            
            # 测试预警规则创建
            try:
                test_rule = AlertRule(
                    name="测试预警规则",
                    description="用于系统测试的预警规则",
                    symbol="BTC",
                    timeframes=["1h"],
                    trigger_type=AlertTriggerType.PRICE_THRESHOLD,
                    trigger_conditions=QueryCondition(
                        field=QueryField.CLOSE,
                        operator=QueryOperator.GT,
                        value=999999  # 设置一个不会触发的高价格
                    )
                )
                
                rule_id = await alert_manager.create_alert_rule(test_rule)
                if rule_id:
                    self.log_test("预警规则创建", True, f"规则ID: {rule_id}")
                    
                    # 测试规则查询
                    retrieved_rule = await alert_manager.get_alert_rule(rule_id)
                    if retrieved_rule:
                        self.log_test("预警规则查询", True, f"规则名称: {retrieved_rule.name}")
                    else:
                        self.log_test("预警规则查询", False, "无法查询到创建的规则")
                    
                    # 测试规则删除
                    deleted = await alert_manager.delete_alert_rule(rule_id)
                    if deleted:
                        self.log_test("预警规则删除", True, "规则删除成功")
                    else:
                        self.log_test("预警规则删除", False, "规则删除失败")
                        
                else:
                    self.log_test("预警规则创建", False, "创建失败")
                    
            except Exception as e:
                self.log_test("预警规则管理", False, str(e))
            
            # 测试预警统计
            try:
                stats = await alert_manager.get_alert_stats()
                self.log_test("预警统计", True, f"总规则数: {stats.total_rules}, 激活规则: {stats.active_rules}")
            except Exception as e:
                self.log_test("预警统计", False, str(e))
            
            return True
            
        except Exception as e:
            self.log_test("预警系统", False, str(e))
            return False
    
    async def test_9_webhook_messaging(self) -> bool:
        """测试9: Webhook消息发送"""
        print("\n🔍 测试9: Webhook消息发送测试")
        
        try:
            from alerts.webhook_client import LarkWebhookClient
            
            webhook_client = LarkWebhookClient()
            
            # 测试简单文本消息
            try:
                test_message = f"🧪 系统测试消息 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                result = await webhook_client.send_text_message(test_message)
                
                if result.get("success"):
                    self.log_test("Webhook文本消息", True, "消息发送成功")
                else:
                    self.log_test("Webhook文本消息", False, f"发送失败: {result.get('error', 'unknown')}")
                    
            except Exception as e:
                self.log_test("Webhook文本消息", False, str(e))
            
            # 测试预警消息
            try:
                result = await webhook_client.send_crypto_alert(
                    alert_rule_name="系统测试预警",
                    alert_rule_description="这是一个用于测试系统功能的预警消息",
                    alert_type="系统测试",
                    symbol="BTC",
                    timeframe="1h",
                    trigger_condition="系统测试触发条件",
                    actual_value="测试数值",
                    threshold_value="测试阈值",
                    comparison_result="测试对比结果",
                    price=50000.0,
                    trigger_time=datetime.now(),
                    custom_message="这是系统测试，请忽略此消息"
                )
                
                if result.get("success"):
                    self.log_test("Webhook预警消息", True, "预警消息发送成功")
                else:
                    self.log_test("Webhook预警消息", False, f"发送失败: {result.get('error', 'unknown')}")
                    
            except Exception as e:
                self.log_test("Webhook预警消息", False, str(e))
            
            # 测试Webhook连接
            try:
                test_result = await webhook_client.test_webhook()
                if test_result.get("success"):
                    self.log_test("Webhook连接测试", True, "连接测试成功")
                else:
                    self.log_test("Webhook连接测试", False, f"连接测试失败: {test_result.get('error', 'unknown')}")
            except Exception as e:
                self.log_test("Webhook连接测试", False, str(e))
            
            return True
            
        except Exception as e:
            self.log_test("Webhook消息发送", False, str(e))
            return False
    
    async def test_10_mcp_tools_integration(self) -> bool:
        """测试10: MCP工具集成"""
        print("\n🔍 测试10: MCP工具集成测试")
        
        try:
            from alerts.mcp_tools import AlertMCPTools
            
            mcp_tools = AlertMCPTools()
            
            # 测试统计信息工具
            try:
                result = await mcp_tools.execute_tool("get_alert_statistics", {})
                if result.get("success"):
                    stats = result.get("data", {})
                    self.log_test("MCP统计工具", True, f"总规则: {stats.get('total_rules', 0)}")
                else:
                    self.log_test("MCP统计工具", False, f"执行失败: {result.get('error', 'unknown')}")
            except Exception as e:
                self.log_test("MCP统计工具", False, str(e))
            
            # 测试查询工具
            try:
                result = await mcp_tools.execute_tool("flexible_crypto_query", {
                    "symbol": "BTC",
                    "timeframes": ["1h"],
                    "conditions": {
                        "field": "close",
                        "operator": "gt",
                        "value": 0
                    },
                    "limit": 3
                })
                
                if result.get("success"):
                    matched = result.get("data", {}).get("matched_records", 0)
                    self.log_test("MCP查询工具", True, f"匹配记录: {matched}")
                else:
                    self.log_test("MCP查询工具", False, f"执行失败: {result.get('error', 'unknown')}")
                    
            except Exception as e:
                self.log_test("MCP查询工具", False, str(e))
            
            # 测试价格预警创建工具
            try:
                result = await mcp_tools.execute_tool("create_price_alert", {
                    "name": "MCP测试预警",
                    "symbol": "BTC",
                    "price_threshold": 999999,  # 不会触发的高价格
                    "condition": "above",
                    "timeframes": ["1h"],
                    "frequency": "once",
                    "custom_message": "这是MCP工具测试创建的预警"
                })
                
                if result.get("success"):
                    rule_id = result.get("data", {}).get("rule_id")
                    self.log_test("MCP预警创建工具", True, f"创建成功: {rule_id}")
                    
                    # 清理测试数据
                    try:
                        from alerts.alert_manager import AlertManager
                        alert_manager = AlertManager()
                        await alert_manager.delete_alert_rule(rule_id)
                        self.log_test("MCP测试数据清理", True, "清理成功")
                    except Exception:
                        pass
                        
                else:
                    self.log_test("MCP预警创建工具", False, f"创建失败: {result.get('error', 'unknown')}")
                    
            except Exception as e:
                self.log_test("MCP预警创建工具", False, str(e))
            
            # 测试Webhook测试工具
            try:
                result = await mcp_tools.execute_tool("test_webhook", {
                    "message_type": "text",
                    "test_message": "MCP工具Webhook测试"
                })
                
                if result.get("success"):
                    self.log_test("MCP Webhook测试工具", True, "测试成功")
                else:
                    self.log_test("MCP Webhook测试工具", False, f"测试失败: {result.get('error', 'unknown')}")
                    
            except Exception as e:
                self.log_test("MCP Webhook测试工具", False, str(e))
            
            return True
            
        except Exception as e:
            self.log_test("MCP工具集成", False, str(e))
            return False
    
    async def test_11_complete_integration(self) -> bool:
        """测试11: 完整集成流程"""
        print("\n🔍 测试11: 完整集成流程测试")
        
        try:
            # 这是一个端到端的集成测试
            # 模拟一个完整的预警触发流程
            
            from alerts.mcp_tools import AlertMCPTools
            from database.mongo_client import mongodb_client
            
            mcp_tools = AlertMCPTools()
            
            # 1. 查询当前BTC价格
            collection = mongodb_client.get_collection()
            latest_btc = collection.find_one(
                {"symbol": "BTC", "timeframe": "1h"},
                sort=[("timestamp", -1)]
            )
            
            if not latest_btc:
                self.log_test("集成测试-获取BTC数据", False, "无法获取最新BTC数据")
                return False
                
            current_price = latest_btc.get("close", 0)
            self.log_test("集成测试-获取BTC数据", True, f"当前价格: ${current_price:,.2f}")
            
            # 2. 创建一个会立即触发的预警 (价格低于当前价格+1000)
            test_threshold = current_price + 1000
            
            result = await mcp_tools.execute_tool("create_price_alert", {
                "name": "集成测试预警",
                "symbol": "BTC",
                "price_threshold": test_threshold,
                "condition": "below",  # 当前价格肯定低于阈值
                "timeframes": ["1h"],
                "frequency": "once",
                "custom_message": "这是完整集成测试创建的预警，应该会立即触发"
            })
            
            if not result.get("success"):
                self.log_test("集成测试-创建预警", False, f"创建失败: {result.get('error')}")
                return False
                
            rule_id = result.get("data", {}).get("rule_id")
            self.log_test("集成测试-创建预警", True, f"创建成功: {rule_id}")
            
            # 3. 等待一会儿，让系统有时间处理
            await asyncio.sleep(2)
            
            # 4. 手动触发预警检查
            try:
                from alerts.alert_manager import AlertManager
                alert_manager = AlertManager()
                
                triggered_alerts = await alert_manager.check_alert_rules()
                
                # 查找我们的测试预警是否触发
                test_alert_triggered = any(
                    alert.rule_id == rule_id for alert in triggered_alerts
                )
                
                if test_alert_triggered:
                    self.log_test("集成测试-预警触发", True, "预警成功触发")
                else:
                    self.log_test("集成测试-预警触发", False, "预警未触发")
                
                # 清理测试数据
                await alert_manager.delete_alert_rule(rule_id)
                self.log_test("集成测试-清理数据", True, "测试数据清理完成")
                
            except Exception as e:
                self.log_test("集成测试-预警触发", False, str(e))
            
            # 5. 测试完整的查询分析流程
            try:
                # 使用MCP工具进行复合查询
                query_result = await mcp_tools.execute_tool("analyze_price_levels", {
                    "symbol": "BTC",
                    "timeframes": ["1h"],
                    "price_level": current_price,
                    "analysis_type": "support",
                    "periods": 24
                })
                
                if query_result.get("success"):
                    analysis = query_result.get("data", {})
                    self.log_test("集成测试-价格分析", True, f"分析完成，检查了{analysis.get('total_periods', 0)}个时段")
                else:
                    self.log_test("集成测试-价格分析", False, f"分析失败: {query_result.get('error')}")
                    
            except Exception as e:
                self.log_test("集成测试-价格分析", False, str(e))
            
            return True
            
        except Exception as e:
            self.log_test("完整集成流程", False, str(e))
            return False
    
    def generate_test_report(self):
        """生成测试报告"""
        print("\n" + "="*80)
        print("📊 完整系统测试报告")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        
        print("\n📋 详细结果:")
        
        current_test_group = ""
        for result in self.test_results:
            test_name = result["test_name"]
            # 提取测试组名称（如果测试名称包含组信息）
            if "-" in test_name:
                group = test_name.split("-")[0]
                if group != current_test_group:
                    current_test_group = group
                    print(f"\n🔶 {group}:")
            
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {test_name}")
            if result["message"]:
                print(f"     {result['message']}")
            
            if not result["success"] and result["details"]:
                print(f"     详情: {result['details']}")
        
        print("\n" + "="*80)
        
        if passed_tests == total_tests:
            print("🎉 所有测试通过！系统运行正常。")
            print("\n💡 系统现在可以正常使用以下功能：")
            print("   • K线数据采集和技术指标计算")
            print("   • RESTful API查询服务")
            print("   • MCP协议AI Agent接口")
            print("   • 智能预警系统")
            print("   • 飞书Webhook消息推送")
        else:
            print("⚠️ 部分测试失败，请检查相关模块。")
            print("\n🔧 建议检查：")
            print("   • 数据库连接和数据完整性")
            print("   • 网络连接和外部服务")
            print("   • 配置文件和环境变量")
            print("   • 服务启动状态")
        
        print("="*80)
        
        return passed_tests == total_tests
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始完整系统端到端测试")
        print("测试范围: 数据采集 → 技术分析 → API服务 → MCP接口 → 预警系统 → 消息推送")
        print("="*80)
        
        # 同步测试
        tests = [
            self.test_1_module_imports,
            self.test_2_database_connection,
            self.test_3_data_collection,
            self.test_4_technical_indicators,
            self.test_5_signal_detection,
            self.test_6_api_service,
            self.test_7_mcp_service,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_test(f"测试异常: {test.__name__}", False, str(e))
        
        # 异步测试
        async_tests = [
            self.test_8_alert_system,
            self.test_9_webhook_messaging,
            self.test_10_mcp_tools_integration,
            self.test_11_complete_integration,
        ]
        
        for test in async_tests:
            try:
                await test()
            except Exception as e:
                self.log_test(f"测试异常: {test.__name__}", False, str(e))
        
        # 生成报告
        return self.generate_test_report()

async def main():
    """主函数"""
    runner = SystemTestRunner()
    success = await runner.run_all_tests()
    
    if success:
        print("\n🎯 下一步操作建议:")
        print("1. 启动所有服务: python start_all_services.py")
        print("2. 访问API文档: http://localhost:5000/api/v1/docs")
        print("3. 查看MCP服务状态: http://localhost:8081/health")
        print("4. 开始使用预警系统和MCP工具")
    else:
        print("\n🔧 故障排除建议:")
        print("1. 检查MongoDB是否启动: mongod")
        print("2. 检查网络连接和防火墙设置")
        print("3. 验证所有依赖包是否正确安装")
        print("4. 查看详细日志: logs/目录下的日志文件")
    
    return success

if __name__ == "__main__":
    asyncio.run(main()) 