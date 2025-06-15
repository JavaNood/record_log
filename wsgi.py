#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WSGI 入口文件 - 用于生产环境部署
支持多进程、性能监控和错误处理
"""

import os
import sys
import logging

# 确保当前目录在Python路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 生产环境性能优化
if os.environ.get('FLASK_CONFIG') == 'production':
    # 设置线程数限制
    os.environ.setdefault('OMP_NUM_THREADS', '2')
    # 内存优化
    import gc
    gc.set_threshold(700, 10, 10)

from app import create_app

# 根据环境变量决定配置
config_name = os.environ.get('FLASK_CONFIG') or 'production'

try:
    # 创建应用实例
    application = create_app(config_name)
    
    # 生产环境性能监控
    if config_name == 'production':
        from flask import request
        
        @application.before_request
        def log_request_info():
            """记录请求信息用于性能监控"""
            if application.config.get('LOG_TO_FILE'):
                application.logger.debug(f'Request: {request.method} {request.url}')
        
        @application.after_request
        def log_response_info(response):
            """记录响应信息"""
            if response.status_code >= 400:
                application.logger.warning(f'Response: {response.status_code} for {request.url}')
            return response
        
        # 错误处理
        @application.errorhandler(500)
        def internal_error(error):
            """记录500错误"""
            application.logger.error(f'Server Error: {error}', exc_info=True)
            return "Internal server error", 500
            
        @application.errorhandler(404)
        def not_found_error(error):
            """记录404错误"""
            application.logger.warning(f'Page not found: {request.url}')
            return "Page not found", 404

except Exception as e:
    # 应用创建失败时的错误处理
    logging.error(f"Failed to create application: {e}")
    # 创建一个简单的错误应用
    from flask import Flask
    application = Flask(__name__)
    
    @application.route('/')
    def error_page():
        return "Application configuration error. Please check server logs.", 500

if __name__ == '__main__':
    application.run() 