"""
Flask API应用主文件
创建和配置Flask应用
"""
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from .routes import api_bp
from alerts.api_routes import alerts_bp
from utils.logger import setup_logging


def create_app(config=None):
    """
    创建Flask应用实例
    
    Args:
        config: 配置对象
        
    Returns:
        Flask: 配置好的Flask应用实例
    """
    # 创建Flask应用
    app = Flask(__name__)
    
    # 基础配置
    app.config.update({
        'JSON_AS_ASCII': False,  # 支持中文
        'JSONIFY_PRETTYPRINT_REGULAR': True,  # JSON格式化
        'JSON_SORT_KEYS': False,  # 保持JSON字段顺序
    })
    
    # 如果有自定义配置，应用它
    if config:
        app.config.update(config)
    
    # 设置日志
    setup_logging()
    
    # 启用CORS（跨域请求支持）
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # 注册蓝图
    app.register_blueprint(api_bp)
    app.register_blueprint(alerts_bp)  # 添加预警系统API
    
    # 根路径处理
    @app.route('/')
    def index():
        """API根路径"""
        return jsonify({
            'name': '加密货币技术信号查询API',
            'version': 'v1.0.0',
            'status': 'running',
            'description': '提供加密货币技术分析信号的RESTful API服务',
            'endpoints': {
                'health': '/api/v1/health',
                'signals_post': '/api/v1/signals',
                'signals_get': '/api/v1/signals/<symbol>',
                'symbols': '/api/v1/symbols',
                'docs': '/api/v1/docs',
                # 预警系统端点
                'alerts_health': '/api/v1/alerts/health',
                'alerts_query': '/api/v1/alerts/query',
                'alerts_rules': '/api/v1/alerts/rules',
                'alerts_webhook_test': '/api/v1/alerts/webhook/test',
                'alerts_stats': '/api/v1/alerts/stats'
            },
            'documentation': '/api/v1/docs'
        })
    
    # 全局错误处理
    @app.errorhandler(Exception)
    def handle_exception(e):
        """处理未捕获的异常"""
        logger = logging.getLogger(__name__)
        logger.error(f"未捕获的异常: {e}", exc_info=True)
        
        return jsonify({
            'success': False,
            'message': '服务器内部错误',
            'error_code': 'INTERNAL_SERVER_ERROR',
            'details': {'error': str(e)}
        }), 500
    
    return app


if __name__ == '__main__':
    # 开发模式运行
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True) 