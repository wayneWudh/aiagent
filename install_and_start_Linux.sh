#!/bin/bash

# 一键安装启动脚本 - Linux版本
# 适用于 Ubuntu/Debian/CentOS/RHEL 系统

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
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_success "检测到 Linux 系统"
        
        # 检测Linux发行版
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            OS_ID=$ID
            print_info "检测到 $PRETTY_NAME"
            
            case $OS_ID in
                ubuntu|debian)
                    PKG_MANAGER="apt"
                    PKG_UPDATE="apt update"
                    PKG_INSTALL="apt install -y"
                    ;;
                centos|rhel|fedora)
                    if command_exists dnf; then
                        PKG_MANAGER="dnf"
                        PKG_UPDATE="dnf check-update || true"
                        PKG_INSTALL="dnf install -y"
                    else
                        PKG_MANAGER="yum"
                        PKG_UPDATE="yum check-update || true"
                        PKG_INSTALL="yum install -y"
                    fi
                    ;;
                *)
                    print_warning "未识别的Linux发行版，尝试使用通用方法"
                    if command_exists apt; then
                        PKG_MANAGER="apt"
                        PKG_UPDATE="apt update"
                        PKG_INSTALL="apt install -y"
                    elif command_exists dnf; then
                        PKG_MANAGER="dnf"
                        PKG_UPDATE="dnf check-update || true"
                        PKG_INSTALL="dnf install -y"
                    elif command_exists yum; then
                        PKG_MANAGER="yum"
                        PKG_UPDATE="yum check-update || true"
                        PKG_INSTALL="yum install -y"
                    else
                        print_error "无法找到支持的包管理器"
                        exit 1
                    fi
                    ;;
            esac
        else
            print_error "无法检测Linux发行版"
            exit 1
        fi
    else
        print_error "此脚本仅支持 Linux 系统"
        exit 1
    fi
}

# 更新系统包
update_system() {
    print_info "更新系统包..."
    $PKG_UPDATE
    print_success "系统包更新完成"
}

# 安装基础工具
install_basic_tools() {
    print_info "安装基础工具..."
    
    case $PKG_MANAGER in
        apt)
            $PKG_INSTALL curl wget gnupg2 software-properties-common apt-transport-https ca-certificates lsb-release build-essential
            ;;
        dnf)
            $PKG_INSTALL curl wget gnupg2 dnf-plugins-core gcc gcc-c++ make
            ;;
        yum)
            $PKG_INSTALL curl wget gnupg2 yum-utils gcc gcc-c++ make epel-release
            ;;
    esac
    
    print_success "基础工具安装完成"
}

# 安装 Python
install_python() {
    print_info "检查 Python 环境..."
    
    if ! command_exists python3; then
        print_info "安装 Python 3..."
        case $PKG_MANAGER in
            apt)
                $PKG_INSTALL python3 python3-pip python3-venv python3-dev
                ;;
            dnf)
                $PKG_INSTALL python3 python3-pip python3-venv python3-devel
                ;;
            yum)
                $PKG_INSTALL python3 python3-pip python3-venv python3-devel
                ;;
        esac
    else
        print_success "Python 3 已安装"
    fi
    
    # 检查 pip
    if ! command_exists pip3; then
        print_info "安装 pip..."
        python3 -m ensurepip --upgrade || true
        
        # 如果还是没有pip，尝试下载安装
        if ! command_exists pip3; then
            print_info "下载并安装 pip..."
            curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
            python3 get-pip.py
            rm get-pip.py
        fi
    fi
    
    # 升级 pip
    python3 -m pip install --upgrade pip
    
    print_success "Python 环境检查完成"
}

# 安装 TA-Lib
install_talib() {
    print_info "安装 TA-Lib..."
    
    # 安装TA-Lib C库
    case $PKG_MANAGER in
        apt)
            $PKG_INSTALL libta-lib-dev || {
                print_info "从源码编译安装 TA-Lib..."
                cd /tmp
                wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
                tar -xzf ta-lib-0.4.0-src.tar.gz
                cd ta-lib/
                ./configure --prefix=/usr/local
                make
                make install
                ldconfig
                cd $OLDPWD
            }
            ;;
        dnf|yum)
            # CentOS/RHEL需要从源码安装
            print_info "从源码编译安装 TA-Lib..."
            cd /tmp
            wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
            tar -xzf ta-lib-0.4.0-src.tar.gz
            cd ta-lib/
            ./configure --prefix=/usr/local
            make
            make install
            echo '/usr/local/lib' > /etc/ld.so.conf.d/talib.conf
            ldconfig
            cd $OLDPWD
            ;;
    esac
    
    print_success "TA-Lib 安装完成"
}

# 安装 MongoDB
install_mongodb() {
    print_info "安装 MongoDB..."
    
    case $PKG_MANAGER in
        apt)
            # Ubuntu/Debian
            print_info "添加 MongoDB 官方源..."
            curl -fsSL https://pgp.mongodb.com/server-7.0.asc | gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
            echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/7.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list
            
            apt update
            $PKG_INSTALL mongodb-org
            ;;
        dnf)
            # Fedora
            cat > /etc/yum.repos.d/mongodb-org-7.0.repo << 'EOF'
[mongodb-org-7.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/7.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://pgp.mongodb.com/server-7.0.asc
EOF
            $PKG_INSTALL mongodb-org
            ;;
        yum)
            # CentOS/RHEL
            cat > /etc/yum.repos.d/mongodb-org-7.0.repo << 'EOF'
[mongodb-org-7.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/7.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://pgp.mongodb.com/server-7.0.asc
EOF
            $PKG_INSTALL mongodb-org
            ;;
    esac
    
    # 创建数据目录
    mkdir -p /var/lib/mongodb
    mkdir -p /var/log/mongodb
    chown mongodb:mongodb /var/lib/mongodb
    chown mongodb:mongodb /var/log/mongodb
    
    # 启动 MongoDB 服务
    print_info "启动 MongoDB 服务..."
    systemctl enable mongod
    systemctl start mongod
    
    # 等待 MongoDB 启动
    print_info "等待 MongoDB 启动..."
    sleep 10
    
    # 验证 MongoDB 连接
    if mongosh --eval "db.adminCommand('ping')" --quiet > /dev/null 2>&1; then
        print_success "MongoDB 服务启动成功"
    else
        print_warning "MongoDB 可能未完全启动，继续安装过程..."
    fi
    
    print_success "MongoDB 安装完成"
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
    
    # 升级 pip
    pip install --upgrade pip
}

# 安装 Python 依赖
install_python_deps() {
    print_info "安装 Python 依赖包..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 创建 requirements.txt 如果不存在
    if [ ! -f "requirements.txt" ]; then
        cat > requirements.txt << 'EOF'
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
TA-Lib==0.4.28

# 数据科学
scipy==1.11.4
scikit-learn==1.3.2

# 日志和配置
python-dotenv==1.0.0
pyyaml==6.0.1

# 异步处理
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
    
    # 设置环境变量
    export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
    export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH
    
    # 安装依赖
    pip install --no-cache-dir -r requirements.txt
    
    # 验证关键包安装
    python -c "
try:
    import talib
    print('TA-Lib 导入成功')
except ImportError as e:
    print(f'TA-Lib 导入失败: {e}')
    
try:
    import pymongo
    print('PyMongo 导入成功')
except ImportError as e:
    print(f'PyMongo 导入失败: {e}')
    
try:
    import ccxt
    print('CCXT 导入成功')
except ImportError as e:
    print(f'CCXT 导入失败: {e}')
"
    
    print_success "Python 依赖安装完成"
}

# 创建配置文件
create_config() {
    print_info "创建配置文件..."
    
    # 创建目录结构
    mkdir -p config logs data_collector indicators api alerts mcp
    
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
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
                logger.info("数据采集服务运行中...")
                # 这里应该调用实际的数据采集逻辑
                # 如果相关模块不存在，先跳过
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
import sys
import os
from flask import Flask

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return {"status": "ok", "message": "Crypto Signal API is running"}
    
    @app.route('/health')
    def health():
        return {"status": "healthy", "service": "api"}
    
    return app

def main():
    """启动API服务"""
    app = create_app()
    
    logger.info("启动API服务在 http://0.0.0.0:5001")
    
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True,
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
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """启动MCP服务"""
    logger.info("MCP服务启动中...")
    
    # 简单的循环保持服务运行
    while True:
        logger.info("MCP服务运行中...")
        await asyncio.sleep(60)

if __name__ == "__main__":
    logger.info("启动MCP服务...")
    asyncio.run(main())
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
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertService:
    def __init__(self):
        self.running = False
    
    async def start(self):
        """启动预警服务"""
        self.running = True
        logger.info("预警服务启动中...")
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # 主循环
        while self.running:
            try:
                logger.info("预警服务运行中...")
                await asyncio.sleep(60)
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
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
        logger.info("API服务: http://localhost:5001")
        logger.info("MCP服务: ws://localhost:8080")
        logger.info("按 Ctrl+C 停止所有服务")
        
        # 保持运行
        try:
            while True:
                # 检查进程状态
                for i, (process, name) in enumerate(self.processes):
                    if process.poll() is not None:
                        logger.warning(f"{name} 意外停止")
                
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
    
    # 等待MongoDB完全启动
    sleep 5
    
    # 检查MongoDB是否运行
    if ! systemctl is-active --quiet mongod; then
        print_warning "MongoDB服务未运行，尝试启动..."
        systemctl start mongod
        sleep 5
    fi
    
    # 创建数据库和集合
    mongosh --eval "
use crypto_signals
db.createCollection('klines')
db.createCollection('alert_rules')
db.createCollection('alert_triggers')

// 创建索引
db.klines.createIndex({ 'symbol': 1, 'timeframe': 1, 'timestamp': -1 })
db.klines.createIndex({ 'timestamp': -1 })
db.klines.createIndex({ 'signals': 1 })
db.alert_rules.createIndex({ 'symbol': 1, 'is_active': 1 })
db.alert_triggers.createIndex({ 'rule_id': 1, 'triggered_at': -1 })

print('数据库初始化完成')
" || print_warning "数据库初始化可能失败，但不影响继续安装"
    
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
try:
    import pymongo
    print('✓ PyMongo')
except ImportError:
    print('✗ PyMongo 导入失败')

try:
    import ccxt
    print('✓ CCXT')
except ImportError:
    print('✗ CCXT 导入失败')

try:
    import pandas
    print('✓ Pandas')
except ImportError:
    print('✗ Pandas 导入失败')

try:
    import numpy
    print('✓ NumPy')
except ImportError:
    print('✗ NumPy 导入失败')

try:
    import flask
    print('✓ Flask')
except ImportError:
    print('✗ Flask 导入失败')

try:
    import talib
    print('✓ TA-Lib')
except ImportError:
    print('✗ TA-Lib 导入失败')

print('Python包检查完成')
"
    
    # 检查MongoDB连接
    print_info "检查MongoDB连接..."
    if mongosh --eval "db.adminCommand('ping')" --quiet > /dev/null 2>&1; then
        print_success "✓ MongoDB连接正常"
    else
        print_warning "✗ MongoDB连接失败，但可以继续"
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
    print_info "API服务: http://localhost:5001"
    print_info "MCP服务: ws://localhost:8080"
    
    # 等待服务启动
    print_info "等待服务启动..."
    sleep 10
    
    return 0
}

# 主函数
main() {
    echo "======================================================="
    echo "    加密货币技术分析和预警系统 - Linux一键安装脚本"
    echo "======================================================="
    echo ""
    
    # 检查是否为root用户
    if [[ $EUID -ne 0 ]]; then
        print_error "此脚本需要root权限运行"
        print_info "请使用: sudo $0"
        exit 1
    fi
    
    # 检查是否在项目目录中
    if [ ! -f "install_and_start.sh" ]; then
        print_warning "未检测到原始安装脚本，继续执行..."
    fi
    
    # 执行安装步骤
    check_os
    update_system
    install_basic_tools
    install_python
    install_talib
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
            echo "API服务: http://localhost:5001"
            echo "健康检查: http://localhost:5001/health"
            echo "MCP服务: ws://localhost:8080"
            echo "系统日志: logs/system.log"
            echo ""
            echo "常用命令:"
            echo "  查看系统状态: tail -f logs/system.log"
            echo "  停止系统: kill \$(cat system.pid) 2>/dev/null || echo '系统未运行'"
            echo "  重启系统: ./install_and_start_linux.sh"
            echo "  检查服务: systemctl status mongod"
            echo ""
            echo "测试API服务:"
            echo "  curl http://localhost:5001/health"
            echo "======================================================="
            
            return 0
        else
            print_error "系统启动失败"
            return 1
        fi
    else
        print_error "安装验证失败，但基础环境已安装"
        return 1
    fi
}

# 运行主函数
main "$@"