"""
CCXT数据采集模块
负责从加密货币交易所获取K线数据，支持增量更新
"""
import logging
import ccxt
from typing import Dict, List, Optional
from datetime import datetime, timezone
import time

from config.settings import EXCHANGE_CONFIG, SYMBOLS, SYMBOL_MAPPING, TIMEFRAMES, HISTORICAL_LIMIT
from database.mongo_client import mongodb_client

logger = logging.getLogger(__name__)


class CCXTDataCollector:
    """CCXT数据采集器"""
    
    def __init__(self):
        """初始化CCXT数据采集器"""
        self.exchange = None
        self.initialize_exchange()
    
    def initialize_exchange(self) -> bool:
        """
        初始化交易所连接
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 获取交易所类
            exchange_class = getattr(ccxt, EXCHANGE_CONFIG['exchange'])
            
            # 创建交易所实例
            self.exchange = exchange_class({
                'rateLimit': EXCHANGE_CONFIG['rateLimit'],
                'timeout': EXCHANGE_CONFIG['timeout'],
                'sandbox': EXCHANGE_CONFIG['sandbox'],
                'enableRateLimit': True,
            })
            
            # 加载市场数据
            self.exchange.load_markets()
            
            logger.info(f"成功初始化交易所: {EXCHANGE_CONFIG['exchange']}")
            return True
            
        except Exception as e:
            logger.error(f"初始化交易所失败: {e}")
            return False
    
    def fetch_klines(self, symbol: str, timeframe: str, limit: int = None) -> Optional[List[List]]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对符号
            timeframe: 时间周期
            limit: 获取数量限制
            
        Returns:
            Optional[List[List]]: K线数据列表
        """
        try:
            if limit is None:
                limit = HISTORICAL_LIMIT
            
            # 获取K线数据
            ohlcv = self.exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                limit=limit
            )
            
            logger.debug(f"成功获取K线数据: {symbol} {timeframe}, 数量: {len(ohlcv)}")
            return ohlcv
            
        except Exception as e:
            logger.error(f"获取K线数据失败 {symbol} {timeframe}: {e}")
            return None
    
    def process_kline_data(self, raw_data: List[List], symbol: str, timeframe: str) -> List[Dict]:
        """
        处理K线数据，转换为标准格式
        
        Args:
            raw_data: 原始K线数据
            symbol: 交易对符号
            timeframe: 时间周期
            
        Returns:
            List[Dict]: 处理后的K线数据
        """
        processed_data = []
        
        try:
            for kline in raw_data:
                timestamp, open_price, high, low, close, volume = kline
                
                # 转换时间戳
                dt = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
                
                # 构建K线数据字典
                kline_dict = {
                    'symbol': SYMBOL_MAPPING.get(symbol, symbol),
                    'timeframe': timeframe,
                    'timestamp': dt,
                    'open': float(open_price),
                    'high': float(high),
                    'low': float(low),
                    'close': float(close),
                    'volume': float(volume),
                    # 技术指标字段初始化为空
                    'ma': {},
                    'rsi': None,
                    'macd': {},
                    'stochastic': {},
                    'bollinger': {},
                    'cci': None,
                    'skdj': {},
                    'kdj': {},
                    'signals': [],
                }
                
                processed_data.append(kline_dict)
            
            logger.debug(f"成功处理K线数据: {symbol} {timeframe}, 数量: {len(processed_data)}")
            return processed_data
            
        except Exception as e:
            logger.error(f"处理K线数据失败 {symbol} {timeframe}: {e}")
            return []
    
    def get_latest_timestamp(self, symbol: str, timeframe: str) -> Optional[datetime]:
        """
        获取数据库中最新的K线时间戳
        
        Args:
            symbol: 币种符号
            timeframe: 时间周期
            
        Returns:
            Optional[datetime]: 最新时间戳
        """
        try:
            latest_kline = mongodb_client.get_latest_kline(symbol, timeframe)
            if latest_kline:
                return latest_kline.get('timestamp')
            return None
        except Exception as e:
            logger.error(f"获取最新时间戳失败 {symbol} {timeframe}: {e}")
            return None
    
    def is_kline_exists(self, symbol: str, timeframe: str, timestamp: datetime) -> bool:
        """
        检查K线是否已存在
        
        Args:
            symbol: 币种符号
            timeframe: 时间周期 
            timestamp: 时间戳
            
        Returns:
            bool: 是否存在
        """
        try:
            return mongodb_client.kline_exists(symbol, timeframe, timestamp)
        except Exception as e:
            logger.error(f"检查K线存在性失败 {symbol} {timeframe}: {e}")
            return False
    
    def collect_and_store_data(self) -> bool:
        """
        采集并存储所有配置的交易对和时间周期的数据（初始化用）
        
        Returns:
            bool: 采集是否成功
        """
        success_count = 0
        total_count = len(SYMBOLS) * len(TIMEFRAMES)
        
        logger.info("开始采集加密货币K线数据...")
        
        for symbol in SYMBOLS:
            for timeframe in TIMEFRAMES:
                try:
                    # 获取K线数据
                    raw_data = self.fetch_klines(symbol, timeframe)
                    
                    if raw_data:
                        # 处理数据
                        processed_data = self.process_kline_data(raw_data, symbol, timeframe)
                        
                        if processed_data:
                            # 存储到数据库
                            for kline in processed_data:
                                # 检查是否已存在，避免重复插入
                                if not self.is_kline_exists(kline['symbol'], kline['timeframe'], kline['timestamp']):
                                    if mongodb_client.insert_kline(kline):
                                        success_count += 1
                                else:
                                    logger.debug(f"K线已存在，跳过: {kline['symbol']} {kline['timeframe']} {kline['timestamp']}")
                    
                    # 添加延迟以避免触发API限制
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"采集数据失败 {symbol} {timeframe}: {e}")
                    continue
        
        logger.info(f"数据采集完成，成功: {success_count}/{total_count}")
        return success_count > 0
    
    def collect_latest_data(self) -> bool:
        """
        采集最新的K线数据（用于定时更新，每分钟调用）
        只获取和存储新的数据，避免重复
        
        Returns:
            bool: 采集是否成功
        """
        success_count = 0
        new_data_count = 0
        total_count = len(SYMBOLS) * len(TIMEFRAMES)
        
        logger.info("采集最新K线数据...")
        
        for symbol in SYMBOLS:
            for timeframe in TIMEFRAMES:
                try:
                    # 获取最新的5根K线（确保能捕获最新数据）
                    raw_data = self.fetch_klines(symbol, timeframe, limit=5)
                    
                    if raw_data:
                        # 处理数据
                        processed_data = self.process_kline_data(raw_data, symbol, timeframe)
                        
                        if processed_data:
                            # 只存储不存在的K线数据
                            for kline in processed_data:
                                if not self.is_kline_exists(kline['symbol'], kline['timeframe'], kline['timestamp']):
                                    if mongodb_client.insert_kline(kline):
                                        success_count += 1
                                        new_data_count += 1
                                        logger.info(f"新增K线数据: {kline['symbol']} {kline['timeframe']} {kline['timestamp']}")
                                        
                                        # 新增数据后，触发技术指标和信号计算
                                        self._trigger_indicators_calculation(kline['symbol'], kline['timeframe'])
                    
                    # 添加延迟以避免触发API限制
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"采集最新数据失败 {symbol} {timeframe}: {e}")
                    continue
        
        logger.info(f"最新数据采集完成，新增: {new_data_count}, 成功: {success_count}/{total_count}")
        return success_count > 0
    
    def _trigger_indicators_calculation(self, symbol: str, timeframe: str):
        """
        触发技术指标和信号计算
        
        Args:
            symbol: 币种符号
            timeframe: 时间周期
        """
        try:
            # 导入技术指标计算模块（避免循环导入）
            from indicators.calculator import indicator_calculator
            from indicators.signals import signal_detector
            
            # 计算技术指标
            indicator_calculator.calculate_indicators_for_symbol_timeframe(symbol, timeframe)
            logger.debug(f"技术指标计算完成: {symbol} {timeframe}")
            
            # 检测交易信号
            signal_detector.detect_signals_for_symbol_timeframe(symbol, timeframe) 
            logger.debug(f"交易信号检测完成: {symbol} {timeframe}")
            
        except Exception as e:
            logger.error(f"触发技术指标计算失败 {symbol} {timeframe}: {e}")
    
    def get_market_info(self) -> Dict:
        """
        获取市场信息
        
        Returns:
            Dict: 市场信息
        """
        try:
            market_info = {}
            
            for symbol in SYMBOLS:
                ticker = self.exchange.fetch_ticker(symbol)
                market_info[symbol] = {
                    'last_price': ticker['last'],
                    '24h_change': ticker['percentage'],
                    '24h_volume': ticker['quoteVolume'],
                    'bid': ticker['bid'],
                    'ask': ticker['ask'],
                }
            
            logger.debug(f"获取市场信息成功: {list(market_info.keys())}")
            return market_info
            
        except Exception as e:
            logger.error(f"获取市场信息失败: {e}")
            return {}
    
    def fetch_ohlcv_data(self, symbol: str, timeframe: str, limit: int = None) -> Optional[List[List]]:
        """
        获取OHLCV数据（fetch_klines的别名方法）
        
        Args:
            symbol: 交易对符号
            timeframe: 时间周期
            limit: 获取数量限制
            
        Returns:
            Optional[List[List]]: K线数据列表
        """
        return self.fetch_klines(symbol, timeframe, limit)


# 全局数据采集器实例
data_collector = CCXTDataCollector() 