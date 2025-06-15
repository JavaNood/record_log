#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库初始化和管理脚本
支持开发和生产环境，包含性能优化的索引
包含评论、点赞、发布地址等所有功能字段

使用方法：
python init_db.py --init        # 初始化数据库（创建表和初始数据）
python init_db.py --reset       # 重置数据库（删除所有数据并重新初始化）
python init_db.py --upgrade     # 升级数据库结构（仅添加缺失的表和字段）
python init_db.py --check       # 检查数据库状态
"""

import os
import sys
import argparse
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Admin, Config, Article, Tag, Comment, SiteVisit, Music
from app.utils import get_local_now
from sqlalchemy import text, inspect


def check_database_connection():
    """检查数据库连接是否正常"""
    try:
        print("🔍 检查数据库连接...")
        db.session.execute(text('SELECT 1'))
        print("✅ 数据库连接正常")
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        print("💡 请检查：")
        print("   - 数据库服务是否启动")
        print("   - 数据库配置是否正确（config.py）")
        print("   - 网络连接是否正常")
        return False


def check_table_exists(table_name):
    """检查表是否存在"""
    try:
        inspector = inspect(db.engine)
        return table_name in inspector.get_table_names()
    except Exception:
        return False


def get_database_status():
    """获取数据库状态信息"""
    status = {
        'tables': {},
        'data': {}
    }
    
    # 检查表存在情况
    tables = ['articles', 'tags', 'admins', 'site_config', 'comments', 'site_visits', 'article_tags', 'music']
    for table_name in tables:
        status['tables'][table_name] = check_table_exists(table_name)
    
    # 检查数据统计
    try:
        if status['tables'].get('articles'):
            status['data']['articles'] = db.session.execute(text("SELECT COUNT(*) FROM articles")).scalar() or 0
        if status['tables'].get('tags'):
            status['data']['tags'] = db.session.execute(text("SELECT COUNT(*) FROM tags")).scalar() or 0
        if status['tables'].get('admins'):
            status['data']['admins'] = db.session.execute(text("SELECT COUNT(*) FROM admins")).scalar() or 0
        if status['tables'].get('comments'):
            status['data']['comments'] = db.session.execute(text("SELECT COUNT(*) FROM comments")).scalar() or 0
        if status['tables'].get('site_visits'):
            status['data']['site_visits'] = db.session.execute(text("SELECT COUNT(*) FROM site_visits")).scalar() or 0
        if status['tables'].get('music'):
            status['data']['music'] = db.session.execute(text("SELECT COUNT(*) FROM music")).scalar() or 0
    except Exception as e:
        print(f"⚠️  获取数据统计时出错: {str(e)}")
    
    return status


def create_database_tables():
    """创建数据库表结构"""
    print("🔄 创建数据库表结构...")
    try:
        db.create_all()
        print("✅ 数据库表创建成功")
        return True
    except Exception as e:
        print(f"❌ 创建数据库表失败: {str(e)}")
        return False


def create_default_admin():
    """创建默认管理员账户"""
    print("🔄 创建默认管理员账户...")
    try:
        # 检查是否已存在管理员
        admin = Admin.query.filter_by(username='admin').first()
        if admin:
            print("ℹ️  管理员账户已存在，跳过创建")
            return True
        
        # 创建新管理员
        admin = Admin(
            username='admin',
            email='admin@myblog.com',
            created_at=get_local_now()
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        
        print("✅ 管理员账户创建成功")
        print("   用户名: admin")
        print("   密码: admin123")
        print("   ⚠️  请登录后立即修改密码！")
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 创建管理员账户失败: {str(e)}")
        return False


def create_default_configs():
    """创建默认系统配置"""
    print("🔄 创建默认系统配置...")
    try:
        configs = [
            ('site_title', '我的个人博客'),
            ('site_description', '记录生活，分享思考'),
            ('homepage_welcome_title', '欢迎来到我的个人博客'),
            ('homepage_welcome_subtitle', '记录生活，分享想法，探索世界'),
            ('background_type', 'preset'),
            ('background_preset', 'reading'),
            ('background_image', ''),
            ('background_time_based', 'False'),
            ('background_blur_level', '10'),
            ('background_fit_mode', 'cover'),
            ('background_animated_enabled', 'True'),
            ('background_animated_intensity', 'normal'),
            ('music_enabled', 'True'),
            ('music_auto_play', 'False'),
            ('music_default_volume', '0.5'),
        ]
        
        created_count = 0
        for key, value in configs:
            existing_config = Config.query.get(key)
            if not existing_config:
                config = Config(key_name=key, value=value)
                db.session.add(config)
                created_count += 1
        
        db.session.commit()
        print(f"✅ 系统配置创建成功（新增 {created_count} 项）")
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 创建系统配置失败: {str(e)}")
        return False


def create_default_tags():
    """创建默认标签"""
    print("🔄 创建默认标签...")
    try:
        default_tags = [
            ('技术', '#007bff'),
            ('生活', '#28a745'),
            ('随笔', '#17a2b8'),
            ('学习', '#ffc107'),
            ('项目', '#dc3545'),
        ]
        
        created_count = 0
        for name, color in default_tags:
            existing_tag = Tag.query.filter_by(name=name).first()
            if not existing_tag:
                tag = Tag(name=name, color=color, created_at=get_local_now())
                db.session.add(tag)
                created_count += 1
        
        db.session.commit()
        print(f"✅ 默认标签创建成功（新增 {created_count} 个）")
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 创建默认标签失败: {str(e)}")
        return False


def create_welcome_article():
    """创建欢迎文章"""
    print("🔄 创建欢迎文章...")
    try:
        # 检查是否已存在文章 - 使用原生SQL避免字段依赖问题
        result = db.session.execute(text("SELECT COUNT(*) FROM articles")).scalar()
        if result and result > 0:
            print("ℹ️  已存在文章，跳过欢迎文章创建")
            return True
        
        welcome_content = """# 欢迎使用个人博客系统

这是一个功能完整的个人博客系统，具有以下特性：

## 主要功能

### 📝 文章管理
- 支持Markdown语法
- 文章分类和标签
- 草稿和发布状态
- 文章置顶功能
- 阅读量和点赞统计

### 💬 评论系统
- 支持访客评论
- 管理员审核机制
- 回复功能
- 私密评论选项
- IP地理位置显示

### 🎨 界面定制
- 多种预设背景主题
- 时间变化背景
- 自定义背景图片
- 响应式设计

### 📊 统计功能
- 访问统计
- 热门文章
- 数据分析

### 🔐 权限管理
- 管理员后台
- 文章访问验证
- 安全防护

## 开始使用

1. 登录管理后台：访问 `/admin` 
2. 默认账户：`admin` / `admin123`
3. **请立即修改默认密码！**
4. 开始创建你的第一篇文章

## 技术栈

- **后端**: Python Flask
- **数据库**: MySQL 
- **前端**: Bootstrap + jQuery
- **部署**: Gunicorn + Nginx

祝你使用愉快！🎉
"""
        
        # 获取技术标签
        tech_tag = Tag.query.filter_by(name='技术').first()
        
        # 创建欢迎文章 - 动态设置字段，兼容旧版本数据库
        article_data = {
            'title': '欢迎使用个人博客系统',
            'content': welcome_content,
            'status': 'published',
            'permission': 'public',
            'is_top': True,
            'view_count': 0,
            'likes_count': 0,
            'publish_location': '系统',
            'created_at': get_local_now(),
            'updated_at': get_local_now()
        }
        
        # 检查是否存在评论相关字段，如果存在则添加
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('articles')]
        
        if 'allow_comments' in columns:
            article_data['allow_comments'] = True
        if 'comments_count' in columns:
            article_data['comments_count'] = 0
        if 'publish_location' not in columns:
            # 如果数据库中没有publish_location字段，则不设置该字段
            article_data.pop('publish_location', None)
        
        article = Article(**article_data)
        
        if tech_tag:
            article.tags.append(tech_tag)
        
        db.session.add(article)
        db.session.commit()
        
        print("✅ 欢迎文章创建成功")
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 创建欢迎文章失败: {str(e)}")
        return False


def init_database():
    """初始化数据库"""
    print("=" * 60)
    print("开始初始化数据库...")
    print("=" * 60)
    print()
    
    success = True
    
    # 1. 创建表结构
    if not create_database_tables():
        success = False
    
    # 2. 创建默认管理员
    if success and not create_default_admin():
        success = False
    
    # 3. 创建系统配置
    if success and not create_default_configs():
        success = False
    
    # 4. 创建默认标签
    if success and not create_default_tags():
        success = False
    
    # 5. 创建欢迎文章
    if success and not create_welcome_article():
        success = False
    
    print()
    if success:
        print("🎉 数据库初始化完成！")
        print()
        print("📋 初始化摘要：")
        print("   ✅ 数据库表结构")
        print("   ✅ 管理员账户 (admin/admin123)")
        print("   ✅ 系统配置")
        print("   ✅ 默认标签")
        print("   ✅ 欢迎文章")
        print()
        print("🚀 系统就绪，请访问以下地址：")
        print("   - 前端: http://localhost:5000")
        print("   - 后台: http://localhost:5000/admin")
        print()
        print("⚠️  重要提醒：请立即登录后台修改默认密码！")
    else:
        print("❌ 数据库初始化失败")
        return False
    
    return True


def reset_database():
    """重置数据库"""
    print("=" * 60)
    print("重置数据库")
    print("=" * 60)
    print()
    
    print("⚠️  警告：此操作将删除所有数据！")
    confirm = input("确认要重置数据库吗？(输入 'yes' 确认): ").strip().lower()
    
    if confirm != 'yes':
        print("操作已取消")
        return True
    
    try:
        print("🔄 删除现有数据库表...")
        db.drop_all()
        print("✅ 数据库表删除完成")
        
        print()
        return init_database()
        
    except Exception as e:
        print(f"❌ 重置数据库失败: {str(e)}")
        return False


def upgrade_database():
    """升级数据库结构"""
    print("=" * 60)
    print("升级数据库结构")
    print("=" * 60)
    print()
    
    try:
        # 创建缺失的表
        print("🔄 检查并创建缺失的表...")
        db.create_all()
        print("✅ 数据库表检查完成")
        
        # 检查并添加缺失的字段
        print("🔄 检查数据库字段...")
        inspector = inspect(db.engine)
        
        # 检查articles表的字段
        if 'articles' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('articles')]
            
            # 添加评论相关字段
            if 'allow_comments' not in columns:
                print("🔄 添加 allow_comments 字段...")
                db.session.execute(text(
                    "ALTER TABLE articles ADD COLUMN allow_comments BOOLEAN DEFAULT TRUE"
                ))
                print("✅ allow_comments 字段添加成功")
            
            if 'comments_count' not in columns:
                print("🔄 添加 comments_count 字段...")
                db.session.execute(text(
                    "ALTER TABLE articles ADD COLUMN comments_count INTEGER DEFAULT 0"
                ))
                print("✅ comments_count 字段添加成功")
            
            if 'publish_location' not in columns:
                print("🔄 添加 publish_location 字段...")
                db.session.execute(text(
                    "ALTER TABLE articles ADD COLUMN publish_location VARCHAR(100) DEFAULT '未知'"
                ))
                print("✅ publish_location 字段添加成功")
        
        # 检查music表的字段
        if 'music' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('music')]
            
            # 添加音乐启用状态字段
            if 'is_enabled' not in columns:
                print("🔄 添加 music.is_enabled 字段...")
                db.session.execute(text(
                    "ALTER TABLE music ADD COLUMN is_enabled BOOLEAN DEFAULT TRUE NOT NULL"
                ))
                print("✅ music.is_enabled 字段添加成功")
        
        db.session.commit()
        
        # 更新配置（添加新的配置项）
        print("🔄 更新系统配置...")
        if create_default_configs():
            print("✅ 系统配置更新完成")
        
        print()
        print("🎉 数据库升级完成！")
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 数据库升级失败: {str(e)}")
        return False


def check_database():
    """检查数据库状态"""
    print("=" * 60)
    print("数据库状态检查")
    print("=" * 60)
    print()
    
    status = get_database_status()
    
    print("📋 数据库表状态：")
    for table_name, exists in status['tables'].items():
        status_icon = "✅" if exists else "❌"
        print(f"   {status_icon} {table_name}")
    
    print()
    print("📊 数据统计：")
    for data_type, count in status['data'].items():
        print(f"   {data_type}: {count}")
    
    print()
    
    # 检查必要表是否都存在
    required_tables = ['articles', 'tags', 'admins', 'site_config']
    missing_tables = [name for name in required_tables if not status['tables'].get(name)]
    
    if missing_tables:
        print(f"⚠️  缺少必要的表: {', '.join(missing_tables)}")
        print("建议运行: python init_db.py --upgrade")
    else:
        print("✅ 所有必要的表都已存在")
    
    # 检查管理员账户
    try:
        admin_count = status['data'].get('admins', 0)
        if admin_count == 0:
            print("⚠️  没有管理员账户")
            print("建议运行: python init_db.py --upgrade")
        else:
            print(f"✅ 管理员账户数量: {admin_count}")
    except:
        pass
    
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='数据库初始化和管理脚本')
    parser.add_argument('--init', action='store_true', help='初始化数据库（创建表和初始数据）')
    parser.add_argument('--reset', action='store_true', help='重置数据库（删除所有数据并重新初始化）')
    parser.add_argument('--upgrade', action='store_true', help='升级数据库结构（仅添加缺失的表和字段）')
    parser.add_argument('--check', action='store_true', help='检查数据库状态')
    
    args = parser.parse_args()
    
    if not any([args.init, args.reset, args.upgrade, args.check]):
        parser.print_help()
        return
    
    # 从环境变量获取配置，默认为development
    config_name = os.getenv('FLASK_CONFIG', 'development')
    print(f"使用配置环境: {config_name}")
    print()
    
    app = create_app(config_name)
    with app.app_context():
        try:
            # 检查数据库连接
            if not check_database_connection():
                print("❌ 无法连接到数据库，操作终止")
                sys.exit(1)
            
            print()  # 添加空行分隔
            
            success = True
            
            if args.check:
                success = check_database()
            elif args.init:
                success = init_database()
            elif args.reset:
                success = reset_database()
            elif args.upgrade:
                success = upgrade_database()
            
            if not success:
                sys.exit(1)
                
        except Exception as e:
            print(f"执行过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    main() 