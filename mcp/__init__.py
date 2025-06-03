"""
MCP (Model Context Protocol) 模块
为加密货币技术信号查询系统提供MCP协议封装
"""

from .server import MCPServer
from .tools import CryptoSignalTools

__all__ = ['MCPServer', 'CryptoSignalTools']

__version__ = '1.0.0' 