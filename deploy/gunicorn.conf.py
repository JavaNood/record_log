#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gunicorn 配置文件 - 个人博客系统
"""

import multiprocessing

# 基础配置
bind = "127.0.0.1:5000"
backlog = 2048

# 工作进程配置
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# 超时配置
timeout = 30
keepalive = 2
graceful_timeout = 30

# 安全配置
user = "myblog"
group = "myblog"

# 进程命名
proc_name = "record_log"

# 日志配置
loglevel = "info"
accesslog = "/home/myblog/record_log/logs/gunicorn_access.log"
errorlog = "/home/myblog/record_log/logs/gunicorn_error.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 其他配置
daemon = False
pidfile = "/home/myblog/record_log/logs/gunicorn.pid"

# 性能优化
worker_tmp_dir = "/dev/shm"

# 环境变量
raw_env = [
        'FLASK_CONFIG=production'] 