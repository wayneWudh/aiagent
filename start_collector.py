#!/usr/bin/env python3
"""
数据采集服务启动脚本
"""
import logging
import time
import signal
import sys
from threading import Thread
from data_collector.ccxt_collector import data_collector
from indicators.calculator import indicator_calculator
from indicators.signals import signal_detector

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataCollectionService:
    def __init__(self):
        self.running = False
        
    def start(self):
        """启动数据采集服务"""
        self.running = True
        logger.info("数据采集服务启动中...")
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # 主循环
        while self.running:
            try:
                logger.info("开始数据采集...")
                
                # 采集最新数据
                success = data_collector.collect_latest_data()
                if success:
                    logger.info("数据采集成功")
                    
                    # 计算技术指标
                    indicator_calculator.calculate_all_indicators()
                    logger.info("技术指标计算完成")
                    
                    # 检测交易信号
                    signal_detector.detect_all_signals()
                    logger.info("交易信号检测完成")
                    
                else:
                    logger.warning("数据采集失败")
                
                # 等待下次采集
                time.sleep(300)  # 5分钟
                
            except Exception as e:
                logger.error(f"数据采集过程中出错: {e}")
                time.sleep(60)  # 出错后等待1分钟
    
    def signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"收到信号 {signum}，正在关闭...")
        self.running = False
        sys.exit(0)

if __name__ == "__main__":
    service = DataCollectionService()
    service.start()
