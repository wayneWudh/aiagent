#!/usr/bin/env python3
"""
API服务启动脚本
"""
import logging
from api.app import create_app
from config.settings import API_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """启动API服务"""
    app = create_app()
    
    logger.info(f"启动API服务在 http://{API_CONFIG['host']}:{API_CONFIG['port']}")
    
    app.run(
        host=API_CONFIG['host'],
        port=API_CONFIG['port'],
        debug=API_CONFIG['debug'],
        threaded=True
    )

if __name__ == "__main__":
    main()
