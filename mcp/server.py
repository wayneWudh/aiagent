"""
MCP服务器实现
基于Model Context Protocol规范的服务器实现
"""
import asyncio
import json
import logging
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
import websockets
from websockets.server import WebSocketServerProtocol
from .tools import CryptoSignalTools

logger = logging.getLogger(__name__)


class MCPServer:
    """Model Context Protocol 服务器"""
    
    def __init__(self, host: str = "localhost", port: int = 8080, api_base_url: str = "http://localhost:5000"):
        """
        初始化MCP服务器
        
        Args:
            host: 服务器地址
            port: 服务器端口
            api_base_url: API服务基础URL
        """
        self.host = host
        self.port = port
        self.tools = CryptoSignalTools(api_base_url)
        self.connected_clients: Dict[WebSocketServerProtocol, str] = {}
        
        # MCP协议版本
        self.protocol_version = "1.0.0"
        self.server_info = {
            "name": "crypto-signal-mcp-server",
            "version": "1.0.0",
            "description": "加密货币技术信号分析MCP服务器",
            "author": "Crypto Signal Analysis Team",
            "capabilities": {
                "tools": True,
                "prompts": False,
                "resources": False
            }
        }
    
    async def start_server(self):
        """启动MCP服务器"""
        logger.info(f"启动MCP服务器 {self.host}:{self.port}")
        
        try:
            async with websockets.serve(
                self.handle_client,
                self.host,
                self.port,
                ping_interval=30,
                ping_timeout=10
            ):
                logger.info(f"🎯 MCP服务器已启动: ws://{self.host}:{self.port}")
                logger.info(f"📋 可用工具数量: {len(self.tools.get_tool_definitions())}")
                logger.info("等待AI Agent连接...")
                
                # 保持服务器运行
                await asyncio.Future()  # 永远等待
                
        except Exception as e:
            logger.error(f"启动MCP服务器失败: {e}")
            raise
    
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """处理客户端连接"""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        self.connected_clients[websocket] = client_id
        
        logger.info(f"新的AI Agent连接: {client_id}")
        
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"AI Agent断开连接: {client_id}")
        except Exception as e:
            logger.error(f"处理客户端消息时发生错误: {e}")
        finally:
            if websocket in self.connected_clients:
                del self.connected_clients[websocket]
    
    async def handle_message(self, websocket: WebSocketServerProtocol, message: str):
        """处理来自客户端的消息"""
        try:
            data = json.loads(message)
            request_id = data.get("id", "unknown")
            method = data.get("method")
            params = data.get("params", {})
            
            logger.debug(f"收到请求: {method}, ID: {request_id}")
            
            # 处理不同的MCP方法
            if method == "initialize":
                response = await self.handle_initialize(params)
            elif method == "tools/list":
                response = await self.handle_tools_list()
            elif method == "tools/call":
                response = await self.handle_tools_call(params)
            elif method == "ping":
                response = {"result": "pong"}
            else:
                response = {
                    "error": {
                        "code": -32601,
                        "message": f"方法未找到: {method}"
                    }
                }
            
            # 发送响应
            response["id"] = request_id
            response["jsonrpc"] = "2.0"
            
            await websocket.send(json.dumps(response))
            
        except json.JSONDecodeError:
            error_response = {
                "id": None,
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "解析错误: 无效的JSON"
                }
            }
            await websocket.send(json.dumps(error_response))
            
        except Exception as e:
            logger.error(f"处理消息时发生错误: {e}")
            error_response = {
                "id": data.get("id") if 'data' in locals() else None,
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"内部错误: {str(e)}"
                }
            }
            await websocket.send(json.dumps(error_response))
    
    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理初始化请求"""
        client_info = params.get("clientInfo", {})
        client_name = client_info.get("name", "Unknown Client")
        client_version = client_info.get("version", "Unknown")
        
        logger.info(f"初始化连接: {client_name} v{client_version}")
        
        return {
            "result": {
                "protocolVersion": self.protocol_version,
                "serverInfo": self.server_info,
                "capabilities": self.server_info["capabilities"]
            }
        }
    
    async def handle_tools_list(self) -> Dict[str, Any]:
        """处理工具列表请求"""
        tools = self.tools.get_tool_definitions()
        
        logger.debug(f"返回工具列表，共 {len(tools)} 个工具")
        
        return {
            "result": {
                "tools": tools
            }
        }
    
    async def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理工具调用请求"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        logger.info(f"执行工具调用: {tool_name}")
        logger.debug(f"工具参数: {arguments}")
        
        try:
            # 执行工具
            result = await self.tools.execute_tool(tool_name, arguments)
            
            # 格式化结果为MCP响应格式
            if result.get("error"):
                return {
                    "error": {
                        "code": -32000,
                        "message": result["message"],
                        "data": {
                            "tool_name": tool_name,
                            "arguments": arguments
                        }
                    }
                }
            else:
                return {
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, ensure_ascii=False, indent=2)
                            }
                        ],
                        "isError": False
                    }
                }
                
        except Exception as e:
            logger.error(f"工具执行失败: {e}")
            return {
                "error": {
                    "code": -32000,
                    "message": f"工具执行失败: {str(e)}",
                    "data": {
                        "tool_name": tool_name,
                        "arguments": arguments
                    }
                }
            }
    
    def get_server_info(self) -> Dict[str, Any]:
        """获取服务器信息"""
        return {
            "server_info": self.server_info,
            "host": self.host,
            "port": self.port,
            "protocol_version": self.protocol_version,
            "connected_clients": len(self.connected_clients),
            "available_tools": len(self.tools.get_tool_definitions()),
            "status": "running"
        }


# 简化的HTTP服务器用于健康检查
class MCPHealthServer:
    """MCP健康检查HTTP服务器"""
    
    def __init__(self, mcp_server: MCPServer, http_port: int = 8081):
        self.mcp_server = mcp_server
        self.http_port = http_port
    
    async def start_health_server(self):
        """启动健康检查HTTP服务器"""
        from aiohttp import web, web_runner
        
        app = web.Application()
        app.router.add_get('/health', self.health_check)
        app.router.add_get('/status', self.server_status)
        
        runner = web_runner.AppRunner(app)
        await runner.setup()
        
        site = web_runner.TCPSite(runner, 'localhost', self.http_port)
        await site.start()
        
        logger.info(f"MCP健康检查服务启动: http://localhost:{self.http_port}/health")
    
    async def health_check(self, request):
        """健康检查端点"""
        from aiohttp import web
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "mcp_server": self.mcp_server.get_server_info()
        }
        
        return web.json_response(health_data)
    
    async def server_status(self, request):
        """服务器状态端点"""
        from aiohttp import web
        
        status_data = self.mcp_server.get_server_info()
        return web.json_response(status_data) 