"""
预警系统数据模型定义
定义查询条件、预警规则和响应数据的标准格式
"""
from typing import Dict, List, Any, Optional, Union, Literal
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class QueryOperator(str, Enum):
    """查询操作符"""
    # 比较操作符
    EQ = "eq"        # 等于
    NE = "ne"        # 不等于
    GT = "gt"        # 大于
    GTE = "gte"      # 大于等于
    LT = "lt"        # 小于
    LTE = "lte"      # 小于等于
    
    # 范围操作符
    IN = "in"        # 在范围内
    NIN = "nin"      # 不在范围内
    BETWEEN = "between"  # 在两值之间
    
    # 模式匹配
    CONTAINS = "contains"    # 包含
    NOT_CONTAINS = "not_contains"  # 不包含
    STARTS_WITH = "starts_with"    # 以...开始
    ENDS_WITH = "ends_with"        # 以...结束
    
    # 时间相关
    WITHIN_LAST = "within_last"    # 在过去N个时段内
    BEFORE = "before"              # 在某时间之前
    AFTER = "after"                # 在某时间之后


class LogicalOperator(str, Enum):
    """逻辑操作符"""
    AND = "and"
    OR = "or"
    NOT = "not"


class QueryField(str, Enum):
    """可查询的字段"""
    # 基础价格字段
    OPEN = "open"
    HIGH = "high"
    LOW = "low"
    CLOSE = "close"
    VOLUME = "volume"
    
    # 技术指标字段
    RSI = "rsi"
    MACD_LINE = "macd.macd_line"
    MACD_SIGNAL = "macd.macd_signal"
    MACD_HISTOGRAM = "macd.macd_histogram"
    MA_5 = "ma.ma_5"
    MA_10 = "ma.ma_10"
    MA_20 = "ma.ma_20"
    MA_50 = "ma.ma_50"
    BB_UPPER = "bollinger.upper"
    BB_MIDDLE = "bollinger.middle"
    BB_LOWER = "bollinger.lower"
    CCI = "cci"
    KDJ_K = "kdj.k"
    KDJ_D = "kdj.d"
    KDJ_J = "kdj.j"
    STOCH_K = "stochastic.k"
    STOCH_D = "stochastic.d"
    
    # 信号字段
    SIGNALS = "signals"
    
    # 时间字段
    TIMESTAMP = "timestamp"
    TIMEFRAME = "timeframe"
    SYMBOL = "symbol"


class QueryCondition(BaseModel):
    """单个查询条件"""
    field: QueryField = Field(..., description="查询字段")
    operator: QueryOperator = Field(..., description="查询操作符")
    value: Union[str, int, float, List[Union[str, int, float]]] = Field(..., description="查询值")
    
    class Config:
        use_enum_values = True


class LogicalCondition(BaseModel):
    """逻辑组合条件"""
    operator: LogicalOperator = Field(..., description="逻辑操作符")
    conditions: List[Union[QueryCondition, 'LogicalCondition']] = Field(..., description="子条件列表")
    
    class Config:
        use_enum_values = True


# 更新前向引用
LogicalCondition.model_rebuild()


class QueryRequest(BaseModel):
    """查询请求"""
    symbol: str = Field(..., description="币种符号")
    timeframes: List[str] = Field(default=["1h"], description="时间周期")
    conditions: Union[QueryCondition, LogicalCondition] = Field(..., description="查询条件")
    limit: int = Field(default=100, description="返回记录数量限制")
    sort_by: QueryField = Field(default=QueryField.TIMESTAMP, description="排序字段")
    sort_order: Literal["asc", "desc"] = Field(default="desc", description="排序方向")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if v.upper() not in ['BTC', 'ETH']:
            raise ValueError('只支持BTC和ETH')
        return v.upper()
    
    @validator('timeframes')
    def validate_timeframes(cls, v):
        valid_timeframes = ['5m', '15m', '1h', '1d']
        for tf in v:
            if tf not in valid_timeframes:
                raise ValueError(f'无效的时间周期: {tf}')
        return v


class AlertTriggerType(str, Enum):
    """预警触发类型"""
    PRICE_THRESHOLD = "price_threshold"      # 价格阈值
    INDICATOR_THRESHOLD = "indicator_threshold"  # 指标阈值
    SIGNAL_DETECTION = "signal_detection"    # 信号检测
    PATTERN_MATCH = "pattern_match"          # 模式匹配
    CUSTOM_QUERY = "custom_query"            # 自定义查询


class AlertFrequency(str, Enum):
    """预警频率"""
    ONCE = "once"            # 只触发一次
    EVERY_TIME = "every_time"    # 每次满足条件都触发
    DAILY = "daily"          # 每天最多一次
    HOURLY = "hourly"        # 每小时最多一次


class LarkMessageType(str, Enum):
    """Lark消息类型"""
    TEXT = "text"
    CARD = "interactive"


class AlertRule(BaseModel):
    """预警规则"""
    id: Optional[str] = Field(None, description="预警规则ID")
    name: str = Field(..., description="预警名称")
    description: Optional[str] = Field(None, description="预警描述")
    
    # 监控配置
    symbol: str = Field(..., description="监控的币种")
    timeframes: List[str] = Field(default=["1h"], description="监控的时间周期")
    
    # 触发条件
    trigger_type: AlertTriggerType = Field(..., description="触发类型")
    trigger_conditions: Union[QueryCondition, LogicalCondition] = Field(..., description="触发条件")
    
    # 预警配置
    frequency: AlertFrequency = Field(default=AlertFrequency.ONCE, description="触发频率")
    webhook_url: Optional[str] = Field(None, description="Webhook URL")
    message_type: LarkMessageType = Field(default=LarkMessageType.TEXT, description="消息类型")
    custom_message: Optional[str] = Field(None, description="自定义消息")
    
    # 状态
    is_active: bool = Field(default=True, description="是否激活")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    last_triggered_at: Optional[datetime] = Field(None, description="最后触发时间")
    trigger_count: int = Field(default=0, description="触发次数")
    
    class Config:
        use_enum_values = True


class QueryResult(BaseModel):
    """查询结果"""
    symbol: str = Field(..., description="币种符号")
    timeframes: List[str] = Field(..., description="查询的时间周期")
    total_records: int = Field(..., description="总记录数")
    matched_records: int = Field(..., description="匹配记录数")
    data: List[Dict[str, Any]] = Field(..., description="查询数据")
    query_time: datetime = Field(..., description="查询时间")
    execution_time_ms: float = Field(..., description="执行时间(毫秒)")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AlertTriggerResult(BaseModel):
    """预警触发结果"""
    rule_id: str = Field(..., description="规则ID")
    rule_name: str = Field(..., description="规则名称")
    symbol: str = Field(..., description="币种")
    timeframe: str = Field(..., description="时间周期")
    trigger_time: datetime = Field(..., description="触发时间")
    trigger_data: Dict[str, Any] = Field(..., description="触发时的数据")
    message_sent: bool = Field(..., description="消息是否发送成功")
    webhook_response: Optional[Dict[str, Any]] = Field(None, description="Webhook响应")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AlertStats(BaseModel):
    """预警统计"""
    total_rules: int = Field(..., description="总规则数")
    active_rules: int = Field(..., description="激活规则数")
    triggered_today: int = Field(..., description="今日触发次数")
    triggered_this_hour: int = Field(..., description="本小时触发次数")
    success_rate: float = Field(..., description="成功率")
    last_check_time: datetime = Field(..., description="最后检查时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 