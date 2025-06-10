#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
时区修复脚本
将数据库中的UTC时间转换为本地时间（中国时区 UTC+8）

使用方法：
python fix_timezone.py --preview   # 预览将要修改的数据
python fix_timezone.py --fix       # 执行修复
python fix_timezone.py --rollback  # 回滚修复（将本地时间转换回UTC）
"""

import sys
import os
import argparse
from datetime import datetime, timezone, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Article, Tag, Admin, Config, SiteVisit
from app.utils import CHINA_TZ

# 中国时区
UTC_OFFSET = timedelta(hours=8)


def convert_utc_to_local(utc_time):
    """将UTC时间转换为本地时间（加8小时）"""
    if utc_time is None:
        return None
    return utc_time + UTC_OFFSET


def convert_local_to_utc(local_time):
    """将本地时间转换为UTC时间（减8小时）"""
    if local_time is None:
        return None
    return local_time - UTC_OFFSET


def get_table_stats():
    """获取各表的时间数据统计"""
    stats = {}
    
    # 文章表
    article_count = Article.query.count()
    if article_count > 0:
        earliest_article = Article.query.order_by(Article.created_at.asc()).first()
        latest_article = Article.query.order_by(Article.created_at.desc()).first()
        stats['articles'] = {
            'count': article_count,
            'earliest': earliest_article.created_at,
            'latest': latest_article.created_at
        }
    
    # 标签表
    tag_count = Tag.query.count()
    if tag_count > 0:
        earliest_tag = Tag.query.order_by(Tag.created_at.asc()).first()
        latest_tag = Tag.query.order_by(Tag.created_at.desc()).first()
        stats['tags'] = {
            'count': tag_count,
            'earliest': earliest_tag.created_at,
            'latest': latest_tag.created_at
        }
    
    # 管理员表
    admin_count = Admin.query.count()
    if admin_count > 0:
        earliest_admin = Admin.query.order_by(Admin.created_at.asc()).first()
        latest_admin = Admin.query.order_by(Admin.created_at.desc()).first()
        stats['admins'] = {
            'count': admin_count,
            'earliest': earliest_admin.created_at,
            'latest': latest_admin.created_at
        }
    
    # 配置表
    config_count = Config.query.count()
    if config_count > 0:
        earliest_config = Config.query.order_by(Config.updated_at.asc()).first()
        latest_config = Config.query.order_by(Config.updated_at.desc()).first()
        stats['configs'] = {
            'count': config_count,
            'earliest': earliest_config.updated_at,
            'latest': latest_config.updated_at
        }
    
    # 访问统计表
    visit_count = SiteVisit.query.count()
    if visit_count > 0:
        earliest_visit = SiteVisit.query.order_by(SiteVisit.visit_time.asc()).first()
        latest_visit = SiteVisit.query.order_by(SiteVisit.visit_time.desc()).first()
        stats['visits'] = {
            'count': visit_count,
            'earliest': earliest_visit.visit_time,
            'latest': latest_visit.visit_time
        }
    
    return stats


def preview_changes():
    """预览将要进行的时间转换"""
    print("=" * 60)
    print("时区修复预览 - 将UTC时间转换为中国时区（UTC+8）")
    print("=" * 60)
    print()
    
    stats = get_table_stats()
    total_records = 0
    
    for table_name, data in stats.items():
        print(f"{table_name.upper()} 表:")
        print(f"  记录数量: {data['count']}")
        print(f"  最早时间: {data['earliest']} -> {convert_utc_to_local(data['earliest'])}")
        print(f"  最晚时间: {data['latest']} -> {convert_local_to_utc(data['latest'])}")
        print()
        
        if table_name == 'articles':
            total_records += data['count'] * 2  # created_at + updated_at
        elif table_name == 'configs':
            total_records += data['count']  # 只有updated_at
        else:
            total_records += data['count']  # 只有created_at或visit_time
    
    print(f"总计将修改 {total_records} 个时间字段")
    print()
    print("⚠️  注意：此操作将修改数据库中的所有时间字段")
    print("⚠️  建议在执行前备份数据库")
    print()


def fix_timezone():
    """执行时区修复"""
    print("=" * 60)
    print("开始执行时区修复...")
    print("=" * 60)
    print()
    
    try:
        # 修复文章表
        print("修复文章表...")
        articles = Article.query.all()
        for article in articles:
            if article.created_at:
                article.created_at = convert_utc_to_local(article.created_at)
            if article.updated_at:
                article.updated_at = convert_utc_to_local(article.updated_at)
        print(f"✅ 修复了 {len(articles)} 篇文章的时间")
        
        # 修复标签表
        print("修复标签表...")
        tags = Tag.query.all()
        for tag in tags:
            if tag.created_at:
                tag.created_at = convert_utc_to_local(tag.created_at)
        print(f"✅ 修复了 {len(tags)} 个标签的时间")
        
        # 修复管理员表
        print("修复管理员表...")
        admins = Admin.query.all()
        for admin in admins:
            if admin.created_at:
                admin.created_at = convert_utc_to_local(admin.created_at)
        print(f"✅ 修复了 {len(admins)} 个管理员的时间")
        
        # 修复配置表
        print("修复配置表...")
        configs = Config.query.all()
        for config in configs:
            if config.updated_at:
                config.updated_at = convert_utc_to_local(config.updated_at)
        print(f"✅ 修复了 {len(configs)} 个配置的时间")
        
        # 修复访问统计表
        print("修复访问统计表...")
        visits = SiteVisit.query.all()
        for visit in visits:
            if visit.visit_time:
                visit.visit_time = convert_utc_to_local(visit.visit_time)
        print(f"✅ 修复了 {len(visits)} 条访问记录的时间")
        
        # 提交更改
        db.session.commit()
        print()
        print("🎉 时区修复完成！")
        print("📝 所有时间都已从UTC转换为中国时区（UTC+8）")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 修复失败: {str(e)}")
        raise


def rollback_timezone():
    """回滚时区修复（将本地时间转换回UTC）"""
    print("=" * 60)
    print("开始回滚时区修复...")
    print("=" * 60)
    print()
    
    try:
        # 回滚文章表
        print("回滚文章表...")
        articles = Article.query.all()
        for article in articles:
            if article.created_at:
                article.created_at = convert_local_to_utc(article.created_at)
            if article.updated_at:
                article.updated_at = convert_local_to_utc(article.updated_at)
        print(f"✅ 回滚了 {len(articles)} 篇文章的时间")
        
        # 回滚标签表
        print("回滚标签表...")
        tags = Tag.query.all()
        for tag in tags:
            if tag.created_at:
                tag.created_at = convert_local_to_utc(tag.created_at)
        print(f"✅ 回滚了 {len(tags)} 个标签的时间")
        
        # 回滚管理员表
        print("回滚管理员表...")
        admins = Admin.query.all()
        for admin in admins:
            if admin.created_at:
                admin.created_at = convert_local_to_utc(admin.created_at)
        print(f"✅ 回滚了 {len(admins)} 个管理员的时间")
        
        # 回滚配置表
        print("回滚配置表...")
        configs = Config.query.all()
        for config in configs:
            if config.updated_at:
                config.updated_at = convert_local_to_utc(config.updated_at)
        print(f"✅ 回滚了 {len(configs)} 个配置的时间")
        
        # 回滚访问统计表
        print("回滚访问统计表...")
        visits = SiteVisit.query.all()
        for visit in visits:
            if visit.visit_time:
                visit.visit_time = convert_local_to_utc(visit.visit_time)
        print(f"✅ 回滚了 {len(visits)} 条访问记录的时间")
        
        # 提交更改
        db.session.commit()
        print()
        print("🎉 时区回滚完成！")
        print("📝 所有时间都已从本地时区转换回UTC")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 回滚失败: {str(e)}")
        raise


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='时区修复脚本')
    parser.add_argument('--preview', action='store_true', help='预览将要修改的数据')
    parser.add_argument('--fix', action='store_true', help='执行时区修复')
    parser.add_argument('--rollback', action='store_true', help='回滚时区修复')
    
    args = parser.parse_args()
    
    if not any([args.preview, args.fix, args.rollback]):
        parser.print_help()
        return
    
    # 从环境变量获取配置，默认为development
    config_name = os.getenv('FLASK_CONFIG', 'development')
    print(f"使用配置环境: {config_name}")
    print()
    
    # 创建Flask应用
    app = create_app(config_name)
    
    with app.app_context():
        try:
            # 检查数据库连接
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            
            if args.preview:
                preview_changes()
            elif args.fix:
                # 确认操作
                confirm = input("确认要执行时区修复吗？这将修改数据库中的时间数据 (输入 'yes' 确认): ").strip().lower()
                if confirm == 'yes':
                    fix_timezone()
                else:
                    print("操作已取消")
            elif args.rollback:
                # 确认回滚
                confirm = input("确认要回滚时区修复吗？这将把时间转换回UTC (输入 'yes' 确认): ").strip().lower()
                if confirm == 'yes':
                    rollback_timezone()
                else:
                    print("操作已取消")
                
        except Exception as e:
            print(f"执行过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    main()