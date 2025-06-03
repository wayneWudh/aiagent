"""
初始化历史数据脚本
用于一次性采集足够的历史数据来计算技术指标
"""
import logging
from data_collector.ccxt_collector import data_collector
from indicators.calculator import indicator_calculator
from indicators.signals import signal_detector
from utils.logger import setup_logging

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 开始初始化历史数据...")
    print("=" * 60)
    
    try:
        # 1. 采集历史数据
        print("\n📈 1. 采集历史K线数据...")
        success = data_collector.collect_and_store_data()
        
        if not success:
            print("❌ 历史数据采集失败")
            return
            
        print("✅ 历史数据采集完成")
        
        # 2. 计算技术指标
        print("\n📊 2. 计算技术指标...")
        indicator_calculator.batch_calculate_indicators()
        print("✅ 技术指标计算完成")
        
        # 3. 检测技术信号
        print("\n🔍 3. 检测技术信号...")
        signal_detector.batch_detect_signals()
        print("✅ 技术信号检测完成")
        
        print("\n🎉 历史数据初始化完成！")
        print("现在可以启动主系统: python main.py")
        
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        print(f"❌ 初始化失败: {e}")

if __name__ == "__main__":
    main() 