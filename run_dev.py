#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
开发环境启动脚本
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 强制使用开发环境配置
os.environ['FLASK_CONFIG'] = 'development'
os.environ['FLASK_DEBUG'] = 'true'

from app import create_app

# 创建Flask应用实例
app = create_app('development')

if __name__ == '__main__':
    # 开发环境启动参数
    app.run(
        host='127.0.0.1',  # 只允许本地访问
        port=5000,
        debug=True,
        use_reloader=True,  # 自动重载
        use_debugger=True   # 启用调试器
    ) 