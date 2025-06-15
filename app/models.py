#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .utils import get_local_now


# 文章标签关联表
article_tags = db.Table('article_tags',
    db.Column('article_id', db.Integer, db.ForeignKey('articles.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)


class Article(db.Model):
    """文章模型"""
    __tablename__ = 'articles'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    content = db.Column(db.Text)
    summary = db.Column(db.Text)
    author = db.Column(db.String(100))
    
    # 状态：draft草稿, published已发布
    status = db.Column(db.Enum('draft', 'published'), default='draft', nullable=False, index=True)
    
    # 权限：public公开, verify需要验证
    permission = db.Column(db.Enum('public', 'verify'), default='public', nullable=False, index=True)
    verify_question = db.Column(db.Text)  # 验证问题
    verify_answer = db.Column(db.String(255))  # 验证答案
    
    is_top = db.Column(db.Boolean, default=False, nullable=False, index=True)  # 是否置顶
    view_count = db.Column(db.Integer, default=0, nullable=False, index=True)  # 浏览数
    likes_count = db.Column(db.Integer, default=0, nullable=False, index=True)  # 点赞数
    
    # 评论相关字段
    allow_comments = db.Column(db.Boolean, default=True, nullable=False)  # 是否允许评论
    comments_count = db.Column(db.Integer, default=0, nullable=False, index=True)  # 评论数量
    
    # 发布地址
    publish_location = db.Column(db.String(100), index=True)  # 发布地址
    
    created_at = db.Column(db.DateTime, default=get_local_now, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=get_local_now, nullable=False, index=True)
    
    # 关联关系
    tags = db.relationship('Tag', secondary=article_tags, backref=db.backref('articles', lazy='dynamic'))
    comments = db.relationship('Comment', backref='article', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Article {self.title}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'summary': self.summary,
            'author': self.author,
            'status': self.status,
            'permission': self.permission,
            'verify_question': self.verify_question,
            'is_top': self.is_top,
            'view_count': self.view_count,
            'likes_count': self.likes_count,
            'allow_comments': self.allow_comments,
            'comments_count': self.comments_count,
            'publish_location': self.publish_location,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'tags': [tag.to_dict() for tag in self.tags]
        }


class Tag(db.Model):
    """标签模型"""
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    color = db.Column(db.String(7), default='#007bff', nullable=False)  # 标签颜色
    created_at = db.Column(db.DateTime, default=get_local_now, nullable=False)
    
    def __repr__(self):
        return f'<Tag {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'article_count': self.articles.count()
        }


class Admin(db.Model):
    """管理员模型"""
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=get_local_now, nullable=False)
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<Admin {self.username}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Config(db.Model):
    """系统配置模型"""
    __tablename__ = 'site_config'
    
    key_name = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=get_local_now, onupdate=get_local_now, nullable=False)
    
    def __repr__(self):
        return f'<Config {self.key_name}>'
    
    @staticmethod
    def get_value(key, default=None):
        """获取配置值"""
        config = Config.query.get(key)
        return config.value if config else default
    
    @staticmethod
    def set_value(key, value):
        """设置配置值"""
        config = Config.query.get(key)
        if config:
            config.value = value
            config.updated_at = get_local_now()
        else:
            config = Config(key_name=key, value=value)
            db.session.add(config)
        db.session.commit()
        return config
    
    def to_dict(self):
        """转换为字典"""
        return {
            'key_name': self.key_name,
            'value': self.value,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SiteVisit(db.Model):
    """网站访问统计模型"""
    __tablename__ = 'site_visits'
    
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False, index=True)  # 支持IPv6
    session_id = db.Column(db.String(255), nullable=False, index=True)
    user_agent = db.Column(db.Text)  # 用户代理信息
    referer = db.Column(db.String(255))  # 来源页面
    visit_time = db.Column(db.DateTime, default=get_local_now, nullable=False, index=True)
    page_url = db.Column(db.String(255))  # 访问的页面URL
    
    def __repr__(self):
        return f'<SiteVisit {self.ip_address} at {self.visit_time}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'session_id': self.session_id,
            'user_agent': self.user_agent,
            'referer': self.referer,
            'visit_time': self.visit_time.isoformat() if self.visit_time else None,
            'page_url': self.page_url
        }
    
    @staticmethod
    def get_stats():
        """获取访问统计信息"""
        from sqlalchemy import func, distinct
        
        # 总访问次数
        total_visits = SiteVisit.query.count()
        
        # 独立访客数（按IP去重）
        unique_visitors = db.session.query(func.count(distinct(SiteVisit.ip_address))).scalar()
        
        # 今日访问次数
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_visits = SiteVisit.query.filter(SiteVisit.visit_time >= today_start).count()
        
        # 今日独立访客
        today_unique = db.session.query(func.count(distinct(SiteVisit.ip_address))).filter(
            SiteVisit.visit_time >= today_start
        ).scalar()
        
        # 最近7天访问次数
        week_ago = datetime.now() - timedelta(days=7)
        week_visits = SiteVisit.query.filter(SiteVisit.visit_time >= week_ago).count()
        
        # 最近7天独立访客
        week_unique = db.session.query(func.count(distinct(SiteVisit.ip_address))).filter(
            SiteVisit.visit_time >= week_ago
        ).scalar()
        
        return {
            'total_visits': total_visits or 0,
            'unique_visitors': unique_visitors or 0,
            'today_visits': today_visits or 0,
            'today_unique': today_unique or 0,
            'week_visits': week_visits or 0,
            'week_unique': week_unique or 0
        }


class Comment(db.Model):
    """评论模型"""
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)  # 评论内容
    nickname = db.Column(db.String(50))  # 评论昵称
    ip_address = db.Column(db.String(45), nullable=False, index=True)  # IP地址
    location = db.Column(db.String(100))  # 地理位置信息
    is_private = db.Column(db.Boolean, default=False, nullable=False)  # 是否私密评论
    
    # 状态：pending待审核, approved已通过, rejected已拒绝
    status = db.Column(db.Enum('pending', 'approved', 'rejected'), default='pending', nullable=False, index=True)
    
    created_at = db.Column(db.DateTime, default=get_local_now, nullable=False, index=True)
    
    # 关联关系
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), index=True)  # 父评论ID，支持回复
    
    # 自引用关系，支持评论层级结构
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    
    def __repr__(self):
        return f'<Comment {self.id} on Article {self.article_id}>'
    
    @property
    def display_name(self):
        """显示名称：如果有昵称显示昵称，否则显示匿名访客"""
        if self.nickname and self.nickname.strip():
            return self.nickname
        else:
            # 匿名化IP显示，只显示前缀，不暴露真实IP
            return f"访客_{self.id:04d}"
    
    @property
    def location_display(self):
        """显示地理位置信息"""
        if self.location and self.location != '未知地区':
            return f"来自 {self.location}"
        return ""
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'content': self.content,
            'nickname': self.nickname,
            'display_name': self.display_name,
            'ip_address': self.ip_address,
            'location': self.location,
            'location_display': self.location_display,
            'is_private': self.is_private,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'article_id': self.article_id,
            'parent_id': self.parent_id,
            'replies_count': self.replies.count()
        }


class Music(db.Model):
    """音乐模型"""
    __tablename__ = 'music'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)  # 原始文件名
    display_name = db.Column(db.String(255), nullable=False, index=True)  # 显示名称
    file_path = db.Column(db.String(500), nullable=False)  # 文件存储路径
    file_size = db.Column(db.Integer, default=0)  # 文件大小（字节）
    mime_type = db.Column(db.String(100))  # MIME类型
    duration = db.Column(db.Integer, default=0)  # 音乐时长（秒）
    is_enabled = db.Column(db.Boolean, default=True, nullable=False, index=True)  # 是否添加到前端播放列表
    created_at = db.Column(db.DateTime, default=get_local_now, nullable=False, index=True)
    
    def __repr__(self):
        return f'<Music {self.display_name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'filename': self.filename,
            'display_name': self.display_name,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'duration': self.duration,
            'is_enabled': self.is_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @property
    def file_size_mb(self):
        """获取文件大小（MB）"""
        return round(self.file_size / (1024 * 1024), 2) if self.file_size else 0
    
    @property
    def web_path(self):
        """获取Web访问路径"""
        return f"/{self.file_path}" if self.file_path else "" 