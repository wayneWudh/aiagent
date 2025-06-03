#!/usr/bin/env python3
"""
数据采集系统测试脚本
测试数据采集、技术指标计算和信号检测功能
"""
import asyncio
import logging
import time
from datetime import datetime
from data_collector.ccxt_collector import data_collector
from indicators.calculator import indicator_calculator
from indicators.signals import signal_detector
from database.mongo_client import mongodb_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataCollectionTester:
    """数据采集测试器"""
    
    def __init__(self):
        self.test_results = []
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("=== 开始数据采集系统测试 ===")
        
        tests = [
            ("测试交易所连接", self.test_exchange_connection),
            ("测试数据采集", self.test_data_collection),
            ("测试增量数据采集", self.test_incremental_collection),
            ("测试技术指标计算", self.test_indicators_calculation),
            ("测试信号检测", self.test_signals_detection),
            ("测试数据库存储", self.test_database_storage),
        ]
        
        for test_name, test_func in tests:
            try:
                logger.info(f"\n--- {test_name} ---")
                result = test_func()
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
    
    def test_exchange_connection(self):
        """测试交易所连接"""
        try:
            success = data_collector.initialize_exchange()
            if success:
                logger.info("交易所连接成功")
                return True
            else:
                logger.error("交易所连接失败")
                return False
        except Exception as e:
            logger.error(f"交易所连接异常: {e}")
            return False
    
    def test_data_collection(self):
        """测试数据采集"""
        try:
            # 测试获取最新K线数据
            success = data_collector.collect_latest_data()
            if success:
                logger.info("数据采集成功")
                return True
            else:
                logger.error("数据采集失败")
                return False
        except Exception as e:
            logger.error(f"数据采集异常: {e}")
            return False
    
    def test_incremental_collection(self):
        """测试增量数据采集"""
        try:
            # 获取当前数据库中的记录数
            initial_count = 0
            for symbol in ["BTC", "ETH"]:
                for timeframe in ["5m", "15m", "1h", "1d"]:
                    data = mongodb_client.get_historical_data(symbol, timeframe, limit=1)
                    if data:
                        initial_count += 1
            
            logger.info(f"初始数据记录数: {initial_count}")
            
            # 再次采集
            success = data_collector.collect_latest_data()
            
            # 检查是否有新数据（可能没有，因为是实时数据）
            final_count = 0
            for symbol in ["BTC", "ETH"]:
                for timeframe in ["5m", "15m", "1h", "1d"]:
                    data = mongodb_client.get_historical_data(symbol, timeframe, limit=1)
                    if data:
                        final_count += 1
            
            logger.info(f"最终数据记录数: {final_count}")
            logger.info("增量采集测试完成（注意：可能没有新数据）")
            return success
            
        except Exception as e:
            logger.error(f"增量采集测试异常: {e}")
            return False
    
    def test_indicators_calculation(self):
        """测试技术指标计算"""
        try:
            # 测试计算BTC 1小时的技术指标
            success = indicator_calculator.calculate_indicators_for_symbol_timeframe("BTC", "1h")
            if success:
                logger.info("技术指标计算成功")
                
                # 验证指标是否已存储
                data = mongodb_client.get_latest_data("BTC", "1h", limit=1)
                if data and len(data) > 0:
                    indicators = data[0]
                    has_indicators = any([
                        indicators.get('ma'),
                        indicators.get('rsi'),
                        indicators.get('macd'),
                        indicators.get('bollinger')
                    ])
                    
                    if has_indicators:
                        logger.info("技术指标数据验证成功")
                        return True
                    else:
                        logger.warning("技术指标数据缺失")
                        return False
                else:
                    logger.warning("未找到数据记录")
                    return False
            else:
                logger.error("技术指标计算失败")
                return False
                
        except Exception as e:
            logger.error(f"技术指标计算异常: {e}")
            return False
    
    def test_signals_detection(self):
        """测试信号检测"""
        try:
            # 测试检测BTC 1小时的信号
            signals = signal_detector.detect_signals_for_symbol_timeframe("BTC", "1h")
            logger.info(f"检测到的信号: {signals}")
            
            # 验证信号是否已存储
            data = mongodb_client.get_latest_data("BTC", "1h", limit=1)
            if data and len(data) > 0:
                stored_signals = data[0].get('signals', [])
                logger.info(f"存储的信号: {stored_signals}")
                return True
            else:
                logger.warning("未找到信号数据")
                return False
                
        except Exception as e:
            logger.error(f"信号检测异常: {e}")
            return False
    
    def test_database_storage(self):
        """测试数据库存储"""
        try:
            # 测试数据库连接
            db_info = mongodb_client.get_database_info()
            logger.info(f"数据库信息: {db_info}")
            
            # 验证数据是否存在
            total_records = 0
            for symbol in ["BTC", "ETH"]:
                for timeframe in ["5m", "15m", "1h", "1d"]:
                    data = mongodb_client.get_historical_data(symbol, timeframe, limit=10)
                    total_records += len(data)
            
            logger.info(f"数据库中总记录数: {total_records}")
            
            if total_records > 0:
                logger.info("数据库存储验证成功")
                return True
            else:
                logger.warning("数据库中没有数据")
                return False
                
        except Exception as e:
            logger.error(f"数据库存储测试异常: {e}")
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


def main():
    """主函数"""
    try:
        tester = DataCollectionTester()
        tester.run_all_tests()
        logger.info("\n=== 数据采集系统测试完成 ===")
    except Exception as e:
        logger.error(f"测试运行失败: {e}")


if __name__ == "__main__":
    main() 