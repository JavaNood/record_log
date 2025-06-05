#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WSGI 入口文件 - 用于生产环境部署
"""

import os
import sys

# 确保当前目录在Python路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app import create_app

# 根据环境变量决定配置
config_name = os.environ.get('FLASK_CONFIG') or 'production'

# 创建应用实例
application = create_app(config_name)

if __name__ == '__main__':
    application.run() 