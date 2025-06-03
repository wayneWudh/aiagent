"""
请求处理工具
提供请求ID生成、验证和响应格式化功能
"""
import uuid
import time
import json
from typing import Dict, Any, Optional
from datetime import datetime


def datetime_serializer(obj):
    """自定义datetime序列化器"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


class RequestIDGenerator:
    """请求ID生成器"""
    
    @staticmethod
    def generate() -> str:
        """
        生成唯一的请求ID
        格式: req_{timestamp}_{uuid}
        """
        timestamp = int(time.time() * 1000)  # 毫秒时间戳
        unique_id = str(uuid.uuid4())[:8]  # 取UUID的前8位
        return f"req_{timestamp}_{unique_id}"
    
    @staticmethod
    def is_valid(request_id: str) -> bool:
        """验证请求ID格式是否正确"""
        if not request_id or not isinstance(request_id, str):
            return False
        
        parts = request_id.split('_')
        if len(parts) != 3 or parts[0] != 'req':
            return False
        
        try:
            # 验证时间戳部分是否为数字
            int(parts[1])
            return True
        except ValueError:
            return False


class ResponseFormatter:
    """响应格式化器"""
    
    @staticmethod
    def _serialize_datetime_values(data: Any) -> Any:
        """递归序列化数据中的datetime对象"""
        if isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, dict):
            return {key: ResponseFormatter._serialize_datetime_values(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [ResponseFormatter._serialize_datetime_values(item) for item in data]
        else:
            return data
    
    @staticmethod
    def format_success(
        request_id: str,
        data: Any,
        message: str = "请求处理成功"
    ) -> Dict[str, Any]:
        """格式化成功响应"""
        return {
            "request_id": request_id,
            "success": True,
            "message": message,
            "data": ResponseFormatter._serialize_datetime_values(data),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def format_error(
        request_id: str,
        error_message: str,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """格式化错误响应"""
        response = {
            "request_id": request_id,
            "success": False,
            "message": error_message,
            "error_code": error_code,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if details:
            response["details"] = ResponseFormatter._serialize_datetime_values(details)
        
        return response
    
    @staticmethod
    def format_mcp_response(
        request_id: str,
        data: Dict[str, Any],
        field_descriptions: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        格式化MCP响应，包含字段描述
        
        Args:
            request_id: 请求ID
            data: 响应数据
            field_descriptions: 字段描述映射
        """
        # 首先序列化datetime对象
        serialized_data = ResponseFormatter._serialize_datetime_values(data)
        
        if field_descriptions:
            # 为每个字段添加描述
            formatted_data = {}
            for key, value in serialized_data.items():
                if key in field_descriptions:
                    formatted_data[key] = {
                        "value": value,
                        "description": field_descriptions[key]
                    }
                else:
                    formatted_data[key] = value
            
            return {
                "request_id": request_id,
                "success": True,
                "data": formatted_data,
                "field_descriptions": field_descriptions,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return ResponseFormatter.format_success(request_id, serialized_data)


# 常用的字段描述
ALERT_FIELD_DESCRIPTIONS = {
    "rule_id": "预警规则的唯一标识符，用于后续管理和查询操作",
    "rule_name": "用户定义的预警规则名称，便于识别和区分不同规则",
    "symbol": "监控的加密货币符号，如BTC、ETH",
    "timeframes": "监控的时间周期列表，如['1h', '1d']",
    "threshold_value": "预警触发的阈值，当实际值达到此阈值时触发预警",
    "condition": "预警触发条件，如'above'(大于)、'below'(小于)",
    "frequency": "预警触发频率，控制预警消息的发送频率",
    "is_active": "预警规则是否处于激活状态，只有激活状态的规则才会被监控",
    "monitoring_status": "当前监控状态，表示系统是否正在监控此规则",
    "expected_trigger": "预期触发条件的详细描述，帮助用户理解何时会触发预警",
    "created_time": "预警规则创建时间",
    "trigger_count": "预警规则历史触发次数统计",
    "last_triggered_at": "最后一次触发预警的时间"
}

QUERY_FIELD_DESCRIPTIONS = {
    "symbol": "查询的加密货币符号",
    "timeframes": "查询的时间周期列表",
    "total_records": "查询返回的总记录数",
    "matched_records": "满足条件的记录数",
    "query_time": "查询执行时间",
    "execution_time_ms": "查询执行耗时（毫秒）",
    "data": "查询结果数据列表"
} 