#!/usr/bin/env python3
"""
统一启动所有服务
"""
import subprocess
import time
import signal
import sys
import logging
import argparse
from multiprocessing import Process

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceManager:
    def __init__(self):
        self.processes = []
    
    def start_service(self, script_name, service_name, extra_args=None):
        """启动单个服务"""
        try:
            logger.info(f"启动 {service_name}...")
            
            cmd = [sys.executable, script_name]
            if extra_args:
                cmd.extend(extra_args)
            
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            
            self.processes.append((process, service_name))
            logger.info(f"{service_name} 启动成功 (PID: {process.pid})")
            return process
            
        except Exception as e:
            logger.error(f"启动 {service_name} 失败: {e}")
            return None
    
    def start_all(self, skip_services=None):
        """启动所有服务"""
        logger.info("=== 启动加密货币技术分析和预警系统 ===")
        
        skip_services = skip_services or []
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # 启动各个服务
        services = [
            ("start_collector.py", "数据采集服务", None),
            ("start_api.py", "查询API服务 (5000)", ["--port", "5000"]),
            ("start_alerts.py", "预警API服务 (5001)", ["--port", "5001"]),
            ("start_mcp.py", "查询MCP服务 (8080)", ["--port", "8080"]),
        ]
        
        for script, name, args in services:
            service_key = script.replace('.py', '')
            if service_key not in skip_services:
                self.start_service(script, name, args)
                time.sleep(2)  # 服务启动间隔
            else:
                logger.info(f"跳过 {name}")
        
        logger.info("=== 所有服务启动完成 ===")
        logger.info("服务端口分配:")
        logger.info("  查询API服务:      http://localhost:5000")
        logger.info("  预警API服务:      http://localhost:5001")
        logger.info("  查询MCP服务:      ws://localhost:8080")
        logger.info("  预警MCP服务:      (集成在查询MCP中)")
        logger.info("")
        logger.info("健康检查端点:")
        logger.info("  查询API:         http://localhost:5000/api/v1/health")
        logger.info("  预警API:         http://localhost:5001/api/v1/alerts/health")
        logger.info("  查询MCP:         http://localhost:8081/health (如果启用)")
        logger.info("")
        logger.info("外部集成:")
        logger.info("  预警发送目标:     http://localhost:8081/webhook/alert/trigger")
        logger.info("")
        logger.info("按 Ctrl+C 停止所有服务")
        
        # 保持运行
        try:
            while True:
                # 检查进程状态
                for i, (process, name) in enumerate(self.processes):
                    if process.poll() is not None:
                        logger.warning(f"{name} 意外停止 (退出码: {process.returncode})")
                        # 可以在这里添加重启逻辑
                
                time.sleep(10)
                
        except KeyboardInterrupt:
            logger.info("收到停止信号...")
            self.stop_all()
    
    def stop_all(self):
        """停止所有服务"""
        logger.info("正在停止所有服务...")
        
        for process, name in self.processes:
            try:
                if process.poll() is None:
                    logger.info(f"停止 {name}...")
                    process.terminate()
                    process.wait(timeout=5)
                    logger.info(f"{name} 已停止")
            except subprocess.TimeoutExpired:
                logger.warning(f"强制杀死 {name}...")
                process.kill()
            except Exception as e:
                logger.error(f"停止 {name} 时出错: {e}")
        
        logger.info("所有服务已停止")
    
    def signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"收到信号 {signum}")
        self.stop_all()
        sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="启动所有服务")
    parser.add_argument(
        "--skip-collector",
        action="store_true",
        help="跳过数据采集服务"
    )
    parser.add_argument(
        "--skip-api",
        action="store_true",
        help="跳过查询API服务"
    )
    parser.add_argument(
        "--skip-alerts",
        action="store_true",
        help="跳过预警API服务"
    )
    parser.add_argument(
        "--skip-mcp",
        action="store_true",
        help="跳过MCP服务"
    )
    
    args = parser.parse_args()
    
    # 构建跳过服务列表
    skip_services = []
    if args.skip_collector:
        skip_services.append("start_collector")
    if args.skip_api:
        skip_services.append("start_api")
    if args.skip_alerts:
        skip_services.append("start_alerts")
    if args.skip_mcp:
        skip_services.append("start_mcp")
    
    manager = ServiceManager()
    manager.start_all(skip_services)

if __name__ == "__main__":
    main()
