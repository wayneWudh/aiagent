"""
日志工具模块
配置和管理系统日志
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from config.settings import LOGGING_CONFIG


def setup_logging():
    """设置系统日志配置"""
    
    # 创建logs目录
    log_dir = os.path.dirname(LOGGING_CONFIG['filename'])
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 创建根logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, LOGGING_CONFIG['level']))
    
    # 清除现有的handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 创建formatter
    formatter = logging.Formatter(LOGGING_CONFIG['format'])
    
    # 文件handler
    file_handler = RotatingFileHandler(
        filename=LOGGING_CONFIG['filename'],
        maxBytes=LOGGING_CONFIG['max_bytes'],
        backupCount=LOGGING_CONFIG['backup_count'],
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, LOGGING_CONFIG['level']))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('apscheduler').setLevel(logging.INFO)
    logging.getLogger('pymongo').setLevel(logging.WARNING)
    
    logger.info("日志系统初始化完成")


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的logger
    
    Args:
        name: logger名称
        
    Returns:
        logging.Logger: logger实例
    """
    return logging.getLogger(name) 