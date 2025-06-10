#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
工具函数模块
包含时区处理、时间格式化等通用功能
"""

from datetime import datetime, timezone, timedelta
from flask import current_app


# 中国时区 (UTC+8)
CHINA_TZ = timezone(timedelta(hours=8))


def get_local_now():
    """获取当前本地时间（中国时区）"""
    return datetime.now(CHINA_TZ)


def utc_to_local(utc_dt):
    """将UTC时间转换为本地时间"""
    if utc_dt is None:
        return None
    
    # 如果是naive datetime，假设它是UTC时间
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    
    # 转换为中国时区
    return utc_dt.astimezone(CHINA_TZ)


def local_to_utc(local_dt):
    """将本地时间转换为UTC时间"""
    if local_dt is None:
        return None
    
    # 如果是naive datetime，假设它是本地时间
    if local_dt.tzinfo is None:
        local_dt = local_dt.replace(tzinfo=CHINA_TZ)
    
    # 转换为UTC
    return local_dt.astimezone(timezone.utc).replace(tzinfo=None)


def format_datetime(dt, format_str='%Y-%m-%d %H:%M:%S'):
    """格式化时间显示"""
    if dt is None:
        return ''
    
    # 转换为本地时间后格式化
    local_dt = utc_to_local(dt)
    return local_dt.strftime(format_str)


def format_relative_time(dt):
    """格式化为相对时间（如：2小时前）"""
    if dt is None:
        return ''
    
    local_dt = utc_to_local(dt)
    now = get_local_now()
    
    # 计算时间差
    diff = now - local_dt
    
    if diff.days > 0:
        if diff.days == 1:
            return '1天前'
        elif diff.days < 30:
            return f'{diff.days}天前'
        elif diff.days < 365:
            months = diff.days // 30
            return f'{months}个月前'
        else:
            years = diff.days // 365
            return f'{years}年前'
    
    seconds = diff.seconds
    if seconds < 60:
        return '刚刚'
    elif seconds < 3600:
        minutes = seconds // 60
        return f'{minutes}分钟前'
    else:
        hours = seconds // 3600
        return f'{hours}小时前' 