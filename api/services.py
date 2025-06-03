"""
API业务逻辑服务层
处理技术信号查询的核心业务逻辑
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from database.mongo_client import mongodb_client
from config.settings import TIMEFRAMES, SYMBOL_MAPPING

logger = logging.getLogger(__name__)


class SignalService:
    """技术信号查询服务"""
    
    def __init__(self):
        """初始化服务"""
        self.db_client = mongodb_client
        self.supported_symbols = list(SYMBOL_MAPPING.values())
        self.supported_timeframes = TIMEFRAMES
    
    def get_recent_signals(self, symbol: str, timeframes: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        获取指定币种最近两个交易时段的技术信号
        
        Args:
            symbol: 币种符号 (如BTC, ETH)
            timeframes: 时间周期列表，None表示查询所有周期
            
        Returns:
            Dict: 包含技术信号数据的字典
        """
        try:
            # 验证币种
            if symbol not in self.supported_symbols:
                raise ValueError(f"不支持的币种: {symbol}，支持的币种: {self.supported_symbols}")
            
            # 验证时间周期
            if timeframes is None:
                timeframes = self.supported_timeframes
            else:
                for tf in timeframes:
                    if tf not in self.supported_timeframes:
                        raise ValueError(f"不支持的时间周期: {tf}，支持的周期: {self.supported_timeframes}")
            
            # 查询各时间周期的信号数据
            timeframe_results = []
            for timeframe in timeframes:
                recent_data = self._get_recent_data_for_timeframe(symbol, timeframe)
                if recent_data:
                    timeframe_results.append({
                        'timeframe': timeframe,
                        'recent_periods': recent_data
                    })
            
            # 生成汇总统计
            summary = self._generate_summary(timeframe_results)
            
            result = {
                'symbol': symbol,
                'query_time': datetime.utcnow(),
                'timeframes': timeframe_results,
                'summary': summary
            }
            
            logger.info(f"成功查询技术信号: {symbol}, 时间周期: {timeframes}")
            return result
            
        except Exception as e:
            logger.error(f"查询技术信号失败: {e}")
            raise
    
    def _get_recent_data_for_timeframe(self, symbol: str, timeframe: str) -> List[Dict[str, Any]]:
        """
        获取指定时间周期的最近两个时段数据
        
        Args:
            symbol: 币种符号
            timeframe: 时间周期
            
        Returns:
            List[Dict]: 最近两个时段的数据列表
        """
        try:
            # 查询最近两个时段的数据
            query = {
                'symbol': symbol,
                'timeframe': timeframe
            }
            
            cursor = self.db_client.collection.find(query).sort('timestamp', -1).limit(2)
            raw_data = list(cursor)
            
            if not raw_data:
                logger.warning(f"未找到数据: {symbol} {timeframe}")
                return []
            
            # 按时间正序排列（最老的在前）
            raw_data.reverse()
            
            # 格式化数据
            formatted_data = []
            for item in raw_data:
                formatted_item = {
                    'timestamp': item.get('timestamp'),
                    'timeframe': timeframe,
                    'open': float(item.get('open', 0)),
                    'high': float(item.get('high', 0)),
                    'low': float(item.get('low', 0)),
                    'close': float(item.get('close', 0)),
                    'volume': float(item.get('volume', 0)),
                    'signals': item.get('signals', [])
                }
                formatted_data.append(formatted_item)
            
            return formatted_data
            
        except Exception as e:
            logger.error(f"获取时间周期数据失败: {symbol} {timeframe}, 错误: {e}")
            return []
    
    def _generate_summary(self, timeframe_results: List[Dict]) -> Dict[str, Any]:
        """
        生成技术信号汇总统计
        
        Args:
            timeframe_results: 各时间周期的结果数据
            
        Returns:
            Dict: 汇总统计数据
        """
        try:
            all_signals = []
            total_periods = 0
            signal_counts = {}
            timeframe_summary = {}
            
            for tf_result in timeframe_results:
                timeframe = tf_result['timeframe']
                periods_data = tf_result['recent_periods']
                
                # 统计这个时间周期的信号
                tf_signals = []
                for period in periods_data:
                    period_signals = period.get('signals', [])
                    tf_signals.extend(period_signals)
                    all_signals.extend(period_signals)
                    total_periods += 1
                
                # 时间周期汇总
                timeframe_summary[timeframe] = {
                    'periods_count': len(periods_data),
                    'signals_count': len(tf_signals),
                    'unique_signals': list(set(tf_signals))
                }
            
            # 统计信号出现次数
            for signal in all_signals:
                signal_counts[signal] = signal_counts.get(signal, 0) + 1
            
            # 计算热门信号（按出现频率排序）
            popular_signals = sorted(signal_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            summary = {
                'total_periods': total_periods,
                'total_signals': len(all_signals),
                'unique_signals_count': len(set(all_signals)),
                'timeframe_summary': timeframe_summary,
                'signal_frequency': dict(signal_counts),
                'popular_signals': [{'signal': signal, 'count': count} for signal, count in popular_signals],
                'has_signals': len(all_signals) > 0
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"生成汇总统计失败: {e}")
            return {
                'total_periods': 0,
                'total_signals': 0,
                'unique_signals_count': 0,
                'has_signals': False,
                'error': str(e)
            }
    
    def check_health(self) -> Dict[str, Any]:
        """
        检查服务健康状态
        
        Returns:
            Dict: 健康状态信息
        """
        try:
            # 检查数据库连接
            db_status = 'connected'
            db_info = {}
            
            try:
                # 测试数据库连接
                self.db_client.client.admin.command('ping')
                
                # 获取数据库统计信息
                stats = self.db_client.database.command('collstats', 'klines')
                db_info = {
                    'documents_count': stats.get('count', 0),
                    'size_mb': round(stats.get('size', 0) / 1024 / 1024, 2),
                    'avg_doc_size': round(stats.get('avgObjSize', 0), 2)
                }
            except Exception as e:
                db_status = 'disconnected'
                db_info = {'error': str(e)}
            
            health_info = {
                'status': 'healthy' if db_status == 'connected' else 'unhealthy',
                'timestamp': datetime.utcnow(),
                'database': {
                    'status': db_status,
                    'info': db_info
                },
                'supported_symbols': self.supported_symbols,
                'supported_timeframes': self.supported_timeframes
            }
            
            return health_info
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                'status': 'unhealthy',
                'timestamp': datetime.utcnow(),
                'error': str(e)
            }


# 全局服务实例
signal_service = SignalService() 