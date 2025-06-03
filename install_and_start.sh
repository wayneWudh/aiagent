#!/bin/bash

#一键安装启动脚本
# 适用于 macOS 系统，如果迁移到Linux系统，需要修改部分命令，按环境修改配置文件即可，具体环境需要具体来看看。

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的信息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查操作系统
check_os() {
    print_info "检查操作系统..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        print_success "检测到 macOS 系统"
        OS="macos"
    else
        print_error "此脚本仅支持 macOS 系统"
        exit 1
    fi
}

# 安装 Homebrew
install_homebrew() {
    if ! command_exists brew; then
        print_info "安装 Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        print_success "Homebrew 安装完成"
    else
        print_success "Homebrew 已安装"
    fi
}

# 安装 Python
install_python() {
    print_info "检查 Python 环境..."
    
    if ! command_exists python3; then
        print_info "安装 Python 3..."
        brew install python@3.11
    fi
    
    # 检查 pip
    if ! command_exists pip3; then
        print_info "安装 pip..."
        python3 -m ensurepip --upgrade
    fi
    
    print_success "Python 环境检查完成"
}

# 安装 MongoDB
install_mongodb() {
    print_info "安装 MongoDB..."
    
    if ! command_exists mongod; then
        print_info "添加 MongoDB tap..."
        brew tap mongodb/brew
        
        print_info "安装 MongoDB Community Edition..."
        brew install mongodb-community
        
        # 创建数据目录
        sudo mkdir -p /usr/local/var/mongodb
        sudo mkdir -p /usr/local/var/log/mongodb
        sudo chown $(whoami) /usr/local/var/mongodb
        sudo chown $(whoami) /usr/local/var/log/mongodb
        
        print_success "MongoDB 安装完成"
    else
        print_success "MongoDB 已安装"
    fi
    
    # 启动 MongoDB 服务
    print_info "启动 MongoDB 服务..."
    brew services start mongodb-community
    
    # 等待 MongoDB 启动
    print_info "等待 MongoDB 启动..."
    sleep 5
    
    # 验证 MongoDB 连接
    if mongosh --eval "db.adminCommand('ping')" --quiet > /dev/null 2>&1; then
        print_success "MongoDB 服务启动成功"
    else
        print_error "MongoDB 启动失败"
        exit 1
    fi
}

# 创建虚拟环境
create_venv() {
    print_info "创建 Python 虚拟环境..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "虚拟环境创建完成"
    else
        print_success "虚拟环境已存在"
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    print_success "虚拟环境已激活"
}

# 安装 Python 依赖
install_python_deps() {
    print_info "安装 Python 依赖包..."
    
    # 升级 pip
    pip install --upgrade pip
    
    # 创建 requirements.txt 如果不存在
    if [ ! -f "requirements.txt" ]; then
        cat > requirements.txt << EOF
# 核心依赖
pymongo==4.6.0
ccxt==4.1.70
pandas==2.1.4
numpy==1.24.3
flask==3.0.0
flask-cors==4.0.0
requests==2.31.0
aiohttp==3.9.1
asyncio-mqtt==0.16.1

# 技术指标计算
ta-lib==0.4.28
talib==0.4.28

# 数据科学
scipy==1.11.4
scikit-learn==1.3.2

# 日志和配置
python-dotenv==1.0.0
pyyaml==6.0.1

# 异步处理
asyncio==3.4.3
uvloop==0.19.0

# Web服务
gunicorn==21.2.0
uvicorn==0.24.0

# MCP协议
websockets==12.0
pydantic==2.5.0

# 时间处理
python-dateutil==2.8.2
pytz==2023.3

# HTTP客户端
httpx==0.25.2

# 进程管理
supervisor==4.2.5
EOF
        print_success "requirements.txt 创建完成"
    fi
    
    # 安装依赖
    pip install -r requirements.txt
    
    # 如果 ta-lib 安装失败，尝试用 brew 安装
    if ! python -c "import talib" 2>/dev/null; then
        print_warning "ta-lib 安装失败，尝试通过 brew 安装..."
        brew install ta-lib
        pip install ta-lib
    fi
    
    print_success "Python 依赖安装完成"
}

# 创建配置文件
create_config() {
    print_info "创建配置文件..."
    
    # 创建目录结构
    mkdir -p config logs
    
    # 创建主配置文件
    if [ ! -f "config/settings.py" ]; then
        cat > config/settings.py << 'EOF'
"""
系统配置文件
"""
import os
from datetime import timedelta

# 基础配置
PROJECT_NAME = "SignalAgent"
VERSION = "1.0.0"
DEBUG = True

# MongoDB配置
MONGODB_CONFIG = {
    'host': 'localhost',
    'port': 27017,
    'database': 'crypto_signals',
    'collection': 'klines',
    'username': '',
    'password': ''
}

# 交易所配置
EXCHANGE_CONFIG = {
    'exchange': 'binance',
    'sandbox': False,
    'rateLimit': 1200,
    'timeout': 30000,
    'retries': 3
}

# 币种配置
SYMBOLS = ['BTC/USDT', 'ETH/USDT']
SYMBOL_MAPPING = {
    'BTC/USDT': 'BTC',
    'ETH/USDT': 'ETH'
}

# 时间周期配置
TIMEFRAMES = ['5m', '15m', '1h', '1d']

# 历史数据限制
HISTORICAL_LIMIT = 500

# API配置
API_CONFIG = {
    'host': '0.0.0.0',
    'port': 5001,
    'debug': True
}

# MCP配置
MCP_CONFIG = {
    'websocket_port': 8080,
    'health_port': 8081,
    'host': '0.0.0.0'
}

# 预警配置
ALERT_CONFIG = {
    'check_interval': 60,  # 检查间隔（秒）
    'max_alerts_per_day': 100,
    'webhook_timeout': 30
}

# Lark Webhook配置
LARK_WEBHOOK_URL = "https://open.larksuite.com/open-apis/bot/v2/hook/2691e416-0374-4181-b195-9e1de11968da"

# 日志配置
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'level': 'INFO'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.log',
            'maxBytes': 10485760,
            'backupCount': 5,
            'formatter': 'default',
            'level': 'DEBUG'
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

# 数据采集配置
COLLECTOR_CONFIG = {
    'update_interval': 300,  # 5分钟
    'batch_size': 100,
    'retry_attempts': 3,
    'retry_delay': 5
}

# 技术指标配置
INDICATOR_CONFIG = {
    'ma_periods': [5, 10, 20, 50, 100, 200],
    'rsi_period': 14,
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    'bb_period': 20,
    'bb_std': 2,
    'kdj_period': 9,
    'stoch_k': 14,
    'stoch_d': 3,
    'cci_period': 14
}
EOF
        print_success "配置文件创建完成"
    else
        print_success "配置文件已存在"
    fi
    
    # 创建 __init__.py 文件
    touch config/__init__.py
}

# 创建启动脚本
create_start_scripts() {
    print_info "创建启动脚本..."
    
    # 创建数据采集启动脚本
    cat > start_collector.py << 'EOF'
#!/usr/bin/env python3
"""
数据采集服务启动脚本
"""
import logging
import time
import signal
import sys
from threading import Thread
from data_collector.ccxt_collector import data_collector
from indicators.calculator import indicator_calculator
from indicators.signals import signal_detector

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataCollectionService:
    def __init__(self):
        self.running = False
        
    def start(self):
        """启动数据采集服务"""
        self.running = True
        logger.info("数据采集服务启动中...")
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # 主循环
        while self.running:
            try:
                logger.info("开始数据采集...")
                
                # 采集最新数据
                success = data_collector.collect_latest_data()
                if success:
                    logger.info("数据采集成功")
                    
                    # 计算技术指标
                    indicator_calculator.calculate_all_indicators()
                    logger.info("技术指标计算完成")
                    
                    # 检测交易信号
                    signal_detector.detect_all_signals()
                    logger.info("交易信号检测完成")
                    
                else:
                    logger.warning("数据采集失败")
                
                # 等待下次采集
                time.sleep(60)  # 1分钟
                
            except Exception as e:
                logger.error(f"数据采集过程中出错: {e}")
                time.sleep(60)  # 出错后等待1分钟
    
    def signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"收到信号 {signum}，正在关闭...")
        self.running = False
        sys.exit(0)

if __name__ == "__main__":
    service = DataCollectionService()
    service.start()
EOF
    
    # 创建API服务启动脚本
    cat > start_api.py << 'EOF'
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
EOF
    
    # 创建MCP服务启动脚本
    cat > start_mcp.py << 'EOF'
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
EOF
    
    # 创建预警服务启动脚本
    cat > start_alerts.py << 'EOF'
#!/usr/bin/env python3
"""
预警服务启动脚本
"""
import asyncio
import logging
import signal
import sys
from alerts.alert_manager import AlertManager
from config.settings import ALERT_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertService:
    def __init__(self):
        self.alert_manager = AlertManager()
        self.running = False
    
    async def start(self):
        """启动预警服务"""
        self.running = True
        logger.info("预警服务启动中...")
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # 启动预警监控
        await self.alert_manager.start_monitoring()
        
        # 主循环
        while self.running:
            try:
                await asyncio.sleep(ALERT_CONFIG['check_interval'])
            except asyncio.CancelledError:
                break
    
    def signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"收到信号 {signum}，正在关闭...")
        self.running = False

async def main():
    service = AlertService()
    await service.start()

if __name__ == "__main__":
    asyncio.run(main())
EOF
    
    # 创建统一启动脚本
    cat > start_all_services.py << 'EOF'
#!/usr/bin/env python3
"""
统一启动所有服务
"""
import subprocess
import time
import signal
import sys
import logging
from multiprocessing import Process

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceManager:
    def __init__(self):
        self.processes = []
    
    def start_service(self, script_name, service_name):
        """启动单个服务"""
        try:
            logger.info(f"启动 {service_name}...")
            process = subprocess.Popen([
                sys.executable, script_name
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes.append((process, service_name))
            logger.info(f"{service_name} 启动成功 (PID: {process.pid})")
            return process
            
        except Exception as e:
            logger.error(f"启动 {service_name} 失败: {e}")
            return None
    
    def start_all(self):
        """启动所有服务"""
        logger.info("=== 启动加密货币技术分析和预警系统 ===")
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # 启动各个服务
        services = [
            ("start_collector.py", "数据采集服务"),
            ("start_api.py", "API服务"),
            ("start_mcp.py", "MCP服务"),
            ("start_alerts.py", "预警服务")
        ]
        
        for script, name in services:
            self.start_service(script, name)
            time.sleep(2)  # 服务启动间隔
        
        logger.info("=== 所有服务启动完成 ===")
        logger.info("查询API服务: http://localhost:5000")
        logger.info("预警API服务: http://localhost:5001")
        logger.info("查询MCP服务: ws://localhost:8080")
        logger.info("外部预警推送目标: http://localhost:8081/webhook/alert/trigger")
        logger.info("按 Ctrl+C 停止所有服务")
        
        # 保持运行
        try:
            while True:
                # 检查进程状态
                for i, (process, name) in enumerate(self.processes):
                    if process.poll() is not None:
                        logger.warning(f"{name} 意外停止，重启中...")
                        # 重启服务逻辑可以在这里添加
                
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

if __name__ == "__main__":
    manager = ServiceManager()
    manager.start_all()
EOF
    
    # 设置执行权限
    chmod +x start_collector.py start_api.py start_mcp.py start_alerts.py start_all_services.py
    
    print_success "启动脚本创建完成"
}

# 初始化数据库
init_database() {
    print_info "初始化数据库..."
    
    # 创建数据库和集合
    mongosh << 'EOF'
use crypto_signals
db.createCollection("klines")
db.createCollection("alert_rules")
db.createCollection("alert_triggers")

// 创建索引
db.klines.createIndex({ "symbol": 1, "timeframe": 1, "timestamp": -1 })
db.klines.createIndex({ "timestamp": -1 })
db.klines.createIndex({ "signals": 1 })
db.alert_rules.createIndex({ "symbol": 1, "is_active": 1 })
db.alert_triggers.createIndex({ "rule_id": 1, "triggered_at": -1 })

print("数据库初始化完成")
EOF
    
    print_success "数据库初始化完成"
}

# 验证安装
verify_installation() {
    print_info "验证安装..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 检查Python包
    print_info "检查Python包..."
    python -c "
import pymongo
import ccxt
import pandas
import numpy
import flask
import requests
print('所有Python包导入成功')
"
    
    # 检查MongoDB连接
    print_info "检查MongoDB连接..."
    if mongosh --eval "db.adminCommand('ping')" --quiet > /dev/null 2>&1; then
        print_success "MongoDB连接正常"
    else
        print_error "MongoDB连接失败"
        return 1
    fi
    
    print_success "安装验证完成"
}

# 启动系统
start_system() {
    print_info "启动系统..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 后台启动所有服务
    nohup python start_all_services.py > logs/system.log 2>&1 &
    SYSTEM_PID=$!
    echo $SYSTEM_PID > system.pid
    
    print_success "系统启动完成"
    print_info "系统PID: $SYSTEM_PID"
    print_info "日志文件: logs/system.log"
    print_info "查询API服务: http://localhost:5000"
    print_info "预警API服务: http://localhost:5001"
    print_info "查询MCP服务: ws://localhost:8080"
    print_info "外部预警推送目标: http://localhost:8081/webhook/alert/trigger"
    
    # 等待服务启动
    print_info "等待服务启动..."
    sleep 10
    
    return 0
}

# 主函数
main() {
    echo "======================================================="
    echo "    加密货币技术分析和预警系统 - 一键安装启动脚本"
    echo "======================================================="
    echo ""
    
    # 检查是否在项目目录中
    if [ ! -f "test_complete_system.py" ]; then
        print_error "请在项目根目录中运行此脚本"
        exit 1
    fi
    
    # 执行安装步骤
    check_os
    install_homebrew
    install_python
    install_mongodb
    create_venv
    install_python_deps
    create_config
    create_start_scripts
    init_database
    
    # 验证安装
    if verify_installation; then
        print_success "安装完成！"
        
        # 启动系统
        if start_system; then
            print_success "系统启动成功！"
            
            echo ""
            echo "======================================================="
            echo "                    安装和启动完成"
            echo "======================================================="
            echo "查询API服务: http://localhost:5000"
            echo "预警API服务: http://localhost:5001"
            echo "查询MCP服务: ws://localhost:8080"
            echo "外部预警推送目标: http://localhost:8081/webhook/alert/trigger"
            echo "系统日志: logs/system.log"
            echo ""
            echo "常用命令:"
            echo "  查看系统状态: tail -f logs/system.log"
            echo "  停止系统: kill \$(cat system.pid)"
            echo "  重启系统: ./install_and_start.sh"
            echo ""
            echo "现在可以运行测试验证系统: python test_complete_system.py"
            echo "======================================================="
            
            return 0
        else
            print_error "系统启动失败"
            return 1
        fi
    else
        print_error "安装验证失败"
        return 1
    fi
}

# 运行主函数
main "$@" 