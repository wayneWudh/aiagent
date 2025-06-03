# MCP服务配置和使用指南

## 概述

本系统基于[Model Context Protocol (MCP)](https://github.com/modelcontextprotocol/modelcontextprotocol)规范，为AI Agent提供加密货币技术信号分析能力。MCP是一个开放标准，允许AI模型安全地访问外部数据和工具。

## 🌐 服务架构

### 系统组成

```
┌─────────────────────────────────────────────────────────────┐
│                    加密货币技术信号分析系统                   │
├─────────────────┬─────────────────┬─────────────────────────┤
│   数据采集系统   │   RESTful API   │      MCP协议服务         │
│   (Data Layer)   │   (HTTP API)    │   (AI Agent Interface)  │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### 三层服务设计

1. **数据采集层**: 定时采集加密货币K线数据和技术指标
2. **API服务层**: 提供RESTful API接口，供Web应用和直接HTTP调用
3. **MCP协议层**: 基于WebSocket，专为AI Agent设计的标准化接口

## 🔌 端口配置

### 默认端口分配

| 服务名称 | 协议 | 默认端口 | 用途 | 对外开放 |
|----------|------|----------|------|----------|
| **数据采集系统** | - | - | 后台定时任务 | ❌ |
| **RESTful API** | HTTP | **5000** | Web API接口 | ✅ |
| **MCP WebSocket** | WebSocket | **8080** | AI Agent连接 | ✅ |
| **MCP健康检查** | HTTP | **8081** | MCP服务监控 | ✅ |

### 生产环境端口建议

| 服务名称 | 建议端口 | 防火墙规则 | 负载均衡 |
|----------|----------|------------|----------|
| RESTful API | 5000 | 允许外部访问 | 支持 |
| MCP WebSocket | 8080 | 仅AI Agent访问 | 不建议 |
| MCP健康检查 | 8081 | 仅内网监控 | 不需要 |

## 🚀 快速启动

### 1. 安装依赖

```bash
# 安装所有依赖包
pip install -r requirements.txt

# 确保MongoDB已启动
mongod
```

### 2. 统一启动所有服务

```bash
# 启动全部服务（推荐）
python start_all_services.py

# 自定义端口启动
python start_all_services.py \
  --api-port 5000 \
  --mcp-port 8080 \
  --mcp-health-port 8081

# 启用调试模式
python start_all_services.py --debug
```

### 3. 选择性启动服务

```bash
# 只启动API服务（跳过MCP）
python start_all_services.py --skip-mcp

# 只启动MCP服务（跳过数据采集）
python start_all_services.py --skip-collector

# 完全自定义
python start_all_services.py \
  --skip-collector \
  --api-port 8000 \
  --mcp-port 9000
```

### 4. 单独启动MCP服务

```bash
# 使用默认配置
python -m mcp.run_mcp

# 自定义配置
python -m mcp.run_mcp \
  --host localhost \
  --port 8080 \
  --health-port 8081 \
  --api-url http://localhost:5000
```

## 🔧 MCP协议详解

### MCP工具列表

MCP服务提供以下4个工具供AI Agent调用：

#### 1. query_crypto_signals
- **功能**: 查询指定加密货币的技术信号
- **参数**: 
  - `symbol` (必填): BTC 或 ETH
  - `timeframes` (可选): ["5m", "15m", "1h", "1d"]
- **返回**: 最近两个交易时段的完整技术分析数据

#### 2. get_supported_symbols
- **功能**: 获取系统支持的币种和时间周期
- **参数**: 无
- **返回**: 支持的币种列表和时间周期

#### 3. check_system_health
- **功能**: 检查技术信号系统健康状态
- **参数**: 无
- **返回**: 系统状态、数据库连接、数据统计

#### 4. analyze_signal_patterns
- **功能**: 深度分析技术信号模式和趋势
- **参数**:
  - `symbol` (必填): 目标币种
  - `timeframes` (可选): 分析的时间周期
- **返回**: 信号模式分析、交易建议

### MCP连接示例

#### JavaScript/TypeScript 客户端

```javascript
import { WebSocket } from 'ws';

// 连接MCP服务器
const ws = new WebSocket('ws://localhost:8080');

// 初始化连接
const initMessage = {
  jsonrpc: "2.0",
  id: 1,
  method: "initialize",
  params: {
    protocolVersion: "1.0.0",
    clientInfo: {
      name: "crypto-analysis-client",
      version: "1.0.0"
    }
  }
};

ws.send(JSON.stringify(initMessage));

// 查询BTC技术信号
const queryMessage = {
  jsonrpc: "2.0",
  id: 2,
  method: "tools/call",
  params: {
    name: "query_crypto_signals",
    arguments: {
      symbol: "BTC",
      timeframes: ["1h", "1d"]
    }
  }
};

ws.send(JSON.stringify(queryMessage));
```

#### Python 客户端

```python
import asyncio
import websockets
import json

async def test_mcp_client():
    uri = "ws://localhost:8080"
    
    async with websockets.connect(uri) as websocket:
        # 初始化连接
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "1.0.0",
                "clientInfo": {
                    "name": "python-test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        await websocket.send(json.dumps(init_msg))
        response = await websocket.recv()
        print("初始化响应:", json.loads(response))
        
        # 查询技术信号
        query_msg = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "query_crypto_signals",
                "arguments": {
                    "symbol": "BTC",
                    "timeframes": ["1h"]
                }
            }
        }
        
        await websocket.send(json.dumps(query_msg))
        response = await websocket.recv()
        result = json.loads(response)
        print("查询结果:", json.dumps(result, indent=2, ensure_ascii=False))

# 运行测试
asyncio.run(test_mcp_client())
```

## 🏥 健康检查和监控

### API健康检查

```bash
# RESTful API健康检查
curl http://localhost:5000/api/v1/health

# 响应示例
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "database": {
    "status": "connected",
    "info": {
      "documents_count": 533,
      "size_mb": 0.16
    }
  }
}
```

### MCP服务健康检查

```bash
# MCP服务健康检查
curl http://localhost:8081/health

# MCP服务状态查询
curl http://localhost:8081/status
```

### 服务状态监控

```bash
# 检查端口占用
netstat -tulpn | grep -E "(5000|8080|8081)"

# 检查进程状态
ps aux | grep -E "(main.py|run_api.py|mcp)"

# 查看日志
tail -f logs/service_manager.log
tail -f logs/mcp_server.log
```

## 🔒 安全配置

### 网络安全

1. **防火墙配置**
```bash
# 允许API访问
sudo ufw allow 5000/tcp

# 限制MCP访问（仅内网）
sudo ufw allow from 192.168.0.0/16 to any port 8080

# 禁止外网访问健康检查端口
sudo ufw deny 8081/tcp
```

2. **反向代理配置** (Nginx)
```nginx
# API服务代理
location /api/ {
    proxy_pass http://localhost:5000/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

# MCP WebSocket代理
location /mcp/ {
    proxy_pass http://localhost:8080/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

### 访问控制

1. **IP白名单**: 限制MCP服务只允许特定IP访问
2. **API密钥**: 为RESTful API添加认证机制
3. **SSL/TLS**: 在生产环境中启用HTTPS和WSS

## 🛠️ 运维配置

### 服务管理脚本

```bash
# 启动全部服务
./start_all_services.py

# 停止服务（Ctrl+C 或）
pkill -f "start_all_services.py"

# 重启服务
./restart_services.sh  # 需要创建
```

### 日志管理

```bash
# 日志文件位置
logs/
├── crypto_analysis.log     # 数据采集日志
├── service_manager.log     # 服务管理日志
└── mcp_server.log         # MCP服务日志

# 日志轮转配置
sudo vim /etc/logrotate.d/crypto-signals
```

### 性能监控

1. **CPU和内存监控**
```bash
# 监控服务资源使用
top -p $(pgrep -f "python.*start_all_services")
```

2. **网络连接监控**
```bash
# 监控WebSocket连接
ss -tuln | grep -E "(5000|8080|8081)"
```

3. **数据库监控**
```bash
# MongoDB状态
mongo --eval "db.adminCommand('serverStatus')"
```

## 🚨 故障排除

### 常见问题

#### 1. MCP服务无法启动
```bash
# 检查端口占用
lsof -i :8080

# 查看详细错误
python -m mcp.run_mcp --debug
```

#### 2. AI Agent连接失败
- 确认MCP服务正在运行
- 检查防火墙设置
- 验证WebSocket URL格式

#### 3. 数据查询返回空结果
- 检查数据采集系统是否正常运行
- 确认MongoDB数据库有数据
- 查看API健康检查状态

### 调试命令

```bash
# 测试MCP工具
python -c "
import asyncio
from mcp.tools import CryptoSignalTools

async def test():
    tools = CryptoSignalTools()
    result = await tools.execute_tool('check_system_health', {})
    print(result)

asyncio.run(test())
"

# 测试WebSocket连接
wscat -c ws://localhost:8080
```

## 📊 性能规格

### 系统要求

- **CPU**: 2核心以上
- **内存**: 4GB以上
- **存储**: 20GB可用空间
- **网络**: 稳定的互联网连接

### 性能指标

- **数据采集**: 每分钟更新
- **API响应时间**: < 100ms
- **MCP工具执行**: < 200ms
- **并发连接**: 支持50+并发WebSocket连接
- **数据查询**: 支持1000次/分钟查询频率

### 扩展性

- **水平扩展**: 支持多实例负载均衡
- **数据分片**: MongoDB支持分片扩展
- **缓存策略**: 可添加Redis缓存层

## 🔄 版本更新

### MCP协议版本

- 当前版本: **1.0.0**
- 兼容性: 向后兼容
- 更新计划: 跟随MCP官方规范

### 服务版本管理

```bash
# 查看当前版本
python -c "from mcp import __version__; print(__version__)"

# 更新依赖
pip install -r requirements.txt --upgrade
```

---

## 📞 技术支持

如遇到问题，请检查：

1. **日志文件**: `logs/` 目录下的相关日志
2. **健康检查**: 所有服务的健康检查端点
3. **端口状态**: 确认所有必要端口已开放
4. **依赖版本**: 确认所有Python包版本兼容

更多信息请参考[MCP官方文档](https://github.com/modelcontextprotocol/modelcontextprotocol)。

# MCP 服务集成指南

## 📝 概述

本指南介绍如何将加密货币分析系统与MCP (Model Context Protocol) 协议集成，为AI系统提供强大的数据查询和预警功能。

## 🏗️ 系统架构

### 核心组件
- **MCP工具层**: 提供标准化的工具接口
- **查询引擎**: 执行复杂的数据查询逻辑
- **预警管理器**: 处理预警规则和触发机制
- **数据采集器**: 每分钟自动采集最新K线数据
- **响应格式化器**: 统一的响应格式和字段描述

### 数据流转
```
AI系统 → MCP工具 → 查询引擎/预警管理器 → MongoDB → 响应格式化 → AI系统
```

## 🔧 时间周期(Timeframes)系统

### 支持的时间周期
- `5m` - 5分钟K线
- `15m` - 15分钟K线  
- `1h` - 1小时K线
- `4h` - 4小时K线
- `1d` - 日线

### 在查询中使用Timeframes
所有MCP工具都支持`timeframes`参数：

```python
# 查询多个时间周期
arguments = {
    "symbol": "BTC",
    "timeframes": ["15m", "1h", "4h"],  # 指定要查询的时间周期
    "conditions": {...}
}
```

### 数据采集和timeframes
- **自动采集**: 系统每分钟自动采集所有配置的时间周期数据
- **增量更新**: 只存储新的数据，避免重复
- **实时计算**: 新数据采集后自动计算技术指标和信号

## 📊 字段描述系统

### 响应格式标准化
所有MCP工具响应都包含详细的字段描述：

```json
{
  "success": true,
  "request_id": "req_xxx",
  "data": {
    "processed_data": "具体数据内容"
  },
  "field_descriptions": {
    "symbol": "加密货币交易对符号，如BTC、ETH等",
    "timeframe": "K线时间周期，如5m、1h、1d等",
    "timestamp": "数据时间戳，ISO 8601格式",
    "close": "收盘价格，以USDT计价",
    "volume": "成交量，表示该时间段内的交易量",
    "rsi": "RSI相对强弱指数，范围0-100，用于判断超买超卖",
    "macd": "MACD指标对象，包含主线、信号线和柱状图数据"
  },
  "message": "操作描述",
  "timestamp": "响应时间戳"
}
```

### 字段描述常量
系统提供统一的字段描述常量，确保一致性：

```python
from utils.request_utils import FIELD_DESCRIPTIONS

# 获取字段描述
price_desc = FIELD_DESCRIPTIONS["close"]  # "收盘价格，以USDT计价"
rsi_desc = FIELD_DESCRIPTIONS["rsi"]      # "RSI相对强弱指数..."
```

## 🛠️ MCP工具详细说明

### 1. 查询工具 (CryptoSignalTools)

#### query_crypto_signals
查询技术信号，支持多时间周期过滤。

**timeframes参数使用**：
```json
{
  "symbol": "BTC",
  "timeframes": ["5m", "1h"],     // 只查询这两个时间周期
  "limit": 10
}
```

**响应包含的字段描述**：
- 完整的技术指标字段说明
- 信号类型和含义解释
- 时间周期相关说明

#### flexible_crypto_query
灵活的数据查询工具，支持复杂条件。

**多时间周期查询示例**：
```json
{
  "symbol": "ETH", 
  "timeframes": ["15m", "1d"],    // 同时查询15分钟和日线数据
  "conditions": {
    "field": "rsi",
    "operator": "between",
    "value": [20, 80]
  }
}
```

### 2. 预警工具 (AlertMCPTools)

#### create_price_alert
创建价格预警，支持多时间周期监控。

**timeframes在预警中的作用**：
```json
{
  "name": "BTC多周期监控", 
  "symbol": "BTC",
  "timeframes": ["1h", "4h"],     // 在这两个时间周期上监控价格
  "price_threshold": 110000,
  "condition": "above"
}
```

#### create_signal_alert  
创建信号预警，可指定特定时间周期的信号。

#### get_alert_statistics
获取预警统计，响应包含详细的字段描述。

## 🔄 数据采集集成

### 自动数据采集
系统通过`install_and_start.sh`启动后：

1. **每分钟采集**: 自动从交易所获取最新K线数据
2. **多时间周期**: 同时采集所有配置的时间周期
3. **增量存储**: 只存储新的数据，避免重复
4. **实时计算**: 新数据后立即计算技术指标和信号

### 采集配置
```python
# config/settings.py
TIMEFRAMES = ["5m", "15m", "1h", "4h", "1d"]  # 采集的时间周期
SYMBOLS = ["BTC/USDT", "ETH/USDT"]             # 采集的交易对
```

### 采集触发的后续处理
```python
# 数据采集完成后自动执行
def on_new_data_collected(symbol: str, timeframe: str):
    # 1. 计算技术指标
    indicator_calculator.calculate_indicators_for_symbol_timeframe(symbol, timeframe)
    
    # 2. 检测交易信号  
    signal_detector.detect_signals_for_symbol_timeframe(symbol, timeframe)
    
    # 3. 检查预警触发
    alert_manager.check_alerts_for_symbol_timeframe(symbol, timeframe)
```

## 🚀 部署和启动

### 一键启动
```bash
# 启动所有服务，包含数据采集
bash install_and_start.sh
```

### 服务端口分配
- **查询API**: `http://localhost:5000`
- **预警API**: `http://localhost:5001`  
- **MCP服务**: `ws://localhost:8080`
- **外部预警推送**: `http://localhost:8081/webhook/alert/trigger`

### 健康检查
```bash
# 检查各服务状态
curl http://localhost:5000/api/v1/health     # 查询API
curl http://localhost:5001/api/v1/alerts/health  # 预警API
```

## 🔍 调试和监控

### 日志级别
- **数据采集**: INFO级别，显示采集进度
- **指标计算**: DEBUG级别，显示计算详情
- **预警触发**: INFO级别，显示触发情况
- **MCP工具**: DEBUG级别，显示工具执行

### 常见问题

#### timeframes相关
1. **查询无结果**: 确认指定的时间周期有数据
2. **预警未触发**: 检查预警规则中的时间周期设置
3. **数据延迟**: 确认数据采集服务正常运行

#### 字段描述相关
1. **字段缺少描述**: 检查ResponseFormatter的使用
2. **描述不准确**: 更新FIELD_DESCRIPTIONS常量

## 📈 性能优化

### 查询优化
- 指定具体的timeframes减少查询范围
- 使用合理的limit限制返回数据量
- 善用索引优化查询性能

### 数据采集优化
- 增量采集避免重复数据
- 批量处理提高效率
- 异步计算技术指标和信号

## 🔐 安全考虑

### API访问控制
- 本地服务默认只监听localhost
- 生产环境建议配置防火墙规则
- 可通过配置文件修改监听地址

### 数据验证
- 所有MCP工具输入都经过验证
- 防止SQL注入和NoSQL注入
- 限制查询结果大小防止资源耗尽

## 🧪 测试和验证

### 功能测试
```bash
# 运行完整测试套件
python test_alert_system.py              # 预警系统测试
python test_data_collection.py           # 数据采集测试
python test_mcp_with_timeframes.py       # MCP timeframes测试
```

### 集成测试
- 验证MCP工具的timeframes参数
- 检查响应字段描述完整性
- 测试数据采集和计算流程 