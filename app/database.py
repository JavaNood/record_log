#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库初始化脚本
用于创建表结构、初始管理员账户和基本配置数据
"""

from flask import Flask
from . import create_app, db
from .models import Admin, Config
import os


def init_database():
    """初始化数据库"""
    print("开始初始化数据库...")
    
    # 创建所有表
    print("创建数据库表结构...")
    db.create_all()
    print("数据库表创建成功！")
    
    # 创建初始管理员账户
    print("创建初始管理员账户...")
    admin = Admin.query.filter_by(username='admin').first()
    if not admin:
        admin = Admin(
            username='admin',
            email='admin@example.com'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        print("管理员账户创建成功！用户名: admin, 密码: admin123")
    else:
        print("管理员账户已存在，跳过创建")
    
    # 初始化基本系统配置
    print("初始化系统配置...")
    configs = [
        ('site_title', '我的个人博客'),
        ('site_description', '记录生活，分享思考'),
        ('about_personal', '这里是个人介绍内容，可以在后台管理系统中修改。'),
        ('about_changelog', '# 版本更新日志\n\n## v1.0.0\n- 初始版本发布\n- 基础文章管理功能'),
        ('about_diary', '# 随手日记\n\n这里记录一些日常的想法和感悟。'),
        ('homepage_welcome', '欢迎来到我的个人博客！'),
        ('background_image', ''),  # 背景图片URL，默认为空
    ]
    
    for key, value in configs:
        existing_config = Config.query.get(key)
        if not existing_config:
            Config.set_value(key, value)
            print(f"配置项 {key} 创建成功")
        else:
            print(f"配置项 {key} 已存在，跳过创建")
    
    # 提交所有更改
    db.session.commit()
    print("数据库初始化完成！")


def reset_database():
    """重置数据库（删除所有表后重新创建）"""
    print("警告：即将重置数据库，所有数据将被删除！")
    
    # 删除所有表
    print("删除现有数据库表...")
    db.drop_all()
    print("数据库表删除完成")
    
    # 重新初始化
    init_database()


if __name__ == '__main__':
    # 创建应用上下文
    config_name = os.getenv('FLASK_CONFIG', 'development')
    print(f"使用配置环境: {config_name}")
    app = create_app(config_name)
    with app.app_context():
        init_database() 