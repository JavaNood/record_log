#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import session, redirect, url_for, request, flash, current_app


def hash_password(password):
    """加密密码"""
    # 使用随机盐值增强安全性
    salt = os.urandom(32)  # 32字节随机盐
    # 使用PBKDF2进行多次哈希
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    # 返回盐值和哈希值的组合
    return salt + pwdhash


def verify_password(stored_password, provided_password):
    """验证密码"""
    if not stored_password or not provided_password:
        return False
    
    # 提取盐值（前32字节）
    salt = stored_password[:32]
    stored_hash = stored_password[32:]
    
    # 使用相同的盐值和算法计算提供密码的哈希
    pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
    
    # 比较哈希值
    return pwdhash == stored_hash


def get_or_create_default_admin():
    """获取或创建默认管理员"""
    from .models import Admin, db
    
    # 查找现有管理员
    admin = Admin.query.filter_by(username='admin').first()
    
    if not admin:
        # 创建默认管理员
        from .utils import get_local_now
        admin = Admin(
            username='admin',
            email='admin@myblog.com',
            created_at=get_local_now()
        )
        admin.set_password('admin123')  # 使用Admin模型的set_password方法
        db.session.add(admin)
        db.session.commit()
    
    return admin


def authenticate_admin(username, password):
    """验证管理员身份"""
    if not username or not password:
        return False
    
    # 查找管理员
    from .models import Admin
    admin = Admin.query.filter_by(username=username).first()
    
    if not admin:
        # 如果是默认管理员用户名，尝试创建
        if username.lower() == 'admin':
            admin = get_or_create_default_admin()
        else:
            return False
    
    # 检查是否有临时密码（用于密码找回）
    temp_password = os.environ.get('ADMIN_TEMP_PASSWORD')
    if temp_password and password == temp_password:
        return True
    
    # 验证密码
    return admin.check_password(password)


def check_session_validity():
    """检查会话有效性"""
    if not session.get('admin_logged_in'):
        return False
    
    # 检查会话是否过期
    if session.permanent:
        # 获取会话开始时间
        login_time = session.get('admin_login_time')
        if login_time:
            try:
                login_datetime = datetime.fromisoformat(login_time)
                session_duration = current_app.config.get('PERMANENT_SESSION_LIFETIME', timedelta(hours=1))
                if datetime.now() - login_datetime > session_duration:
                    # 会话过期
                    admin_logout()
                    return False
            except (ValueError, TypeError):
                # 时间格式错误，强制登出
                admin_logout()
                return False
    
    return True


def login_required(f):
    """登录装饰器 - 要求用户必须登录才能访问"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查会话有效性
        if not check_session_validity():
            # 记录用户试图访问的页面
            session['next_url'] = request.url
            flash('会话已过期，请重新登录', 'warning')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """管理员权限装饰器 - 更严格的权限检查"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not check_session_validity():
            flash('需要管理员权限，请登录', 'danger')
            return redirect(url_for('admin.login'))
        
        # 额外的权限检查
        admin_username = session.get('admin_username')
        if not admin_username:
            flash('权限不足', 'danger')
            admin_logout()
            return redirect(url_for('admin.login'))
        
        # 验证管理员是否存在于数据库中
        from .models import Admin
        admin = Admin.query.filter_by(username=admin_username).first()
        if not admin:
            flash('管理员账户不存在', 'danger')
            admin_logout()
            return redirect(url_for('admin.login'))
        
        return f(*args, **kwargs)
    return decorated_function


def is_admin_logged_in():
    """检查管理员是否已登录"""
    return check_session_validity()


def get_current_admin():
    """获取当前登录的管理员信息"""
    if is_admin_logged_in():
        admin_username = session.get('admin_username')
        if admin_username:
            from .models import Admin
            admin = Admin.query.filter_by(username=admin_username).first()
            if admin:
                login_time = session.get('admin_login_time')
                return {
                    'username': admin.username,
                    'email': admin.email,
                    'login_time': login_time,
                    'session_permanent': session.permanent
                }
    return None


def admin_login(username, remember_me=False):
    """管理员登录成功后的会话设置"""
    session['admin_logged_in'] = True
    session['admin_username'] = username
    session['admin_login_time'] = datetime.now().isoformat()
    
    # 根据"记住我"选项设置session持久性
    if remember_me:
        session.permanent = True
    else:
        session.permanent = False
    
    # 清理可能的旧重定向URL
    session.pop('next_url', None)


def admin_logout():
    """管理员登出"""
    # 记录登出信息
    username = session.get('admin_username', '未知用户')
    
    # 清除所有管理员相关的session数据
    keys_to_remove = [
        'admin_logged_in', 
        'admin_username', 
        'admin_login_time',
        'next_url'
    ]
    for key in keys_to_remove:
        session.pop(key, None)
    
    # 重置session状态
    session.permanent = False
    
    return username


def change_admin_password(old_password, new_password):
    """修改管理员密码"""
    # 获取当前登录的管理员
    admin_username = session.get('admin_username')
    if not admin_username:
        return False, '用户未登录'
    
    from .models import Admin, db
    admin = Admin.query.filter_by(username=admin_username).first()
    if not admin:
        return False, '管理员账户不存在'
    
    # 验证旧密码
    if not admin.check_password(old_password):
        return False, '当前密码错误'
    
    # 验证新密码强度
    if len(new_password) < 6:
        return False, '新密码长度至少6位'
    
    if new_password == old_password:
        return False, '新密码不能与当前密码相同'
    
    try:
        # 更新密码到数据库
        admin.set_password(new_password)
        db.session.commit()
        
        # 强制所有会话重新登录（安全措施）
        admin_logout()
        
        return True, '密码修改成功，请重新登录'
    except Exception as e:
        db.session.rollback()
        return False, f'密码修改失败: {str(e)}'


def get_admin_info():
    """获取管理员基本信息"""
    from .models import Admin
    admin = Admin.query.filter_by(username='admin').first()
    if admin:
        return {
            'username': admin.username,
            'email': admin.email,
            'has_password': True
        }
    else:
        return {
            'username': 'admin',
            'email': 'admin@myblog.com',
            'has_password': False
        }


def get_session_info():
    """获取当前会话信息"""
    if not is_admin_logged_in():
        return None
    
    login_time = session.get('admin_login_time')
    session_duration = current_app.config.get('PERMANENT_SESSION_LIFETIME', timedelta(hours=1))
    
    info = {
        'username': session.get('admin_username'),
        'login_time': login_time,
        'is_permanent': session.permanent,
        'session_duration': str(session_duration)
    }
    
    if login_time and session.permanent:
        try:
            login_datetime = datetime.fromisoformat(login_time)
            expires_at = login_datetime + session_duration
            remaining_time = expires_at - datetime.now()
            info['expires_at'] = expires_at.isoformat()
            info['remaining_seconds'] = int(remaining_time.total_seconds())
            info['remaining_minutes'] = int(remaining_time.total_seconds() / 60)
        except (ValueError, TypeError):
            pass
    
    return info 