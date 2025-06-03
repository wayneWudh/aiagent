"""
技术指标计算模块
实现各种技术指标的计算功能
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import talib

from config.settings import TECHNICAL_INDICATORS
from database.mongo_client import mongodb_client

logger = logging.getLogger(__name__)


class TechnicalIndicatorCalculator:
    """技术指标计算器"""
    
    def __init__(self):
        """初始化技术指标计算器"""
        self.config = TECHNICAL_INDICATORS
    
    def prepare_data(self, historical_data: List[Dict]) -> Optional[pd.DataFrame]:
        """
        准备计算所需的数据
        
        Args:
            historical_data: 历史K线数据
            
        Returns:
            Optional[pd.DataFrame]: 处理后的DataFrame
        """
        try:
            if not historical_data:
                logger.warning("历史数据为空，无法计算技术指标")
                return None
            
            # 转换为DataFrame
            df = pd.DataFrame(historical_data)
            
            # 确保必要的列存在
            required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in df.columns:
                    logger.error(f"缺少必要的数据列: {col}")
                    return None
            
            # 设置时间戳为索引
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # 确保数据按时间排序
            df.sort_index(inplace=True)
            
            logger.debug(f"成功准备数据，数据量: {len(df)}")
            return df
            
        except Exception as e:
            logger.error(f"数据准备失败: {e}")
            return None
    
    def calculate_moving_averages(self, df: pd.DataFrame) -> Dict:
        """
        计算移动平均线
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            Dict: 移动平均线数据
        """
        try:
            ma_data = {}
            
            for period in self.config['MA_PERIODS']:
                ma_values = talib.SMA(df['close'].values, timeperiod=period)
                ma_data[f'ma{period}'] = float(ma_values[-1]) if not np.isnan(ma_values[-1]) else None
            
            logger.debug(f"计算移动平均线完成: {list(ma_data.keys())}")
            return ma_data
            
        except Exception as e:
            logger.error(f"计算移动平均线失败: {e}")
            return {}
    
    def calculate_rsi(self, df: pd.DataFrame) -> Optional[float]:
        """
        计算相对强弱指数(RSI)
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            Optional[float]: RSI值
        """
        try:
            rsi_values = talib.RSI(df['close'].values, timeperiod=self.config['RSI_PERIOD'])
            rsi = float(rsi_values[-1]) if not np.isnan(rsi_values[-1]) else None
            
            logger.debug(f"计算RSI完成: {rsi}")
            return rsi
            
        except Exception as e:
            logger.error(f"计算RSI失败: {e}")
            return None
    
    def calculate_macd(self, df: pd.DataFrame) -> Dict:
        """
        计算MACD指标
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            Dict: MACD数据
        """
        try:
            macd, signal, histogram = talib.MACD(
                df['close'].values,
                fastperiod=self.config['MACD_FAST'],
                slowperiod=self.config['MACD_SLOW'],
                signalperiod=self.config['MACD_SIGNAL']
            )
            
            macd_data = {
                'macd': float(macd[-1]) if not np.isnan(macd[-1]) else None,
                'signal': float(signal[-1]) if not np.isnan(signal[-1]) else None,
                'histogram': float(histogram[-1]) if not np.isnan(histogram[-1]) else None,
            }
            
            logger.debug(f"计算MACD完成: {macd_data}")
            return macd_data
            
        except Exception as e:
            logger.error(f"计算MACD失败: {e}")
            return {}
    
    def calculate_stochastic(self, df: pd.DataFrame) -> Dict:
        """
        计算随机振荡器
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            Dict: 随机振荡器数据
        """
        try:
            slowk, slowd = talib.STOCH(
                df['high'].values,
                df['low'].values,
                df['close'].values,
                fastk_period=self.config['STOCH_K'],
                slowk_period=self.config['STOCH_D'],
                slowd_period=self.config['STOCH_D']
            )
            
            stoch_data = {
                'k': float(slowk[-1]) if not np.isnan(slowk[-1]) else None,
                'd': float(slowd[-1]) if not np.isnan(slowd[-1]) else None,
            }
            
            logger.debug(f"计算随机振荡器完成: {stoch_data}")
            return stoch_data
            
        except Exception as e:
            logger.error(f"计算随机振荡器失败: {e}")
            return {}
    
    def calculate_bollinger_bands(self, df: pd.DataFrame) -> Dict:
        """
        计算布林带
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            Dict: 布林带数据
        """
        try:
            upper, middle, lower = talib.BBANDS(
                df['close'].values,
                timeperiod=self.config['BB_PERIOD'],
                nbdevup=self.config['BB_STD'],
                nbdevdn=self.config['BB_STD']
            )
            
            bb_data = {
                'upper': float(upper[-1]) if not np.isnan(upper[-1]) else None,
                'middle': float(middle[-1]) if not np.isnan(middle[-1]) else None,
                'lower': float(lower[-1]) if not np.isnan(lower[-1]) else None,
            }
            
            logger.debug(f"计算布林带完成: {bb_data}")
            return bb_data
            
        except Exception as e:
            logger.error(f"计算布林带失败: {e}")
            return {}
    
    def calculate_cci(self, df: pd.DataFrame) -> Optional[float]:
        """
        计算商品通道指数(CCI)
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            Optional[float]: CCI值
        """
        try:
            cci_values = talib.CCI(
                df['high'].values,
                df['low'].values,
                df['close'].values,
                timeperiod=self.config['CCI_PERIOD']
            )
            
            cci = float(cci_values[-1]) if not np.isnan(cci_values[-1]) else None
            
            logger.debug(f"计算CCI完成: {cci}")
            return cci
            
        except Exception as e:
            logger.error(f"计算CCI失败: {e}")
            return None
    
    def calculate_kdj(self, df: pd.DataFrame) -> Dict:
        """
        计算KDJ指标
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            Dict: KDJ数据
        """
        try:
            # 计算RSV
            low_min = df['low'].rolling(window=self.config['KDJ_PERIOD']).min()
            high_max = df['high'].rolling(window=self.config['KDJ_PERIOD']).max()
            rsv = (df['close'] - low_min) / (high_max - low_min) * 100
            
            # 计算K值
            k_values = []
            k = 50  # 初始值
            for rsv_val in rsv:
                if not np.isnan(rsv_val):
                    k = (2/3) * k + (1/3) * rsv_val
                k_values.append(k)
            
            # 计算D值
            d_values = []
            d = 50  # 初始值
            for k_val in k_values:
                d = (2/3) * d + (1/3) * k_val
                d_values.append(d)
            
            # 计算J值
            j_values = [3 * k_val - 2 * d_val for k_val, d_val in zip(k_values, d_values)]
            
            kdj_data = {
                'k': float(k_values[-1]) if k_values else None,
                'd': float(d_values[-1]) if d_values else None,
                'j': float(j_values[-1]) if j_values else None,
            }
            
            logger.debug(f"计算KDJ完成: {kdj_data}")
            return kdj_data
            
        except Exception as e:
            logger.error(f"计算KDJ失败: {e}")
            return {}
    
    def calculate_skdj(self, df: pd.DataFrame) -> Dict:
        """
        计算慢速KD指标
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            Dict: 慢速KD数据
        """
        try:
            # 使用TA-Lib的慢速随机振荡器
            slowk, slowd = talib.STOCH(
                df['high'].values,
                df['low'].values,
                df['close'].values,
                fastk_period=self.config['KDJ_PERIOD'],
                slowk_period=self.config['KDJ_SMOOTH'],
                slowd_period=self.config['KDJ_SMOOTH']
            )
            
            skdj_data = {
                'k': float(slowk[-1]) if not np.isnan(slowk[-1]) else None,
                'd': float(slowd[-1]) if not np.isnan(slowd[-1]) else None,
            }
            
            logger.debug(f"计算慢速KD完成: {skdj_data}")
            return skdj_data
            
        except Exception as e:
            logger.error(f"计算慢速KD失败: {e}")
            return {}
    
    def calculate_all_indicators(self, symbol: str, timeframe: str) -> bool:
        """
        计算指定交易对和时间周期的所有技术指标
        
        Args:
            symbol: 币种符号
            timeframe: 时间周期
            
        Returns:
            bool: 计算是否成功
        """
        try:
            # 获取历史数据
            historical_data = mongodb_client.get_historical_data(symbol, timeframe)
            
            if not historical_data:
                logger.warning(f"无历史数据用于计算技术指标: {symbol} {timeframe}")
                return False
            
            # 准备数据
            df = self.prepare_data(historical_data)
            if df is None:
                return False
            
            # 需要足够的数据来计算技术指标
            if len(df) < 50:
                logger.warning(f"数据量不足，无法计算技术指标: {symbol} {timeframe}, 数据量: {len(df)}")
                return False
            
            # 计算各项技术指标
            indicators = {}
            
            # 移动平均线
            indicators['ma'] = self.calculate_moving_averages(df)
            
            # RSI
            indicators['rsi'] = self.calculate_rsi(df)
            
            # MACD
            indicators['macd'] = self.calculate_macd(df)
            
            # 随机振荡器
            indicators['stochastic'] = self.calculate_stochastic(df)
            
            # 布林带
            indicators['bollinger'] = self.calculate_bollinger_bands(df)
            
            # CCI
            indicators['cci'] = self.calculate_cci(df)
            
            # KDJ
            indicators['kdj'] = self.calculate_kdj(df)
            
            # 慢速KD
            indicators['skdj'] = self.calculate_skdj(df)
            
            # 更新数据库中最新的K线数据
            latest_timestamp = df.index[-1].to_pydatetime()
            success = mongodb_client.update_technical_indicators(
                symbol, timeframe, latest_timestamp, indicators
            )
            
            if success:
                logger.info(f"成功计算并更新技术指标: {symbol} {timeframe}")
            else:
                logger.error(f"更新技术指标失败: {symbol} {timeframe}")
            
            return success
            
        except Exception as e:
            logger.error(f"计算技术指标失败 {symbol} {timeframe}: {e}")
            return False
    
    def batch_calculate_indicators(self) -> bool:
        """
        批量计算所有交易对和时间周期的技术指标
        
        Returns:
            bool: 批量计算是否成功
        """
        from config.settings import SYMBOLS, TIMEFRAMES, SYMBOL_MAPPING
        
        success_count = 0
        total_count = len(SYMBOLS) * len(TIMEFRAMES)
        
        logger.info("开始批量计算技术指标...")
        
        for symbol_pair in SYMBOLS:
            symbol = SYMBOL_MAPPING.get(symbol_pair, symbol_pair)
            for timeframe in TIMEFRAMES:
                if self.calculate_all_indicators(symbol, timeframe):
                    success_count += 1
        
        logger.info(f"技术指标计算完成，成功: {success_count}/{total_count}")
        return success_count > 0
    
    def calculate_indicators_for_symbol_timeframe(self, symbol: str, timeframe: str) -> bool:
        """
        为特定币种和时间周期计算技术指标（用于新数据触发的实时计算）
        
        Args:
            symbol: 币种符号
            timeframe: 时间周期
            
        Returns:
            bool: 计算是否成功
        """
        try:
            logger.debug(f"开始计算技术指标: {symbol} {timeframe}")
            return self.calculate_all_indicators(symbol, timeframe)
        except Exception as e:
            logger.error(f"计算技术指标失败 {symbol} {timeframe}: {e}")
            return False


# 全局技术指标计算器实例
indicator_calculator = TechnicalIndicatorCalculator() 