#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库更新脚本
用于在现有数据库中添加新的SiteVisit表
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db


def update_database():
    """更新数据库表结构"""
    print("开始更新数据库...")
    
    try:
        # 导入新模型
        from app.models import SiteVisit
        
        # 创建新表
        print("创建SiteVisit访问统计表...")
        db.create_all()
        
        print("✅ 数据库更新成功！")
        print("新增了网站访问统计功能，可以在后台管理中查看访问数据。")
        
    except Exception as e:
        print(f"❌ 数据库更新失败: {str(e)}")
        return False
    
    return True


def main():
    """主函数"""
    app = create_app('development')
    with app.app_context():
        update_database()


if __name__ == '__main__':
    main() 