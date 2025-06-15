#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
开发环境启动脚本
"""

import os
from app import create_app

if __name__ == '__main__':
    # 设置开发环境配置
    os.environ['FLASK_CONFIG'] = 'development'
    
    # 创建Flask应用
    app = create_app('development')
    
    # 启动开发服务器
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        threaded=True
    ) 