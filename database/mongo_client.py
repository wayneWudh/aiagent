"""
MongoDB数据库连接管理模块
提供数据库连接、操作和管理功能
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pymongo import MongoClient, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from config.settings import MONGODB_CONFIG

logger = logging.getLogger(__name__)


class MongoDBClient:
    """MongoDB客户端管理类"""
    
    def __init__(self):
        """初始化MongoDB连接"""
        self.client: Optional[MongoClient] = None
        self.database: Optional[Database] = None
        self.collection: Optional[Collection] = None
        self.connect()
    
    def connect(self) -> bool:
        """
        建立MongoDB连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 构建连接字符串
            if MONGODB_CONFIG['username'] and MONGODB_CONFIG['password']:
                connection_string = (
                    f"mongodb://{MONGODB_CONFIG['username']}:"
                    f"{MONGODB_CONFIG['password']}@"
                    f"{MONGODB_CONFIG['host']}:{MONGODB_CONFIG['port']}/"
                    f"{MONGODB_CONFIG['database']}"
                )
            else:
                connection_string = (
                    f"mongodb://{MONGODB_CONFIG['host']}:"
                    f"{MONGODB_CONFIG['port']}"
                )
            
            # 建立连接
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            self.database = self.client[MONGODB_CONFIG['database']]
            self.collection = self.database[MONGODB_CONFIG['collection']]
            
            # 测试连接
            self.client.admin.command('ping')
            
            # 创建索引
            self._create_indexes()
            
            logger.info("成功连接到MongoDB数据库")
            return True
            
        except Exception as e:
            logger.error(f"连接MongoDB失败: {e}")
            return False
    
    def _create_indexes(self):
        """创建数据库索引以优化查询性能"""
        try:
            # 创建复合索引
            self.collection.create_index([
                ("symbol", 1),
                ("timeframe", 1),
                ("timestamp", -1)
            ])
            
            # 创建时间戳索引
            self.collection.create_index([("timestamp", -1)])
            
            # 创建信号索引
            self.collection.create_index([("signals", 1)])
            
            logger.info("数据库索引创建成功")
            
        except Exception as e:
            logger.warning(f"创建索引时出现警告: {e}")
    
    def insert_kline(self, kline_data: Dict) -> bool:
        """
        插入K线数据
        
        Args:
            kline_data: K线数据字典
            
        Returns:
            bool: 插入是否成功
        """
        try:
            # 添加时间戳
            kline_data['created_at'] = datetime.utcnow()
            kline_data['updated_at'] = datetime.utcnow()
            
            # 使用upsert模式，避免重复数据
            query = {
                'symbol': kline_data['symbol'],
                'timeframe': kline_data['timeframe'],
                'timestamp': kline_data['timestamp']
            }
            
            result = self.collection.update_one(
                query,
                {'$set': kline_data},
                upsert=True
            )
            
            if result.upserted_id or result.modified_count:
                logger.debug(f"成功插入/更新K线数据: {kline_data['symbol']} {kline_data['timeframe']}")
                return True
            else:
                logger.debug(f"K线数据无变化: {kline_data['symbol']} {kline_data['timeframe']}")
                return True
                
        except Exception as e:
            logger.error(f"插入K线数据失败: {e}")
            return False
    
    def get_historical_data(self, symbol: str, timeframe: str, limit: int = 60) -> List[Dict]:
        """
        获取历史K线数据
        
        Args:
            symbol: 币种符号
            timeframe: 时间周期
            limit: 获取数量限制
            
        Returns:
            List[Dict]: 历史K线数据列表
        """
        try:
            query = {
                'symbol': symbol,
                'timeframe': timeframe
            }
            
            cursor = self.collection.find(query).sort('timestamp', DESCENDING).limit(limit)
            data = list(cursor)
            
            # 按时间正序排列
            data.reverse()
            
            logger.debug(f"获取历史数据: {symbol} {timeframe}, 数量: {len(data)}")
            return data
            
        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
            return []
    
    def update_technical_indicators(self, symbol: str, timeframe: str, timestamp: datetime, indicators: Dict) -> bool:
        """
        更新技术指标数据
        
        Args:
            symbol: 币种符号
            timeframe: 时间周期
            timestamp: 时间戳
            indicators: 技术指标数据
            
        Returns:
            bool: 更新是否成功
        """
        try:
            query = {
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp': timestamp
            }
            
            update_data = {
                **indicators,
                'updated_at': datetime.utcnow()
            }
            
            result = self.collection.update_one(
                query,
                {'$set': update_data}
            )
            
            if result.modified_count:
                logger.debug(f"成功更新技术指标: {symbol} {timeframe}")
                return True
            else:
                logger.debug(f"技术指标无变化: {symbol} {timeframe}")
                return True
                
        except Exception as e:
            logger.error(f"更新技术指标失败: {e}")
            return False
    
    def update_signals(self, symbol: str, timeframe: str, timestamp: datetime, signals: List[str]) -> bool:
        """
        更新技术信号
        
        Args:
            symbol: 币种符号
            timeframe: 时间周期
            timestamp: 时间戳
            signals: 技术信号列表
            
        Returns:
            bool: 更新是否成功
        """
        try:
            query = {
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp': timestamp
            }
            
            update_data = {
                'signals': signals,
                'updated_at': datetime.utcnow()
            }
            
            result = self.collection.update_one(
                query,
                {'$set': update_data}
            )
            
            if result.modified_count:
                logger.debug(f"成功更新技术信号: {symbol} {timeframe}, 信号数量: {len(signals)}")
                return True
            else:
                logger.debug(f"技术信号无变化: {symbol} {timeframe}")
                return True
                
        except Exception as e:
            logger.error(f"更新技术信号失败: {e}")
            return False
    
    def get_latest_data(self, symbol: str, timeframe: str, limit: int = 1) -> List[Dict]:
        """
        获取最新的K线数据
        
        Args:
            symbol: 币种符号
            timeframe: 时间周期
            limit: 获取数量限制
            
        Returns:
            List[Dict]: 最新K线数据列表
        """
        try:
            query = {
                'symbol': symbol,
                'timeframe': timeframe
            }
            
            cursor = self.collection.find(query).sort('timestamp', DESCENDING).limit(limit)
            data = list(cursor)
            
            logger.debug(f"获取最新数据: {symbol} {timeframe}, 数量: {len(data)}")
            return data
            
        except Exception as e:
            logger.error(f"获取最新数据失败: {e}")
            return []
    
    def get_latest_kline(self, symbol: str, timeframe: str) -> Optional[Dict]:
        """
        获取最新的K线记录
        
        Args:
            symbol: 币种符号
            timeframe: 时间周期
            
        Returns:
            Optional[Dict]: 最新K线数据
        """
        try:
            query = {
                'symbol': symbol,
                'timeframe': timeframe
            }
            
            latest = self.collection.find_one(query, sort=[('timestamp', DESCENDING)])
            
            if latest:
                logger.debug(f"获取到最新K线: {symbol} {timeframe} {latest.get('timestamp')}")
            else:
                logger.debug(f"未找到K线数据: {symbol} {timeframe}")
            
            return latest
            
        except Exception as e:
            logger.error(f"获取最新K线失败: {e}")
            return None
    
    def kline_exists(self, symbol: str, timeframe: str, timestamp: datetime) -> bool:
        """
        检查指定时间的K线是否存在
        
        Args:
            symbol: 币种符号
            timeframe: 时间周期
            timestamp: 时间戳
            
        Returns:
            bool: 是否存在
        """
        try:
            query = {
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp': timestamp
            }
            
            count = self.collection.count_documents(query)
            exists = count > 0
            
            logger.debug(f"检查K线存在性: {symbol} {timeframe} {timestamp} -> {exists}")
            return exists
            
        except Exception as e:
            logger.error(f"检查K线存在性失败: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        try:
            if self.client:
                self.client.close()
                logger.info("MongoDB连接已关闭")
        except Exception as e:
            logger.error(f"关闭MongoDB连接失败: {e}")
    
    def get_database_info(self) -> Dict:
        """
        获取数据库信息
        
        Returns:
            Dict: 数据库信息
        """
        try:
            if self.database is None:
                return {"error": "数据库未连接"}
            
            stats = self.database.command("dbstats")
            collection_stats = self.collection.count_documents({})
            
            return {
                "database": self.database.name,
                "collection": self.collection.name,
                "documents": collection_stats,
                "size_mb": stats.get("dataSize", 0) / (1024 * 1024),
                "indexes": stats.get("indexes", 0),
                "avg_doc_size": stats.get("avgObjSize", 0)
            }
        except Exception as e:
            logger.error(f"获取数据库信息失败: {e}")
            return {"error": str(e)}
    
    def get_collection(self):
        """
        获取集合对象
        
        Returns:
            Collection: MongoDB集合对象
        """
        return self.collection


# 全局数据库客户端实例
mongodb_client = MongoDBClient() 