#!/usr/bin/env python3
"""
API服务器启动脚本
启动技术信号查询API服务
"""
import sys
import argparse
import logging
from api.app import create_app

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='启动加密货币技术信号查询API服务')
    parser.add_argument('--host', default='0.0.0.0', help='服务器地址 (默认: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='服务器端口 (默认: 5000)')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    
    args = parser.parse_args()
    
    try:
        # 创建Flask应用
        app = create_app()
        
        print(f"🚀 启动加密货币技术信号查询API服务...")
        print(f"📍 服务地址: http://{args.host}:{args.port}")
        print(f"📚 API文档: http://{args.host}:{args.port}/api/v1/docs")
        print(f"❤️ 健康检查: http://{args.host}:{args.port}/api/v1/health")
        print(f"🔧 调试模式: {'开启' if args.debug else '关闭'}")
        print("按 Ctrl+C 停止服务")
        
        # 启动服务器
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 收到停止信号，正在关闭API服务...")
    except Exception as e:
        logging.error(f"启动API服务失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 