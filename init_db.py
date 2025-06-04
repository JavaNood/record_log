#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库初始化脚本
运行此脚本来初始化数据库表和基础数据
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import init_database, reset_database


def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == '--reset':
        # 重置数据库
        app = create_app('development')
        with app.app_context():
            reset_database()
    else:
        # 正常初始化
        app = create_app('development')
        with app.app_context():
            init_database()


if __name__ == '__main__':
    main() 