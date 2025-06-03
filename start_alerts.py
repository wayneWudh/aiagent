#!/usr/bin/env python3
"""
预警服务启动脚本
"""
import asyncio
import logging
import signal
import sys
from alerts.alert_manager import AlertManager
from config.settings import ALERT_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertService:
    def __init__(self):
        self.alert_manager = AlertManager()
        self.running = False
    
    async def start(self):
        """启动预警服务"""
        self.running = True
        logger.info("预警服务启动中...")
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # 启动预警监控
        await self.alert_manager.start_monitoring()
        
        # 主循环
        while self.running:
            try:
                await asyncio.sleep(ALERT_CONFIG['check_interval'])
            except asyncio.CancelledError:
                break
    
    def signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"收到信号 {signum}，正在关闭...")
        self.running = False

async def main():
    service = AlertService()
    await service.start()

if __name__ == "__main__":
    asyncio.run(main())
