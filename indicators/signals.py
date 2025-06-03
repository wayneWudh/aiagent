"""
技术信号识别模块
实现各种技术信号的识别功能
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional

from config.settings import SIGNAL_THRESHOLDS, SYMBOLS, TIMEFRAMES, SYMBOL_MAPPING
from database.mongo_client import mongodb_client

logger = logging.getLogger(__name__)


class TechnicalSignalDetector:
    """技术信号检测器"""
    
    def __init__(self):
        """初始化技术信号检测器"""
        self.thresholds = SIGNAL_THRESHOLDS
    
    def prepare_signal_data(self, historical_data: List[Dict]) -> Optional[pd.DataFrame]:
        """
        准备信号检测所需的数据
        
        Args:
            historical_data: 历史K线数据
            
        Returns:
            Optional[pd.DataFrame]: 处理后的DataFrame
        """
        try:
            if not historical_data or len(historical_data) < 2:
                logger.warning("历史数据不足，无法进行信号检测")
                return None
            
            # 转换为DataFrame
            df = pd.DataFrame(historical_data)
            
            # 设置时间戳为索引
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # 确保数据按时间排序
            df.sort_index(inplace=True)
            
            logger.debug(f"成功准备信号检测数据，数据量: {len(df)}")
            return df
            
        except Exception as e:
            logger.error(f"信号数据准备失败: {e}")
            return None
    
    def detect_rsi_signals(self, df: pd.DataFrame) -> List[str]:
        """
        检测RSI相关信号
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            List[str]: RSI信号列表
        """
        signals = []
        
        try:
            if len(df) < 2:
                return signals
            
            current_rsi = df.iloc[-1].get('rsi')
            prev_rsi = df.iloc[-2].get('rsi') if len(df) > 1 else None
            
            if current_rsi is None:
                return signals
            
            # RSI超卖和超买
            if current_rsi < self.thresholds['RSI_OVERSOLD']:
                signals.append('RSI_OVERSOLD')
            elif current_rsi > self.thresholds['RSI_OVERBOUGHT']:
                signals.append('RSI_OVERBOUGHT')
            
            # RSI背离信号（需要更多历史数据）
            if len(df) >= 10 and prev_rsi is not None:
                recent_prices = df['close'].tail(5).values
                recent_rsi = [df.iloc[i].get('rsi') for i in range(-5, 0)]
                recent_rsi = [rsi for rsi in recent_rsi if rsi is not None]
                
                if len(recent_rsi) >= 3:
                    # 价格新低但RSI未创新低（看涨背离）
                    if (recent_prices[-1] < min(recent_prices[:-1]) and 
                        recent_rsi[-1] > min(recent_rsi[:-1])):
                        signals.append('RSI_DIVERGENCE_BULLISH')
                    
                    # 价格新高但RSI未创新高（看跌背离）
                    if (recent_prices[-1] > max(recent_prices[:-1]) and 
                        recent_rsi[-1] < max(recent_rsi[:-1])):
                        signals.append('RSI_DIVERGENCE_BEARISH')
            
            logger.debug(f"检测到RSI信号: {signals}")
            return signals
            
        except Exception as e:
            logger.error(f"RSI信号检测失败: {e}")
            return []
    
    def detect_macd_signals(self, df: pd.DataFrame) -> List[str]:
        """
        检测MACD相关信号
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            List[str]: MACD信号列表
        """
        signals = []
        
        try:
            if len(df) < 2:
                return signals
            
            current_macd = df.iloc[-1].get('macd', {})
            prev_macd = df.iloc[-2].get('macd', {}) if len(df) > 1 else {}
            
            if not current_macd or not prev_macd:
                return signals
            
            current_macd_line = current_macd.get('macd')
            current_signal_line = current_macd.get('signal')
            prev_macd_line = prev_macd.get('macd')
            prev_signal_line = prev_macd.get('signal')
            
            if None in [current_macd_line, current_signal_line, prev_macd_line, prev_signal_line]:
                return signals
            
            # MACD金叉和死叉
            if prev_macd_line <= prev_signal_line and current_macd_line > current_signal_line:
                signals.append('MACD_BULLISH_CROSS')
            elif prev_macd_line >= prev_signal_line and current_macd_line < current_signal_line:
                signals.append('MACD_BEARISH_CROSS')
            
            # MACD零轴穿越
            if prev_macd_line <= 0 and current_macd_line > 0:
                signals.append('MACD_ZERO_CROSS_UP')
            elif prev_macd_line >= 0 and current_macd_line < 0:
                signals.append('MACD_ZERO_CROSS_DOWN')
            
            # MACD背离（简化版本）
            if len(df) >= 10:
                recent_closes = df['close'].tail(5).values
                recent_macd = [df.iloc[i].get('macd', {}).get('macd') for i in range(-5, 0)]
                recent_macd = [macd for macd in recent_macd if macd is not None]
                
                if len(recent_macd) >= 3:
                    if (recent_closes[-1] < min(recent_closes[:-1]) and 
                        recent_macd[-1] > min(recent_macd[:-1])):
                        signals.append('MACD_DIVERGENCE_BULLISH')
                    
                    if (recent_closes[-1] > max(recent_closes[:-1]) and 
                        recent_macd[-1] < max(recent_macd[:-1])):
                        signals.append('MACD_DIVERGENCE_BEARISH')
            
            logger.debug(f"检测到MACD信号: {signals}")
            return signals
            
        except Exception as e:
            logger.error(f"MACD信号检测失败: {e}")
            return []
    
    def detect_ma_signals(self, df: pd.DataFrame) -> List[str]:
        """
        检测移动平均线相关信号
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            List[str]: 移动平均线信号列表
        """
        signals = []
        
        try:
            if len(df) < 2:
                return signals
            
            current = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else None
            
            current_ma = current.get('ma', {})
            prev_ma = prev.get('ma', {}) if prev is not None else {}
            
            # 获取各周期移动平均线
            ma5_curr = current_ma.get('ma5')
            ma10_curr = current_ma.get('ma10')
            ma20_curr = current_ma.get('ma20')
            ma50_curr = current_ma.get('ma50')
            
            ma5_prev = prev_ma.get('ma5')
            ma20_prev = prev_ma.get('ma20')
            
            current_close = current['close']
            
            # 检查数据完整性
            if None in [ma5_curr, ma10_curr, ma20_curr, ma50_curr]:
                return signals
            
            # 金叉和死叉
            if (ma5_prev is not None and ma20_prev is not None and
                ma5_prev <= ma20_prev and ma5_curr > ma20_curr):
                signals.append('MA_GOLDEN_CROSS')
            elif (ma5_prev is not None and ma20_prev is not None and
                  ma5_prev >= ma20_prev and ma5_curr < ma20_curr):
                signals.append('MA_DEATH_CROSS')
            
            # 多头排列和空头排列
            if ma5_curr > ma10_curr > ma20_curr > ma50_curr:
                signals.append('MA_BULLISH_ARRANGEMENT')
            elif ma5_curr < ma10_curr < ma20_curr < ma50_curr:
                signals.append('MA_BEARISH_ARRANGEMENT')
            
            # 价格与重要均线的关系
            if current_close > ma50_curr:
                signals.append('PRICE_ABOVE_MA50')
            elif current_close < ma50_curr:
                signals.append('PRICE_BELOW_MA50')
            
            logger.debug(f"检测到MA信号: {signals}")
            return signals
            
        except Exception as e:
            logger.error(f"MA信号检测失败: {e}")
            return []
    
    def detect_bollinger_signals(self, df: pd.DataFrame) -> List[str]:
        """
        检测布林带相关信号
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            List[str]: 布林带信号列表
        """
        signals = []
        
        try:
            if len(df) < 20:  # 需要足够数据计算带宽
                return signals
            
            current = df.iloc[-1]
            current_bb = current.get('bollinger', {})
            current_close = current['close']
            
            upper = current_bb.get('upper')
            middle = current_bb.get('middle')
            lower = current_bb.get('lower')
            
            if None in [upper, middle, lower]:
                return signals
            
            # 计算布林带宽度
            recent_bb_data = []
            for i in range(-20, 0):
                if abs(i) <= len(df):
                    bb_data = df.iloc[i].get('bollinger', {})
                    if bb_data.get('upper') and bb_data.get('lower'):
                        bandwidth = bb_data['upper'] - bb_data['lower']
                        recent_bb_data.append(bandwidth)
            
            if len(recent_bb_data) >= 15:
                avg_bandwidth = np.mean(recent_bb_data[:-1])  # 排除当前值
                current_bandwidth = upper - lower
                
                # 布林带收缩和扩张
                if current_bandwidth < avg_bandwidth * 0.8:
                    signals.append('BB_SQUEEZE')
                elif current_bandwidth > avg_bandwidth * 1.2:
                    signals.append('BB_EXPANSION')
            
            # 价格触及布林带
            if current_close >= upper * 0.995:  # 允许小误差
                signals.append('BB_UPPER_TOUCH')
            elif current_close <= lower * 1.005:  # 允许小误差
                signals.append('BB_LOWER_TOUCH')
            
            # 价格穿越中轨
            if len(df) >= 2:
                prev = df.iloc[-2]
                prev_close = prev['close']
                prev_bb = prev.get('bollinger', {})
                prev_middle = prev_bb.get('middle')
                
                if prev_middle is not None:
                    if prev_close <= prev_middle and current_close > middle:
                        signals.append('BB_MIDDLE_CROSS_UP')
                    elif prev_close >= prev_middle and current_close < middle:
                        signals.append('BB_MIDDLE_CROSS_DOWN')
            
            logger.debug(f"检测到布林带信号: {signals}")
            return signals
            
        except Exception as e:
            logger.error(f"布林带信号检测失败: {e}")
            return []
    
    def detect_kdj_signals(self, df: pd.DataFrame) -> List[str]:
        """
        检测KDJ相关信号
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            List[str]: KDJ信号列表
        """
        signals = []
        
        try:
            if len(df) < 2:
                return signals
            
            current_kdj = df.iloc[-1].get('kdj', {})
            prev_kdj = df.iloc[-2].get('kdj', {}) if len(df) > 1 else {}
            
            k_curr = current_kdj.get('k')
            d_curr = current_kdj.get('d')
            j_curr = current_kdj.get('j')
            
            k_prev = prev_kdj.get('k')
            d_prev = prev_kdj.get('d')
            
            if None in [k_curr, d_curr, j_curr]:
                return signals
            
            # KDJ超买超卖
            if j_curr < self.thresholds['KDJ_OVERSOLD']:
                signals.append('KDJ_OVERSOLD')
            elif j_curr > self.thresholds['KDJ_OVERBOUGHT']:
                signals.append('KDJ_OVERBOUGHT')
            
            # KDJ金叉死叉
            if (k_prev is not None and d_prev is not None):
                if k_prev <= d_prev and k_curr > d_curr and j_curr < 80:
                    signals.append('KDJ_GOLDEN_CROSS')
                elif k_prev >= d_prev and k_curr < d_curr and j_curr > 20:
                    signals.append('KDJ_DEATH_CROSS')
            
            logger.debug(f"检测到KDJ信号: {signals}")
            return signals
            
        except Exception as e:
            logger.error(f"KDJ信号检测失败: {e}")
            return []
    
    def detect_stochastic_signals(self, df: pd.DataFrame) -> List[str]:
        """
        检测随机振荡器相关信号
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            List[str]: 随机振荡器信号列表
        """
        signals = []
        
        try:
            if len(df) < 2:
                return signals
            
            current_stoch = df.iloc[-1].get('stochastic', {})
            prev_stoch = df.iloc[-2].get('stochastic', {}) if len(df) > 1 else {}
            
            k_curr = current_stoch.get('k')
            d_curr = current_stoch.get('d')
            k_prev = prev_stoch.get('k')
            d_prev = prev_stoch.get('d')
            
            if None in [k_curr, d_curr]:
                return signals
            
            # 随机振荡器超买超卖
            if k_curr < self.thresholds['STOCH_OVERSOLD'] and d_curr < self.thresholds['STOCH_OVERSOLD']:
                signals.append('STOCH_OVERSOLD')
            elif k_curr > self.thresholds['STOCH_OVERBOUGHT'] and d_curr > self.thresholds['STOCH_OVERBOUGHT']:
                signals.append('STOCH_OVERBOUGHT')
            
            # 随机振荡器金叉死叉
            if (k_prev is not None and d_prev is not None):
                if k_prev <= d_prev and k_curr > d_curr and k_curr < 80:
                    signals.append('STOCH_BULLISH_CROSS')
                elif k_prev >= d_prev and k_curr < d_curr and k_curr > 20:
                    signals.append('STOCH_BEARISH_CROSS')
            
            logger.debug(f"检测到随机振荡器信号: {signals}")
            return signals
            
        except Exception as e:
            logger.error(f"随机振荡器信号检测失败: {e}")
            return []
    
    def detect_cci_signals(self, df: pd.DataFrame) -> List[str]:
        """
        检测CCI相关信号
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            List[str]: CCI信号列表
        """
        signals = []
        
        try:
            if len(df) < 2:
                return signals
            
            current_cci = df.iloc[-1].get('cci')
            prev_cci = df.iloc[-2].get('cci') if len(df) > 1 else None
            
            if current_cci is None:
                return signals
            
            # CCI超买超卖
            if current_cci < self.thresholds['CCI_OVERSOLD']:
                signals.append('CCI_OVERSOLD')
            elif current_cci > self.thresholds['CCI_OVERBOUGHT']:
                signals.append('CCI_OVERBOUGHT')
            
            # CCI零轴穿越
            if prev_cci is not None:
                if prev_cci <= 0 and current_cci > 0:
                    signals.append('CCI_ZERO_CROSS_UP')
                elif prev_cci >= 0 and current_cci < 0:
                    signals.append('CCI_ZERO_CROSS_DOWN')
            
            logger.debug(f"检测到CCI信号: {signals}")
            return signals
            
        except Exception as e:
            logger.error(f"CCI信号检测失败: {e}")
            return []
    
    def detect_volume_signals(self, df: pd.DataFrame) -> List[str]:
        """
        检测成交量相关信号
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            List[str]: 成交量信号列表
        """
        signals = []
        
        try:
            if len(df) < 20:  # 需要足够数据计算平均成交量
                return signals
            
            current_volume = df.iloc[-1]['volume']
            recent_volumes = df['volume'].tail(20).values[:-1]  # 排除当前值
            avg_volume = np.mean(recent_volumes)
            
            # 成交量放大
            if current_volume > avg_volume * 2:
                signals.append('VOLUME_SPIKE')
            # 成交量萎缩
            elif current_volume < avg_volume * 0.5:
                signals.append('VOLUME_DRY')
            
            logger.debug(f"检测到成交量信号: {signals}")
            return signals
            
        except Exception as e:
            logger.error(f"成交量信号检测失败: {e}")
            return []
    
    def detect_all_signals(self, symbol: str, timeframe: str) -> List[str]:
        """
        检测指定交易对和时间周期的所有技术信号
        
        Args:
            symbol: 币种符号
            timeframe: 时间周期
            
        Returns:
            List[str]: 所有检测到的信号列表
        """
        all_signals = []
        
        try:
            # 获取历史数据
            historical_data = mongodb_client.get_historical_data(symbol, timeframe, limit=100)
            
            if not historical_data:
                logger.warning(f"无历史数据用于信号检测: {symbol} {timeframe}")
                return all_signals
            
            # 准备数据
            df = self.prepare_signal_data(historical_data)
            if df is None:
                return all_signals
            
            # 检测各类信号
            all_signals.extend(self.detect_rsi_signals(df))
            all_signals.extend(self.detect_macd_signals(df))
            all_signals.extend(self.detect_ma_signals(df))
            all_signals.extend(self.detect_bollinger_signals(df))
            all_signals.extend(self.detect_kdj_signals(df))
            all_signals.extend(self.detect_stochastic_signals(df))
            all_signals.extend(self.detect_cci_signals(df))
            all_signals.extend(self.detect_volume_signals(df))
            
            # 去重
            all_signals = list(set(all_signals))
            
            # 更新数据库
            if historical_data:
                latest_timestamp = historical_data[-1]['timestamp']
                if isinstance(latest_timestamp, str):
                    from datetime import datetime
                    latest_timestamp = datetime.fromisoformat(latest_timestamp.replace('Z', '+00:00'))
                
                mongodb_client.update_signals(symbol, timeframe, latest_timestamp, all_signals)
            
            logger.info(f"检测到技术信号 {symbol} {timeframe}: {all_signals}")
            return all_signals
            
        except Exception as e:
            logger.error(f"技术信号检测失败 {symbol} {timeframe}: {e}")
            return []
    
    def batch_detect_signals(self) -> bool:
        """
        批量检测所有交易对和时间周期的技术信号
        
        Returns:
            bool: 批量检测是否成功
        """
        success_count = 0
        total_count = len(SYMBOLS) * len(TIMEFRAMES)
        
        logger.info("开始批量检测技术信号...")
        
        for symbol_pair in SYMBOLS:
            symbol = SYMBOL_MAPPING.get(symbol_pair, symbol_pair)
            for timeframe in TIMEFRAMES:
                signals = self.detect_all_signals(symbol, timeframe)
                if signals is not None:  # 即使没有信号也算成功
                    success_count += 1
        
        logger.info(f"技术信号检测完成，成功: {success_count}/{total_count}")
        return success_count > 0
    
    def detect_signals_for_symbol_timeframe(self, symbol: str, timeframe: str) -> List[str]:
        """
        为特定币种和时间周期检测信号（用于新数据触发的实时检测）
        
        Args:
            symbol: 币种符号
            timeframe: 时间周期
            
        Returns:
            List[str]: 检测到的信号列表
        """
        try:
            logger.debug(f"开始检测交易信号: {symbol} {timeframe}")
            return self.detect_all_signals(symbol, timeframe)
        except Exception as e:
            logger.error(f"检测交易信号失败 {symbol} {timeframe}: {e}")
            return []


# 全局技术信号检测器实例
signal_detector = TechnicalSignalDetector() 