# MCP预警系统使用指南

## 🎯 系统概述

本系统是一个完整的加密货币技术分析和智能预警平台，专为AI Agent设计，通过MCP协议提供强大的数据查询和预警管理功能。

### 🌟 核心特性

- **请求ID追踪**：所有MCP请求都有唯一标识符，支持完整的请求生命周期追踪
- **异步预警处理**：预警设置与触发分离，立即返回设置成功，触发时异步推送到外部API
- **多时间周期支持**：所有工具都支持timeframes参数，精确控制查询和监控范围  
- **详细字段描述**：每个响应都包含字段描述，便于AI Agent理解和处理
- **实时数据更新**：每分钟采集最新数据，新增数据后自动计算技术指标和信号

## 🔧 MCP工具集成

### 工具概览

系统提供**10个专业MCP工具**，所有工具都支持request_id追踪和timeframes参数：

| 工具名称 | 功能描述 | Timeframes支持 | Request ID支持 |
|---------|----------|---------------|----------------|
| `flexible_crypto_query` | 灵活的加密货币数据查询 | ✅ | ✅ |
| `query_trading_signals` | 交易信号查询分析 | ✅ | ✅ |
| `analyze_price_levels` | 价格水平分析 | ✅ | ✅ |
| `analyze_indicator_extremes` | 指标极值分析 | ✅ | ✅ |
| `create_price_alert` | 创建价格预警 | ✅ | ✅ |
| `create_indicator_alert` | 创建指标预警 | ✅ | ✅ |
| `create_signal_alert` | 创建信号预警 | ✅ | ✅ |
| `manage_alert_rules` | 预警规则管理 | N/A | ✅ |
| `test_webhook` | Webhook测试工具 | N/A | ✅ |
| `get_alert_statistics` | 统计信息获取 | N/A | ✅ |

## 📊 查询工具详解

### 1. flexible_crypto_query - 灵活数据查询

**功能**：提供最灵活的加密货币数据查询能力，支持复杂条件组合和多时间周期筛选。

**参数**：
```json
{
  "request_id": "string (可选)",
  "symbol": "BTC|ETH", 
  "timeframes": ["5m", "15m", "1h", "1d"] (可选),
  "conditions": {
    "field": "string",
    "operator": "gt|lt|eq|gte|lte|in|between|contains|within_last",
    "value": "any"
  },
  "logic": "AND|OR|NOT (可选)",
  "limit": "number (可选，默认10)"
}
```

**支持查询字段**：
- **价格字段**：`open`, `high`, `low`, `close`, `volume`
- **技术指标**：`rsi`, `macd_line`, `macd_signal`, `ma_5`, `ma_10`, `ma_20`, `ma_50`, `ma_100`, `ma_200`
- **其他指标**：`bollinger_upper`, `bollinger_lower`, `cci`, `stochastic_k`, `stochastic_d`
- **信号字段**：`signals`
- **时间字段**：`timestamp`

**操作符说明**：
- `gt/lt/gte/lte`：数值比较（大于、小于、大于等于、小于等于）
- `eq`：等于
- `in`：包含在列表中
- `between`：范围查询 [min, max]
- `contains`：字符串/数组包含
- `within_last`：时间范围查询（分钟数）

**使用示例**：

**基础价格查询**：
```json
{
  "request_id": "query_001",
  "symbol": "BTC",
  "timeframes": ["1h"],
  "conditions": {
    "field": "close",
    "operator": "gt",
    "value": 100000
  },
  "limit": 5
}
```

**技术指标查询**：
```json
{
  "request_id": "query_002", 
  "symbol": "ETH",
  "timeframes": ["15m", "1h"],
  "conditions": {
    "field": "rsi",
    "operator": "lt",
    "value": 30
  }
}
```

**复合条件查询**：
```json
{
  "request_id": "query_003",
  "symbol": "BTC",
  "timeframes": ["1h"],
  "conditions": [
    {
      "field": "rsi",
      "operator": "lt", 
      "value": 30
    },
    {
      "field": "close",
      "operator": "gt",
      "value": 95000
    }
  ],
  "logic": "AND"
}
```

### 2. query_trading_signals - 交易信号查询

**功能**：专门查询和分析技术交易信号，支持信号类型筛选和时间周期分析。

**参数**：
```json
{
  "request_id": "string (可选)",
  "symbol": "BTC|ETH",
  "timeframes": ["5m", "15m", "1h", "1d"] (可选),
  "signal_types": ["RSI_OVERSOLD", "MACD_GOLDEN_CROSS", ...] (可选),
  "limit": "number (可选，默认10)"
}
```

**支持的信号类型**：

**RSI信号**：
- `RSI_OVERSOLD` - RSI超卖（< 30）
- `RSI_OVERBOUGHT` - RSI超买（> 70）
- `RSI_BULLISH_DIVERGENCE` - RSI看涨背离
- `RSI_BEARISH_DIVERGENCE` - RSI看跌背离

**MACD信号**：
- `MACD_GOLDEN_CROSS` - MACD金叉
- `MACD_DEATH_CROSS` - MACD死叉
- `MACD_ABOVE_ZERO` - MACD上穿零轴
- `MACD_BELOW_ZERO` - MACD下穿零轴

**移动平均线信号**：
- `MA_GOLDEN_CROSS` - MA金叉
- `MA_DEATH_CROSS` - MA死叉
- `MA_BULLISH_ARRANGEMENT` - 多头排列
- `MA_BEARISH_ARRANGEMENT` - 空头排列
- `PRICE_ABOVE_MA50` - 价格高于MA50
- `PRICE_BELOW_MA50` - 价格低于MA50

**布林带信号**：
- `BB_UPPER_TOUCH` - 触及上轨
- `BB_LOWER_TOUCH` - 触及下轨
- `BB_MIDDLE_CROSS_UP` - 上穿中轨
- `BB_MIDDLE_CROSS_DOWN` - 下穿中轨
- `BB_SQUEEZE` - 布林带收缩
- `BB_EXPANSION` - 布林带扩张

**使用示例**：

**查询所有信号**：
```json
{
  "request_id": "signals_001",
  "symbol": "BTC",
  "timeframes": ["5m", "1h"]
}
```

**筛选特定信号**：
```json
{
  "request_id": "signals_002",
  "symbol": "ETH", 
  "timeframes": ["1h"],
  "signal_types": ["RSI_OVERSOLD", "MACD_GOLDEN_CROSS"]
}
```

### 3. analyze_price_levels - 价格水平分析

**功能**：分析价格的支撑阻力水平，识别关键价格区域和突破点。

**参数**：
```json
{
  "request_id": "string (可选)",
  "symbol": "BTC|ETH",
  "timeframes": ["5m", "15m", "1h", "1d"] (可选),
  "analysis_type": "support_resistance|breakout|trend_analysis",
  "lookback_periods": "number (可选，默认20)"
}
```

**分析类型**：
- `support_resistance` - 支撑阻力分析
- `breakout` - 突破点分析  
- `trend_analysis` - 趋势分析

**使用示例**：
```json
{
  "request_id": "price_001",
  "symbol": "BTC",
  "timeframes": ["1h", "1d"],
  "analysis_type": "support_resistance",
  "lookback_periods": 50
}
```

### 4. analyze_indicator_extremes - 指标极值分析

**功能**：分析技术指标的极值情况，识别超买超卖和异常值。

**参数**：
```json
{
  "request_id": "string (可选)",
  "symbol": "BTC|ETH",
  "timeframes": ["5m", "15m", "1h", "1d"] (可选),
  "indicators": ["rsi", "cci", "stochastic_k", "macd_line"] (可选),
  "extreme_type": "high|low|both",
  "lookback_periods": "number (可选，默认20)"
}
```

**支持的指标**：
- `rsi` - 相对强弱指数
- `cci` - 商品通道指数
- `stochastic_k` - 随机振荡器K值
- `stochastic_d` - 随机振荡器D值
- `macd_line` - MACD线
- `macd_signal` - MACD信号线

**使用示例**：
```json
{
  "request_id": "extreme_001",
  "symbol": "BTC",
  "timeframes": ["1h"],
  "indicators": ["rsi", "cci"],
  "extreme_type": "both",
  "lookback_periods": 100
}
```

## 🚨 预警工具详解

### 预警架构设计

系统采用**异步预警架构**：

1. **预警设置阶段**：AI Agent通过MCP工具创建预警规则，立即返回成功响应
2. **监控阶段**：系统后台持续监控数据，检测预警条件
3. **触发阶段**：条件满足时，构建预警数据包
4. **推送阶段**：发送POST请求到外部API (`http://localhost:8081/webhook/alert/trigger`)

### 1. create_price_alert - 创建价格预警

**功能**：创建基于价格阈值的预警规则，支持多时间周期监控。

**参数**：
```json
{
  "request_id": "string (可选)",
  "name": "string",
  "symbol": "BTC|ETH",
  "price_threshold": "number",
  "condition": "above|below|equal",
  "timeframes": ["5m", "15m", "1h", "1d"] (可选),
  "frequency": "once|every_time|hourly|daily",
  "custom_message": "string (可选)"
}
```

**condition说明**：
- `above` - 价格高于阈值时触发
- `below` - 价格低于阈值时触发  
- `equal` - 价格等于阈值时触发（±0.1%容差）

**frequency说明**：
- `once` - 只触发一次，触发后自动禁用
- `every_time` - 每次满足条件都触发
- `hourly` - 每小时最多触发一次
- `daily` - 每天最多触发一次

**使用示例**：

**基础价格预警**：
```json
{
  "request_id": "alert_001",
  "name": "BTC突破10万美元",
  "symbol": "BTC",
  "price_threshold": 100000,
  "condition": "above",
  "timeframes": ["1h"],
  "frequency": "once",
  "custom_message": "BTC价格突破重要心理关口！"
}
```

**多时间周期监控**：
```json
{
  "request_id": "alert_002", 
  "name": "ETH跌破支撑位",
  "symbol": "ETH",
  "price_threshold": 3000,
  "condition": "below",
  "timeframes": ["15m", "1h", "1d"],
  "frequency": "every_time"
}
```

### 2. create_indicator_alert - 创建指标预警

**功能**：基于技术指标值创建预警，支持RSI、MACD、CCI等指标的阈值监控。

**参数**：
```json
{
  "request_id": "string (可选)",
  "name": "string",
  "symbol": "BTC|ETH",
  "indicator": "rsi|macd_line|macd_signal|cci|stochastic_k|stochastic_d",
  "threshold": "number",
  "condition": "above|below|equal",
  "timeframes": ["5m", "15m", "1h", "1d"] (可选),
  "frequency": "once|every_time|hourly|daily",
  "custom_message": "string (可选)"
}
```

**使用示例**：

**RSI超买预警**：
```json
{
  "request_id": "indicator_001",
  "name": "BTC RSI超买预警",
  "symbol": "BTC", 
  "indicator": "rsi",
  "threshold": 70,
  "condition": "above",
  "timeframes": ["1h"],
  "frequency": "once"
}
```

**CCI极值预警**：
```json
{
  "request_id": "indicator_002",
  "name": "ETH CCI超卖", 
  "symbol": "ETH",
  "indicator": "cci",
  "threshold": -100,
  "condition": "below",
  "timeframes": ["15m", "1h"],
  "frequency": "every_time"
}
```

### 3. create_signal_alert - 创建信号预警

**功能**：基于技术信号创建预警，当检测到特定技术信号时触发通知。

**参数**：
```json
{
  "request_id": "string (可选)",
  "name": "string",
  "symbol": "BTC|ETH",
  "signal_types": ["RSI_OVERSOLD", "MACD_GOLDEN_CROSS", ...],
  "timeframes": ["5m", "15m", "1h", "1d"] (可选),
  "frequency": "once|every_time|hourly|daily",
  "custom_message": "string (可选)"
}
```

**使用示例**：

**RSI超卖信号预警**：
```json
{
  "request_id": "signal_001", 
  "name": "BTC RSI超卖信号",
  "symbol": "BTC",
  "signal_types": ["RSI_OVERSOLD"],
  "timeframes": ["1h"],
  "frequency": "once"
}
```

**组合信号预警**：
```json
{
  "request_id": "signal_002",
  "name": "ETH买入信号组合",
  "symbol": "ETH",
  "signal_types": ["RSI_OVERSOLD", "MACD_GOLDEN_CROSS", "BB_LOWER_TOUCH"],
  "timeframes": ["15m", "1h"],
  "frequency": "every_time",
  "custom_message": "多个买入信号同时出现！"
}
```

## 🛠️ 管理工具详解

### 1. manage_alert_rules - 预警规则管理

**功能**：管理预警规则的生命周期，包括查看、修改、启用、禁用和删除。

**参数**：
```json
{
  "request_id": "string (可选)",
  "action": "list|enable|disable|delete|update",
  "rule_id": "string (action不为list时必填)",
  "updates": "object (action为update时必填)"
}
```

**action说明**：
- `list` - 列出所有预警规则
- `enable` - 启用指定规则
- `disable` - 禁用指定规则
- `delete` - 删除指定规则
- `update` - 更新规则参数

**使用示例**：

**列出所有规则**：
```json
{
  "request_id": "manage_001",
  "action": "list"
}
```

**禁用指定规则**：
```json
{
  "request_id": "manage_002",
  "action": "disable", 
  "rule_id": "rule-uuid-123"
}
```

**更新规则**：
```json
{
  "request_id": "manage_003",
  "action": "update",
  "rule_id": "rule-uuid-123",
  "updates": {
    "price_threshold": 105000,
    "frequency": "hourly"
  }
}
```

### 2. get_alert_statistics - 统计信息获取

**功能**：获取预警系统的运行统计信息和性能指标。

**参数**：
```json
{
  "request_id": "string (可选)",
  "stats_type": "overview|performance|recent_activity"
}
```

**使用示例**：
```json
{
  "request_id": "stats_001",
  "stats_type": "overview"
}
```

### 3. test_webhook - Webhook测试

**功能**：测试预警推送的连通性和格式正确性。

**参数**：
```json
{
  "request_id": "string (可选)",
  "test_type": "connectivity|format|full"
}
```

**使用示例**：
```json
{
  "request_id": "test_001",
  "test_type": "full"
}
```

## 📡 预警推送格式

### 推送端点
预警触发时，系统会发送POST请求到：
```
http://localhost:8081/webhook/alert/trigger
```

### 预警数据格式

**价格预警数据包**：
```json
{
  "request_id": "req_1748752984777_af684a9d",
  "alert_type": "price_alert", 
  "rule_id": "rule-uuid-123",
  "rule_name": "BTC突破10万美元",
  "symbol": "BTC",
  "timeframe": "1h",
  "trigger_time": "2025-06-01T04:43:04.777667",
  "trigger_data": {
    "description": "BTC价格大于$100000时触发预警",
    "actual_value": "$105123.45",
    "threshold": 100000,
    "comparison": "当前价格$105123.45 大于 设定阈值$100000.00",
    "custom_message": "BTC价格突破重要心理关口！",
    "condition": "above"
  }
}
```

**指标预警数据包**：
```json
{
  "request_id": "req_1748752984778_bg752c8e",
  "alert_type": "indicator_alert",
  "rule_id": "rule-uuid-456", 
  "rule_name": "BTC RSI超买预警",
  "symbol": "BTC",
  "timeframe": "1h",
  "trigger_time": "2025-06-01T04:43:04.777667",
  "trigger_data": {
    "description": "RSI指标大于70时触发预警",
    "indicator": "rsi",
    "actual_value": 75.23,
    "threshold": 70,
    "comparison": "当前RSI值75.23 大于 设定阈值70.00",
    "condition": "above"
  }
}
```

**信号预警数据包**：
```json
{
  "request_id": "req_1748752984779_ch863d9f",
  "alert_type": "signal_alert",
  "rule_id": "rule-uuid-789",
  "rule_name": "BTC RSI超卖信号",
  "symbol": "BTC", 
  "timeframe": "1h",
  "trigger_time": "2025-06-01T04:43:04.777667",
  "trigger_data": {
    "description": "检测到RSI_OVERSOLD信号时触发预警",
    "detected_signals": ["RSI_OVERSOLD"],
    "signal_context": "RSI值为28.45，触发超卖信号",
    "custom_message": "BTC出现超卖信号，可能是买入机会"
  }
}
```

## 📖 时间周期（Timeframes）系统

### 支持的时间周期
- `5m` - 5分钟K线
- `15m` - 15分钟K线  
- `1h` - 1小时K线
- `1d` - 1天K线

### Timeframes在不同工具中的作用

**查询工具**：
- 指定要查询的数据时间周期
- 可以同时查询多个时间周期的数据
- 不指定则默认查询所有时间周期

**预警工具**：
- 指定监控的时间周期范围
- 支持多时间周期同时监控
- 只有指定时间周期的数据变化才会触发预警

### 使用建议

**短期交易**：
```json
{
  "timeframes": ["5m", "15m"]
}
```

**中期分析**：
```json
{
  "timeframes": ["15m", "1h"]
}
```

**长期趋势**：
```json
{
  "timeframes": ["1h", "1d"]
}
```

**全面监控**：
```json
{
  "timeframes": ["5m", "15m", "1h", "1d"]
}
```

## 🎯 实际应用场景

### 场景1：日内交易策略

**目标**：捕捉BTC的短期交易机会

**实施步骤**：

1. **创建RSI超卖预警**：
```json
{
  "name": "BTC 5分钟RSI超卖",
  "symbol": "BTC",
  "indicator": "rsi", 
  "threshold": 30,
  "condition": "below",
  "timeframes": ["5m"],
  "frequency": "every_time"
}
```

2. **创建MACD金叉预警**：
```json
{
  "name": "BTC MACD金叉信号",
  "symbol": "BTC",
  "signal_types": ["MACD_GOLDEN_CROSS"],
  "timeframes": ["5m", "15m"],
  "frequency": "every_time"
}
```

3. **设置止损预警**：
```json
{
  "name": "BTC止损预警",
  "symbol": "BTC", 
  "price_threshold": 98000,
  "condition": "below",
  "timeframes": ["5m"],
  "frequency": "once"
}
```

### 场景2：长期投资监控

**目标**：监控ETH的长期趋势变化

**实施步骤**：

1. **创建趋势突破预警**：
```json
{
  "name": "ETH突破关键阻力",
  "symbol": "ETH",
  "price_threshold": 4000, 
  "condition": "above",
  "timeframes": ["1h", "1d"],
  "frequency": "once"
}
```

2. **创建布林带信号监控**：
```json
{
  "name": "ETH布林带压缩",
  "symbol": "ETH",
  "signal_types": ["BB_SQUEEZE"],
  "timeframes": ["1d"],
  "frequency": "every_time"
}
```

### 场景3：风险管理

**目标**：及时发现市场异常和风险信号

**实施步骤**：

1. **创建极端RSI预警**：
```json
{
  "name": "BTC极端RSI预警",
  "symbol": "BTC",
  "indicator": "rsi",
  "threshold": 80,
  "condition": "above", 
  "timeframes": ["1h"],
  "frequency": "once"
}
```

2. **创建成交量异常监控**：
```json
{
  "name": "成交量激增预警",
  "symbol": "BTC",
  "signal_types": ["VOLUME_SPIKE"],
  "timeframes": ["15m", "1h"],
  "frequency": "every_time"
}
```

## 🔧 响应格式和字段描述

### 标准响应格式

所有MCP工具都返回统一的响应格式：

```json
{
  "request_id": "req_1748752984777_af684a9d",
  "success": true,
  "data": {
    // 具体数据内容
  },
  "field_descriptions": {
    // 字段描述映射
  },
  "timestamp": "2025-06-01T04:43:04.777667"
}
```

### 字段描述系统

每个响应都包含`field_descriptions`对象，提供所有字段的详细说明：

**基础字段描述**：
```json
{
  "field_descriptions": {
    "rule_id": "预警规则的唯一标识符，用于后续管理和查询操作",
    "rule_name": "用户定义的预警规则名称，便于识别和区分不同规则", 
    "symbol": "监控的加密货币符号，如BTC、ETH",
    "timeframes": "监控的时间周期列表，如['1h', '1d']",
    "threshold_value": "预警触发的阈值，当实际值达到此阈值时触发预警",
    "condition": "预警触发条件，如'above'(大于)、'below'(小于)",
    "frequency": "预警触发频率，控制预警消息的发送频率",
    "is_active": "预警规则是否处于激活状态，只有激活状态的规则才会被监控",
    "monitoring_status": "当前监控状态，表示系统是否正在监控此规则",
    "created_time": "预警规则创建时间",
    "trigger_count": "预警规则历史触发次数统计",
    "last_triggered_at": "最后一次触发预警的时间"
  }
}
```

## 📈 性能和最佳实践

### 性能优化建议

1. **合理使用timeframes参数**：
   - 只指定需要的时间周期，避免查询不必要的数据
   - 短期策略使用5m、15m，长期分析使用1h、1d

2. **预警频率控制**：
   - 重要预警使用`once`频率，避免重复通知
   - 监控性预警使用`hourly`或`daily`频率

3. **request_id使用**：
   - 为重要请求提供有意义的request_id
   - 便于后续追踪和调试

### 错误处理和重试

**常见错误类型**：
- `INVALID_SYMBOL` - 不支持的币种
- `INVALID_TIMEFRAME` - 不支持的时间周期  
- `INVALID_CONDITION` - 无效的条件操作符
- `DUPLICATE_RULE` - 重复的预警规则
- `RULE_NOT_FOUND` - 预警规则不存在

**重试策略**：
- 网络错误：自动重试3次，间隔1秒
- 参数错误：立即返回错误，不重试
- 系统错误：记录日志，等待系统恢复

### 监控和维护

**系统健康监控**：
```json
{
  "tool": "get_alert_statistics",
  "arguments": {
    "stats_type": "overview"
  }
}
```

**定期维护建议**：
- 每周检查预警规则的有效性
- 每月清理不再需要的预警规则
- 定期测试预警推送的连通性

## 🔗 外部集成指南

### 预警接收API设计

外部系统需要提供接收预警的API端点：

**端点要求**：
- **URL**: `http://localhost:8081/webhook/alert/trigger`
- **方法**: POST
- **Content-Type**: application/json

**请求处理示例**（Python Flask）：
```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook/alert/trigger', methods=['POST'])
def receive_alert():
    try:
        alert_data = request.json
        
        # 提取基本信息
        request_id = alert_data.get('request_id')
        alert_type = alert_data.get('alert_type')
        symbol = alert_data.get('symbol')
        
        # 处理不同类型的预警
        if alert_type == 'price_alert':
            handle_price_alert(alert_data)
        elif alert_type == 'indicator_alert':
            handle_indicator_alert(alert_data)
        elif alert_type == 'signal_alert':
            handle_signal_alert(alert_data)
        
        return jsonify({
            "success": True,
            "message": "预警接收成功", 
            "request_id": request_id
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def handle_price_alert(data):
    # 处理价格预警逻辑
    pass

def handle_indicator_alert(data):
    # 处理指标预警逻辑
    pass
    
def handle_signal_alert(data):
    # 处理信号预警逻辑
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)
```

### 消息推送集成

**飞书机器人集成示例**：
```python
import requests

def send_to_lark(alert_data):
    webhook_url = "YOUR_LARK_WEBHOOK_URL"
    
    message = {
        "msg_type": "text",
        "content": {
            "text": f"🚨 {alert_data['rule_name']}\n"
                   f"币种: {alert_data['symbol']}\n" 
                   f"时间: {alert_data['trigger_time']}\n"
                   f"详情: {alert_data['trigger_data']['description']}"
        }
    }
    
    response = requests.post(webhook_url, json=message)
    return response.status_code == 200
```

## 📝 总结

MCP预警系统为AI Agent提供了强大而灵活的加密货币数据查询和预警管理能力。通过合理使用timeframes参数、request_id追踪和字段描述系统，AI Agent可以：

1. **精确查询**：通过flexible_crypto_query进行复杂的数据查询
2. **信号分析**：通过query_trading_signals获取技术信号洞察  
3. **智能预警**：通过多种预警工具创建个性化监控策略
4. **规则管理**：通过manage_alert_rules进行规则生命周期管理
5. **系统监控**：通过get_alert_statistics了解系统运行状态

系统的异步预警架构确保了高性能和可靠性，而详细的字段描述和标准化的响应格式使得AI Agent能够更好地理解和处理返回的数据。 