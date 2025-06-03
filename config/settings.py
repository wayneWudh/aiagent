"""
系统配置文件
包含数据库连接、API配置、技术指标参数等
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# MongoDB 配置
MONGODB_CONFIG = {
    'host': os.getenv('MONGODB_HOST', 'localhost'),
    'port': int(os.getenv('MONGODB_PORT', 27017)),
    'database': os.getenv('MONGODB_DATABASE', 'crypto_analysis'),
    'collection': os.getenv('MONGODB_COLLECTION', 'klines'),
    'username': os.getenv('MONGODB_USERNAME'),
    'password': os.getenv('MONGODB_PASSWORD'),
}

# CCXT 配置
EXCHANGE_CONFIG = {
    'exchange': 'binance',  # 使用币安交易所
    'sandbox': False,       # 生产环境
    'rateLimit': 1200,     # 请求限制
    'timeout': 30000,      # 超时时间
}

# 交易对配置
SYMBOLS = ['BTC/USDT', 'ETH/USDT']  # 监控的交易对
SYMBOL_MAPPING = {
    'BTC/USDT': 'BTC',
    'ETH/USDT': 'ETH'
}

# 时间周期配置
TIMEFRAMES = ['5m', '15m', '1h', '1d']  # K线周期
HISTORICAL_LIMIT = 60  # 获取历史数据的条数

# 技术指标参数
TECHNICAL_INDICATORS = {
    'MA_PERIODS': [5, 10, 20, 50],
    'RSI_PERIOD': 14,
    'MACD_FAST': 12,
    'MACD_SLOW': 26,
    'MACD_SIGNAL': 9,
    'STOCH_K': 14,
    'STOCH_D': 3,
    'BB_PERIOD': 20,
    'BB_STD': 2,
    'CCI_PERIOD': 20,
    'KDJ_PERIOD': 9,
    'KDJ_SMOOTH': 3,
}

# 信号阈值配置
SIGNAL_THRESHOLDS = {
    'RSI_OVERSOLD': 30,
    'RSI_OVERBOUGHT': 70,
    'STOCH_OVERSOLD': 20,
    'STOCH_OVERBOUGHT': 80,
    'CCI_OVERSOLD': -100,
    'CCI_OVERBOUGHT': 100,
    'KDJ_OVERSOLD': 0,
    'KDJ_OVERBOUGHT': 100,
}

# 日志配置
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'filename': 'logs/crypto_analysis.log',
    'max_bytes': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5,
}

# 调度器配置
SCHEDULER_CONFIG = {
    'timezone': 'Asia/Shanghai',
    'data_collection_interval': 60,  # 每60秒采集一次数据
} 