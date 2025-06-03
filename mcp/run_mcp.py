#!/usr/bin/env python3
"""
MCP服务器启动脚本
启动Model Context Protocol服务器
"""
import asyncio
import argparse
import logging
import sys
import signal
from .server import MCPServer, MCPHealthServer

def setup_logging(debug: bool = False):
    """设置日志"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/mcp_server.log')
        ]
    )

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='启动MCP服务器')
    parser.add_argument('--host', default='localhost', help='MCP服务器地址')
    parser.add_argument('--port', type=int, default=8080, help='MCP服务器端口')
    parser.add_argument('--health-port', type=int, default=8081, help='健康检查端口')
    parser.add_argument('--api-url', default='http://localhost:5000', help='API服务URL')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    
    try:
        # 创建MCP服务器
        mcp_server = MCPServer(
            host=args.host,
            port=args.port,
            api_base_url=args.api_url
        )
        
        # 创建健康检查服务器
        health_server = MCPHealthServer(mcp_server, args.health_port)
        
        # 设置信号处理
        def signal_handler(signum, frame):
            logger.info("收到停止信号，正在关闭MCP服务器...")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        print("🚀 启动加密货币技术信号MCP服务器...")
        print(f"🎯 MCP WebSocket服务: ws://{args.host}:{args.port}")
        print(f"❤️ 健康检查服务: http://localhost:{args.health_port}/health")
        print(f"📊 服务状态查询: http://localhost:{args.health_port}/status")
        print(f"🔧 调试模式: {'开启' if args.debug else '关闭'}")
        print("按 Ctrl+C 停止服务")
        
        # 同时启动两个服务器
        await asyncio.gather(
            mcp_server.start_server(),
            health_server.start_health_server()
        )
        
    except KeyboardInterrupt:
        logger.info("用户中断，正在关闭服务器...")
    except Exception as e:
        logger.error(f"启动MCP服务器失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main()) 