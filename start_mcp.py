#!/usr/bin/env python3
"""
MCP服务启动脚本
"""
import asyncio
import logging
from mcp.run_mcp import main as mcp_main

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("启动MCP服务...")
    asyncio.run(mcp_main())
