#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from app import create_app

# 创建Flask应用实例
app = create_app(os.getenv('FLASK_CONFIG') or 'development')

if __name__ == '__main__':
    # 安全修复：不再硬编码debug=True，从环境变量获取
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    
    app.run(host=host, port=port, debug=debug_mode) 