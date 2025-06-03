"""
加密货币K线数据采集与技术分析系统
主程序入口

功能：
1. 每分钟从CCXT获取BTC和ETH的K线数据
2. 支持4种时间周期：5分钟、15分钟、1小时、1天
3. 计算8种主要技术指标
4. 识别30+种技术交易信号
5. 使用MongoDB存储所有数据

"""
import signal
import sys
import time
import argparse
from typing import Optional

# 导入模块
from utils.logger import setup_logging, get_logger
from config.settings import SYMBOLS, TIMEFRAMES
from database.mongo_client import mongodb_client
from data_collector.ccxt_collector import data_collector
from indicators.calculator import indicator_calculator
from indicators.signals import signal_detector
from scheduler.tasks import task_scheduler

# 设置日志
setup_logging()
logger = get_logger(__name__)


class CryptoAnalysisSystem:
    """加密货币分析系统主类"""
    
    def __init__(self):
        """初始化系统"""
        self.is_running = False
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """设置信号处理器"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """信号处理函数"""
        logger.info(f"接收到信号 {signum}，正在优雅关闭系统...")
        self.stop()
        sys.exit(0)
    
    def check_dependencies(self) -> bool:
        """检查系统依赖"""
        logger.info("检查系统依赖...")
        
        try:
            # 检查数据库连接
            if not mongodb_client.client:
                logger.error("MongoDB连接失败")
                return False
            
            # 检查交易所连接
            if not data_collector.exchange:
                logger.error("交易所连接失败")
                return False
            
            logger.info("系统依赖检查通过")
            return True
            
        except Exception as e:
            logger.error(f"依赖检查失败: {e}")
            return False
    
    def initialize_data(self) -> bool:
        """初始化历史数据"""
        logger.info("开始初始化历史数据...")
        
        try:
            # 采集初始历史数据
            success = data_collector.collect_and_store_data()
            
            if not success:
                logger.warning("初始数据采集部分失败，但系统将继续运行")
            
            # 计算技术指标
            logger.info("计算初始技术指标...")
            indicator_calculator.batch_calculate_indicators()
            
            # 检测技术信号
            logger.info("检测初始技术信号...")
            signal_detector.batch_detect_signals()
            
            logger.info("历史数据初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"初始化历史数据失败: {e}")
            return False
    
    def start(self, skip_init: bool = False):
        """启动系统"""
        logger.info("=" * 60)
        logger.info("启动加密货币K线数据采集与技术分析系统")
        logger.info("=" * 60)
        
        try:
            # 检查依赖
            if not self.check_dependencies():
                logger.error("系统依赖检查失败，无法启动")
                return False
            
            # 初始化数据（如果需要）
            if not skip_init:
                if not self.initialize_data():
                    logger.error("初始化数据失败，无法启动")
                    return False
            
            # 启动定时任务调度器
            logger.info("启动定时任务调度器...")
            task_scheduler.start()
            
            self.is_running = True
            logger.info("系统启动成功！")
            logger.info(f"监控币种: {SYMBOLS}")
            logger.info(f"时间周期: {TIMEFRAMES}")
            logger.info("系统正在运行，按 Ctrl+C 停止...")
            
            return True
            
        except Exception as e:
            logger.error(f"系统启动失败: {e}")
            return False
    
    def stop(self):
        """停止系统"""
        if self.is_running:
            logger.info("正在停止系统...")
            
            # 停止调度器
            task_scheduler.stop()
            
            # 关闭数据库连接
            mongodb_client.close()
            
            self.is_running = False
            logger.info("系统已停止")
        else:
            logger.info("系统未在运行")
    
    def run_once(self):
        """运行一次完整的数据采集和分析流程"""
        logger.info("执行一次完整的数据采集和分析流程...")
        
        try:
            # 数据采集
            logger.info("1. 数据采集...")
            data_collector.collect_latest_data()
            
            # 技术指标计算
            logger.info("2. 技术指标计算...")
            indicator_calculator.batch_calculate_indicators()
            
            # 技术信号检测
            logger.info("3. 技术信号检测...")
            signal_detector.batch_detect_signals()
            
            logger.info("完整流程执行完成")
            
        except Exception as e:
            logger.error(f"执行流程失败: {e}")
    
    def status(self):
        """显示系统状态"""
        logger.info("=" * 60)
        logger.info("系统状态信息")
        logger.info("=" * 60)
        
        # 显示基本信息
        logger.info(f"系统运行状态: {'运行中' if self.is_running else '已停止'}")
        logger.info(f"监控币种: {SYMBOLS}")
        logger.info(f"时间周期: {TIMEFRAMES}")
        
        # 显示任务状态
        if self.is_running:
            jobs_status = task_scheduler.get_job_status()
            logger.info("\n定时任务状态:")
            for job_id, job_info in jobs_status.items():
                logger.info(f"  {job_info['name']}: 下次运行 {job_info['next_run_time']}")
        
        # 显示数据库统计
        try:
            from config.settings import SYMBOL_MAPPING
            logger.info("\n数据库统计:")
            for symbol_pair in SYMBOLS:
                symbol = SYMBOL_MAPPING.get(symbol_pair, symbol_pair)
                for timeframe in TIMEFRAMES:
                    count = mongodb_client.collection.count_documents({
                        'symbol': symbol,
                        'timeframe': timeframe
                    })
                    logger.info(f"  {symbol} {timeframe}: {count} 条记录")
        
        except Exception as e:
            logger.error(f"获取数据库统计失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='加密货币K线数据采集与技术分析系统')
    parser.add_argument('--mode', choices=['start', 'once', 'status'], default='start',
                       help='运行模式: start(持续运行), once(运行一次), status(显示状态)')
    parser.add_argument('--skip-init', action='store_true',
                       help='跳过初始化数据采集')
    parser.add_argument('--job', choices=['data', 'indicators', 'signals'],
                       help='手动执行指定任务')
    
    args = parser.parse_args()
    
    # 创建系统实例
    system = CryptoAnalysisSystem()
    
    try:
        if args.mode == 'start':
            # 持续运行模式
            if system.start(skip_init=args.skip_init):
                # 保持程序运行
                try:
                    while system.is_running:
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
            
        elif args.mode == 'once':
            # 运行一次模式
            if system.check_dependencies():
                system.run_once()
            
        elif args.mode == 'status':
            # 状态显示模式
            system.status()
        
        elif args.job:
            # 手动执行任务
            if system.check_dependencies():
                if args.job == 'data':
                    task_scheduler.run_job_now('data_collection')
                elif args.job == 'indicators':
                    task_scheduler.run_job_now('indicator_calculation')
                elif args.job == 'signals':
                    task_scheduler.run_job_now('signal_detection')
    
    except Exception as e:
        logger.error(f"程序执行异常: {e}")
        system.stop()
        sys.exit(1)
    
    finally:
        system.stop()


if __name__ == "__main__":
    main() 