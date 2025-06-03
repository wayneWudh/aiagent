"""
查询引擎
提供灵活的K线数据查询功能
"""
import logging
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from database.mongo_client import mongodb_client
from .models import (
    QueryRequest, QueryResult, QueryCondition, LogicalCondition,
    QueryOperator, QueryField, LogicalOperator
)

logger = logging.getLogger(__name__)


class QueryEngine:
    """K线数据查询引擎"""
    
    def __init__(self):
        self.db_client = mongodb_client
        
    async def execute_query(self, query_request: QueryRequest) -> QueryResult:
        """
        执行查询请求
        
        Args:
            query_request: 查询请求对象
            
        Returns:
            QueryResult: 查询结果
        """
        start_time = time.time()
        
        try:
            # 构建MongoDB查询条件
            mongo_query = self._build_mongo_query(query_request)
            
            # 执行查询
            results = []
            total_count = 0
            
            for timeframe in query_request.timeframes:
                # 添加时间周期条件
                tf_query = {**mongo_query, "timeframe": timeframe}
                
                # 获取总数
                count = self.db_client.collection.count_documents(tf_query)
                total_count += count
                
                # 执行查询
                cursor = self.db_client.collection.find(tf_query)
                
                # 排序
                sort_field = self._map_sort_field(query_request.sort_by)
                sort_direction = 1 if query_request.sort_order == "asc" else -1
                cursor = cursor.sort(sort_field, sort_direction)
                
                # 限制数量
                cursor = cursor.limit(query_request.limit)
                
                # 获取结果
                timeframe_results = list(cursor)
                
                # 处理结果数据
                for item in timeframe_results:
                    processed_item = self._process_result_item(item)
                    results.append(processed_item)
            
            execution_time = (time.time() - start_time) * 1000
            
            return QueryResult(
                symbol=query_request.symbol,
                timeframes=query_request.timeframes,
                total_records=total_count,
                matched_records=len(results),
                data=results,
                query_time=datetime.utcnow(),
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            logger.error(f"查询执行失败: {e}")
            raise
    
    def _build_mongo_query(self, query_request: QueryRequest) -> Dict[str, Any]:
        """构建MongoDB查询条件"""
        base_query = {
            "symbol": query_request.symbol
        }
        
        # 构建条件查询
        condition_query = self._build_condition_query(query_request.conditions)
        
        # 合并查询条件
        if condition_query:
            base_query.update(condition_query)
        
        return base_query
    
    def _build_condition_query(self, conditions: Union[QueryCondition, LogicalCondition]) -> Dict[str, Any]:
        """构建条件查询"""
        if isinstance(conditions, QueryCondition):
            return self._build_single_condition(conditions)
        elif isinstance(conditions, LogicalCondition):
            return self._build_logical_condition(conditions)
        else:
            return {}
    
    def _build_single_condition(self, condition: QueryCondition) -> Dict[str, Any]:
        """构建单个查询条件"""
        field_name = self._map_field_name(condition.field)
        operator = condition.operator
        value = condition.value
        
        if operator == QueryOperator.EQ:
            return {field_name: value}
        elif operator == QueryOperator.NE:
            return {field_name: {"$ne": value}}
        elif operator == QueryOperator.GT:
            return {field_name: {"$gt": value}}
        elif operator == QueryOperator.GTE:
            return {field_name: {"$gte": value}}
        elif operator == QueryOperator.LT:
            return {field_name: {"$lt": value}}
        elif operator == QueryOperator.LTE:
            return {field_name: {"$lte": value}}
        elif operator == QueryOperator.IN:
            return {field_name: {"$in": value if isinstance(value, list) else [value]}}
        elif operator == QueryOperator.NIN:
            return {field_name: {"$nin": value if isinstance(value, list) else [value]}}
        elif operator == QueryOperator.BETWEEN:
            if isinstance(value, list) and len(value) == 2:
                return {field_name: {"$gte": value[0], "$lte": value[1]}}
            else:
                raise ValueError("BETWEEN操作符需要包含两个值的列表")
        elif operator == QueryOperator.CONTAINS:
            if condition.field == QueryField.SIGNALS:
                return {field_name: {"$in": [value] if isinstance(value, str) else value}}
            else:
                return {field_name: {"$regex": str(value), "$options": "i"}}
        elif operator == QueryOperator.NOT_CONTAINS:
            if condition.field == QueryField.SIGNALS:
                return {field_name: {"$nin": [value] if isinstance(value, str) else value}}
            else:
                return {field_name: {"$not": {"$regex": str(value), "$options": "i"}}}
        elif operator == QueryOperator.STARTS_WITH:
            return {field_name: {"$regex": f"^{value}", "$options": "i"}}
        elif operator == QueryOperator.ENDS_WITH:
            return {field_name: {"$regex": f"{value}$", "$options": "i"}}
        elif operator == QueryOperator.WITHIN_LAST:
            # 在过去N个时段内
            if isinstance(value, int):
                # 计算时间范围
                now = datetime.utcnow()
                time_delta = self._calculate_time_delta(value)
                start_time = now - time_delta
                return {"timestamp": {"$gte": start_time}}
            else:
                raise ValueError("WITHIN_LAST操作符需要整数值")
        elif operator == QueryOperator.BEFORE:
            if isinstance(value, str):
                try:
                    date_value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    return {"timestamp": {"$lt": date_value}}
                except ValueError:
                    raise ValueError("BEFORE操作符需要有效的日期时间格式")
            else:
                raise ValueError("BEFORE操作符需要日期时间字符串")
        elif operator == QueryOperator.AFTER:
            if isinstance(value, str):
                try:
                    date_value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    return {"timestamp": {"$gt": date_value}}
                except ValueError:
                    raise ValueError("AFTER操作符需要有效的日期时间格式")
            else:
                raise ValueError("AFTER操作符需要日期时间字符串")
        else:
            raise ValueError(f"不支持的操作符: {operator}")
    
    def _build_logical_condition(self, condition: LogicalCondition) -> Dict[str, Any]:
        """构建逻辑组合条件"""
        sub_conditions = []
        
        for sub_condition in condition.conditions:
            sub_query = self._build_condition_query(sub_condition)
            if sub_query:
                sub_conditions.append(sub_query)
        
        if not sub_conditions:
            return {}
        
        if condition.operator == LogicalOperator.AND:
            if len(sub_conditions) == 1:
                return sub_conditions[0]
            return {"$and": sub_conditions}
        elif condition.operator == LogicalOperator.OR:
            if len(sub_conditions) == 1:
                return sub_conditions[0]
            return {"$or": sub_conditions}
        elif condition.operator == LogicalOperator.NOT:
            if len(sub_conditions) == 1:
                return {"$not": sub_conditions[0]}
            else:
                raise ValueError("NOT操作符只能包含一个子条件")
        else:
            raise ValueError(f"不支持的逻辑操作符: {condition.operator}")
    
    def _map_field_name(self, field: QueryField) -> str:
        """映射字段名到MongoDB字段名"""
        field_mapping = {
            QueryField.OPEN: "open",
            QueryField.HIGH: "high", 
            QueryField.LOW: "low",
            QueryField.CLOSE: "close",
            QueryField.VOLUME: "volume",
            QueryField.RSI: "rsi",
            QueryField.MACD_LINE: "macd.macd_line",
            QueryField.MACD_SIGNAL: "macd.macd_signal",
            QueryField.MACD_HISTOGRAM: "macd.macd_histogram",
            QueryField.MA_5: "ma.ma_5",
            QueryField.MA_10: "ma.ma_10",
            QueryField.MA_20: "ma.ma_20",
            QueryField.MA_50: "ma.ma_50",
            QueryField.BB_UPPER: "bollinger.upper",
            QueryField.BB_MIDDLE: "bollinger.middle",
            QueryField.BB_LOWER: "bollinger.lower",
            QueryField.CCI: "cci",
            QueryField.KDJ_K: "kdj.k",
            QueryField.KDJ_D: "kdj.d",
            QueryField.KDJ_J: "kdj.j",
            QueryField.STOCH_K: "stochastic.k",
            QueryField.STOCH_D: "stochastic.d",
            QueryField.SIGNALS: "signals",
            QueryField.TIMESTAMP: "timestamp",
            QueryField.TIMEFRAME: "timeframe",
            QueryField.SYMBOL: "symbol"
        }
        
        return field_mapping.get(field, str(field))
    
    def _map_sort_field(self, field: QueryField) -> str:
        """映射排序字段"""
        return self._map_field_name(field)
    
    def _calculate_time_delta(self, periods: int) -> timedelta:
        """根据时段数计算时间差"""
        # 这里简化处理，假设是小时单位
        # 实际应用中可能需要根据timeframe来计算
        return timedelta(hours=periods)
    
    def _process_result_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """处理查询结果项"""
        # 移除MongoDB的_id字段
        if '_id' in item:
            del item['_id']
        
        # 格式化时间戳
        if 'timestamp' in item and isinstance(item['timestamp'], datetime):
            item['timestamp'] = item['timestamp'].isoformat()
        
        return item
    
    async def get_historical_stats(
        self, 
        symbol: str, 
        field: QueryField,
        timeframes: List[str],
        periods: int = 100
    ) -> Dict[str, Any]:
        """
        获取历史统计数据
        
        Args:
            symbol: 币种符号
            field: 统计字段
            timeframes: 时间周期
            periods: 历史时段数
            
        Returns:
            Dict: 统计结果
        """
        try:
            field_name = self._map_field_name(field)
            stats = {}
            
            for timeframe in timeframes:
                # 获取最近N个时段的数据
                cursor = self.db_client.collection.find(
                    {"symbol": symbol, "timeframe": timeframe},
                    {field_name: 1, "timestamp": 1}
                ).sort("timestamp", -1).limit(periods)
                
                data = list(cursor)
                values = []
                
                for item in data:
                    # 处理嵌套字段
                    value = item
                    for key in field_name.split('.'):
                        if key in value:
                            value = value[key]
                        else:
                            value = None
                            break
                    
                    if value is not None and isinstance(value, (int, float)):
                        values.append(value)
                
                if values:
                    stats[timeframe] = {
                        "count": len(values),
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values),
                        "current": values[0] if values else None,
                        "previous": values[1] if len(values) > 1 else None
                    }
                else:
                    stats[timeframe] = {
                        "count": 0,
                        "min": None,
                        "max": None,
                        "avg": None,
                        "current": None,
                        "previous": None
                    }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取历史统计失败: {e}")
            raise 