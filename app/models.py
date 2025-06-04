#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


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
    status = db.Column(db.Enum('draft', 'published'), default='draft', nullable=False)
    
    # 权限：public公开, verify需要验证
    permission = db.Column(db.Enum('public', 'verify'), default='public', nullable=False)
    verify_question = db.Column(db.Text)  # 验证问题
    verify_answer = db.Column(db.String(255))  # 验证答案
    
    is_top = db.Column(db.Boolean, default=False, nullable=False)  # 是否置顶
    view_count = db.Column(db.Integer, default=0, nullable=False)  # 浏览数
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关联关系
    tags = db.relationship('Tag', secondary=article_tags, backref=db.backref('articles', lazy='dynamic'))
    
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
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
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
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
            config.updated_at = datetime.utcnow()
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