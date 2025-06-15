#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
工具函数模块
包含时区处理、时间格式化等通用功能
"""

from datetime import datetime, timezone, timedelta
from flask import current_app


def get_local_now():
    """获取当前本地时间（naive datetime）"""
    return datetime.now()


def format_datetime(dt, format_str='%Y-%m-%d %H:%M:%S'):
    """格式化时间显示"""
    if dt is None:
        return ''
    return dt.strftime(format_str)


def format_relative_time(dt):
    """格式化为相对时间（如：2小时前）"""
    if dt is None:
        return ''
    
    now = datetime.now()
    
    # 计算时间差
    diff = now - dt
    
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


def get_ip_location(ip_address):
    """获取IP地址的地理位置信息"""
    if not ip_address or ip_address in ['127.0.0.1', 'localhost', '::1']:
        return '本地'
    
    try:
        import requests
        # 使用免费的ip-api.com服务，支持中文
        response = requests.get(
            f'http://ip-api.com/json/{ip_address}?lang=zh-CN',
            timeout=3  # 3秒超时
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                country = data.get('country', '')
                region = data.get('regionName', '')  # 省份/州
                
                # 如果是中国，显示省份
                if country == '中国' or country == 'China':
                    if region and region != country:
                        # 处理一些特殊的省份名称
                        if region.endswith('省') or region.endswith('市') or region.endswith('区'):
                            return region
                        else:
                            return f'{region}省'
                    else:
                        return '中国'
                # 其他国家显示国家名
                elif country:
                    return country
                else:
                    return '未知地区'
            else:
                return '未知地区'
        else:
            return '未知地区'
            
    except Exception as e:
        # 网络错误或其他异常，返回未知地区
        return '未知地区'


# 保留兼容性的函数（但简化实现）
def utc_to_local(dt):
    """兼容性函数：直接返回输入"""
    return dt


def local_to_utc(dt):
    """兼容性函数：直接返回输入"""
    return dt


# 中国时区（保持兼容性）
CHINA_TZ = timezone(timedelta(hours=8)) 