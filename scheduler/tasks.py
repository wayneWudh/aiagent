"""
定时任务管理模块
负责调度数据采集、技术指标计算和信号检测等任务
"""
import logging
from typing import Optional
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import pytz

from config.settings import SCHEDULER_CONFIG
from data_collector.ccxt_collector import data_collector
from indicators.calculator import indicator_calculator
from indicators.signals import signal_detector

logger = logging.getLogger(__name__)


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self, background_mode: bool = True):
        """
        初始化任务调度器
        
        Args:
            background_mode: 是否使用后台模式
        """
        self.timezone = pytz.timezone(SCHEDULER_CONFIG['timezone'])
        
        # 选择调度器类型
        if background_mode:
            self.scheduler = BackgroundScheduler(timezone=self.timezone)
        else:
            self.scheduler = BlockingScheduler(timezone=self.timezone)
        
        self.is_running = False
        self._setup_jobs()
    
    def _setup_jobs(self):
        """设置定时任务"""
        try:
            # 1. 数据采集任务 - 每分钟执行
            self.scheduler.add_job(
                func=self.data_collection_task,
                trigger=IntervalTrigger(seconds=SCHEDULER_CONFIG['data_collection_interval']),
                id='data_collection',
                name='数据采集任务',
                replace_existing=True,
                max_instances=1,
                misfire_grace_time=30
            )
            
            # 2. 技术指标计算任务 - 每分钟执行（在数据采集后）
            self.scheduler.add_job(
                func=self.indicator_calculation_task,
                trigger=IntervalTrigger(seconds=SCHEDULER_CONFIG['data_collection_interval']),
                id='indicator_calculation',
                name='技术指标计算任务',
                replace_existing=True,
                max_instances=1,
                misfire_grace_time=30
            )
            
            # 3. 技术信号检测任务 - 每分钟执行（在指标计算后）
            self.scheduler.add_job(
                func=self.signal_detection_task,
                trigger=IntervalTrigger(seconds=SCHEDULER_CONFIG['data_collection_interval']),
                id='signal_detection',
                name='技术信号检测任务',
                replace_existing=True,
                max_instances=1,
                misfire_grace_time=30
            )
            
            # 4. 系统状态监控任务 - 每5分钟执行
            self.scheduler.add_job(
                func=self.system_monitor_task,
                trigger=IntervalTrigger(minutes=5),
                id='system_monitor',
                name='系统状态监控任务',
                replace_existing=True,
                max_instances=1
            )
            
            # 5. 数据清理任务 - 每天凌晨3点执行
            self.scheduler.add_job(
                func=self.data_cleanup_task,
                trigger=CronTrigger(hour=3, minute=0),
                id='data_cleanup',
                name='数据清理任务',
                replace_existing=True,
                max_instances=1
            )
            
            logger.info("定时任务设置完成")
            
        except Exception as e:
            logger.error(f"设置定时任务失败: {e}")
    
    def data_collection_task(self):
        """
        数据采集任务
        采集最新的K线数据
        """
        try:
            logger.info("开始执行数据采集任务...")
            
            # 采集最新数据
            success = data_collector.collect_latest_data()
            
            if success:
                logger.info("数据采集任务执行成功")
            else:
                logger.warning("数据采集任务执行失败")
                
        except Exception as e:
            logger.error(f"数据采集任务异常: {e}")
    
    def indicator_calculation_task(self):
        """
        技术指标计算任务
        计算所有技术指标
        """
        try:
            logger.info("开始执行技术指标计算任务...")
            
            # 批量计算技术指标
            success = indicator_calculator.batch_calculate_indicators()
            
            if success:
                logger.info("技术指标计算任务执行成功")
            else:
                logger.warning("技术指标计算任务执行失败")
                
        except Exception as e:
            logger.error(f"技术指标计算任务异常: {e}")
    
    def signal_detection_task(self):
        """
        技术信号检测任务
        检测所有技术信号
        """
        try:
            logger.info("开始执行技术信号检测任务...")
            
            # 批量检测技术信号
            success = signal_detector.batch_detect_signals()
            
            if success:
                logger.info("技术信号检测任务执行成功")
            else:
                logger.warning("技术信号检测任务执行失败")
                
        except Exception as e:
            logger.error(f"技术信号检测任务异常: {e}")
    
    def system_monitor_task(self):
        """
        系统状态监控任务
        监控系统运行状态
        """
        try:
            logger.info("开始执行系统状态监控任务...")
            
            # 检查数据库连接
            from database.mongo_client import mongodb_client
            if not mongodb_client.client:
                logger.warning("数据库连接异常，尝试重新连接...")
                mongodb_client.connect()
            
            # 检查交易所连接
            if not data_collector.exchange:
                logger.warning("交易所连接异常，尝试重新连接...")
                data_collector.initialize_exchange()
            
            # 获取市场信息
            market_info = data_collector.get_market_info()
            if market_info:
                logger.info(f"市场状态正常，监控的交易对: {list(market_info.keys())}")
            else:
                logger.warning("获取市场信息失败")
            
            logger.info("系统状态监控任务执行完成")
            
        except Exception as e:
            logger.error(f"系统状态监控任务异常: {e}")
    
    def data_cleanup_task(self):
        """
        数据清理任务
        清理过期或冗余数据
        """
        try:
            logger.info("开始执行数据清理任务...")
            
            from datetime import datetime, timedelta
            from database.mongo_client import mongodb_client
            
            # 清理30天前的分钟级数据（保留小时级以上）
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            # 删除过期的5分钟和15分钟数据
            for timeframe in ['5m', '15m']:
                delete_query = {
                    'timeframe': timeframe,
                    'timestamp': {'$lt': cutoff_date}
                }
                
                result = mongodb_client.collection.delete_many(delete_query)
                logger.info(f"清理过期数据 {timeframe}: 删除 {result.deleted_count} 条记录")
            
            logger.info("数据清理任务执行完成")
            
        except Exception as e:
            logger.error(f"数据清理任务异常: {e}")
    
    def start(self):
        """启动调度器"""
        try:
            if not self.is_running:
                self.scheduler.start()
                self.is_running = True
                logger.info("任务调度器已启动")
            else:
                logger.warning("任务调度器已经在运行中")
                
        except Exception as e:
            logger.error(f"启动任务调度器失败: {e}")
    
    def stop(self):
        """停止调度器"""
        try:
            if self.is_running:
                self.scheduler.shutdown(wait=True)
                self.is_running = False
                logger.info("任务调度器已停止")
            else:
                logger.warning("任务调度器未在运行")
                
        except Exception as e:
            logger.error(f"停止任务调度器失败: {e}")
    
    def pause_job(self, job_id: str):
        """
        暂停指定任务
        
        Args:
            job_id: 任务ID
        """
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"任务已暂停: {job_id}")
            
        except Exception as e:
            logger.error(f"暂停任务失败 {job_id}: {e}")
    
    def resume_job(self, job_id: str):
        """
        恢复指定任务
        
        Args:
            job_id: 任务ID
        """
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"任务已恢复: {job_id}")
            
        except Exception as e:
            logger.error(f"恢复任务失败 {job_id}: {e}")
    
    def get_job_status(self) -> dict:
        """
        获取所有任务状态
        
        Returns:
            dict: 任务状态信息
        """
        try:
            jobs_info = {}
            
            for job in self.scheduler.get_jobs():
                jobs_info[job.id] = {
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger),
                    'pending': job.pending
                }
            
            return jobs_info
            
        except Exception as e:
            logger.error(f"获取任务状态失败: {e}")
            return {}
    
    def run_job_now(self, job_id: str):
        """
        立即执行指定任务
        
        Args:
            job_id: 任务ID
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.func()
                logger.info(f"手动执行任务完成: {job_id}")
            else:
                logger.warning(f"任务不存在: {job_id}")
                
        except Exception as e:
            logger.error(f"手动执行任务失败 {job_id}: {e}")


# 全局任务调度器实例
task_scheduler = TaskScheduler(background_mode=True) 