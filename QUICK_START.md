# 🚀 快速启动指南

## 端口配置总览

| 服务 | 端口 | 协议 | 用途 |
|------|------|------|------|
| RESTful API | **5000** | HTTP | Web API接口 |
| MCP WebSocket | **8080** | WebSocket | AI Agent连接 |
| MCP健康检查 | **8081** | HTTP | 服务监控 |

## 一键启动所有服务

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动MongoDB
mongod

# 3. 启动所有服务
python start_all_services.py
```

## 快速验证

```bash
# API健康检查
curl http://localhost:5000/api/v1/health

# MCP健康检查
curl http://localhost:8081/health

# 测试MCP服务
python mcp/test_mcp_client.py
```

## 单独启动服务

```bash
# 只启动MCP服务
python start_all_services.py --skip-collector --skip-api

# 只启动API服务
python start_all_services.py --skip-mcp

# 自定义端口
python start_all_services.py --api-port 8000 --mcp-port 9000
```

更多详细信息请查看 [MCP_SERVICES_GUIDE.md](MCP_SERVICES_GUIDE.md) 