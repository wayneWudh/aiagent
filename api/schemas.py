"""
API Schema定义
包含请求和响应的数据结构定义
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class SignalQueryRequest(BaseModel):
    """技术信号查询请求Schema"""
    symbol: str = Field(..., description="币种符号，如BTC或ETH", example="BTC")
    timeframes: Optional[List[str]] = Field(
        default=None, 
        description="时间周期列表，不指定则查询所有周期", 
        example=["5m", "15m", "1h", "1d"]
    )
    
    @validator('symbol')
    def validate_symbol(cls, v):
        """验证币种符号"""
        if not v:
            raise ValueError('币种符号不能为空')
        # 转换为大写
        return v.upper()
    
    @validator('timeframes')
    def validate_timeframes(cls, v):
        """验证时间周期"""
        if v is not None:
            valid_timeframes = ['5m', '15m', '1h', '1d']
            for tf in v:
                if tf not in valid_timeframes:
                    raise ValueError(f'无效的时间周期: {tf}，支持的周期: {valid_timeframes}')
        return v


class TechnicalSignalData(BaseModel):
    """技术信号数据Schema"""
    timestamp: datetime = Field(..., description="时间戳")
    timeframe: str = Field(..., description="时间周期")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: float = Field(..., description="成交量")
    signals: List[str] = Field(default_factory=list, description="技术信号列表")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TimeframeSignals(BaseModel):
    """按时间周期分组的信号数据Schema"""
    timeframe: str = Field(..., description="时间周期")
    recent_periods: List[TechnicalSignalData] = Field(..., description="最近两个交易时段的数据")


class SignalQueryResponse(BaseModel):
    """技术信号查询响应Schema"""
    success: bool = Field(..., description="请求是否成功")
    message: str = Field(..., description="响应消息")
    data: Dict[str, Any] = Field(..., description="响应数据")
    
    class SignalData(BaseModel):
        """信号数据"""
        symbol: str = Field(..., description="币种符号")
        query_time: datetime = Field(..., description="查询时间")
        timeframes: List[TimeframeSignals] = Field(..., description="各时间周期的信号数据")
        summary: Dict[str, Any] = Field(..., description="信号汇总统计")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """错误响应Schema"""
    success: bool = Field(default=False, description="请求是否成功")
    message: str = Field(..., description="错误消息")
    error_code: str = Field(..., description="错误代码")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")


class HealthCheckResponse(BaseModel):
    """健康检查响应Schema"""
    status: str = Field(..., description="服务状态")
    timestamp: datetime = Field(..., description="检查时间")
    database: Dict[str, Any] = Field(..., description="数据库状态")
    supported_symbols: List[str] = Field(..., description="支持的币种列表")
    supported_timeframes: List[str] = Field(..., description="支持的时间周期列表")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 