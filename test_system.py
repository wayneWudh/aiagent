#!/usr/bin/env python3
"""
系统测试脚本
用于验证各个模块是否正常工作
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        from utils.logger import setup_logging
        print("✅ 日志模块导入成功")
        
        from config.settings import SYMBOLS, TIMEFRAMES
        print("✅ 配置模块导入成功")
        
        from database.mongo_client import mongodb_client
        print("✅ 数据库模块导入成功")
        
        from data_collector.ccxt_collector import data_collector
        print("✅ 数据采集模块导入成功")
        
        from indicators.calculator import indicator_calculator
        print("✅ 技术指标模块导入成功")
        
        from indicators.signals import signal_detector
        print("✅ 技术信号模块导入成功")
        
        from scheduler.tasks import task_scheduler
        print("✅ 任务调度模块导入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_dependencies():
    """测试外部依赖"""
    print("\n🔍 测试外部依赖...")
    
    try:
        import ccxt
        print("✅ CCXT库可用")
        
        import pymongo
        print("✅ PyMongo库可用")
        
        import pandas
        print("✅ Pandas库可用")
        
        import numpy
        print("✅ Numpy库可用")
        
        try:
            import talib
            print("✅ TA-Lib库可用")
        except ImportError:
            print("⚠️  TA-Lib库未安装，请先安装TA-Lib")
            return False
        
        from apscheduler.schedulers.background import BackgroundScheduler
        print("✅ APScheduler库可用")
        
        return True
        
    except Exception as e:
        print(f"❌ 依赖测试失败: {e}")
        return False

def test_configuration():
    """测试配置"""
    print("\n🔍 测试配置...")
    
    try:
        from config.settings import SYMBOLS, TIMEFRAMES, MONGODB_CONFIG
        
        print(f"✅ 监控币种: {SYMBOLS}")
        print(f"✅ 时间周期: {TIMEFRAMES}")
        print(f"✅ MongoDB配置: {MONGODB_CONFIG['host']}:{MONGODB_CONFIG['port']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False

def test_exchange_connection():
    """测试交易所连接"""
    print("\n🔍 测试交易所连接...")
    
    try:
        from data_collector.ccxt_collector import data_collector
        
        if data_collector.exchange:
            print("✅ 交易所连接成功")
            
            # 测试获取市场信息
            market_info = data_collector.get_market_info()
            if market_info:
                print("✅ 市场数据获取成功")
                for symbol, info in market_info.items():
                    print(f"   {symbol}: ${info['last_price']:.2f}")
            else:
                print("⚠️  市场数据获取失败")
            
            return True
        else:
            print("❌ 交易所连接失败")
            return False
            
    except Exception as e:
        print(f"❌ 交易所连接测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🚀 加密货币分析系统 - 模块测试")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_dependencies,
        test_configuration,
        test_exchange_connection,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统准备就绪。")
        print("\n💡 运行建议:")
        print("   python main.py --mode once    # 运行一次测试")
        print("   python main.py               # 启动完整系统")
    else:
        print("⚠️  部分测试失败，请检查配置和依赖。")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 